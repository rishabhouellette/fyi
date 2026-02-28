"""Background scheduler: polls for due posts and publishes them."""
import os
import asyncio
from datetime import datetime
from typing import Any

from fastapi import HTTPException

from core.config import db
from core.models import FacebookUploadRequest, YouTubeUploadRequest
from services.platforms import (
    _facebook_upload_video_impl,
    youtube_upload_video_impl,
    _instagram_publish_internal,
)


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
    errors: dict[str, str] = {}
    selected_accounts = payload.get("accounts") if isinstance(payload.get("accounts"), dict) else {}
    for platform in (post.get("platforms") or []):
        p = str(platform).strip().lower()
        try:
            if p in {"facebook", "fb"}:
                external_fb = None
                try:
                    external_fb = (payload.get("external") or {}).get("facebook") if isinstance(payload.get("external"), dict) else None
                except Exception:
                    external_fb = None

                if isinstance(external_fb, dict) and external_fb.get("scheduled_publish_time"):
                    results["facebook"] = {
                        "success": True,
                        "platform": "facebook",
                        "scheduled": True,
                        "video_id": external_fb.get("video_id"),
                        "account_id": external_fb.get("account_id"),
                    }
                else:
                    results["facebook"] = await _facebook_upload_video_impl(
                        FacebookUploadRequest(
                            account_id=(selected_accounts.get("facebook") if isinstance(selected_accounts, dict) else None),
                            file_id=media_id,
                            title=title,
                            description=caption,
                            scheduled_publish_time=None,
                        )
                    )
            elif p in {"youtube", "yt"}:
                external_yt = None
                try:
                    external_yt = (payload.get("external") or {}).get("youtube") if isinstance(payload.get("external"), dict) else None
                except Exception:
                    external_yt = None

                if isinstance(external_yt, dict) and external_yt.get("publish_at"):
                    results["youtube"] = {
                        "success": True,
                        "platform": "youtube",
                        "scheduled": True,
                        "video_id": external_yt.get("video_id"),
                        "account_id": external_yt.get("account_id"),
                    }
                else:
                    results["youtube"] = await youtube_upload_video_impl(
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
                # Skip if already published at scheduling time
                external_ig = None
                try:
                    external_ig = (payload.get("external") or {}).get("instagram") if isinstance(payload.get("external"), dict) else None
                except Exception:
                    external_ig = None

                if isinstance(external_ig, dict) and external_ig.get("published_now"):
                    results["instagram"] = {
                        "success": True,
                        "platform": "instagram",
                        "published_at_schedule_time": True,
                    }
                else:
                    results["instagram"] = await _instagram_publish_internal(
                        (selected_accounts.get("instagram") if isinstance(selected_accounts, dict) else None),
                        media_id,
                        caption,
                        "REELS",
                    )
            else:
                errors[p] = f"Scheduling execution not implemented for platform '{platform}'"
                continue
        except Exception as e:
            errors[p] = str(e)

    if errors and not results:
        # Every platform failed
        combined = "; ".join(f"{k}: {v}" for k, v in errors.items())
        db.mark_scheduled_post_result(post["id"], "failed", results, combined)
        return

    error_summary = "; ".join(f"{k}: {v}" for k, v in errors.items()) if errors else None
    db.mark_scheduled_post_result(post["id"], "posted", results, error_summary)


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
            pass
        await asyncio.sleep(poll)
