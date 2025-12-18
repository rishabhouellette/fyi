"""
Enhanced Database Manager for FYI Social Media Management Platform
Handles all 15 features: scheduling, analytics, team, inbox, library, listening, etc.
"""
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from logger_config import get_logger

logger = get_logger(__name__)

DB_PATH = Path(__file__).parent / "data" / "fyi_social_media.db"

@dataclass
class Post:
    """Represents a scheduled or published post"""
    id: Optional[int] = None
    team_id: int = None
    account_id: int = None
    platform: str = None
    title: str = None
    content: str = None
    media_paths: List[str] = None
    scheduled_time: str = None
    published_time: str = None
    status: str = "draft"  # draft, scheduled, published, failed, archived
    approval_status: str = "pending"  # pending, approved, rejected
    internal_notes: str = None
    created_by_user_id: int = None
    created_at: str = None
    updated_at: str = None

@dataclass
class Account:
    """Represents a linked social media account"""
    id: Optional[int] = None
    team_id: int = None
    platform: str = None
    account_name: str = None
    account_id: str = None
    page_id: str = None
    access_token: str = None
    is_active: bool = True

@dataclass
class AnalyticsMetric:
    """Represents analytics data for a post or account"""
    id: Optional[int] = None
    team_id: int = None
    account_id: int = None
    post_id: Optional[int] = None
    platform: str = None
    metric_date: str = None
    reach: int = 0
    impressions: int = 0
    engagement: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    followers: int = 0

