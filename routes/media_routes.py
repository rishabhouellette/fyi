"""Media routes: uploads, video processing, links, content, templates, guides, analytics."""
import os
import re
import json
import shutil
import uuid
import mimetypes
import subprocess
import sqlite3
import urllib.parse
from datetime import datetime, timedelta
from typing import Any, Optional, List, Dict
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException, Request, UploadFile, File, Response
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse

from core.config import (
    PROJECT_DIR, DATA_DIR, UPLOADS_DIR, db,
    _get_byok_key, _add_usage,
)
from core.models import (
    VideoProcessRequest, VideoScoreRequest, FacelessVideoRequest,
    FacelessVideoWithVoiceRequest, LinkCreateRequest,
    IngestURLRequest, RepurposeRequest, ApplyTemplateRequest,
    AIVoiceRequest,
)
from core.utils import (
    _slugify, _gen_slug, _safe_upload_ext, _parse_iso_loose,
    _ffprobe_json, _script_to_srt, _ffmpeg_burn_subtitles, _ffmpeg_split_equal,
    _ollama_models, _ollama_generate,
)

import ipaddress as _ipaddress

router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _validate_safe_url(url: str) -> None:
    """Validate URL scheme is http(s) and target is not a private/internal IP (anti-SSRF)."""
    import socket
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(status_code=400, detail="Only http and https URLs are allowed")
    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(status_code=400, detail="URL must include a hostname")
    # Block obviously internal hostnames
    if hostname in ("localhost", "0.0.0.0"):
        raise HTTPException(status_code=400, detail="Internal addresses are not allowed")
    try:
        addr = _ipaddress.ip_address(hostname)
        if addr.is_private or addr.is_loopback or addr.is_reserved or addr.is_link_local:
            raise HTTPException(status_code=400, detail="Internal addresses are not allowed")
    except ValueError:
        # hostname is a DNS name — resolve and check
        try:
            resolved = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
            for family, _, _, _, sockaddr in resolved:
                ip_str = sockaddr[0]
                addr = _ipaddress.ip_address(ip_str)
                if addr.is_private or addr.is_loopback or addr.is_reserved or addr.is_link_local:
                    raise HTTPException(status_code=400, detail="Internal addresses are not allowed")
        except HTTPException:
            raise
        except Exception:
            pass  # DNS resolution failure will be caught by httpx


_BG_COLOR_RE = __import__("re").compile(r"^[a-zA-Z]{1,20}$|^#[0-9a-fA-F]{3,8}$|^0x[0-9a-fA-F]{6,8}$")


def _sanitize_bg_color(raw: str) -> str:
    """Validate bg_color to prevent ffmpeg command injection."""
    color = (raw or "black").strip() or "black"
    if not _BG_COLOR_RE.match(color):
        return "black"
    return color


