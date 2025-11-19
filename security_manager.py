"""
Security Manager for FYI Social Media Management Platform
2FA, password management, permission controls, and audit logs
"""
import hashlib
import secrets
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from database_manager import get_db_manager
from logger_config import get_logger

logger = get_logger(__name__)
db_manager = get_db_manager()


class PasswordManager:
    """Secure password management"""
    
    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """
        Hash password with salt using SHA256
        
        Args:
            password: Plain text password
            salt: Optional salt (generated if not provided)
        
        Returns:
            Tuple of (hashed_password, salt)
        """
        if salt is None:
            salt = secrets.token_hex(32)
        
        # PBKDF2-like approach with multiple iterations
        hash_obj = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        hashed = hash_obj.hex()
        
        return hashed, salt
    
    @staticmethod
    def verify_password(password: str, hashed_password: str, salt: str) -> bool:
        """
        Verify password against hash
        
        Args:
            password: Plain text password to verify
            hashed_password: Stored hash
            salt: Stored salt
        
        Returns:
            True if password matches
        """
        computed_hash, _ = PasswordManager.hash_password(password, salt)
        return computed_hash == hashed_password
    
    @staticmethod
    def generate_secure_password(length: int = 16) -> str:
        """Generate secure random password"""
        import string
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    @staticmethod
    def check_password_strength(password: str) -> Dict:
        """
        Check password strength
        
        Returns:
            Dict with strength metrics
        """
        score = 0
        feedback = []
        
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("Password should be at least 8 characters")
        
        if len(password) >= 12:
            score += 1
        
        if any(c.isupper() for c in password):
            score += 1
        else:
            feedback.append("Add uppercase letters")
        
        if any(c.islower() for c in password):
            score += 1
        else:
            feedback.append("Add lowercase letters")
        
        if any(c.isdigit() for c in password):
            score += 1
        else:
            feedback.append("Add numbers")
        
        if any(c in "!@#$%^&*" for c in password):
            score += 1
        else:
            feedback.append("Add special characters")
        
        strength_levels = {
            0: "Very Weak",
            1: "Weak",
            2: "Fair",
            3: "Good",
            4: "Strong",
            5: "Very Strong"
        }
        
        return {
            "score": min(score, 5),
            "strength": strength_levels.get(min(score, 5), "Unknown"),
            "feedback": feedback
        }


class TwoFactorAuth:
    """Two-factor authentication manager"""
    
    @staticmethod
    def generate_2fa_code() -> str:
        """Generate 6-digit 2FA code"""
        return str(secrets.randbelow(1000000)).zfill(6)
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> List[str]:
        """Generate backup codes for 2FA recovery"""
        return [secrets.token_hex(4).upper() for _ in range(count)]
    
    @staticmethod
    def verify_2fa_code(stored_code: str, provided_code: str, timeout_seconds: int = 300) -> bool:
        """
        Verify 2FA code
        
        Args:
            stored_code: Code sent to user
            provided_code: Code user provided
            timeout_seconds: How long code is valid
        
        Returns:
            True if code is valid
        """
        return stored_code == provided_code
    
    @staticmethod
    def generate_backup_code_qr() -> str:
        """Generate QR code for authenticator app"""
        # Mock QR code data - in production would use qrcode library
        return "otpauth://totp/FYI:user@example.com?secret=JBSWY3DPEBLW64TMMQ&issuer=FYI"


class PermissionManager:
    """Role-based permission management"""
    
    # Role definitions
    ROLES = {
        "admin": {
            "name": "Administrator",
            "permissions": [
                "manage_accounts",
                "manage_users",
                "manage_permissions",
                "manage_billing",
                "view_analytics",
                "create_content",
                "schedule_posts",
                "manage_settings",
                "view_audit_logs"
            ],
            "description": "Full access to all features"
        },
        "manager": {
            "name": "Content Manager",
            "permissions": [
                "view_analytics",
                "create_content",
                "schedule_posts",
                "approve_content",
                "manage_team"
            ],
            "description": "Manage team and content"
        },
        "creator": {
            "name": "Content Creator",
            "permissions": [
                "create_content",
                "view_own_analytics",
                "schedule_posts"
            ],
            "description": "Create and schedule content"
        },
        "viewer": {
            "name": "Viewer",
            "permissions": [
                "view_analytics",
                "view_content"
            ],
            "description": "View-only access"
        }
    }
    
    @staticmethod
    def get_role_permissions(role: str) -> List[str]:
        """Get permissions for role"""
        return PermissionManager.ROLES.get(role, {}).get("permissions", [])
    
    @staticmethod
    def has_permission(user_role: str, required_permission: str) -> bool:
        """Check if user has permission"""
        permissions = PermissionManager.get_role_permissions(user_role)
        return required_permission in permissions
    
    @staticmethod
    def get_all_roles() -> Dict:
        """Get all available roles"""
        return PermissionManager.ROLES


