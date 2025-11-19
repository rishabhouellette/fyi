"""
Analytics Dashboard Module for FYI Social Media Management Platform
Displays reach, engagement, growth, and trending metrics
"""
import customtkinter as ctk
from tkinter import ttk
from datetime import datetime, timedelta
from typing import List
from database_manager import get_db_manager, AnalyticsMetric
from logger_config import get_logger

logger = get_logger(__name__)

class AnalyticsDashboardFrame(ctk.CTkFrame):
    """Analytics dashboard showing performance metrics"""
    
    def __init__(self, parent, team_id: int, **kwargs):
        super().__init__(parent, **kwargs)
        self.team_id = team_id
        self.db = get_db_manager()
        self.selected_days = 30
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """Create analytics UI components"""
        # Header with date range selector
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Analytics", font=("Arial", 18, "bold")).pack(side="left")
        
        ctk.CTkLabel(header_frame, text="Days:").pack(side="right", padx=5)
        for days in [7, 30, 90]:
            btn = ctk.CTkButton(
                header_frame, text=str(days), width=40,
                command=lambda d=days: self._set_date_range(d)
            )
            btn.pack(side="right", padx=2)
        
        # Metrics cards
        self.metrics_frame = ctk.CTkFrame(self)
        self.metrics_frame.pack(fill="x", padx=10, pady=10)
        
        # Charts placeholder (will use matplotlib or similar)
        self.chart_frame = ctk.CTkFrame(self)
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Detailed metrics table
        self.table_frame = ctk.CTkFrame(self)
        self.table_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _set_date_range(self, days: int):
        """Set date range for analytics"""
        self.selected_days = days
        self.refresh()
    
    def refresh(self):
        """Refresh analytics display"""
        # Get metrics for selected period
        metrics = self.db.get_analytics(self.team_id, days=self.selected_days)
        
        # Clear previous metrics
        for widget in self.metrics_frame.winfo_children():
            widget.destroy()
        
        if not metrics:
            ctk.CTkLabel(self.metrics_frame, text="No analytics data available").pack()
            return
        
        # Calculate aggregates
        total_reach = sum(m.reach for m in metrics)
        total_engagement = sum(m.engagement for m in metrics)
        total_followers = metrics[-1].followers if metrics else 0
        avg_engagement_rate = (total_engagement / total_reach * 100) if total_reach > 0 else 0
        
        # Display metric cards
        metrics_data = [
            ("Reach", str(total_reach), "#1877F2"),
            ("Engagement", str(total_engagement), "#E4405F"),
            ("Engagement Rate", f"{avg_engagement_rate:.1f}%", "#FF6B6B"),
            ("Followers", str(total_followers), "#51CF66"),
        ]
        
        for metric_name, metric_value, color in metrics_data:
            self._create_metric_card(metric_name, metric_value, color)
        
        # Display table
        self._update_metrics_table(metrics)
    
    def _create_metric_card(self, name: str, value: str, color: str):
        """Create a metric card"""
        card = ctk.CTkFrame(self.metrics_frame, fg_color=color, corner_radius=10)
        card.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        
        ctk.CTkLabel(card, text=name, font=("Arial", 12)).pack(pady=5)
        ctk.CTkLabel(card, text=value, font=("Arial", 24, "bold"), text_color="#FFFFFF").pack(pady=10)
    
    def _update_metrics_table(self, metrics: List[AnalyticsMetric]):
        """Update metrics table"""
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        
        # Table header
        headers = ["Date", "Platform", "Reach", "Engagement", "Followers", "Engagement %"]
        
        for col, header in enumerate(headers):
            label = ctk.CTkLabel(
                self.table_frame, text=header, font=("Arial", 11, "bold"),
                text_color="#CCCCCC"
            )
            label.grid(row=0, column=col, sticky="w", padx=5, pady=5)
        
        # Table rows
        for row, metric in enumerate(metrics[:20], 1):  # Show last 20
            data = [
                metric.metric_date,
                metric.platform,
                str(metric.reach),
                str(metric.engagement),
                str(metric.followers),
                f"{(metric.engagement / metric.reach * 100):.1f}%" if metric.reach > 0 else "0%"
            ]
            
            for col, value in enumerate(data):
                label = ctk.CTkLabel(
                    self.table_frame, text=value, font=("Arial", 10),
                    text_color="#AAAAAA"
                )
                label.grid(row=row, column=col, sticky="w", padx=5, pady=3)
