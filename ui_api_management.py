"""
API Management UI for FYI Platform
Manage REST API server, webhooks, API keys, and third-party integrations
"""
import customtkinter as ctk
from datetime import datetime
from database_manager import get_db_manager

db_manager = get_db_manager()


class APIManagementFrame(ctk.CTkFrame):
    """API Management tab with server control, webhooks, and integrations"""
    
    def __init__(self, parent, team_id=1):
        super().__init__(parent)
        self.team_id = team_id
        self.api_running = False
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI layout"""
        # Create tabs for API management
        self.tab_view = ctk.CTkTabview(self, height=600)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Tab 1: Server Control
        self.server_tab = self.tab_view.add("🖥️  Server")
        self._setup_server_tab()
        
        # Tab 2: API Keys
        self.keys_tab = self.tab_view.add("🔑 API Keys")
        self._setup_keys_tab()
        
        # Tab 3: Webhooks
        self.webhooks_tab = self.tab_view.add("🪝 Webhooks")
        self._setup_webhooks_tab()
        
        # Tab 4: Integrations
        self.integrations_tab = self.tab_view.add("🔗 Integrations")
        self._setup_integrations_tab()
        
        # Tab 5: Documentation
        self.docs_tab = self.tab_view.add("📖 Docs")
        self._setup_docs_tab()
    
    def _setup_server_tab(self):
        """Setup server control tab"""
        # Header
        header_frame = ctk.CTkFrame(self.server_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        title = ctk.CTkLabel(header_frame, text="API Server Control", font=("Arial", 16, "bold"))
        title.pack(anchor="w")
        
        # Server status
        status_frame = ctk.CTkFrame(self.server_tab)
        status_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(status_frame, text="Status:", font=("Arial", 12)).pack(side="left", padx=5)
        self.status_label = ctk.CTkLabel(status_frame, text="⚫ Stopped", text_color="red", font=("Arial", 12, "bold"))
        self.status_label.pack(side="left", padx=5)
        
        # Server URL
        url_frame = ctk.CTkFrame(self.server_tab)
        url_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(url_frame, text="URL:", font=("Arial", 11)).pack(side="left", padx=5)
        self.url_label = ctk.CTkLabel(url_frame, text="http://localhost:8000", text_color="gray")
        self.url_label.pack(side="left", padx=5)
        
        # Port configuration
        port_frame = ctk.CTkFrame(self.server_tab)
        port_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(port_frame, text="Port:", font=("Arial", 11)).pack(side="left", padx=5)
        self.port_entry = ctk.CTkEntry(port_frame, width=100)
        self.port_entry.insert(0, "8000")
        self.port_entry.pack(side="left", padx=5)
        
        # Server control buttons
        button_frame = ctk.CTkFrame(self.server_tab)
        button_frame.pack(fill="x", padx=20, pady=20)
        
        self.start_btn = ctk.CTkButton(
            button_frame,
            text="▶️  Start Server",
            command=self._start_server,
            fg_color="green"
        )
        self.start_btn.pack(side="left", padx=5)
        
        self.stop_btn = ctk.CTkButton(
            button_frame,
            text="⏹️  Stop Server",
            command=self._stop_server,
            fg_color="red",
            state="disabled"
        )
        self.stop_btn.pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="🔄 Restart",
            command=self._restart_server
        ).pack(side="left", padx=5)
        
        # Request stats
        stats_frame = ctk.CTkFrame(self.server_tab)
        stats_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(stats_frame, text="API Request Statistics", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        
        stats_data = [
            ("Total Requests", "1,247"),
            ("POST Requests", "523"),
            ("GET Requests", "612"),
            ("Average Response Time", "145ms"),
            ("Errors (24h)", "3"),
        ]
        
        for label, value in stats_data:
            row_frame = ctk.CTkFrame(stats_frame)
            row_frame.pack(fill="x", pady=3)
            ctk.CTkLabel(row_frame, text=f"{label}:", text_color="gray").pack(side="left", padx=5)
            ctk.CTkLabel(row_frame, text=value, font=("Arial", 11, "bold")).pack(side="left", padx=5)
    
    def _setup_keys_tab(self):
        """Setup API keys tab"""
        # Header
        header_frame = ctk.CTkFrame(self.keys_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="API Key Management", font=("Arial", 16, "bold")).pack(anchor="w")
        
        # Generate new key button
        ctk.CTkButton(
            header_frame,
            text="🔐 Generate New Key",
            command=self._generate_key,
            fg_color="blue"
        ).pack(anchor="e", pady=10)
        
        # API Keys list
        keys_frame = ctk.CTkFrame(self.keys_tab)
        keys_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Create scrollable frame
        self.keys_scroll = ctk.CTkScrollableFrame(keys_frame)
        self.keys_scroll.pack(fill="both", expand=True)
        
        # Mock API keys
        keys_data = [
            {
                "name": "Production API Key",
                "key": "fyi_prod_abc123def456",
                "created": "2024-01-15",
                "lastUsed": "2 hours ago",
                "requests": "12,345"
            },
            {
                "name": "Development Key",
                "key": "fyi_dev_xyz789uvw123",
                "created": "2024-01-10",
                "lastUsed": "1 day ago",
                "requests": "456"
            },
            {
                "name": "Zapier Integration",
                "key": "fyi_zapier_automation",
                "created": "2024-01-08",
                "lastUsed": "30 minutes ago",
                "requests": "8,932"
            },
        ]
        
        for key_info in keys_data:
            self._create_key_widget(key_info)
    
    def _create_key_widget(self, key_info):
        """Create API key card widget"""
        card = ctk.CTkFrame(self.keys_scroll, fg_color="gray25")
        card.pack(fill="x", padx=5, pady=8)
        
        # Key name and actions
        header = ctk.CTkFrame(card)
        header.pack(fill="x", padx=10, pady=8)
        
        ctk.CTkLabel(header, text=key_info["name"], font=("Arial", 12, "bold")).pack(side="left", anchor="w", expand=True)
        
        ctk.CTkButton(header, text="📋 Copy", width=80, fg_color="blue").pack(side="left", padx=2)
        ctk.CTkButton(header, text="🗑️ Delete", width=80, fg_color="red").pack(side="left", padx=2)
        
        # Key details
        details_frame = ctk.CTkFrame(card)
        details_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(details_frame, text=f"Key: {key_info['key']}", text_color="gray", font=("Arial", 9)).pack(anchor="w")
        ctk.CTkLabel(details_frame, text=f"Created: {key_info['created']} | Last Used: {key_info['lastUsed']} | Requests: {key_info['requests']}", 
                    text_color="gray", font=("Arial", 9)).pack(anchor="w", pady=3)
    
    def _setup_webhooks_tab(self):
        """Setup webhooks tab"""
        # Header
        header_frame = ctk.CTkFrame(self.webhooks_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Webhook Management", font=("Arial", 16, "bold")).pack(anchor="w")
        
        # Add webhook button
        ctk.CTkButton(
            header_frame,
            text="➕ Add Webhook",
            command=self._add_webhook,
            fg_color="green"
        ).pack(anchor="e", pady=10)
        
        # Webhooks list
        webhooks_frame = ctk.CTkFrame(self.webhooks_tab)
        webhooks_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Create scrollable frame
        self.webhooks_scroll = ctk.CTkScrollableFrame(webhooks_frame)
        self.webhooks_scroll.pack(fill="both", expand=True)
        
        # Mock webhooks
        webhooks_data = [
            {
                "event": "post_published",
                "url": "https://zapier.com/hooks/catch/abc123",
                "status": "Active",
                "deliveries": "342",
                "failures": "2"
            },
            {
                "event": "comment_received",
                "url": "https://make.com/webhook/xyz789",
                "status": "Active",
                "deliveries": "1,234",
                "failures": "8"
            },
            {
                "event": "mention_detected",
                "url": "https://your-api.com/webhooks/mentions",
                "status": "Inactive",
                "deliveries": "0",
                "failures": "0"
            },
        ]
        
        for webhook in webhooks_data:
            self._create_webhook_widget(webhook)
    
    def _create_webhook_widget(self, webhook):
        """Create webhook card widget"""
        card = ctk.CTkFrame(self.webhooks_scroll, fg_color="gray25")
        card.pack(fill="x", padx=5, pady=8)
        
        # Event and status
        header = ctk.CTkFrame(card)
        header.pack(fill="x", padx=10, pady=8)
        
        ctk.CTkLabel(header, text=webhook["event"].upper(), font=("Arial", 12, "bold")).pack(side="left", padx=5)
        
        status_color = "green" if webhook["status"] == "Active" else "gray"
        ctk.CTkLabel(header, text=f"● {webhook['status']}", text_color=status_color, font=("Arial", 11)).pack(side="left", padx=5)
        
        ctk.CTkButton(header, text="⚙️ Test", width=70, fg_color="blue").pack(side="right", padx=2)
        ctk.CTkButton(header, text="🗑️ Delete", width=70, fg_color="red").pack(side="right", padx=2)
        
        # URL
        url_frame = ctk.CTkFrame(card)
        url_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(url_frame, text=f"URL: {webhook['url']}", text_color="gray", font=("Arial", 9)).pack(anchor="w")
        
        # Stats
        stats_frame = ctk.CTkFrame(card)
        stats_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(stats_frame, 
                    text=f"Deliveries: {webhook['deliveries']} | Failures: {webhook['failures']}", 
                    text_color="gray", font=("Arial", 9)).pack(anchor="w")
    
    def _setup_integrations_tab(self):
        """Setup integrations tab"""
        # Header
        header_frame = ctk.CTkFrame(self.integrations_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Third-Party Integrations", font=("Arial", 16, "bold")).pack(anchor="w")
        
        # Integrations grid
        integrations_frame = ctk.CTkFrame(self.integrations_tab)
        integrations_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Create scrollable frame
        integrations_scroll = ctk.CTkScrollableFrame(integrations_frame)
        integrations_scroll.pack(fill="both", expand=True)
        
        # Mock integrations
        integrations = [
            {
                "name": "Zapier",
                "description": "Connect to 5,000+ apps and automate workflows",
                "status": "Connected",
                "icon": "⚡"
            },
            {
                "name": "Make (Integromat)",
                "description": "Advanced automation and workflow builder",
                "status": "Connected",
                "icon": "🔧"
            },
            {
                "name": "IFTTT",
                "description": "Simple automation rules",
                "status": "Not Connected",
                "icon": "📱"
            },
            {
                "name": "Google Sheets",
                "description": "Export analytics and scheduling data",
                "status": "Connected",
                "icon": "📊"
            },
            {
                "name": "Slack",
                "description": "Get notifications in Slack channels",
                "status": "Connected",
                "icon": "💬"
            },
            {
                "name": "Discord",
                "description": "Post updates to Discord servers",
                "status": "Not Connected",
                "icon": "🎮"
            },
        ]
        
        for integration in integrations:
            self._create_integration_widget(integration, integrations_scroll)
    
    def _create_integration_widget(self, integration, parent):
        """Create integration card widget"""
        card = ctk.CTkFrame(parent, fg_color="gray25")
        card.pack(fill="x", padx=5, pady=8)
        
        # Header
        header = ctk.CTkFrame(card)
        header.pack(fill="x", padx=10, pady=8)
        
        ctk.CTkLabel(header, text=f"{integration['icon']} {integration['name']}", font=("Arial", 12, "bold")).pack(anchor="w", expand=True)
        
        status_color = "green" if integration["status"] == "Connected" else "gray"
        status_text = "🔗 Connected" if integration["status"] == "Connected" else "⚪ Not Connected"
        ctk.CTkLabel(header, text=status_text, text_color=status_color).pack(side="right")
        
        # Description
        desc_frame = ctk.CTkFrame(card)
        desc_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(desc_frame, text=integration["description"], text_color="gray", font=("Arial", 10)).pack(anchor="w")
        
        # Action button
        button_frame = ctk.CTkFrame(card)
        button_frame.pack(fill="x", padx=10, pady=5)
        
        if integration["status"] == "Connected":
            ctk.CTkButton(button_frame, text="⚙️ Configure", fg_color="blue", width=120).pack(side="left", padx=5)
            ctk.CTkButton(button_frame, text="🔌 Disconnect", fg_color="red", width=120).pack(side="left", padx=5)
        else:
            ctk.CTkButton(button_frame, text="🔌 Connect", fg_color="green", width=120).pack(side="left", padx=5)
    
    def _setup_docs_tab(self):
        """Setup documentation tab"""
        # Header
        header_frame = ctk.CTkFrame(self.docs_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="API Documentation", font=("Arial", 16, "bold")).pack(anchor="w")
        
        # Documentation content
        docs_frame = ctk.CTkFrame(self.docs_tab)
        docs_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        docs_scroll = ctk.CTkScrollableFrame(docs_frame)
        docs_scroll.pack(fill="both", expand=True)
        
        # API endpoints documentation
        docs_sections = [
            ("GET /api/posts", "Retrieve all posts for team"),
            ("POST /api/posts", "Create new post draft"),
            ("POST /api/posts/schedule", "Schedule post for specific time"),
            ("PUT /api/posts/{id}", "Update post status"),
            ("DELETE /api/posts/{id}", "Delete post"),
            ("GET /api/analytics", "Get analytics data"),
            ("GET /api/accounts", "Get team accounts"),
            ("POST /api/webhooks", "Register webhook for events"),
            ("GET /api/health", "Check API server status"),
        ]
        
        for endpoint, description in docs_sections:
            section_frame = ctk.CTkFrame(docs_scroll, fg_color="gray25")
            section_frame.pack(fill="x", padx=5, pady=5)
            
            ctk.CTkLabel(section_frame, text=endpoint, font=("Arial", 11, "bold"), text_color="cyan").pack(anchor="w", padx=10, pady=5)
            ctk.CTkLabel(section_frame, text=description, text_color="gray", font=("Arial", 10)).pack(anchor="w", padx=20, pady=3)
        
        # Code examples section
        examples_label = ctk.CTkLabel(docs_scroll, text="Code Examples", font=("Arial", 12, "bold"))
        examples_label.pack(anchor="w", pady=10)
        
        example_frame = ctk.CTkFrame(docs_scroll, fg_color="gray20")
        example_frame.pack(fill="x", padx=5, pady=5)
        
        example_code = """# Python Example