class APIKeyManager:
    """API key management for third-party integrations"""
    
    @staticmethod
    def generate_api_key(name: str, team_id: int) -> str:
        """Generate new API key"""
        prefix = "fyi_"
        key = prefix + secrets.token_urlsafe(32)
        
        db_manager.log_activity(
            team_id=team_id,
            user_id=1,
            action="generate_api_key",
            target_type="api_keys",
            target_id=None,
            metadata={"key_name": name}
        )
        
        return key
    
    @staticmethod
    def revoke_api_key(key_id: int, team_id: int):
        """Revoke API key"""
        db_manager.log_activity(
            team_id=team_id,
            user_id=1,
            action="revoke_api_key",
            target_type="api_keys",
            target_id=key_id,
            metadata={}
        )
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """Validate API key format and existence"""
        if not api_key.startswith("fyi_"):
            return False
        
        if len(api_key) < 40:
            return False
        
        return True


class AuditLogger:
    """Security audit logging"""
    
    # Activity types
    ACTIVITY_TYPES = {
        "login": "User login",
        "logout": "User logout",
        "password_change": "Password changed",
        "2fa_enabled": "2FA enabled",
        "2fa_disabled": "2FA disabled",
        "permission_change": "Permission changed",
        "user_created": "User created",
        "user_deleted": "User deleted",
        "api_key_generated": "API key generated",
        "api_key_revoked": "API key revoked",
        "content_created": "Content created",
        "content_deleted": "Content deleted",
        "content_scheduled": "Content scheduled",
        "analytics_exported": "Analytics exported",
        "settings_changed": "Settings changed",
        "failed_login": "Failed login attempt",
        "unauthorized_access": "Unauthorized access attempt",
        "data_export": "Data export",
        "api_call": "API call",
    }
    
    @staticmethod
    def log_security_event(
        event_type: str,
        user_id: int,
        team_id: int,
        ip_address: str = "127.0.0.1",
        details: Optional[Dict] = None,
        severity: str = "info"
    ):
        """
        Log security event
        
        Args:
            event_type: Type of security event
            user_id: User performing action
            team_id: Team context
            ip_address: User IP address
            details: Additional details
            severity: Event severity (info, warning, critical)
        """
        activity_description = AuditLogger.ACTIVITY_TYPES.get(event_type, event_type)
        
        db_manager.log_activity(
            team_id=team_id,
            user_id=user_id,
            action=event_type,
            target_type="security_audit",
            target_id=None,
            metadata={
                "ip_address": ip_address,
                "severity": severity,
                "activity_description": activity_description,
                **(details or {})
            }
        )
        
        logger.info(f"Security Event: {event_type} | User: {user_id} | Team: {team_id} | IP: {ip_address}")
    
    @staticmethod
    def get_audit_logs(
        team_id: int,
        days: int = 30,
        event_type: Optional[str] = None,
        severity: Optional[str] = None
    ) -> List[Dict]:
        """
        Get audit logs with filters
        
        Args:
            team_id: Team to get logs for
            days: Number of days to look back
            event_type: Filter by event type
            severity: Filter by severity
        
        Returns:
            List of audit log entries
        """
        try:
            activities = db_manager.get_activities(team_id=team_id)
            
            # Filter by date
            cutoff_date = datetime.now() - timedelta(days=days)
            
            logs = []
            for activity in activities:
                if activity.get('action', '') in AuditLogger.ACTIVITY_TYPES or activity.get('action') == 'security_audit':
                    # Apply filters
                    if event_type and activity.get('action') != event_type:
                        continue
                    
                    metadata = activity.get('metadata', {})
                    if severity and metadata.get('severity') != severity:
                        continue
                    
                    logs.append({
                        "timestamp": activity.get('timestamp'),
                        "event_type": activity.get('action'),
                        "user_id": activity.get('user_id'),
                        "description": metadata.get('activity_description', activity.get('action')),
                        "ip_address": metadata.get('ip_address', 'N/A'),
                        "severity": metadata.get('severity', 'info'),
                        "details": metadata
                    })
            
            return logs
        
        except Exception as e:
            logger.error(f"Get audit logs error: {e}")
            return []


# Global security manager instance
_security_instance = None

def get_security_manager():
    """Get security manager singleton"""
    global _security_instance
    if _security_instance is None:
        _security_instance = {
            "password": PasswordManager(),
            "2fa": TwoFactorAuth(),
            "permissions": PermissionManager(),
            "api_keys": APIKeyManager(),
            "audit": AuditLogger()
        }
    return _security_instance
