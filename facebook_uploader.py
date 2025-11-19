"""
Facebook Video Uploader with Multi-Account Support
Handles video uploads, scheduling, cross-posting to Instagram, and thumbnails
Merged/Improved from old version: Dynamic chunking, better scheduling fetch, thumbnail extraction
FIXED: Separate thumbnail upload post-finish; Retry on connection errors; Larger chunks (~4 max)
FINAL: Multipart file upload for thumbnails (fixes base64 400 errors); Compression + retries

CROSS-POSTING TO INSTAGRAM:
For cross-posting to work, ensure the Facebook page token has these OAuth scopes:
- instagram_content_publish
- instagram_business_content_publish
- pages_manage_posts

If cross-posting fails with OAuthException #10, see OAUTH_SCOPES_FIX.md
"""
import os
import json
import time
import requests
from requests.adapters import HTTPAdapter
import base64
import cv2  # For thumbnail frame extraction
import numpy as np  # For thumbnail compression (if needed)
from pathlib import Path
from typing import Callable, Tuple, Optional, List
from datetime import datetime
from logger_config import get_logger
from config import get_config
from account_manager import get_account_manager, Account
from exceptions import (
    UploadError,
    NetworkError,
    AccountNotLinkedError,
    RateLimitError,
    VideoProcessingError,
)

logger = get_logger(__name__)
config = get_config()
account_manager = get_account_manager()

# Cache file for last scheduled times (per page_id)
CACHE_FILE = config.data_dir / "last_schedules.json"

def _load_cache() -> dict:
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Expire entries older than 24h
            now = datetime.now().timestamp()
            data = {k: v for k, v in data.items() if now - v < 86400}
            return data
    except Exception:
        logger.debug("Failed to read schedule cache")
    return {}

def _save_cache(data: dict):
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        logger.debug("Failed to write schedule cache")

def get_last_scheduled_time(page_id: str) -> Optional[float]:
    data = _load_cache()
    val = data.get(page_id)
    return float(val) if val else None

def update_last_scheduled_time(page_id: str, timestamp: float):
    data = _load_cache()
    data[page_id] = float(timestamp)
    _save_cache(data)

