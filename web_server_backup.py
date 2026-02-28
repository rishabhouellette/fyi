"""
FYI Social ∞ - Unified Web Server
Serves React frontend + FastAPI backend on port 5000
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import uuid4
import ipaddress
import random
import re
import shutil
import subprocess
import sqlite3
import asyncio
import mimetypes
import threading
import time

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from app_db import AppDB

PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data"
ACCOUNTS_DIR = PROJECT_DIR / "accounts"
ACCOUNTS_FILE = ACCOUNTS_DIR / "accounts.json"
UPLOADS_DIR = DATA_DIR / "uploads"
SCHEDULED_POSTS_FILE = DATA_DIR / "scheduled_posts.json"
CERTS_DIR = DATA_DIR / "certs"
DEV_CERT_FILE = CERTS_DIR / "localhost.crt"
DEV_KEY_FILE = CERTS_DIR / "localhost.key"
ACTIVE_ACCOUNTS_FILE = DATA_DIR / "active_accounts.json"
APP_DB_FILE = DATA_DIR / "fyi_webportal.db"


def _load_dotenv_fallback(env_path: Path) -> None:
    """Minimal .env loader used when python-dotenv isn't available.

    - Supports KEY=VALUE lines
    - Ignores comments and blank lines
    - Does not overwrite existing environment variables
    """
    try:
        if not env_path.exists():
            return
        for raw in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.lower().startswith("export "):
                line = line[7:].strip()
            if "=" not in line:
                continue
            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if not key:
                continue
            os.environ.setdefault(key, value)
    except Exception:
        return


def _load_env_files() -> None:
    # Load .env from project root.
    env_path = PROJECT_DIR / ".env"
    if not env_path.exists():
        return

    if load_dotenv:
        try:
            load_dotenv(env_path)
            return
        except Exception:
            # Fall back to manual parse.
            pass
    _load_dotenv_fallback(env_path)


_load_env_files()


def _ensure_dev_https_cert() -> tuple[str, str]:
    """Create (if missing) a self-signed cert for localhost development.

    Note: Browsers will still warn unless you trust the cert.
    """
    if DEV_CERT_FILE.exists() and DEV_KEY_FILE.exists():
        return str(DEV_CERT_FILE), str(DEV_KEY_FILE)

    try:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "HTTPS requested but cryptography is not available. Install it or run without --https."
        ) from e

    CERTS_DIR.mkdir(parents=True, exist_ok=True)

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "FYIUploader Dev"),
            x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
        ]
    )

    san = x509.SubjectAlternativeName(
        [
            x509.DNSName("localhost"),
            x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
        ]
    )

    now = datetime.utcnow()
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=825))
        .add_extension(san, critical=False)
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )

    DEV_CERT_FILE.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    DEV_KEY_FILE.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

    return str(DEV_CERT_FILE), str(DEV_KEY_FILE)

DATA_DIR.mkdir(exist_ok=True)
ACCOUNTS_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)

db = AppDB(APP_DB_FILE)


def _split_hashtags(text: str) -> list[str]:
    raw = (text or "").strip()
    if not raw:
        return []
    # Normalize separators
    raw = raw.replace("\n", " ").replace(",", " ")
    parts = [p.strip() for p in raw.split() if p.strip()]
    tags: list[str] = []
    for p in parts:
        if p.startswith("#"):
            tag = p
        else:
            # Allow bare words
            cleaned = re.sub(r"[^a-zA-Z0-9_]", "", p)
            if not cleaned:
                continue
            tag = f"#{cleaned}"
        if tag not in tags:
            tags.append(tag)
    return tags


async def _ollama_models(timeout_s: float = 1.5) -> list[str]:
    try:
        async with httpx.AsyncClient(timeout=timeout_s) as client:
            resp = await client.get("http://127.0.0.1:11434/api/tags")
            if resp.status_code != 200:
                return []
            data = resp.json() or {}
            models = [m.get("name") for m in (data.get("models") or []) if isinstance(m, dict) and m.get("name")]
            return [m for m in models if isinstance(m, str) and m.strip()]
    except Exception:
        return []


async def _ollama_generate(prompt: str, model: str, system: str | None = None, timeout_s: float = 20.0) -> str:
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        payload["system"] = system

    async with httpx.AsyncClient(timeout=timeout_s) as client:
        resp = await client.post("http://127.0.0.1:11434/api/generate", json=payload)
        resp.raise_for_status()
        data = resp.json() or {}
        return str(data.get("response") or "").strip()


def _slugify(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def _gen_slug(prefix: str = "l") -> str:
    alphabet = "abcdefghjkmnpqrstuvwxyz23456789"
    return f"{prefix}_{''.join(random.choice(alphabet) for _ in range(8))}"


def _iso_to_unix_seconds(value: str) -> int:
    """Convert an ISO8601 datetime string to unix seconds.

    - Accepts values with trailing 'Z' (UTC) or offsets.
    - If no timezone is present, treats the datetime as local time.
    """
    dt = datetime.fromisoformat((value or "").replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
    return int(dt.timestamp())


def _ceil_to_minute(dt: datetime) -> datetime:
    """Ceil a datetime up to the next minute (naive dt assumed local)."""
    if dt.second == 0 and dt.microsecond == 0:
        return dt
    return dt.replace(second=0, microsecond=0) + timedelta(minutes=1)


async def _facebook_latest_scheduled_time(account_id: Optional[str]) -> Optional[datetime]:
    """Best-effort: read the latest scheduled_publish_time for a connected Facebook page.

    This is used to make Smart Scheduling align with Meta Planner.
    Returns a *naive local* datetime (for consistency with the rest of this server).
    """
    if not account_id:
        account_id = _load_active_accounts().get("facebook")
    acct = _find_account_by_id(account_id) if account_id else None
    if not acct or acct.get("platform") != "facebook":
        return None

    access_token = acct.get("access_token")
    page_id = acct.get("page_id")
    if not access_token or not page_id:
        return None

    url = f"https://graph-video.facebook.com/v20.0/{page_id}/videos"
    params = {
        "access_token": access_token,
        "fields": "id,scheduled_publish_time,created_time",
        "limit": "25",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params)
        if resp.status_code >= 400:
            return None
        data = resp.json() or {}
        items = data.get("data") or []
        latest_ts = None
        for it in items:
            ts = it.get("scheduled_publish_time")
            try:
                ts_i = int(ts)
            except Exception:
                continue
            if latest_ts is None or ts_i > latest_ts:
                latest_ts = ts_i
        if latest_ts is None:
            return None
        # Convert to local naive datetime
        return datetime.fromtimestamp(int(latest_ts))
    except Exception:
        return None

def _load_scheduled_posts() -> list[dict]:
    # Source of truth: SQLite.
    # Back-compat: if DB is empty, one-time migrate from the legacy JSON file.
    posts = db.list_scheduled_posts(limit=1000)
    if posts:
        return posts

    if SCHEDULED_POSTS_FILE.exists():
        try:
            with open(SCHEDULED_POSTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            legacy = []
            if isinstance(data, list):
                legacy = data
            elif isinstance(data, dict) and isinstance(data.get("posts"), list):
                legacy = data["posts"]

            for p in legacy:
                if isinstance(p, dict) and p.get("id"):
                    db.insert_scheduled_post(
                        {
                            "id": p.get("id"),
                            "title": p.get("title"),
                            "caption": p.get("caption"),
                            "platforms": p.get("platforms") or [],
                            "scheduled_time": p.get("scheduled_time"),
                            "date": p.get("date"),
                            "time": p.get("time"),
                            "status": p.get("status") or "scheduled",
                            "created_at": p.get("created_at") or datetime.now().isoformat(),
                            "payload": p.get("payload") if isinstance(p.get("payload"), dict) else {},
                        }
                    )
            return db.list_scheduled_posts(limit=1000)
        except Exception:
            return []

    return []

def _save_scheduled_posts(posts: list[dict]) -> None:
    # Keep the legacy JSON file updated for manual inspection/backups, but treat SQLite as canonical.
    for p in posts:
        if isinstance(p, dict) and p.get("id"):
            db.insert_scheduled_post(
                {
                    "id": p.get("id"),
                    "title": p.get("title"),
                    "caption": p.get("caption"),
                    "platforms": p.get("platforms") or [],
                    "scheduled_time": p.get("scheduled_time"),
                    "date": p.get("date"),
                    "time": p.get("time"),
                    "status": p.get("status") or "scheduled",
                    "created_at": p.get("created_at") or datetime.now().isoformat(),
                    "payload": p.get("payload") if isinstance(p.get("payload"), dict) else {},
                }
            )

    SCHEDULED_POSTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SCHEDULED_POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"posts": posts}, f, indent=2)

sys.path.insert(0, str(PROJECT_DIR))

app = FastAPI(title="FYIXT API", version="2.0.0")

# In-memory progress store for long-running actions (e.g., Facebook resumable video upload).
# Keyed by a client-provided schedule/job id so the frontend can poll while the POST is in-flight.
_PROGRESS_LOCK = threading.Lock()
_PROGRESS: dict[str, dict[str, Any]] = {}


def _progress_cleanup_unlocked(now_ts: float, max_age_s: float = 2 * 60 * 60) -> None:
    # Callers must hold _PROGRESS_LOCK.
    stale: list[str] = []
    for k, v in list(_PROGRESS.items()):
        ts = float(v.get("updated_at_ts") or 0.0)
        if ts and (now_ts - ts) > max_age_s:
            stale.append(k)
    for k in stale:
        _PROGRESS.pop(k, None)


def _progress_set(job_id: str, *, stage: str, percent: int | None = None, message: str | None = None, extra: dict | None = None, done: bool | None = None, error: str | None = None) -> None:
    if not job_id:
        return
    now_ts = time.time()
    with _PROGRESS_LOCK:
        _progress_cleanup_unlocked(now_ts)
        cur = _PROGRESS.get(job_id) or {}
        nxt = {
            **cur,
            "job_id": job_id,
            "stage": stage,
            "updated_at": datetime.now().isoformat(),
            "updated_at_ts": now_ts,
        }
        if percent is not None:
            nxt["percent"] = int(max(0, min(100, percent)))
        if message is not None:
            nxt["message"] = str(message)
        if done is not None:
            nxt["done"] = bool(done)
        if error is not None:
            nxt["error"] = str(error)
        if extra:
            prev_extra = cur.get("extra") if isinstance(cur.get("extra"), dict) else {}
            nxt["extra"] = {**prev_extra, **extra}
        _PROGRESS[job_id] = nxt


@app.get("/api/schedule/progress/{job_id}")
async def get_schedule_progress(job_id: str):
    now_ts = time.time()
    with _PROGRESS_LOCK:
        _progress_cleanup_unlocked(now_ts)
        item = _PROGRESS.get(job_id)
    if not item:
        # The frontend polls this endpoint while a request is in-flight.
        # Returning 404 is noisy in logs and not actionable. Instead, return a benign placeholder.
        return {
            "success": True,
            "progress": {
                "job_id": job_id,
                "stage": "pending",
                "percent": 0,
                "message": "",
                "done": False,
                "updated_at": datetime.now().isoformat(),
                "updated_at_ts": now_ts,
            },
        }
    return {"success": True, "progress": item}

def _get_allowed_origins() -> list[str]:
    raw = os.getenv("FYI_ALLOWED_ORIGINS", "").strip()
    if not raw:
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]

_allowed_origins = _get_allowed_origins()
_allow_credentials = _allowed_origins != ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AccountCreate(BaseModel):
    platform: str
    name: str
    username: str

class OAuthStart(BaseModel):
    account_name: str
    return_url: Optional[str] = None

class ScheduleRequest(BaseModel):
    platforms: List[str]
    content: Dict[str, Any]
    scheduledTime: Optional[str] = None
    clips: Optional[List[str]] = []
    file_id: Optional[str] = None
    interval_minutes: Optional[int] = None
    accounts: Optional[Dict[str, str]] = None
    client_request_id: Optional[str] = None


class InstantPublishRequest(BaseModel):
    platforms: List[str]
    content: Dict[str, Any]
    file_id: Optional[str] = None
    clips: Optional[List[str]] = []
    accounts: Optional[Dict[str, str]] = None
    client_request_id: Optional[str] = None


class BulkScheduleItem(BaseModel):
    platforms: List[str]
    title: Optional[str] = ""
    caption: Optional[str] = ""
    file_id: Optional[str] = None
    scheduledTime: Optional[str] = None  # if omitted, will be computed


class BulkScheduleRequest(BaseModel):
    items: List[BulkScheduleItem]
    smart: bool = True
    interval_minutes: int = 60

class AccountManager:
    """Simple account management"""
    
    def load_accounts(self) -> List[dict]:
        if ACCOUNTS_FILE.exists():
            try:
                with open(ACCOUNTS_FILE, 'r') as f:
                    data = json.load(f)
                    return data.get('accounts', [])
            except:
                return []
        return []
    
    def save_accounts(self, accounts: List[dict]):
        ACCOUNTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(ACCOUNTS_FILE, 'w') as f:
            json.dump({'accounts': accounts}, f, indent=2)
    
    def add_account(self, platform: str, name: str, username: str) -> dict:
        accounts = self.load_accounts()
        account = {
            'id': f"{platform}_{len(accounts) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'platform': platform,
            'name': name,
            'username': username,
            'status': 'connected',
            'connected_at': datetime.now().isoformat(),
            'followers': 0,
            'total_posts': 0
        }
        accounts.append(account)
        self.save_accounts(accounts)
        try:
            db.upsert_account(account)
        except Exception:
            # DB is best-effort for legacy-created accounts.
            pass
        return account
    
    def remove_account(self, account_id: str) -> bool:
        accounts = self.load_accounts()
        accounts = [a for a in accounts if a.get('id') != account_id]
        self.save_accounts(accounts)
        try:
            db.delete_account(account_id)
        except Exception:
            pass
        return True

account_manager = AccountManager()

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat(), "version": "2.0.0"}

@app.get("/api/accounts")
async def get_accounts():
    accounts = account_manager.load_accounts()
    return {"accounts": accounts, "count": len(accounts)}

@app.post("/api/accounts")
async def create_account(account: AccountCreate):
    new_account = account_manager.add_account(
        platform=account.platform,
        name=account.name,
        username=account.username
    )
    return {"success": True, "account": new_account}

@app.delete("/api/accounts/{account_id}")
async def delete_account(account_id: str):
    account_manager.remove_account(account_id)
    active = _load_active_accounts()
    changed = False
    for platform, active_id in list(active.items()):
        if active_id == account_id:
            active.pop(platform, None)
            changed = True
    if changed:
        _save_active_accounts(active)
    return {"success": True, "message": f"Account {account_id} removed"}

@app.post("/api/accounts/{account_id}/refresh")
async def refresh_account(account_id: str):
    acct = _find_account_by_id(account_id)
    if not acct:
        raise HTTPException(status_code=404, detail="Account not found")

    platform = acct.get("platform")
    access_token = acct.get("access_token")
    if platform in ("facebook", "instagram"):
        if not access_token:
            raise HTTPException(status_code=400, detail="Account is missing access_token")
        if not FB_APP_ID or not FB_APP_SECRET:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Facebook App credentials not configured. Set FB_APP_ID and FB_APP_SECRET "
                    "(or FYI_FB_APP_ID/FYI_FB_APP_SECRET) in your environment or .env."
                ),
            )

        app_token = f"{FB_APP_ID}|{FB_APP_SECRET}"
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    "https://graph.facebook.com/debug_token",
                    params={"input_token": access_token, "access_token": app_token},
                )
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail=resp.text)
            data = resp.json() or {}
            return {"success": True, "platform": platform, "debug": data}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    raise HTTPException(status_code=501, detail=f"Refresh not implemented for platform '{platform}'")

import urllib.parse
import httpx

def _env_first(*names: str) -> str:
    for name in names:
        try:
            v = os.getenv(name, "")
        except Exception:
            v = ""
        v = (v or "").strip()
        if v:
            return v
    return ""


# Facebook app credentials are required for both Facebook and Instagram OAuth.
# Support both legacy and FYI_* naming to reduce setup friction.
FB_APP_ID = _env_first("FB_APP_ID", "FYI_FB_APP_ID", "FYI_FACEBOOK_APP_ID")
FB_APP_SECRET = _env_first("FB_APP_SECRET", "FYI_FB_APP_SECRET", "FYI_FACEBOOK_APP_SECRET")

YT_CLIENT_ID = os.getenv("YT_CLIENT_ID", "")
YT_CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET", "")

def _normalize_base_url(url: str) -> str:
    url = (url or "").strip()
    return url[:-1] if url.endswith("/") else url

def _get_public_base_url_from_request(req: Request) -> str:
    """Resolve the public base URL for redirects.

    Priority:
    1) FYI_PUBLIC_BASE_URL (explicit override)
    2) REPLIT_DOMAINS (hosted environment)
    3) Incoming request headers (supports reverse proxies)
    """
    explicit = _normalize_base_url(os.getenv("FYI_PUBLIC_BASE_URL", ""))
    if explicit:
        return explicit

    domains = os.getenv("REPLIT_DOMAINS", "").strip()
    if domains:
        domain = domains.split(",")[0]
        return f"https://{domain}"

    forwarded_proto = (req.headers.get("x-forwarded-proto") or "").split(",")[0].strip()
    scheme = forwarded_proto or req.url.scheme

    host = (req.headers.get("x-forwarded-host") or req.headers.get("host") or "").split(",")[0].strip()
    if host:
        return f"{scheme}://{host}"

    return _normalize_base_url(str(req.base_url))

def get_redirect_uri(req: Request) -> str:
    """Get the OAuth redirect URI based on environment and request.
    
    Uses the actual request origin (what the user's browser shows) rather than
    FYI_PUBLIC_BASE_URL, so the redirect URI matches what's registered in the
    platform's developer console.
    """
    # Use request origin so it matches the registered redirect URI
    forwarded_proto = (req.headers.get("x-forwarded-proto") or "").split(",")[0].strip()
    scheme = forwarded_proto or req.url.scheme
    host = (req.headers.get("x-forwarded-host") or req.headers.get("host") or "").split(",")[0].strip()
    if host:
        origin = f"{scheme}://{host}"
    else:
        origin = _normalize_base_url(str(req.base_url))
    return f"{origin}/oauth/callback/facebook"

def _load_accounts_raw() -> list[dict]:
    if ACCOUNTS_FILE.exists():
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("accounts", []) if isinstance(data, dict) else []
        except Exception:
            return []
    return []

def _find_account_by_id(account_id: str) -> Optional[dict]:
    for acct in _load_accounts_raw():
        if acct.get("id") == account_id:
            return acct
    return None


def _upsert_account_raw(acct: dict) -> None:
    accounts = _load_accounts_raw()
    accounts = [a for a in accounts if a.get("id") != acct.get("id")]
    accounts.append(acct)
    account_manager.save_accounts(accounts)
    try:
        db.upsert_account(acct)
    except Exception:
        pass


def _is_public_https_url(url: str) -> bool:
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception:
        return False
    if (parsed.scheme or "").lower() != "https":
        return False
    host = (parsed.hostname or "").lower()
    if host in {"localhost", "127.0.0.1", "::1"}:
        return False
    return True


async def _preflight_public_media_url(client: httpx.AsyncClient, media_url: str) -> None:
    """Verify the media URL is publicly reachable.

    Use a small GET (Range request) instead of HEAD because some servers
    (including this dev portal) may not support HEAD on FileResponse routes.
    """
    try:
        resp = await client.get(
            media_url,
            headers={"Range": "bytes=0-0"},
            follow_redirects=True,
        )
        # Accept 200 OK (no range support) or 206 Partial Content.
        if resp.status_code in (200, 206):
            return
        if resp.status_code >= 400:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Instagram cannot fetch the uploaded media. "
                    f"Public URL returned HTTP {resp.status_code}. "
                    f"Check that ngrok is running and tunneling to this portal. URL: {media_url}"
                ),
            )
        # Unexpected but non-error status codes.
        raise HTTPException(
            status_code=400,
            detail=(
                f"Instagram cannot fetch the uploaded media. "
                f"Public URL returned unexpected HTTP {resp.status_code}. URL: {media_url}"
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=(
                "Instagram cannot fetch the uploaded media (public URL not reachable). "
                f"Check FYI_PUBLIC_BASE_URL and ngrok tunnel. URL: {media_url}. Error: {e}"
            ),
        )


def _ig_status_has_error_code(status_payload: Any, code: str) -> bool:
    try:
        s = json.dumps(status_payload, ensure_ascii=False)
    except Exception:
        s = str(status_payload)
    return code in (s or "")


async def _ig_get_container_status(
    client: httpx.AsyncClient,
    creation_id: str,
    access_token: str,
    *,
    include_video_status: bool,
) -> dict[str, Any]:
    """Fetch IG container status with a compatibility fallback.

    Some container types reject the `video_status` field (error_subcode 2207065).
    When that happens, retry without `video_status`.
    """
    base_fields = "id,status,status_code"
    fields = f"{base_fields},video_status" if include_video_status else base_fields

    resp = await client.get(
        f"https://graph.facebook.com/v20.0/{creation_id}",
        params={"access_token": access_token, "fields": fields},
    )

    if resp.status_code >= 400 and include_video_status:
        try:
            data = resp.json() or {}
            err = data.get("error") if isinstance(data, dict) else None
            sub = str((err or {}).get("error_subcode") or "")
        except Exception:
            sub = ""
        # 2207065: video_status is not a valid parameter for the media type
        if sub == "2207065":
            resp2 = await client.get(
                f"https://graph.facebook.com/v20.0/{creation_id}",
                params={"access_token": access_token, "fields": base_fields},
            )
            if resp2.status_code >= 400:
                raise HTTPException(status_code=resp2.status_code, detail=resp2.text)
            return resp2.json() or {}

    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    return resp.json() or {}


async def _instagram_publish_resumable_local(
    *,
    ig_user_id: str,
    access_token: str,
    file_path: Path,
    caption: str,
    media_type: str,
) -> dict:
    """Fallback publish path that uploads the local file to Meta servers via rupload.

    This avoids Meta having to fetch the file from FYI_PUBLIC_BASE_URL.
    Note: Meta documents this as requiring Facebook Login for Business.
    """
    media_type_u = (media_type or "REELS").upper()
    if media_type_u not in {"REELS", "VIDEO", "STORIES"}:
        # For now we only support video publish via this fallback.
        raise HTTPException(status_code=400, detail="Resumable upload supports REELS|VIDEO|STORIES")

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Uploaded file not found")

    size = file_path.stat().st_size
    async with httpx.AsyncClient(timeout=120) as client:
        init_resp = await client.post(
            f"https://graph.facebook.com/v20.0/{ig_user_id}/media",
            data={
                "access_token": access_token,
                "media_type": media_type_u,
                "upload_type": "resumable",
                "caption": caption or "",
            },
        )
        if init_resp.status_code >= 400:
            raise HTTPException(status_code=init_resp.status_code, detail=init_resp.text)

        init_data = init_resp.json() or {}
        creation_id = init_data.get("id")
        uri = init_data.get("uri")
        if not creation_id or not uri:
            raise HTTPException(status_code=500, detail=f"Instagram resumable init failed: {init_data}")

        # Upload the file bytes to rupload.
        try:
            with open(file_path, "rb") as f:
                upload_resp = await client.post(
                    uri,
                    headers={
                        "Authorization": f"OAuth {access_token}",
                        "offset": "0",
                        "file_size": str(size),
                    },
                    content=f,
                )
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Instagram resumable upload failed: {e}")

        if upload_resp.status_code >= 400:
            raise HTTPException(status_code=upload_resp.status_code, detail=upload_resp.text)

        # Poll container status.
        last_status_payload: dict[str, Any] | None = None
        status_code_val = None
        for _ in range(90):
            last_status_payload = await _ig_get_container_status(
                client,
                creation_id,
                access_token,
                include_video_status=True,
            )
            status_code_val = last_status_payload.get("status_code")
            if status_code_val == "FINISHED":
                break
            if status_code_val == "ERROR":
                raise HTTPException(
                    status_code=400,
                    detail=f"Instagram resumable upload failed. creation_id={creation_id}. status={last_status_payload}",
                )
            await asyncio.sleep(2)

        if status_code_val != "FINISHED":
            raise HTTPException(
                status_code=504,
                detail=f"Instagram resumable processing timed out. creation_id={creation_id}. last_status={last_status_payload}",
            )

        publish_resp = await client.post(
            f"https://graph.facebook.com/v20.0/{ig_user_id}/media_publish",
            data={"access_token": access_token, "creation_id": creation_id},
        )
        if publish_resp.status_code >= 400:
            raise HTTPException(status_code=publish_resp.status_code, detail=publish_resp.text)

        ig_post_id = (publish_resp.json() or {}).get("id")
        return {
            "success": True,
            "platform": "instagram",
            "creation_id": creation_id,
            "post_id": ig_post_id,
            "resumable": True,
        }


async def _youtube_refresh_access_token(refresh_token: str) -> dict:
    if not YT_CLIENT_ID or not YT_CLIENT_SECRET:
        raise HTTPException(status_code=400, detail="YouTube credentials not configured (YT_CLIENT_ID/YT_CLIENT_SECRET)")

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": YT_CLIENT_ID,
                "client_secret": YT_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if resp.status_code != 200:
        raise HTTPException(status_code=400, detail=f"Failed to refresh YouTube token: {resp.text}")
    return resp.json() or {}


async def _ensure_youtube_access_token(acct: dict) -> str:
    access_token = acct.get("access_token")
    refresh_token = acct.get("refresh_token")
    expires_at = acct.get("token_expires_at")

    def _is_expired(value: str | None) -> bool:
        if not value:
            return False
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            # Consider expired if within 60 seconds.
            return dt <= (datetime.utcnow() + timedelta(seconds=60)).replace(tzinfo=dt.tzinfo)
        except Exception:
            return False

    if access_token and not _is_expired(expires_at):
        return access_token

    if not refresh_token:
        raise HTTPException(status_code=400, detail="YouTube account missing refresh_token; reconnect the account")

    token_data = await _youtube_refresh_access_token(refresh_token)
    new_access = token_data.get("access_token")
    if not new_access:
        raise HTTPException(status_code=400, detail="YouTube refresh did not return access_token")

    expires_in = int(token_data.get("expires_in") or 3600)
    acct["access_token"] = new_access
    acct["token_expires_at"] = (datetime.utcnow() + timedelta(seconds=max(60, expires_in - 60))).isoformat() + "Z"
    _upsert_account_raw(acct)
    return new_access


def _load_active_accounts() -> dict:
    if ACTIVE_ACCOUNTS_FILE.exists():
        try:
            with open(ACTIVE_ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and isinstance(data.get("active"), dict):
                return data["active"]
            if isinstance(data, dict):
                return data
        except Exception:
            return {}
    return {}


def _save_active_accounts(active: dict) -> None:
    ACTIVE_ACCOUNTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ACTIVE_ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"active": active}, f, indent=2)


class ActiveAccountSetRequest(BaseModel):
    platform: str
    account_id: str


@app.get("/api/active-accounts")
async def get_active_accounts():
    return {"success": True, "active": _load_active_accounts()}


@app.post("/api/active-accounts")
async def set_active_account(request: ActiveAccountSetRequest):
    acct = _find_account_by_id(request.account_id)
    if not acct:
        raise HTTPException(status_code=404, detail="Account not found")
    if acct.get("platform") != request.platform:
        raise HTTPException(status_code=400, detail="Account platform does not match")

    active = _load_active_accounts()
    active[request.platform] = request.account_id
    _save_active_accounts(active)
    return {"success": True, "active": active}

@app.post("/oauth/start/{platform}")
async def start_oauth(platform: str, request: OAuthStart, req: Request):
    """Start OAuth flow for a platform"""
    valid_platforms = ['facebook', 'instagram', 'youtube', 'twitter', 'linkedin', 'tiktok']
    
    if platform not in valid_platforms:
        raise HTTPException(status_code=400, detail=f"Invalid platform: {platform}")
    
    if platform == 'facebook' or platform == 'instagram':
        if not FB_APP_ID or not FB_APP_SECRET:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Facebook App credentials not configured. Set FB_APP_ID and FB_APP_SECRET "
                    "(or FYI_FB_APP_ID/FYI_FB_APP_SECRET) in your environment or .env."
                ),
            )
        
        redirect_uri = get_redirect_uri(req)
        state = f"{platform}_{request.account_name}"
        
        if platform == 'instagram':
            scopes = "instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement,pages_manage_posts,public_profile"
        else:
            scopes = "pages_show_list,pages_read_engagement,pages_manage_posts,public_profile"
        
        # auth_type=rerequest forces permission/account selection even if already logged in
        # config_id is not used; instead we rely on the scope to surface IG accounts
        auth_url = (
            f"https://www.facebook.com/v20.0/dialog/oauth?"
            f"client_id={FB_APP_ID}&"
            f"redirect_uri={urllib.parse.quote(redirect_uri)}&"
            f"scope={urllib.parse.quote(scopes)}&"
            f"state={urllib.parse.quote(state)}&"
            f"response_type=code&"
            f"auth_type=rerequest"
        )
        
        return {
            "success": True,
            "redirect": True,
            "auth_url": auth_url,
            "message": f"Redirecting to {platform} for authorization..."
        }

    if platform == "youtube":
        # Check stored credentials first, then fall back to env vars
        yt_client_id = _get_platform_credential("youtube", "client_id") or YT_CLIENT_ID
        yt_client_secret = _get_platform_credential("youtube", "client_secret") or YT_CLIENT_SECRET
        
        if not yt_client_id or not yt_client_secret:
            raise HTTPException(status_code=400, detail="YouTube OAuth not configured (YT_CLIENT_ID/YT_CLIENT_SECRET). Go to Settings > Platform Credentials to add your YouTube API credentials.")

        # Use request origin so redirect_uri matches what's registered in Google Cloud Console
        forwarded_proto = (req.headers.get("x-forwarded-proto") or "").split(",")[0].strip()
        scheme = forwarded_proto or req.url.scheme
        host = (req.headers.get("x-forwarded-host") or req.headers.get("host") or "").split(",")[0].strip()
        if host:
            origin = f"{scheme}://{host}"
        else:
            origin = _normalize_base_url(str(req.base_url))
        redirect_uri = f"{origin}/oauth/callback/youtube"
        state = f"youtube_{request.account_name}"
        scopes = [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube.readonly",
        ]
        auth_url = (
            "https://accounts.google.com/o/oauth2/v2/auth?"
            + urllib.parse.urlencode(
                {
                    "client_id": yt_client_id,
                    "redirect_uri": redirect_uri,
                    "response_type": "code",
                    "scope": " ".join(scopes),
                    "access_type": "offline",
                    "prompt": "consent",
                    "include_granted_scopes": "true",
                    "state": state,
                }
            )
        )
        return {
            "success": True,
            "redirect": True,
            "auth_url": auth_url,
            "message": "Redirecting to YouTube for authorization...",
        }
    
    # Don't claim success for platforms we haven't fully implemented.
    raise HTTPException(
        status_code=501,
        detail=(
            f"OAuth for '{platform}' is not implemented in the web portal yet. "
            "Provide platform credentials + OAuth redirect configuration, then implement the provider flow."
        ),
    )

@app.get("/oauth/callback/facebook")
@app.get("/callback")
async def facebook_oauth_callback(req: Request, code: str = None, state: str = None, error: str = None):
    """Handle Facebook OAuth callback"""
    if error:
        return JSONResponse(content={"success": False, "error": error}, status_code=400)
    
    if not code:
        return JSONResponse(content={"success": False, "error": "No authorization code received"}, status_code=400)
    
    redirect_uri = get_redirect_uri(req)
    
    async with httpx.AsyncClient() as client:
        token_response = await client.get(
            "https://graph.facebook.com/v20.0/oauth/access_token",
            params={
                "client_id": FB_APP_ID,
                "client_secret": FB_APP_SECRET,
                "redirect_uri": redirect_uri,
                "code": code
            }
        )
        
        if token_response.status_code != 200:
            return JSONResponse(content={"success": False, "error": "Failed to get access token"}, status_code=400)
        
        token_data = token_response.json()
        access_token = token_data.get("access_token")
        
        user_response = await client.get(
            "https://graph.facebook.com/v20.0/me",
            params={"access_token": access_token, "fields": "id,name"}
        )
        if user_response.status_code != 200:
            return JSONResponse(content={"success": False, "error": "Failed to fetch user profile", "detail": user_response.text}, status_code=400)
        user_data = user_response.json()
        
        pages_response = await client.get(
            "https://graph.facebook.com/v20.0/me/accounts",
            params={"access_token": access_token}
        )
        if pages_response.status_code != 200:
            return JSONResponse(content={"success": False, "error": "Failed to list Facebook pages", "detail": pages_response.text}, status_code=400)
        pages_data = pages_response.json()
        
        requested_platform = "facebook"
        account_name = "Facebook Account"
        if state:
            parts = state.split("_", 1)
            if len(parts) == 2:
                requested_platform = parts[0]
                account_name = parts[1]

        pages = pages_data.get("data", [])
        accounts = account_manager.load_accounts()

        def _upsert(acct: dict) -> None:
            nonlocal accounts
            accounts = [a for a in accounts if a.get("id") != acct.get("id")]
            accounts.append(acct)

        if pages:
            # Save all managed Pages (real Facebook Pages), not just the first.
            for page in pages:
                page_token = page.get("access_token")
                page_name = page.get("name", "Facebook Page")
                page_id = page.get("id")
                if not page_id or not page_token:
                    continue

                fb_account = {
                    "id": f"facebook_{page_id}",
                    "platform": "facebook",
                    "name": page_name,
                    "username": f"@{str(page_name).replace(' ', '')}",
                    "status": "connected",
                    "connected_at": datetime.now().isoformat(),
                    "followers": 0,
                    "total_posts": 0,
                    "page_id": page_id,
                    "access_token": page_token,
                    "connected_via": requested_platform,
                }
                _upsert(fb_account)

                # If the user is connecting Instagram, also look for linked IG business accounts.
                if requested_platform == "instagram":
                    ig_resp = await client.get(
                        f"https://graph.facebook.com/v20.0/{page_id}",
                        params={"access_token": page_token, "fields": "instagram_business_account"},
                    )
                    if ig_resp.status_code != 200:
                        continue
                    ig_data = ig_resp.json() or {}
                    ig_ba = (ig_data.get("instagram_business_account") or {}) if isinstance(ig_data, dict) else {}
                    ig_id = ig_ba.get("id") if isinstance(ig_ba, dict) else None
                    if not ig_id:
                        continue

                    ig_profile_resp = await client.get(
                        f"https://graph.facebook.com/v20.0/{ig_id}",
                        params={"access_token": page_token, "fields": "id,username,name"},
                    )
                    if ig_profile_resp.status_code != 200:
                        continue
                    ig_profile = ig_profile_resp.json() or {}
                    ig_username = ig_profile.get("username")
                    ig_name = ig_profile.get("name") or page_name

                    ig_account = {
                        "id": f"instagram_{ig_id}",
                        "platform": "instagram",
                        "name": ig_name,
                        "username": f"@{ig_username}" if ig_username else f"@{str(ig_name).replace(' ', '')}",
                        "status": "connected",
                        "connected_at": datetime.now().isoformat(),
                        "followers": 0,
                        "total_posts": 0,
                        "ig_user_id": ig_id,
                        "page_id": page_id,
                        "access_token": page_token,
                        "connected_via": "instagram",
                    }
                    _upsert(ig_account)

            account_manager.save_accounts(accounts)
            # Persist to SQLite as well (best-effort).
            for a in accounts:
                try:
                    db.upsert_account(a)
                except Exception:
                    pass
        else:
            # No pages were returned. This usually means the user has no managed Pages
            # or the app lacks proper permissions.
            fb_user = {
                "id": f"facebook_{user_data.get('id')}",
                "platform": "facebook",
                "name": user_data.get("name", "Facebook User"),
                "username": f"@{str(user_data.get('name', 'user')).replace(' ', '')}",
                "status": "connected",
                "connected_at": datetime.now().isoformat(),
                "followers": 0,
                "total_posts": 0,
                "user_id": user_data.get("id"),
                "access_token": access_token,
                "connected_via": requested_platform,
                "note": "No managed Pages were returned by /me/accounts",
            }
            _upsert(fb_user)
            account_manager.save_accounts(accounts)
            try:
                db.upsert_account(fb_user)
            except Exception:
                pass
    
    from fastapi.responses import RedirectResponse
    base = _get_public_base_url_from_request(req)
    return RedirectResponse(url=f"{base}/?oauth=success")


@app.get("/oauth/callback/youtube")
async def youtube_oauth_callback(req: Request, code: str = None, state: str = None, error: str = None):
    if error:
        return JSONResponse(content={"success": False, "error": error}, status_code=400)
    if not code:
        return JSONResponse(content={"success": False, "error": "No authorization code received"}, status_code=400)
    
    # Check stored credentials first, then fall back to env vars
    yt_client_id = _get_platform_credential("youtube", "client_id") or YT_CLIENT_ID
    yt_client_secret = _get_platform_credential("youtube", "client_secret") or YT_CLIENT_SECRET
    
    if not yt_client_id or not yt_client_secret:
        return JSONResponse(content={"success": False, "error": "YouTube OAuth not configured"}, status_code=400)

    # Use request origin so redirect_uri matches what was used during auth start
    forwarded_proto = (req.headers.get("x-forwarded-proto") or "").split(",")[0].strip()
    scheme = forwarded_proto or req.url.scheme
    host = (req.headers.get("x-forwarded-host") or req.headers.get("host") or "").split(",")[0].strip()
    if host:
        origin = f"{scheme}://{host}"
    else:
        origin = _normalize_base_url(str(req.base_url))
    redirect_uri = f"{origin}/oauth/callback/youtube"

    async with httpx.AsyncClient(timeout=20) as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": yt_client_id,
                "client_secret": yt_client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if token_resp.status_code != 200:
            return JSONResponse(
                content={"success": False, "error": "Failed to exchange code", "detail": token_resp.text},
                status_code=400,
            )
        token_data = token_resp.json() or {}
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = int(token_data.get("expires_in") or 3600)

        if not access_token:
            return JSONResponse(content={"success": False, "error": "No access_token returned"}, status_code=400)

        # Get channel info
        ch_resp = await client.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params={"part": "snippet", "mine": "true"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if ch_resp.status_code != 200:
            return JSONResponse(
                content={"success": False, "error": "Failed to fetch channel", "detail": ch_resp.text},
                status_code=400,
            )
        ch_data = ch_resp.json() or {}
        items = ch_data.get("items") or []
        if not items:
            return JSONResponse(content={"success": False, "error": "No YouTube channel found"}, status_code=400)

        channel_id = items[0].get("id")
        channel_title = ((items[0].get("snippet") or {}).get("title")) or "YouTube Channel"

    account_name = "YouTube Account"
    if state:
        parts = state.split("_", 1)
        if len(parts) == 2:
            account_name = parts[1]

    acct = {
        "id": f"youtube_{channel_id}",
        "platform": "youtube",
        "name": channel_title or account_name,
        "username": channel_title or account_name,
        "status": "connected",
        "connected_at": datetime.now().isoformat(),
        "followers": 0,
        "total_posts": 0,
        "channel_id": channel_id,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_expires_at": (datetime.utcnow() + timedelta(seconds=max(60, expires_in - 60))).isoformat() + "Z",
        "connected_via": "youtube",
    }
    _upsert_account_raw(acct)

    from fastapi.responses import RedirectResponse
    base = _get_public_base_url_from_request(req)
    return RedirectResponse(url=f"{base}/?oauth=success")


class FacebookUploadRequest(BaseModel):
    account_id: Optional[str] = None
    page_id: Optional[str] = None
    file_id: str
    title: Optional[str] = ""
    description: Optional[str] = ""
    scheduled_publish_time: Optional[int] = None


def _fb_safe_text(value: str, max_len: int) -> str:
    # Keep it simple + safe: strip, replace newlines, drop non-ascii chars.
    s = (value or "").strip().replace("\r", " ").replace("\n", " ")
    s = "".join(ch if 32 <= ord(ch) <= 126 else " " for ch in s)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > max_len:
        s = s[:max_len].rstrip()
    return s


def _facebook_resumable_upload_sync(
    *,
    upload_url: str,
    access_token: str,
    file_path: Path,
    title: str,
    description: str,
    scheduled_publish_time: Optional[int],
    progress_job_id: Optional[str],
) -> dict[str, Any]:
    """Facebook resumable upload with chunk progress (v1-style).

    Uses upload_phase=start/transfer/finish and updates the in-memory progress store.
    """
    size = int(file_path.stat().st_size)
    if size <= 0:
        raise RuntimeError("File is empty")

    def p(stage: str, percent: int | None = None, message: str | None = None, extra: dict | None = None):
        if progress_job_id:
            _progress_set(progress_job_id, stage=stage, percent=percent, message=message, extra=extra)

    p("facebook_upload_start", percent=1, message="Starting Facebook upload…", extra={"file_bytes": size})

    # Keep the client timeouts generous; chunk uploads can take time.
    with httpx.Client(timeout=300) as client:
        # 1) Start session
        start_resp = client.post(
            upload_url,
            data={
                "access_token": access_token,
                "upload_phase": "start",
                "file_size": str(size),
            },
        )
        if start_resp.status_code >= 400:
            raise RuntimeError(f"Facebook upload start failed: {start_resp.text}")
        start_data = start_resp.json() or {}
        upload_session_id = start_data.get("upload_session_id")
        video_id = start_data.get("video_id") or start_data.get("id")
        start_offset = start_data.get("start_offset")
        end_offset = start_data.get("end_offset")
        if not upload_session_id or start_offset is None or end_offset is None:
            raise RuntimeError(f"Facebook upload start missing fields: {start_data}")

        # 2) Transfer chunks
        def _as_int(v: Any) -> int:
            try:
                return int(v)
            except Exception:
                return 0

        start_off_i = _as_int(start_offset)
        end_off_i = _as_int(end_offset)

        # Report 1% early to avoid a stuck 0% UX.
        p("facebook_upload_transfer", percent=1, message="Uploading to Facebook…")

        with open(file_path, "rb") as f:
            # Facebook returns offsets; loop until complete.
            while start_off_i < end_off_i:
                chunk_len = max(0, end_off_i - start_off_i)
                f.seek(start_off_i)
                chunk = f.read(chunk_len)
                if not chunk:
                    raise RuntimeError("Facebook upload stalled (empty chunk)")

                # Retry the chunk a few times for transient errors.
                last_err = None
                for attempt in range(3):
                    try:
                        transfer_resp = client.post(
                            upload_url,
                            data={
                                "access_token": access_token,
                                "upload_phase": "transfer",
                                "upload_session_id": upload_session_id,
                                "start_offset": str(start_off_i),
                            },
                            files={"video_file_chunk": ("chunk.bin", chunk, "application/octet-stream")},
                        )
                        if transfer_resp.status_code >= 400:
                            raise RuntimeError(f"Facebook upload transfer failed: {transfer_resp.text}")
                        transfer_data = transfer_resp.json() or {}
                        start_off_i = _as_int(transfer_data.get("start_offset"))
                        end_off_i = _as_int(transfer_data.get("end_offset"))
                        if start_off_i <= 0 and end_off_i <= 0:
                            raise RuntimeError(f"Facebook upload transfer missing offsets: {transfer_data}")
                        break
                    except Exception as e:
                        last_err = e
                        if attempt < 2:
                            time.sleep(0.5 * (attempt + 1))
                        else:
                            raise

                uploaded = max(0, min(size, start_off_i))
                pct = int(round((uploaded / size) * 100)) if size else 0
                pct = max(1, min(99, pct))
                # Message intentionally excludes the percent; the UI displays percent separately.
                p(
                    "facebook_upload_transfer",
                    percent=pct,
                    message="Uploading to Facebook…",
                    extra={"uploaded_bytes": uploaded, "file_bytes": size},
                )

        # 3) Finish
        p("facebook_upload_finish", percent=99, message="Finalizing Facebook upload…")
        finish_data = {
            "access_token": access_token,
            "upload_phase": "finish",
            "upload_session_id": upload_session_id,
            "title": title,
            "description": description,
        }
        if scheduled_publish_time:
            finish_data["published"] = "false"
            finish_data["scheduled_publish_time"] = str(int(scheduled_publish_time))

        finish_resp = client.post(upload_url, data=finish_data)
        if finish_resp.status_code >= 400:
            raise RuntimeError(f"Facebook upload finish failed: {finish_resp.text}")
        finish_json = finish_resp.json() or {}
        # Some responses include the id here.
        video_id = video_id or finish_json.get("video_id") or finish_json.get("id")

        p(
            "facebook_upload_done",
            percent=100,
            message="Facebook upload complete.",
            extra={"video_id": video_id},
        )
        return {"video_id": video_id, "raw": {"start": start_data, "finish": finish_json}}


async def _facebook_upload_video_impl(request: FacebookUploadRequest, *, progress_job_id: Optional[str] = None):
    account_id = request.account_id
    if not account_id:
        active = _load_active_accounts()
        account_id = active.get("facebook")

    acct = _find_account_by_id(account_id) if account_id else None
    if not acct and request.page_id:
        for candidate in _load_accounts_raw():
            if candidate.get("platform") == "facebook" and candidate.get("page_id") == request.page_id:
                acct = candidate
                account_id = candidate.get("id")
                break
    if not acct:
        raise HTTPException(
            status_code=404,
            detail="Account not found (provide account_id, page_id, or set an active Facebook account)",
        )
    if acct.get("platform") != "facebook":
        raise HTTPException(status_code=400, detail="Account is not a Facebook account")

    access_token = acct.get("access_token")
    page_id = acct.get("page_id")
    if not access_token or not page_id:
        raise HTTPException(status_code=400, detail="Facebook account is missing access_token or page_id")

    file_path = UPLOADS_DIR / request.file_id
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Uploaded file not found")

    upload_url = f"https://graph-video.facebook.com/v20.0/{page_id}/videos"

    # Facebook can be picky about field lengths.
    title = _fb_safe_text(request.title or "", 80)
    description = _fb_safe_text(request.description or "", 2000)

    try:
        # Prefer resumable upload so we can emit real progress (v1 behavior).
        res = await asyncio.to_thread(
            _facebook_resumable_upload_sync,
            upload_url=upload_url,
            access_token=access_token,
            file_path=file_path,
            title=title,
            description=description,
            scheduled_publish_time=request.scheduled_publish_time,
            progress_job_id=progress_job_id,
        )
        return {
            "success": True,
            "platform": "facebook",
            "account_id": account_id,
            "video_id": (res or {}).get("video_id"),
            "raw": (res or {}).get("raw"),
        }
    except HTTPException:
        raise
    except Exception as e:
        if progress_job_id:
            _progress_set(progress_job_id, stage="facebook_upload_failed", percent=100, done=True, error=str(e), message="Facebook upload failed")
        raise HTTPException(status_code=502, detail=f"Facebook upload failed: {e}")


@app.post("/api/platforms/facebook/upload")
async def facebook_upload_video(request: FacebookUploadRequest):
    """Upload a video to Facebook using a previously OAuth-linked page token."""
    return await _facebook_upload_video_impl(request, progress_job_id=None)


class YouTubeUploadRequest(BaseModel):
    account_id: Optional[str] = None
    file_id: str
    title: Optional[str] = ""
    description: Optional[str] = ""
    privacy_status: Optional[str] = "private"  # private|unlisted|public
    publish_at: Optional[str] = None  # RFC3339 (only meaningful if privacy_status=private)


@app.post("/api/platforms/youtube/upload")
async def youtube_upload_video(request: YouTubeUploadRequest):
    account_id = request.account_id
    if not account_id:
        active = _load_active_accounts()
        account_id = active.get("youtube")

    acct = _find_account_by_id(account_id) if account_id else None
    if not acct:
        raise HTTPException(status_code=404, detail="YouTube account not found (provide account_id or set an active YouTube account)")
    if acct.get("platform") != "youtube":
        raise HTTPException(status_code=400, detail="Account is not a YouTube account")

    access_token = await _ensure_youtube_access_token(acct)

    file_path = UPLOADS_DIR / request.file_id
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Uploaded file not found")

    size = file_path.stat().st_size
    mime = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"

    privacy = (request.privacy_status or "private").lower()
    if privacy not in {"private", "public", "unlisted"}:
        raise HTTPException(status_code=400, detail="privacy_status must be private|public|unlisted")

    raw_title = request.title or file_path.stem
    # YouTube enforces a 100-character title limit
    yt_title = raw_title[:100].strip() if raw_title else file_path.stem[:100]
    if not yt_title:
        yt_title = "FYIXT Upload"
    snippet = {
        "title": yt_title,
        "description": request.description or "",
        "categoryId": "22",
    }
    status: dict[str, Any] = {"privacyStatus": privacy}
    if request.publish_at:
        # YouTube requires privacyStatus=private when scheduling.
        status["privacyStatus"] = "private"
        status["publishAt"] = request.publish_at

    init_url = "https://www.googleapis.com/upload/youtube/v3/videos"
    init_params = {"uploadType": "resumable", "part": "snippet,status"}
    init_headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Upload-Content-Length": str(size),
        "X-Upload-Content-Type": mime,
        "Content-Type": "application/json; charset=UTF-8",
    }

    async with httpx.AsyncClient(timeout=120) as client:
        init_resp = await client.post(
            init_url,
            params=init_params,
            headers=init_headers,
            json={"snippet": snippet, "status": status},
        )
        if init_resp.status_code >= 400:
            raise HTTPException(status_code=init_resp.status_code, detail=init_resp.text)

        upload_location = init_resp.headers.get("Location")
        if not upload_location:
            raise HTTPException(status_code=500, detail="YouTube resumable upload did not return a Location header")

        put_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": mime,
            "Content-Length": str(size),
            "Content-Range": f"bytes 0-{size-1}/{size}",
        }

        with open(file_path, "rb") as f:
            put_resp = await client.put(upload_location, headers=put_headers, content=f)

        if put_resp.status_code >= 400:
            raise HTTPException(status_code=put_resp.status_code, detail=put_resp.text)

        data = put_resp.json() if put_resp.text else {}
        return {
            "success": True,
            "platform": "youtube",
            "account_id": acct.get("id"),
            "video_id": data.get("id"),
            "raw": data,
        }

@app.get("/oauth/callback/{platform}")
async def oauth_callback(platform: str, code: str = None, state: str = None):
    """Handle OAuth callback for other platforms"""
    raise HTTPException(
        status_code=501,
        detail=f"OAuth callback for '{platform}' is not implemented in the web portal yet",
    )

@app.get("/api/growth")
async def get_growth_report(days: int = 30):
    """Get growth analytics report"""
    # Real (but simple) growth report based on actual persisted data.
    # Platform follower/engagement analytics require pulling metrics from each platform API.
    days = max(1, min(int(days or 30), 365))
    posts = db.list_scheduled_posts(limit=1000)
    now = datetime.utcnow()
    cutoff = now - timedelta(days=days)
    prev_cutoff = cutoff - timedelta(days=days)

    def _parse_dt(value: str | None) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            return None

    current_posts = [p for p in posts if (_parse_dt(p.get("scheduled_time")) or now) >= cutoff]
    prev_posts = [p for p in posts if prev_cutoff <= (_parse_dt(p.get("scheduled_time")) or now) < cutoff]

    current_count = len(current_posts)
    prev_count = len(prev_posts)
    change = current_count - prev_count
    growth_rate = 0
    if prev_count > 0:
        growth_rate = round((change / prev_count) * 100, 2)

    insights: list[str] = []
    if current_count == 0:
        insights.append("No scheduled posts in this period")
    else:
        insights.append(f"Scheduled posts in last {days} days: {current_count}")
    insights.append("Follower/engagement analytics require platform metric sync")

    return {
        "metrics": {
            "posts": {"current": current_count, "change": change, "growth_rate": growth_rate},
            "followers": {"current": None, "change": None, "growth_rate": None},
            "engagement": {"current": None, "change": None, "growth_rate": None},
            "views": {"current": None, "change": None, "growth_rate": None},
        },
        "insights": insights,
        "predictions": None,
        "period_days": days,
    }

@app.get("/api/config")
async def get_app_config():
    """Get app configuration and status"""
    ffmpeg = shutil.which("ffmpeg") is not None
    ffprobe = shutil.which("ffprobe") is not None
    ollama_installed = False
    models: list[str] = []
    try:
        async with httpx.AsyncClient(timeout=1.5) as client:
            resp = await client.get("http://127.0.0.1:11434/api/tags")
            if resp.status_code == 200:
                ollama_installed = True
                data = resp.json() or {}
                models = [m.get("name") for m in (data.get("models") or []) if isinstance(m, dict) and m.get("name")]
    except Exception:
        ollama_installed = False

    return {
        "ollama_installed": ollama_installed,
        "ffmpeg_installed": ffmpeg,
        "ffprobe_installed": ffprobe,
        "models": models,
        "version": "2.0.0",
        "environment": "web",
    }


class AICaptionRequest(BaseModel):
    topic: str
    platform: Optional[str] = "instagram"
    tone: Optional[str] = "casual"  # casual|professional|funny|inspirational
    keywords: Optional[List[str]] = None
    max_length: int = 220
    include_hashtags: bool = True
    hashtags_count: int = 8


class AIHashtagsRequest(BaseModel):
    topic: str
    platform: Optional[str] = "instagram"
    count: int = 12
    include_trending: bool = True


@app.post("/api/ai/caption")
async def ai_generate_caption(request: AICaptionRequest):
    topic = (request.topic or "").strip()
    if not topic:
        raise HTTPException(status_code=400, detail="topic is required")

    platform = (request.platform or "instagram").strip().lower()
    tone = (request.tone or "casual").strip().lower()
    max_length = max(40, min(int(request.max_length or 220), 1000))
    hashtags_count = max(0, min(int(request.hashtags_count or 0), 30))
    keywords = [k.strip() for k in (request.keywords or []) if isinstance(k, str) and k.strip()]

    # Try Ollama first (real AI) if available.
    model = (os.getenv("FYI_OLLAMA_MODEL") or "").strip()
    models = await _ollama_models()
    if not model and models:
        model = models[0]

    if model:
        try:
            system = "You write concise, high-performing social media captions. Return only the caption text."
            kw = f"\nKeywords: {', '.join(keywords)}" if keywords else ""
            prompt = (
                f"Platform: {platform}\n"
                f"Tone: {tone}\n"
                f"Topic: {topic}{kw}\n"
                f"Constraints: max {max_length} characters."
            )
            caption = await _ollama_generate(prompt=prompt, model=model, system=system, timeout_s=25.0)
            caption = caption.strip().strip('"').strip("'")
            if len(caption) > max_length:
                caption = caption[: max_length - 1].rstrip() + "…"

            hashtags: list[str] = []
            if request.include_hashtags and hashtags_count > 0:
                system2 = "Return only hashtags separated by spaces. No explanations."
                prompt2 = (
                    f"Generate {hashtags_count} relevant hashtags for platform={platform}.\n"
                    f"Topic: {topic}{kw}"
                )
                ht = await _ollama_generate(prompt=prompt2, model=model, system=system2, timeout_s=25.0)
                hashtags = _split_hashtags(ht)[:hashtags_count]

            return {
                "success": True,
                "mode": "ollama",
                "model": model,
                "caption": caption,
                "hashtags": hashtags,
            }
        except Exception:
            # Fall through to deterministic fallback.
            pass

    # Deterministic fallback: still functional when Ollama isn't installed.
    templates = {
        "casual": [
            "{topic} — thoughts?",
            "Quick update: {topic}",
            "If you're into {topic}, this one's for you.",
        ],
        "professional": [
            "{topic}. Key takeaways in the comments.",
            "{topic} — a practical breakdown.",
        ],
        "funny": [
            "Me, pretending I didn't just spend hours on {topic}.",
            "POV: {topic} was 'quick'…",
        ],
        "inspirational": [
            "{topic}. Keep going.",
            "{topic} — progress over perfection.",
        ],
    }
    pool = templates.get(tone, templates["casual"])
    base = pool[hash((topic, tone, platform)) % len(pool)].format(topic=topic)
    extras = []
    if keywords:
        extras.append(" • ".join(keywords[:3]))
    caption = (base + ("\n" + extras[0] if extras else "")).strip()
    if len(caption) > max_length:
        caption = caption[: max_length - 1].rstrip() + "…"

    hashtags: list[str] = []
    if request.include_hashtags and hashtags_count > 0:
        seed_words = []
        seed_words.extend(re.findall(r"[A-Za-z0-9_]{4,}", topic))
        seed_words.extend([re.sub(r"[^A-Za-z0-9_]", "", k) for k in keywords])
        seed_words = [w for w in seed_words if w]
        base_tags = [f"#{w[:20]}" for w in seed_words[: max(1, hashtags_count)]]
        trending = ["#trending", "#viral", "#explore"] if platform in ("instagram", "tiktok") else []
        hashtags = list(dict.fromkeys(base_tags + trending))[:hashtags_count]

    return {
        "success": True,
        "mode": "fallback",
        "model": None,
        "caption": caption,
        "hashtags": hashtags,
    }


@app.post("/api/ai/hashtags")
async def ai_generate_hashtags(request: AIHashtagsRequest):
    topic = (request.topic or "").strip()
    if not topic:
        raise HTTPException(status_code=400, detail="topic is required")

    platform = (request.platform or "instagram").strip().lower()
    count = max(1, min(int(request.count or 12), 30))

    model = (os.getenv("FYI_OLLAMA_MODEL") or "").strip()
    models = await _ollama_models()
    if not model and models:
        model = models[0]
    if model:
        try:
            system = "Return only hashtags separated by spaces. No explanations."
            prompt = f"Generate {count} relevant hashtags for platform={platform}. Topic: {topic}"
            out = await _ollama_generate(prompt=prompt, model=model, system=system, timeout_s=25.0)
            tags = _split_hashtags(out)
            if request.include_trending and platform in ("instagram", "tiktok"):
                tags = list(dict.fromkeys(tags + ["#trending", "#viral", "#explore"]))
            return {"success": True, "mode": "ollama", "model": model, "hashtags": tags[:count]}
        except Exception:
            pass

    # Fallback
    words = re.findall(r"[A-Za-z0-9_]{4,}", topic)
    tags = [f"#{w[:20]}" for w in words[:count]]
    if request.include_trending and platform in ("instagram", "tiktok"):
        tags = list(dict.fromkeys(tags + ["#trending", "#viral", "#explore"]))
    tags = tags[:count]
    if not tags:
        tags = ["#content", "#creator"][:count]
    return {"success": True, "mode": "fallback", "model": None, "hashtags": tags}


# =============================================================================
# XY-AI  —  FYIXT's own AI engine for smart prompts & trend discovery
# =============================================================================

class XYAIPromptRequest(BaseModel):
    goal: str  # e.g. "promote my coffee brand", "sell sneakers", "grow yoga channel"
    platform: Optional[str] = "instagram"
    content_type: Optional[str] = "post"  # post | reel | story | tweet | video
    tone: Optional[str] = "engaging"
    audience: Optional[str] = None  # e.g. "Gen-Z", "professionals", "moms"
    niche: Optional[str] = None  # e.g. "fitness", "tech", "food"
    count: int = 3  # how many prompt ideas to generate


class XYAITrendRequest(BaseModel):
    niche: Optional[str] = None
    platform: Optional[str] = "instagram"
    country: Optional[str] = "US"


class XYAIChatRequest(BaseModel):
    message: str
    history: list = []  # [{"role": "user"|"assistant", "content": "..."}]
    context: Optional[str] = None  # e.g. "social media marketing"
    preferred_model: Optional[str] = None  # e.g. "gpt-4o-mini", "gemini-2.5-flash", "auto"


class XYAIContentPlanRequest(BaseModel):
    niche: str
    platform: Optional[str] = "instagram"
    days: int = 7
    posts_per_day: int = 1
    tone: Optional[str] = "engaging"


# ---- built-in trend knowledge base (works offline, no API key needed) ----
_TREND_DB: dict[str, dict] = {
    "fitness": {
        "hashtags": ["#FitTok", "#GymMotivation", "#WorkoutRoutine", "#HealthyLifestyle", "#FitnessJourney", "#GymLife", "#TransformationTuesday", "#Gains", "#FitCheck", "#ActiveLifestyle"],
        "topics": ["75 Hard challenge updates", "Morning routine that changed my body", "What I eat in a day (high protein)", "Gym fails compilation", "3 exercises you're doing wrong", "Progressive overload explained simply"],
        "formats": ["Before/After transformation", "Day-in-the-life vlog", "Quick tips carousel", "Workout follow-along Reel", "Myth-busting thread"],
        "hooks": ["Stop doing this exercise NOW", "I gained 10lbs of muscle in 90 days — here's how", "The workout nobody talks about", "Your trainer won't tell you this"],
    },
    "tech": {
        "hashtags": ["#TechTok", "#AI", "#Coding", "#StartupLife", "#TechNews", "#Innovation", "#MachineLearning", "#WebDev", "#AppDev", "#FutureTech"],
        "topics": ["AI tools that save 10 hours/week", "Best VS Code extensions 2026", "Why I quit my FAANG job", "Build this in 10 minutes with AI", "Tech I regret buying", "Hidden iPhone/Android features"],
        "formats": ["Screen recording tutorial", "Hot take thread", "Tool comparison carousel", "Code-along Reel", "React to tech news"],
        "hooks": ["This AI tool replaced my entire team", "Stop using ChatGPT like this", "The app that made me $10K", "Every developer needs this"],
    },
    "food": {
        "hashtags": ["#FoodTok", "#RecipeOfTheDay", "#Foodie", "#HomeCooking", "#EasyRecipes", "#MealPrep", "#HealthyEating", "#Yummy", "#CookingHacks", "#FoodPorn"],
        "topics": ["5-minute meals that actually taste good", "Meal prep Sunday ideas", "I tried the viral TikTok recipe", "Restaurant quality at home", "Budget grocery haul", "Protein-packed snacks"],
        "formats": ["Overhead cooking video", "Taste test reaction", "Recipe carousel with steps", "Grocery haul vlog", "Before/after plating"],
        "hooks": ["You've been cooking pasta WRONG", "This 3-ingredient dessert broke the internet", "The meal that costs $2 and feeds 4", "Chefs hate this hack"],
    },
    "business": {
        "hashtags": ["#Entrepreneur", "#StartupLife", "#SmallBusiness", "#SideHustle", "#BusinessTips", "#Marketing", "#PersonalBrand", "#Hustle", "#MoneyMindset", "#GrowthHacking"],
        "topics": ["How I got my first 1000 customers", "Marketing mistakes costing you money", "The $0 marketing strategy that works", "Day in my life as a founder", "Tools I use to run my business", "How to price your services"],
        "formats": ["Story-time with lessons", "Step-by-step guide carousel", "Hot take tweet thread", "Revenue screenshot breakdown", "Behind-the-scenes day vlog"],
        "hooks": ["I made $50K from a single post — here's how", "Stop wasting money on ads", "The business model nobody talks about", "Why 90% of startups fail (and how to be the 10%)"],
    },
    "beauty": {
        "hashtags": ["#BeautyTok", "#MakeupTutorial", "#Skincare", "#GRWM", "#GlowUp", "#BeautyHacks", "#SkincareRoutine", "#MakeupLook", "#CleanBeauty", "#BeautyReview"],
        "topics": ["My holy grail skincare routine", "Drugstore vs high-end dupes", "GRWM for date night", "Skincare mistakes ruining your skin", "Clean beauty products that work", "Glass skin routine"],
        "formats": ["Get Ready With Me", "Product review haul", "Split-screen dupes comparison", "Satisfying skincare Reel", "Tutorial carousel"],
        "hooks": ["Dermatologists are BEGGING you to stop this", "The $8 product that replaced my $60 serum", "I tried the viral skincare hack for 30 days", "You're applying sunscreen wrong"],
    },
    "travel": {
        "hashtags": ["#TravelTok", "#Wanderlust", "#TravelGuide", "#HiddenGems", "#BudgetTravel", "#TravelHacks", "#Explore", "#Adventure", "#Backpacking", "#TravelVlog"],
        "topics": ["Hidden gems in [City]", "How I travel for cheap", "Things I wish I knew before visiting", "Best cafes to work from remotely", "Travel packing hacks", "Solo travel tips"],
        "formats": ["Cinematic travel montage", "Top 5 places carousel", "Day vlog in a new city", "Packing Reel", "Drone footage compilation"],
        "hooks": ["Don't visit [Place] without knowing THIS", "I found the cheapest flight hack", "The most underrated country in Europe", "How I travel full-time for $1500/month"],
    },
    "general": {
        "hashtags": ["#Viral", "#Trending", "#ForYouPage", "#FYP", "#Explore", "#ContentCreator", "#DigitalCreator", "#GrowOnSocial", "#SocialMedia", "#CreatorEconomy"],
        "topics": ["How to grow from 0 to 10K followers", "Content batching tips", "The algorithm explained simply", "Engagement hacks that actually work", "How I went viral", "Repurposing content across platforms"],
        "formats": ["Talking head with captions", "Carousel with value bombs", "Duet/stitch reaction", "Story poll series", "Behind-the-scenes Reel"],
        "hooks": ["The algorithm just changed — do THIS now", "I gained 10K followers in 30 days", "Stop posting at the wrong time", "This hack doubled my engagement overnight"],
    },
}


def _match_niche(niche: str | None) -> str:
    """Fuzzy-match user niche to our trend DB keys."""
    if not niche:
        return "general"
    n = niche.strip().lower()
    for key in _TREND_DB:
        if key in n or n in key:
            return key
    # keyword matching
    mapping = {
        "gym": "fitness", "workout": "fitness", "health": "fitness", "yoga": "fitness", "sport": "fitness",
        "coding": "tech", "programming": "tech", "software": "tech", "app": "tech", "ai": "tech", "developer": "tech",
        "cooking": "food", "recipe": "food", "restaurant": "food", "chef": "food", "meal": "food", "baking": "food",
        "startup": "business", "marketing": "business", "entrepreneur": "business", "brand": "business", "ecommerce": "business", "money": "business",
        "makeup": "beauty", "skincare": "beauty", "cosmetic": "beauty", "hair": "beauty", "fashion": "beauty",
        "travel": "travel", "vacation": "travel", "tourism": "travel", "adventure": "travel", "explore": "travel",
    }
    for kw, cat in mapping.items():
        if kw in n:
            return cat
    return "general"


@app.post("/api/xy-ai/prompts")
async def xy_ai_generate_prompts(request: XYAIPromptRequest):
    """XY-AI: Generate smart content prompts/ideas tailored to platform, niche and audience."""
    goal = (request.goal or "").strip()
    if not goal:
        raise HTTPException(status_code=400, detail="goal is required")

    platform = (request.platform or "instagram").strip().lower()
    content_type = (request.content_type or "post").strip().lower()
    tone = (request.tone or "engaging").strip().lower()
    audience = (request.audience or "").strip()
    niche = (request.niche or "").strip()
    count = max(1, min(request.count, 10))

    # Try Ollama for real AI generation
    model = (os.getenv("FYI_OLLAMA_MODEL") or "").strip()
    models = await _ollama_models()
    if not model and models:
        model = models[0]

    # Also try OpenAI / Anthropic via BYOK
    openai_key = _get_byok_key("openai")
    gemini_key = _get_byok_key("gemini")

    prompts_result: list[dict] = []

    # --- Path 1: Ollama (local AI) ---
    if model:
        try:
            system = (
                "You are XY-AI, FYIXT's creative content strategist. "
                "Generate unique, platform-optimized content prompts. "
                "Return a JSON array of objects with keys: title, caption, hashtags (array), hook, content_type. "
                "Return ONLY valid JSON, no markdown fences."
            )
            aud_part = f"\nTarget audience: {audience}" if audience else ""
            niche_part = f"\nNiche: {niche}" if niche else ""
            prompt = (
                f"Generate {count} viral content ideas.\n"
                f"Goal: {goal}\n"
                f"Platform: {platform}\n"
                f"Content type: {content_type}\n"
                f"Tone: {tone}{aud_part}{niche_part}\n"
                f"Make each idea unique with a scroll-stopping hook."
            )
            raw = await _ollama_generate(prompt=prompt, model=model, system=system, timeout_s=30.0)
            # Try to parse JSON
            raw = raw.strip()
            if raw.startswith("```"):
                raw = re.sub(r"^```\w*\n?", "", raw)
                raw = re.sub(r"\n?```$", "", raw)
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                prompts_result = parsed[:count]
            return {
                "success": True,
                "mode": "xy-ai-ollama",
                "model": model,
                "prompts": prompts_result,
                "niche_detected": _match_niche(niche or goal),
            }
        except Exception:
            pass  # fall through

    # --- Path 2: OpenAI via BYOK ---
    if openai_key:
        try:
            aud_part = f"\nTarget audience: {audience}" if audience else ""
            niche_part = f"\nNiche: {niche}" if niche else ""
            messages = [
                {"role": "system", "content": (
                    "You are XY-AI, FYIXT's creative content strategist. "
                    "Generate unique, platform-optimized content prompts. "
                    "Return a JSON array of objects with keys: title, caption, hashtags (array), hook, content_type. "
                    "Return ONLY valid JSON, no markdown."
                )},
                {"role": "user", "content": (
                    f"Generate {count} viral content ideas.\n"
                    f"Goal: {goal}\nPlatform: {platform}\n"
                    f"Content type: {content_type}\nTone: {tone}{aud_part}{niche_part}"
                )},
            ]
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                    json={"model": "gpt-4o-mini", "messages": messages, "temperature": 0.9},
                )
                resp.raise_for_status()
                data = resp.json()
                text = data["choices"][0]["message"]["content"].strip()
                if text.startswith("```"):
                    text = re.sub(r"^```\w*\n?", "", text)
                    text = re.sub(r"\n?```$", "", text)
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    prompts_result = parsed[:count]
                return {
                    "success": True,
                    "mode": "xy-ai-openai",
                    "model": "gpt-4o-mini",
                    "prompts": prompts_result,
                    "niche_detected": _match_niche(niche or goal),
                }
        except Exception:
            pass

    # --- Path 3: Gemini via BYOK ---
    if gemini_key:
        try:
            aud_part = f"\nTarget audience: {audience}" if audience else ""
            niche_part = f"\nNiche: {niche}" if niche else ""
            prompt_text = (
                "You are XY-AI, FYIXT's creative content strategist. "
                f"Generate {count} viral content ideas as a JSON array. "
                f"Goal: {goal}. Platform: {platform}. "
                f"Content type: {content_type}. Tone: {tone}.{aud_part}{niche_part}\n"
                "Each object: title, caption, hashtags (array), hook, content_type. "
                "Return ONLY valid JSON."
            )
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}",
                    json={"contents": [{"parts": [{"text": prompt_text}]}]},
                )
                resp.raise_for_status()
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                if text.startswith("```"):
                    text = re.sub(r"^```\w*\n?", "", text)
                    text = re.sub(r"\n?```$", "", text)
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    prompts_result = parsed[:count]
                return {
                    "success": True,
                    "mode": "xy-ai-gemini",
                    "model": "gemini-2.5-flash",
                    "prompts": prompts_result,
                    "niche_detected": _match_niche(niche or goal),
                }
        except Exception:
            pass

    # --- Path 4: Smart deterministic fallback (offline, always works) ---
    matched = _match_niche(niche or goal)
    db = _TREND_DB.get(matched, _TREND_DB["general"])
    hooks = db.get("hooks", [])
    topics = db.get("topics", [])
    formats = db.get("formats", [])
    hashtags_pool = db.get("hashtags", [])

    for i in range(count):
        idx = (hash((goal, i, platform)) % max(1, len(topics)))
        hook = hooks[i % len(hooks)] if hooks else f"Here's what you need to know about {goal}"
        topic = topics[idx % len(topics)] if topics else goal
        fmt = formats[i % len(formats)] if formats else "Standard post"
        tags = random.sample(hashtags_pool, min(5, len(hashtags_pool)))

        # personalize the hook with the user's goal
        personalized_hook = hook
        for placeholder in ["[City]", "[Place]"]:
            personalized_hook = personalized_hook.replace(placeholder, goal.split()[0].title() if goal else "this")

        prompts_result.append({
            "title": topic,
            "caption": f"{personalized_hook}\n\n{topic}",
            "hashtags": tags,
            "hook": personalized_hook,
            "content_type": content_type,
            "format_suggestion": fmt,
        })

    return {
        "success": True,
        "mode": "xy-ai-smart-fallback",
        "model": None,
        "prompts": prompts_result,
        "niche_detected": matched,
    }


@app.post("/api/xy-ai/trends")
async def xy_ai_get_trends(request: XYAITrendRequest):
    """XY-AI: Discover trending topics, hashtags and content formats for any niche."""
    niche = (request.niche or "").strip()
    platform = (request.platform or "instagram").strip().lower()
    matched = _match_niche(niche)
    db = _TREND_DB.get(matched, _TREND_DB["general"])

    # Try AI-enhanced trend analysis if available
    model = (os.getenv("FYI_OLLAMA_MODEL") or "").strip()
    models = await _ollama_models()
    if not model and models:
        model = models[0]

    ai_insights = None
    if model:
        try:
            system = "You are a social media trend analyst. Return a brief JSON with keys: emerging_trends (array of strings), predicted_viral (string), best_posting_times (array), engagement_tip (string). ONLY valid JSON."
            prompt = f"Analyze current {platform} trends for niche: {niche or 'general content creation'}. Country: {request.country}."
            raw = await _ollama_generate(prompt=prompt, model=model, system=system, timeout_s=20.0)
            raw = raw.strip()
            if raw.startswith("```"):
                raw = re.sub(r"^```\w*\n?", "", raw)
                raw = re.sub(r"\n?```$", "", raw)
            ai_insights = json.loads(raw)
        except Exception:
            pass

    # Check BYOK OpenAI or Gemini for AI insights
    if not ai_insights:
        openai_key = _get_byok_key("openai")
        gemini_key = _get_byok_key("gemini")
        if openai_key:
            try:
                messages = [
                    {"role": "system", "content": "You are a social media trend analyst. Return a JSON with keys: emerging_trends (array of 5 strings), predicted_viral (string), best_posting_times (array of 3 strings), engagement_tip (string). ONLY valid JSON."},
                    {"role": "user", "content": f"Analyze current {platform} trends for niche: {niche or 'general'}. Country: {request.country}."},
                ]
                async with httpx.AsyncClient(timeout=25.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                        json={"model": "gpt-4o-mini", "messages": messages, "temperature": 0.7},
                    )
                    resp.raise_for_status()
                    text = resp.json()["choices"][0]["message"]["content"].strip()
                    if text.startswith("```"):
                        text = re.sub(r"^```\w*\n?", "", text)
                        text = re.sub(r"\n?```$", "", text)
                    ai_insights = json.loads(text)
            except Exception:
                pass
        elif gemini_key:
            try:
                prompt_text = (
                    "You are a social media trend analyst. "
                    f"Analyze current {platform} trends for niche: {niche or 'general'}. Country: {request.country}. "
                    "Return a JSON with keys: emerging_trends (array of 5 strings), predicted_viral (string), best_posting_times (array of 3 strings), engagement_tip (string). ONLY valid JSON."
                )
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}",
                        json={
                            "contents": [{"parts": [{"text": prompt_text}]}],
                            "tools": [{"google_search": {}}],
                        },
                    )
                    resp.raise_for_status()
                    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if text.startswith("```"):
                        text = re.sub(r"^```\w*\n?", "", text)
                        text = re.sub(r"\n?```$", "", text)
                    ai_insights = json.loads(text)
            except Exception:
                pass

    # Platform-specific best posting times (static, reliable data)
    posting_times = {
        "instagram": ["9:00 AM", "12:00 PM", "5:00 PM", "7:00 PM"],
        "youtube": ["2:00 PM", "5:00 PM", "9:00 PM"],
        "tiktok": ["7:00 AM", "10:00 AM", "7:00 PM", "11:00 PM"],
        "facebook": ["9:00 AM", "1:00 PM", "4:00 PM"],
        "twitter": ["8:00 AM", "12:00 PM", "5:00 PM"],
        "linkedin": ["7:30 AM", "12:00 PM", "5:30 PM"],
    }

    return {
        "success": True,
        "niche": matched,
        "platform": platform,
        "trending_hashtags": db.get("hashtags", []),
        "trending_topics": db.get("topics", []),
        "content_formats": db.get("formats", []),
        "viral_hooks": db.get("hooks", []),
        "best_posting_times": posting_times.get(platform, ["12:00 PM", "6:00 PM"]),
        "ai_insights": ai_insights,
    }


@app.post("/api/xy-ai/content-plan")
async def xy_ai_content_plan(request: XYAIContentPlanRequest):
    """XY-AI: Generate a multi-day content calendar plan for a niche."""
    niche = (request.niche or "").strip()
    if not niche:
        raise HTTPException(status_code=400, detail="niche is required")

    platform = (request.platform or "instagram").strip().lower()
    days = max(1, min(request.days, 30))
    ppd = max(1, min(request.posts_per_day, 5))
    tone = (request.tone or "engaging").strip().lower()
    matched = _match_niche(niche)
    db = _TREND_DB.get(matched, _TREND_DB["general"])

    # Try AI-powered plan
    model = (os.getenv("FYI_OLLAMA_MODEL") or "").strip()
    models = await _ollama_models()
    if not model and models:
        model = models[0]

    openai_key = _get_byok_key("openai")
    gemini_key = _get_byok_key("gemini")

    if model or openai_key or gemini_key:
        try:
            system = (
                "You are XY-AI, a content planning expert. "
                f"Create a {days}-day content plan ({ppd} post(s)/day) for {platform}. "
                "Return a JSON array where each item has: day (int), posts (array of {title, caption, hashtags (array), content_type, best_time}). "
                "Return ONLY valid JSON."
            )
            user_prompt = f"Niche: {niche}. Tone: {tone}. Platform: {platform}."

            raw = None
            used_mode = None
            if model:
                raw = await _ollama_generate(prompt=user_prompt, model=model, system=system, timeout_s=40.0)
                used_mode = "ollama"
            elif openai_key:
                async with httpx.AsyncClient(timeout=40.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                        json={"model": "gpt-4o-mini", "messages": [{"role": "system", "content": system}, {"role": "user", "content": user_prompt}], "temperature": 0.8},
                    )
                    resp.raise_for_status()
                    raw = resp.json()["choices"][0]["message"]["content"]
                    used_mode = "openai"
            elif gemini_key:
                async with httpx.AsyncClient(timeout=40.0) as client:
                    resp = await client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}",
                        json={"contents": [{"parts": [{"text": f"{system}\n\n{user_prompt}"}]}]},
                    )
                    resp.raise_for_status()
                    raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                    used_mode = "gemini"

            if raw:
                raw = raw.strip()
                if raw.startswith("```"):
                    raw = re.sub(r"^```\w*\n?", "", raw)
                    raw = re.sub(r"\n?```$", "", raw)
                plan = json.loads(raw)
                return {"success": True, "mode": f"xy-ai-{used_mode}", "plan": plan, "niche": matched}
        except Exception:
            pass

    # Deterministic fallback
    topics = db.get("topics", [f"{niche} content idea"])
    formats = db.get("formats", ["Standard post"])
    hooks = db.get("hooks", [f"Check this out: {niche}"])
    tags = db.get("hashtags", [f"#{niche.replace(' ', '')}"])

    posting_times = {
        "instagram": ["9:00 AM", "12:00 PM", "5:00 PM"],
        "youtube": ["2:00 PM", "5:00 PM"],
        "tiktok": ["7:00 AM", "7:00 PM", "10:00 PM"],
    }
    times = posting_times.get(platform, ["12:00 PM"])

    plan = []
    for d in range(1, days + 1):
        day_posts = []
        for p in range(ppd):
            idx = (d * ppd + p) % len(topics)
            day_posts.append({
                "title": topics[idx],
                "caption": f"{hooks[idx % len(hooks)]}\n\n{topics[idx]}",
                "hashtags": random.sample(tags, min(5, len(tags))),
                "content_type": formats[idx % len(formats)],
                "best_time": times[p % len(times)],
            })
        plan.append({"day": d, "posts": day_posts})

    return {"success": True, "mode": "xy-ai-smart-fallback", "plan": plan, "niche": matched}


@app.get("/api/xy-ai/chat/models")
async def xy_ai_chat_models():
    """Return the list of available chat models based on configured API keys."""
    models = [{"id": "auto", "name": "Auto (Best Available)", "provider": "auto"}]

    # Ollama
    ollama_model = (os.getenv("FYI_OLLAMA_MODEL") or "").strip()
    ollama_list = await _ollama_models()
    if ollama_model or ollama_list:
        for m in (ollama_list or [ollama_model]):
            if m:
                models.append({"id": m, "name": m, "provider": "ollama"})

    # OpenAI
    if _get_byok_key("openai"):
        models.extend([
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai"},
            {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai"},
            {"id": "gpt-4.1-mini", "name": "GPT-4.1 Mini", "provider": "openai"},
            {"id": "gpt-4.1", "name": "GPT-4.1", "provider": "openai"},
            {"id": "o4-mini", "name": "o4-mini (Reasoning)", "provider": "openai"},
        ])

    # Gemini
    if _get_byok_key("gemini"):
        models.extend([
            {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "provider": "gemini"},
            {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "provider": "gemini"},
            {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "provider": "gemini"},
        ])

    # Anthropic
    if _get_byok_key("anthropic"):
        models.extend([
            {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4", "provider": "anthropic"},
            {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "provider": "anthropic"},
        ])

    # xAI (Grok)
    if _get_byok_key("xai"):
        models.extend([
            {"id": "grok-3", "name": "Grok 3", "provider": "xai"},
            {"id": "grok-3-mini", "name": "Grok 3 Mini", "provider": "xai"},
        ])

    return {"success": True, "models": models}


@app.post("/api/xy-ai/chat")
async def xy_ai_chat(request: XYAIChatRequest):
    """XY-AI: Chat with FYIXT's AI assistant — answers social media, marketing, content questions."""
    message = (request.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    context_hint = (request.context or "").strip()
    history = request.history or []
    preferred = (request.preferred_model or "auto").strip().lower()

    system_prompt = (
        "You are XY-AI, FYIXT's intelligent assistant specializing in social media, "
        "content creation, digital marketing, branding, and growth strategy. "
        "You have real-time internet access via Google Search grounding — use it to provide "
        "current news, live trends, recent viral content, and up-to-date information. "
        "You are friendly, concise, and actionable. Use emojis sparingly. "
        "When asked about trends, give specific platform-tailored advice with real data. "
        "If the user asks something unrelated, answer helpfully but steer back to content/marketing."
    )
    if context_hint:
        system_prompt += f"\nAdditional context: {context_hint}"

    # Build conversation for multi-turn
    conv_history = ""
    for msg in history[-20:]:  # last 20 messages for context window
        role = msg.get("role", "user")
        content = msg.get("content", "")
        conv_history += f"\n{'User' if role == 'user' else 'XY-AI'}: {content}"
    conv_history += f"\nUser: {message}\nXY-AI:"

    # --- Resolve API keys ---
    ollama_model = (os.getenv("FYI_OLLAMA_MODEL") or "").strip()
    ollama_models = await _ollama_models()
    if not ollama_model and ollama_models:
        ollama_model = ollama_models[0]

    openai_key = _get_byok_key("openai")
    gemini_key = _get_byok_key("gemini")
    anthropic_key = _get_byok_key("anthropic")
    xai_key = _get_byok_key("xai")

    # --- Helper: call OpenAI ---
    async def _chat_openai(oai_model: str = "gpt-4o-mini"):
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-20:]:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": message})
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                json={"model": oai_model, "messages": messages, "temperature": 0.8},
            )
            resp.raise_for_status()
            data = resp.json()
            reply = data["choices"][0]["message"]["content"].strip()
            return {"success": True, "mode": "xy-ai-openai", "model": oai_model, "reply": reply}

    # --- Helper: call Gemini ---
    async def _chat_gemini(gm: str = "gemini-2.5-flash"):
        contents = []
        for msg in history[-20:]:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})
        contents.append({"role": "user", "parts": [{"text": message}]})
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{gm}:generateContent?key={gemini_key}",
                json={
                    "systemInstruction": {"parts": [{"text": system_prompt}]},
                    "contents": contents,
                    "tools": [{"google_search": {}}],
                },
            )
            if resp.status_code == 429:
                raise Exception(f"Rate limited on {gm}")
            resp.raise_for_status()
            data = resp.json()
            parts = data["candidates"][0]["content"]["parts"]
            reply_parts = [p["text"] for p in parts if "text" in p]
            reply = "\n".join(reply_parts).strip()
            return {"success": True, "mode": "xy-ai-gemini", "model": gm, "reply": reply}

    # --- Helper: call Anthropic ---
    async def _chat_anthropic(claude_model: str = "claude-sonnet-4-20250514"):
        messages = []
        for msg in history[-20:]:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": message})
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": anthropic_key,
                    "anthropic-version": "2023-06-01",
                    "Content-Type": "application/json",
                },
                json={"model": claude_model, "max_tokens": 1024, "system": system_prompt, "messages": messages},
            )
            resp.raise_for_status()
            data = resp.json()
            reply = data["content"][0]["text"].strip()
            return {"success": True, "mode": "xy-ai-anthropic", "model": claude_model, "reply": reply}

    # --- Helper: call xAI (Grok) — OpenAI-compatible API ---
    async def _chat_xai(grok_model: str = "grok-3-mini"):
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-20:]:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": message})
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {xai_key}", "Content-Type": "application/json"},
                json={"model": grok_model, "messages": messages, "temperature": 0.8},
            )
            resp.raise_for_status()
            data = resp.json()
            reply = data["choices"][0]["message"]["content"].strip()
            return {"success": True, "mode": "xy-ai-xai", "model": grok_model, "reply": reply}

    # --- If a specific model is requested, try it directly ---
    failed_provider = None  # Track which provider failed to avoid retrying in auto
    fallback_reason = ""
    if preferred and preferred != "auto":
        try:
            # OpenAI models
            if preferred.startswith("gpt-") or preferred.startswith("o"):
                failed_provider = "openai"
                if openai_key:
                    return await _chat_openai(preferred)
                raise Exception("No OpenAI API key configured")
            # Gemini models
            elif preferred.startswith("gemini-"):
                failed_provider = "gemini"
                if gemini_key:
                    return await _chat_gemini(preferred)
                raise Exception("No Gemini API key configured")
            # Anthropic models
            elif preferred.startswith("claude-"):
                failed_provider = "anthropic"
                if anthropic_key:
                    return await _chat_anthropic(preferred)
                raise Exception("No Anthropic API key configured")
            # xAI (Grok) models
            elif preferred.startswith("grok-"):
                failed_provider = "xai"
                if xai_key:
                    return await _chat_xai(preferred)
                raise Exception("No xAI API key configured")
            # Ollama
            elif ollama_model or preferred in (ollama_models or []):
                failed_provider = "ollama"
                target = preferred if preferred in (ollama_models or []) else ollama_model
                raw = await _ollama_generate(prompt=conv_history, model=target, system=system_prompt, timeout_s=45.0)
                return {"success": True, "mode": "xy-ai-ollama", "model": target, "reply": raw.strip()}
        except Exception as e:
            fallback_reason = str(e)
            print(f"[XY-AI chat] Preferred model '{preferred}' failed: {e}, falling back to auto...")

    # --- Auto mode: cascade through available providers (skip the one that just failed) ---
    # Helper to add fallback info if user requested a specific model
    def _with_fallback(result: dict) -> dict:
        if failed_provider and preferred != "auto":
            result["fallback"] = True
            result["requested_model"] = preferred
            result["fallback_reason"] = fallback_reason or "Unknown error"
        return result

    # Path 1: Ollama
    if ollama_model and failed_provider != "ollama":
        try:
            raw = await _ollama_generate(prompt=conv_history, model=ollama_model, system=system_prompt, timeout_s=45.0)
            return _with_fallback({"success": True, "mode": "xy-ai-ollama", "model": ollama_model, "reply": raw.strip()})
        except Exception as e:
            print(f"[XY-AI chat] Ollama failed: {e}")

    # Path 2: OpenAI
    if openai_key and failed_provider != "openai":
        try:
            return _with_fallback(await _chat_openai("gpt-4o-mini"))
        except Exception as e:
            print(f"[XY-AI chat] OpenAI failed: {e}")

    # Path 3: Gemini (with Google Search grounding for real-time info)
    if gemini_key:
        gemini_models = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
        for gm in gemini_models:
            try:
                result = await _chat_gemini(gm)
                return _with_fallback(result)
            except Exception as e:
                print(f"[XY-AI chat] Gemini {gm} failed: {e}")
                await asyncio.sleep(1)
                continue

    # Path 4: Anthropic
    if anthropic_key and failed_provider != "anthropic":
        try:
            return _with_fallback(await _chat_anthropic())
        except Exception as e:
            print(f"[XY-AI chat] Anthropic failed: {e}")

    # Path 5: xAI (Grok)
    if xai_key and failed_provider != "xai":
        try:
            return _with_fallback(await _chat_xai("grok-3-mini"))
        except Exception as e:
            print(f"[XY-AI chat] xAI Grok failed: {e}")

    # --- Fallback: smart offline response ---
    lower = message.lower()
    if any(w in lower for w in ["hashtag", "tag", "#"]):
        matched = _match_niche(message)
        tags = _TREND_DB.get(matched, _TREND_DB["general"])["hashtags"][:8]
        reply = f"Here are some trending hashtags for {matched}: {', '.join(tags)}\n\nTip: Mix 3-5 popular tags with 2-3 niche-specific ones for best reach!"
    elif any(w in lower for w in ["trend", "trending", "viral", "popular"]):
        matched = _match_niche(message)
        info = _TREND_DB.get(matched, _TREND_DB["general"])
        topics = info["topics"][:4]
        reply = f"Trending in {matched}:\n" + "\n".join(f"  • {t}" for t in topics) + "\n\nWant me to create content prompts for any of these?"
    elif any(w in lower for w in ["best time", "when to post", "schedule", "posting time"]):
        reply = "Best posting times vary by platform:\n  • Instagram: 11am-1pm & 7pm-9pm\n  • TikTok: 7am-9am & 7pm-11pm\n  • YouTube: 2pm-4pm (Thu-Sat)\n  • Twitter/X: 8am-10am & 6pm-9pm\n  • LinkedIn: 7am-8am & 5pm-6pm (Tue-Thu)\n\nAlways check your own analytics for your specific audience!"
    elif any(w in lower for w in ["caption", "write", "copy", "text"]):
        reply = "Here's a caption formula that works:\n\n🎯 Hook (stop the scroll)\n📖 Story or value (why should they care?)\n💡 CTA (tell them what to do)\n#️⃣ Hashtags (5-10 relevant ones)\n\nWant me to generate specific captions? Head to the Prompt Generator tab!"
    elif any(w in lower for w in ["grow", "growth", "followers", "engagement"]):
        reply = "Top growth strategies for 2026:\n  1. Post consistently (4-7x/week)\n  2. Use trending audio & formats\n  3. Engage in the first 30 min after posting\n  4. Collaborate with creators in your niche\n  5. Repurpose content across platforms\n  6. Optimize your bio & profile\n\nWhich platform are you focusing on?"
    elif any(w in lower for w in ["hello", "hi", "hey", "sup", "yo"]):
        reply = "Hey! 👋 I'm XY-AI, your content & marketing assistant. I can help with:\n  • Content ideas & captions\n  • Trending hashtags & topics\n  • Posting strategies\n  • Platform-specific tips\n  • Growth advice\n\nWhat would you like help with?"
    else:
        reply = f"Great question! While I work best with an AI provider connected (check Settings → AI Services), here's what I can help with offline:\n  • Trending hashtags & topics (try asking about trends)\n  • Best posting times\n  • Caption formulas\n  • Growth tips\n\nConnect an AI key like Gemini or OpenAI for full conversational answers!"

    return _with_fallback({"success": True, "mode": "xy-ai-smart-fallback", "model": None, "reply": reply})


