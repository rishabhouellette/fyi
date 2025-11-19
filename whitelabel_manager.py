"""
White-label & Branding Module for FYI Social Media Management Platform
Custom branding, agency features, and multi-tenant administration
"""
import json
from datetime import datetime
from typing import Dict, Optional
from database_manager import get_db_manager
from logger_config import get_logger

logger = get_logger(__name__)
db_manager = get_db_manager()


class BrandingManager:
    """Manage white-label branding and customization"""
    
    def __init__(self):
        self.default_branding = {
            "app_name": "FYI",
            "logo_url": "/assets/fyi-logo.png",
            "primary_color": "#0066ff",
            "secondary_color": "#00cc88",
            "accent_color": "#ff6600",
            "logo_text": "FYI Social Media Manager",
            "support_email": "support@fyi.com",
            "support_url": "https://fyi.com/support",
            "terms_url": "https://fyi.com/terms",
            "privacy_url": "https://fyi.com/privacy"
        }
    
    def get_branding(self, team_id: int) -> Dict:
        """Get branding configuration for team"""
        try:
            # In production, fetch from database
            team_branding = db_manager.get_settings(team_id=team_id, key="branding")
            
            if team_branding:
                return {**self.default_branding, **json.loads(team_branding)}
            return self.default_branding
        except:
            return self.default_branding
    
    def set_branding(self, team_id: int, branding: Dict) -> bool:
        """Set custom branding for team"""
        try:
            db_manager.save_settings(
                team_id=team_id,
                key="branding",
                value=json.dumps(branding)
            )
            
            db_manager.log_activity(
                team_id=team_id,
                user_id=1,
                action="update_branding",
                target_type="branding",
                target_id=None,
                metadata=branding
            )
            
            logger.info(f"Branding updated for team {team_id}")
            return True
        except Exception as e:
            logger.error(f"Set branding error: {e}")
            return False
    
    def get_white_label_features(self) -> Dict:
        """Get available white-label features"""
        return {
            "custom_logo": {
                "enabled": True,
                "description": "Replace app logo with your brand logo",
                "plan": "pro"
            },
            "custom_domain": {
                "enabled": True,
                "description": "Host on your own domain (e.g., social.yourcompany.com)",
                "plan": "enterprise"
            },
            "custom_colors": {
                "enabled": True,
                "description": "Customize primary, secondary, and accent colors",
                "plan": "pro"
            },
            "remove_branding": {
                "enabled": True,
                "description": "Remove all FYI branding and logos",
                "plan": "enterprise"
            },
            "custom_email": {
                "enabled": True,
                "description": "Send emails from your custom domain",
                "plan": "enterprise"
            },
            "custom_support": {
                "enabled": True,
                "description": "Point to your own support pages and contact",
                "plan": "pro"
            }
        }