# ----------------------------------------------------------------------
# FacebookUploader class – one instance per account
# ----------------------------------------------------------------------
class FacebookUploader:
    API_VERSION = "v20.0"
    BASE_URL = f"https://graph.facebook.com/{API_VERSION}"
    UPLOAD_URL = f"https://graph-video.facebook.com/{API_VERSION}"  # Correct for videos

    def __init__(self, account_id: str):
        self.account_id = account_id
        self.account = account_manager.get_account(account_id)
        if not self.account:
            raise AccountNotLinkedError(f"Account {account_id} not found")
        if self.account.platform != "facebook":
            raise ValueError(f"Account {account_id} is not a Facebook account")
        if not self.account.is_token_valid():
            raise AccountNotLinkedError(f"Token expired for {self.account.name}")

        self.access_token = self.account.access_token
        self.page_id = self.account.page_id
        self.page_name = getattr(self.account, "page_name", None) or f"Page {self.page_id}"
        self.session = self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        adapter = HTTPAdapter(pool_connections=4, pool_maxsize=4, max_retries=config.max_retries)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        session.headers.update({"Connection": "keep-alive"})
        return session

    def _calculate_chunk_size(self, file_size: int) -> int:
        # Allow tuning via CHUNK_SIZE_MB env, but never drop below 50MB for throughput
        base_chunk_mb = max(config.chunk_size_mb, 50)
        base_chunk = base_chunk_mb * 1024 * 1024
        target_chunks = 3  # Aim for ~3 chunks for very large files
        adaptive_chunk = max(base_chunk, file_size // target_chunks if file_size > base_chunk else file_size)
        # Cap to 180MB to avoid Graph API timeouts on poor networks
        return min(adaptive_chunk, 180 * 1024 * 1024)

    # ------------------------------------------------------------------
    # Public upload entry-point (Added thumbnail support)
    # ------------------------------------------------------------------
    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        status_callback: Callable[[str], None],
        scheduled_time: Optional[int] = None,
        cross_post_to_instagram: bool = True,
        thumbnail_path: Optional[str] = None,  # NEW: Custom thumbnail path (or auto-gen)
    ) -> Tuple[bool, str, Optional[str]]:
        video_path = Path(video_path)
        if not video_path.is_file():
            return False, "Video file not found", None

        logger.info(f"Starting Facebook upload: {video_path.name}")
        try:
            # Rate-limit check (non-blocking)
            self._check_rate_limit()

            # Upload
            status_callback("Uploading video to Facebook...")
            video_id = self._upload_resumable(str(video_path), description, status_callback, scheduled_time, thumbnail_path)
            if not video_id:
                return False, "Upload failed – no video ID returned", None

            # Cross-post (only for instant uploads)
            if cross_post_to_instagram and not scheduled_time:
                self._cross_post_to_instagram(video_id, description)
            # Update schedule cache for this page if scheduled
            if scheduled_time:
                try:
                    update_last_scheduled_time(self.page_id, int(scheduled_time))
                    logger.debug(f"Updated schedule cache for page {self.page_id} -> {scheduled_time}")
                except Exception:
                    logger.debug("Failed to update schedule cache after upload")

            logger.info(f"Video uploaded: {video_id}")
            return True, f"Success! Video ID: {video_id}", video_id

        except Exception as exc:
            logger.error(f"Upload failed: {exc}")
            if hasattr(exc, 'response') and exc.response:
                logger.error(f"Facebook API Error Response: {exc.response.text}")
            return False, str(exc), None

    # ------------------------------------------------------------------
    # Resumable upload (chunked) – FIXED: Larger chunks (~4), retries on finish
    # ------------------------------------------------------------------
    def _upload_resumable(
        self,
        video_path: str,
        description: str,
        status_callback: Callable[[str], None],
        scheduled_time: Optional[int],
        thumbnail_path: Optional[str],
    ) -> Optional[str]:
        file_size = Path(video_path).stat().st_size
        init_url = f"{self.UPLOAD_URL}/{self.page_id}/videos"
        start_time = datetime.now().timestamp()  # For polling match

        chunk_size = self._calculate_chunk_size(file_size)
        num_chunks = (file_size + chunk_size - 1) // chunk_size  # Ceiling div

        # ---- 1. INIT SESSION -------------------------------------------------
        try:
            resp = self.session.post(
                init_url,
                params={
                    "access_token": self.access_token,
                    "upload_phase": "start",
                    "file_size": file_size,
                },
                timeout=30
            )
            resp.raise_for_status()
            data = resp.json()
            session_id = data.get("upload_session_id")
            if not session_id:
                raise UploadError("No upload session ID")
            logger.info(f"Session ID: {session_id} (Planning {num_chunks} chunks)")
        except Exception as e:
            logger.error(f"INIT FAILED: {e}")
            if hasattr(e, "response") and e.response:
                logger.error(f"FB says: {e.response.text}")
            raise

        video_id = data.get("video_id")  # Grab early if available

        # ---- 2. FIXED LARGE CHUNKED TRANSFER --------------------------------------------
        offset = 0
        chunk_num = 1
        min_chunk = 15 * 1024 * 1024  # 15MB floor helps avoid 413
        p = Path(video_path)  # Cache for name/suffix

        def _recalc_chunk_count(current_size: int) -> int:
            return max(1, (file_size + current_size - 1) // current_size)

        num_chunks = _recalc_chunk_count(chunk_size)

        with open(video_path, "rb") as f:
            while offset < file_size:
                current_chunk_size = min(chunk_size, file_size - offset)
                f.seek(offset)
                chunk = f.read(current_chunk_size)
                if not chunk:
                    break

                while True:
                    try:
                        files = {
                            "video_file_chunk": (p.name, chunk, f"video/{p.suffix[1:]}")
                        }

                        upload_resp = self.session.post(
                            init_url,
                            params={
                                "access_token": self.access_token,
                                "upload_phase": "transfer",
                                "upload_session_id": session_id,
                                "start_offset": offset,
                            },
                            files=files,
                            timeout=120
                        )
                        upload_resp.raise_for_status()
                        new_offset = int(upload_resp.json().get("start_offset", offset + len(chunk)))
                        offset = new_offset

                        pct = int(offset * 100 / file_size)
                        status_callback(f"Uploading {pct}% (Chunk {chunk_num}/{num_chunks})")
                        logger.info(f"Uploaded {pct}% (Chunk {chunk_num}/{num_chunks})")
                        chunk_num += 1
                        break

                    except requests.exceptions.HTTPError as e:
                        status_code = getattr(e.response, "status_code", None)
                        if status_code == 413 and chunk_size > min_chunk:
                            chunk_size = max(min_chunk, chunk_size // 2)
                            num_chunks = _recalc_chunk_count(chunk_size)
                            current_chunk_size = min(chunk_size, file_size - offset)
                            f.seek(offset)
                            chunk = f.read(current_chunk_size)
                            logger.warning(
                                "Chunk rejected (413). Reducing chunk size to %d MB and retrying.",
                                chunk_size // (1024 * 1024)
                            )
                            continue
                        logger.error(f"CHUNK FAILED at {offset}: {e}")
                        if hasattr(e, "response") and e.response:
                            logger.error(f"FB says: {e.response.text}")
                        else:
                            logger.error("No response from Facebook.")
                        raise
                    except Exception as e:
                        logger.error(f"CHUNK FAILED at {offset}: {e}")
                        if hasattr(e, "response") and e.response:
                            logger.error(f"FB says: {e.response.text}")
                        else:
                            logger.error("No response from Facebook.")
                        raise

        # ---- 3. THUMBNAIL PREP (NEW: Auto-gen or use provided) ----------------------------------
        thumb_file_data = None
        thumb_filename = None
        if thumbnail_path:
            # Use custom path
            try:
                thumb_filename = Path(thumbnail_path).name
                with open(thumbnail_path, "rb") as thumb_file:
                    thumb_file_data = thumb_file.read()
                logger.info("Using custom thumbnail")
            except Exception as e:
                logger.warning(f"Custom thumbnail load failed: {e}")
        else:
            # Auto-extract frame (mid-video)
            try:
                cap = cv2.VideoCapture(video_path)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)  # Mid-frame
                ret, frame = cap.read()
                if ret:
                    # Resize to FB rec (1200x1200 max, square crop)
                    height, width = frame.shape[:2]
                    size = min(width, height)
                    y = (height - size) // 2
                    x = (width - size) // 2
                    frame = frame[y:y+size, x:x+size]
                    frame = cv2.resize(frame, (1200, 1200), interpolation=cv2.INTER_AREA)
                    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 90])
                    thumb_file_data = buffer.tobytes()
                    thumb_filename = "thumb.jpg"
                    logger.info("Auto-generated thumbnail from mid-frame")
                cap.release()
            except Exception as e:
                logger.warning(f"Thumbnail generation failed: {e} (skipping)")

        # ---- 4. FINISH WITH RETRIES + SEPARATE THUMB UPLOAD ----------------------------------
        finish_params = {
            "access_token": self.access_token,
            "upload_phase": "finish",
            "upload_session_id": session_id,
            "title": p.stem,
            "description": description,
        }
        if scheduled_time:
            finish_params["published"] = "false"
            # Ensure scheduled_publish_time is an integer (epoch seconds)
            try:
                finish_params["scheduled_publish_time"] = int(scheduled_time)
            except Exception:
                finish_params["scheduled_publish_time"] = scheduled_time
        else:
            finish_params["published"] = "true"

        # Retry logic for finish (up to 3x, backoff)
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Log the finish params at INFO so we can see them in normal runs
                logger.info(f"Finish params: {finish_params}")
                resp = self.session.post(init_url, params=finish_params, timeout=120)  # Bumped timeout
                resp.raise_for_status()
                finish_data = resp.json()
                logger.info(f"Finish response (attempt {attempt+1}): {finish_data}")
                video_id = finish_data.get("video_id") or video_id or finish_data.get("id")
                if video_id:
                    break  # Success
                else:
                    raise UploadError("No video ID in finish response")
            except (requests.exceptions.ConnectionError, ConnectionResetError) as e:
                logger.warning(f"Finish connection error (attempt {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s
                    continue
                raise
            except Exception as e:
                logger.error(f"FINISH FAILED (attempt {attempt+1}): {e}")
                if hasattr(e, "response") and e.response:
                    logger.error(f"FB says: {e.response.text}")
                raise

        if not video_id:
            # Fallback poll if still no ID
            logger.info("No video ID from finish – polling...")
            status_callback("Finishing upload (polling for ID)...")
            for poll_attempt in range(6):
                time.sleep(5)
                if self._is_video_ready(video_id):  # If partial ID
                    break
                videos_resp = self.session.get(
                    f"{self.BASE_URL}/{self.page_id}/videos",
                    params={"access_token": self.access_token, "fields": "id,created_time,title", "limit": 5},
                    timeout=10
                )
                videos_resp.raise_for_status()
                videos = videos_resp.json().get("data", [])
                for vid in videos:
                    vid_time = datetime.fromisoformat(vid.get("created_time", "").rstrip("Z")).timestamp()
                    if (abs(vid_time - start_time) < 60 and vid.get("title") == p.stem):
                        video_id = vid.get("id")
                        if video_id:
                            logger.info(f"Polled video ID: {video_id}")
                            break
                status_callback(f"Polling attempt {poll_attempt+1}/6...")
            if not video_id:
                raise UploadError("No video ID found after polling")

        # If this was a scheduled upload, attempt a few debug queries to confirm the scheduled resource exists.
        if scheduled_time:
            try:
                # Build endpoints
                posts_url = f"{self.BASE_URL}/{self.page_id}/scheduled_posts"
                posts_params = {"access_token": self.access_token, "fields": "id,title,scheduled_publish_time,attachments{media}", "limit": 50}
                videos_url = f"{self.BASE_URL}/{self.page_id}/videos"
                videos_params = {"access_token": self.access_token, "fields": "id,title,scheduled_publish_time,created_time", "limit": 50}

                found = False
                for attempt in range(4):
                    time.sleep(2 ** attempt)
                    try:
                        pr = self.session.get(posts_url, params=posts_params, timeout=20)
                        pr.raise_for_status()
                        pitems = pr.json().get("data", [])
                        for p in pitems:
                            # check if this post references our video id or scheduled time
                            if p.get("scheduled_publish_time") and int(p.get("scheduled_publish_time")) == int(scheduled_time):
                                logger.info(f"Scheduled post discovered in /scheduled_posts (id={p.get('id')}) matching scheduled_time")
                                found = True
                                break
                        if found:
                            break
                    except Exception as e:
                        logger.debug(f"Scheduled posts probe failed (attempt {attempt+1}): {e}")

                if not found:
                    # Probe /videos endpoint
                    for attempt in range(4):
                        time.sleep(2 ** attempt)
                        try:
                            vr = self.session.get(videos_url, params=videos_params, timeout=20)
                            vr.raise_for_status()
                            vitems = vr.json().get("data", [])
                            for v in vitems:
                                if v.get("scheduled_publish_time") and int(v.get("scheduled_publish_time")) == int(scheduled_time):
                                    logger.info(f"Scheduled video discovered in /videos (id={v.get('id')}) matching scheduled_time")
                                    found = True
                                    break
                            if found:
                                break
                        except Exception as e:
                            logger.debug(f"Videos probe failed (attempt {attempt+1}): {e}")

                if not found:
                    logger.warning("Scheduled upload completed but no matching scheduled post/video found in quick probes (FB may still be propagating)")
            except Exception as e:
                logger.debug(f"Error during scheduled-post verification probes: {e}")

        # ---- 5. UPLOAD THUMBNAIL SEPARATELY (FINAL: Multipart + retries + compress) ----------------------------------
        if thumb_file_data:
            # Optional: Compress more if big (under 1MB ideal)
            if len(thumb_file_data) > 1_000_000:  # Rough size check
                logger.info("Compressing thumbnail for upload")
                # Decode, resize smaller, re-encode
                nparr = np.frombuffer(thumb_file_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                img = cv2.resize(img, (800, 800), interpolation=cv2.INTER_AREA)  # Smaller
                _, buffer = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 80])
                thumb_file_data = buffer.tobytes()

            thumb_url = f"{self.BASE_URL}/{video_id}/thumbnails"
            thumb_params = {"access_token": self.access_token}
            files = {"source": (thumb_filename, thumb_file_data, "image/jpeg")}
            
            # Retry loop (up to 3x)
            for thumb_attempt in range(3):
                try:
                    thumb_resp = self.session.post(thumb_url, params=thumb_params, files=files, timeout=60)
                    thumb_resp.raise_for_status()
                    logger.info("Thumbnail uploaded successfully")
                    break
                except (requests.exceptions.ConnectionError, ConnectionResetError) as e:
                    logger.warning(f"Thumb connection error (attempt {thumb_attempt+1}/3): {e}")
                    if thumb_attempt < 2:
                        time.sleep(2 ** thumb_attempt)  # Backoff
                        continue
                    logger.warning("Thumbnail upload failed after retries (video OK)")
                except Exception as e:
                    logger.warning(f"Thumbnail error: {e}")
                    break

        return video_id

    # ------------------------------------------------------------------
    # Borrowed from old: Video readiness check
    # ------------------------------------------------------------------
    def _is_video_ready(self, video_id: str) -> bool:
        if not video_id:
            return False
        try:
            resp = self.session.get(
                f"{self.BASE_URL}/{video_id}",
                params={'access_token': self.access_token, 'fields': 'status'},
                timeout=10
            ).json()
            status = resp.get('status', {}).get('video_status')
            return status == 'ready'
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Rate-limit helper (non-blocking)
    # ------------------------------------------------------------------
    def _check_rate_limit(self) -> None:
        try:
            url = f"{self.BASE_URL}/{self.page_id}/insights"
            params = {
                "metric": "page_posts_impressions",
                "period": "day",
                "access_token": self.access_token,
            }
            self.session.get(url, params=params, timeout=10).raise_for_status()
        except Exception as exc:
            logger.warning(f"Rate-limit check failed (continuing anyway): {exc}")

    # ------------------------------------------------------------------
    # Instagram cross-post (Simplified from old)
    # ------------------------------------------------------------------
    def _cross_post_to_instagram(self, video_id: str, description: str) -> None:
        """Cross-post a video to Instagram via the IG Content Publishing API.
        
        Challenge: Facebook videos are restricted and can't be directly downloaded by Instagram.
        Solution: Use the native FB→IG cross-post via the Page's /feed endpoint with attached_media.
        
        Required OAuth scopes:
        - instagram_content_publish
        - instagram_business_content_publish
        
        If this fails with OAuthException #10, the token is missing required scopes.
        See OAUTH_SCOPES_FIX.md for troubleshooting.
        """
        ig_id = self._get_instagram_business_account()
        if not ig_id:
            logger.info("No linked Instagram account – skipping cross-post")
            return
        
        logger.info(f"Cross-posting FB video {video_id} to IG account {ig_id}")
        
        try:
            # Use the native cross-post method: attach media to the Page feed with instagram_actor_id
            # This tells Facebook to also publish to the linked Instagram account
            feed_url = f"{self.BASE_URL}/{self.page_id}/feed"
            feed_payload = {
                "message": description,
                "attached_media": [{"media_fbid": video_id}],  # Pass as list, not JSON string
                "instagram_actor_id": ig_id,
                "access_token": self.access_token,
            }
            
            logger.info(f"Posting to Page feed with cross-post to IG")
            resp = self.session.post(feed_url, json=feed_payload, timeout=30)
            logger.info(f"Page feed response: HTTP {resp.status_code}")
            
            if resp.status_code == 200:
                result = resp.json()
                logger.info(f"✓ Successfully cross-posted to Instagram via feed: {result}")
                return
            else:
                logger.info(f"Feed post response: {resp.text}")
        
        except Exception as exc:
            exc_str = str(exc)
            logger.warning(f"Cross-post via feed exception: {exc}")
            # Check if it's an OAuth scope issue
            if "OAuthException" in exc_str or "Permission denied" in exc_str.lower():
                logger.error("This appears to be an OAuth scope issue (OAuthException #10).")
                logger.error("The token is missing required Instagram publishing scopes.")
                logger.error("See OAUTH_SCOPES_FIX.md for resolution steps.")
        
        # Fallback: Try using form data instead of JSON
        try:
            logger.info("Trying cross-post with form-encoded data")
            feed_url = f"{self.BASE_URL}/{self.page_id}/feed"
            feed_payload = {
                "message": description,
                "attached_media": json.dumps([{"media_fbid": video_id}]),
                "instagram_actor_id": ig_id,
                "access_token": self.access_token,
            }
            
            resp = self.session.post(feed_url, data=feed_payload, timeout=30)
            logger.info(f"Form-encoded feed response: HTTP {resp.status_code}")
            
            if resp.status_code == 200:
                result = resp.json()
                logger.info(f"✓ Successfully cross-posted (form-encoded): {result}")
                return
            else:
                logger.info(f"Form-encoded response: {resp.text}")
        
        except Exception as exc:
            logger.warning(f"Form-encoded cross-post exception: {exc}")
        
        logger.warning(f"Instagram cross-post failed for video {video_id}. "
                      f"This may require the app to be in production mode (not Development). "
                      f"Check: https://developers.facebook.com/apps > Settings > Basic > App Mode")


    def _get_instagram_business_account(self) -> Optional[str]:
        try:
            url = f"{self.BASE_URL}/{self.page_id}"
            params = {"fields": "instagram_business_account", "access_token": self.access_token}
            resp = self.session.get(url, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            ig = data.get("instagram_business_account")
            return ig.get("id") if ig else None
        except Exception as exc:
            logger.warning(f"Failed to fetch Instagram account: {exc}")
            return None


# ----------------------------------------------------------------------
# Public helpers (Merged: Use old's /scheduled_posts but filter videos)
# ----------------------------------------------------------------------
def create_facebook_uploader(account_id: str) -> FacebookUploader:
    return FacebookUploader(account_id)


def get_scheduled_videos(page_id: Optional[str] = None, access_token: Optional[str] = None) -> List[dict]:
    if not page_id or not access_token:
        accounts = account_manager.get_accounts_by_platform("facebook")
        if not accounts:
            return []
        acct = accounts[0]
        page_id = acct.page_id
        access_token = acct.access_token
    # First: query /scheduled_posts (page post objects)
    posts_url = f"https://graph.facebook.com/v20.0/{page_id}/scheduled_posts"
    posts_params = {
        "access_token": access_token,
        "fields": "id,title,scheduled_publish_time,attachments{media}",
        "limit": 100,
    }

    videos: List[dict] = []
    try:
        resp = requests.get(posts_url, params=posts_params, timeout=30)
        resp.raise_for_status()
        posts = resp.json().get("data", [])
        for p in posts:
            if "scheduled_publish_time" in p:
                attachments = p.get("attachments", {}).get("data", [])
                for att in attachments:
                    media = att.get("media")
                    if media and media.get("type") == "video":
                        videos.append(p)
                        break
    except Exception as exc:
        logger.debug(f"Failed to fetch /scheduled_posts: {exc}")

    # Second: query /{page_id}/videos — some scheduled videos appear as video objects
    videos_url = f"https://graph.facebook.com/v20.0/{page_id}/videos"
    videos_params = {
        "access_token": access_token,
        "fields": "id,title,scheduled_publish_time,created_time",
        "limit": 100,
    }
    try:
        vresp = requests.get(videos_url, params=videos_params, timeout=30)
        vresp.raise_for_status()
        vdata = vresp.json().get("data", [])
        for v in vdata:
            if "scheduled_publish_time" in v:
                # Represent video objects similarly to posts for caller convenience
                videos.append(v)
    except Exception as exc:
        logger.debug(f"Failed to fetch /videos: {exc}")

    # Log debug counts from both endpoints (avoid INFO spam)
    logger.debug(f"Scheduled discovery: total candidates={len(videos)} (posts+videos)")
    return videos


def get_page_access_token() -> Optional[str]:
    accounts = account_manager.get_accounts_by_platform("facebook")
    return accounts[0].access_token if accounts else None


def upload_video_to_facebook(
    video_path: str,
    title: str,
    description: str,
    status_callback: Callable[[str], None],
    scheduled_time: Optional[int] = None,
    page_id: Optional[str] = None,
    access_token: Optional[str] = None,
    thumbnail_path: Optional[str] = None,  # NEW
) -> Tuple[bool, str, Optional[str]]:
    accounts = account_manager.get_accounts_by_platform("facebook")
    if not accounts:
        return False, "No Facebook account linked", None

    acct = None
    if page_id:
        # FIXED: Find account matching the provided page_id
        for a in accounts:
            if a.page_id == page_id:
                acct = a
                break
        if not acct:
            return False, f"No account found for page_id {page_id}", None
    else:
        # Fallback to first account
        acct = accounts[0]

    # Create uploader with the correct account_id
    uploader = FacebookUploader(acct.account_id)
    # Override with provided values (in case token updated or specific page)
    if page_id:
        uploader.page_id = page_id
    if access_token:
        uploader.access_token = access_token

    return uploader.upload_video(
        video_path,
        title,
        description,
        status_callback,
        scheduled_time,
        cross_post_to_instagram=False,
        thumbnail_path=thumbnail_path,
    )


__all__ = [
    "FacebookUploader",
    "create_facebook_uploader",
    "upload_video_to_facebook",
    "get_scheduled_videos",
    "get_page_access_token",
]