# ═══════════════════════════════════════════════════════════════════════════════
# File Uploads
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload a file and return its ID."""
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
        "size": file_path.stat().st_size,
    }


@router.delete("/api/uploads/{file_id}")
async def delete_uploaded_file(file_id: str):
    """Delete an uploaded file by id (best-effort)."""
    raw = str(file_id or "").strip()
    safe = raw.replace("..", "").replace("/", "").replace("\\", "")
    if not safe or safe != raw:
        raise HTTPException(status_code=400, detail="Invalid file id")

    file_path = UPLOADS_DIR / safe
    if not file_path.exists() or not file_path.is_file():
        return {"success": True, "deleted": False}
    try:
        file_path.unlink(missing_ok=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {e}")
    return {"success": True, "deleted": True}


@router.get("/uploads/{file_id}")
async def serve_uploaded_file(file_id: str):
    """Serve an uploaded file."""
    file_id = (file_id or "").replace("..", "").replace("/", "").replace("\\", "")
    file_path = UPLOADS_DIR / file_id
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    media_type, _ = mimetypes.guess_type(str(file_path))
    headers = {"Accept-Ranges": "bytes", "Cache-Control": "no-store"}
    return FileResponse(file_path, media_type=media_type, headers=headers)


@router.head("/uploads/{file_id}")
async def head_uploaded_file(file_id: str):
    """Support HEAD for external fetchers (e.g., Meta)."""
    file_id = (file_id or "").replace("..", "").replace("/", "").replace("\\", "")
    file_path = UPLOADS_DIR / file_id
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    media_type, _ = mimetypes.guess_type(str(file_path))
    size = file_path.stat().st_size
    headers = {"Content-Length": str(size), "Accept-Ranges": "bytes", "Cache-Control": "no-store"}
    if media_type:
        headers["Content-Type"] = media_type
    return Response(status_code=200, headers=headers)


# ═══════════════════════════════════════════════════════════════════════════════
# Video Processing
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/video/process")
async def process_video(request: VideoProcessRequest):
    """Process video into clips using ffmpeg."""
    file_path = UPLOADS_DIR / request.file_id
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise HTTPException(status_code=501, detail="Video processing requires ffmpeg + ffprobe in PATH")

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


@router.post("/api/video/faceless")
async def create_faceless_video(request: FacelessVideoRequest):
    """Create a simple 'faceless' video from a script with burnt subtitles."""
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
            bg_color=_sanitize_bg_color(request.bg_color),
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


@router.post("/api/video/faceless-with-voice")
async def create_faceless_video_with_voice(request: FacelessVideoWithVoiceRequest):
    """Create faceless video with AI voiceover."""
    script = (request.script or "").strip()
    if not script:
        raise HTTPException(status_code=400, detail="script is required")

    if shutil.which("ffmpeg") is None:
        raise HTTPException(status_code=501, detail="ffmpeg required")

    # 1. Generate voiceover via ai_routes
    from routes.ai_routes import ai_generate_voice
    voice_req = AIVoiceRequest(text=script, provider=request.voice_provider, voice_id=request.voice_id)
    voice_result = await ai_generate_voice(voice_req)
    audio_file_id = voice_result["file_id"]
    audio_path = UPLOADS_DIR / audio_file_id

    # 2. Get audio duration
    try:
        info = _ffprobe_json(audio_path)
        duration = float(info.get("format", {}).get("duration", 0))
    except Exception:
        duration = len(script) / 15

    # 3. Generate SRT from script
    srt_text, _ = _script_to_srt(script, max_words_per_caption=7)

    job_id = uuid.uuid4().hex[:10]
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
        "-i", f"color=c={_sanitize_bg_color(request.bg_color)}:s={request.width}x{request.height}:r=30:d={duration}",
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


@router.post("/api/video/score")
async def score_video(request: VideoScoreRequest):
    """Score video for viral potential based on technical metadata."""
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

    vstreams = [s for s in streams if s.get("codec_type") == "video"]
    astreams = [s for s in streams if s.get("codec_type") == "audio"]

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


# ═══════════════════════════════════════════════════════════════════════════════
# Short Links
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/links")
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


@router.get("/api/links")
async def list_links(limit: int = 200):
    return {"success": True, "links": db.list_links(limit=limit)}


@router.get("/api/links/{slug}")
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


@router.get("/l/{slug}")
async def redirect_short_link(slug: str, req: Request):
    link = db.get_link_by_slug(slug)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    ip = req.client.host if req.client else None
    user_agent = req.headers.get("user-agent")
    referrer = req.headers.get("referer")
    try:
        db.record_click(link.id, ip=ip, user_agent=user_agent, referrer=referrer)
    except Exception:
        pass

    # Validate redirect target to prevent open-redirect attacks
    target = (link.target_url or "").strip()
    try:
        parsed = urllib.parse.urlparse(target)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid target URL")
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise HTTPException(status_code=400, detail="Invalid redirect target")
    return RedirectResponse(url=target)


# ═══════════════════════════════════════════════════════════════════════════════
# Content Ingestion & Repurposing
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/content/ingest")
async def ingest_content_source(request: IngestURLRequest):
    """Extract content from URLs for repurposing."""
    url = (request.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="url is required")

    _validate_safe_url(url)

    extract_type = (request.extract_type or "article").strip().lower()

    try:
        async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
            if extract_type == "youtube" and ("youtube.com" in url or "youtu.be" in url):
                video_id = None
                if "v=" in url:
                    video_id = url.split("v=")[1].split("&")[0]
                elif "youtu.be/" in url:
                    video_id = url.split("youtu.be/")[1].split("?")[0]
                if not video_id:
                    raise HTTPException(status_code=400, detail="Could not extract YouTube video ID")

                caption_url = f"https://www.youtube.com/api/timedtext?v={video_id}&lang=en&fmt=srv3"
                resp = await client.get(caption_url)
                transcript = ""
                if resp.status_code == 200 and resp.text:
                    import xml.etree.ElementTree as ET
                    try:
                        root = ET.fromstring(resp.text)
                        texts = [elem.text for elem in root.findall(".//text") if elem.text]
                        transcript = " ".join(texts)
                    except Exception:
                        pass

                oembed_url = f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json"
                oembed_resp = await client.get(oembed_url)
                title = ""
                if oembed_resp.status_code == 200:
                    title = oembed_resp.json().get("title", "")

                return {
                    "success": True, "type": "youtube", "video_id": video_id,
                    "title": title, "transcript": transcript if transcript else "(No public captions available)",
                    "url": url,
                }
            else:
                resp = await client.get(url)
                if resp.status_code >= 400:
                    raise HTTPException(status_code=resp.status_code, detail=f"Failed to fetch URL: {resp.status_code}")

                html = resp.text
                title = ""
                title_match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
                if title_match:
                    title = title_match.group(1).strip()

                text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r"<[^>]+>", " ", text)
                text = re.sub(r"\s+", " ", text).strip()
                text = text[:10000] if len(text) > 10000 else text

                return {
                    "success": True, "type": "article", "title": title,
                    "text": text, "url": url, "char_count": len(text),
                }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/content/repurpose")
async def repurpose_content(request: RepurposeRequest):
    """Repurpose content into multiple formats using AI."""
    content = (request.content or "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="content is required")

    target_formats = request.target_formats or ["tweet", "linkedin", "caption"]
    language = request.language or "en"

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
                openai_key = _get_byok_key("openai")
                gemini_key = _get_byok_key("gemini")
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
                elif gemini_key:
                    async with httpx.AsyncClient(timeout=60) as client:
                        prompt_text = f"{system}\n\n{prompt}"
                        resp = await client.post(
                            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}",
                            json={"contents": [{"parts": [{"text": prompt_text}]}]},
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            result = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                            results[fmt] = {"content": result, "mode": "gemini"}
                            _add_usage("repurpose", 2, {"format": fmt})
                        else:
                            results[fmt] = {"content": "", "error": resp.text, "mode": "failed"}
                else:
                    results[fmt] = {"content": content[:500], "mode": "fallback", "note": "Configure Ollama, OpenAI, or Gemini for AI repurposing"}
        except Exception as e:
            results[fmt] = {"content": "", "error": str(e), "mode": "failed"}

    return {"success": True, "results": results}


# ═══════════════════════════════════════════════════════════════════════════════
# Viral Templates
# ═══════════════════════════════════════════════════════════════════════════════

VIRAL_TEMPLATES = [
    {"id": "hook_curiosity", "category": "hooks", "name": "Curiosity Gap", "template": "I never expected {topic} to change my life, but here's what happened…", "example": "I never expected a $5 app to change my life, but here's what happened…", "platforms": ["tiktok", "instagram", "youtube"]},
    {"id": "hook_contrarian", "category": "hooks", "name": "Contrarian Take", "template": "Stop {common_advice}. Here's what actually works for {goal}.", "example": "Stop waking up at 5am. Here's what actually works for productivity.", "platforms": ["tiktok", "instagram", "linkedin"]},
    {"id": "hook_listicle", "category": "hooks", "name": "Numbered List", "template": "{number} {topic} that will {benefit} (#{number} is a game-changer)", "example": "5 AI tools that will 10x your productivity (#3 is a game-changer)", "platforms": ["tiktok", "instagram", "youtube"]},
    {"id": "hook_pov", "category": "hooks", "name": "POV Hook", "template": "POV: You just discovered {topic} and your {aspect} will never be the same", "example": "POV: You just discovered ChatGPT and your workflow will never be the same", "platforms": ["tiktok", "instagram"]},
    {"id": "hook_secret", "category": "hooks", "name": "Secret/Insider", "template": "The {industry} secret they don't want you to know about {topic}", "example": "The tech industry secret they don't want you to know about salaries", "platforms": ["tiktok", "youtube", "instagram"]},
    {"id": "structure_problem", "category": "structures", "name": "Problem-Agitate-Solution", "template": "Hook: State the problem\nAgitate: Show why it's painful\nSolution: Reveal your answer\nCTA: Tell them what to do", "example": "Tired of wasting hours on social media?\nEvery minute scrolling is a minute lost forever.\nI use this 3-step system to post in 10 mins/day.\nSave this and try it tomorrow.", "platforms": ["all"]},
    {"id": "structure_story", "category": "structures", "name": "Story Arc", "template": "Setup: Where I was\nConflict: The challenge\nResolution: How I overcame it\nLesson: What you can learn", "example": "2 years ago I was broke and stuck.\nI tried everything but nothing worked.\nThen I discovered {method} and everything changed.\nHere's the one thing that made the difference…", "platforms": ["all"]},
    {"id": "structure_tutorial", "category": "structures", "name": "Quick Tutorial", "template": "Here's how to {goal} in {timeframe}:\n\nStep 1: {action}\nStep 2: {action}\nStep 3: {action}\n\nThat's it! Save for later 🔖", "example": "Here's how to get 1000 followers in 30 days:\n\nStep 1: Post 2x daily\nStep 2: Engage for 30 mins\nStep 3: Use trending sounds\n\nThat's it! Save for later 🔖", "platforms": ["all"]},
    {"id": "cta_save", "category": "ctas", "name": "Save CTA", "template": "Save this for when you need it 🔖", "platforms": ["instagram", "tiktok"]},
    {"id": "cta_follow", "category": "ctas", "name": "Follow CTA", "template": "Follow for more {topic} tips 👆", "platforms": ["all"]},
    {"id": "cta_comment", "category": "ctas", "name": "Comment CTA", "template": "Drop a 🔥 if you want part 2", "platforms": ["all"]},
    {"id": "cta_share", "category": "ctas", "name": "Share CTA", "template": "Share this with someone who needs to hear it 💯", "platforms": ["all"]},
]


@router.get("/api/templates")
async def list_viral_templates(category: Optional[str] = None, platform: Optional[str] = None):
    """Get viral content templates."""
    templates = VIRAL_TEMPLATES
    if category:
        templates = [t for t in templates if t["category"] == category.lower()]
    if platform:
        templates = [t for t in templates if platform.lower() in t["platforms"] or "all" in t["platforms"]]
    return {"success": True, "templates": templates, "count": len(templates)}


@router.post("/api/templates/apply")
async def apply_viral_template(request: ApplyTemplateRequest):
    """Apply variables to a template."""
    template = next((t for t in VIRAL_TEMPLATES if t["id"] == request.template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    result = template["template"]
    for key, value in (request.variables or {}).items():
        result = result.replace(f"{{{key}}}", value)

    return {"success": True, "template_id": request.template_id, "result": result}


# ═══════════════════════════════════════════════════════════════════════════════
# Social Media Guides
# ═══════════════════════════════════════════════════════════════════════════════

SOCIAL_GUIDES = {
    "instagram": {
        "best_times": ["Tuesday 11am", "Wednesday 11am", "Friday 10-11am"],
        "optimal_hashtags": 5,
        "video_length": "7-15 seconds for Reels",
        "image_size": "1080x1350 (4:5)",
        "tips": ["Use trending audio for Reels", "Post carousel for higher saves", "Engage 30 mins before/after posting"],
    },
    "tiktok": {
        "best_times": ["Tuesday 9am", "Thursday 12pm", "Friday 5am"],
        "optimal_hashtags": 3,
        "video_length": "21-34 seconds",
        "tips": ["Hook in first 1 second", "Use trending sounds", "Post 1-4 times per day"],
    },
    "youtube": {
        "best_times": ["Friday 3-4pm", "Saturday 9-11am", "Sunday 9-11am"],
        "optimal_tags": 10,
        "video_length": "8-12 minutes for monetization",
        "thumbnail_size": "1280x720",
        "tips": ["First 30 seconds = most important", "Ask for likes/subs at engagement peaks", "Use chapters for longer videos"],
    },
    "linkedin": {
        "best_times": ["Tuesday 10am-12pm", "Wednesday 12pm", "Thursday 9am"],
        "optimal_hashtags": 3,
        "post_length": "1300 characters",
        "tips": ["Start with a hook line", "Use line breaks for readability", "Ask a question at the end"],
    },
    "facebook": {
        "best_times": ["Wednesday 11am-1pm", "Thursday 1-2pm"],
        "optimal_hashtags": 2,
        "video_length": "1-3 minutes",
        "tips": ["Native video outperforms links", "Use captions (85% watch muted)", "Post in Groups for more reach"],
    },
}


@router.get("/api/guides/{platform}")
async def get_social_guide(platform: str):
    """Get platform-specific social media guide."""
    platform = platform.lower()
    if platform not in SOCIAL_GUIDES:
        raise HTTPException(status_code=404, detail=f"No guide for platform: {platform}")
    return {"success": True, "platform": platform, "guide": SOCIAL_GUIDES[platform]}


@router.get("/api/guides")
async def list_social_guides():
    """List all social media guides."""
    return {"success": True, "guides": SOCIAL_GUIDES}


# ═══════════════════════════════════════════════════════════════════════════════
# Analytics
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/api/analytics/summary")
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
        "scheduled_posts": {"total": len(recent_posts), "by_platform": by_platform},
        "links": {"total": len(links), "clicks_total": clicks_total},
        "note": "Platform analytics (reach/engagement) require platform metric sync; this summary uses portal data only.",
    }


@router.get("/api/analytics/export.csv")
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

    import csv
    import io

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "title", "caption", "platforms", "scheduled_time", "status", "created_at"])
    for p in rows:
        writer.writerow([
            p.get("id"), p.get("title"), p.get("caption"),
            ";".join([str(x) for x in (p.get("platforms") or [])]),
            p.get("scheduled_time"), p.get("status"), p.get("created_at"),
        ])

    return JSONResponse(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=analytics_{days}d.csv"},
    )
