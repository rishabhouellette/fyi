"""
Instagram Video Uploader - FINAL WORKING VERSION
Uploads videos to Instagram by posting through connected Facebook page
This is the ONLY method that works reliably with Instagram Graph API

KEY INSIGHT: Instagram Graph API ONLY accepts Facebook Page Access Tokens
            Using Instagram User Tokens will ALWAYS fail with error 190
            Solution: Upload through the Facebook page that's connected to Instagram
"""
import os
import json
import time
import requests
from pathlib import Path
from typing import Callable, Tuple, Optional, List
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
    BASE_URL = f"https://graph.facebook.com/{API_VERSION}"
    
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

    @staticmethod
    def create_uploader(account_id: str):
        return InstagramUploader(account_id)

    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        status_callback: Callable[[str], None],
        scheduled_timestamp=None,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Upload video to Instagram.
        
        Args:
            video_path: Path to video file
            title: Video title
            description: Video description/caption
            status_callback: Callback for progress updates
            scheduled_timestamp: Unix timestamp for scheduled posting (Instagram doesn't support this via API)
        
        Returns:
            Tuple of (success: bool, message: str, video_id: Optional[str])
        """
        try:
            if scheduled_timestamp:
                logger.warning("Instagram API does not support scheduled posts. Publishing immediately.")
            
            video_id = self._upload_reel(video_path, description or title, status_callback)
            return True, f"Instagram Video ID: {video_id}", video_id
        except Exception as exc:
            error_msg = str(exc)
            logger.error(f"Instagram upload error: {error_msg}")
            return False, error_msg, None

    def _upload_reel(
        self,
        video_path: str,
        caption: str,
        status_callback: Callable[[str], None],
    ) -> Optional[str]:
        """
        Upload video to Instagram using Facebook Page Access Token.
        
        CRITICAL: Instagram Content Publishing API requires a Facebook Page Access Token
                 from the page that's connected to the Instagram account.
                 Instagram User tokens DO NOT WORK with the Content Publishing API.
        """
        try:
            caption = caption[:2200] if caption else ""
            
            # Get Instagram Business Account ID
            ig_user_id = self.account.page_id
            
            # CRITICAL: Must use Facebook Page Access Token (not Instagram token)
            # Get the connected Facebook page
            facebook_accounts = account_manager.get_accounts_by_platform("facebook")
            if not facebook_accounts:
                raise UploadError(
                    "SETUP REQUIRED:\n"
                    "Instagram uploads require a connected Facebook Page.\n\n"
                    "Steps:\n"
                    "1. Go to Upload → Facebook tab\n"
                    "2. Click 'Link New Account'\n"
                    "3. Connect your Facebook Page\n"
                    "4. Make sure this Facebook Page is connected to your Instagram account"
                )
            
            # Try to find Facebook page by matching name
            fb_account = None
            for fb_acc in facebook_accounts:
                if getattr(fb_acc, 'name', '') == getattr(self.account, 'name', ''):
                    fb_account = fb_acc
                    break
            
            # Use first Facebook page if no match
            if not fb_account:
                fb_account = facebook_accounts[0]
            
            fb_page_id = getattr(fb_account, 'page_id', None)
            fb_page_token = getattr(fb_account, 'access_token', None)
            
            if not fb_page_id or not fb_page_token:
                raise UploadError("Facebook page token is missing")
            
            logger.info(f"Using Facebook Page: {fb_page_id} → Instagram: {ig_user_id}")
            logger.info(f"Page token (first 20): {fb_page_token[:20]}...")
            
            # Step 1: Create media container with resumable upload
            # IMPORTANT: Instagram Business actions live under graph.facebook.com
            create_media_url = f"https://graph.facebook.com/v20.0/{ig_user_id}/media"
            
            status_callback("10% - Creating media container...")
            
            # Get file size for upload
            file_size = Path(video_path).stat().st_size
            
            # Create container with resumable upload type
            create_params = {
                "access_token": fb_page_token,
                "media_type": "REELS",
                "upload_type": "resumable",  # CRITICAL: Required for video upload
                "caption": caption,
            }
            
            logger.debug(f"Creating resumable upload container")
            status_callback("20% - Preparing upload session...")
            
            create_resp = requests.post(
                create_media_url,
                data=create_params,
                timeout=60
            )
                
            logger.debug(f"Container response: {create_resp.status_code}")
            logger.debug(f"Container body: {create_resp.text[:400]}")
            
            if create_resp.status_code != 200:
                logger.error(f"Full response: {create_resp.text}")
                create_resp.raise_for_status()
            
            create_result = create_resp.json()
            
            if "error" in create_result:
                error_info = create_result.get("error", {})
                error_msg = error_info.get("message", "Unknown")
                error_code = error_info.get("code", "N/A")
                raise UploadError(f"Container error {error_code}: {error_msg}")
            
            if "id" not in create_result:
                raise UploadError(f"No container ID returned")
            
            container_id = create_result.get("id")
            upload_url = create_result.get("upload_url") or create_result.get("uri")
            logger.info(f"✓ Container created: {container_id}")
            if upload_url:
                logger.debug(f"Upload URL provided: {upload_url}")
            
            # Step 2: Upload video to resumable endpoint
            if not upload_url:
                upload_url = f"https://rupload.facebook.com/ig-api-upload/v20.0/{container_id}"
                logger.debug("Upload URL missing; using ig-api-upload fallback")
            
            logger.debug(f"Uploading video to {upload_url}")
            status_callback("50% - Uploading video...")
            
            with open(video_path, "rb") as video_file:
                video_data = video_file.read()
            upload_headers = {
                "Authorization": f"OAuth {fb_page_token}",
                "offset": "0",
                "file_size": str(file_size),
                "Content-Type": "application/octet-stream",
                "Content-Length": str(file_size),
                "X-Entity-Length": str(file_size),
                "X-Entity-Name": container_id,
                "X-Entity-Type": "video/mp4",
                "Accept": "*/*",
            }
            upload_resp = requests.post(
                upload_url,
                headers=upload_headers,
                data=video_data,
                timeout=600
            )
            
            logger.debug(f"Upload response: {upload_resp.status_code}")
            logger.debug(f"Body: {upload_resp.text[:200]}")
            
            if upload_resp.status_code != 200:
                logger.error(f"Upload failed: {upload_resp.text}")
                upload_resp.raise_for_status()
            
            upload_result = upload_resp.json()
            
            if not upload_result.get("success"):
                raise UploadError(f"Upload failed: {upload_result}")
            
            logger.info(f"✓ Video uploaded successfully")
            
            # Step 3: Publish the media using /media_publish endpoint
            publish_url = f"https://graph.facebook.com/v20.0/{ig_user_id}/media_publish"
            
            status_callback("80% - Publishing to Instagram...")
            
            publish_params = {
                "access_token": fb_page_token,
                "creation_id": container_id,  # Use container ID
            }
            
            logger.debug(f"Publishing container {container_id}")
            
            publish_resp = requests.post(
                publish_url,
                data=publish_params,
                timeout=60
            )
            
            logger.debug(f"Publish response: {publish_resp.status_code}")
            logger.debug(f"Body: {publish_resp.text[:200]}")
            
            if publish_resp.status_code != 200:
                logger.error(f"Full response: {publish_resp.text}")
                publish_resp.raise_for_status()
            
            publish_result = publish_resp.json()
            
            if "error" in publish_result:
                error_info = publish_result.get("error", {})
                error_msg = error_info.get("message", "Unknown")
                error_code = error_info.get("code", "N/A")
                raise UploadError(f"Publish error {error_code}: {error_msg}")
            
            if "id" not in publish_result:
                raise UploadError(f"No media ID returned")
            
            media_id = publish_result.get("id")
            logger.info(f"✓ Reel published to Instagram: {media_id}")
            status_callback("100% - Complete!")
            
            return media_id
        
        except Exception as exc:
            error_msg = str(exc)
            logger.error(f"Upload failed: {error_msg}")
            status_callback(f"ERROR: {error_msg}")
            raise


# Module-level functions for compatibility
def upload_video_to_instagram(
    video_path: str,
    title: str,
    status_callback: Callable[[str], None],
) -> Tuple[bool, str, Optional[str]]:
    """
    Upload video to Instagram.
    
    This is called by main.py during instant upload.
    """
    try:
        # Get default Instagram account
        ig_accounts = account_manager.get_accounts_by_platform("instagram")
        if not ig_accounts:
            return False, "No Instagram account linked", None
        
        # Use first account
        uploader = InstagramUploader.create_uploader(ig_accounts[0].account_id)
        return uploader.upload_video(
            video_path,
            Path(video_path).stem,
            Path(video_path).stem,
            status_callback
        )
    except Exception as exc:
        logger.error(f"Failed to upload to Instagram: {exc}")
        return False, str(exc), None


def create_instagram_uploader(account_id: str) -> InstagramUploader:
    """Create an Instagram uploader for the given account"""
    return InstagramUploader.create_uploader(account_id)
