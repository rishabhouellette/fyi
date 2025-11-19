"""
Configuration management for FYI Uploader
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import os
from dotenv import load_dotenv
import sys

@dataclass
class Config:
    """Application configuration"""
    # Facebook App Credentials
    fb_app_id: str
    fb_app_secret: str
    ngrok_url: str
    
    # Server settings
    server_host: str = "127.0.0.1"
    server_port: int = 5000
    
    # Paths
    base_dir: Path = field(default_factory=lambda: Path(__file__).parent)
    accounts_dir: Path = None
    logs_dir: Path = None
    data_dir: Path = None
    
    # Upload settings
    max_retries: int = 3
    chunk_size_mb: int = 4
    request_timeout: int = 30
    
    # Security
    allowed_ips: list = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize derived paths"""
        if self.accounts_dir is None:
            self.accounts_dir = self.base_dir / "accounts"
        if self.logs_dir is None:
            self.logs_dir = self.base_dir / "logs"
        if self.data_dir is None:
            self.data_dir = self.base_dir / "data"
    
    @property
    def redirect_uri(self) -> str:
        """Generate OAuth redirect URI"""
        return f"{self.ngrok_url}/callback"
    
    @classmethod
    def from_env(cls, env_path: Optional[Path] = None) -> 'Config':
        """Load configuration from environment"""
        # Load .env file
        if env_path and env_path.exists():
            load_dotenv(env_path)
        else:
            # Try default locations
            for env_file in [Path('.env'), Path(__file__).parent / '.env']:
                if env_file.exists():
                    load_dotenv(env_file)
                    break
        
        # Validate required variables
        required = {
            'FB_APP_ID': os.getenv('FB_APP_ID'),
            'FB_APP_SECRET': os.getenv('FB_APP_SECRET'),
            'NGROK_URL': os.getenv('NGROK_URL'),
        }
        
        missing = [k for k, v in required.items() if not v]
        if missing:
            error_msg = f"Missing required environment variables: {', '.join(missing)}"
            print(error_msg)
            sys.exit(1)
        
        # Parse allowed IPs
        allowed_ips = []
        if os.getenv('ALLOWED_IPS'):
            allowed_ips = [ip.strip() for ip in os.getenv('ALLOWED_IPS').split(',') if ip.strip()]
        
        return cls(
            fb_app_id=required['FB_APP_ID'].strip(),
            fb_app_secret=required['FB_APP_SECRET'].strip(),
            ngrok_url=required['NGROK_URL'].strip().rstrip('/'),
            server_host=os.getenv('SERVER_HOST', '127.0.0.1'),
            server_port=int(os.getenv('SERVER_PORT', '5000')),
            max_retries=int(os.getenv('MAX_RETRIES', '3')),
            chunk_size_mb=int(os.getenv('CHUNK_SIZE_MB', '4')),
            request_timeout=int(os.getenv('REQUEST_TIMEOUT', '30')),
            allowed_ips=allowed_ips,
        )
    
    def ensure_directories(self):
        """Create necessary directories"""
        self.accounts_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        
        # Create platform subdirectories
        for platform in ['facebook', 'instagram', 'youtube']:
            (self.accounts_dir / platform).mkdir(exist_ok=True)
    
    def validate(self) -> bool:
        """Validate configuration"""
        errors = []
        
        # Check ngrok URL format
        if not self.ngrok_url.startswith('https://'):
            errors.append("NGROK_URL must start with https://")
        
        # Check if ngrok is running
        try:
            import requests
            response = requests.get(self.ngrok_url, timeout=5)
        except:
            errors.append(f"Cannot reach ngrok URL: {self.ngrok_url}. Is ngrok running?")
        
        if errors:
            print("\n⚠️  Configuration Warnings:")
            for error in errors:
                print(f"   - {error}")
            return False
        
        return True

# Global config instance
_config: Optional[Config] = None

def get_config() -> Config:
    """Get global config instance"""
    global _config
    if _config is None:
        _config = Config.from_env()
        _config.ensure_directories()
    return _config

def reload_config():
    """Reload configuration from environment"""
    global _config
    _config = Config.from_env()
    _config.ensure_directories()
    return _config