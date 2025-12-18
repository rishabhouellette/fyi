"""
FYI Social ∞ - OAuth Registry
Platform-specific OAuth flows for Facebook, Instagram, YouTube, etc.
"""

import requests
from typing import Dict, Tuple
from datetime import datetime, timedelta

from backend.config import get_config
from backend.database import get_database
from backend.services.local_oauth import get_oauth_server

config = get_config()
db = get_database()
oauth_server = get_oauth_server()


class OAuthRegistry:
    """Registry of OAuth flows for different platforms"""
    
    def __init__(self):
        self.platforms = {
            'facebook': FacebookOAuth(),
            'instagram': InstagramOAuth(),
            'youtube': YouTubeOAuth(),
        }
    
    def get_platform_oauth(self, platform: str):
        """Get OAuth handler for a platform"""
        return self.platforms.get(platform.lower())
    
    def initiate_oauth(self, platform: str, account_name: str = None) -> str:
        """Start OAuth flow for a platform"""
        oauth_handler = self.get_platform_oauth(platform)
        if not oauth_handler:
            raise ValueError(f"Platform {platform} not supported")
        
        # Register callback
        oauth_server.register_callback(platform, oauth_handler.handle_callback)
        
        # Start OAuth server if not running
        oauth_server.start()
        
        # Get authorization URL
        auth_url = oauth_handler.get_authorization_url()
        
        # Open in browser
        oauth_server.open_authorization_url(auth_url)
        
        return auth_url


class FacebookOAuth:
    """Facebook OAuth handler"""
    
    API_VERSION = "v20.0"
    AUTH_URL = "https://www.facebook.com/v20.0/dialog/oauth"
    TOKEN_URL = f"https://graph.facebook.com/{API_VERSION}/oauth/access_token"
    
    SCOPES = [
        'pages_show_list',
        'pages_read_engagement',
        'pages_manage_posts',
        'pages_manage_metadata',
        'instagram_basic',
        'instagram_content_publish',
        'instagram_business_content_publish',
    ]
    
    def get_authorization_url(self) -> str:
        """Get Facebook authorization URL"""
        params = {
            'client_id': config.FACEBOOK_APP_ID,
            'scope': ','.join(self.SCOPES),
            'response_type': 'code',
        }
        
        return oauth_server.get_authorization_url('facebook', self.AUTH_URL, params)
    
    def handle_callback(self, code: str, params: dict) -> dict:
        """Handle OAuth callback and exchange code for token"""
        # Exchange code for access token
        token_response = requests.get(self.TOKEN_URL, params={
            'client_id': config.FACEBOOK_APP_ID,
            'client_secret': config.FACEBOOK_APP_SECRET,
            'code': code,
            'redirect_uri': oauth_server.redirect_uri
        })
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        if not access_token:
            raise ValueError("Failed to get access token")
        
        # Get user info
        me_response = requests.get(
            f'https://graph.facebook.com/{self.API_VERSION}/me',
            params={'access_token': access_token, 'fields': 'id,name'}
        )
        user_data = me_response.json()
        
        # Get pages
        pages_response = requests.get(
            f'https://graph.facebook.com/{self.API_VERSION}/me/accounts',
            params={'access_token': access_token}
        )
        pages_data = pages_response.json()
        
        # Store accounts in database
        for page in pages_data.get('data', []):
            account_id = f"fb_{page['id']}"
            
            db.create_account({
                'account_id': account_id,
                'platform': 'facebook',
                'name': page['name'],
                'username': page.get('username', ''),
                'access_token': page['access_token'],
                'token_expires_at': int((datetime.now() + timedelta(days=60)).timestamp()),
                'metadata': {
                    'page_id': page['id'],
                    'category': page.get('category', ''),
                }
            })
        
        return {'status': 'success', 'pages_count': len(pages_data.get('data', []))}


class InstagramOAuth:
    """Instagram OAuth handler (via Facebook)"""
    
    def get_authorization_url(self) -> str:
        """Instagram uses Facebook OAuth"""
        return FacebookOAuth().get_authorization_url()
    
    def handle_callback(self, code: str, params: dict) -> dict:
        """Handle Instagram OAuth callback"""
        # Instagram uses Facebook pages, so use Facebook handler
        fb_oauth = FacebookOAuth()
        fb_result = fb_oauth.handle_callback(code, params)
        
        # Get Instagram business accounts linked to pages
        # This is handled in the Facebook callback
        
        return fb_result


class YouTubeOAuth:
    """YouTube OAuth handler"""
    
    AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    TOKEN_URL = "https://oauth2.googleapis.com/token"
    
    SCOPES = [
        'https://www.googleapis.com/auth/youtube.upload',
        'https://www.googleapis.com/auth/youtube.readonly',
    ]
    
    def get_authorization_url(self) -> str:
        """Get YouTube authorization URL"""
        params = {
            'client_id': config.GOOGLE_CLIENT_ID,
            'scope': ' '.join(self.SCOPES),
            'response_type': 'code',
            'access_type': 'offline',  # Get refresh token
            'prompt': 'consent',
        }
        
        return oauth_server.get_authorization_url('youtube', self.AUTH_URL, params)
    
    def handle_callback(self, code: str, params: dict) -> dict:
        """Handle YouTube OAuth callback"""
        # Exchange code for tokens
        token_response = requests.post(self.TOKEN_URL, data={
            'client_id': config.GOOGLE_CLIENT_ID,
            'client_secret': config.GOOGLE_CLIENT_SECRET,
            'code': code,
            'redirect_uri': oauth_server.redirect_uri,
            'grant_type': 'authorization_code'
        })
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        
        if not access_token:
            raise ValueError("Failed to get access token")
        
        # Get channel info
        channel_response = requests.get(
            'https://www.googleapis.com/youtube/v3/channels',
            params={
                'part': 'snippet',
                'mine': 'true'
            },
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        channel_data = channel_response.json()
        
        if channel_data.get('items'):
            channel = channel_data['items'][0]
            account_id = f"yt_{channel['id']}"
            
            db.create_account({
                'account_id': account_id,
                'platform': 'youtube',
                'name': channel['snippet']['title'],
                'username': channel['snippet'].get('customUrl', ''),
                'access_token': access_token,
                'refresh_token': refresh_token,
                'token_expires_at': int((datetime.now() + timedelta(seconds=token_data.get('expires_in', 3600))).timestamp()),
                'metadata': {
                    'channel_id': channel['id'],
                }
            })
        
        return {'status': 'success'}


# Global OAuth registry
_oauth_registry = None

def get_oauth_registry() -> OAuthRegistry:
    """Get global OAuth registry instance"""
    global _oauth_registry
    if _oauth_registry is None:
        _oauth_registry = OAuthRegistry()
    return _oauth_registry