class DatabaseManager:
    """Manages all database operations for the FYI platform"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database with schema if not exists"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            schema_path = Path(__file__).parent / "database_schema.sql"
            if not schema_path.exists():
                logger.warning("Database schema file not found; skipping initialization")
                return

            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='users'"
            )
            schema_already_applied = cursor.fetchone() is not None

            if schema_already_applied:
                logger.debug("Database schema already present; skipping initialization")
                return

            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = f.read()
                cursor.executescript(schema)
                logger.info("Database schema initialized")

            conn.commit()
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
        finally:
            if conn:
                conn.close()
    
    def get_connection(self):
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # ==================== POSTS ====================
    
    def create_post(self, post: Post) -> int:
        """Create a new post"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO posts (
                    team_id, account_id, platform, title, content, media_paths,
                    scheduled_time, status, created_by_user_id, internal_notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                post.team_id, post.account_id, post.platform, post.title,
                post.content, json.dumps(post.media_paths or []),
                post.scheduled_time, post.status, post.created_by_user_id,
                post.internal_notes
            ))
            post_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Post created: {post_id}")
            return post_id
        except Exception as e:
            logger.error(f"Failed to create post: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()

    def get_post(self, post_id: int) -> Optional[Post]:
        """Fetch a single post by ID."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
            row = cursor.fetchone()
            return self._row_to_post(row) if row else None
        except Exception as e:
            logger.error(f"Failed to fetch post %s: %s", post_id, e)
            return None
        finally:
            conn.close()

    def schedule_post(self, post_id: int, scheduled_time: str, status: str = "scheduled") -> bool:
        """Update a post's schedule time and status."""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE posts
                SET scheduled_time = ?, status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (scheduled_time, status, post_id),
            )
            if cursor.rowcount == 0:
                return False
            conn.commit()
            logger.info("Post %s scheduled for %s", post_id, scheduled_time)
            return True
        except Exception as e:
            logger.error("Failed to schedule post %s: %s", post_id, e)
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def get_posts(self, team_id: int, filters: Dict[str, Any] = None) -> List[Post]:
        """Get posts for a team with optional filters"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM posts WHERE team_id = ?"
        params = [team_id]
        
        if filters:
            if filters.get('status'):
                query += " AND status = ?"
                params.append(filters['status'])
            if filters.get('platform'):
                query += " AND platform = ?"
                params.append(filters['platform'])
            if filters.get('account_id'):
                query += " AND account_id = ?"
                params.append(filters['account_id'])
        
        query += " ORDER BY scheduled_time DESC"
        
        try:
            cursor.execute(query, params)
            posts = [self._row_to_post(row) for row in cursor.fetchall()]
            return posts
        except Exception as e:
            logger.error(f"Failed to get posts: {e}")
            return []
        finally:
            conn.close()
    
    def update_post_status(self, post_id: int, status: str, platform_post_id: str = None):
        """Update post status and platform ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE posts SET status = ?, platform_post_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, platform_post_id, post_id))
            conn.commit()
            logger.info(f"Post {post_id} status updated to {status}")
        except Exception as e:
            logger.error(f"Failed to update post status: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def approve_post(self, post_id: int, approved_by_user_id: int, approved: bool):
        """Approve or reject a post"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            status = "approved" if approved else "rejected"
            cursor.execute("""
                UPDATE posts SET approval_status = ?, approval_by_user_id = ?, approval_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, approved_by_user_id, post_id))
            conn.commit()
            logger.info(f"Post {post_id} {status}")
        except Exception as e:
            logger.error(f"Failed to approve post: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    # ==================== ACCOUNTS ====================
    
    def add_account(self, account: Account) -> int:
        """Add a new linked social media account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO accounts (
                    team_id, platform, account_name, account_id, page_id, access_token
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                account.team_id, account.platform, account.account_name,
                account.account_id, account.page_id, account.access_token
            ))
            account_id = cursor.lastrowid
            conn.commit()
            logger.info(f"Account added: {account_id}")
            return account_id
        except Exception as e:
            logger.error(f"Failed to add account: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def get_accounts(self, team_id: int, platform: str = None) -> List[Account]:
        """Get accounts for a team"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM accounts WHERE team_id = ? AND is_active = 1"
        params = [team_id]
        
        if platform:
            query += " AND platform = ?"
            params.append(platform)
        
        try:
            cursor.execute(query, params)
            accounts = [self._row_to_account(row) for row in cursor.fetchall()]
            return accounts
        except Exception as e:
            logger.error(f"Failed to get accounts: {e}")
            return []
        finally:
            conn.close()
    
    # ==================== ANALYTICS ====================
    
    def record_analytics(self, metric: AnalyticsMetric):
        """Record analytics metrics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO analytics (
                    team_id, account_id, post_id, platform, metric_date,
                    reach, impressions, engagement, likes, comments, shares, followers
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metric.team_id, metric.account_id, metric.post_id, metric.platform,
                metric.metric_date or datetime.now().date().isoformat(),
                metric.reach, metric.impressions, metric.engagement,
                metric.likes, metric.comments, metric.shares, metric.followers
            ))
            conn.commit()
            logger.debug(f"Analytics recorded for account {metric.account_id}")
        except Exception as e:
            logger.error(f"Failed to record analytics: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_analytics(self, team_id: int, days: int = 30, account_id: int = None) -> List[AnalyticsMetric]:
        """Get analytics metrics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        start_date = (datetime.now() - timedelta(days=days)).date().isoformat()
        
        query = "SELECT * FROM analytics WHERE team_id = ? AND metric_date >= ?"
        params = [team_id, start_date]
        
        if account_id:
            query += " AND account_id = ?"
            params.append(account_id)
        
        query += " ORDER BY metric_date DESC"
        
        try:
            cursor.execute(query, params)
            metrics = [self._row_to_analytics(row) for row in cursor.fetchall()]
            return metrics
        except Exception as e:
            logger.error(f"Failed to get analytics: {e}")
            return []
        finally:
            conn.close()

    def get_post_analytics(self, post_id: int, days: int = 30) -> List[AnalyticsMetric]:
        """Get analytics metrics for a specific post."""
        conn = self.get_connection()
        cursor = conn.cursor()

        cutoff = (datetime.now() - timedelta(days=days)).date().isoformat()

        try:
            cursor.execute(
                """
                SELECT * FROM analytics
                WHERE post_id = ? AND metric_date >= ?
                ORDER BY metric_date DESC
                """,
                (post_id, cutoff),
            )
            return [self._row_to_analytics(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error("Failed to get analytics for post %s: %s", post_id, e)
            return []
        finally:
            conn.close()
    
    # ==================== SOCIAL INBOX ====================
    
    def add_inbox_message(self, team_id: int, account_id: int, platform: str,
                         message_id: str, from_user_name: str, content: str,
                         message_type: str = "dm"):
        """Add a message to social inbox"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO social_inbox (
                    team_id, account_id, platform, message_id, from_user_name,
                    message_content, message_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (team_id, account_id, platform, message_id, from_user_name, content, message_type))
            conn.commit()
            logger.debug(f"Inbox message added: {message_id}")
        except Exception as e:
            logger.error(f"Failed to add inbox message: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_inbox_messages(self, team_id: int, unread_only: bool = False) -> List[Dict]:
        """Get messages from social inbox"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = "SELECT * FROM social_inbox WHERE team_id = ?"
        params = [team_id]
        
        if unread_only:
            query += " AND is_read = 0"
        
        query += " ORDER BY received_at DESC"
        
        try:
            cursor.execute(query, params)
            messages = [dict(row) for row in cursor.fetchall()]
            return messages
        except Exception as e:
            logger.error(f"Failed to get inbox messages: {e}")
            return []
        finally:
            conn.close()
    
    # ==================== ACTIVITY LOGGING ====================
    
    def log_activity(self, team_id: int, user_id: int, action: str,
                    resource_type: str = None, resource_id: int = None,
                    details: Dict = None):
        """Log user activity for audit trail"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO activity_log (
                    team_id, user_id, action, resource_type, resource_id, details
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (team_id, user_id, action, resource_type, resource_id, json.dumps(details or {})))
            conn.commit()
            logger.debug(f"Activity logged: {action} by user {user_id}")
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    # ==================== HELPER METHODS ====================
    
    def _row_to_post(self, row) -> Post:
        """Convert database row to Post object"""
        return Post(
            id=row['id'],
            team_id=row['team_id'],
            account_id=row['account_id'],
            platform=row['platform'],
            title=row['title'],
            content=row['content'],
            media_paths=json.loads(row['media_paths']) if row['media_paths'] else [],
            scheduled_time=row['scheduled_time'],
            published_time=row['published_time'],
            status=row['status'],
            approval_status=row['approval_status'],
            internal_notes=row['internal_notes'],
            created_by_user_id=row['created_by_user_id'],
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    def _row_to_account(self, row) -> Account:
        """Convert database row to Account object"""
        return Account(
            id=row['id'],
            team_id=row['team_id'],
            platform=row['platform'],
            account_name=row['account_name'],
            account_id=row['account_id'],
            page_id=row['page_id'],
            access_token=row['access_token'],
            is_active=row['is_active']
        )
    
    def _row_to_analytics(self, row) -> AnalyticsMetric:
        """Convert database row to AnalyticsMetric object"""
        return AnalyticsMetric(
            id=row['id'],
            team_id=row['team_id'],
            account_id=row['account_id'],
            post_id=row['post_id'],
            platform=row['platform'],
            metric_date=row['metric_date'],
            reach=row['reach'],
            impressions=row['impressions'],
            engagement=row['engagement'],
            likes=row['likes'],
            comments=row['comments'],
            shares=row['shares'],
            followers=row['followers']
        )

# Global database manager instance
_db_manager = None

def get_db_manager() -> DatabaseManager:
    """Get or create global database manager"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager()
    return _db_manager