class AgencyManager:
    """Manage agency features and client accounts"""
    
    def __init__(self):
        self.plans = {
            "standard": {
                "name": "Standard",
                "max_clients": 10,
                "max_team_members": 5,
                "features": ["basic_branding", "client_isolation"]
            },
            "professional": {
                "name": "Professional",
                "max_clients": 50,
                "max_team_members": 20,
                "features": ["advanced_branding", "client_isolation", "white_label", "api_access"]
            },
            "enterprise": {
                "name": "Enterprise",
                "max_clients": 500,
                "max_team_members": 100,
                "features": ["full_branding", "client_isolation", "white_label", "api_access", "custom_domain", "sso"]
            }
        }
    
    def create_client_account(self, agency_id: int, client_name: str, email: str) -> Dict:
        """Create new client account under agency"""
        try:
            client = {
                "id": db_manager.get_next_team_id(),
                "agency_id": agency_id,
                "name": client_name,
                "email": email,
                "created_at": datetime.now().isoformat(),
                "status": "active",
                "plan": "standard"
            }
            
            db_manager.create_team(client)
            
            db_manager.log_activity(
                team_id=agency_id,
                user_id=1,
                action="create_client",
                target_type="clients",
                target_id=client["id"],
                metadata={"client_name": client_name, "email": email}
            )
            
            logger.info(f"Client account created: {client_name}")
            return client
        except Exception as e:
            logger.error(f"Create client error: {e}")
            return {}
    
    def get_agency_clients(self, agency_id: int) -> list:
        """Get all clients for agency"""
        try:
            # In production, fetch from database
            clients = [
                {
                    "id": 101,
                    "name": "Client A Corp",
                    "email": "admin@clienta.com",
                    "created": "2024-01-01",
                    "status": "active",
                    "posts": 245,
                    "team_members": 5
                },
                {
                    "id": 102,
                    "name": "Client B Inc",
                    "email": "admin@clientb.com",
                    "created": "2024-01-15",
                    "status": "active",
                    "posts": 189,
                    "team_members": 3
                },
                {
                    "id": 103,
                    "name": "Client C Ltd",
                    "email": "admin@clientc.com",
                    "created": "2024-02-01",
                    "status": "active",
                    "posts": 89,
                    "team_members": 2
                }
            ]
            return clients
        except Exception as e:
            logger.error(f"Get agency clients error: {e}")
            return []
    
    def get_client_analytics(self, client_id: int) -> Dict:
        """Get aggregated analytics for client"""
        try:
            analytics = {
                "total_posts": 524,
                "total_engagement": 15482,
                "avg_reach": 3215,
                "followers": 45230,
                "growth_rate": 12.5,
                "top_platform": "Instagram",
                "period": "last_30_days"
            }
            return analytics
        except Exception as e:
            logger.error(f"Get client analytics error: {e}")
            return {}
    
    def set_client_plan(self, client_id: int, plan: str) -> bool:
        """Set client subscription plan"""
        try:
            if plan not in self.plans:
                return False
            
            db_manager.update_settings(
                team_id=client_id,
                key="plan",
                value=plan
            )
            
            db_manager.log_activity(
                team_id=client_id,
                user_id=1,
                action="plan_changed",
                target_type="billing",
                target_id=None,
                metadata={"plan": plan}
            )
            
            logger.info(f"Client {client_id} plan changed to {plan}")
            return True
        except Exception as e:
            logger.error(f"Set client plan error: {e}")
            return False


class MultiTenantManager:
    """Manage multi-tenant administration and isolation"""
    
    def get_tenant_isolation_policy(self, team_id: int) -> Dict:
        """Get isolation policy for team"""
        return {
            "data_isolation": True,
            "api_isolation": True,
            "user_isolation": True,
            "rate_limit": 1000,
            "storage_quota_gb": 100,
            "api_calls_per_day": 100000
        }
    
    def verify_tenant_access(self, user_id: int, team_id: int, resource: str) -> bool:
        """Verify user has access to tenant resource"""
        try:
            # Check if user belongs to team
            user_team = db_manager.get_user_team(user_id=user_id)
            
            if user_team.id != team_id:
                logger.warning(f"Unauthorized access attempt: User {user_id} to Team {team_id}")
                return False
            
            return True
        except:
            return False
    
    def get_tenant_usage(self, team_id: int) -> Dict:
        """Get tenant resource usage"""
        return {
            "storage_used_gb": 45.2,
            "storage_quota_gb": 100,
            "api_calls_today": 52300,
            "api_calls_limit": 100000,
            "active_users": 12,
            "max_users": 25,
            "data_exports": 5
        }
    
    def enforce_tenant_limits(self, team_id: int, resource: str) -> bool:
        """Check if tenant has reached resource limit"""
        usage = self.get_tenant_usage(team_id)
        
        limits = {
            "storage": usage["storage_used_gb"] >= usage["storage_quota_gb"],
            "api_calls": usage["api_calls_today"] >= usage["api_calls_limit"],
            "users": usage["active_users"] >= usage["max_users"]
        }
        
        return limits.get(resource, False)


