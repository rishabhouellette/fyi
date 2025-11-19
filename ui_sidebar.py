"""
Modern Sidebar Navigation
Provides Hootsuite-style left sidebar for FYI Uploader
Premium futuristic design with neon accents
"""
import customtkinter as ctk
from theme_manager import get_theme_manager

class SidebarNavigation:
    def __init__(self, parent, on_nav_callback=None):
        self.parent = parent
        self.on_nav_callback = on_nav_callback
        self.active_item = "dashboard"
        
        # Get current theme
        self.theme_manager = get_theme_manager()
        current_mode = ctk.get_appearance_mode()
        theme = self.theme_manager.get_theme(current_mode)
        
        # Apply theme colors
        self.bg_dark = theme["sidebar_bg"]
        self.bg_hover = theme["bg_secondary"]  # Use lighter bg_secondary for better contrast
        self.accent_blue = theme["accent_primary"]
        self.text_primary = theme["text_primary"]
        self.text_secondary = theme["text_secondary"]
        
        # Navigation items: (id, label, icon)
        self.nav_items = [
            ("dashboard", "📊 Dashboard", "Dashboard"),
            ("upload", "📤 Upload", "Upload"),
            ("platforms", "🌐 Platforms", "Platforms"),
            ("calendar", "📅 Calendar", "Calendar"),
            ("analytics", "📈 Analytics", "Analytics"),
            ("content_lib", "📚 Content Library", "Content"),
            ("ai_tools", "🤖 AI Tools", "AI"),
            ("team", "👥 Team", "Team"),
            ("settings", "⚙️ Settings", "Settings"),
        ]
        
        self.buttons = {}
    
    def create_sidebar(self):
        """Create the sidebar frame - DEPRECATED, use _create_sidebar_content instead"""
        return None
    
    def _create_sidebar_content(self, parent_frame):
        """Create sidebar content inside a provided frame (for grid layout)"""
        # Logo/Title area
        logo_frame = ctk.CTkFrame(parent_frame, fg_color=self.bg_dark)
        logo_frame.pack(fill="x", padx=15, pady=20)
        
        logo_label = ctk.CTkLabel(
            logo_frame,
            text="📱 FYI",
            font=("Helvetica", 20, "bold"),
            text_color=self.accent_blue
        )
        logo_label.pack()
        
        subtitle = ctk.CTkLabel(
            logo_frame,
            text="Uploader",
            font=("Helvetica", 10),
            text_color=self.text_secondary
        )
        subtitle.pack()
        
        # Separator
        sep1 = ctk.CTkFrame(parent_frame, fg_color=self.bg_hover, height=1)
        sep1.pack(fill="x", padx=10, pady=10)
        
        # Navigation items
        nav_frame = ctk.CTkFrame(parent_frame, fg_color=self.bg_dark)
        nav_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        for item_id, label, shorthand in self.nav_items:
            self._create_nav_button(nav_frame, item_id, label, shorthand)
        
        # Separator
        sep2 = ctk.CTkFrame(parent_frame, fg_color=self.bg_hover, height=1)
        sep2.pack(fill="x", padx=10, pady=10)
        
        # Footer section
        footer_frame = ctk.CTkFrame(parent_frame, fg_color=self.bg_dark)
        footer_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(
            footer_frame,
            text="v2.0",
            font=("Helvetica", 9),
            text_color=self.text_secondary
        ).pack()
    
    def _create_nav_button(self, parent, item_id, label, shorthand):
        """Create a navigation button"""
        # Determine button colors based on active state
        is_active = item_id == self.active_item
        btn_fg_color = self.accent_blue if is_active else self.bg_hover
        btn_text_color = "#000000" if is_active else self.text_primary
        
        btn = ctk.CTkButton(
            parent,
            text=label,
            font=("Helvetica", 12),
            fg_color=btn_fg_color,
            hover_color=self.bg_hover,
            text_color=btn_text_color,
            command=lambda: self._on_nav_click(item_id),
            anchor="w",
            height=40,
            corner_radius=6,
        )
        btn.pack(fill="x", padx=10, pady=5)
        self.buttons[item_id] = btn
    
    def _on_nav_click(self, item_id):
        """Handle navigation click"""
        # Update active state
        for bid, btn in self.buttons.items():
            if bid == item_id:
                btn.configure(
                    fg_color=self.accent_blue,
                    text_color="#000000"
                )
                self.active_item = item_id
            else:
                btn.configure(
                    fg_color=self.bg_hover,
                    text_color=self.text_primary
                )
        
        # Call callback
        if self.on_nav_callback:
            self.on_nav_callback(item_id)
    
    def set_active(self, item_id):
        """Set active navigation item"""
        if item_id in self.buttons:
            self._on_nav_click(item_id)
