"""
Analytics Dashboard UI
Displays social media performance metrics and insights inspired by Hootsuite
Futuristic dark mode with neon accents
"""
import customtkinter as ctk
from datetime import datetime, timedelta
from database_manager import get_db_manager
from theme_manager import get_theme_manager

class DashboardUI:
    def __init__(self, parent, theme_manager=None):
        self.parent = parent
        self.theme_manager = theme_manager or get_theme_manager()
        self.db_manager = get_db_manager()
        
        # Get current theme
        self.current_mode = ctk.get_appearance_mode()
        theme = self.theme_manager.get_theme(self.current_mode)
        
        # Apply theme colors
        self.bg_primary = theme["bg_primary"]
        self.bg_secondary = theme["bg_secondary"]
        self.accent_primary = theme["accent_primary"]
        self.accent_secondary = theme["accent_secondary"]
        self.accent_success = theme["accent_success"]
        self.accent_danger = theme["accent_danger"]
        self.text_primary = theme["text_primary"]
        self.text_secondary = theme["text_secondary"]
        self.card_bg = theme["card_bg"]
        self.border = theme["border"]
        
    def setup_ui(self):
        """Create the dashboard layout"""
        # Main container
        main_frame = ctk.CTkFrame(self.parent, fg_color=self.bg_primary)
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Header section
        self._setup_header(main_frame)
        
        # Scrollable content area
        scroll_frame = ctk.CTkScrollableFrame(main_frame, fg_color=self.bg_primary)
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Metrics row 1
        self._setup_metrics_row_1(scroll_frame)
        
        # Metrics row 2
        self._setup_metrics_row_2(scroll_frame)
        
        # Insights section
        self._setup_insights_section(scroll_frame)
        
        # Performance factors section
        self._setup_performance_factors(scroll_frame)
        
        return main_frame
    
    def _setup_header(self, parent):
        """Header with title and filters - enhanced styling"""
        header_frame = ctk.CTkFrame(parent, fg_color=self.bg_primary)
        header_frame.pack(fill="x", padx=15, pady=(20, 10))
        
        # Title with gradient-like effect
        title_label = ctk.CTkLabel(
            header_frame,
            text="Social score and insights",
            font=("Helvetica", 32, "bold"),
            text_color=self.accent_primary
        )
        title_label.pack(side="left", padx=0, pady=10)
        
        # Right side filters
        filter_frame = ctk.CTkFrame(header_frame, fg_color=self.bg_primary)
        filter_frame.pack(side="right", padx=0, pady=10)
        
        # Period selector with better styling
        period_menu = ctk.CTkOptionMenu(
            filter_frame,
            values=["Weekly overview", "Monthly overview", "Daily overview"],
            fg_color=self.card_bg,
            button_color=self.accent_primary,
            text_color=self.text_primary,
            font=("Helvetica", 11),
            corner_radius=10
        )
        period_menu.pack(side="left", padx=10)
        period_menu.set("Weekly overview")
        
        # Date range with accent color
        date_label = ctk.CTkLabel(
            filter_frame,
            text=self._get_date_range(),
            font=("Helvetica", 12, "bold"),
            text_color=self.accent_primary
        )
        date_label.pack(side="left", padx=10)
    
    def _get_date_range(self):
        """Generate date range string"""
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        return f"For {week_ago.strftime('%b %d')} - {today.strftime('%b %d, %Y')}"
    
    def _setup_metrics_row_1(self, parent):
        """First row of metrics with enhanced styling"""
        row_frame = ctk.CTkFrame(parent, fg_color=self.bg_primary)
        row_frame.pack(fill="x", pady=15)
        
        # Social Performance Score
        self._create_metric_card(
            row_frame,
            title="Social performance score",
            value="937",
            max_value="1,000",
            insight="Doing great!",
            detail="Over the past two months, your score has\nconsistently improved, and it's even higher\nthan your average earlier this year!",
            position="left"
        )
        
        # Placeholder for chart on the right with enhanced styling
        chart_frame = ctk.CTkFrame(row_frame, fg_color=self.card_bg, corner_radius=14, border_width=2, border_color=self.accent_secondary)
        chart_frame.pack(side="right", fill="both", expand=True, padx=(15, 0))
        
        chart_label = ctk.CTkLabel(
            chart_frame,
            text="📊 Score Trend Chart",
            font=("Helvetica", 13, "bold"),
            text_color=self.accent_secondary
        )
        chart_label.pack(expand=True)
    
    def _setup_metrics_row_2(self, parent):
        """Second row of performance metrics"""
        row_frame = ctk.CTkFrame(parent, fg_color=self.bg_primary)
        row_frame.pack(fill="x", pady=15)
        
        metrics = [
            ("Post Views", "2,847", "📊"),
            ("Post Clicks", "456", "🖱️"),
            ("Post Interactions", "189", "❤️"),
            ("Post Comments", "34", "💬"),
        ]
        
        for title, value, icon in metrics:
            self._create_small_metric_card(row_frame, icon, title, value)
    
    def _setup_insights_section(self, parent):
        """Insights and factors section with enhanced styling"""
        insights_frame = ctk.CTkFrame(parent, fg_color=self.bg_primary)
        insights_frame.pack(fill="x", pady=(20, 15))
        
        # Title with accent color
        title_label = ctk.CTkLabel(
            insights_frame,
            text="Factors influencing your score over the past 8 weeks",
            font=("Helvetica", 15, "bold"),
            text_color=self.accent_primary
        )
        title_label.pack(anchor="w", pady=(0, 18))
        
        # Factors grid
        factors_container = ctk.CTkFrame(insights_frame, fg_color=self.bg_primary)
        factors_container.pack(fill="x")
        
        factors = [
            ("📈 Post Views", "Positive trend"),
            ("🔗 Post Clicks", "Positive trend"),
            ("📊 Post Interactions", "Stable"),
            ("💬 Post Comments", "Growing"),
            ("♻️ Post Shares", "Moderate"),
            ("👥 Followers", "Steady growth"),
        ]
        
        for i, (factor, status) in enumerate(factors):
            col = i % 3
            row = i // 3
            self._create_factor_item(factors_container, factor, status, col, row)
    
    def _setup_performance_factors(self, parent):
        """Performance summary section with enhanced styling"""
        perf_frame = ctk.CTkFrame(parent, fg_color=self.card_bg, corner_radius=14, border_width=2, border_color=self.accent_primary)
        perf_frame.pack(fill="x", pady=20, padx=0)
        
        label = ctk.CTkLabel(
            perf_frame,
            text="💡 Performance Summary",
            font=("Helvetica", 13, "bold"),
            text_color=self.accent_primary
        )
        label.pack(anchor="w", padx=20, pady=(16, 8))
        
        summary = ctk.CTkLabel(
            perf_frame,
            text="Your content is performing well across all platforms. Focus on engagement-driving content.\nContinue posting at optimal times for maximum reach.",
            font=("Helvetica", 11),
            text_color=self.text_secondary,
            justify="left"
        )
        summary.pack(anchor="w", padx=20, pady=(0, 16))
    
    def _create_metric_card(self, parent, title, value, max_value, insight, detail, position="left"):
        """Create a large metric card with enhanced visual appeal"""
        # Use a more vibrant card background with border
        card_frame = ctk.CTkFrame(parent, fg_color=self.card_bg, corner_radius=16, border_width=2, border_color=self.accent_primary)
        card_frame.pack(side=position, fill="both", expand=True, padx=(0, 15 if position == "left" else 0))
        
        # Title
        title_label = ctk.CTkLabel(
            card_frame,
            text=title,
            font=("Helvetica", 13, "bold"),
            text_color=self.text_secondary
        )
        title_label.pack(anchor="w", padx=20, pady=(20, 10))
        
        # Large score display with glow effect
        score_frame = ctk.CTkFrame(card_frame, fg_color=self.card_bg)
        score_frame.pack(anchor="w", padx=20, pady=15)
        
        score_label = ctk.CTkLabel(
            score_frame,
            text=f"{value}/{max_value}",
            font=("Helvetica", 56, "bold"),
            text_color=self.accent_primary
        )
        score_label.pack(side="left")
        
        # Insight text with accent color
        insight_label = ctk.CTkLabel(
            card_frame,
            text=insight,
            font=("Helvetica", 13, "bold"),
            text_color=self.accent_success
        )
        insight_label.pack(anchor="w", padx=20, pady=(5, 8))
        
        # Detail text with better styling
        detail_label = ctk.CTkLabel(
            card_frame,
            text=detail,
            font=("Helvetica", 11),
            text_color=self.text_secondary,
            justify="left"
        )
        detail_label.pack(anchor="w", padx=20, pady=(0, 20))
    
    def _create_small_metric_card(self, parent, icon, title, value):
        """Create a small metric card with enhanced visual appeal"""
        card_frame = ctk.CTkFrame(parent, fg_color=self.card_bg, corner_radius=14, border_width=1.5, border_color=self.accent_primary)
        card_frame.pack(side="left", fill="both", expand=True, padx=7.5)
        
        # Icon + Title
        header_frame = ctk.CTkFrame(card_frame, fg_color=self.card_bg)
        header_frame.pack(anchor="w", padx=16, pady=(14, 6), fill="x")
        
        icon_label = ctk.CTkLabel(
            header_frame,
            text=icon,
            font=("Helvetica", 18)
        )
        icon_label.pack(side="left", padx=(0, 10))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text=title,
            font=("Helvetica", 10, "bold"),
            text_color=self.text_secondary
        )
        title_label.pack(side="left")
        
        # Value with accent color
        value_label = ctk.CTkLabel(
            card_frame,
            text=value,
            font=("Helvetica", 24, "bold"),
            text_color=self.accent_primary
        )
        value_label.pack(anchor="w", padx=16, pady=(0, 14))
    
    def _create_factor_item(self, parent, factor, status, col, row):
        """Create a performance factor item with enhanced styling"""
        item_frame = ctk.CTkFrame(parent, fg_color=self.card_bg, corner_radius=12, border_width=1.5, border_color=self.accent_primary)
        
        # Grid positioning
        item_frame.grid(row=row, column=col, padx=7, pady=7, sticky="nsew")
        parent.grid_columnconfigure(col, weight=1)
        
        # Factor label
        factor_label = ctk.CTkLabel(
            item_frame,
            text=factor,
            font=("Helvetica", 11, "bold"),
            text_color=self.text_primary
        )
        factor_label.pack(anchor="w", padx=14, pady=(12, 4))
        
        # Status label with accent
        status_label = ctk.CTkLabel(
            item_frame,
            text=status,
            font=("Helvetica", 10, "bold"),
            text_color=self.accent_success
        )
        status_label.pack(anchor="w", padx=14, pady=(0, 12))


def create_dashboard_tab(parent, theme_manager=None):
    """Create and return the dashboard tab"""
    dashboard = DashboardUI(parent, theme_manager)
    return dashboard.setup_ui()
