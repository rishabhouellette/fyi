"""
FYI Social ∞ - Encryption Service
Secure storage for API keys and tokens
"""

import os
import base64
from pathlib import Path
from cryptography.fernet import Fernet
from typing import Optional

from backend.config import get_config

config = get_config()


class EncryptionService:
    """Handle encryption/decryption of sensitive data"""
    
    def __init__(self):
        self.key = self._get_or_create_key()
        self.cipher = Fernet(self.key)
    
    def _get_or_create_key(self) -> bytes:
        """Get encryption key from env or generate new one"""
        # Try environment variable first
        if config.ENCRYPTION_KEY:
            return base64.urlsafe_b64encode(config.ENCRYPTION_KEY.encode().ljust(32)[:32])
        
        # Try loading from file
        key_file = config.DATA_DIR / ".encryption_key"
        
        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        
        # Generate new key
        key = Fernet.generate_key()
        
        # Save for future use
        key_file.parent.mkdir(parents=True, exist_ok=True)
        with open(key_file, 'wb') as f:
            f.write(key)
        
        # Set restrictive permissions (Unix-like systems)
        try:
            os.chmod(key_file, 0o600)
        except:
            pass
        
        return key
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string"""
        if not plaintext:
            return ""
        
        encrypted_bytes = self.cipher.encrypt(plaintext.encode())
        return base64.urlsafe_b64encode(encrypted_bytes).decode()
    
    def decrypt(self, encrypted: str) -> str:
        """Decrypt a string"""
        if not encrypted:
            return ""
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted.encode())
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")
    
    def encrypt_dict(self, data: dict) -> dict:
        """Encrypt all string values in a dictionary"""
        encrypted = {}
        for key, value in data.items():
            if isinstance(value, str):
                encrypted[key] = self.encrypt(value)
            else:
                encrypted[key] = value
        return encrypted
    
    def decrypt_dict(self, encrypted_data: dict) -> dict:
        """Decrypt all encrypted values in a dictionary"""
        decrypted = {}
        for key, value in encrypted_data.items():
            if isinstance(value, str):
                try:
                    decrypted[key] = self.decrypt(value)
                except:
                    decrypted[key] = value
            else:
                decrypted[key] = value
        return decrypted


# Global encryption instance
_encryption = None

def get_encryption() -> EncryptionService:
    """Get global encryption instance"""
    global _encryption
    if _encryption is None:
        _encryption = EncryptionService()
    return _encryption