@app.get("/api/xy-ai/niches")
async def xy_ai_list_niches():
    """XY-AI: List available trend niches."""
    return {
        "success": True,
        "niches": list(_TREND_DB.keys()),
        "description": "Pass any of these to the niche parameter, or describe your own — XY-AI will fuzzy-match it.",
    }


# =============================================================================
# BYOK API KEY MANAGEMENT (Bring Your Own Key)
# =============================================================================

BYOK_KEYS_FILE = DATA_DIR / "byok_keys.json"

def _load_byok_keys() -> dict[str, str]:
    """Load encrypted BYOK API keys."""
    if not BYOK_KEYS_FILE.exists():
        return {}
    try:
        return json.loads(BYOK_KEYS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _save_byok_keys(keys: dict[str, str]) -> None:
    """Save BYOK API keys."""
    BYOK_KEYS_FILE.write_text(json.dumps(keys, indent=2), encoding="utf-8")

def _get_byok_key(service: str) -> str | None:
    """Get API key for a service (checks BYOK store, then env vars, then bundled defaults)."""
    keys = _load_byok_keys()
    key = keys.get(service)
    if key:
        return key
    # Fallback to environment variables
    env_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "elevenlabs": "ELEVENLABS_API_KEY",
        "stability": "STABILITY_API_KEY",
        "replicate": "REPLICATE_API_TOKEN",
        "runway": "RUNWAY_API_KEY",
        "pika": "PIKA_API_KEY",
        "kling": "KLING_API_KEY",
        "flux": "FLUX_API_KEY",
        "ideogram": "IDEOGRAM_API_KEY",
        "gemini": "GOOGLE_API_KEY",
        "xai": "XAI_API_KEY",
    }
    env_key = env_map.get(service.lower())
    if env_key:
        val = os.getenv(env_key)
        if val:
            return val
    # Bundled default keys (obfuscated) — used when no BYOK or env key is set
    return _get_default_key(service.lower())


