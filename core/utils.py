"""Utility functions: progress tracking, text helpers, URL helpers, ffmpeg, Ollama."""
import os
import json
import re
import random
import subprocess
import shutil
import asyncio
import threading
import time
import urllib.parse
from typing import Any, Optional
from pathlib import Path
from datetime import datetime, timedelta

import httpx
from fastapi import Request

from core.config import DATA_DIR, SCHEDULED_POSTS_FILE, UPLOADS_DIR, db


# ═══════════════════════════════════════════════════════════════════════════════
# Progress Tracking
# ═══════════════════════════════════════════════════════════════════════════════

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


def _progress_set(
    job_id: str,
    *,
    stage: str,
    percent: Optional[int] = None,
    message: Optional[str] = None,
    extra: Optional[dict] = None,
    done: Optional[bool] = None,
    error: Optional[str] = None,
) -> None:
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


# ═══════════════════════════════════════════════════════════════════════════════
# Text Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _split_hashtags(text: str) -> list[str]:
    raw = (text or "").strip()
    if not raw:
        return []
    raw = raw.replace("\n", " ").replace(",", " ")
    parts = [p.strip() for p in raw.split() if p.strip()]
    tags: list[str] = []
    for p in parts:
        if p.startswith("#"):
            tag = p
        else:
            cleaned = re.sub(r"[^a-zA-Z0-9_]", "", p)
            if not cleaned:
                continue
            tag = f"#{cleaned}"
        if tag not in tags:
            tags.append(tag)
    return tags


def _slugify(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def _gen_slug(prefix: str = "l") -> str:
    alphabet = "abcdefghjkmnpqrstuvwxyz23456789"
    return f"{prefix}_{''.join(random.choice(alphabet) for _ in range(8))}"


def _iso_to_unix_seconds(value: str) -> int:
    """Convert an ISO8601 datetime string to unix seconds."""
    dt = datetime.fromisoformat((value or "").replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
    return int(dt.timestamp())


def _ceil_to_minute(dt: datetime) -> datetime:
    """Ceil a datetime up to the next minute (naive dt assumed local)."""
    if dt.second == 0 and dt.microsecond == 0:
        return dt
    return dt.replace(second=0, microsecond=0) + timedelta(minutes=1)


def _parse_iso_loose(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


def _safe_upload_ext(original_filename: str) -> str:
    name = (original_filename or "").strip()
    base, ext = os.path.splitext(name)
    ext = (ext or "").lower()
    if not ext or len(ext) > 10 or any(ch for ch in ext if ch not in ".abcdefghijklmnopqrstuvwxyz0123456789"):
        return ".bin"
    return ext


# ═══════════════════════════════════════════════════════════════════════════════
# URL Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _normalize_base_url(url: str) -> str:
    url = (url or "").strip()
    return url[:-1] if url.endswith("/") else url


def _get_public_base_url_from_request(req: Request) -> str:
    """Resolve the public base URL for redirects."""
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
    """Get the OAuth redirect URI based on environment and request."""
    forwarded_proto = (req.headers.get("x-forwarded-proto") or "").split(",")[0].strip()
    scheme = forwarded_proto or req.url.scheme
    host = (req.headers.get("x-forwarded-host") or req.headers.get("host") or "").split(",")[0].strip()
    if host:
        origin = f"{scheme}://{host}"
    else:
        origin = _normalize_base_url(str(req.base_url))
    return f"{origin}/oauth/callback/facebook"


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


# ═══════════════════════════════════════════════════════════════════════════════
# Scheduled Posts I/O
# ═══════════════════════════════════════════════════════════════════════════════

def _load_scheduled_posts() -> list[dict]:
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
                    db.insert_scheduled_post({
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
                    })
            return db.list_scheduled_posts(limit=1000)
        except Exception:
            return []

    return []


def _save_scheduled_posts(posts: list[dict]) -> None:
    for p in posts:
        if isinstance(p, dict) and p.get("id"):
            db.insert_scheduled_post({
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
            })

    SCHEDULED_POSTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SCHEDULED_POSTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"posts": posts}, f, indent=2)


# ═══════════════════════════════════════════════════════════════════════════════
# Ollama Helpers
# ═══════════════════════════════════════════════════════════════════════════════

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


async def _ollama_generate(prompt: str, model: str, system: Optional[str] = None, timeout_s: float = 20.0) -> str:
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


# ═══════════════════════════════════════════════════════════════════════════════
# FFmpeg / SRT Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _ffprobe_json(file_path: Path) -> dict:
    if shutil.which("ffprobe") is None:
        raise RuntimeError("ffprobe is not installed")

    args = [
        "ffprobe", "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(file_path),
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
    """Convert a script into a simple SRT with heuristic timings."""
    raw = re.sub(r"\s+", " ", (script or "").strip())
    if not raw:
        return "", 0.0

    parts = re.split(r"(?<=[\.\!\?])\s+", raw)
    words: list[str] = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        words.extend(p.split())

    max_words_per_caption = max(3, min(int(max_words_per_caption or 7), 16))
    wps = 2.2
    min_seg = 1.5

    out_lines: list[str] = []
    t = 0.0
    idx = 1
    i = 0
    while i < len(words):
        chunk = words[i: i + max_words_per_caption]
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

    # Sanitize bg_color to prevent command injection
    import re as _re
    if not _re.match(r"^[a-zA-Z]{1,20}$|^#[0-9a-fA-F]{3,8}$|^0x[0-9a-fA-F]{6,8}$", bg_color):
        bg_color = "black"

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
        "-i", f"color=c={bg_color}:s={width}x{height}:r={fps}:d={duration_sec}",
        "-vf", vf,
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
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
        out_path = out_dir / f"clip_{i + 1:02d}.mp4"
        args = [
            "ffmpeg", "-y", "-ss", str(start),
            "-i", str(file_path),
            "-t", str(seg), "-c", "copy",
            str(out_path),
        ]
        proc = subprocess.run(args, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            args = [
                "ffmpeg", "-y", "-ss", str(start),
                "-i", str(file_path),
                "-t", str(seg),
                "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "23", "-c:a", "aac",
                str(out_path),
            ]
            proc = subprocess.run(args, capture_output=True, text=True, check=False)
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr.strip() or "ffmpeg split failed")
        if out_path.exists():
            outputs.append(out_path)

    return outputs
