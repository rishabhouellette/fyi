"""
Instagram Video Uploader
Handles video uploads to Instagram (Reels and Feed videos)

OAUTH SCOPE REQUIREMENTS:
- instagram_content_publish (required for publishing)
- instagram_business_content_publish (required for business accounts)
- pages_manage_posts (required for Facebook page integration)

If receiving OAuthException #10, see OAUTH_SCOPES_FIX.md for troubleshooting.
"""
import os
import json
import time
import requests
from pathlib import Path
from typing import Callable, Tuple, Optional, List
from urllib.parse import urlencode
from logger_config import get_logger
from config import get_config
from account_manager import get_account_manager
from exceptions import (
    UploadError,
    AccountNotLinkedError,
)

logger = get_logger(__name__)
config = get_config()
account_manager = get_account_manager()


class InstagramUploader:
    API_VERSION = "v20.0"
    BASE_URL = f"https://graph.instagram.com/{API_VERSION}"
    
    # Required OAuth scopes for Instagram publishing
    REQUIRED_SCOPES = [
        'instagram_content_publish',
        'instagram_business_content_publish',
    ]

    def __init__(self, account_id: str):
        self.account_id = account_id
        self.account = account_manager.get_account(account_id)
        if not self.account:
            raise AccountNotLinkedError(f"Account {account_id} not found")
        if self.account.platform != "instagram":
            raise ValueError(f"Account {account_id} is not an Instagram account")
        if not self.account.is_token_valid():
            raise AccountNotLinkedError(f"Token expired for {self.account.name}")

        self.access_token = self.account.access_token
        self.ig_user_id = getattr(self.account, "ig_user_id", None)
        self.username = getattr(self.account, "username", None)

    def upload_video(
        self,
        video_path: str,
        caption: str,
        status_callback: Callable[[str], None],
    ) -> Tuple[bool, str, Optional[str]]:
        """Upload video to Instagram (Reel or Feed video)"""
        video_path = Path(video_path)
        if not video_path.is_file():
            return False, "Video file not found", None

        logger.info(f"Starting Instagram upload: {video_path.name}")
        try:
            # Check OAuth scopes before attempting upload
            scopes_ok, scope_msg = self._check_oauth_scopes()
            if not scopes_ok:
                logger.warning(f"OAuth scope issue: {scope_msg}")
                # Log warning but continue - might still work if scopes are sufficient
                logger.info("Attempting upload despite scope warning. If it fails with OAuthException #10, see OAUTH_SCOPES_FIX.md")
            else:
                logger.info("✓ Required OAuth scopes verified")
            
            status_callback("Uploading video to Instagram...")
            
            # Get the IG user ID if not already set
            if not self.ig_user_id:
                self.ig_user_id = self._get_ig_user_id()
            
            if not self.ig_user_id:
                return False, "Unable to determine Instagram user ID", None

            # For now, use simple video upload (Reels or Feed)
            # Note: Reels require specific handling and may need container creation
            video_id = self._upload_reel(str(video_path), caption, status_callback)
            
            if not video_id:
                return False, "Upload failed – no video ID returned", None

            logger.info(f"Video uploaded to Instagram: {video_id}")
            return True, f"Success! Instagram Video ID: {video_id}", video_id

        except Exception as exc:
            logger.error(f"Instagram upload failed: {exc}")
            # Check if it's an OAuth scope issue
            error_str = str(exc)
            if "OAuthException" in error_str or "Permission denied" in error_str.lower():
                logger.error("This appears to be an OAuth scope issue. See OAUTH_SCOPES_FIX.md for help.")
            return False, str(exc), None

    def _check_oauth_scopes(self) -> Tuple[bool, str]:
        """
        Check if the access token has required OAuth scopes.
        
        Returns:
            Tuple of (scopes_ok: bool, message: str)
        """
        try:
            # Use debug_token endpoint to check scopes
            app_id = "2221888558294490"
            app_secret = "6f1c65510e626e9bb45fd5d2f52f8565"
            app_token = f"{app_id}|{app_secret}"
            
            resp = requests.get(
                "https://graph.facebook.com/debug_token",
                params={
                    "input_token": self.access_token,
                    "access_token": app_token
                },
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            
            if not data.get("data", {}).get("is_valid"):
                return False, "Access token is invalid or expired"
            
            granted_scopes = data.get("data", {}).get("scopes", [])
            logger.debug(f"Granted scopes: {granted_scopes}")
            
            # Check for at least one of the required scopes
            has_required = any(scope in granted_scopes for scope in self.REQUIRED_SCOPES)
            
            if not has_required:
                missing = [s for s in self.REQUIRED_SCOPES if s not in granted_scopes]
                return False, f"Missing required OAuth scopes: {', '.join(missing)}"
            
            return True, f"Token has required scopes: {[s for s in self.REQUIRED_SCOPES if s in granted_scopes]}"
        
        except requests.exceptions.Timeout:
            logger.warning("OAuth scope check timed out")
            return True, "Scope check timed out (proceeding anyway)"
        except Exception as exc:
            logger.warning(f"Could not verify OAuth scopes: {exc}")
            return True, f"Could not verify scopes: {str(exc)}"

    def _get_ig_user_id(self) -> Optional[str]:
        """Get Instagram user ID from account info or Facebook page"""
        try:
            # Try to get from account metadata first
            if hasattr(self.account, 'ig_user_id') and self.account.ig_user_id:
                return self.account.ig_user_id
            # If the stored page_id already looks like an Instagram user ID (starts with '178'),
            # return it directly. Some account entries store the IG id in `page_id`.
            page_id = getattr(self.account, 'page_id', None)
            if page_id and str(page_id).startswith('178'):
                return str(page_id)

            # Otherwise, try to fetch from Facebook page's Instagram business account
            if page_id:
                url = f"https://graph.facebook.com/v20.0/{page_id}"
                params = {"fields": "instagram_business_account", "access_token": self.access_token}
                resp = requests.get(url, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                ig = data.get("instagram_business_account")
                if ig:
                    return ig.get("id")
            
            return None
        except Exception as exc:
            logger.warning(f"Failed to fetch Instagram user ID: {exc}")
            return None

    def _upload_reel(
        self,
        video_path: str,
        caption: str,
        status_callback: Callable[[str], None],
    ) -> Optional[str]:
        """Upload a Reel to Instagram via direct Instagram Graph API endpoint"""
        try:
            # Truncate caption to Instagram's limit (2200 chars for captions)
            caption = caption[:2200] if caption else ""
            
            ig_user_id = self.account.page_id  # Instagram User ID (17841478154541888)
            
            logger.debug(f"Using Instagram User ID: {ig_user_id}")
            logger.debug(f"Access token (first 20 chars): {self.access_token[:20]}...")
            
            # Step 1: Upload video file to create media container on Instagram
            # Endpoint: POST /{ig-user-id}/media
            upload_url = f"https://graph.instagram.com/v20.0/{ig_user_id}/media"
            
            logger.debug(f"Uploading video to Instagram media endpoint: {upload_url}")
            
            status_callback("Starting upload to Instagram...")
            
            with open(video_path, "rb") as f:
                files = {"video": (Path(video_path).name, f, "video/mp4")}
                
                # Media creation parameters for Reel
                upload_params = {
                    "access_token": self.access_token,
                    "caption": caption,
                    "media_type": "REELS",  # This is the key - REELS for Reels, not regular VIDEO
                    "thumb_offset": 0,  # Thumbnail at start
                }
                
                logger.debug(f"Creating Reel media container on Instagram")
                status_callback("50% - Creating media container...")
                
                upload_resp = requests.post(upload_url, files=files, data=upload_params, timeout=300)
                
                # Log response for debugging
                logger.debug(f"Upload response status: {upload_resp.status_code}")
                
                upload_resp.raise_for_status()
                upload_data = upload_resp.json()
                
                if not upload_data.get("id"):
                    # Check if there's an error in the response
                    if "error" in upload_data:
                        error_info = upload_data.get("error", {})
                        raise UploadError(f"Instagram API error: {error_info.get('message', 'Unknown error')}")
                    raise UploadError(f"No media ID returned: {upload_data}")
                
                media_id = upload_data.get("id")
                logger.info(f"Reel media container created: {media_id}")
                status_callback("75% - Publishing to profile...")
            
            # Step 2: Publish the media (make it visible on profile)
            publish_url = f"https://graph.instagram.com/v20.0/{media_id}/publish"
            
            publish_params = {
                "access_token": self.access_token,
            }
            
            logger.debug(f"Publishing Reel to Instagram profile")
            publish_resp = requests.post(publish_url, params=publish_params, timeout=60)
            
            logger.debug(f"Publish response status: {publish_resp.status_code}")
            
            publish_resp.raise_for_status()
            publish_data = publish_resp.json()
            
            if not publish_data.get("id"):
                if "error" in publish_data:
                    error_info = publish_data.get("error", {})
                    raise UploadError(f"Instagram publish error: {error_info.get('message', 'Unknown error')}")
                raise UploadError(f"Publish failed: {publish_data}")
            
            published_id = publish_data.get("id")
            logger.info(f"Reel successfully published to Instagram: {published_id}")
            status_callback("100% - Upload complete!")
            return published_id
        
        except Exception as exc:
            logger.error(f"Reel upload failed: {exc}")
            status_callback(f"ERROR: {str(exc)}")
            # Log response body for debugging if available
            if hasattr(exc, 'response') and exc.response is not None:
                try:
                    error_data = exc.response.json()
                    error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                    error_code = error_data.get('error', {}).get('code', 'Unknown code')
                    logger.error(f"Instagram API error (Code {error_code}): {error_msg}")
                    
                    # Provide guidance based on error code
                    if error_code == 190:
                        logger.error("ERROR CODE 190: Invalid OAuth access token")
                        logger.error("SOLUTION: Token may be invalid. Try re-authenticating:")
                        logger.error("  1. Unlink the Instagram account from FYI Uploader")
                        logger.error("  2. Link it again with fresh authentication")
                    elif error_code == 100:
                        logger.error("ERROR CODE 100: Invalid parameter")
                        logger.error("SOLUTION: Check video format (MP4), duration (3-600s), and resolution (min 720px)")
                    elif error_code == 200:
                        logger.error("ERROR CODE 200: Permissions error")
                        logger.error("SOLUTION: Ensure your app has required Instagram permissions in Production mode")
                    
                except (ValueError, KeyError):
                    logger.error(f"Instagram API response: {exc.response.text}")
            raise


def upload_video_to_instagram(
    video_path: str,
    caption: str,
    status_callback: Callable[[str], None],
) -> Tuple[bool, str, Optional[str]]:
    """Wrapper function to upload video to Instagram using first available account"""
    accounts = account_manager.get_accounts_by_platform("instagram")
    if not accounts:
        return False, "No Instagram account linked", None

    account = accounts[0]
    uploader = InstagramUploader(account.account_id)
    return uploader.upload_video(video_path, caption, status_callback)


__all__ = [
    "InstagramUploader",
    "upload_video_to_instagram",
]