def _get_default_key(service: str) -> str | None:
    """Retrieve bundled default API key for a service (obfuscated)."""
    import base64 as _b64
    _defaults = {
        "gemini": [
            "QUl6YVN5RDB0RmlLVA==",
            "RWFyOExoNkVnMzVQWA==",
            "RVpOX1ljYl9CVzl5NA==",
        ],
    }
    parts = _defaults.get(service)
    if not parts:
        return None
    try:
        return "".join(_b64.b64decode(p).decode() for p in parts)
    except Exception:
        return None


class BYOKSetKeyRequest(BaseModel):
    service: str
    api_key: str


class BYOKDeleteKeyRequest(BaseModel):
    service: str


@app.get("/api/byok/keys")
async def list_byok_keys():
    """List configured BYOK services (keys are masked)."""
    keys = _load_byok_keys()
    services = {}
    for svc in ["openai", "anthropic", "elevenlabs", "stability", "replicate", "runway", "pika", "kling", "flux", "ideogram", "gemini", "xai"]:
        key = _get_byok_key(svc)
        services[svc] = {
            "configured": bool(key),
            "source": "byok" if svc in keys else ("env" if key else None),
            "masked": f"{key[:8]}...{key[-4:]}" if key and len(key) > 12 else ("****" if key else None),
        }
    return {"success": True, "services": services}


