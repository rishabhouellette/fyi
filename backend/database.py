"""
FYI Social ∞ - Database Layer
SQLite for local storage + Optional Supabase sync
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
from contextlib import contextmanager

from backend.config import get_config

config = get_config()


class Database:
    """Unified database layer with SQLite + optional Supabase sync"""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or config.DB_PATH
        self.supabase_client = None
        
        # Initialize database
        self._init_db()
        
        # Initialize Supabase if enabled
        if config.USE_SUPABASE:
            self._init_supabase()
    
    def _init_db(self):
        """Initialize SQLite database with schema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Accounts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS accounts (
                    account_id TEXT PRIMARY KEY,
                    platform TEXT NOT NULL,
                    name TEXT NOT NULL,
                    username TEXT,
                    access_token TEXT,
                    refresh_token TEXT,
                    token_expires_at INTEGER,
                    metadata TEXT,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                )
            ''')
            
            # Posts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS posts (
                    post_id TEXT PRIMARY KEY,
                    account_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    title TEXT,
                    description TEXT,
                    file_path TEXT,
                    thumbnail_path TEXT,
                    status TEXT DEFAULT 'draft',
                    scheduled_time INTEGER,
                    published_time INTEGER,
                    platform_post_id TEXT,
                    metadata TEXT,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL,
                    FOREIGN KEY (account_id) REFERENCES accounts(account_id)
                )
            ''')
            
            # Analytics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analytics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_id TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    views INTEGER DEFAULT 0,
                    likes INTEGER DEFAULT 0,
                    comments INTEGER DEFAULT 0,
                    shares INTEGER DEFAULT 0,
                    engagement_rate REAL DEFAULT 0.0,
                    synced_at INTEGER NOT NULL,
                    FOREIGN KEY (post_id) REFERENCES posts(post_id)
                )
            ''')
            
            # User settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at INTEGER NOT NULL
                )
            ''')
            
            # API keys table (encrypted)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_keys (
                    service TEXT PRIMARY KEY,
                    encrypted_key TEXT NOT NULL,
                    created_at INTEGER NOT NULL,
                    updated_at INTEGER NOT NULL
                )
            ''')
            
            conn.commit()
    
    def _init_supabase(self):
        """Initialize Supabase client for cloud sync"""
        try:
            from supabase import create_client
            self.supabase_client = create_client(
                config.SUPABASE_URL,
                config.SUPABASE_KEY
            )
        except ImportError:
            print("Warning: supabase-py not installed. Cloud sync disabled.")
            config.USE_SUPABASE = False
    
    @contextmanager
    def get_connection(self):
        """Get database connection context manager"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    # ========================================================================
    # ACCOUNTS
    # ========================================================================
    
    def create_account(self, account_data: Dict[str, Any]) -> str:
        """Create a new account"""
        now = int(datetime.now().timestamp())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO accounts (
                    account_id, platform, name, username, access_token,
                    refresh_token, token_expires_at, metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                account_data['account_id'],
                account_data['platform'],
                account_data['name'],
                account_data.get('username'),
                account_data.get('access_token'),
                account_data.get('refresh_token'),
                account_data.get('token_expires_at'),
                json.dumps(account_data.get('metadata', {})),
                now,
                now
            ))
            conn.commit()
        
        if self.supabase_client:
            self._sync_to_supabase('accounts', account_data)
        
        return account_data['account_id']
    
    def get_account(self, account_id: str) -> Optional[Dict[str, Any]]:
        """Get account by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM accounts WHERE account_id = ?', (account_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def list_accounts(self, platform: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all accounts, optionally filtered by platform"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if platform:
                cursor.execute('SELECT * FROM accounts WHERE platform = ?', (platform,))
            else:
                cursor.execute('SELECT * FROM accounts')
            
            return [dict(row) for row in cursor.fetchall()]
    
    def update_account(self, account_id: str, updates: Dict[str, Any]):
        """Update account data"""
        now = int(datetime.now().timestamp())
        updates['updated_at'] = now
        
        set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [account_id]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'UPDATE accounts SET {set_clause} WHERE account_id = ?', values)
            conn.commit()
        
        if self.supabase_client:
            self._sync_to_supabase('accounts', {'account_id': account_id, **updates})
    
    def delete_account(self, account_id: str):
        """Delete an account"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM accounts WHERE account_id = ?', (account_id,))
            conn.commit()
    
    # ========================================================================
    # POSTS
    # ========================================================================
    
    def create_post(self, post_data: Dict[str, Any]) -> str:
        """Create a new post"""
        now = int(datetime.now().timestamp())
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO posts (
                    post_id, account_id, platform, title, description,
                    file_path, thumbnail_path, status, scheduled_time,
                    metadata, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                post_data['post_id'],
                post_data['account_id'],
                post_data['platform'],
                post_data.get('title'),
                post_data.get('description'),
                post_data.get('file_path'),
                post_data.get('thumbnail_path'),
                post_data.get('status', 'draft'),
                post_data.get('scheduled_time'),
                json.dumps(post_data.get('metadata', {})),
                now,
                now
            ))
            conn.commit()
        
        return post_data['post_id']
    
    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        """Get post by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM posts WHERE post_id = ?', (post_id,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None
    
    def list_posts(self, account_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List posts with optional filters"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = 'SELECT * FROM posts WHERE 1=1'
            params = []
            
            if account_id:
                query += ' AND account_id = ?'
                params.append(account_id)
            
            if status:
                query += ' AND status = ?'
                params.append(status)
            
            query += ' ORDER BY created_at DESC'
            
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    # ========================================================================
    # SETTINGS
    # ========================================================================
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
            row = cursor.fetchone()
            
            if row:
                try:
                    return json.loads(row['value'])
                except:
                    return row['value']
            return default
    
    def set_setting(self, key: str, value: Any):
        """Set a setting value"""
        now = int(datetime.now().timestamp())
        value_str = json.dumps(value) if not isinstance(value, str) else value
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO settings (key, value, updated_at)
                VALUES (?, ?, ?)
            ''', (key, value_str, now))
            conn.commit()
    
    # ========================================================================
    # SUPABASE SYNC
    # ========================================================================
    
    def _sync_to_supabase(self, table: str, data: Dict[str, Any]):
        """Sync data to Supabase"""
        if not self.supabase_client:
            return
        
        try:
            self.supabase_client.table(table).upsert(data).execute()
        except Exception as e:
            print(f"Supabase sync error: {e}")


# Global database instance
_db = None

def get_database() -> Database:
    """Get global database instance"""
    global _db
    if _db is None:
        _db = Database()
    return _db