class CustomDomainManager:
    """Manage custom domain white-label hosting"""
    
    def add_custom_domain(self, team_id: int, domain: str) -> bool:
        """Add custom domain for team"""
        try:
            # Validate domain
            if not self._validate_domain(domain):
                logger.error(f"Invalid domain format: {domain}")
                return False
            
            db_manager.save_settings(
                team_id=team_id,
                key="custom_domain",
                value=domain
            )
            
            db_manager.log_activity(
                team_id=team_id,
                user_id=1,
                action="add_custom_domain",
                target_type="domains",
                target_id=None,
                metadata={"domain": domain}
            )
            
            logger.info(f"Custom domain added: {domain}")
            return True
        except Exception as e:
            logger.error(f"Add custom domain error: {e}")
            return False
    
    def verify_domain_ownership(self, domain: str, verification_code: str) -> bool:
        """Verify domain ownership via DNS"""
        # Mock verification - in production would check DNS records
        logger.info(f"Verifying domain ownership: {domain}")
        return True
    
    def get_dns_records(self, domain: str) -> Dict:
        """Get DNS records needed for custom domain"""
        return {
            "CNAME": {
                "name": f"app.{domain}",
                "value": "app-cname.fyi.com"
            },
            "TXT": {
                "name": domain,
                "value": "fyi-verification-code-12345"
            }
        }
    
    @staticmethod
    def _validate_domain(domain: str) -> bool:
        """Validate domain format"""
        import re
        pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        return re.match(pattern, domain) is not None


class SSOManager:
    """Single Sign-On (SSO) management for enterprise"""
    
    def enable_sso(self, team_id: int, provider: str, config: Dict) -> bool:
        """Enable SSO for team"""
        try:
            supported_providers = ["okta", "azure_ad", "google_workspace", "saml"]
            
            if provider not in supported_providers:
                logger.error(f"Unsupported SSO provider: {provider}")
                return False
            
            db_manager.save_settings(
                team_id=team_id,
                key="sso_provider",
                value=provider
            )
            
            db_manager.save_settings(
                team_id=team_id,
                key="sso_config",
                value=json.dumps(config)
            )
            
            db_manager.log_activity(
                team_id=team_id,
                user_id=1,
                action="enable_sso",
                target_type="sso",
                target_id=None,
                metadata={"provider": provider}
            )
            
            logger.info(f"SSO enabled for team {team_id}: {provider}")
            return True
        except Exception as e:
            logger.error(f"Enable SSO error: {e}")
            return False
    
    def get_sso_config(self, team_id: int) -> Optional[Dict]:
        """Get SSO configuration for team"""
        try:
            sso_provider = db_manager.get_settings(team_id=team_id, key="sso_provider")
            
            if not sso_provider:
                return None
            
            sso_config_json = db_manager.get_settings(team_id=team_id, key="sso_config")
            
            return {
                "provider": sso_provider,
                "config": json.loads(sso_config_json) if sso_config_json else {}
            }
        except:
            return None


# Global instances
_branding_manager = None
_agency_manager = None
_multitenant_manager = None
_custom_domain_manager = None
_sso_manager = None

def get_branding_manager():
    """Get branding manager"""
    global _branding_manager
    if _branding_manager is None:
        _branding_manager = BrandingManager()
    return _branding_manager

def get_agency_manager():
    """Get agency manager"""
    global _agency_manager
    if _agency_manager is None:
        _agency_manager = AgencyManager()
    return _agency_manager

def get_multitenant_manager():
    """Get multi-tenant manager"""
    global _multitenant_manager
    if _multitenant_manager is None:
        _multitenant_manager = MultiTenantManager()
    return _multitenant_manager

def get_custom_domain_manager():
    """Get custom domain manager"""
    global _custom_domain_manager
    if _custom_domain_manager is None:
        _custom_domain_manager = CustomDomainManager()
    return _custom_domain_manager

def get_sso_manager():
    """Get SSO manager"""
    global _sso_manager
    if _sso_manager is None:
        _sso_manager = SSOManager()
    return _sso_manager