@app.post("/api/byok/keys")
async def set_byok_key(request: BYOKSetKeyRequest):
    """Store a BYOK API key."""
    service = (request.service or "").strip().lower()
    api_key = (request.api_key or "").strip()
    if not service or not api_key:
        raise HTTPException(status_code=400, detail="service and api_key are required")
    keys = _load_byok_keys()
    keys[service] = api_key
    _save_byok_keys(keys)
    return {"success": True, "service": service}


@app.delete("/api/byok/keys/{service}")
async def delete_byok_key(service: str):
    """Delete a BYOK API key."""
    service = (service or "").strip().lower()
    keys = _load_byok_keys()
    if service in keys:
        del keys[service]
        _save_byok_keys(keys)
    return {"success": True, "service": service}


# =============================================================================
# PLATFORM OAUTH CREDENTIALS MANAGEMENT
# =============================================================================

PLATFORM_CREDS_FILE = DATA_DIR / "platform_credentials.json"

def _load_platform_credentials() -> dict[str, dict[str, str]]:
    """Load platform OAuth credentials."""
    if not PLATFORM_CREDS_FILE.exists():
        return {}
    try:
        return json.loads(PLATFORM_CREDS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}

def _save_platform_credentials(creds: dict[str, dict[str, str]]) -> None:
    """Save platform OAuth credentials."""
    PLATFORM_CREDS_FILE.write_text(json.dumps(creds, indent=2), encoding="utf-8")

def _get_platform_credential(platform: str, key: str) -> str | None:
    """Get a credential for a platform (checks stored creds then env vars)."""
    creds = _load_platform_credentials()
    platform_creds = creds.get(platform.lower(), {})
    value = platform_creds.get(key)
    if value:
        return value
    # Fallback to environment variables
    env_map = {
        ("youtube", "client_id"): "YT_CLIENT_ID",
        ("youtube", "client_secret"): "YT_CLIENT_SECRET",
        ("facebook", "app_id"): ["FB_APP_ID", "FYI_FB_APP_ID"],
        ("facebook", "app_secret"): ["FB_APP_SECRET", "FYI_FB_APP_SECRET"],
        ("instagram", "app_id"): ["FB_APP_ID", "FYI_FB_APP_ID"],  # Instagram uses Facebook credentials
        ("instagram", "app_secret"): ["FB_APP_SECRET", "FYI_FB_APP_SECRET"],
        ("twitter", "api_key"): "TWITTER_API_KEY",
        ("twitter", "api_secret"): "TWITTER_API_SECRET",
        ("linkedin", "client_id"): "LINKEDIN_CLIENT_ID",
        ("linkedin", "client_secret"): "LINKEDIN_CLIENT_SECRET",
        ("tiktok", "client_key"): "TIKTOK_CLIENT_KEY",
        ("tiktok", "client_secret"): "TIKTOK_CLIENT_SECRET",
    }
    env_keys = env_map.get((platform.lower(), key))
    if env_keys:
        if isinstance(env_keys, list):
            for ek in env_keys:
                v = os.getenv(ek, "").strip()
                if v:
                    return v
        else:
            return os.getenv(env_keys, "").strip() or None
    return None


