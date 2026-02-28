"""API routes: health, accounts, OAuth, scheduling, BYOK, platform credentials, usage."""
import os
import json
import shutil
import asyncio
import urllib.parse
import mimetypes
import time
import threading
from datetime import datetime, timedelta
from typing import Any, Optional, List, Dict
from uuid import uuid4

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse

import core.config as cfg
from core.config import (
    PROJECT_DIR, DATA_DIR, UPLOADS_DIR, db,
    FB_APP_ID, FB_APP_SECRET, YT_CLIENT_ID, YT_CLIENT_SECRET,
    _get_byok_key, _get_default_key,
    _load_byok_keys, _save_byok_keys,
    _get_platform_credential, _load_platform_credentials, _save_platform_credentials,
    _load_usage, _save_usage, _add_usage,
)
from core.models import (
    AccountCreate, OAuthStart, ActiveAccountSetRequest,
    ScheduleRequest, InstantPublishRequest,
    BulkScheduleItem, BulkScheduleRequest, ScheduledPostUpdateRequest,
    FacebookUploadRequest, YouTubeUploadRequest, InstagramPublishRequest,
    BYOKSetKeyRequest, BYOKDeleteKeyRequest, PlatformCredentialRequest,
)
from core.utils import (
    _progress_set, _PROGRESS, _PROGRESS_LOCK, _progress_cleanup_unlocked,
    _normalize_base_url, _get_public_base_url_from_request, get_redirect_uri,
    _is_public_https_url, _load_scheduled_posts, _save_scheduled_posts,
    _iso_to_unix_seconds, _ceil_to_minute, _parse_iso_loose,
    _ollama_models,
)
from services.accounts import (
    account_manager,
    _load_accounts_raw, _find_account_by_id, _upsert_account_raw,
    _load_active_accounts, _save_active_accounts,
)
from services.platforms import (
    _facebook_upload_video_impl, _facebook_latest_scheduled_time,
    youtube_upload_video_impl,
    _instagram_publish_internal,
    _preflight_public_media_url, _ig_get_container_status, _ig_status_has_error_code,
    _instagram_publish_resumable_local,
    _ensure_youtube_access_token,
)

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# Health / Config / Growth
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/api/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now().isoformat(), "version": "2.0.0"}


@router.get("/api/config")
async def get_app_config():
    """Get app configuration and status."""
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


@router.get("/api/growth")
async def get_growth_report(days: int = 30):
    """Get growth analytics report."""
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


# ═══════════════════════════════════════════════════════════════════════════════
# Accounts
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/api/accounts")
async def get_accounts():
    accounts = account_manager.load_accounts()
    return {"accounts": accounts, "count": len(accounts)}


@router.post("/api/accounts")
async def create_account(account: AccountCreate):
    new_account = account_manager.add_account(
        platform=account.platform,
        name=account.name,
        username=account.username,
    )
    return {"success": True, "account": new_account}


@router.delete("/api/accounts/{account_id}")
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


@router.post("/api/accounts/{account_id}/refresh")
async def refresh_account(account_id: str):
    acct = _find_account_by_id(account_id)
    if not acct:
        raise HTTPException(status_code=404, detail="Account not found")

    platform = acct.get("platform")
    access_token = acct.get("access_token")
    if platform in ("facebook", "instagram"):
        if not access_token:
            raise HTTPException(status_code=400, detail="Account is missing access_token")
        if not cfg.FB_APP_ID or not cfg.FB_APP_SECRET:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Facebook App credentials not configured. Set FB_APP_ID and FB_APP_SECRET "
                    "(or FYI_FB_APP_ID/FYI_FB_APP_SECRET) in your environment or .env."
                ),
            )

        app_token = f"{cfg.FB_APP_ID}|{cfg.FB_APP_SECRET}"
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


# ═══════════════════════════════════════════════════════════════════════════════
# Active Accounts
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/api/active-accounts")
async def get_active_accounts():
    return {"success": True, "active": _load_active_accounts()}


@router.post("/api/active-accounts")
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


