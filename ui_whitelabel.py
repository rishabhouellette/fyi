"""
White-label & Agency UI for FYI Platform
Branding customization, agency management, and multi-tenant administration
"""
import customtkinter as ctk
from whitelabel_manager import (
    get_branding_manager, get_agency_manager, get_multitenant_manager,
    get_custom_domain_manager, get_sso_manager
)
from database_manager import get_db_manager

db_manager = get_db_manager()
branding_mgr = get_branding_manager()
agency_mgr = get_agency_manager()
multitenant_mgr = get_multitenant_manager()
domain_mgr = get_custom_domain_manager()
sso_mgr = get_sso_manager()


class WhiteLabelFrame(ctk.CTkFrame):
    """White-label and agency administration interface"""
    
    def __init__(self, parent, team_id=1):
        super().__init__(parent)
        self.team_id = team_id
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI layout"""
        # Create tabs
        self.tab_view = ctk.CTkTabview(self, height=600)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab 1: Branding
        self.branding_tab = self.tab_view.add("🎨 Branding")
        self._setup_branding_tab()
        
        # Tab 2: Agency Management
        self.agency_tab = self.tab_view.add("🏢 Agency")
        self._setup_agency_tab()
        
        # Tab 3: Custom Domain
        self.domain_tab = self.tab_view.add("🌐 Domain")
        self._setup_domain_tab()
        
        # Tab 4: SSO
        self.sso_tab = self.tab_view.add("🔐 SSO")
        self._setup_sso_tab()
        
        # Tab 5: Usage
        self.usage_tab = self.tab_view.add("📊 Usage")
        self._setup_usage_tab()
    
    def _setup_branding_tab(self):
        """Setup branding customization tab"""
        # Header
        header_frame = ctk.CTkFrame(self.branding_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="White-Label Branding", font=("Arial", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="Customize app appearance with your brand", text_color="gray", font=("Arial", 10)).pack(anchor="w")
        
        # Logo section
        logo_frame = ctk.CTkFrame(self.branding_tab)
        logo_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(logo_frame, text="🖼️ Logo", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        ctk.CTkLabel(logo_frame, text="Upload your company logo (PNG, JPG, up to 2MB)", text_color="gray", font=("Arial", 9)).pack(anchor="w", pady=2)
        
        logo_button_frame = ctk.CTkFrame(logo_frame)
        logo_button_frame.pack(fill="x", pady=8)
        ctk.CTkButton(logo_button_frame, text="📁 Choose File", fg_color="blue").pack(side="left", padx=5)
        ctk.CTkLabel(logo_button_frame, text="No file selected", text_color="gray").pack(side="left", padx=5)
        
        # App name
        name_frame = ctk.CTkFrame(self.branding_tab)
        name_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(name_frame, text="📱 App Name", font=("Arial", 12, "bold")).pack(anchor="w", pady=3)
        self.app_name = ctk.CTkEntry(name_frame, placeholder_text="e.g., MyBrand Social Manager")
        self.app_name.insert(0, "FYI")
        self.app_name.pack(fill="x")
        
        # Color customization
        colors_frame = ctk.CTkFrame(self.branding_tab)
        colors_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(colors_frame, text="🎯 Brand Colors", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        
        # Primary color
        primary_frame = ctk.CTkFrame(colors_frame)
        primary_frame.pack(fill="x", pady=8)
        ctk.CTkLabel(primary_frame, text="Primary Color:", width=120).pack(side="left", padx=5)
        ctk.CTkButton(primary_frame, text="■ #0066ff", width=80, fg_color="#0066ff").pack(side="left", padx=5)
        ctk.CTkButton(primary_frame, text="Choose", fg_color="gray", width=80).pack(side="left", padx=5)
        
        # Secondary color
        secondary_frame = ctk.CTkFrame(colors_frame)
        secondary_frame.pack(fill="x", pady=8)
        ctk.CTkLabel(secondary_frame, text="Secondary Color:", width=120).pack(side="left", padx=5)
        ctk.CTkButton(secondary_frame, text="■ #00cc88", width=80, fg_color="#00cc88").pack(side="left", padx=5)
        ctk.CTkButton(secondary_frame, text="Choose", fg_color="gray", width=80).pack(side="left", padx=5)
        
        # Accent color
        accent_frame = ctk.CTkFrame(colors_frame)
        accent_frame.pack(fill="x", pady=8)
        ctk.CTkLabel(accent_frame, text="Accent Color:", width=120).pack(side="left", padx=5)
        ctk.CTkButton(accent_frame, text="■ #ff6600", width=80, fg_color="#ff6600").pack(side="left", padx=5)
        ctk.CTkButton(accent_frame, text="Choose", fg_color="gray", width=80).pack(side="left", padx=5)
        
        # Support info
        support_frame = ctk.CTkFrame(self.branding_tab)
        support_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(support_frame, text="💬 Support Information", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        
        email_frame = ctk.CTkFrame(support_frame)
        email_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(email_frame, text="Support Email:", width=120).pack(side="left", padx=5)
        support_email = ctk.CTkEntry(email_frame, placeholder_text="support@example.com")
        support_email.insert(0, "support@fyi.com")
        support_email.pack(side="left", fill="x", expand=True, padx=5)
        
        url_frame = ctk.CTkFrame(support_frame)
        url_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(url_frame, text="Support URL:", width=120).pack(side="left", padx=5)
        support_url = ctk.CTkEntry(url_frame, placeholder_text="https://support.example.com")
        support_url.insert(0, "https://fyi.com/support")
        support_url.pack(side="left", fill="x", expand=True, padx=5)
        
        # Save button
        ctk.CTkButton(
            self.branding_tab,
            text="💾 Save Branding",
            command=self._save_branding,
            fg_color="green",
            height=40
        ).pack(fill="x", padx=15, pady=15)
    
    def _setup_agency_tab(self):
        """Setup agency management tab"""
        # Header
        header_frame = ctk.CTkFrame(self.agency_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Agency Management", font=("Arial", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="Manage client accounts and plans", text_color="gray", font=("Arial", 10)).pack(anchor="w")
        
        ctk.CTkButton(
            header_frame,
            text="➕ Add Client",
            command=self._add_client,
            fg_color="green"
        ).pack(anchor="e", pady=10)
        
        # Statistics
        stats_frame = ctk.CTkFrame(self.agency_tab)
        stats_frame.pack(fill="x", padx=15, pady=10)
        
        stats_data = [
            ("Total Clients", "3"),
            ("Active Users", "12"),
            ("Total Posts", "524"),
            ("Revenue", "$12,450/mo")
        ]
        
        for label, value in stats_data:
            stat_card = ctk.CTkFrame(stats_frame, fg_color="gray25")
            stat_card.pack(fill="x", padx=5, pady=3)
            ctk.CTkLabel(stat_card, text=f"{label}: {value}", font=("Arial", 11)).pack(anchor="w", padx=10, pady=8)
        
        # Clients list
        clients_frame = ctk.CTkFrame(self.agency_tab)
        clients_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        ctk.CTkLabel(clients_frame, text="📋 Your Clients:", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        
        scroll_frame = ctk.CTkScrollableFrame(clients_frame)
        scroll_frame.pack(fill="both", expand=True)
        
        clients = agency_mgr.get_agency_clients(self.team_id)
        
        for client in clients:
            self._create_client_card(client, scroll_frame)
    
    def _create_client_card(self, client, parent):
        """Create client card widget"""
        card = ctk.CTkFrame(parent, fg_color="gray25")
        card.pack(fill="x", padx=5, pady=8)
        
        # Header
        header = ctk.CTkFrame(card)
        header.pack(fill="x", padx=10, pady=8)
        
        ctk.CTkLabel(header, text=client["name"], font=("Arial", 11, "bold")).pack(side="left", expand=True, anchor="w")
        
        # Plan dropdown
        plan_combo = ctk.CTkComboBox(
            header,
            values=["Standard", "Professional", "Enterprise"],
            state="readonly",
            width=120
        )
        plan_combo.set("Standard")
        plan_combo.pack(side="left", padx=5)
        
        # Actions
        ctk.CTkButton(header, text="⚙️ Manage", width=80).pack(side="left", padx=2)
        ctk.CTkButton(header, text="🗑️ Remove", fg_color="red", width=80).pack(side="left", padx=2)
        
        # Details
        details_frame = ctk.CTkFrame(card)
        details_frame.pack(fill="x", padx=10, pady=(0, 8))
        
        details_text = f"Email: {client['email']} | Created: {client['created']} | Posts: {client['posts']} | Team: {client['team_members']}"
        ctk.CTkLabel(details_frame, text=details_text, text_color="gray", font=("Arial", 9)).pack(anchor="w")
    
    def _setup_domain_tab(self):
        """Setup custom domain tab"""
        # Header
        header_frame = ctk.CTkFrame(self.domain_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Custom Domain", font=("Arial", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="Host FYI on your own domain (Enterprise feature)", text_color="gray", font=("Arial", 10)).pack(anchor="w")
        
        # Current domain
        current_frame = ctk.CTkFrame(self.domain_tab)
        current_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(current_frame, text="📍 Current Domain:", font=("Arial", 11)).pack(anchor="w", pady=3)
        ctk.CTkLabel(current_frame, text="app.fyi.com (Default)", text_color="cyan", font=("Arial", 11, "bold")).pack(anchor="w")
        
        # Add custom domain
        custom_frame = ctk.CTkFrame(self.domain_tab)
        custom_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(custom_frame, text="🌐 Add Custom Domain:", font=("Arial", 11, "bold")).pack(anchor="w", pady=5)
        
        domain_input_frame = ctk.CTkFrame(custom_frame)
        domain_input_frame.pack(fill="x", pady=8)
        
        self.domain_input = ctk.CTkEntry(domain_input_frame, placeholder_text="e.g., app.yourcompany.com")
        self.domain_input.pack(side="left", fill="x", expand=True, padx=5)
        
        ctk.CTkButton(
            domain_input_frame,
            text="➕ Add",
            command=self._add_domain,
            fg_color="green",
            width=80
        ).pack(side="left", padx=5)
        
        # DNS Setup
        dns_frame = ctk.CTkFrame(self.domain_tab)
        dns_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(dns_frame, text="🔗 DNS Configuration Required:", font=("Arial", 11, "bold")).pack(anchor="w", pady=5)
        
        dns_records = [
            {"type": "CNAME", "name": "app.yourcompany.com", "value": "app-cname.fyi.com"},
            {"type": "TXT", "name": "yourcompany.com", "value": "fyi-verification-12345"}
        ]
        
        for record in dns_records:
            record_frame = ctk.CTkFrame(dns_frame)
            record_frame.pack(fill="x", pady=5)
            
            ctk.CTkLabel(record_frame, text=f"{record['type']}:", font=("Arial", 10, "bold"), width=50).pack(side="left", padx=5)
            ctk.CTkLabel(record_frame, text=record["name"], text_color="cyan", font=("Courier", 9)).pack(side="left", padx=5)
            ctk.CTkLabel(record_frame, text="→", text_color="gray").pack(side="left", padx=5)
            ctk.CTkLabel(record_frame, text=record["value"], text_color="lightgreen", font=("Courier", 9)).pack(side="left", padx=5)
        
        # Verification
        verify_frame = ctk.CTkFrame(self.domain_tab)
        verify_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkButton(
            verify_frame,
            text="✅ Verify Ownership",
            command=self._verify_domain,
            fg_color="blue",
            height=40
        ).pack(fill="x", pady=10)
    
    def _setup_sso_tab(self):
        """Setup SSO tab"""
        # Header
        header_frame = ctk.CTkFrame(self.sso_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Single Sign-On (SSO)", font=("Arial", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="Enterprise authentication (requires Enterprise plan)", text_color="gray", font=("Arial", 10)).pack(anchor="w")
        
        # SSO Status
        status_frame = ctk.CTkFrame(self.sso_tab)
        status_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(status_frame, text="SSO Status:", font=("Arial", 11, "bold")).pack(anchor="w", pady=3)
        ctk.CTkLabel(status_frame, text="🔴 Not Enabled", text_color="red", font=("Arial", 11)).pack(anchor="w")
        
        # Provider selection
        provider_frame = ctk.CTkFrame(self.sso_tab)
        provider_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(provider_frame, text="Select SSO Provider:", font=("Arial", 11, "bold")).pack(anchor="w", pady=5)
        
        providers = [
            {"name": "Okta", "icon": "🔐"},
            {"name": "Azure AD", "icon": "☁️"},
            {"name": "Google Workspace", "icon": "📧"},
            {"name": "SAML 2.0", "icon": "🔑"}
        ]
        
        for provider in providers:
            provider_card = ctk.CTkFrame(provider_frame)
            provider_card.pack(fill="x", pady=5)
            
            ctk.CTkLabel(provider_card, text=f"{provider['icon']} {provider['name']}", font=("Arial", 10)).pack(side="left", padx=5)
            ctk.CTkButton(provider_card, text="Configure", width=100, fg_color="blue").pack(side="right", padx=5)
        
        # Configuration
        config_frame = ctk.CTkFrame(self.sso_tab)
        config_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(config_frame, text="SSO Configuration:", font=("Arial", 11, "bold")).pack(anchor="w", pady=5)
        
        ctk.CTkLabel(config_frame, text="SSO URL:", font=("Arial", 10)).pack(anchor="w", pady=3)
        sso_url = ctk.CTkEntry(config_frame, placeholder_text="https://your-sso-provider.com/auth")
        sso_url.pack(fill="x", pady=3)
        
        ctk.CTkLabel(config_frame, text="Client ID:", font=("Arial", 10)).pack(anchor="w", pady=3)
        client_id = ctk.CTkEntry(config_frame, placeholder_text="Your SSO client ID")
        client_id.pack(fill="x", pady=3)
        
        ctk.CTkLabel(config_frame, text="Client Secret:", font=("Arial", 10)).pack(anchor="w", pady=3)
        client_secret = ctk.CTkEntry(config_frame, show="•", placeholder_text="Your SSO client secret")
        client_secret.pack(fill="x", pady=3)
        
        ctk.CTkButton(
            config_frame,
            text="🔐 Enable SSO",
            command=self._enable_sso,
            fg_color="green",
            height=40
        ).pack(fill="x", pady=15)
    
    def _setup_usage_tab(self):
        """Setup usage and quotas tab"""
        # Header
        header_frame = ctk.CTkFrame(self.usage_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Resource Usage & Quotas", font=("Arial", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="Monitor team resource consumption", text_color="gray", font=("Arial", 10)).pack(anchor="w")
        
        # Usage metrics
        usage = multitenant_mgr.get_tenant_usage(self.team_id)
        
        metrics_frame = ctk.CTkFrame(self.usage_tab)
        metrics_frame.pack(fill="x", padx=15, pady=15)
        
        # Storage usage
        self._create_usage_meter(
            metrics_frame,
            "Storage",
            f"{usage['storage_used_gb']} GB / {usage['storage_quota_gb']} GB",
            usage['storage_used_gb'] / usage['storage_quota_gb']
        )
        
        # API calls usage
        self._create_usage_meter(
            metrics_frame,
            "API Calls (Today)",
            f"{usage['api_calls_today']} / {usage['api_calls_limit']}",
            usage['api_calls_today'] / usage['api_calls_limit']
        )
        
        # Team members
        self._create_usage_meter(
            metrics_frame,
            "Team Members",
            f"{usage['active_users']} / {usage['max_users']}",
            usage['active_users'] / usage['max_users']
        )
    
    def _create_usage_meter(self, parent, label, text, percentage):
        """Create usage meter widget"""
        card = ctk.CTkFrame(parent)
        card.pack(fill="x", padx=5, pady=10)
        
        # Label
        label_frame = ctk.CTkFrame(card)
        label_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(label_frame, text=label, font=("Arial", 11, "bold")).pack(side="left")
        ctk.CTkLabel(label_frame, text=text, text_color="cyan", font=("Arial", 10)).pack(side="right")
        
        # Progress bar
        percentage = min(1.0, percentage)
        color = "green" if percentage < 0.7 else "orange" if percentage < 0.9 else "red"
        
        progress_frame = ctk.CTkFrame(card, fg_color="gray20", height=20)
        progress_frame.pack(fill="x", pady=5)
        progress_frame.pack_propagate(False)
        
        progress_bar = ctk.CTkFrame(progress_frame, fg_color=color, height=20)
        progress_bar.pack(fill="both", side="left", expand=False)
        progress_bar.pack_propagate(False)
        
        # Set width based on percentage
        card.update()
        progress_bar.configure(width=int(card.winfo_width() * percentage))
    
    # ===== ACTION HANDLERS =====
    
    def _save_branding(self):
        """Save branding changes"""
        branding = {
            "app_name": self.app_name.get(),
        }
        branding_mgr.set_branding(self.team_id, branding)
    
    def _add_client(self):
        """Add new client"""
        db_manager.log_activity(
            team_id=self.team_id,
            user_id=1,
            action="create_client",
            target_type="clients",
            target_id=None,
            metadata={}
        )
    
    def _add_domain(self):
        """Add custom domain"""
        domain = self.domain_input.get()
        if domain:
            domain_mgr.add_custom_domain(self.team_id, domain)
    
    def _verify_domain(self):
        """Verify domain ownership"""
        domain = self.domain_input.get()
        if domain:
            domain_mgr.verify_domain_ownership(domain, "verification-code")
    
    def _enable_sso(self):
        """Enable SSO"""
        sso_mgr.enable_sso(self.team_id, "okta", {})
