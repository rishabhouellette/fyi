"""
Account management system for multiple platforms and accounts
"""
import json
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import secrets
from logger_config import get_logger
from config import get_config
from exceptions import AccountNotLinkedError

logger = get_logger(__name__)
config = get_config()

@dataclass
class Account:
    """Represents a linked social media account"""
    account_id: str  # Unique ID for this account
    platform: str  # facebook, instagram, youtube
    name: str  # Display name
    username: Optional[str] = None
    page_id: Optional[str] = None  # For Facebook/Instagram
    channel_id: Optional[str] = None  # For YouTube
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[int] = None
    linked_at: int = None
    last_used: int = None
    is_active: bool = True
    
    def __post_init__(self):
        if self.linked_at is None:
            self.linked_at = int(datetime.now().timestamp())
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Account':
        """Create from dictionary"""
        return cls(**data)
    
    def update_token(self, access_token: str, refresh_token: str = None, expires_at: int = None):
        """Update account tokens"""
        self.access_token = access_token
        if refresh_token:
            self.refresh_token = refresh_token
        if expires_at:
            self.token_expires_at = expires_at
        self.last_used = int(datetime.now().timestamp())
    
    def is_token_valid(self) -> bool:
        """Check if token is still valid"""
        if not self.access_token:
            return False
        if self.token_expires_at:
            return datetime.now().timestamp() < self.token_expires_at
        return True

class AccountManager:
    """Manage multiple social media accounts"""
    
    def __init__(self):
        self.accounts_file = config.accounts_dir / "accounts.json"
        self.accounts: Dict[str, Account] = {}
        self._last_loaded_mtime: Optional[float] = None
        self.load_accounts()
    
    def load_accounts(self):
        """Load accounts from file"""
        if self.accounts_file.exists():
            try:
                with open(self.accounts_file, 'r') as f:
                    data = json.load(f)
                    self.accounts = {
                        account_id: Account.from_dict(acc_data)
                        for account_id, acc_data in data.items()
                    }
                try:
                    self._last_loaded_mtime = self.accounts_file.stat().st_mtime
                except FileNotFoundError:
                    self._last_loaded_mtime = None
                logger.info(f"Loaded {len(self.accounts)} accounts")
            except Exception as e:
                logger.error(f"Error loading accounts: {e}")
                self.accounts = {}
    
    def save_accounts(self):
        """Save accounts to file"""
        data = {account_id: acc.to_dict() for account_id, acc in self.accounts.items()}
        try:
            with open(self.accounts_file, 'w') as f:
                json.dump(data, f, indent=4)
            try:
                self._last_loaded_mtime = self.accounts_file.stat().st_mtime
            except FileNotFoundError:
                self._last_loaded_mtime = None
        except Exception as e:
            logger.error(f"Error saving accounts: {e}")
    
    def add_account(self, account: Account) -> str:
        """Add or update account
        Returns:
            Account ID
        """
        if not account.account_id:
            account.account_id = self._generate_account_id(account.platform)
        
        self.accounts[account.account_id] = account
        self.save_accounts()
        
        logger.info(f"Added account: {account.name} ({account.platform})")
        return account.account_id
    
    def remove_account(self, account_id: str):
        """Remove account"""
        if account_id in self.accounts:
            account = self.accounts[account_id]
            del self.accounts[account_id]
            self.save_accounts()
            logger.info(f"Removed account: {account.name}")
    
    def get_account(self, account_id: str) -> Optional[Account]:
        """Get account by ID"""
        self._ensure_latest_accounts()
        return self.accounts.get(account_id)
    
    def get_accounts_by_platform(self, platform: str) -> List[Account]:
        """Get all accounts for a platform"""
        self._ensure_latest_accounts()
        return [
            acc for acc in self.accounts.values()
            if acc.platform == platform and acc.is_active
        ]
    
    def get_all_accounts(self) -> List[Account]:
        """Get all active accounts"""
        return [acc for acc in self.accounts.values() if acc.is_active]
    
    def update_account(self, account_id: str, **kwargs):
        """Update account properties"""
        if account_id in self.accounts:
            account = self.accounts[account_id]
            for key, value in kwargs.items():
                if hasattr(account, key):
                    setattr(account, key, value)
            self.save_accounts()
    
    def _generate_account_id(self, platform: str) -> str:
        """Generate unique account ID"""
        timestamp = int(datetime.now().timestamp())
        random_part = secrets.token_hex(4)
        return f"{platform}_{timestamp}_{random_part}"

    def _ensure_latest_accounts(self):
        """Reload accounts if file has changed on disk"""
        try:
            mtime = self.accounts_file.stat().st_mtime
        except FileNotFoundError:
            return
        if self._last_loaded_mtime is None or mtime > self._last_loaded_mtime:
            self.load_accounts()
    
    def get_active_token(self, account_id: str) -> str:
        """
        Get active access token for account
        
        Raises:
            AccountNotLinkedError: If account not found or token invalid
        """
        account = self.get_account(account_id)
        if not account:
            raise AccountNotLinkedError(f"Account {account_id} not found")
        
        if not account.is_token_valid():
            raise AccountNotLinkedError(f"Token expired for {account.name}")
        
        account.last_used = int(datetime.now().timestamp())
        self.save_accounts()
        
        return account.access_token

# Global account manager instance
_account_manager: Optional[AccountManager] = None

def get_account_manager() -> AccountManager:
    """Get global account manager instance"""
    global _account_manager
    if _account_manager is None:
        _account_manager = AccountManager()
    return _account_manager