# ═══════════════════════════════════════════════════════════════════════════════
# OAuth
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/oauth/start/{platform}")
async def start_oauth(platform: str, request: OAuthStart, req: Request):
    """Start OAuth flow for a platform."""
    valid_platforms = ["facebook", "instagram", "youtube", "twitter", "linkedin", "tiktok"]

    if platform not in valid_platforms:
        raise HTTPException(status_code=400, detail=f"Invalid platform: {platform}")

    if platform in ("facebook", "instagram"):
        if not cfg.FB_APP_ID or not cfg.FB_APP_SECRET:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Facebook App credentials not configured. Set FB_APP_ID and FB_APP_SECRET "
                    "(or FYI_FB_APP_ID/FYI_FB_APP_SECRET) in your environment or .env."
                ),
            )

        redirect_uri = get_redirect_uri(req)
        state = f"{platform}_{request.account_name}"

        if platform == "instagram":
            scopes = "instagram_basic,instagram_content_publish,pages_show_list,pages_read_engagement,pages_manage_posts,public_profile"
        else:
            scopes = "pages_show_list,pages_read_engagement,pages_manage_posts,public_profile"

        auth_url = (
            f"https://www.facebook.com/v20.0/dialog/oauth?"
            f"client_id={cfg.FB_APP_ID}&"
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
            "message": f"Redirecting to {platform} for authorization...",
        }

    if platform == "youtube":
        yt_client_id = _get_platform_credential("youtube", "client_id") or cfg.YT_CLIENT_ID
        yt_client_secret = _get_platform_credential("youtube", "client_secret") or cfg.YT_CLIENT_SECRET

        if not yt_client_id or not yt_client_secret:
            raise HTTPException(
                status_code=400,
                detail="YouTube OAuth not configured (YT_CLIENT_ID/YT_CLIENT_SECRET). Go to Settings > Platform Credentials to add your YouTube API credentials.",
            )

        forwarded_proto = (req.headers.get("x-forwarded-proto") or "").split(",")[0].strip()
        scheme = forwarded_proto or req.url.scheme
        host = (req.headers.get("x-forwarded-host") or req.headers.get("host") or "").split(",")[0].strip()
        if host:
            origin = f"{scheme}://{host}"
        else:
            origin = _normalize_base_url(str(req.base_url))
        redirect_uri = f"{origin}/oauth/callback/youtube"
        state = f"youtube_{request.account_name}"
        yt_scopes = [
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
                    "scope": " ".join(yt_scopes),
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

    raise HTTPException(
        status_code=501,
        detail=(
            f"OAuth for '{platform}' is not implemented in the web portal yet. "
            "Provide platform credentials + OAuth redirect configuration, then implement the provider flow."
        ),
    )


@router.get("/oauth/callback/facebook")
@router.get("/callback")
async def facebook_oauth_callback(req: Request, code: str = None, state: str = None, error: str = None):
    """Handle Facebook OAuth callback."""
    if error:
        return JSONResponse(content={"success": False, "error": error}, status_code=400)
    if not code:
        return JSONResponse(content={"success": False, "error": "No authorization code received"}, status_code=400)

    redirect_uri = get_redirect_uri(req)

    async with httpx.AsyncClient() as client:
        token_response = await client.get(
            "https://graph.facebook.com/v20.0/oauth/access_token",
            params={
                "client_id": cfg.FB_APP_ID,
                "client_secret": cfg.FB_APP_SECRET,
                "redirect_uri": redirect_uri,
                "code": code,
            },
        )

        if token_response.status_code != 200:
            return JSONResponse(content={"success": False, "error": "Failed to get access token"}, status_code=400)

        token_data = token_response.json()
        access_token = token_data.get("access_token")

        user_response = await client.get(
            "https://graph.facebook.com/v20.0/me",
            params={"access_token": access_token, "fields": "id,name"},
        )
        if user_response.status_code != 200:
            return JSONResponse(content={"success": False, "error": "Failed to fetch user profile", "detail": user_response.text}, status_code=400)
        user_data = user_response.json()

        pages_response = await client.get(
            "https://graph.facebook.com/v20.0/me/accounts",
            params={"access_token": access_token},
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
            for a in accounts:
                try:
                    db.upsert_account(a)
                except Exception:
                    pass
        else:
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

    base = _get_public_base_url_from_request(req)
    return RedirectResponse(url=f"{base}/?oauth=success")


@router.get("/oauth/callback/youtube")
async def youtube_oauth_callback(req: Request, code: str = None, state: str = None, error: str = None):
    if error:
        return JSONResponse(content={"success": False, "error": error}, status_code=400)
    if not code:
        return JSONResponse(content={"success": False, "error": "No authorization code received"}, status_code=400)

    yt_client_id = _get_platform_credential("youtube", "client_id") or cfg.YT_CLIENT_ID
    yt_client_secret = _get_platform_credential("youtube", "client_secret") or cfg.YT_CLIENT_SECRET

    if not yt_client_id or not yt_client_secret:
        return JSONResponse(content={"success": False, "error": "YouTube OAuth not configured"}, status_code=400)

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

    base = _get_public_base_url_from_request(req)
    return RedirectResponse(url=f"{base}/?oauth=success")


@router.get("/oauth/callback/{platform}")
async def oauth_callback(platform: str, code: str = None, state: str = None):
    """Handle OAuth callback for other platforms."""
    raise HTTPException(
        status_code=501,
        detail=f"OAuth callback for '{platform}' is not implemented in the web portal yet",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Platform Uploads
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/platforms/facebook/upload")
async def facebook_upload_video(request: FacebookUploadRequest):
    """Upload a video to Facebook using a previously OAuth-linked page token."""
    return await _facebook_upload_video_impl(request, progress_job_id=None)


@router.post("/api/platforms/youtube/upload")
async def youtube_upload_video(request: YouTubeUploadRequest):
    return await youtube_upload_video_impl(request)


@router.post("/api/platforms/instagram/publish")
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


# ═══════════════════════════════════════════════════════════════════════════════
# Progress Tracking
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/api/schedule/progress/{job_id}")
async def get_schedule_progress(job_id: str):
    now_ts = time.time()
    with _PROGRESS_LOCK:
        _progress_cleanup_unlocked(now_ts)
        item = _PROGRESS.get(job_id)
    if not item:
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


# ═══════════════════════════════════════════════════════════════════════════════
# Scheduling
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/schedule")
async def schedule_post(request: ScheduleRequest):
    """Schedule a post across platforms."""
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
        try:
            plats = {str(p).strip().lower() for p in (platforms or []) if str(p).strip()}
        except Exception:
            plats = set()
        now = datetime.now()
        # Always start at +1 minute.  If the first smart slot is essentially
        # "now", the Facebook upload path will publish immediately instead of
        # scheduling (Facebook scheduling requires >= 10 min lead time).
        return _ceil_to_minute(now + timedelta(minutes=1))

    def _looks_like_fb_too_soon_error(msg: str) -> bool:
        m = (msg or "").lower()
        signals = [
            "scheduled", "scheduled_publish_time", "must be at least",
            "in the future", "too soon", "10 minute", "ten minute", "600",
            "publish time", "invalid",
        ]
        return any(s in m for s in signals)

    def _compute_smart_time(platforms: list[str], interval_minutes: int,
                            account_id: str | None = None) -> datetime:
        """Compute the next smart-schedule time.
        When *account_id* is given, only posts belonging to that account
        (payload.accounts.<platform>) are considered so that switching
        pages/channels starts a fresh timeline.
        """
        interval_minutes = max(1, min(int(interval_minutes or 60), 24 * 60))
        min_dt = _min_smart_start(platforms)
        posts = db.list_scheduled_posts(limit=1000)
        target = {str(p).strip().lower() for p in (platforms or []) if str(p).strip()}
        occupied: set[str] = set()
        latest_existing: datetime | None = None
        for p in posts:
            if str(p.get("status") or "").lower() in {"cancelled", "failed"}:
                continue
            plats = [str(x).strip().lower() for x in (p.get("platforms") or [])]
            if not any(x in target for x in plats):
                continue
            # ── account-level filter ──────────────────────────────
            if account_id:
                post_accounts = (p.get("payload") or {}).get("accounts") or {}
                # Check every matching platform key for the account
                post_matches = False
                for plat_key in target:
                    if post_accounts.get(plat_key) == account_id:
                        post_matches = True
                        break
                if not post_matches:
                    continue
            # ──────────────────────────────────────────────────────
            dt = _parse_dt_local(p.get("scheduled_time"))
            if not dt:
                continue
            # Track the latest existing post so we start after it + interval
            if latest_existing is None or dt > latest_existing:
                latest_existing = dt
            if dt < min_dt:
                continue
            key = dt.replace(second=0, microsecond=0).isoformat(timespec="minutes")
            occupied.add(key)

        # Ensure we start after the latest existing post + interval
        if latest_existing is not None:
            min_dt = max(min_dt, _ceil_to_minute(latest_existing + timedelta(minutes=interval_minutes)))

        cand = min_dt
        for _ in range(0, 24 * 60 + 5):
            k = cand.isoformat(timespec="minutes")
            if k not in occupied:
                return cand
            cand = _ceil_to_minute(cand + timedelta(minutes=interval_minutes))
        return cand

    try:
        scheduled_time = (request.scheduledTime or "").strip() if request.scheduledTime is not None else ""
        if not scheduled_time or scheduled_time.upper() == "SMART":
            # Resolve the account_id for the target platform so smart time
            # only considers posts for THIS account/page.
            _smart_acct_id: str | None = None
            try:
                _accts = request.accounts or {}
                for _pk in (request.platforms or []):
                    _smart_acct_id = _accts.get(str(_pk).strip().lower()) or _accts.get(str(_pk).strip())
                    if _smart_acct_id:
                        break
            except Exception:
                _smart_acct_id = None
            dt_smart = _compute_smart_time(request.platforms, int(request.interval_minutes or 60),
                                           account_id=_smart_acct_id)

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

        try:
            platforms_norm = {str(p).strip().lower() for p in (request.platforms or []) if str(p).strip()}
        except Exception:
            platforms_norm = set()

        # Track per-platform errors so one failure doesn't block the others.
        _platform_errors: dict[str, str] = {}
        fb_publish_now = False

        # Facebook native scheduling
        if any(p in {"facebook", "fb"} for p in platforms_norm):
            media_id = post["payload"].get("file_id") or (post["payload"].get("clips") or [None])[0]
            if not media_id:
                _platform_errors["facebook"] = "Facebook scheduling requires file_id (or clips[0])"
            else:
                try:
                    unix_ts = _iso_to_unix_seconds(scheduled_time)
                except Exception:
                    _platform_errors["facebook"] = "Invalid scheduled_time for Facebook scheduling"
                    unix_ts = None

                if unix_ts is not None:
                    selected_fb_account = None
                    try:
                        selected_fb_account = (request.accounts or {}).get("facebook")
                    except Exception:
                        selected_fb_account = None

                    now_ts = int(datetime.now().timestamp())
                    fb_min_lead = 660  # 11 minutes (10-min Facebook minimum + 1-min safety)

                    # If the computed time is essentially "now" (first available slot,
                    # within 2 minutes), publish immediately instead of scheduling.
                    fb_publish_now = (unix_ts <= now_ts + 120)

                    if not fb_publish_now and unix_ts < now_ts + fb_min_lead:
                        # Too close for Facebook scheduling but not "now" — bump to 11 min
                        unix_ts = now_ts + fb_min_lead
                        scheduled_time = datetime.fromtimestamp(unix_ts).isoformat(timespec="minutes")
                        post["scheduled_time"] = scheduled_time
                        try:
                            dt_fix = datetime.fromisoformat(scheduled_time)
                            post["date"] = dt_fix.date().isoformat()
                            post["time"] = dt_fix.strftime("%H:%M")
                        except Exception:
                            pass

                    try:
                        _progress_set(schedule_id, stage="facebook_schedule_start", percent=1, message="Publishing to Facebook…" if fb_publish_now else "Preparing Facebook scheduling…")
                        try:
                            fb_res = await _facebook_upload_video_impl(
                                FacebookUploadRequest(
                                    account_id=selected_fb_account,
                                    file_id=media_id,
                                    title=post.get("title") or "",
                                    description=post.get("caption") or "",
                                    scheduled_publish_time=None if fb_publish_now else unix_ts,
                                ),
                                progress_job_id=schedule_id,
                            )
                        except HTTPException as he:
                            if int(getattr(he, "status_code", 400) or 400) in {400, 422, 502} and _looks_like_fb_too_soon_error(str(getattr(he, "detail", ""))):
                                retry_now = int(datetime.now().timestamp())
                                unix_ts2 = max(unix_ts, retry_now + fb_min_lead)
                                _progress_set(schedule_id, stage="facebook_schedule_retry", percent=5, message="Facebook requires more lead time; retrying at +11 minutes…")
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

                        if fb_publish_now:
                            _progress_set(schedule_id, stage="facebook_publish_done", percent=100, message="Published to Facebook.", done=False)
                        else:
                            _progress_set(schedule_id, stage="facebook_schedule_done", percent=100, message="Facebook scheduled.", done=False)
                        payload = post.get("payload") if isinstance(post.get("payload"), dict) else {}
                        external = payload.get("external") if isinstance(payload.get("external"), dict) else {}
                        external["facebook"] = {
                            "scheduled_publish_time": None if fb_publish_now else unix_ts,
                            "video_id": (fb_res or {}).get("video_id"),
                            "account_id": (fb_res or {}).get("account_id"),
                            "raw": (fb_res or {}).get("raw"),
                        }
                        payload["external"] = external
                        post["payload"] = payload
                    except Exception as e:
                        _platform_errors["facebook"] = str(e)
                        _progress_set(schedule_id, stage="facebook_schedule_failed", percent=100, message=f"Facebook scheduling failed: {e}", done=False)

        # YouTube native scheduling
        if any(p in {"youtube", "yt"} for p in platforms_norm):
            media_id_yt = post["payload"].get("file_id") or (post["payload"].get("clips") or [None])[0]
            if media_id_yt:
                try:
                    dt_yt = datetime.fromisoformat(scheduled_time)
                    publish_at_rfc3339 = dt_yt.isoformat() + "Z" if not dt_yt.tzinfo else dt_yt.isoformat()

                    selected_yt_account = None
                    try:
                        selected_yt_account = (request.accounts or {}).get("youtube")
                    except Exception:
                        selected_yt_account = None

                    _progress_set(schedule_id, stage="youtube_schedule_start", percent=1, message="Uploading to YouTube (scheduled)…")
                    yt_res = await youtube_upload_video_impl(
                        YouTubeUploadRequest(
                            account_id=selected_yt_account,
                            file_id=str(media_id_yt),
                            title=post.get("title") or "",
                            description=post.get("caption") or "",
                            privacy_status="private",
                            publish_at=publish_at_rfc3339,
                        )
                    )
                    _progress_set(schedule_id, stage="youtube_schedule_done", percent=100, message="YouTube scheduled.", done=False)

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
                    _platform_errors["youtube"] = str(e)
                    _progress_set(schedule_id, stage="youtube_schedule_failed", percent=100, message=f"YouTube scheduling failed: {e}", done=False)

        # Instagram handling
        # Instagram Graph API does not support native scheduling to a future
        # time, so when scheduling for the future the post is saved and the
        # background scheduler executor will publish at the scheduled time.
        # However, when fb_publish_now is True (the slot is "now"), we publish
        # to Instagram immediately so it doesn't get orphaned — the scheduler
        # only processes posts with status "scheduled".
        if any(p in {"instagram", "ig"} for p in platforms_norm):
            media_id_ig = post["payload"].get("file_id") or (post["payload"].get("clips") or [None])[0]
            if fb_publish_now and media_id_ig:
                # Publish to Instagram NOW (alongside the instant FB publish).
                try:
                    selected_ig_account = None
                    try:
                        selected_ig_account = (request.accounts or {}).get("instagram")
                    except Exception:
                        selected_ig_account = None

                    _progress_set(schedule_id, stage="instagram_publish_start", percent=1, message="Publishing to Instagram…", done=False)
                    ig_res = await _instagram_publish_internal(
                        selected_ig_account,
                        str(media_id_ig),
                        post.get("caption") or "",
                        "REELS",
                    )
                    _progress_set(schedule_id, stage="instagram_publish_done", percent=100, message="Published to Instagram.", done=False)

                    payload = post.get("payload") if isinstance(post.get("payload"), dict) else {}
                    external = payload.get("external") if isinstance(payload.get("external"), dict) else {}
                    external["instagram"] = {
                        "published_now": True,
                        "result": ig_res,
                    }
                    payload["external"] = external
                    post["payload"] = payload
                except Exception as e:
                    _platform_errors["instagram"] = str(e)
                    _progress_set(schedule_id, stage="instagram_publish_failed", percent=100, message=f"Instagram publish failed: {e}", done=False)
            # else: deferred to scheduler executor at scheduled_time (it handles IG natively)

        # Determine final post status.
        # "published" only if fb_publish_now was used and no other platforms are
        # still waiting for the scheduler to run them.
        if fb_publish_now:
            # Check if all selected platforms were handled immediately.
            has_deferred = False
            if any(p in {"instagram", "ig"} for p in platforms_norm):
                ig_external = ((post.get("payload") or {}).get("external") or {}).get("instagram")
                if not ig_external:
                    has_deferred = True  # IG still needs scheduler
            if any(p in {"youtube", "yt"} for p in platforms_norm):
                yt_external = ((post.get("payload") or {}).get("external") or {}).get("youtube")
                if not yt_external:
                    has_deferred = True  # YT still needs scheduler
            post["status"] = "scheduled" if has_deferred else "published"
        # else: stays "scheduled" (default)

        # If ALL platforms failed, raise so the caller sees an error.
        if _platform_errors and not any(
            k in ((post.get("payload") or {}).get("external") or {})
            for k in ("facebook", "youtube", "instagram")
        ):
            combined = "; ".join(f"{k}: {v}" for k, v in _platform_errors.items())
            raise HTTPException(status_code=502, detail=combined)

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


@router.post("/api/publish/instant")
async def publish_instant(request: InstantPublishRequest, req: Request):
    """Publish a post immediately (no scheduling)."""
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
    errors: dict[str, str] = {}

    # Process each platform independently so one failure does not block others.
    for platform in (request.platforms or []):
        p = str(platform).strip().lower()
        try:
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
                results["youtube"] = await youtube_upload_video_impl(
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
                errors[p] = f"Instant publish not implemented for platform '{platform}'"
                continue
        except HTTPException as he:
            errors[p] = str(getattr(he, "detail", str(he)))
            _progress_set(job_id, stage=f"{p}_post_failed", percent=100, message=f"{platform} failed: {errors[p]}", done=False)
        except Exception as e:
            errors[p] = str(e)
            _progress_set(job_id, stage=f"{p}_post_failed", percent=100, message=f"{platform} failed: {e}", done=False)

    if not results and errors:
        # Every platform failed — report the combined error.
        combined = "; ".join(f"{k}: {v}" for k, v in errors.items())
        _progress_set(job_id, stage="instant_publish_failed", percent=100, message="Instant post failed", done=True, error=combined)
        raise HTTPException(status_code=502, detail=combined)

    _progress_set(job_id, stage="instant_publish_done", percent=100, message="Instant post complete.", done=True)
    return {"success": True, "job_id": job_id, "results": results, "errors": errors or None}


@router.post("/api/schedule/bulk")
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

    all_platforms: list[str] = []
    for it in items:
        all_platforms.extend(it.platforms or [])
    target = {str(p).strip().lower() for p in all_platforms if str(p).strip()}
    # Resolve the account_id for filtering (same logic as single-post path)
    _bulk_acct_id: str | None = None
    try:
        _accts = request.accounts or {}
        for _pk in target:
            _bulk_acct_id = _accts.get(_pk) or _accts.get(_pk.title())
            if _bulk_acct_id:
                break
    except Exception:
        _bulk_acct_id = None

    posts = db.list_scheduled_posts(limit=1000)
    occupied: set[str] = set()
    latest_existing: datetime | None = None
    for p in posts:
        if str(p.get("status") or "").lower() in {"cancelled", "failed"}:
            continue
        plats = [str(x).strip().lower() for x in (p.get("platforms") or [])]
        if not any(x in target for x in plats):
            continue
        # ── account-level filter (same as _compute_smart_time) ────
        if _bulk_acct_id:
            post_accounts = (p.get("payload") or {}).get("accounts") or {}
            post_matches = False
            for plat_key in target:
                if post_accounts.get(plat_key) == _bulk_acct_id:
                    post_matches = True
                    break
            if not post_matches:
                continue
        # ──────────────────────────────────────────────────────────
        dt = _parse_dt_local(p.get("scheduled_time"))
        if not dt:
            continue
        # Track the latest existing post so we start after it + interval
        if latest_existing is None or dt > latest_existing:
            latest_existing = dt
        key = dt.replace(second=0, microsecond=0).isoformat(timespec="minutes")
        occupied.add(key)

    now = datetime.now()

    try:
        any_fb = any(
            any(str(p).strip().lower() in {"facebook", "fb"} for p in (it.platforms or []))
            for it in items
        )
    except Exception:
        any_fb = False

    # Facebook requires scheduled_publish_time >= 10 min; use 15-min buffer.
    # Other platforms can start at +1 minute.
    fb_lead_minutes = 15 if any_fb else 1
    min_dt = _ceil_to_minute(now + timedelta(minutes=fb_lead_minutes))
    next_dt = min_dt

    # Ensure we start after the latest existing local post + interval
    if latest_existing is not None:
        next_dt = max(next_dt, _ceil_to_minute(latest_existing + timedelta(minutes=interval_minutes)))

    if any_fb:
        _fb_acct = _bulk_acct_id if _bulk_acct_id and "facebook" in (_bulk_acct_id or "").lower() else None
        fb_latest = await _facebook_latest_scheduled_time(_fb_acct or _bulk_acct_id)
        if fb_latest is not None:
            next_dt = max(next_dt, _ceil_to_minute(fb_latest + timedelta(minutes=interval_minutes)))

    created: list[dict[str, Any]] = []
    for it in items:
        schedule_id = f"post_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid4().hex[:8]}"

        scheduled_time = ""
        if smart:
            # When smart=true the server ALWAYS computes the schedule slot,
            # ignoring any client-supplied scheduledTime so the interval is
            # guaranteed to be respected.
            cand = _ceil_to_minute(next_dt)
            for _ in range(0, 24 * 60 + 5):
                k = cand.isoformat(timespec="minutes")
                if k not in occupied:
                    break
                cand = _ceil_to_minute(cand + timedelta(minutes=interval_minutes))
            scheduled_time = cand.isoformat(timespec="minutes")
            occupied.add(scheduled_time)
            next_dt = cand + timedelta(minutes=interval_minutes)
        else:
            scheduled_time = (it.scheduledTime or "").strip() if it.scheduledTime is not None else ""

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
                "accounts": request.accounts or {},
            },
        }

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
            fb_min_lead = 660  # 11 minutes (10-min Facebook minimum + 1-min safety)

            # In bulk mode, always schedule (never publish immediately).
            # The smart loop already starts at +15 min for Facebook.
            if unix_ts < now_ts + fb_min_lead:
                unix_ts = now_ts + fb_min_lead
                scheduled_time = datetime.fromtimestamp(unix_ts).isoformat(timespec="minutes")
                post["scheduled_time"] = scheduled_time
                try:
                    dt_fix = datetime.fromisoformat(scheduled_time)
                    post["date"] = dt_fix.date().isoformat()
                    post["time"] = dt_fix.strftime("%H:%M")
                except Exception:
                    pass

            try:
                fb_res = await _facebook_upload_video_impl(
                    FacebookUploadRequest(
                        file_id=it.file_id,
                        title=it.title or "",
                        description=it.caption or "",
                        scheduled_publish_time=unix_ts,
                    )
                )
            except HTTPException as he:
                msg = str(getattr(he, "detail", ""))
                m = msg.lower()
                if int(getattr(he, "status_code", 400) or 400) in {400, 422, 502} and (
                    "scheduled" in m or "must be at least" in m or "in the future" in m or "10 minute" in m or "scheduled_publish_time" in m or "invalid" in m
                ):
                    retry_now = int(datetime.now().timestamp())
                    unix_ts2 = max(unix_ts, retry_now + fb_min_lead)
                    fb_res = await _facebook_upload_video_impl(
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

        existing_posts = _load_scheduled_posts()
        existing_posts.append(post)
        _save_scheduled_posts(existing_posts)
        created.append(post)

    return {"success": True, "count": len(created), "scheduled_posts": created}


# ═══════════════════════════════════════════════════════════════════════════════
# Scheduled Posts CRUD
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/api/scheduled-posts")
async def list_scheduled_posts(limit: int = 200):
    posts = _load_scheduled_posts()
    posts_sorted = sorted(posts, key=lambda p: (p.get("scheduled_time") or "", p.get("created_at") or ""), reverse=True)
    return {
        "success": True,
        "posts": posts_sorted[: max(1, min(limit, 1000))],
        "count": len(posts),
    }


@router.put("/api/scheduled-posts/{post_id}")
async def update_scheduled_post(post_id: str, request: ScheduledPostUpdateRequest):
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


@router.delete("/api/scheduled-posts/{post_id}")
async def cancel_scheduled_post(post_id: str):
    ok = db.cancel_scheduled_post(post_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Scheduled post not found")
    return {"success": True}


@router.get("/api/scheduler/status")
async def scheduler_status():
    enabled = os.getenv("FYI_SCHEDULER_ENABLED", "1").strip() not in {"0", "false", "False"}
    poll = int(os.getenv("FYI_SCHEDULER_POLL_SECONDS", "10") or 10)
    return {"success": True, "enabled": enabled, "poll_seconds": max(2, min(poll, 300))}


# ═══════════════════════════════════════════════════════════════════════════════
# BYOK API Key Management
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/api/byok/keys")
async def list_byok_keys():
    """List configured BYOK services (keys are masked)."""
    keys = _load_byok_keys()
    services = {}
    for svc in ["openai", "anthropic", "elevenlabs", "stability", "replicate", "runway", "pika", "kling", "flux", "ideogram", "gemini", "xai"]:
        key = _get_byok_key(svc)
        services[svc] = {
            "configured": bool(key),
            "source": "byok" if svc in keys else ("env" if key else None),
            "masked": f"{key[:4]}...{key[-2:]}" if key and len(key) > 12 else ("****" if key else None),
        }
    return {"success": True, "services": services}


@router.post("/api/byok/keys")
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


@router.delete("/api/byok/keys/{service}")
async def delete_byok_key(service: str):
    """Delete a BYOK API key."""
    service = (service or "").strip().lower()
    keys = _load_byok_keys()
    if service in keys:
        del keys[service]
        _save_byok_keys(keys)
    return {"success": True, "service": service}


# ═══════════════════════════════════════════════════════════════════════════════
# Platform OAuth Credentials
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/api/platform-credentials")
async def list_platform_credentials():
    """List configured platforms (credentials are masked)."""
    creds = _load_platform_credentials()
    platforms = {}

    platform_keys = {
        "youtube": ["client_id", "client_secret"],
        "facebook": ["app_id", "app_secret"],
        "instagram": ["app_id", "app_secret"],
        "twitter": ["api_key", "api_secret"],
        "linkedin": ["client_id", "client_secret"],
        "tiktok": ["client_key", "client_secret"],
    }

    for plat, keys in platform_keys.items():
        platform_info = {"configured": True, "keys": {}}
        for key in keys:
            value = _get_platform_credential(plat, key)
            platform_info["keys"][key] = {
                "configured": bool(value),
                "source": "stored" if creds.get(plat, {}).get(key) else ("env" if value else None),
                "masked": f"{value[:4]}...{value[-2:]}" if value and len(value) > 10 else ("****" if value else None),
            }
            if not value:
                platform_info["configured"] = False
        platforms[plat] = platform_info

    return {"success": True, "platforms": platforms}


@router.post("/api/platform-credentials")
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
    if platform == "youtube":
        cfg.YT_CLIENT_ID = _get_platform_credential("youtube", "client_id") or cfg.YT_CLIENT_ID
        cfg.YT_CLIENT_SECRET = _get_platform_credential("youtube", "client_secret") or cfg.YT_CLIENT_SECRET
    elif platform in ("facebook", "instagram"):
        cfg.FB_APP_ID = _get_platform_credential("facebook", "app_id") or cfg.FB_APP_ID
        cfg.FB_APP_SECRET = _get_platform_credential("facebook", "app_secret") or cfg.FB_APP_SECRET

    return {"success": True, "platform": platform}


@router.delete("/api/platform-credentials/{platform}")
async def delete_platform_credentials(platform: str):
    """Delete platform OAuth credentials."""
    platform = (platform or "").strip().lower()
    creds = _load_platform_credentials()
    if platform in creds:
        del creds[platform]
        _save_platform_credentials(creds)
    return {"success": True, "platform": platform}


# ═══════════════════════════════════════════════════════════════════════════════
# Usage / Credits
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/api/usage")
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
        "history": data.get("history", [])[-50:],
    }


@router.post("/api/usage/reset")
async def reset_usage():
    """Reset usage credits (for new billing period)."""
    data = _load_usage()
    data["credits_used"] = 0
    data["history"] = []
    _save_usage(data)
    return {"success": True, "credits_used": 0}