import requests

API_KEY = "fyi_prod_abc123"
headers = {"Authorization": f"Bearer {API_KEY}"}

# Get posts
response = requests.get("http://localhost:8000/api/posts", headers=headers)
posts = response.json()

# Schedule post
data = {
    "platform": "facebook",
    "content": "Hello world!",
    "scheduled_at": "2024-02-15T14:30:00"
}
response = requests.post("http://localhost:8000/api/posts/schedule", json=data, headers=headers)"""
        
        ctk.CTkLabel(example_frame, text=example_code, text_color="lightgreen", font=("Courier", 9), justify="left").pack(anchor="nw", padx=10, pady=10)
    
    # ===== ACTION HANDLERS =====
    
    def _start_server(self):
        """Start API server"""
        self.api_running = True
        self.status_label.configure(text="🟢 Running", text_color="green")
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        
        db_manager.log_activity(
            team_id=self.team_id,
            user_id=1,
            action="start_api_server",
            target_type="api",
            target_id=None,
            metadata={"port": self.port_entry.get()}
        )
    
    def _stop_server(self):
        """Stop API server"""
        self.api_running = False
        self.status_label.configure(text="⚫ Stopped", text_color="red")
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        
        db_manager.log_activity(
            team_id=self.team_id,
            user_id=1,
            action="stop_api_server",
            target_type="api",
            target_id=None,
            metadata={}
        )
    
    def _restart_server(self):
        """Restart API server"""
        self._stop_server()
        self._start_server()
    
    def _generate_key(self):
        """Generate new API key"""
        db_manager.log_activity(
            team_id=self.team_id,
            user_id=1,
            action="generate_api_key",
            target_type="api_keys",
            target_id=None,
            metadata={}
        )
    
    def _add_webhook(self):
        """Add new webhook"""
        db_manager.log_activity(
            team_id=self.team_id,
            user_id=1,
            action="add_webhook",
            target_type="webhooks",
            target_id=None,
            metadata={}
        )
