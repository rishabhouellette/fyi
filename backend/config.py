"""
FYI Social ∞ - Unified Configuration
Mode Detection + All Settings
"""

import os
from pathlib import Path
from enum import Enum
from dotenv import load_dotenv

# Load .env file
env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    load_dotenv(env_file)

class AppMode(Enum):
    """Application running mode"""
    DESKTOP = "desktop"      # Native desktop app (Tauri/PyWebView)
    WEB = "web"             # Web portal (browser)
    API = "api"             # API only mode
    HYBRID = "hybrid"       # All services running

class Config:
    """Unified configuration for all modes"""
    
    def __init__(self):
        # Detect mode
        self.mode = self._detect_mode()
        
        # Project paths
        self.PROJECT_DIR = Path(__file__).parent.parent
        self.DATA_DIR = self.PROJECT_DIR / "data"
        self.ACCOUNTS_DIR = self.PROJECT_DIR / "accounts"
        self.UPLOADS_DIR = self.DATA_DIR / "uploads"
        self.LOGS_DIR = self.PROJECT_DIR / "logs"
        
        # Database
        self.DB_PATH = self.DATA_DIR / "fyi_social_media.db"
        self.USE_SUPABASE = os.getenv("FYI_USE_SUPABASE", "false").lower() == "true"
        self.SUPABASE_URL = os.getenv("SUPABASE_URL", "")
        self.SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
        
        # Server configuration
        self.WEB_PORT = int(os.getenv("FYI_WEB_PORT", "8080"))
        self.DESKTOP_PORT = int(os.getenv("FYI_DESKTOP_PORT", "8081"))
        self.API_PORT = int(os.getenv("FYI_API_PORT", "5000"))
        
        # OAuth settings
        self.OAUTH_REDIRECT_URI = os.getenv("FYI_OAUTH_REDIRECT", "https://127.0.0.1:5000/oauth/callback")
        self.PROTOCOL_HANDLER = "fyi://"  # Custom protocol for OAuth (THE NGROK KILLER)
        
        # Encryption
        self.ENCRYPTION_KEY = os.getenv("FYI_ENCRYPTION_KEY", None)
        self.USE_HARDWARE_KEY = os.getenv("FYI_USE_HARDWARE_KEY", "false").lower() == "true"
        
        # AI Models (BYOK - Bring Your Own Key)
        self.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        self.ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
        self.GROK_API_KEY = os.getenv("GROK_API_KEY", "")
        
        # Platform API Keys - Load from .env (FB_APP_ID/FB_APP_SECRET)
        self.FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID") or os.getenv("FB_APP_ID", "")
        self.FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET") or os.getenv("FB_APP_SECRET", "")
        self.GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
        self.GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
        
        # Features
        self.ENABLE_AI = os.getenv("FYI_ENABLE_AI", "true").lower() == "true"
        self.ENABLE_ANALYTICS = os.getenv("FYI_ENABLE_ANALYTICS", "true").lower() == "true"
        self.ENABLE_SCHEDULING = os.getenv("FYI_ENABLE_SCHEDULING", "true").lower() == "true"
        
        # Ensure directories exist
        self._create_directories()
    
    def _detect_mode(self) -> AppMode:
        """Detect which mode the app is running in"""
        mode_env = os.getenv("FYI_MODE", "").lower()
        
        if mode_env == "desktop":
            return AppMode.DESKTOP
        elif mode_env == "web":
            return AppMode.WEB
        elif mode_env == "api":
            return AppMode.API
        elif mode_env == "hybrid":
            return AppMode.HYBRID
        
        # Auto-detect based on environment
        if os.getenv("NICEGUI_NO_BROWSER") == "1":
            return AppMode.DESKTOP
        elif os.getenv("FYI_API_ONLY") == "1":
            return AppMode.API
        
        return AppMode.WEB  # Default
    
    def _create_directories(self):
        """Ensure all required directories exist"""
        for dir_path in [
            self.DATA_DIR,
            self.ACCOUNTS_DIR,
            self.UPLOADS_DIR,
            self.LOGS_DIR
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def get_port(self) -> int:
        """Get the appropriate port for current mode"""
        if self.mode == AppMode.DESKTOP:
            return self.DESKTOP_PORT
        elif self.mode == AppMode.API:
            return self.API_PORT
        return self.WEB_PORT
    
    def is_desktop_mode(self) -> bool:
        """Check if running in desktop mode"""
        return self.mode == AppMode.DESKTOP
    
    def is_web_mode(self) -> bool:
        """Check if running in web mode"""
        return self.mode == AppMode.WEB
    
    def is_api_mode(self) -> bool:
        """Check if running in API mode"""
        return self.mode == AppMode.API


# Global config instance
_config = None

def get_config() -> Config:
    """Get global config instance"""
    global _config
    if _config is None:
        _config = Config()
    return _config
