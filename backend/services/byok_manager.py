"""
FYI Social ∞ - BYOK Manager (Bring Your Own Key)
Securely manage user's own API keys for OpenAI, Grok, Claude, etc.
"""

from typing import Optional, Dict
from datetime import datetime
import sqlite3

from backend.database import get_database
from backend.services.encryption import get_encryption


class BYOKManager:
    """Manage user's own API keys with encryption"""
    
    SUPPORTED_SERVICES = {
        'openai': 'OpenAI',
        'anthropic': 'Anthropic (Claude)',
        'grok': 'Grok (xAI)',
        'gemini': 'Google Gemini',
        'mistral': 'Mistral AI'
    }
    
    def __init__(self):
        self.db = get_database()
        self.encryption = get_encryption()
        self._ensure_api_keys_schema()

    def _ensure_api_keys_schema(self):
        """Ensure the api_keys table has the columns required by BYOK."""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()

            # If the table does not exist yet, the Database initializer will have created it.
            try:
                cursor.execute("PRAGMA table_info(api_keys)")
                columns = {row[1] for row in cursor.fetchall()}  # row[1] == column name
            except sqlite3.OperationalError:
                columns = set()

            required = {"service", "encrypted_key", "created_at", "updated_at"}
            if required.issubset(columns):
                return  # Schema already good

            if not columns:
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS api_keys (
                        service TEXT PRIMARY KEY,
                        encrypted_key TEXT NOT NULL,
                        created_at INTEGER NOT NULL,
                        updated_at INTEGER NOT NULL
                    )
                ''')
                conn.commit()
                return

            print("⚙️ Updating api_keys table schema for BYOK manager...")
            cursor.execute("ALTER TABLE api_keys RENAME TO api_keys_legacy")
            cursor.execute('''
                CREATE TABLE api_keys (
                    service TEXT PRIMARY KEY,
                    encrypted_key TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                )
            ''')

            if {"service", "encrypted_key"}.issubset(columns):
                cursor.execute('''
                    INSERT OR IGNORE INTO api_keys (service, encrypted_key, created_at, updated_at)
                    SELECT service,
                           encrypted_key,
                           COALESCE(created_at, strftime('%s','now')),
                           COALESCE(updated_at, strftime('%s','now'))
                    FROM api_keys_legacy
                    WHERE service IS NOT NULL
                ''')

            cursor.execute("DROP TABLE IF EXISTS api_keys_legacy")
            conn.commit()
    
    def set_api_key(self, service: str, api_key: str):
        """Store an API key securely"""
        if service not in self.SUPPORTED_SERVICES:
            raise ValueError(f"Unsupported service: {service}")
        
        # Encrypt the key
        encrypted_key = self.encryption.encrypt(api_key)
        
        # Store in database
        now = int(datetime.now().timestamp())
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO api_keys (service, encrypted_key, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (service, encrypted_key, now, now))
            conn.commit()
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Retrieve and decrypt an API key"""
        if service not in self.SUPPORTED_SERVICES:
            return None
        
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT encrypted_key FROM api_keys WHERE service = ?', (service,))
            row = cursor.fetchone()
            
            if row:
                try:
                    return self.encryption.decrypt(row['encrypted_key'])
                except:
                    return None
            return None
    
    def delete_api_key(self, service: str):
        """Delete an API key"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM api_keys WHERE service = ?', (service,))
            conn.commit()
    
    def list_configured_services(self) -> Dict[str, str]:
        """List all services with API keys configured"""
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT service, created_at FROM api_keys')
            rows = cursor.fetchall()
            
            return {
                row['service']: self.SUPPORTED_SERVICES[row['service']]
                for row in rows
                if row['service'] in self.SUPPORTED_SERVICES
            }
    
    def has_api_key(self, service: str) -> bool:
        """Check if an API key is configured for a service"""
        return self.get_api_key(service) is not None
    
    def validate_key_format(self, service: str, api_key: str) -> bool:
        """Basic validation of API key format"""
        if not api_key or len(api_key) < 10:
            return False
        
        # Service-specific validation
        if service == 'openai' and not api_key.startswith('sk-'):
            return False
        elif service == 'anthropic' and not api_key.startswith('sk-ant-'):
            return False
        
        return True


# Global BYOK manager instance
_byok_manager = None

def get_byok_manager() -> BYOKManager:
    """Get global BYOK manager instance"""
    global _byok_manager
    if _byok_manager is None:
        _byok_manager = BYOKManager()
    return _byok_manager