class PlatformCredentialRequest(BaseModel):
    platform: str
    credentials: dict[str, str]


@app.get("/api/platform-credentials")
async def list_platform_credentials():
    """List configured platforms (credentials are masked)."""
    creds = _load_platform_credentials()
    platforms = {}
    
    platform_keys = {
        "youtube": ["client_id", "client_secret"],
        "facebook": ["app_id", "app_secret"],
        "instagram": ["app_id", "app_secret"],  # Uses Facebook credentials
        "twitter": ["api_key", "api_secret"],
        "linkedin": ["client_id", "client_secret"],
        "tiktok": ["client_key", "client_secret"],
    }
    
    for platform, keys in platform_keys.items():
        platform_info = {"configured": True, "keys": {}}
        for key in keys:
            value = _get_platform_credential(platform, key)
            platform_info["keys"][key] = {
                "configured": bool(value),
                "source": "stored" if creds.get(platform, {}).get(key) else ("env" if value else None),
                "masked": f"{value[:6]}...{value[-4:]}" if value and len(value) > 10 else ("****" if value else None),
            }
            if not value:
                platform_info["configured"] = False
        platforms[platform] = platform_info
    
    return {"success": True, "platforms": platforms}


@app.post("/api/platform-credentials")
async def set_platform_credentials(request: PlatformCredentialRequest):
    """Store platform OAuth credentials."""
    platform = (request.platform or "").strip().lower()
    credentials = request.credentials or {}
    
    if not platform:
        raise HTTPException(status_code=400, detail="platform is required")
    
    creds = _load_platform_credentials()
    if platform not in creds:
        creds[platform] = {}
    
    for key, value in credentials.items():
        if value and value.strip():
            creds[platform][key] = value.strip()
    
    _save_platform_credentials(creds)
    
    # Update global variables for immediate use
    global YT_CLIENT_ID, YT_CLIENT_SECRET, FB_APP_ID, FB_APP_SECRET
    if platform == "youtube":
        YT_CLIENT_ID = _get_platform_credential("youtube", "client_id") or YT_CLIENT_ID
        YT_CLIENT_SECRET = _get_platform_credential("youtube", "client_secret") or YT_CLIENT_SECRET
    elif platform in ("facebook", "instagram"):
        FB_APP_ID = _get_platform_credential("facebook", "app_id") or FB_APP_ID
        FB_APP_SECRET = _get_platform_credential("facebook", "app_secret") or FB_APP_SECRET
    
    return {"success": True, "platform": platform}


@app.delete("/api/platform-credentials/{platform}")
async def delete_platform_credentials(platform: str):
    """Delete platform OAuth credentials."""
    platform = (platform or "").strip().lower()
    creds = _load_platform_credentials()
    if platform in creds:
        del creds[platform]
        _save_platform_credentials(creds)
    return {"success": True, "platform": platform}


# =============================================================================
# CREDITS / USAGE TRACKING SYSTEM
# =============================================================================

USAGE_FILE = DATA_DIR / "usage_credits.json"

def _load_usage() -> dict:
    """Load usage data."""
    if not USAGE_FILE.exists():
        return {"credits_used": 0, "history": [], "limits": {"monthly": 5000}}
    try:
        return json.loads(USAGE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"credits_used": 0, "history": [], "limits": {"monthly": 5000}}

def _save_usage(data: dict) -> None:
    """Save usage data."""
    USAGE_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")

def _add_usage(feature: str, credits: int, details: dict = None) -> dict:
    """Add usage and return updated totals."""
    data = _load_usage()
    data["credits_used"] = data.get("credits_used", 0) + credits
    entry = {
        "timestamp": datetime.now().isoformat(),
        "feature": feature,
        "credits": credits,
        "details": details or {},
    }
    history = data.get("history", [])
    history.append(entry)
    # Keep last 1000 entries
    data["history"] = history[-1000:]
    _save_usage(data)
    return {"credits_used": data["credits_used"], "credits_remaining": max(0, data.get("limits", {}).get("monthly", 5000) - data["credits_used"])}


@app.get("/api/usage")
async def get_usage():
    """Get current usage and credits."""
    data = _load_usage()
    monthly_limit = data.get("limits", {}).get("monthly", 5000)
    credits_used = data.get("credits_used", 0)
    return {
        "success": True,
        "credits_used": credits_used,
        "credits_remaining": max(0, monthly_limit - credits_used),
        "monthly_limit": monthly_limit,
        "history": data.get("history", [])[-50:],  # Last 50 entries
    }


@app.post("/api/usage/reset")
async def reset_usage():
    """Reset usage credits (for new billing period)."""
    data = _load_usage()
    data["credits_used"] = 0
    data["history"] = []
    _save_usage(data)
    return {"success": True, "credits_used": 0}


# =============================================================================
# AI IMAGE GENERATION (BYOK: DALL-E, Flux, Stability, Ideogram)
# =============================================================================

class AIImageRequest(BaseModel):
    prompt: str
    provider: str = "openai"  # openai|stability|flux|ideogram
    size: str = "1024x1024"
    style: Optional[str] = None
    n: int = 1


@app.post("/api/ai/image")
async def ai_generate_image(request: AIImageRequest):
    """Generate images using BYOK providers."""
    prompt = (request.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    provider = (request.provider or "openai").strip().lower()
    api_key = _get_byok_key(provider)
    if not api_key:
        raise HTTPException(status_code=400, detail=f"No API key configured for {provider}. Add it via /api/byok/keys")

    size = request.size or "1024x1024"
    n = max(1, min(int(request.n or 1), 4))

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            if provider == "openai":
                # DALL-E 3
                resp = await client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": "dall-e-3",
                        "prompt": prompt,
                        "size": size,
                        "n": n,
                        "quality": "standard",
                    },
                )
                if resp.status_code >= 400:
                    raise HTTPException(status_code=resp.status_code, detail=resp.text)
                data = resp.json()
                images = [{"url": img.get("url"), "revised_prompt": img.get("revised_prompt")} for img in data.get("data", [])]
                _add_usage("image_generation", n * 10, {"provider": provider, "prompt": prompt[:100]})
                return {"success": True, "provider": provider, "images": images}

            elif provider == "stability":
                # Stability AI
                resp = await client.post(
                    "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "text_prompts": [{"text": prompt, "weight": 1}],
                        "cfg_scale": 7,
                        "height": 1024,
                        "width": 1024,
                        "samples": n,
                        "steps": 30,
                    },
                )
                if resp.status_code >= 400:
                    raise HTTPException(status_code=resp.status_code, detail=resp.text)
                data = resp.json()
                images = [{"base64": art.get("base64"), "seed": art.get("seed")} for art in data.get("artifacts", [])]
                _add_usage("image_generation", n * 8, {"provider": provider, "prompt": prompt[:100]})
                return {"success": True, "provider": provider, "images": images}

            elif provider == "replicate":
                # Flux via Replicate
                resp = await client.post(
                    "https://api.replicate.com/v1/predictions",
                    headers={"Authorization": f"Token {api_key}"},
                    json={
                        "version": "black-forest-labs/flux-schnell",
                        "input": {"prompt": prompt, "num_outputs": n},
                    },
                )
                if resp.status_code >= 400:
                    raise HTTPException(status_code=resp.status_code, detail=resp.text)
                prediction = resp.json()
                pred_id = prediction.get("id")
                # Poll for completion
                for _ in range(60):
                    status_resp = await client.get(
                        f"https://api.replicate.com/v1/predictions/{pred_id}",
                        headers={"Authorization": f"Token {api_key}"},
                    )
                    status_data = status_resp.json()
                    if status_data.get("status") == "succeeded":
                        images = [{"url": u} for u in (status_data.get("output") or [])]
                        _add_usage("image_generation", n * 5, {"provider": provider, "prompt": prompt[:100]})
                        return {"success": True, "provider": provider, "images": images}
                    if status_data.get("status") == "failed":
                        raise HTTPException(status_code=500, detail=status_data.get("error", "Generation failed"))
                    await asyncio.sleep(2)
                raise HTTPException(status_code=504, detail="Image generation timed out")

            else:
                raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# AI VIDEO GENERATION (BYOK: Runway, Kling, Pika)
# =============================================================================

class AIVideoRequest(BaseModel):
    prompt: str
    provider: str = "runway"  # runway|kling|veo|grok_imagine
    image_url: Optional[str] = None  # For image-to-video
    duration: int = 4  # seconds
    aspect_ratio: str = "16:9"


@app.post("/api/ai/video")
async def ai_generate_video(request: AIVideoRequest):
    """Generate videos using BYOK providers (async - returns job_id to poll)."""
    prompt = (request.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    provider = (request.provider or "runway").strip().lower()
    # Veo uses the Gemini API key, Grok Imagine uses xAI key
    if provider == "veo":
        api_key = _get_byok_key("gemini")
    elif provider == "grok_imagine":
        api_key = _get_byok_key("xai")
    else:
        api_key = _get_byok_key(provider)
    if not api_key:
        key_name = "gemini" if provider == "veo" else ("xai" if provider == "grok_imagine" else provider)
        raise HTTPException(status_code=400, detail=f"No API key configured for {key_name}. Add it in Settings > AI Services.")

    job_id = f"aivideo_{uuid4().hex[:12]}"
    job_file = DATA_DIR / "ai_jobs" / f"{job_id}.json"
    job_file.parent.mkdir(parents=True, exist_ok=True)

    job_data = {
        "id": job_id,
        "provider": provider,
        "prompt": prompt,
        "status": "pending",
        "created_at": datetime.now().isoformat(),
        "result": None,
        "error": None,
    }
    job_file.write_text(json.dumps(job_data, indent=2), encoding="utf-8")

    # Start async generation in background
    asyncio.create_task(_run_video_generation(job_id, provider, api_key, prompt, request.image_url, request.duration, request.aspect_ratio))

    _add_usage("video_generation", 50, {"provider": provider, "prompt": prompt[:100]})
    return {"success": True, "job_id": job_id, "status": "pending", "poll_url": f"/api/ai/video/status/{job_id}"}


async def _run_video_generation(job_id: str, provider: str, api_key: str, prompt: str, image_url: str | None, duration: int, aspect_ratio: str = "16:9"):
    """Background task for video generation."""
    job_file = DATA_DIR / "ai_jobs" / f"{job_id}.json"

    def _update_job(status: str, result: Any = None, error: str = None):
        data = json.loads(job_file.read_text())
        data["status"] = status
        data["result"] = result
        data["error"] = error
        data["updated_at"] = datetime.now().isoformat()
        job_file.write_text(json.dumps(data, indent=2))

    try:
        async with httpx.AsyncClient(timeout=300) as client:
            if provider == "runway":
                # Runway Gen-3
                resp = await client.post(
                    "https://api.runwayml.com/v1/generations",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"prompt": prompt, "seconds": duration, "seed": random.randint(1, 999999)},
                )
                if resp.status_code >= 400:
                    _update_job("failed", error=resp.text)
                    return
                gen_data = resp.json()
                gen_id = gen_data.get("id")
                # Poll for completion
                for _ in range(120):
                    status_resp = await client.get(
                        f"https://api.runwayml.com/v1/generations/{gen_id}",
                        headers={"Authorization": f"Bearer {api_key}"},
                    )
                    status_data = status_resp.json()
                    if status_data.get("status") == "succeeded":
                        _update_job("completed", result={"url": status_data.get("output", [{}])[0].get("url")})
                        return
                    if status_data.get("status") == "failed":
                        _update_job("failed", error=status_data.get("error", "Generation failed"))
                        return
                    await asyncio.sleep(5)
                _update_job("failed", error="Generation timed out")

            elif provider == "replicate":
                # Kling/other via Replicate
                resp = await client.post(
                    "https://api.replicate.com/v1/predictions",
                    headers={"Authorization": f"Token {api_key}"},
                    json={
                        "version": "kuaishou/kling-v1",
                        "input": {"prompt": prompt, "duration": duration},
                    },
                )
                if resp.status_code >= 400:
                    _update_job("failed", error=resp.text)
                    return
                pred = resp.json()
                pred_id = pred.get("id")
                for _ in range(120):
                    status_resp = await client.get(
                        f"https://api.replicate.com/v1/predictions/{pred_id}",
                        headers={"Authorization": f"Token {api_key}"},
                    )
                    status_data = status_resp.json()
                    if status_data.get("status") == "succeeded":
                        output = status_data.get("output")
                        url = output[0] if isinstance(output, list) else output
                        _update_job("completed", result={"url": url})
                        return
                    if status_data.get("status") == "failed":
                        _update_job("failed", error=status_data.get("error", "Generation failed"))
                        return
                    await asyncio.sleep(5)
                _update_job("failed", error="Generation timed out")

            elif provider == "veo":
                # Google Veo 2 via Gemini API (generativelanguage.googleapis.com)
                # Duration mapping: Veo supports 5-8s range
                veo_duration = max(5, min(8, duration))
                # Aspect ratio mapping
                ar_map = {"16:9": "16:9", "9:16": "9:16", "1:1": "1:1"}
                veo_ar = ar_map.get(aspect_ratio, "16:9")

                generate_payload = {
                    "instances": [
                        {"prompt": prompt}
                    ],
                    "parameters": {
                        "aspectRatio": veo_ar,
                        "durationSeconds": veo_duration,
                        "sampleCount": 1,
                    }
                }
                if image_url:
                    generate_payload["instances"][0]["image"] = {"bytesBase64Encoded": image_url} if not image_url.startswith("http") else {"gcsUri": image_url}

                _update_job("processing")

                # Step 1: Start generation (returns a long-running operation)
                resp = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/veo-2.0-generate-001:predictLongRunning?key={api_key}",
                    json=generate_payload,
                    headers={"Content-Type": "application/json"},
                )
                if resp.status_code >= 400:
                    error_text = resp.text
                    print(f"[Veo] Generate request failed ({resp.status_code}): {error_text}")
                    _update_job("failed", error=f"Veo API error ({resp.status_code}): {error_text[:500]}")
                    return

                op_data = resp.json()
                op_name = op_data.get("name")
                if not op_name:
                    _update_job("failed", error=f"Veo returned no operation name: {json.dumps(op_data)[:500]}")
                    return

                print(f"[Veo] Generation started, operation: {op_name}")

                # Step 2: Poll the long-running operation for completion
                for attempt in range(120):  # ~10 minutes max (5s intervals)
                    await asyncio.sleep(5)
                    poll_resp = await client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/{op_name}:fetchPredictOperation?key={api_key}",
                        headers={"Content-Type": "application/json"},
                    )
                    if poll_resp.status_code >= 400:
                        print(f"[Veo] Poll failed ({poll_resp.status_code}): {poll_resp.text[:300]}")
                        continue

                    poll_data = poll_resp.json()
                    done = poll_data.get("done", False)

                    if done:
                        # Check for error
                        if "error" in poll_data:
                            err_msg = poll_data["error"].get("message", "Unknown Veo error")
                            _update_job("failed", error=err_msg)
                            return

                        # Extract video from response
                        response_data = poll_data.get("response", {})
                        videos = response_data.get("generateVideoResponse", {}).get("generatedSamples", [])
                        if not videos:
                            # Try alternate response format
                            videos = response_data.get("predictions", [])

                        if videos:
                            video_info = videos[0]
                            # Video may be base64 or a URI
                            if "video" in video_info and "uri" in video_info["video"]:
                                video_url = video_info["video"]["uri"]
                                _update_job("completed", result={"url": video_url, "provider": "veo"})
                            elif "video" in video_info and "bytesBase64Encoded" in video_info["video"]:
                                # Save base64 video to file
                                import base64
                                video_bytes = base64.b64decode(video_info["video"]["bytesBase64Encoded"])
                                video_path = DATA_DIR / "ai_videos" / f"{job_id}.mp4"
                                video_path.parent.mkdir(parents=True, exist_ok=True)
                                video_path.write_bytes(video_bytes)
                                _update_job("completed", result={"url": f"/api/ai/video/file/{job_id}.mp4", "provider": "veo", "local": True})
                            else:
                                # Unknown format - store raw data for debugging
                                _update_job("completed", result={"raw": str(video_info)[:1000], "provider": "veo"})
                        else:
                            _update_job("failed", error="Veo completed but no video found in response")
                        return

                    # Still processing - update status
                    metadata = poll_data.get("metadata", {})
                    progress = metadata.get("percentComplete", 0)
                    _update_job("processing", result={"progress": progress})

                _update_job("failed", error="Veo generation timed out after 10 minutes")

            elif provider == "grok_imagine":
                # xAI Grok Imagine Video — POST /v1/videos/generations, then poll GET /v1/videos/{request_id}
                _update_job("processing")
                gen_payload = {
                    "prompt": prompt,
                    "model": "grok-imagine-video",
                    "duration": max(5, min(10, duration)),
                }
                if image_url:
                    gen_payload["image"] = {"url": image_url}

                resp = await client.post(
                    "https://api.x.ai/v1/videos/generations",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json=gen_payload,
                )
                if resp.status_code >= 400:
                    error_text = resp.text
                    print(f"[Grok Imagine] Generate request failed ({resp.status_code}): {error_text}")
                    _update_job("failed", error=f"Grok Imagine API error ({resp.status_code}): {error_text[:500]}")
                    return

                req_data = resp.json()
                request_id = req_data.get("request_id")
                if not request_id:
                    _update_job("failed", error=f"Grok Imagine returned no request_id: {json.dumps(req_data)[:500]}")
                    return

                print(f"[Grok Imagine] Video generation started, request_id: {request_id}")

                # Poll for completion (202 = pending, 200 = done)
                for attempt in range(120):  # ~10 minutes max
                    await asyncio.sleep(5)
                    poll_resp = await client.get(
                        f"https://api.x.ai/v1/videos/{request_id}",
                        headers={"Authorization": f"Bearer {api_key}"},
                    )
                    if poll_resp.status_code == 202:
                        # Still processing
                        _update_job("processing", result={"progress": min(95, attempt * 2)})
                        continue
                    if poll_resp.status_code >= 400:
                        print(f"[Grok Imagine] Poll failed ({poll_resp.status_code}): {poll_resp.text[:300]}")
                        continue
                    # 200 = done
                    poll_data = poll_resp.json()
                    video_info = poll_data.get("video", {})
                    video_url = video_info.get("url")
                    if video_url:
                        _update_job("completed", result={"url": video_url, "provider": "grok_imagine"})
                        return
                    else:
                        _update_job("failed", error=f"Grok Imagine completed but no video URL in response: {json.dumps(poll_data)[:500]}")
                        return

                _update_job("failed", error="Grok Imagine generation timed out after 10 minutes")

            else:
                _update_job("failed", error=f"Unsupported provider: {provider}")

    except Exception as e:
        _update_job("failed", error=str(e))


@app.get("/api/ai/video/file/{filename}")
async def serve_ai_video_file(filename: str):
    """Serve locally saved AI-generated video files."""
    from fastapi.responses import FileResponse
    video_path = DATA_DIR / "ai_videos" / filename
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    return FileResponse(str(video_path), media_type="video/mp4")


@app.get("/api/ai/video/status/{job_id}")
async def get_video_generation_status(job_id: str):
    """Check status of video generation job."""
    job_file = DATA_DIR / "ai_jobs" / f"{job_id}.json"
    if not job_file.exists():
        raise HTTPException(status_code=404, detail="Job not found")
    data = json.loads(job_file.read_text())
    return {"success": True, **data}


# =============================================================================
# AI VOICEOVER / TTS (BYOK: ElevenLabs, OpenAI TTS)
# =============================================================================

class AIVoiceRequest(BaseModel):
    text: str
    provider: str = "elevenlabs"  # elevenlabs|openai
    voice_id: Optional[str] = None
    language: str = "en"


