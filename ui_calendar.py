"""
Calendar Module for FYI Social Media Management Platform
Visual content calendar with drag-and-drop scheduling and platform color-coding
"""
import customtkinter as ctk
from tkinter import ttk
from datetime import datetime, timedelta
from typing import List, Dict, Callable
from database_manager import get_db_manager, Post
from logger_config import get_logger

logger = get_logger(__name__)

# Platform colors
PLATFORM_COLORS = {
    "facebook": "#1877F2",
    "instagram": "#E4405F",
    "twitter": "#1DA1F2",
    "linkedin": "#0A66C2",
    "youtube": "#FF0000",
    "tiktok": "#000000",
    "pinterest": "#E60023",
    "threads": "#000000",
}

class ContentCalendarFrame(ctk.CTkFrame):
    """Visual content calendar showing scheduled posts"""
    
    def __init__(self, parent, team_id: int, on_post_selected: Callable = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.team_id = team_id
        self.db = get_db_manager()
        self.on_post_selected = on_post_selected
        self.current_month = datetime.now()
        self.selected_date = None
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """Create calendar UI components"""
        # Header with navigation
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            header_frame, text="← Prev", width=80,
            command=self._prev_month
        ).pack(side="left", padx=5)
        
        self.month_label = ctk.CTkLabel(
            header_frame, text="", font=("Arial", 16, "bold")
        )
        self.month_label.pack(side="left", expand=True)
        
        ctk.CTkButton(
            header_frame, text="Next →", width=80,
            command=self._next_month
        ).pack(side="left", padx=5)
        
        # Calendar grid
        self.calendar_frame = ctk.CTkFrame(self)
        self.calendar_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _prev_month(self):
        """Go to previous month"""
        self.current_month = self.current_month.replace(day=1) - timedelta(days=1)
        self.current_month = self.current_month.replace(day=1)
        self.refresh()
    
    def _next_month(self):
        """Go to next month"""
        self.current_month = self.current_month.replace(day=1) + timedelta(days=32)
        self.current_month = self.current_month.replace(day=1)
        self.refresh()
    
    def refresh(self):
        """Refresh calendar display"""
        self.month_label.configure(text=self.current_month.strftime("%B %Y"))
        
        # Clear previous calendar
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()
        
        # Get posts for this month
        posts = self.db.get_posts(self.team_id, {"status": "scheduled"})
        posts_by_date = {}
        for post in posts:
            if post.scheduled_time:
                date = post.scheduled_time.split(" ")[0]  # YYYY-MM-DD
                if date not in posts_by_date:
                    posts_by_date[date] = []
                posts_by_date[date].append(post)
        
        # Draw calendar
        self._draw_calendar(posts_by_date)
    
    def _draw_calendar(self, posts_by_date: Dict):
        """Draw calendar grid with posts"""
        import calendar
        
        cal = calendar.monthcalendar(self.current_month.year, self.current_month.month)
        
        # Day headers
        for day_name in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]:
            label = ctk.CTkLabel(self.calendar_frame, text=day_name, font=("Arial", 12, "bold"))
            label.grid(sticky="nsew", padx=2, pady=2)
        
        # Calendar days
        row = 1
        for week in cal:
            for col, day in enumerate(week):
                if day == 0:
                    continue
                
                date_str = self.current_month.replace(day=day).strftime("%Y-%m-%d")
                day_frame = ctk.CTkFrame(self.calendar_frame, fg_color="#2B2B2B", border_width=1, border_color="#444")
                day_frame.grid(row=row, column=col, sticky="nsew", padx=2, pady=2)
                
                # Day number
                day_label = ctk.CTkLabel(
                    day_frame, text=str(day), font=("Arial", 10, "bold"),
                    text_color="#FFFFFF"
                )
                day_label.pack(anchor="nw", padx=5, pady=3)
                
                # Posts for this day
                if date_str in posts_by_date:
                    for post in posts_by_date[date_str]:
                        self._draw_post_badge(day_frame, post)
            
            row += 1
    
    def _draw_post_badge(self, parent_frame, post: Post):
        """Draw a post badge in calendar cell"""
        color = PLATFORM_COLORS.get(post.platform, "#999999")
        
        badge = ctk.CTkLabel(
            parent_frame,
            text=post.platform[:3].upper(),
            fg_color=color,
            text_color="#FFFFFF",
            font=("Arial", 8, "bold"),
            padx=5, pady=2,
            corner_radius=3
        )
        badge.pack(fill="x", padx=2, pady=1)
        
        # Tooltip on hover
        badge.bind("<Enter>", lambda e: self._show_tooltip(badge, post))
        badge.bind("<Leave>", lambda e: self._hide_tooltip(badge))
        badge.bind("<Button-1>", lambda e: self.on_post_selected(post) if self.on_post_selected else None)
    
    def _show_tooltip(self, widget, post: Post):
        """Show post details in tooltip"""
        title = post.title or post.content[:30]
        widget.configure(text=f"{post.platform[:3].upper()}\n{title[:15]}...")
    
    def _hide_tooltip(self, widget):
        """Hide tooltip"""
        widget.configure(text=widget.cget("text").split("\n")[0])
