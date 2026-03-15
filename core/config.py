"""Core configuration: paths, environment, database, credential management."""
import os
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None

from cryptography.fernet import Fernet, InvalidToken

from app_db import AppDB

# ─── Path constants ──────────────────────────────────────────────────────────

PROJECT_DIR = Path(__file__).resolve().parent.parent
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
BYOK_KEYS_FILE = DATA_DIR / "byok_keys.json"
PLATFORM_CREDS_FILE = DATA_DIR / "platform_credentials.json"
USAGE_FILE = DATA_DIR / "usage_credits.json"


# ─── Environment loading ─────────────────────────────────────────────────────

def _load_dotenv_fallback(env_path: Path) -> None:
    """Minimal .env loader used when python-dotenv isn't available."""
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
    env_path = PROJECT_DIR / ".env"
    if not env_path.exists():
        return
    if load_dotenv:
        try:
            load_dotenv(env_path)
            return
        except Exception:
            pass
    _load_dotenv_fallback(env_path)


_load_env_files()


# ─── HTTPS cert ──────────────────────────────────────────────────────────────

def _ensure_dev_https_cert() -> tuple[str, str]:
    """Create (if missing) a self-signed cert for localhost development."""
    if DEV_CERT_FILE.exists() and DEV_KEY_FILE.exists():
        return str(DEV_CERT_FILE), str(DEV_KEY_FILE)

    import ipaddress
    try:
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
    except Exception as e:
        raise RuntimeError(
            "HTTPS requested but cryptography is not available. Install it or run without --https."
        ) from e

    CERTS_DIR.mkdir(parents=True, exist_ok=True)

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "FYIUploader Dev"),
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])

    san = x509.SubjectAlternativeName([
        x509.DNSName("localhost"),
        x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
    ])

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


# ─── Directory creation ──────────────────────────────────────────────────────

DATA_DIR.mkdir(exist_ok=True)
ACCOUNTS_DIR.mkdir(exist_ok=True)
UPLOADS_DIR.mkdir(exist_ok=True)


# ─── Encryption ──────────────────────────────────────────────────────────────

_ENCRYPTION_KEY_FILE = DATA_DIR / ".encryption_key"


def _get_fernet() -> Fernet:
    """Load (or create) the Fernet key and return a cipher instance."""
    if _ENCRYPTION_KEY_FILE.exists():
        key = _ENCRYPTION_KEY_FILE.read_text(encoding="utf-8").strip().encode()
    else:
        key = Fernet.generate_key()
        _ENCRYPTION_KEY_FILE.write_text(key.decode(), encoding="utf-8")
    return Fernet(key)


_fernet = _get_fernet()


def _encrypt_json(data: dict) -> str:
    """Serialize *data* to JSON and return Fernet-encrypted base64 string."""
    plaintext = json.dumps(data).encode("utf-8")
    return _fernet.encrypt(plaintext).decode("utf-8")


def _decrypt_json(cipher_text: str) -> dict:
    """Decrypt a Fernet token and parse the JSON payload."""
    return json.loads(_fernet.decrypt(cipher_text.encode("utf-8")).decode("utf-8"))


# ─── Database ────────────────────────────────────────────────────────────────

db = AppDB(APP_DB_FILE)


# ─── Credential globals ─────────────────────────────────────────────────────

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


FB_APP_ID = _env_first("FB_APP_ID", "FYI_FB_APP_ID", "FYI_FACEBOOK_APP_ID")
FB_APP_SECRET = _env_first("FB_APP_SECRET", "FYI_FB_APP_SECRET", "FYI_FACEBOOK_APP_SECRET")
YT_CLIENT_ID = os.getenv("YT_CLIENT_ID", "")
YT_CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET", "")


# ─── BYOK API Key Management ────────────────────────────────────────────────

def _load_byok_keys() -> dict[str, str]:
    """Load BYOK API keys (encrypted on disk, transparently migrated from plaintext)."""
    if not BYOK_KEYS_FILE.exists():
        return {}
    raw = BYOK_KEYS_FILE.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    # Try encrypted format first
    try:
        return _decrypt_json(raw)
    except (InvalidToken, Exception):
        pass
    # Fall back to plaintext JSON (pre-encryption migration)
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            _save_byok_keys(data)  # re-save encrypted
            return data
    except Exception:
        pass
    return {}


def _save_byok_keys(keys: dict[str, str]) -> None:
    """Save BYOK API keys (encrypted)."""
    BYOK_KEYS_FILE.write_text(_encrypt_json(keys), encoding="utf-8")


def _get_byok_key(service: str) -> Optional[str]:
    """Get API key for a service (checks BYOK store, then env vars, then bundled defaults)."""
    keys = _load_byok_keys()
    key = keys.get(service)
    if key:
        return key
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
    return _get_default_key(service.lower())


def _get_default_key(service: str) -> Optional[str]:
    """Retrieve bundled default API key for a service.
    
    REMOVED: Hardcoded keys are a security risk. Configure via .env or BYOK settings instead.
    """
    return None


# ─── Platform OAuth Credentials ─────────────────────────────────────────────

def _load_platform_credentials() -> dict[str, dict[str, str]]:
    if not PLATFORM_CREDS_FILE.exists():
        return {}
    raw = PLATFORM_CREDS_FILE.read_text(encoding="utf-8").strip()
    if not raw:
        return {}
    # Try encrypted format first
    try:
        return _decrypt_json(raw)
    except (InvalidToken, Exception):
        pass
    # Fall back to plaintext JSON (pre-encryption migration)
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            _save_platform_credentials(data)  # re-save encrypted
            return data
    except Exception:
        pass
    return {}


def _save_platform_credentials(creds: dict[str, dict[str, str]]) -> None:
    PLATFORM_CREDS_FILE.write_text(_encrypt_json(creds), encoding="utf-8")


def _get_platform_credential(platform: str, key: str) -> Optional[str]:
    """Get a credential for a platform (checks stored creds then env vars)."""
    creds = _load_platform_credentials()
    platform_creds = creds.get(platform.lower(), {})
    value = platform_creds.get(key)
    if value:
        return value
    env_map = {
        ("youtube", "client_id"): "YT_CLIENT_ID",
        ("youtube", "client_secret"): "YT_CLIENT_SECRET",
        ("facebook", "app_id"): ["FB_APP_ID", "FYI_FB_APP_ID"],
        ("facebook", "app_secret"): ["FB_APP_SECRET", "FYI_FB_APP_SECRET"],
        ("instagram", "app_id"): ["FB_APP_ID", "FYI_FB_APP_ID"],
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


# ─── Credits / Usage Tracking ───────────────────────────────────────────────

def _load_usage() -> dict:
    if not USAGE_FILE.exists():
        return {"credits_used": 0, "history": [], "limits": {"monthly": 5000}}
    try:
        return json.loads(USAGE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"credits_used": 0, "history": [], "limits": {"monthly": 5000}}


def _save_usage(data: dict) -> None:
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
    data["history"] = history[-1000:]
    _save_usage(data)
    return {
        "credits_used": data["credits_used"],
        "credits_remaining": max(0, data.get("limits", {}).get("monthly", 5000) - data["credits_used"]),
    }