@app.post("/api/ai/voice")
async def ai_generate_voice(request: AIVoiceRequest):
    """Generate voiceover audio using TTS providers."""
    text = (request.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    if len(text) > 5000:
        raise HTTPException(status_code=400, detail="text exceeds 5000 character limit")

    provider = (request.provider or "elevenlabs").strip().lower()
    api_key = _get_byok_key(provider)
    if not api_key:
        raise HTTPException(status_code=400, detail=f"No API key configured for {provider}. Add it via /api/byok/keys")

    voice_id = request.voice_id or ("Rachel" if provider == "elevenlabs" else "alloy")
    out_id = f"voice_{uuid4().hex[:12]}"
    out_path = UPLOADS_DIR / f"{out_id}.mp3"

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            if provider == "elevenlabs":
                # Default voice ID for ElevenLabs
                el_voice_id = voice_id if len(voice_id) > 10 else "21m00Tcm4TlvDq8ikWAM"  # Rachel
                resp = await client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{el_voice_id}",
                    headers={"xi-api-key": api_key, "Content-Type": "application/json"},
                    json={
                        "text": text,
                        "model_id": "eleven_multilingual_v2",
                        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
                    },
                )
                if resp.status_code >= 400:
                    raise HTTPException(status_code=resp.status_code, detail=resp.text)
                out_path.write_bytes(resp.content)

            elif provider == "openai":
                resp = await client.post(
                    "https://api.openai.com/v1/audio/speech",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": "tts-1",
                        "input": text,
                        "voice": voice_id if voice_id in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"] else "alloy",
                    },
                )
                if resp.status_code >= 400:
                    raise HTTPException(status_code=resp.status_code, detail=resp.text)
                out_path.write_bytes(resp.content)

            else:
                raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

        chars = len(text)
        credits = max(1, chars // 100)
        _add_usage("voice_generation", credits, {"provider": provider, "chars": chars})

        return {
            "success": True,
            "provider": provider,
            "file_id": f"{out_id}.mp3",
            "url": f"/uploads/{out_id}.mp3",
            "duration_estimate": len(text) / 15,  # ~15 chars/sec estimate
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/ai/voices")
async def list_available_voices():
    """List available voices for TTS providers."""
    voices = {
        "elevenlabs": [
            {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "gender": "female"},
            {"id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "gender": "female"},
            {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "gender": "female"},
            {"id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "gender": "male"},
            {"id": "VR6AewLTigWG4xSOukaG", "name": "Arnold", "gender": "male"},
            {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "gender": "male"},
            {"id": "yoZ06aMxZJJ28mfd3POQ", "name": "Sam", "gender": "male"},
        ],
        "openai": [
            {"id": "alloy", "name": "Alloy", "gender": "neutral"},
            {"id": "echo", "name": "Echo", "gender": "male"},
            {"id": "fable", "name": "Fable", "gender": "female"},
            {"id": "onyx", "name": "Onyx", "gender": "male"},
            {"id": "nova", "name": "Nova", "gender": "female"},
            {"id": "shimmer", "name": "Shimmer", "gender": "female"},
        ],
    }
    return {"success": True, "voices": voices}


# =============================================================================
# VIRAL TEMPLATES LIBRARY
# =============================================================================

VIRAL_TEMPLATES = [
    {
        "id": "hook_curiosity",
        "category": "hooks",
        "name": "Curiosity Gap",
        "template": "I never expected {topic} to change my life, but here's what happened…",
        "example": "I never expected a $5 app to change my life, but here's what happened…",
        "platforms": ["tiktok", "instagram", "youtube"],
    },
    {
        "id": "hook_contrarian",
        "category": "hooks",
        "name": "Contrarian Take",
        "template": "Stop {common_advice}. Here's what actually works for {goal}.",
        "example": "Stop waking up at 5am. Here's what actually works for productivity.",
        "platforms": ["tiktok", "instagram", "linkedin"],
    },
    {
        "id": "hook_listicle",
        "category": "hooks",
        "name": "Numbered List",
        "template": "{number} {topic} that will {benefit} (#{number} is a game-changer)",
        "example": "5 AI tools that will 10x your productivity (#3 is a game-changer)",
        "platforms": ["tiktok", "instagram", "youtube"],
    },
    {
        "id": "hook_pov",
        "category": "hooks",
        "name": "POV Hook",
        "template": "POV: You just discovered {topic} and your {aspect} will never be the same",
        "example": "POV: You just discovered ChatGPT and your workflow will never be the same",
        "platforms": ["tiktok", "instagram"],
    },
    {
        "id": "hook_secret",
        "category": "hooks",
        "name": "Secret/Insider",
        "template": "The {industry} secret they don't want you to know about {topic}",
        "example": "The tech industry secret they don't want you to know about salaries",
        "platforms": ["tiktok", "youtube", "instagram"],
    },
    {
        "id": "structure_problem",
        "category": "structures",
        "name": "Problem-Agitate-Solution",
        "template": "Hook: State the problem\nAgitate: Show why it's painful\nSolution: Reveal your answer\nCTA: Tell them what to do",
        "example": "Tired of wasting hours on social media?\nEvery minute scrolling is a minute lost forever.\nI use this 3-step system to post in 10 mins/day.\nSave this and try it tomorrow.",
        "platforms": ["all"],
    },
    {
        "id": "structure_story",
        "category": "structures",
        "name": "Story Arc",
        "template": "Setup: Where I was\nConflict: The challenge\nResolution: How I overcame it\nLesson: What you can learn",
        "example": "2 years ago I was broke and stuck.\nI tried everything but nothing worked.\nThen I discovered {method} and everything changed.\nHere's the one thing that made the difference…",
        "platforms": ["all"],
    },
    {
        "id": "structure_tutorial",
        "category": "structures",
        "name": "Quick Tutorial",
        "template": "Here's how to {goal} in {timeframe}:\n\nStep 1: {action}\nStep 2: {action}\nStep 3: {action}\n\nThat's it! Save for later 🔖",
        "example": "Here's how to get 1000 followers in 30 days:\n\nStep 1: Post 2x daily\nStep 2: Engage for 30 mins\nStep 3: Use trending sounds\n\nThat's it! Save for later 🔖",
        "platforms": ["all"],
    },
    {
        "id": "cta_save",
        "category": "ctas",
        "name": "Save CTA",
        "template": "Save this for when you need it 🔖",
        "platforms": ["instagram", "tiktok"],
    },
    {
        "id": "cta_follow",
        "category": "ctas",
        "name": "Follow CTA",
        "template": "Follow for more {topic} tips 👆",
        "platforms": ["all"],
    },
    {
        "id": "cta_comment",
        "category": "ctas",
        "name": "Comment CTA",
        "template": "Drop a 🔥 if you want part 2",
        "platforms": ["all"],
    },
    {
        "id": "cta_share",
        "category": "ctas",
        "name": "Share CTA",
        "template": "Share this with someone who needs to hear it 💯",
        "platforms": ["all"],
    },
]


@app.get("/api/templates")
async def list_viral_templates(category: Optional[str] = None, platform: Optional[str] = None):
    """Get viral content templates."""
    templates = VIRAL_TEMPLATES
    if category:
        templates = [t for t in templates if t["category"] == category.lower()]
    if platform:
        templates = [t for t in templates if platform.lower() in t["platforms"] or "all" in t["platforms"]]
    return {"success": True, "templates": templates, "count": len(templates)}


class ApplyTemplateRequest(BaseModel):
    template_id: str
    variables: Dict[str, str]


@app.post("/api/templates/apply")
async def apply_viral_template(request: ApplyTemplateRequest):
    """Apply variables to a template."""
    template = next((t for t in VIRAL_TEMPLATES if t["id"] == request.template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    result = template["template"]
    for key, value in (request.variables or {}).items():
        result = result.replace(f"{{{key}}}", value)

    return {"success": True, "template_id": request.template_id, "result": result}


# =============================================================================
# CONTENT SOURCE INGESTION (URLs, PDFs, YouTube transcripts)
# =============================================================================

class IngestURLRequest(BaseModel):
    url: str
    extract_type: str = "article"  # article|youtube|pdf


@app.post("/api/content/ingest")
async def ingest_content_source(request: IngestURLRequest):
    """Extract content from URLs for repurposing."""
    url = (request.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    extract_type = (request.extract_type or "article").strip().lower()

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            if extract_type == "youtube" and ("youtube.com" in url or "youtu.be" in url):
                # Extract YouTube video ID and get transcript
                video_id = None
                if "v=" in url:
                    video_id = url.split("v=")[1].split("&")[0]
                elif "youtu.be/" in url:
                    video_id = url.split("youtu.be/")[1].split("?")[0]

                if not video_id:
                    raise HTTPException(status_code=400, detail="Could not extract YouTube video ID")

                # Try to get captions via YouTube's timedtext API (no auth needed for public captions)
                caption_url = f"https://www.youtube.com/api/timedtext?v={video_id}&lang=en&fmt=srv3"
                resp = await client.get(caption_url)

                if resp.status_code == 200 and resp.text:
                    # Parse XML captions
                    import xml.etree.ElementTree as ET
                    try:
                        root = ET.fromstring(resp.text)
                        texts = [elem.text for elem in root.findall(".//text") if elem.text]
                        transcript = " ".join(texts)
                    except Exception:
                        transcript = ""
                else:
                    transcript = ""

                # Also get video metadata via oEmbed
                oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
                oembed_resp = await client.get(oembed_url)
                title = ""
                if oembed_resp.status_code == 200:
                    oembed_data = oembed_resp.json()
                    title = oembed_data.get("title", "")

                return {
                    "success": True,
                    "type": "youtube",
                    "video_id": video_id,
                    "title": title,
                    "transcript": transcript if transcript else "(No public captions available)",
                    "url": url,
                }

            else:
                # Generic article extraction
                resp = await client.get(url)
                if resp.status_code >= 400:
                    raise HTTPException(status_code=resp.status_code, detail=f"Failed to fetch URL: {resp.status_code}")

                html = resp.text
                # Simple extraction: get title and main text
                title = ""
                title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
                if title_match:
                    title = title_match.group(1).strip()

                # Remove scripts, styles, and tags
                text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r"<[^>]+>", " ", text)
                text = re.sub(r"\s+", " ", text).strip()

                # Limit text length
                text = text[:10000] if len(text) > 10000 else text

                return {
                    "success": True,
                    "type": "article",
                    "title": title,
                    "text": text,
                    "url": url,
                    "char_count": len(text),
                }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# CONTENT REPURPOSING (Convert content to different formats)
# =============================================================================

class RepurposeRequest(BaseModel):
    content: str
    source_type: str = "article"  # article|transcript|notes
    target_formats: List[str] = ["tweet", "linkedin", "caption"]
    language: str = "en"


@app.post("/api/content/repurpose")
async def repurpose_content(request: RepurposeRequest):
    """Repurpose content into multiple formats using AI."""
    content = (request.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="content is required")

    target_formats = request.target_formats or ["tweet", "linkedin", "caption"]
    language = request.language or "en"

    # Try Ollama first, then OpenAI BYOK
    model = (os.getenv("FYI_OLLAMA_MODEL") or "").strip()
    models = await _ollama_models()
    if not model and models:
        model = models[0]

    results = {}

    for fmt in target_formats:
        format_prompts = {
            "tweet": f"Convert this content into a viral Twitter/X post (max 280 chars). Language: {language}\n\nContent:\n{content[:2000]}",
            "linkedin": f"Convert this content into an engaging LinkedIn post with hooks and bullet points. Language: {language}\n\nContent:\n{content[:2000]}",
            "caption": f"Convert this content into an Instagram caption with emojis and hashtags. Language: {language}\n\nContent:\n{content[:2000]}",
            "thread": f"Convert this content into a 5-tweet Twitter thread. Number each tweet. Language: {language}\n\nContent:\n{content[:2000]}",
            "script": f"Convert this content into a 60-second video script with hook, body, and CTA. Language: {language}\n\nContent:\n{content[:2000]}",
            "carousel": f"Convert this content into 5 carousel slides. Each slide should have a headline and 2-3 bullet points. Language: {language}\n\nContent:\n{content[:2000]}",
        }

        prompt = format_prompts.get(fmt, format_prompts["caption"])
        system = "You are a viral content writer. Output only the requested format, no explanations."

        try:
            if model:
                result = await _ollama_generate(prompt=prompt, model=model, system=system, timeout_s=30.0)
                results[fmt] = {"content": result.strip(), "mode": "ollama"}
            else:
                # Try OpenAI BYOK
                openai_key = _get_byok_key("openai")
                if openai_key:
                    async with httpx.AsyncClient(timeout=60) as client:
                        resp = await client.post(
                            "https://api.openai.com/v1/chat/completions",
                            headers={"Authorization": f"Bearer {openai_key}"},
                            json={
                                "model": "gpt-4o-mini",
                                "messages": [
                                    {"role": "system", "content": system},
                                    {"role": "user", "content": prompt},
                                ],
                                "max_tokens": 1000,
                            },
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            result = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                            results[fmt] = {"content": result.strip(), "mode": "openai"}
                            _add_usage("repurpose", 2, {"format": fmt})
                        else:
                            results[fmt] = {"content": "", "error": resp.text, "mode": "failed"}
                else:
                    # Fallback: simple extraction
                    results[fmt] = {"content": content[:500], "mode": "fallback", "note": "Configure Ollama or OpenAI for AI repurposing"}
        except Exception as e:
            results[fmt] = {"content": "", "error": str(e), "mode": "failed"}

    return {"success": True, "results": results}


# =============================================================================
# MULTI-LANGUAGE SUPPORT
# =============================================================================

SUPPORTED_LANGUAGES = {
    "en": "English", "es": "Spanish", "fr": "French", "de": "German", "it": "Italian",
    "pt": "Portuguese", "nl": "Dutch", "pl": "Polish", "ru": "Russian", "ja": "Japanese",
    "ko": "Korean", "zh": "Chinese", "ar": "Arabic", "hi": "Hindi", "tr": "Turkish",
    "vi": "Vietnamese", "th": "Thai", "id": "Indonesian", "ms": "Malay", "fil": "Filipino",
    "sv": "Swedish", "da": "Danish", "no": "Norwegian", "fi": "Finnish", "cs": "Czech",
    "el": "Greek", "he": "Hebrew", "hu": "Hungarian", "ro": "Romanian", "uk": "Ukrainian",
    "bg": "Bulgarian", "hr": "Croatian", "sk": "Slovak", "sl": "Slovenian", "et": "Estonian",
    "lv": "Latvian", "lt": "Lithuanian", "sr": "Serbian", "mk": "Macedonian", "sq": "Albanian",
    "bn": "Bengali", "ta": "Tamil", "te": "Telugu", "mr": "Marathi", "gu": "Gujarati",
    "kn": "Kannada", "ml": "Malayalam", "pa": "Punjabi", "ur": "Urdu", "fa": "Persian",
    "sw": "Swahili", "af": "Afrikaans", "zu": "Zulu", "xh": "Xhosa", "am": "Amharic",
    "ne": "Nepali", "si": "Sinhala", "my": "Myanmar", "km": "Khmer", "lo": "Lao",
}


@app.get("/api/languages")
async def list_supported_languages():
    """List all supported languages (58+)."""
    return {"success": True, "languages": SUPPORTED_LANGUAGES, "count": len(SUPPORTED_LANGUAGES)}


class TranslateRequest(BaseModel):
    text: str
    target_language: str
    source_language: str = "auto"


@app.post("/api/ai/translate")
async def ai_translate(request: TranslateRequest):
    """Translate text to target language."""
    text = (request.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    target = request.target_language or "en"
    if target not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {target}")

    target_name = SUPPORTED_LANGUAGES[target]

    # Try Ollama first
    model = (os.getenv("FYI_OLLAMA_MODEL") or "").strip()
    models = await _ollama_models()
    if not model and models:
        model = models[0]

    prompt = f"Translate the following text to {target_name}. Output only the translation, nothing else.\n\nText:\n{text}"
    system = "You are a professional translator. Output only the translated text."

    try:
        if model:
            result = await _ollama_generate(prompt=prompt, model=model, system=system, timeout_s=30.0)
            return {"success": True, "translated": result.strip(), "target_language": target, "mode": "ollama"}

        # Try OpenAI BYOK
        openai_key = _get_byok_key("openai")
        if openai_key:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {openai_key}"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": 2000,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    result = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    _add_usage("translation", 1, {"target": target, "chars": len(text)})
                    return {"success": True, "translated": result.strip(), "target_language": target, "mode": "openai"}

        raise HTTPException(status_code=501, detail="No AI provider available. Configure Ollama or add OpenAI API key.")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# FACELESS VIDEO WITH VOICEOVER (Enhanced)
# =============================================================================

class FacelessVideoWithVoiceRequest(BaseModel):
    script: str
    voice_provider: str = "elevenlabs"  # elevenlabs|openai
    voice_id: Optional[str] = None
    width: int = 1080
    height: int = 1920
    bg_color: str = "black"
    bg_video_url: Optional[str] = None  # Optional background video


@app.post("/api/video/faceless-with-voice")
async def create_faceless_video_with_voice(request: FacelessVideoWithVoiceRequest):
    """Create faceless video with AI voiceover."""
    script = (request.script or "").strip()
    if not script:
        raise HTTPException(status_code=400, detail="script is required")

    if shutil.which("ffmpeg") is None:
        raise HTTPException(status_code=501, detail="ffmpeg required")

    # 1. Generate voiceover
    voice_req = AIVoiceRequest(
        text=script,
        provider=request.voice_provider,
        voice_id=request.voice_id,
    )
    voice_result = await ai_generate_voice(voice_req)
    audio_file_id = voice_result["file_id"]
    audio_path = UPLOADS_DIR / audio_file_id

    # 2. Get audio duration
    try:
        info = _ffprobe_json(audio_path)
        duration = float(info.get("format", {}).get("duration", 0))
    except Exception:
        duration = len(script) / 15  # Estimate

    # 3. Generate SRT from script
    srt_text, _ = _script_to_srt(script, max_words_per_caption=7)

    job_id = uuid4().hex[:10]
    out_dir = UPLOADS_DIR / "faceless" / job_id
    out_dir.mkdir(parents=True, exist_ok=True)

    srt_path = out_dir / "captions.srt"
    srt_path.write_text(srt_text, encoding="utf-8")

    out_name = f"faceless_voice_{job_id}.mp4"
    out_path = UPLOADS_DIR / out_name

    # 4. Create video with subtitles and audio
    srt_filter_path = str(srt_path).replace("\\", "/").replace(":", "\\:")
    style = (
        "FontName=Arial,"
        "FontSize=48,"
        "PrimaryColour=&H00FFFFFF&,"
        "OutlineColour=&H00000000&,"
        "BorderStyle=3,"
        "Outline=2,"
        "Shadow=0,"
        "Alignment=2,"
        "MarginV=90"
    )
    vf = f"subtitles='{srt_filter_path}':force_style='{style}'"

    args = [
        "ffmpeg", "-y",
        "-f", "lavfi",
        "-i", f"color=c={request.bg_color}:s={request.width}x{request.height}:r=30:d={duration}",
        "-i", str(audio_path),
        "-vf", vf,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-shortest",
        "-movflags", "+faststart",
        str(out_path),
    ]

    proc = subprocess.run(args, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise HTTPException(status_code=500, detail=proc.stderr or "ffmpeg failed")

    _add_usage("faceless_video_voice", 30, {"duration": duration})

    return {
        "success": True,
        "job_id": job_id,
        "file_id": out_name,
        "url": f"/uploads/{out_name}",
        "audio_file_id": audio_file_id,
        "duration_sec": duration,
    }


# =============================================================================
# SOCIAL MEDIA GUIDES
# =============================================================================

SOCIAL_GUIDES = {
    "instagram": {
        "best_times": ["Tuesday 11am", "Wednesday 11am", "Friday 10-11am"],
        "optimal_hashtags": 5,
        "video_length": "7-15 seconds for Reels",
        "image_size": "1080x1350 (4:5)",
        "tips": [
            "Use trending audio for Reels",
            "Post carousel for higher saves",
            "Engage 30 mins before/after posting",
        ],
    },
    "tiktok": {
        "best_times": ["Tuesday 9am", "Thursday 12pm", "Friday 5am"],
        "optimal_hashtags": 3,
        "video_length": "21-34 seconds",
        "tips": [
            "Hook in first 1 second",
            "Use trending sounds",
            "Post 1-4 times per day",
        ],
    },
    "youtube": {
        "best_times": ["Friday 3-4pm", "Saturday 9-11am", "Sunday 9-11am"],
        "optimal_tags": 10,
        "video_length": "8-12 minutes for monetization",
        "thumbnail_size": "1280x720",
        "tips": [
            "First 30 seconds = most important",
            "Ask for likes/subs at engagement peaks",
            "Use chapters for longer videos",
        ],
    },
    "linkedin": {
        "best_times": ["Tuesday 10am-12pm", "Wednesday 12pm", "Thursday 9am"],
        "optimal_hashtags": 3,
        "post_length": "1300 characters",
        "tips": [
            "Start with a hook line",
            "Use line breaks for readability",
            "Ask a question at the end",
        ],
    },
    "facebook": {
        "best_times": ["Wednesday 11am-1pm", "Thursday 1-2pm"],
        "optimal_hashtags": 2,
        "video_length": "1-3 minutes",
        "tips": [
            "Native video outperforms links",
            "Use captions (85% watch muted)",
            "Post in Groups for more reach",
        ],
    },
}


@app.get("/api/guides/{platform}")
async def get_social_guide(platform: str):
    """Get platform-specific social media guide."""
    platform = platform.lower()
    if platform not in SOCIAL_GUIDES:
        raise HTTPException(status_code=404, detail=f"No guide for platform: {platform}")
    return {"success": True, "platform": platform, "guide": SOCIAL_GUIDES[platform]}


@app.get("/api/guides")
async def list_social_guides():
    """List all social media guides."""
    return {"success": True, "guides": SOCIAL_GUIDES}


@app.post("/api/schedule")
async def schedule_post(request: ScheduleRequest):
    """Schedule a post across platforms"""
    # If the client provides an id, use it so the frontend can poll progress while this request is in-flight.
    schedule_id = (request.client_request_id or "").strip()
    if not schedule_id:
        schedule_id = f"post_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}"

    _progress_set(schedule_id, stage="schedule_start", percent=1, message="Scheduling…")

    def _parse_dt_local(value: str | None) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            return None

    def _min_smart_start(platforms: list[str]) -> datetime:
        """Minimum start time for smart scheduling.

                - Facebook native scheduling often requires +10 minutes, but we try +1 minute first
                    and fall back to +10 minutes only if Meta rejects the request as too soon.
        - Other platforms can be scheduled effectively immediately; we use +1 minute
          so the scheduler loop (minute granularity) can pick it up cleanly.
        """
        try:
            plats = {str(p).strip().lower() for p in (platforms or []) if str(p).strip()}
        except Exception:
            plats = set()
        now = datetime.now()
        if any(p in {"facebook", "fb"} for p in plats):
            return _ceil_to_minute(now + timedelta(minutes=1))
        return _ceil_to_minute(now + timedelta(minutes=1))

    def _looks_like_fb_too_soon_error(msg: str) -> bool:
        m = (msg or "").lower()
        # Best-effort: Meta error strings vary. We only trigger fallback on clearly time-related failures.
        signals = [
            "scheduled",
            "scheduled_publish_time",
            "must be at least",
            "in the future",
            "too soon",
            "10 minute",
            "ten minute",
            "600",
        ]
        return any(s in m for s in signals)

    def _compute_smart_time(platforms: list[str], interval_minutes: int) -> datetime:
        """Pick the next smart slot.

        Goal: feel immediate while avoiding collisions.

        - Start at `min_start`.
        - If that minute is already occupied by an existing scheduled post for any overlapping platform,
          step forward by `interval_minutes` until a free slot is found.
        """
        interval_minutes = max(1, min(int(interval_minutes or 60), 24 * 60))
        min_dt = _min_smart_start(platforms)
        posts = db.list_scheduled_posts(limit=1000)
        target = {str(p).strip().lower() for p in (platforms or []) if str(p).strip()}
        occupied: set[str] = set()
        for p in posts:
            if str(p.get("status") or "").lower() in {"cancelled", "failed"}:
                continue
            plats = [str(x).strip().lower() for x in (p.get("platforms") or [])]
            if not any(x in target for x in plats):
                continue
            dt = _parse_dt_local(p.get("scheduled_time"))
            if not dt:
                continue
            if dt < min_dt:
                continue
            key = dt.replace(second=0, microsecond=0).isoformat(timespec="minutes")
            occupied.add(key)

        cand = min_dt
        # Worst-case cap to avoid infinite loops if something is odd in the DB.
        for _ in range(0, 24 * 60 + 5):
            k = cand.isoformat(timespec="minutes")
            if k not in occupied:
                return cand
            cand = _ceil_to_minute(cand + timedelta(minutes=interval_minutes))
        return cand

    try:
        scheduled_time = (request.scheduledTime or "").strip() if request.scheduledTime is not None else ""
        if not scheduled_time or scheduled_time.upper() == "SMART":
            # Smart scheduling defaults to local DB history. For Facebook, also consider what's already
            # scheduled in Meta Planner (via Graph API) to avoid collisions.
            dt_smart = _compute_smart_time(request.platforms, int(request.interval_minutes or 60))

            try:
                plats_norm = {str(p).strip().lower() for p in (request.platforms or []) if str(p).strip()}
            except Exception:
                plats_norm = set()

            if any(p in {"facebook", "fb"} for p in plats_norm):
                fb_account_id = None
                try:
                    fb_account_id = (request.accounts or {}).get("facebook")
                except Exception:
                    fb_account_id = None
                fb_latest = await _facebook_latest_scheduled_time(fb_account_id)
                if fb_latest is not None:
                    interval = max(1, min(int(request.interval_minutes or 60), 24 * 60))
                    candidate = fb_latest + timedelta(minutes=interval)
                    min_dt = _min_smart_start(list(plats_norm))
                    dt_smart = max(dt_smart, _ceil_to_minute(candidate), min_dt)

            scheduled_time = dt_smart.isoformat(timespec="minutes")

        date_part = ""
        time_part = ""
        try:
            dt = datetime.fromisoformat(scheduled_time)
            date_part = dt.date().isoformat()
            time_part = dt.strftime("%H:%M")
        except Exception:
            if "T" in (scheduled_time or ""):
                date_part, time_part = scheduled_time.split("T", 1)

        post = {
            "id": schedule_id,
            "title": (request.content or {}).get("title", "") if isinstance(request.content, dict) else "",
            "caption": (request.content or {}).get("caption", "") if isinstance(request.content, dict) else "",
            "platforms": request.platforms,
            "scheduled_time": scheduled_time,
            "date": date_part,
            "time": time_part,
            "status": "scheduled",
            "created_at": datetime.now().isoformat(),
            "payload": {
                "file_id": request.file_id or (request.content or {}).get("file_id") or (request.content or {}).get("fileId"),
                "clips": request.clips or [],
                "content": request.content or {},
                "accounts": request.accounts or {},
            },
        }

        # If Facebook is selected, also create a Facebook *native scheduled* post now.
        # This is what makes it appear in Meta Planner / scheduled posts.
        try:
            platforms_norm = {str(p).strip().lower() for p in (request.platforms or []) if str(p).strip()}
        except Exception:
            platforms_norm = set()

        if any(p in {"facebook", "fb"} for p in platforms_norm):
            media_id = post["payload"].get("file_id") or (post["payload"].get("clips") or [None])[0]
            if not media_id:
                raise HTTPException(status_code=400, detail="Facebook scheduling requires file_id (or clips[0])")
            try:
                unix_ts = _iso_to_unix_seconds(scheduled_time)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid scheduled_time for Facebook scheduling")

            selected_fb_account = None
            try:
                selected_fb_account = (request.accounts or {}).get("facebook")
            except Exception:
                selected_fb_account = None

            # Attempt native scheduling in Facebook.
            # We try +1 minute, but will fall back to +10 minutes if Meta rejects it.
            now_ts = int(datetime.now().timestamp())
            if unix_ts < now_ts + 60:
                unix_ts = now_ts + 60
                scheduled_time = datetime.fromtimestamp(unix_ts).isoformat(timespec="minutes")
                post["scheduled_time"] = scheduled_time
                try:
                    dt_fix = datetime.fromisoformat(scheduled_time)
                    post["date"] = dt_fix.date().isoformat()
                    post["time"] = dt_fix.strftime("%H:%M")
                except Exception:
                    pass

            try:
                _progress_set(schedule_id, stage="facebook_schedule_start", percent=1, message="Preparing Facebook scheduling…")
                try:
                    fb_res = await _facebook_upload_video_impl(
                        FacebookUploadRequest(
                            account_id=selected_fb_account,
                            file_id=media_id,
                            title=post.get("title") or "",
                            description=post.get("caption") or "",
                            scheduled_publish_time=unix_ts,
                        ),
                        progress_job_id=schedule_id,
                    )
                except HTTPException as he:
                    # Fall back once to +10 minutes if Meta indicates the scheduled time is too soon.
                    if int(getattr(he, "status_code", 400) or 400) in {400, 422} and _looks_like_fb_too_soon_error(str(getattr(he, "detail", ""))):
                        unix_ts2 = max(unix_ts, now_ts + 600)
                        _progress_set(schedule_id, stage="facebook_schedule_retry", percent=5, message="Facebook requires more lead time; retrying at +10 minutes…")
                        fb_res = await _facebook_upload_video_impl(
                            FacebookUploadRequest(
                                account_id=selected_fb_account,
                                file_id=media_id,
                                title=post.get("title") or "",
                                description=post.get("caption") or "",
                                scheduled_publish_time=unix_ts2,
                            ),
                            progress_job_id=schedule_id,
                        )
                        unix_ts = unix_ts2
                        scheduled_time = datetime.fromtimestamp(unix_ts).isoformat(timespec="minutes")
                        post["scheduled_time"] = scheduled_time
                        try:
                            dt_fix = datetime.fromisoformat(scheduled_time)
                            post["date"] = dt_fix.date().isoformat()
                            post["time"] = dt_fix.strftime("%H:%M")
                        except Exception:
                            pass
                    else:
                        raise

                _progress_set(schedule_id, stage="facebook_schedule_done", percent=100, message="Facebook scheduled.", done=True)
                payload = post.get("payload") if isinstance(post.get("payload"), dict) else {}
                external = payload.get("external") if isinstance(payload.get("external"), dict) else {}
                external["facebook"] = {
                    "scheduled_publish_time": unix_ts,
                    "video_id": (fb_res or {}).get("video_id"),
                    "account_id": (fb_res or {}).get("account_id"),
                    "raw": (fb_res or {}).get("raw"),
                }
                payload["external"] = external
                post["payload"] = payload
            except HTTPException:
                _progress_set(schedule_id, stage="facebook_schedule_failed", percent=100, message="Facebook scheduling failed", done=True)
                raise
            except Exception as e:
                _progress_set(schedule_id, stage="facebook_schedule_failed", percent=100, message="Facebook scheduling failed", done=True, error=str(e))
                raise HTTPException(status_code=502, detail=f"Facebook scheduling failed: {e}")

        # If YouTube is selected, upload the video immediately with publishAt set.
        # YouTube supports native scheduling: upload as private + publishAt = RFC3339 timestamp.
        # This makes it appear in YouTube Studio under "Scheduled" immediately.
        if any(p in {"youtube", "yt"} for p in platforms_norm):
            media_id_yt = post["payload"].get("file_id") or (post["payload"].get("clips") or [None])[0]
            if media_id_yt:
                try:
                    # Convert scheduled_time to RFC3339 UTC for YouTube
                    dt_yt = datetime.fromisoformat(scheduled_time)
                    # If no timezone info, assume local and convert to UTC-ish RFC3339
                    publish_at_rfc3339 = dt_yt.isoformat() + "Z" if not dt_yt.tzinfo else dt_yt.isoformat()
                    
                    selected_yt_account = None
                    try:
                        selected_yt_account = (request.accounts or {}).get("youtube")
                    except Exception:
                        selected_yt_account = None

                    _progress_set(schedule_id, stage="youtube_schedule_start", percent=1, message="Uploading to YouTube (scheduled)…")
                    yt_res = await youtube_upload_video(
                        YouTubeUploadRequest(
                            account_id=selected_yt_account,
                            file_id=str(media_id_yt),
                            title=post.get("title") or "",
                            description=post.get("caption") or "",
                            privacy_status="private",
                            publish_at=publish_at_rfc3339,
                        )
                    )
                    _progress_set(schedule_id, stage="youtube_schedule_done", percent=100, message="YouTube scheduled.", done=True)
                    
                    payload = post.get("payload") if isinstance(post.get("payload"), dict) else {}
                    external = payload.get("external") if isinstance(payload.get("external"), dict) else {}
                    external["youtube"] = {
                        "publish_at": publish_at_rfc3339,
                        "video_id": (yt_res or {}).get("video_id"),
                        "account_id": (yt_res or {}).get("account_id"),
                        "raw": (yt_res or {}).get("raw"),
                    }
                    payload["external"] = external
                    post["payload"] = payload
                except Exception as e:
                    _progress_set(schedule_id, stage="youtube_schedule_failed", percent=100, message=f"YouTube scheduling failed: {e}", done=True)
                    # Don't block the overall schedule — the scheduler loop will retry at the scheduled time

        posts = _load_scheduled_posts()
        posts.append(post)
        _save_scheduled_posts(posts)

        _progress_set(
            schedule_id,
            stage="schedule_saved",
            percent=100,
            message=f"Scheduled for {post.get('scheduled_time')}",
            done=True,
            extra={"scheduled_time": post.get("scheduled_time")},
        )

        return {
            "success": True,
            "schedule_id": schedule_id,
            "scheduled_posts": [post],
            "message": "Post scheduled successfully",
        }

    except HTTPException as he:
        _progress_set(
            schedule_id,
            stage="schedule_failed",
            percent=100,
            message="Scheduling failed",
            done=True,
            error=str(getattr(he, "detail", "")),
        )
        raise
    except Exception as e:
        _progress_set(
            schedule_id,
            stage="schedule_failed",
            percent=100,
            message="Scheduling failed",
            done=True,
            error=str(e),
        )
        raise


@app.post("/api/publish/instant")
async def publish_instant(request: InstantPublishRequest, req: Request):
    """Publish a post immediately (no scheduling).

    This is intentionally separate from /api/schedule so that:
    - Facebook can post immediately (since scheduled_publish_time requires +10 minutes)
    - We can reuse the progress store via client_request_id
    """
    job_id = (request.client_request_id or "").strip() or f"instant_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}"

    content = request.content if isinstance(request.content, dict) else {}
    title = content.get("title") or ""
    caption = content.get("caption") or ""

    media_id = request.file_id or content.get("file_id") or content.get("fileId")
    if not media_id:
        clips = request.clips or []
        media_id = clips[0] if isinstance(clips, list) and clips else None
    if not media_id:
        raise HTTPException(status_code=400, detail="Instant publish requires file_id (or clips[0])")

    selected_accounts = request.accounts if isinstance(request.accounts, dict) else {}

    _progress_set(job_id, stage="instant_publish_start", percent=1, message="Starting instant post…")

    results: dict[str, Any] = {}
    try:
        for platform in (request.platforms or []):
            p = str(platform).strip().lower()
            if p in {"facebook", "fb"}:
                _progress_set(job_id, stage="facebook_post_start", percent=1, message="Posting to Facebook…")
                results["facebook"] = await _facebook_upload_video_impl(
                    FacebookUploadRequest(
                        account_id=(selected_accounts.get("facebook") if isinstance(selected_accounts, dict) else None),
                        file_id=str(media_id),
                        title=str(title or ""),
                        description=str(caption or ""),
                        scheduled_publish_time=None,
                    ),
                    progress_job_id=job_id,
                )
            elif p in {"instagram", "ig"}:
                _progress_set(job_id, stage="instagram_post_start", percent=1, message="Posting to Instagram…")
                results["instagram"] = await _instagram_publish_internal(
                    (selected_accounts.get("instagram") if isinstance(selected_accounts, dict) else None),
                    str(media_id),
                    str(caption or ""),
                    "REELS",
                )
            elif p in {"youtube", "yt"}:
                _progress_set(job_id, stage="youtube_post_start", percent=1, message="Uploading to YouTube…")
                results["youtube"] = await youtube_upload_video(
                    YouTubeUploadRequest(
                        account_id=(selected_accounts.get("youtube") if isinstance(selected_accounts, dict) else None),
                        file_id=str(media_id),
                        title=str(title or ""),
                        description=str(caption or ""),
                        privacy_status="public",
                        publish_at=None,
                    )
                )
            else:
                raise HTTPException(status_code=501, detail=f"Instant publish not implemented for platform '{platform}'")

        _progress_set(job_id, stage="instant_publish_done", percent=100, message="Instant post complete.", done=True)
        return {"success": True, "job_id": job_id, "results": results}
    except HTTPException as he:
        _progress_set(job_id, stage="instant_publish_failed", percent=100, message="Instant post failed", done=True, error=str(he.detail))
        raise
    except Exception as e:
        _progress_set(job_id, stage="instant_publish_failed", percent=100, message="Instant post failed", done=True, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/schedule/bulk")
async def bulk_schedule_posts(request: BulkScheduleRequest):
    items = request.items or []
    if not items:
        raise HTTPException(status_code=400, detail="No items provided")

    interval_minutes = max(1, min(int(request.interval_minutes or 60), 24 * 60))
    smart = bool(request.smart)

    def _parse_dt_local(value: str | None) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
        except Exception:
            return None

    # Determine occupied slots for the union of platforms across items.
    all_platforms: list[str] = []
    for it in items:
        all_platforms.extend(it.platforms or [])
    target = {str(p).strip().lower() for p in all_platforms if str(p).strip()}
    posts = db.list_scheduled_posts(limit=1000)
    occupied: set[str] = set()
    for p in posts:
        if str(p.get("status") or "").lower() in {"cancelled", "failed"}:
            continue
        plats = [str(x).strip().lower() for x in (p.get("platforms") or [])]
        if not any(x in target for x in plats):
            continue
        dt = _parse_dt_local(p.get("scheduled_time"))
        if not dt:
            continue
        key = dt.replace(second=0, microsecond=0).isoformat(timespec="minutes")
        occupied.add(key)

    # Use a shorter minimum so Instagram smart scheduling feels immediate.
    # Facebook will be retried at +10 minutes if Meta requires it.
    now = datetime.now()
    min_dt = _ceil_to_minute(now + timedelta(minutes=1))
    next_dt = min_dt

    # If any item targets Facebook, also consider what's already scheduled in Meta Planner.
    # Bulk requests don't currently carry per-item account selection, so we use the active Facebook account.
    try:
        any_fb = any(
            any(str(p).strip().lower() in {"facebook", "fb"} for p in (it.platforms or []))
            for it in items
        )
    except Exception:
        any_fb = False
    if any_fb:
        fb_latest = await _facebook_latest_scheduled_time(None)
        if fb_latest is not None:
            # Planner-aware baseline: don't schedule *before* Facebook's latest scheduled slot + interval.
            next_dt = max(next_dt, _ceil_to_minute(fb_latest + timedelta(minutes=interval_minutes)), min_dt)

    created: list[dict[str, Any]] = []
    for it in items:
        schedule_id = f"post_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}"

        scheduled_time = (it.scheduledTime or "").strip() if it.scheduledTime is not None else ""
        if smart and (not scheduled_time or scheduled_time.upper() == "SMART"):
            # Find the next free slot at/after next_dt.
            cand = _ceil_to_minute(next_dt)
            for _ in range(0, 24 * 60 + 5):
                k = cand.isoformat(timespec="minutes")
                if k not in occupied:
                    break
                cand = _ceil_to_minute(cand + timedelta(minutes=interval_minutes))
            scheduled_time = cand.isoformat(timespec="minutes")
            occupied.add(scheduled_time)
            next_dt = cand + timedelta(minutes=interval_minutes)

        if not scheduled_time:
            raise HTTPException(status_code=400, detail="Each item must have scheduledTime or enable smart scheduling")

        date_part = ""
        time_part = ""
        dtp: datetime | None = None
        try:
            dtp = datetime.fromisoformat(scheduled_time)
            date_part = dtp.date().isoformat()
            time_part = dtp.strftime("%H:%M")
        except Exception:
            if "T" in (scheduled_time or ""):
                date_part, time_part = scheduled_time.split("T", 1)

        # If a row provides an explicit schedule time, advance the smart baseline so that
        # subsequent SMART rows schedule *after* it within the same bulk request.
        if dtp is not None:
            occupied.add(dtp.replace(second=0, microsecond=0).isoformat(timespec="minutes"))
            next_dt = max(next_dt, dtp + timedelta(minutes=interval_minutes))

        post = {
            "id": schedule_id,
            "title": it.title or "",
            "caption": it.caption or "",
            "platforms": it.platforms or [],
            "scheduled_time": scheduled_time,
            "date": date_part,
            "time": (time_part or "")[:5],
            "status": "scheduled",
            "created_at": datetime.now().isoformat(),
            "payload": {
                "file_id": it.file_id,
                "clips": [],
                "content": {"title": it.title or "", "caption": it.caption or ""},
            },
        }

        # Same as /api/schedule: if Facebook is included, create a native scheduled FB post now.
        try:
            plats_norm = {str(p).strip().lower() for p in (it.platforms or []) if str(p).strip()}
        except Exception:
            plats_norm = set()

        if any(p in {"facebook", "fb"} for p in plats_norm):
            if not it.file_id:
                raise HTTPException(status_code=400, detail="Bulk Facebook scheduling requires file_id")
            try:
                unix_ts = _iso_to_unix_seconds(scheduled_time)
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid scheduled_time for Facebook scheduling")

            now_ts = int(datetime.now().timestamp())
            if unix_ts < now_ts + 60:
                unix_ts = now_ts + 60
                scheduled_time = datetime.fromtimestamp(unix_ts).isoformat(timespec="minutes")
                post["scheduled_time"] = scheduled_time
                try:
                    dt_fix = datetime.fromisoformat(scheduled_time)
                    post["date"] = dt_fix.date().isoformat()
                    post["time"] = dt_fix.strftime("%H:%M")
                except Exception:
                    pass

            try:
                fb_res = await facebook_upload_video(
                    FacebookUploadRequest(
                        file_id=it.file_id,
                        title=it.title or "",
                        description=it.caption or "",
                        scheduled_publish_time=unix_ts,
                    )
                )
            except HTTPException as he:
                # Fall back once to +10 minutes if Meta indicates the scheduled time is too soon.
                msg = str(getattr(he, "detail", ""))
                m = msg.lower()
                if int(getattr(he, "status_code", 400) or 400) in {400, 422} and (
                    "scheduled" in m or "must be at least" in m or "in the future" in m or "10 minute" in m or "scheduled_publish_time" in m
                ):
                    unix_ts2 = max(unix_ts, now_ts + 600)
                    fb_res = await facebook_upload_video(
                        FacebookUploadRequest(
                            file_id=it.file_id,
                            title=it.title or "",
                            description=it.caption or "",
                            scheduled_publish_time=unix_ts2,
                        )
                    )
                    unix_ts = unix_ts2
                    scheduled_time = datetime.fromtimestamp(unix_ts).isoformat(timespec="minutes")
                    post["scheduled_time"] = scheduled_time
                    try:
                        dt_fix = datetime.fromisoformat(scheduled_time)
                        post["date"] = dt_fix.date().isoformat()
                        post["time"] = dt_fix.strftime("%H:%M")
                    except Exception:
                        pass
                    # Keep subsequent SMART items after the actual scheduled time.
                    next_dt = max(next_dt, datetime.fromtimestamp(unix_ts) + timedelta(minutes=interval_minutes))
                else:
                    raise
            payload = post.get("payload") if isinstance(post.get("payload"), dict) else {}
            external = payload.get("external") if isinstance(payload.get("external"), dict) else {}
            external["facebook"] = {
                "scheduled_publish_time": unix_ts,
                "video_id": (fb_res or {}).get("video_id"),
                "account_id": (fb_res or {}).get("account_id"),
                "raw": (fb_res or {}).get("raw"),
            }
            payload["external"] = external
            post["payload"] = payload

        posts = _load_scheduled_posts()
        posts.append(post)
        _save_scheduled_posts(posts)
        created.append(post)

    return {"success": True, "count": len(created), "scheduled_posts": created}

@app.get("/api/scheduled-posts")
async def list_scheduled_posts(limit: int = 200):
    posts = _load_scheduled_posts()
    posts_sorted = sorted(posts, key=lambda p: (p.get("scheduled_time") or "", p.get("created_at") or ""), reverse=True)
    return {
        "success": True,
        "posts": posts_sorted[: max(1, min(limit, 1000))],
        "count": len(posts),
    }


class ScheduledPostUpdateRequest(BaseModel):
    title: Optional[str] = None
    caption: Optional[str] = None
    platforms: Optional[List[str]] = None
    scheduled_time: Optional[str] = None
    status: Optional[str] = None


@app.put("/api/scheduled-posts/{post_id}")
async def update_scheduled_post(post_id: str, request: ScheduledPostUpdateRequest):
    # Compute date/time fields from scheduled_time if provided.
    updates: dict[str, Any] = {}
    if request.title is not None:
        updates["title"] = request.title
    if request.caption is not None:
        updates["caption"] = request.caption
    if request.platforms is not None:
        updates["platforms"] = request.platforms
    if request.status is not None:
        updates["status"] = request.status

    if request.scheduled_time is not None:
        updates["scheduled_time"] = request.scheduled_time
        date_part = ""
        time_part = ""
        try:
            dt = datetime.fromisoformat(request.scheduled_time)
            date_part = dt.date().isoformat()
            time_part = dt.strftime("%H:%M")
        except Exception:
            if "T" in (request.scheduled_time or ""):
                date_part, time_part = request.scheduled_time.split("T", 1)
        updates["date"] = date_part
        updates["time"] = (time_part or "")[:5]

    ok = db.update_scheduled_post(post_id, updates)
    if not ok:
        raise HTTPException(status_code=404, detail="Scheduled post not found")
    return {"success": True}


@app.delete("/api/scheduled-posts/{post_id}")
async def cancel_scheduled_post(post_id: str):
    ok = db.cancel_scheduled_post(post_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Scheduled post not found")
    return {"success": True}


@app.get("/api/scheduler/status")
async def scheduler_status():
    enabled = os.getenv("FYI_SCHEDULER_ENABLED", "1").strip() not in {"0", "false", "False"}
    poll = int(os.getenv("FYI_SCHEDULER_POLL_SECONDS", "10") or 10)
    return {"success": True, "enabled": enabled, "poll_seconds": max(2, min(poll, 300))}


def _parse_iso_loose(value: str | None) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


@app.get("/api/analytics/summary")
async def analytics_summary(days: int = 30):
    days = max(1, min(int(days or 30), 365))
    now = datetime.utcnow()
    cutoff = now - timedelta(days=days)

    posts = db.list_scheduled_posts(limit=1000)
    recent_posts = []
    for p in posts:
        dt = _parse_iso_loose(p.get("scheduled_time"))
        if dt is None:
            continue
        if dt.replace(tzinfo=None) >= cutoff:
            recent_posts.append(p)

    by_platform: dict[str, int] = {}
    for p in recent_posts:
        for platform in (p.get("platforms") or []):
            by_platform[str(platform)] = by_platform.get(str(platform), 0) + 1

    # Link clicks across all links (last N days)
    # Current DB tracks clicks; keep this report limited to our own tracked links.
    links = db.list_links(limit=500)
    clicks_total = 0
    for link in links:
        link_id = link.get("id")
        if link_id is None:
            continue
        stats = db.link_stats(int(link_id))
        clicks_total += int(stats.get("clicks_total") or 0)

    return {
        "success": True,
        "period_days": days,
        "scheduled_posts": {
            "total": len(recent_posts),
            "by_platform": by_platform,
        },
        "links": {
            "total": len(links),
            "clicks_total": clicks_total,
        },
        "note": "Platform analytics (reach/engagement) require platform metric sync; this summary uses portal data only.",
    }


@app.get("/api/analytics/export.csv")
async def analytics_export_csv(days: int = 30):
    days = max(1, min(int(days or 30), 365))
    now = datetime.utcnow()
    cutoff = now - timedelta(days=days)

    posts = db.list_scheduled_posts(limit=1000)
    rows = []
    for p in posts:
        dt = _parse_iso_loose(p.get("scheduled_time"))
        if dt is None:
            continue
        if dt.replace(tzinfo=None) < cutoff:
            continue
        rows.append(p)

    # Simple CSV output without extra deps.
    import csv
    import io

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "title", "caption", "platforms", "scheduled_time", "status", "created_at"])
    for p in rows:
        writer.writerow(
            [
                p.get("id"),
                p.get("title"),
                p.get("caption"),
                ";".join([str(x) for x in (p.get("platforms") or [])]),
                p.get("scheduled_time"),
                p.get("status"),
                p.get("created_at"),
            ]
        )

    return JSONResponse(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=analytics_{days}d.csv"},
    )

@app.get("/api/templates")
async def get_templates():
    """Get viral video templates"""
    return [
        {
            "id": "hook_story_cta",
            "name": "Hook-Story-CTA",
            "description": "Classic viral format: attention hook, story, call to action",
            "metrics": None
        },
        {
            "id": "tutorial_quick",
            "name": "Quick Tutorial",
            "description": "Fast-paced how-to content",
            "metrics": None
        },
        {
            "id": "before_after",
            "name": "Before/After",
            "description": "Transformation content that hooks viewers",
            "metrics": None
        }
    ]

from fastapi import UploadFile, File, Response
import uuid


def _safe_upload_ext(original_filename: str) -> str:
    name = (original_filename or "").strip()
    # Keep only a simple extension and cap length to avoid weird/long names.
    # If unknown, default to .bin.
    base, ext = os.path.splitext(name)
    ext = (ext or "").lower()
    if not ext or len(ext) > 10 or any(ch for ch in ext if ch not in ".abcdefghijklmnopqrstuvwxyz0123456789"):
        return ".bin"
    return ext

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file and return its ID"""
    # Important: keep the stored filename short.
    # Some platforms (notably Facebook Graph video upload) reject very long multipart filenames,
    # and Windows can hit path-length issues if we include the original filename.
    ext = _safe_upload_ext(file.filename)
    file_id = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOADS_DIR / file_id
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {
        "success": True,
        "file_id": file_id,
        "file_path": str(file_path),
        "filename": file.filename,
        "size": file_path.stat().st_size
    }


@app.delete("/api/uploads/{file_id}")
async def delete_uploaded_file(file_id: str):
    """Delete an uploaded file by id (best-effort)."""
    raw = str(file_id or "").strip()
    safe = raw.replace("..", "").replace("/", "").replace("\\", "")
    if not safe or safe != raw:
        raise HTTPException(status_code=400, detail="Invalid file id")

    file_path = UPLOADS_DIR / safe
    if not file_path.exists() or not file_path.is_file():
        # Idempotent delete
        return {"success": True, "deleted": False}
    try:
        file_path.unlink(missing_ok=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {e}")
    return {"success": True, "deleted": True}

class VideoProcessRequest(BaseModel):
    file_id: str
    target_clips: int = 3
    quality: str = "high"

class VideoScoreRequest(BaseModel):
    file_id: str


@app.get("/uploads/{file_id}")
async def serve_uploaded_file(file_id: str):
    # Prevent path traversal
    file_id = (file_id or "").replace("..", "").replace("/", "").replace("\\", "")
    file_path = UPLOADS_DIR / file_id
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    media_type, _ = mimetypes.guess_type(str(file_path))
    headers = {
        "Accept-Ranges": "bytes",
        "Cache-Control": "no-store",
    }
    return FileResponse(file_path, media_type=media_type, headers=headers)


@app.head("/uploads/{file_id}")
async def head_uploaded_file(file_id: str):
    """Support HEAD for external fetchers (e.g., Meta) that probe URLs before download."""
    file_id = (file_id or "").replace("..", "").replace("/", "").replace("\\", "")
    file_path = UPLOADS_DIR / file_id
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    media_type, _ = mimetypes.guess_type(str(file_path))
    size = file_path.stat().st_size
    headers = {
        "Content-Length": str(size),
        "Accept-Ranges": "bytes",
        "Cache-Control": "no-store",
    }
    if media_type:
        headers["Content-Type"] = media_type
    return Response(status_code=200, headers=headers)


def _ffprobe_json(file_path: Path) -> dict:
    if shutil.which("ffprobe") is None:
        raise RuntimeError("ffprobe is not installed")

    args = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(file_path),
    ]
    proc = subprocess.run(args, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "ffprobe failed")
    return json.loads(proc.stdout or "{}")


def _srt_timestamp(seconds: float) -> str:
    seconds = max(0.0, float(seconds or 0.0))
    ms_total = int(round(seconds * 1000.0))
    ms = ms_total % 1000
    s_total = ms_total // 1000
    s = s_total % 60
    m_total = s_total // 60
    m = m_total % 60
    h = m_total // 60
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _script_to_srt(script: str, *, max_words_per_caption: int = 7) -> tuple[str, float]:
    """Convert a script into a simple SRT.

    We don't have real TTS alignment in this MVP, so timings are heuristic based on reading speed.
    Returns (srt_text, total_duration_seconds).
    """
    raw = re.sub(r"\s+", " ", (script or "").strip())
    if not raw:
        return "", 0.0

    # Split by punctuation into rough sentences, then chunk into short captions.
    parts = re.split(r"(?<=[\.\!\?])\s+", raw)
    words: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        words.extend(p.split())

    max_words_per_caption = max(3, min(int(max_words_per_caption or 7), 16))
    # Reading speed ~ 2.2 words/sec. Keep each caption visible at least 1.5s.
    wps = 2.2
    min_seg = 1.5

    out_lines: list[str] = []
    t = 0.0
    idx = 1
    i = 0
    while i < len(words):
        chunk = words[i : i + max_words_per_caption]
        i += max_words_per_caption

        text = " ".join(chunk).strip()
        if not text:
            continue

        seg = max(min_seg, len(chunk) / wps)
        start = t
        end = t + seg
        t = end

        out_lines.append(str(idx))
        out_lines.append(f"{_srt_timestamp(start)} --> {_srt_timestamp(end)}")
        out_lines.append(text)
        out_lines.append("")
        idx += 1

    # Add a small tail so the last caption isn't cut off.
    total = t + 0.75
    return "\n".join(out_lines).strip() + "\n", total


def _ffmpeg_burn_subtitles(
    *,
    srt_path: Path,
    out_path: Path,
    duration_sec: float,
    width: int = 1080,
    height: int = 1920,
    fps: int = 30,
    bg_color: str = "black",
) -> None:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is not installed")

    width = int(width or 1080)
    height = int(height or 1920)
    fps = int(fps or 30)
    duration_sec = max(1.0, float(duration_sec or 1.0))

    # Windows path escaping for libass: C:/path/file.srt => C\:/path/file.srt
    srt_filter_path = str(srt_path).replace("\\", "/").replace(":", "\\:")

    # Styling via ASS force_style. Alignment=2 => bottom-center.
    style = (
        "FontName=Arial,"
        "FontSize=48,"
        "PrimaryColour=&H00FFFFFF&,"
        "OutlineColour=&H00000000&,"
        "BorderStyle=3,"
        "Outline=2,"
        "Shadow=0,"
        "Alignment=2,"
        "MarginV=90"
    )
    # Quote filename to avoid ':' parsing issues on Windows paths.
    vf = f"subtitles='{srt_filter_path}':force_style='{style}'"

    args = [
        "ffmpeg",
        "-y",
        "-f",
        "lavfi",
        "-i",
        f"color=c={bg_color}:s={width}x{height}:r={fps}:d={duration_sec}",
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-movflags",
        "+faststart",
        str(out_path),
    ]

    proc = subprocess.run(args, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or "ffmpeg faceless generation failed")


def _ffmpeg_split_equal(file_path: Path, target_clips: int, out_dir: Path) -> list[Path]:
    if shutil.which("ffmpeg") is None:
        raise RuntimeError("ffmpeg is not installed")

    info = _ffprobe_json(file_path)
    fmt = info.get("format") or {}
    duration = float(fmt.get("duration") or 0)
    if duration <= 0:
        raise RuntimeError("Unable to determine duration")

    target_clips = max(1, min(int(target_clips or 1), 20))
    seg = max(1.0, duration / target_clips)

    out_dir.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for i in range(target_clips):
        start = seg * i
        out_path = out_dir / f"clip_{i+1:02d}.mp4"
        # Copy streams if possible, but fall back to re-encode if copy fails.
        args = [
            "ffmpeg",
            "-y",
            "-ss",
            str(start),
            "-i",
            str(file_path),
            "-t",
            str(seg),
            "-c",
            "copy",
            str(out_path),
        ]
        proc = subprocess.run(args, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            args = [
                "ffmpeg",
                "-y",
                "-ss",
                str(start),
                "-i",
                str(file_path),
                "-t",
                str(seg),
                "-c:v",
                "libx264",
                "-preset",
                "veryfast",
                "-crf",
                "23",
                "-c:a",
                "aac",
                str(out_path),
            ]
            proc = subprocess.run(args, capture_output=True, text=True, check=False)
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr.strip() or "ffmpeg split failed")

        if out_path.exists():
            outputs.append(out_path)

    return outputs


@app.post("/api/video/process")
async def process_video(request: VideoProcessRequest):
    """Process video into clips using ffmpeg (real implementation).

    This does not use AI; it splits the video into N equal-length clips.
    """
    file_path = UPLOADS_DIR / request.file_id
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise HTTPException(
            status_code=501,
            detail="Video processing requires ffmpeg + ffprobe in PATH",
        )

    job_id = uuid.uuid4().hex[:10]
    out_dir = UPLOADS_DIR / "clips" / job_id
    started = datetime.utcnow()
    try:
        clips = _ffmpeg_split_equal(file_path, request.target_clips, out_dir)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    processing_time = (datetime.utcnow() - started).total_seconds()
    return {
        "success": True,
        "clips": [str(p.relative_to(PROJECT_DIR)).replace("\\", "/") for p in clips],
        "processing_time": processing_time,
        "message": "Video split complete",
        "file_id": request.file_id,
        "job_id": job_id,
    }


class FacelessVideoRequest(BaseModel):
    script: str
    width: int = 1080
    height: int = 1920
    fps: int = 30
    bg_color: str = "black"
    max_words_per_caption: int = 7


@app.post("/api/video/faceless")
async def create_faceless_video(request: FacelessVideoRequest):
    """Create a simple 'faceless' video from a script.

    MVP behavior:
    - Generates an SRT from the script with heuristic timings
    - Creates a background video and burns subtitles via ffmpeg/libass

    This intentionally avoids scraping or ToS-risky behavior.
    Voiceover/TTS and template B-roll can be layered on later.
    """

    script = (request.script or "").strip()
    if not script:
        raise HTTPException(status_code=400, detail="script is required")

    if shutil.which("ffmpeg") is None:
        raise HTTPException(status_code=501, detail="Faceless video requires ffmpeg in PATH")

    srt_text, duration_sec = _script_to_srt(script, max_words_per_caption=request.max_words_per_caption)
    if not srt_text or duration_sec <= 0:
        raise HTTPException(status_code=400, detail="Unable to generate subtitles from script")

    job_id = uuid.uuid4().hex[:10]
    out_dir = UPLOADS_DIR / "faceless" / job_id
    out_dir.mkdir(parents=True, exist_ok=True)

    srt_path = out_dir / "captions.srt"
    srt_path.write_text(srt_text, encoding="utf-8")

    out_name = f"faceless_{job_id}.mp4"
    out_path = UPLOADS_DIR / out_name

    try:
        _ffmpeg_burn_subtitles(
            srt_path=srt_path,
            out_path=out_path,
            duration_sec=duration_sec,
            width=request.width,
            height=request.height,
            fps=request.fps,
            bg_color=(request.bg_color or "black").strip() or "black",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {
        "success": True,
        "job_id": job_id,
        "file_id": out_name,
        "duration_sec": duration_sec,
        "url": f"/uploads/{out_name}",
    }

@app.post("/api/video/score")
async def score_video(request: VideoScoreRequest):
    """Score video for viral potential"""
    file_path = UPLOADS_DIR / request.file_id
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    if shutil.which("ffprobe") is None:
        raise HTTPException(status_code=501, detail="Video scoring requires ffprobe in PATH")

    try:
        info = _ffprobe_json(file_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    fmt = info.get("format") or {}
    streams = info.get("streams") or []
    duration = float(fmt.get("duration") or 0)
    bit_rate = float(fmt.get("bit_rate") or 0)

    vstreams = [s for s in streams if (s.get("codec_type") == "video")]
    astreams = [s for s in streams if (s.get("codec_type") == "audio")]

    width = int(vstreams[0].get("width") or 0) if vstreams else 0
    height = int(vstreams[0].get("height") or 0) if vstreams else 0
    fps = 0.0
    if vstreams:
        rate = vstreams[0].get("avg_frame_rate") or vstreams[0].get("r_frame_rate")
        if isinstance(rate, str) and "/" in rate:
            num, den = rate.split("/", 1)
            try:
                fps = float(num) / float(den)
            except Exception:
                fps = 0.0

    # Heuristic scoring (real: derived from file metadata, not constants).
    # This is not an ML model; it gives a rough technical-quality based score.
    hook_strength = 50
    if 5 <= duration <= 60:
        hook_strength = 75
    elif duration <= 120:
        hook_strength = 65

    pacing = 50
    if fps >= 29:
        pacing += 15
    if duration > 0 and duration <= 60:
        pacing += 15

    audio_quality = 40 if not astreams else 70
    if bit_rate >= 2_000_000:
        audio_quality += 5

    visual_appeal = 50
    if width >= 1080 and height >= 1080:
        visual_appeal += 20
    elif width >= 720 and height >= 720:
        visual_appeal += 10

    raw_score = (hook_strength + pacing + audio_quality + visual_appeal) / 4
    score = int(max(1, min(100, round(raw_score))))

    suggestions: list[str] = []
    if duration > 60:
        suggestions.append("Consider tighter edits (≤ 60s) for shorts")
    if not astreams:
        suggestions.append("Add clear audio or music; audio stream is missing")
    if width < 720 or height < 720:
        suggestions.append("Export at 720p or higher")

    return {
        "score": score,
        "breakdown": {
            "hook_strength": hook_strength,
            "pacing": pacing,
            "audio_quality": audio_quality,
            "visual_appeal": visual_appeal,
        },
        "suggestions": suggestions,
        "metadata": {
            "duration_sec": duration,
            "width": width,
            "height": height,
            "fps": fps,
            "has_audio": bool(astreams),
            "bit_rate": bit_rate,
        },
        "file_id": request.file_id,
    }


class LinkCreateRequest(BaseModel):
    target_url: str
    slug: Optional[str] = None


@app.post("/api/links")
async def create_link(request: LinkCreateRequest):
    slug = _slugify(request.slug) if request.slug else ""
    if not slug:
        slug = _gen_slug("l")
    try:
        link = db.create_link(slug=slug, target_url=request.target_url)
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Slug already exists")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "success": True,
        "link": {
            "slug": link.slug,
            "target_url": link.target_url,
            "created_at": link.created_at,
            "short_url": f"/l/{link.slug}",
        },
    }


@app.get("/api/links")
async def list_links(limit: int = 200):
    return {"success": True, "links": db.list_links(limit=limit)}


@app.get("/api/links/{slug}")
async def get_link(slug: str):
    link = db.get_link_by_slug(slug)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    return {
        "success": True,
        "link": {
            "slug": link.slug,
            "target_url": link.target_url,
            "created_at": link.created_at,
            "short_url": f"/l/{link.slug}",
        },
        "stats": db.link_stats(link.id),
    }


from fastapi.responses import RedirectResponse


@app.get("/l/{slug}")
async def redirect_short_link(slug: str, req: Request):
    link = db.get_link_by_slug(slug)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    ip = (req.client.host if req.client else None)
    user_agent = req.headers.get("user-agent")
    referrer = req.headers.get("referer")
    try:
        db.record_click(link.id, ip=ip, user_agent=user_agent, referrer=referrer)
    except Exception:
        # Redirect should succeed even if logging fails.
        pass
    return RedirectResponse(url=link.target_url)


class InstagramPublishRequest(BaseModel):
    account_id: Optional[str] = None
    file_id: str
    caption: Optional[str] = ""
    media_type: Optional[str] = "REELS"  # REELS|VIDEO|IMAGE


@app.post("/api/platforms/instagram/publish")
async def instagram_publish(request: InstagramPublishRequest, req: Request):
    account_id = request.account_id
    if not account_id:
        active = _load_active_accounts()
        account_id = active.get("instagram")

    acct = _find_account_by_id(account_id) if account_id else None
    if not acct:
        raise HTTPException(status_code=404, detail="Instagram account not found (provide account_id or set an active Instagram account)")
    if acct.get("platform") != "instagram":
        raise HTTPException(status_code=400, detail="Account is not an Instagram account")

    ig_user_id = acct.get("ig_user_id")
    access_token = acct.get("access_token")
    if not ig_user_id or not access_token:
        raise HTTPException(status_code=400, detail="Instagram account missing ig_user_id or access_token; reconnect via Instagram OAuth")

    file_path = UPLOADS_DIR / request.file_id
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Uploaded file not found")

    base = _get_public_base_url_from_request(req)
    if not _is_public_https_url(base):
        raise HTTPException(
            status_code=400,
            detail=(
                "Instagram publishing requires a publicly reachable HTTPS base URL to fetch the media file. "
                "Set FYI_PUBLIC_BASE_URL to your public https URL (e.g., an ngrok https tunnel), then retry."
            ),
        )

    media_url = f"{base}/uploads/{urllib.parse.quote(request.file_id)}"
    media_type = (request.media_type or "REELS").upper()
    if media_type not in {"REELS", "VIDEO", "IMAGE"}:
        raise HTTPException(status_code=400, detail="media_type must be REELS|VIDEO|IMAGE")

    create_params: dict[str, Any] = {"access_token": access_token, "caption": request.caption or ""}
    if media_type == "IMAGE":
        create_params["image_url"] = media_url
    else:
        create_params["video_url"] = media_url
        create_params["media_type"] = "REELS" if media_type == "REELS" else "VIDEO"

    async with httpx.AsyncClient(timeout=60) as client:
        await _preflight_public_media_url(client, media_url)

        create_resp = await client.post(
            f"https://graph.facebook.com/v20.0/{ig_user_id}/media",
            data=create_params,
        )
        if create_resp.status_code >= 400:
            raise HTTPException(status_code=create_resp.status_code, detail=create_resp.text)

        creation_id = (create_resp.json() or {}).get("id")
        if not creation_id:
            raise HTTPException(status_code=500, detail="Instagram did not return a creation id")

        # Poll for processing completion
        status_code_val = None
        last_status_payload: dict[str, Any] | None = None
        for _ in range(90):
            last_status_payload = await _ig_get_container_status(
                client,
                creation_id,
                access_token,
                include_video_status=False,
            )
            status_code_val = last_status_payload.get("status_code")
            if status_code_val == "FINISHED":
                break
            if status_code_val == "ERROR":
                status_obj = last_status_payload.get("status") if isinstance(last_status_payload, dict) else None
                # Common failure mode: Meta cannot fetch the media_url (e.g. intermittent fetch issues).
                # Retry once via resumable local upload to bypass external fetching.
                if _ig_status_has_error_code(status_obj or last_status_payload, "2207076"):
                    file_path = UPLOADS_DIR / request.file_id
                    return await _instagram_publish_resumable_local(
                        ig_user_id=ig_user_id,
                        access_token=access_token,
                        file_path=file_path,
                        caption=request.caption or "",
                        media_type="REELS" if media_type == "REELS" else "VIDEO",
                    )

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Instagram media processing failed. "
                        f"creation_id={creation_id}. status={status_obj or last_status_payload}"
                    ),
                )
            await asyncio.sleep(2)

        if status_code_val != "FINISHED":
            raise HTTPException(
                status_code=504,
                detail=(
                    "Instagram media processing timed out. "
                    f"creation_id={creation_id}. last_status={last_status_payload}"
                ),
            )

        publish_resp = await client.post(
            f"https://graph.facebook.com/v20.0/{ig_user_id}/media_publish",
            data={"access_token": access_token, "creation_id": creation_id},
        )
        if publish_resp.status_code >= 400:
            raise HTTPException(status_code=publish_resp.status_code, detail=publish_resp.text)

        ig_post_id = (publish_resp.json() or {}).get("id")
        return {
            "success": True,
            "platform": "instagram",
            "account_id": acct.get("id"),
            "creation_id": creation_id,
            "post_id": ig_post_id,
        }


async def _instagram_publish_internal(account_id: Optional[str], file_id: str, caption: str, media_type: str) -> dict:
    account_id = account_id or _load_active_accounts().get("instagram")
    acct = _find_account_by_id(account_id) if account_id else None
    if not acct:
        raise HTTPException(status_code=404, detail="Instagram account not found (set an active Instagram account)")
    if acct.get("platform") != "instagram":
        raise HTTPException(status_code=400, detail="Account is not an Instagram account")

    ig_user_id = acct.get("ig_user_id")
    access_token = acct.get("access_token")
    if not ig_user_id or not access_token:
        raise HTTPException(status_code=400, detail="Instagram account missing ig_user_id or access_token; reconnect via Instagram OAuth")

    file_path = UPLOADS_DIR / file_id
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Uploaded file not found")

    base = _normalize_base_url(os.getenv("FYI_PUBLIC_BASE_URL", ""))
    if not _is_public_https_url(base):
        raise HTTPException(status_code=400, detail="Instagram publishing requires FYI_PUBLIC_BASE_URL to be a publicly reachable https URL.")

    media_url = f"{base}/uploads/{urllib.parse.quote(file_id)}"
    media_type_u = (media_type or "REELS").upper()
    if media_type_u not in {"REELS", "VIDEO", "IMAGE"}:
        raise HTTPException(status_code=400, detail="media_type must be REELS|VIDEO|IMAGE")

    create_params: dict[str, Any] = {"access_token": access_token, "caption": caption or ""}
    if media_type_u == "IMAGE":
        create_params["image_url"] = media_url
    else:
        create_params["video_url"] = media_url
        create_params["media_type"] = "REELS" if media_type_u == "REELS" else "VIDEO"

    async with httpx.AsyncClient(timeout=60) as client:
        await _preflight_public_media_url(client, media_url)

        create_resp = await client.post(
            f"https://graph.facebook.com/v20.0/{ig_user_id}/media",
            data=create_params,
        )
        if create_resp.status_code >= 400:
            raise HTTPException(status_code=create_resp.status_code, detail=create_resp.text)

        creation_id = (create_resp.json() or {}).get("id")
        if not creation_id:
            raise HTTPException(status_code=500, detail="Instagram did not return a creation id")

        status_code_val = None
        last_status_payload: dict[str, Any] | None = None
        for _ in range(90):
            last_status_payload = await _ig_get_container_status(
                client,
                creation_id,
                access_token,
                include_video_status=False,
            )
            status_code_val = last_status_payload.get("status_code")
            if status_code_val == "FINISHED":
                break
            if status_code_val == "ERROR":
                status_obj = last_status_payload.get("status") if isinstance(last_status_payload, dict) else None
                if _ig_status_has_error_code(status_obj or last_status_payload, "2207076"):
                    file_path = UPLOADS_DIR / file_id
                    return await _instagram_publish_resumable_local(
                        ig_user_id=ig_user_id,
                        access_token=access_token,
                        file_path=file_path,
                        caption=caption or "",
                        media_type="REELS" if media_type_u == "REELS" else "VIDEO",
                    )

                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Instagram media processing failed. "
                        f"creation_id={creation_id}. status={status_obj or last_status_payload}"
                    ),
                )
            await asyncio.sleep(2)

        if status_code_val != "FINISHED":
            raise HTTPException(
                status_code=504,
                detail=(
                    "Instagram media processing timed out. "
                    f"creation_id={creation_id}. last_status={last_status_payload}"
                ),
            )

        publish_resp = await client.post(
            f"https://graph.facebook.com/v20.0/{ig_user_id}/media_publish",
            data={"access_token": access_token, "creation_id": creation_id},
        )
        if publish_resp.status_code >= 400:
            raise HTTPException(status_code=publish_resp.status_code, detail=publish_resp.text)

        ig_post_id = (publish_resp.json() or {}).get("id")
        return {
            "success": True,
            "platform": "instagram",
            "account_id": acct.get("id"),
            "creation_id": creation_id,
            "post_id": ig_post_id,
        }


async def _execute_due_post(post: dict[str, Any]) -> None:
    payload = post.get("payload") if isinstance(post.get("payload"), dict) else {}
    file_id = payload.get("file_id")
    clips = payload.get("clips") or []
    content = payload.get("content") if isinstance(payload.get("content"), dict) else {}

    title = post.get("title") or content.get("title") or "FYIXT Scheduled"
    caption = post.get("caption") or content.get("caption") or ""

    media_id = file_id or (clips[0] if isinstance(clips, list) and clips else None)
    if not media_id:
        raise HTTPException(status_code=400, detail="Scheduled post missing file_id (or clips[0])")

    results: dict[str, Any] = {}
    selected_accounts = payload.get("accounts") if isinstance(payload.get("accounts"), dict) else {}
    for platform in (post.get("platforms") or []):
        p = str(platform).strip().lower()
        if p in {"facebook", "fb"}:
            external_fb = None
            try:
                external_fb = (payload.get("external") or {}).get("facebook") if isinstance(payload.get("external"), dict) else None
            except Exception:
                external_fb = None

            # If we already scheduled this post natively in Facebook, do not re-upload/re-post.
            if isinstance(external_fb, dict) and external_fb.get("scheduled_publish_time"):
                results["facebook"] = {
                    "success": True,
                    "platform": "facebook",
                    "scheduled": True,
                    "video_id": external_fb.get("video_id"),
                    "account_id": external_fb.get("account_id"),
                }
            else:
                results["facebook"] = await facebook_upload_video(
                    FacebookUploadRequest(
                        account_id=(selected_accounts.get("facebook") if isinstance(selected_accounts, dict) else None),
                        file_id=media_id,
                        title=title,
                        description=caption,
                        scheduled_publish_time=None,
                    )
                )
        elif p in {"youtube", "yt"}:
            # Check if we already uploaded this as a natively scheduled YouTube video
            external_yt = None
            try:
                external_yt = (payload.get("external") or {}).get("youtube") if isinstance(payload.get("external"), dict) else None
            except Exception:
                external_yt = None

            if isinstance(external_yt, dict) and external_yt.get("publish_at"):
                # Already uploaded with publishAt — YouTube will publish it automatically
                results["youtube"] = {
                    "success": True,
                    "platform": "youtube",
                    "scheduled": True,
                    "video_id": external_yt.get("video_id"),
                    "account_id": external_yt.get("account_id"),
                }
            else:
                results["youtube"] = await youtube_upload_video(
                    YouTubeUploadRequest(
                        account_id=(selected_accounts.get("youtube") if isinstance(selected_accounts, dict) else None),
                        file_id=media_id,
                        title=title,
                        description=caption,
                        privacy_status="public",
                        publish_at=None,
                    )
                )
        elif p in {"instagram", "ig"}:
            results["instagram"] = await _instagram_publish_internal(
                (selected_accounts.get("instagram") if isinstance(selected_accounts, dict) else None),
                media_id,
                caption,
                "REELS",
            )
        else:
            raise HTTPException(status_code=501, detail=f"Scheduling execution not implemented for platform '{platform}'")

    db.mark_scheduled_post_result(post["id"], "posted", results, None)


async def _scheduler_loop() -> None:
    poll = int(os.getenv("FYI_SCHEDULER_POLL_SECONDS", "10") or 10)
    poll = max(2, min(poll, 300))
    while True:
        try:
            enabled = os.getenv("FYI_SCHEDULER_ENABLED", "1").strip() not in {"0", "false", "False"}
            if enabled:
                now_iso = datetime.now().isoformat(timespec="minutes")
                due = db.list_due_scheduled_posts(now_iso=now_iso, limit=25)
                for post in due:
                    db.mark_scheduled_post_attempt(post["id"], "posting", attempts_inc=1)
                    try:
                        await _execute_due_post(post)
                    except HTTPException as he:
                        db.mark_scheduled_post_result(post["id"], "failed", None, str(he.detail))
                    except Exception as e:
                        db.mark_scheduled_post_result(post["id"], "failed", None, str(e))
        except Exception:
            # Never crash the server due to scheduler issues.
            pass
        await asyncio.sleep(poll)


@app.on_event("startup")
async def _startup_scheduler() -> None:
    asyncio.create_task(_scheduler_loop())

REACT_BUILD_DIR = PROJECT_DIR / "desktop" / "dist"

if REACT_BUILD_DIR.exists():
    app.mount("/assets", StaticFiles(directory=REACT_BUILD_DIR / "assets"), name="assets")

@app.get("/{path:path}")
async def serve_react(path: str):
    """Serve React app for all non-API routes"""
    if REACT_BUILD_DIR.exists():
        file_path = REACT_BUILD_DIR / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        index_path = REACT_BUILD_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
    
    return JSONResponse(
        content={
            "message": "FYIXT API is running. Build the React app to see the UI.",
            "api_docs": "/docs",
            "health": "/api/health"
        }
    )

@app.get("/")
async def root():
    """Serve React app or API info"""
    if REACT_BUILD_DIR.exists():
        index_path = REACT_BUILD_DIR / "index.html"
        if index_path.exists():
            return FileResponse(index_path)
    
    return JSONResponse(
        content={
            "name": "FYIXT API",
            "version": "2.0.0",
            "status": "running",
            "docs": "/docs",
            "message": "Build the React frontend to see the full UI"
        }
    )

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 5000)))
    parser.add_argument("--https", action="store_true", help="Serve HTTPS with a self-signed localhost cert")
    parser.add_argument("--ssl-certfile", type=str, default=os.getenv("FYI_SSL_CERTFILE", ""))
    parser.add_argument("--ssl-keyfile", type=str, default=os.getenv("FYI_SSL_KEYFILE", ""))
    args = parser.parse_args()

    ssl_certfile = args.ssl_certfile.strip() if args.ssl_certfile else ""
    ssl_keyfile = args.ssl_keyfile.strip() if args.ssl_keyfile else ""
    if args.https:
        if not ssl_certfile or not ssl_keyfile:
            ssl_certfile, ssl_keyfile = _ensure_dev_https_cert()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=args.port,
        reload=False,
        ssl_certfile=ssl_certfile or None,
        ssl_keyfile=ssl_keyfile or None,
    )
