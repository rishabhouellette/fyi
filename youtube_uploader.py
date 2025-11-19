"""
YouTube Video Uploader with Multi-Account Support
Handles YouTube uploads via Google API with OAuth authentication
"""
import os
import json
from pathlib import Path
from typing import Callable, Tuple, Optional, List
from datetime import datetime
import pickle

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from logger_config import get_logger
from config import get_config
from account_manager import get_account_manager, Account
from exceptions import (
    UploadError,
    NetworkError,
    AccountNotLinkedError,
    AuthenticationError
)

logger = get_logger(__name__)
config = get_config()
account_manager = get_account_manager()

class YouTubeUploader:
    """Handle YouTube video uploads"""
    
    SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
    
    def __init__(self, account_id: str):
        """
        Initialize uploader for specific YouTube account
        
        Args:
            account_id: ID of the YouTube account to use
        """
        self.account_id = account_id
        self.account = account_manager.get_account(account_id)
        
        if not self.account:
            raise AccountNotLinkedError(f"Account {account_id} not found")
        
        if self.account.platform != "youtube":
            raise ValueError(f"Account {account_id} is not a YouTube account")
        
        self.credentials_file = config.accounts_dir / "youtube" / f"{account_id}_credentials.pickle"
        self.youtube_service = self._get_youtube_service()
    
    def _get_youtube_service(self):
        """Get authenticated YouTube service"""
        creds = None
        
        # Load saved credentials
        if self.credentials_file.exists():
            try:
                with open(self.credentials_file, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                logger.warning(f"Could not load credentials: {e}")
        
        # Refresh or re-authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logger.info("YouTube credentials refreshed")
                except Exception as e:
                    logger.error(f"Failed to refresh credentials: {e}")
                    raise AuthenticationError("YouTube credentials expired. Please re-link account.")
            else:
                raise AccountNotLinkedError("YouTube account not authenticated. Please link account first.")
            
            # Save refreshed credentials
            self._save_credentials(creds)
        
        return build('youtube', 'v3', credentials=creds)
    
    def _save_credentials(self, creds):
        """Save credentials to file"""
        self.credentials_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.credentials_file, 'wb') as token:
            pickle.dump(creds, token)
    
    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: List[str],
        status_callback: Callable[[str], None],
        scheduled_time: Optional[int] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """Upload video to YouTube with optional scheduling"""
        try:
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags,
                    'categoryId': '22'  # People & Blogs
                },
                'status': {
                    'privacyStatus': 'private',
                }
            }
            
            if scheduled_time:
                publish_at = datetime.fromtimestamp(scheduled_time).isoformat() + 'Z'
                body['status']['publishAt'] = publish_at
            
            media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
            
            request = self.youtube_service.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    status_callback(f"Uploading: {progress}%")
            
            video_id = response.get('id')
            msg = f"Video uploaded successfully. ID: {video_id}"
            if scheduled_time:
                msg += f" (Scheduled for {datetime.fromtimestamp(scheduled_time)})"
            return True, msg, video_id
        
        except HttpError as e:
            error_details = json.loads(e.content.decode())
            raise UploadError(f"YouTube API error: {error_details.get('error', {}).get('message')}")
        except Exception as e:
            raise UploadError(f"Upload failed: {str(e)}")
    
    @classmethod
    def authenticate_new_account(cls, account_name: str) -> Optional[str]:
        """Authenticate a new YouTube account and add to manager"""
        client_secrets_file = Path(config.base_dir) / "client_secret.json"
        
        if not client_secrets_file.exists():
            raise AuthenticationError("client_secret.json not found for YouTube OAuth.")
        
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(client_secrets_file),
                cls.SCOPES
            )
            creds = flow.run_local_server(port=0)
            
            youtube = build('youtube', 'v3', credentials=creds)
            response = youtube.channels().list(
                part='snippet',
                mine=True
            ).execute()
            
            if not response.get('items'):
                raise AuthenticationError("No YouTube channel found.")
            
            channel = response['items'][0]
            channel_id = channel['id']
            channel_title = channel['snippet']['title']
            
            account = Account(
                account_id="",
                platform="youtube",
                name=account_name or channel_title,
                username=channel_title,
                channel_id=channel_id,
                access_token="",  # Not used for YouTube
                is_active=True
            )
            
            account_id = account_manager.add_account(account)
            
            credentials_file = config.accounts_dir / "youtube" / f"{account_id}_credentials.pickle"
            with open(credentials_file, 'wb') as token:
                pickle.dump(creds, token)
            
            logger.info(f"YouTube account linked: {channel_title} ({account_id})")
            return account_id
        
        except Exception as e:
            raise AuthenticationError(f"YouTube authentication failed: {e}")

# Helper function
def create_youtube_uploader(account_id: str) -> YouTubeUploader:
    """Create YouTube uploader for account"""
    return YouTubeUploader(account_id)