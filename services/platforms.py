"""Platform upload/publish services: Facebook, YouTube, Instagram."""
import os
import re
import json
import asyncio
import time
import mimetypes
import urllib.parse
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

import httpx
from fastapi import HTTPException

from core.config import (
    UPLOADS_DIR, DATA_DIR,
    FB_APP_ID, FB_APP_SECRET, YT_CLIENT_ID, YT_CLIENT_SECRET,
    _get_platform_credential,
)
from core.utils import _progress_set, _is_public_https_url, _normalize_base_url
from services.accounts import (
    _find_account_by_id, _load_accounts_raw, _load_active_accounts,
    _upsert_account_raw,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Facebook helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _fb_safe_text(value: str, max_len: int) -> str:
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
    """Facebook resumable upload with chunk progress."""
    size = int(file_path.stat().st_size)
    if size <= 0:
        raise RuntimeError("File is empty")

    def p(stage: str, percent: int | None = None, message: str | None = None, extra: dict | None = None):
        if progress_job_id:
            _progress_set(progress_job_id, stage=stage, percent=percent, message=message, extra=extra)

    p("facebook_upload_start", percent=1, message="Starting Facebook upload…", extra={"file_bytes": size})

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

        p("facebook_upload_transfer", percent=1, message="Uploading to Facebook…")

        with open(file_path, "rb") as f:
            while start_off_i < end_off_i:
                chunk_len = max(0, end_off_i - start_off_i)
                f.seek(start_off_i)
                chunk = f.read(chunk_len)
                if not chunk:
                    raise RuntimeError("Facebook upload stalled (empty chunk)")

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
        video_id = video_id or finish_json.get("video_id") or finish_json.get("id")

        p(
            "facebook_upload_done",
            percent=100,
            message="Facebook upload complete.",
            extra={"video_id": video_id},
        )
        return {"video_id": video_id, "raw": {"start": start_data, "finish": finish_json}}


async def _facebook_upload_video_impl(request, *, progress_job_id: Optional[str] = None):
    """Core Facebook upload logic used by both the route and the scheduler."""
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
    title = _fb_safe_text(request.title or "", 80)
    description = _fb_safe_text(request.description or "", 2000)

    try:
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


async def _facebook_latest_scheduled_time(account_id: Optional[str]) -> Optional[datetime]:
    """Best-effort: read the latest scheduled_publish_time for a connected Facebook page."""
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
        return datetime.fromtimestamp(int(latest_ts))
    except Exception:
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# YouTube helpers
# ═══════════════════════════════════════════════════════════════════════════════

async def _youtube_refresh_access_token(refresh_token: str) -> dict:
    yt_cid = _get_platform_credential("youtube", "client_id") or YT_CLIENT_ID
    yt_sec = _get_platform_credential("youtube", "client_secret") or YT_CLIENT_SECRET
    if not yt_cid or not yt_sec:
        raise HTTPException(status_code=400, detail="YouTube credentials not configured (YT_CLIENT_ID/YT_CLIENT_SECRET)")

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": yt_cid,
                "client_secret": yt_sec,
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


async def youtube_upload_video_impl(request) -> dict:
    """Core YouTube upload logic used by both the route and the scheduler."""
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
            "Content-Range": f"bytes 0-{size - 1}/{size}",
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


# ═══════════════════════════════════════════════════════════════════════════════
# Instagram helpers
# ═══════════════════════════════════════════════════════════════════════════════

async def _preflight_public_media_url(client: httpx.AsyncClient, media_url: str) -> None:
    """Verify the media URL is publicly reachable."""
    try:
        resp = await client.get(
            media_url,
            headers={"Range": "bytes=0-0"},
            follow_redirects=True,
        )
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
    """Fetch IG container status with a compatibility fallback."""
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
    """Fallback publish path that uploads the local file to Meta servers via rupload."""
    media_type_u = (media_type or "REELS").upper()
    if media_type_u not in {"REELS", "VIDEO", "STORIES"}:
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

        last_status_payload: dict[str, Any] | None = None
        status_code_val = None
        for _ in range(90):
            last_status_payload = await _ig_get_container_status(
                client, creation_id, access_token, include_video_status=True,
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


async def _instagram_publish_internal(account_id: Optional[str], file_id: str, caption: str, media_type: str) -> dict:
    """Publish to Instagram — used by both the route and the scheduler."""
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
                client, creation_id, access_token, include_video_status=False,
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
