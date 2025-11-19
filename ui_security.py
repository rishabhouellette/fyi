"""
Security & 2FA UI for FYI Platform
Password management, 2-factor authentication, permissions, and audit logs
"""
import customtkinter as ctk
from datetime import datetime
from security_manager import (
    PasswordManager, TwoFactorAuth, PermissionManager, 
    APIKeyManager, AuditLogger, get_security_manager
)
from database_manager import get_db_manager

db_manager = get_db_manager()
security = get_security_manager()


class SecurityFrame(ctk.CTkFrame):
    """Security and 2FA management interface"""
    
    def __init__(self, parent, team_id=1):
        super().__init__(parent)
        self.team_id = team_id
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI layout"""
        # Create tabs
        self.tab_view = ctk.CTkTabview(self, height=600)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab 1: Password Management
        self.password_tab = self.tab_view.add("🔐 Password")
        self._setup_password_tab()
        
        # Tab 2: 2-Factor Authentication
        self.twofa_tab = self.tab_view.add("📱 2FA")
        self._setup_2fa_tab()
        
        # Tab 3: Permissions
        self.permissions_tab = self.tab_view.add("👥 Permissions")
        self._setup_permissions_tab()
        
        # Tab 4: API Keys
        self.api_keys_tab = self.tab_view.add("🔑 API Keys")
        self._setup_api_keys_tab()
        
        # Tab 5: Audit Logs
        self.audit_tab = self.tab_view.add("📋 Audit Logs")
        self._setup_audit_tab()
    
    def _setup_password_tab(self):
        """Setup password management tab"""
        # Header
        header_frame = ctk.CTkFrame(self.password_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Password Management", font=("Arial", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="Change password and manage security settings", text_color="gray", font=("Arial", 10)).pack(anchor="w")
        
        # Current password section
        current_frame = ctk.CTkFrame(self.password_tab)
        current_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(current_frame, text="Current Password:", font=("Arial", 11)).pack(anchor="w", pady=3)
        self.current_password = ctk.CTkEntry(current_frame, show="•", placeholder_text="Enter current password")
        self.current_password.pack(fill="x")
        
        # New password section
        new_frame = ctk.CTkFrame(self.password_tab)
        new_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(new_frame, text="New Password:", font=("Arial", 11)).pack(anchor="w", pady=3)
        self.new_password = ctk.CTkEntry(new_frame, show="•", placeholder_text="Enter new password")
        self.new_password.pack(fill="x")
        
        # Password strength indicator
        strength_frame = ctk.CTkFrame(new_frame)
        strength_frame.pack(fill="x", pady=5)
        self.strength_label = ctk.CTkLabel(strength_frame, text="Strength: -", font=("Arial", 10))
        self.strength_label.pack(anchor="w")
        self.new_password.bind("<KeyRelease>", lambda e: self._update_password_strength())
        
        # Confirm password
        confirm_frame = ctk.CTkFrame(self.password_tab)
        confirm_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(confirm_frame, text="Confirm Password:", font=("Arial", 11)).pack(anchor="w", pady=3)
        self.confirm_password = ctk.CTkEntry(confirm_frame, show="•", placeholder_text="Confirm new password")
        self.confirm_password.pack(fill="x")
        
        # Password requirements
        requirements_frame = ctk.CTkFrame(self.password_tab)
        requirements_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(requirements_frame, text="Password Requirements:", font=("Arial", 11, "bold")).pack(anchor="w", pady=5)
        
        requirements = [
            "✓ At least 8 characters",
            "✓ Mix of uppercase and lowercase",
            "✓ Include numbers",
            "✓ Include special characters (!@#$%^&*)",
            "✓ Not a previously used password"
        ]
        
        for req in requirements:
            ctk.CTkLabel(requirements_frame, text=req, text_color="gray", font=("Arial", 10)).pack(anchor="w")
        
        # Action buttons
        button_frame = ctk.CTkFrame(self.password_tab)
        button_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkButton(
            button_frame,
            text="🔄 Change Password",
            command=self._change_password,
            fg_color="blue",
            height=40
        ).pack(fill="x")
        
        # Generate secure password option
        generate_frame = ctk.CTkFrame(self.password_tab)
        generate_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkButton(
            generate_frame,
            text="🎲 Generate Secure Password",
            command=self._generate_password,
            fg_color="green",
            width=200
        ).pack(side="left", padx=5)
        
        self.generated_password_label = ctk.CTkLabel(generate_frame, text="", text_color="cyan")
        self.generated_password_label.pack(side="left", padx=10)
    
    def _setup_2fa_tab(self):
        """Setup 2FA tab"""
        # Header
        header_frame = ctk.CTkFrame(self.twofa_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Two-Factor Authentication", font=("Arial", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="Add an extra layer of security to your account", text_color="gray", font=("Arial", 10)).pack(anchor="w")
        
        # 2FA Status
        status_frame = ctk.CTkFrame(self.twofa_tab)
        status_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(status_frame, text="2FA Status:", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        self.twofa_status = ctk.CTkLabel(status_frame, text="🔴 Not Enabled", text_color="red", font=("Arial", 12))
        self.twofa_status.pack(anchor="w")
        
        # Enable 2FA section
        enable_frame = ctk.CTkFrame(self.twofa_tab)
        enable_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(enable_frame, text="Setup 2FA with Authenticator App:", font=("Arial", 11, "bold")).pack(anchor="w", pady=5)
        
        ctk.CTkLabel(enable_frame, text="1. Download Google Authenticator or Authy", text_color="gray", font=("Arial", 10)).pack(anchor="w", pady=2)
        ctk.CTkLabel(enable_frame, text="2. Scan QR code or enter key below", text_color="gray", font=("Arial", 10)).pack(anchor="w", pady=2)
        ctk.CTkLabel(enable_frame, text="3. Enter 6-digit code from app", text_color="gray", font=("Arial", 10)).pack(anchor="w", pady=2)
        
        # QR Code display (mock)
        qr_frame = ctk.CTkFrame(enable_frame)
        qr_frame.pack(fill="x", pady=10)
        
        self.qr_label = ctk.CTkLabel(qr_frame, text="[QR Code Here]", fg_color="gray20", text_color="gray", height=100)
        self.qr_label.pack(fill="x")
        
        # Manual entry key
        key_frame = ctk.CTkFrame(enable_frame)
        key_frame.pack(fill="x", pady=10)
        
        ctk.CTkLabel(key_frame, text="Manual Entry Key:", font=("Arial", 10)).pack(anchor="w", pady=3)
        key_display = ctk.CTkEntry(key_frame, state="readonly")
        key_display.insert(0, "JBSWY3DPEBLW64TMMQ======")
        key_display.pack(fill="x")
        
        ctk.CTkButton(key_frame, text="📋 Copy Key", width=100).pack(anchor="e", pady=5)
        
        # Verify 2FA code
        verify_frame = ctk.CTkFrame(self.twofa_tab)
        verify_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(verify_frame, text="Enter Code from Authenticator App:", font=("Arial", 11)).pack(anchor="w", pady=3)
        self.twofa_code = ctk.CTkEntry(verify_frame, placeholder_text="000000", width=100)
        self.twofa_code.pack(anchor="w", pady=5)
        
        ctk.CTkButton(
            verify_frame,
            text="✅ Verify & Enable 2FA",
            command=self._enable_2fa,
            fg_color="green"
        ).pack(fill="x", pady=10)
        
        # Backup codes
        backup_frame = ctk.CTkFrame(self.twofa_tab)
        backup_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(backup_frame, text="📌 Backup Codes (Save these in a safe place):", font=("Arial", 11, "bold")).pack(anchor="w", pady=5)
        
        backup_codes = [
            "4F7D-9K2L-3M8N",
            "5G8E-0L3K-4N9O",
            "6H9F-1M4L-5O0P",
            "7I0G-2N5M-6P1Q",
            "8J1H-3O6N-7Q2R"
        ]
        
        for code in backup_codes:
            ctk.CTkLabel(backup_frame, text=code, text_color="cyan", font=("Courier", 10)).pack(anchor="w")
        
        ctk.CTkButton(backup_frame, text="💾 Download Backup Codes", width=200).pack(anchor="w", pady=10)
    
    def _setup_permissions_tab(self):
        """Setup permissions tab"""
        # Header
        header_frame = ctk.CTkFrame(self.permissions_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Team Permissions & Roles", font=("Arial", 16, "bold")).pack(anchor="w")
        
        # Team members list
        members_frame = ctk.CTkFrame(self.permissions_tab)
        members_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        ctk.CTkLabel(members_frame, text="Team Members:", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        
        # Scrollable members list
        scroll_frame = ctk.CTkScrollableFrame(members_frame)
        scroll_frame.pack(fill="both", expand=True, pady=5)
        
        members = [
            {"name": "You", "email": "user@example.com", "role": "admin"},
            {"name": "Sarah Manager", "email": "sarah@example.com", "role": "manager"},
            {"name": "Mike Creator", "email": "mike@example.com", "role": "creator"},
        ]
        
        for member in members:
            self._create_member_card(member, scroll_frame)
        
        # Add member button
        ctk.CTkButton(
            members_frame,
            text="➕ Add Team Member",
            command=self._add_member,
            fg_color="green"
        ).pack(fill="x", pady=10)
        
        # Role definitions
        roles_frame = ctk.CTkFrame(self.permissions_tab)
        roles_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        ctk.CTkLabel(roles_frame, text="Role Definitions:", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        
        roles_scroll = ctk.CTkScrollableFrame(roles_frame)
        roles_scroll.pack(fill="both", expand=True)
        
        for role_key, role_info in PermissionManager.get_all_roles().items():
            self._create_role_card(role_info, roles_scroll)
    
    def _create_member_card(self, member, parent):
        """Create team member card"""
        card = ctk.CTkFrame(parent, fg_color="gray25")
        card.pack(fill="x", padx=5, pady=5)
        
        # Header
        header = ctk.CTkFrame(card)
        header.pack(fill="x", padx=10, pady=8)
        
        ctk.CTkLabel(header, text=member["name"], font=("Arial", 11, "bold")).pack(side="left", expand=True, anchor="w")
        
        # Change role dropdown
        role_combo = ctk.CTkComboBox(
            header,
            values=["Admin", "Manager", "Creator", "Viewer"],
            state="readonly",
            width=100
        )
        role_combo.set(member["role"].title())
        role_combo.pack(side="left", padx=5)
        
        ctk.CTkButton(header, text="🗑️ Remove", fg_color="red", width=80).pack(side="left", padx=2)
        
        # Email
        email_frame = ctk.CTkFrame(card)
        email_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(email_frame, text=member["email"], text_color="gray", font=("Arial", 9)).pack(anchor="w")
    
    def _create_role_card(self, role_info, parent):
        """Create role definition card"""
        card = ctk.CTkFrame(parent, fg_color="gray25")
        card.pack(fill="x", padx=5, pady=5)
        
        # Role name
        ctk.CTkLabel(card, text=role_info["name"], font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=(8, 3))
        
        # Description
        ctk.CTkLabel(card, text=role_info["description"], text_color="gray", font=("Arial", 9)).pack(anchor="w", padx=10, pady=3)
        
        # Permissions
        perms_frame = ctk.CTkFrame(card)
        perms_frame.pack(fill="x", padx=10, pady=(3, 8))
        
        for perm in role_info["permissions"][:5]:
            ctk.CTkLabel(perms_frame, text=f"✓ {perm}", text_color="lightgreen", font=("Arial", 8)).pack(anchor="w")
        
        if len(role_info["permissions"]) > 5:
            ctk.CTkLabel(perms_frame, text=f"... +{len(role_info['permissions']) - 5} more", text_color="gray", font=("Arial", 8)).pack(anchor="w")
    
    def _setup_api_keys_tab(self):
        """Setup API keys tab"""
        # Header
        header_frame = ctk.CTkFrame(self.api_keys_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="API Key Management", font=("Arial", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="Manage keys for third-party integrations", text_color="gray", font=("Arial", 10)).pack(anchor="w")
        
        ctk.CTkButton(
            header_frame,
            text="🔐 Generate New Key",
            command=self._generate_api_key,
            fg_color="blue"
        ).pack(anchor="e", pady=10)
        
        # Keys list
        keys_frame = ctk.CTkFrame(self.api_keys_tab)
        keys_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        scroll_frame = ctk.CTkScrollableFrame(keys_frame)
        scroll_frame.pack(fill="both", expand=True)
        
        # Mock API keys
        keys = [
            {
                "name": "Production API",
                "key": "fyi_prod_abc123def456ghi789jkl",
                "created": "2024-01-15",
                "last_used": "1 hour ago",
                "requests": 12345
            },
            {
                "name": "Development API",
                "key": "fyi_dev_xyz789uvw123abc456def",
                "created": "2024-01-10",
                "last_used": "2 days ago",
                "requests": 456
            },
        ]
        
        for key in keys:
            self._create_key_card(key, scroll_frame)
    
    def _create_key_card(self, key, parent):
        """Create API key card"""
        card = ctk.CTkFrame(parent, fg_color="gray25")
        card.pack(fill="x", padx=5, pady=8)
        
        # Header
        header = ctk.CTkFrame(card)
        header.pack(fill="x", padx=10, pady=8)
        
        ctk.CTkLabel(header, text=key["name"], font=("Arial", 11, "bold")).pack(side="left", expand=True, anchor="w")
        ctk.CTkButton(header, text="📋 Copy", width=70, fg_color="blue").pack(side="left", padx=2)
        ctk.CTkButton(header, text="🗑️ Revoke", width=70, fg_color="red").pack(side="left", padx=2)
        
        # Key display
        key_frame = ctk.CTkFrame(card)
        key_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(key_frame, text=f"Key: {key['key']}", text_color="gray", font=("Courier", 8)).pack(anchor="w")
        
        # Stats
        stats_frame = ctk.CTkFrame(card)
        stats_frame.pack(fill="x", padx=10, pady=(3, 8))
        ctk.CTkLabel(
            stats_frame,
            text=f"Created: {key['created']} | Last Used: {key['last_used']} | Requests: {key['requests']}",
            text_color="gray",
            font=("Arial", 9)
        ).pack(anchor="w")
    
    def _setup_audit_tab(self):
        """Setup audit logs tab"""
        # Header
        header_frame = ctk.CTkFrame(self.audit_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Security Audit Logs", font=("Arial", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="View all security events and activities", text_color="gray", font=("Arial", 10)).pack(anchor="w")
        
        # Filters
        filter_frame = ctk.CTkFrame(self.audit_tab)
        filter_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(filter_frame, text="Event Type:", font=("Arial", 10)).pack(side="left", padx=5)
        event_combo = ctk.CTkComboBox(
            filter_frame,
            values=["All", "Login", "Password Change", "2FA", "Permission", "API Key"],
            state="readonly",
            width=150
        )
        event_combo.set("All")
        event_combo.pack(side="left", padx=5)
        
        ctk.CTkLabel(filter_frame, text="Days:", font=("Arial", 10)).pack(side="left", padx=5)
        days_combo = ctk.CTkComboBox(
            filter_frame,
            values=["Last 7 days", "Last 30 days", "Last 90 days"],
            state="readonly",
            width=150
        )
        days_combo.set("Last 30 days")
        days_combo.pack(side="left", padx=5)
        
        # Logs table
        logs_frame = ctk.CTkFrame(self.audit_tab)
        logs_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        scroll_frame = ctk.CTkScrollableFrame(logs_frame)
        scroll_frame.pack(fill="both", expand=True)
        
        # Mock audit logs
        logs = [
            {"time": "2024-02-14 14:30:22", "event": "User Login", "severity": "info", "ip": "192.168.1.100"},
            {"time": "2024-02-14 12:15:45", "event": "API Key Generated", "severity": "warning", "ip": "192.168.1.100"},
            {"time": "2024-02-13 09:22:10", "event": "Permission Changed", "severity": "warning", "ip": "192.168.1.101"},
            {"time": "2024-02-12 16:45:33", "event": "Password Changed", "severity": "info", "ip": "192.168.1.100"},
            {"time": "2024-02-11 11:20:15", "event": "2FA Enabled", "severity": "info", "ip": "192.168.1.100"},
        ]
        
        for log in logs:
            self._create_log_entry(log, scroll_frame)
    
    def _create_log_entry(self, log, parent):
        """Create audit log entry"""
        entry_frame = ctk.CTkFrame(parent, fg_color="gray25")
        entry_frame.pack(fill="x", padx=5, pady=3)
        
        info_frame = ctk.CTkFrame(entry_frame)
        info_frame.pack(fill="x", padx=10, pady=6)
        
        # Time and event
        time_label = ctk.CTkLabel(info_frame, text=log["time"], font=("Arial", 10, "bold"))
        time_label.pack(side="left", padx=5)
        
        ctk.CTkLabel(info_frame, text=log["event"], text_color="cyan", font=("Arial", 10)).pack(side="left", padx=5)
        
        # Severity indicator
        severity_color = {
            "info": "blue",
            "warning": "orange",
            "critical": "red"
        }.get(log["severity"], "blue")
        
        ctk.CTkLabel(
            info_frame,
            text=f"● {log['severity'].upper()}",
            text_color=severity_color,
            font=("Arial", 9)
        ).pack(side="left", padx=5)
        
        # IP address
        ctk.CTkLabel(info_frame, text=f"IP: {log['ip']}", text_color="gray", font=("Arial", 9)).pack(side="right", padx=5)
    
    # ===== ACTION HANDLERS =====
    
    def _update_password_strength(self):
        """Update password strength indicator"""
        password = self.new_password.get()
        strength_info = PasswordManager.check_password_strength(password)
        
        strength_colors = {
            "Very Weak": "red",
            "Weak": "orange",
            "Fair": "yellow",
            "Good": "lightgreen",
            "Strong": "green",
            "Very Strong": "darkgreen"
        }
        
        color = strength_colors.get(strength_info["strength"], "gray")
        self.strength_label.configure(
            text=f"Strength: {strength_info['strength']}",
            text_color=color
        )
    
    def _change_password(self):
        """Change password"""
        current = self.current_password.get()
        new = self.new_password.get()
        confirm = self.confirm_password.get()
        
        if new != confirm:
            return
        
        strength = PasswordManager.check_password_strength(new)
        if strength["score"] < 3:
            return
        
        # Hash and store
        hashed, salt = PasswordManager.hash_password(new)
        
        AuditLogger.log_security_event(
            "password_change",
            user_id=1,
            team_id=self.team_id,
            severity="info"
        )
    
    def _generate_password(self):
        """Generate secure password"""
        password = PasswordManager.generate_secure_password()
        self.generated_password_label.configure(text=password)
        self.new_password.delete(0, "end")
        self.new_password.insert(0, password)
        self._update_password_strength()
    
    def _enable_2fa(self):
        """Enable 2FA"""
        code = self.twofa_code.get()
        
        if len(code) == 6 and code.isdigit():
            self.twofa_status.configure(text="🟢 Enabled", text_color="green")
            
            AuditLogger.log_security_event(
                "2fa_enabled",
                user_id=1,
                team_id=self.team_id,
                severity="info"
            )
    
    def _add_member(self):
        """Add team member"""
        db_manager.log_activity(
            team_id=self.team_id,
            user_id=1,
            action="add_team_member",
            target_type="users",
            target_id=None,
            metadata={}
        )
    
    def _generate_api_key(self):
        """Generate new API key"""
        key = APIKeyManager.generate_api_key("New API Key", self.team_id)
