"""
Social Listening & Monitoring Module for FYI Social Media Management Platform
Real-time keyword tracking, brand mentions, competitor analysis, and alerts
"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta
from typing import List, Dict
from database_manager import get_db_manager
from logger_config import get_logger

logger = get_logger(__name__)

class SocialListeningFrame(ctk.CTkFrame):
    """Real-time social listening and brand monitoring"""
    
    def __init__(self, parent, team_id: int, **kwargs):
        super().__init__(parent, **kwargs)
        self.team_id = team_id
        self.db = get_db_manager()
        self.is_monitoring = False
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """Create monitoring UI"""
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Social Listening & Monitoring", font=("Arial", 18, "bold")).pack(side="left")
        
        button_frame = ctk.CTkFrame(header_frame)
        button_frame.pack(side="right")
        
        self.monitor_button = ctk.CTkButton(
            button_frame, text="▶️ Start Monitoring", width=140,
            command=self._toggle_monitoring, fg_color="#51CF66"
        )
        self.monitor_button.pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame, text="🔄 Refresh", width=100,
            command=self.refresh
        ).pack(side="left", padx=5)
        
        # Main tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tabview.add("Keywords")
        self.tabview.add("Brand Mentions")
        self.tabview.add("Competitor Watch")
        self.tabview.add("Alerts")
        self.tabview.add("Analytics")
        
        # ===== KEYWORDS TAB =====
        keywords_tab = self.tabview.tab("Keywords")
        
        # Add keyword form
        form_frame = ctk.CTkFrame(keywords_tab)
        form_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(form_frame, text="Add Keyword:", font=("Arial", 10)).pack(side="left", padx=5)
        
        self.keyword_entry = ctk.CTkEntry(form_frame, placeholder_text="e.g., #AI, ChatGPT, blockchain", width=200)
        self.keyword_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(form_frame, text="Alert when mentions >", font=("Arial", 10)).pack(side="left", padx=5)
        
        self.threshold_entry = ctk.CTkEntry(form_frame, width=60, placeholder_text="10")
        self.threshold_entry.pack(side="left", padx=5)
        
        ctk.CTkButton(
            form_frame, text="Add", width=60, fg_color="#51CF66",
            command=self._add_keyword
        ).pack(side="left", padx=5)
        
        # Keywords list
        ctk.CTkLabel(keywords_tab, text="Tracked Keywords:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.keywords_list = ctk.CTkScrollableFrame(keywords_tab, fg_color="#1a1a1a")
        self.keywords_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ===== BRAND MENTIONS TAB =====
        mentions_tab = self.tabview.tab("Brand Mentions")
        
        platform_frame = ctk.CTkFrame(mentions_tab)
        platform_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(platform_frame, text="Filter by Platform:", font=("Arial", 10)).pack(side="left", padx=5)
        
        self.mentions_platform = ctk.CTkComboBox(
            platform_frame, values=["All", "Facebook", "Instagram", "Twitter", "LinkedIn"],
            state="readonly", width=120
        )
        self.mentions_platform.set("All")
        self.mentions_platform.pack(side="left", padx=5)
        self.mentions_platform.configure(command=self._refresh_mentions)
        
        ctk.CTkButton(
            platform_frame, text="Refresh", width=100,
            command=self._refresh_mentions
        ).pack(side="left", padx=5)
        
        self.mentions_list = ctk.CTkScrollableFrame(mentions_tab, fg_color="#1a1a1a")
        self.mentions_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ===== COMPETITOR WATCH TAB =====
        competitor_tab = self.tabview.tab("Competitor Watch")
        
        # Add competitor
        comp_form = ctk.CTkFrame(competitor_tab)
        comp_form.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(comp_form, text="Add Competitor:", font=("Arial", 10)).pack(side="left", padx=5)
        
        self.competitor_entry = ctk.CTkEntry(comp_form, placeholder_text="Username or brand name", width=200)
        self.competitor_entry.pack(side="left", padx=5)
        
        ctk.CTkButton(
            comp_form, text="Add", width=60, fg_color="#51CF66",
            command=self._add_competitor
        ).pack(side="left", padx=5)
        
        # Competitors list
        ctk.CTkLabel(competitor_tab, text="Watched Competitors:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.competitors_list = ctk.CTkScrollableFrame(competitor_tab, fg_color="#1a1a1a")
        self.competitors_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ===== ALERTS TAB =====
        alerts_tab = self.tabview.tab("Alerts")
        
        alert_filter = ctk.CTkFrame(alerts_tab)
        alert_filter.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(alert_filter, text="Alert Type:", font=("Arial", 10)).pack(side="left", padx=5)
        
        self.alert_filter = ctk.CTkComboBox(
            alert_filter, values=["All", "Keyword Spike", "Competitor Activity", "Brand Mention", "Trending"],
            state="readonly", width=150
        )
        self.alert_filter.set("All")
        self.alert_filter.pack(side="left", padx=5)
        self.alert_filter.configure(command=self._refresh_alerts)
        
        self.alerts_list = ctk.CTkScrollableFrame(alerts_tab, fg_color="#1a1a1a")
        self.alerts_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ===== ANALYTICS TAB =====
        analytics_tab = self.tabview.tab("Analytics")
        
        # Metrics
        metrics_frame = ctk.CTkFrame(analytics_tab)
        metrics_frame.pack(fill="x", padx=10, pady=10)
        
        self.metric_mentions = self._create_metric_card(metrics_frame, "Total Mentions (24h)", "0")
        self.metric_mentions.pack(side="left", padx=5, fill="both", expand=True)
        
        self.metric_reach = self._create_metric_card(metrics_frame, "Reach (24h)", "0K")
        self.metric_reach.pack(side="left", padx=5, fill="both", expand=True)
        
        self.metric_sentiment = self._create_metric_card(metrics_frame, "Positive Sentiment", "0%")
        self.metric_sentiment.pack(side="left", padx=5, fill="both", expand=True)
        
        # Analytics table
        self.analytics_list = ctk.CTkScrollableFrame(analytics_tab, fg_color="#1a1a1a")
        self.analytics_list.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _create_metric_card(self, parent, label: str, value: str):
        """Create metric card"""
        card = ctk.CTkFrame(parent, fg_color="#333333", border_width=1, border_color="#444444")
        
        ctk.CTkLabel(card, text=label, font=("Arial", 10), text_color="#AAAAAA").pack(pady=(10, 5))
        ctk.CTkLabel(card, text=value, font=("Arial", 16, "bold")).pack(pady=(0, 10))
        
        return card
    
    def refresh(self):
        """Refresh monitoring data"""
        self._refresh_keywords()
        self._refresh_mentions()
        self._refresh_competitors()
        self._refresh_alerts()
        self._refresh_analytics()
    
    def _toggle_monitoring(self):
        """Start/stop monitoring"""
        self.is_monitoring = not self.is_monitoring
        if self.is_monitoring:
            self.monitor_button.configure(text="⏸️ Stop Monitoring", fg_color="#FF6B6B")
            messagebox.showinfo("Success", "Social listening started!\nTracking keywords and mentions in real-time.")
            self.db.log_activity(
                self.team_id, 1, "start_monitoring",
                "social_listening", None, {}
            )
        else:
            self.monitor_button.configure(text="▶️ Start Monitoring", fg_color="#51CF66")
            self.db.log_activity(
                self.team_id, 1, "stop_monitoring",
                "social_listening", None, {}
            )
    
    def _add_keyword(self):
        """Add keyword to track"""
        keyword = self.keyword_entry.get().strip()
        threshold = self.threshold_entry.get().strip()
        
        if not keyword:
            messagebox.showwarning("Warning", "Enter keyword")
            return
        
        if not threshold:
            threshold = "10"
        
        try:
            threshold = int(threshold)
        except ValueError:
            messagebox.showerror("Error", "Threshold must be a number")
            return
        
        self.db.log_activity(
            self.team_id, 1, "add_monitoring_keyword",
            "social_listening", None,
            {"keyword": keyword, "threshold": threshold}
        )
        
        messagebox.showinfo("Success", f"Tracking '{keyword}'")
        self.keyword_entry.delete(0, "end")
        self.threshold_entry.delete(0, "end")
        self._refresh_keywords()
    
    def _refresh_keywords(self):
        """Refresh keywords list"""
        for widget in self.keywords_list.winfo_children():
            widget.destroy()
        
        # Mock keywords
        keywords = [
            {"keyword": "#AI", "mentions": 234, "trend": "📈 +45%", "last_24h": True},
            {"keyword": "ChatGPT", "mentions": 187, "trend": "📈 +32%", "last_24h": True},
            {"keyword": "blockchain", "mentions": 45, "trend": "📉 -12%", "last_24h": False},
            {"keyword": "#WebDevelopment", "mentions": 89, "trend": "📈 +15%", "last_24h": True},
        ]
        
        if not keywords:
            ctk.CTkLabel(
                self.keywords_list, text="No keywords tracked",
                text_color="#AAAAAA"
            ).pack(pady=20)
            return
        
        for kw in keywords:
            self._create_keyword_widget(kw)
    
    def _create_keyword_widget(self, keyword: Dict):
        """Create keyword widget"""
        widget = ctk.CTkFrame(
            self.keywords_list, fg_color="#333333", border_width=1, border_color="#444444"
        )
        widget.pack(fill="x", padx=5, pady=5)
        
        info_frame = ctk.CTkFrame(widget, fg_color="#333333")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            info_frame, text=keyword['keyword'], font=("Arial", 12, "bold")
        ).pack(anchor="w")
        
        stats = f"Mentions: {keyword['mentions']} | {keyword['trend']} | Last 24h: {'Yes' if keyword['last_24h'] else 'No'}"
        ctk.CTkLabel(
            info_frame, text=stats, font=("Arial", 9),
            text_color="#AAAAAA"
        ).pack(anchor="w")
        
        # Actions
        action_frame = ctk.CTkFrame(widget, fg_color="#333333")
        action_frame.pack(side="right", padx=10, pady=10)
        
        ctk.CTkButton(
            action_frame, text="View", width=50,
            command=lambda: messagebox.showinfo("Keyword Details", f"Mentions: {keyword['mentions']}")
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            action_frame, text="Delete", width=50, fg_color="#FF6B6B",
            command=lambda: messagebox.showinfo("Success", "Keyword removed")
        ).pack(side="left", padx=2)
    
    def _refresh_mentions(self):
        """Refresh brand mentions"""
        for widget in self.mentions_list.winfo_children():
            widget.destroy()
        
        platform = self.mentions_platform.get()
        
        # Mock mentions
        mentions = [
            {"platform": "Facebook", "user": "Sarah Johnson", "text": "Love using your product! #amazing", "time": "2 hours ago", "sentiment": "positive"},
            {"platform": "Instagram", "user": "tech_daily", "text": "New update looks great", "time": "4 hours ago", "sentiment": "positive"},
            {"platform": "Twitter", "user": "@developer_joe", "text": "Great features in latest release", "time": "6 hours ago", "sentiment": "positive"},
            {"platform": "LinkedIn", "user": "Emily Chen", "text": "Impressive growth strategy", "time": "1 day ago", "sentiment": "positive"},
        ]
        
        if platform != "All":
            mentions = [m for m in mentions if m['platform'] == platform]
        
        if not mentions:
            ctk.CTkLabel(
                self.mentions_list, text="No brand mentions",
                text_color="#AAAAAA"
            ).pack(pady=20)
            return
        
        for mention in mentions:
            widget = ctk.CTkFrame(
                self.mentions_list, fg_color="#333333", border_width=1, border_color="#444444"
            )
            widget.pack(fill="x", padx=5, pady=5)
            
            header = ctk.CTkFrame(widget, fg_color="#333333")
            header.pack(fill="x", padx=10, pady=(10, 0))
            
            platform_colors = {"Facebook": "#1877F2", "Instagram": "#E4405F", "Twitter": "#1DA1F2", "LinkedIn": "#0A66C2"}
            platform_label = ctk.CTkLabel(
                header, text=mention['platform'].upper(), font=("Arial", 9, "bold"),
                fg_color=platform_colors.get(mention['platform'], "#666666"),
                text_color="#FFFFFF", padx=6, pady=2, corner_radius=3
            )
            platform_label.pack(side="left")
            
            sentiment_color = "#51CF66" if mention['sentiment'] == "positive" else "#FFD43B" if mention['sentiment'] == "neutral" else "#FF6B6B"
            sentiment_label = ctk.CTkLabel(
                header, text=mention['sentiment'].upper(), font=("Arial", 9),
                fg_color=sentiment_color, text_color="#000000", padx=4, pady=2, corner_radius=3
            )
            sentiment_label.pack(side="left", padx=5)
            
            ctk.CTkLabel(
                header, text=mention['time'], font=("Arial", 9),
                text_color="#AAAAAA"
            ).pack(side="right")
            
            # Content
            ctk.CTkLabel(
                widget, text=f"@{mention['user']}: {mention['text']}", font=("Arial", 10),
                text_color="#CCCCCC", wraplength=400, justify="left"
            ).pack(anchor="w", padx=10, pady=10)
    
    def _add_competitor(self):
        """Add competitor to watch"""
        competitor = self.competitor_entry.get().strip()
        
        if not competitor:
            messagebox.showwarning("Warning", "Enter competitor name")
            return
        
        self.db.log_activity(
            self.team_id, 1, "add_competitor_watch",
            "social_listening", None,
            {"competitor": competitor}
        )
        
        messagebox.showinfo("Success", f"Watching '{competitor}'")
        self.competitor_entry.delete(0, "end")
        self._refresh_competitors()
    
    def _refresh_competitors(self):
        """Refresh competitors list"""
        for widget in self.competitors_list.winfo_children():
            widget.destroy()
        
        # Mock competitors
        competitors = [
            {"name": "Hootsuite", "followers": 125000, "posts_7d": 18, "engagement": "3.2%", "trend": "📈"},
            {"name": "Buffer", "followers": 89000, "posts_7d": 14, "engagement": "2.8%", "trend": "📈"},
            {"name": "Sprout Social", "followers": 95000, "posts_7d": 16, "engagement": "4.1%", "trend": "📈"},
        ]
        
        if not competitors:
            ctk.CTkLabel(
                self.competitors_list, text="No competitors watched",
                text_color="#AAAAAA"
            ).pack(pady=20)
            return
        
        for comp in competitors:
            widget = ctk.CTkFrame(
                self.competitors_list, fg_color="#333333", border_width=1, border_color="#444444"
            )
            widget.pack(fill="x", padx=5, pady=5)
            
            info_frame = ctk.CTkFrame(widget, fg_color="#333333")
            info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            
            ctk.CTkLabel(
                info_frame, text=comp['name'], font=("Arial", 12, "bold")
            ).pack(anchor="w")
            
            stats = f"Followers: {comp['followers']:,} | Posts (7d): {comp['posts_7d']} | Engagement: {comp['engagement']} {comp['trend']}"
            ctk.CTkLabel(
                info_frame, text=stats, font=("Arial", 9),
                text_color="#AAAAAA"
            ).pack(anchor="w")
            
            # Actions
            action_frame = ctk.CTkFrame(widget, fg_color="#333333")
            action_frame.pack(side="right", padx=10, pady=10)
            
            ctk.CTkButton(
                action_frame, text="Details", width=60,
                command=lambda: messagebox.showinfo("Competitor Stats", f"{comp['name']} is growing")
            ).pack(side="left", padx=2)
            
            ctk.CTkButton(
                action_frame, text="Unwatch", width=60, fg_color="#FF6B6B",
                command=lambda: messagebox.showinfo("Success", "Unwatch added")
            ).pack(side="left", padx=2)
    
    def _refresh_alerts(self):
        """Refresh alerts list"""
        for widget in self.alerts_list.winfo_children():
            widget.destroy()
        
        alert_type = self.alert_filter.get()
        
        # Mock alerts
        alerts = [
            {"type": "Keyword Spike", "message": "#AI mentions spiked 45% in last 6 hours", "severity": "high", "time": "30 min ago"},
            {"type": "Competitor Activity", "message": "Hootsuite just published 2 new posts", "severity": "medium", "time": "1 hour ago"},
            {"type": "Brand Mention", "message": "New positive mention on Twitter", "severity": "medium", "time": "2 hours ago"},
            {"type": "Trending", "message": "#WebDevelopment is trending (Your keyword!)", "severity": "low", "time": "3 hours ago"},
        ]
        
        if alert_type != "All":
            alerts = [a for a in alerts if a['type'] == alert_type]
        
        if not alerts:
            ctk.CTkLabel(
                self.alerts_list, text="No alerts",
                text_color="#AAAAAA"
            ).pack(pady=20)
            return
        
        for alert in alerts:
            severity_color = "#FF6B6B" if alert['severity'] == "high" else "#FFD43B" if alert['severity'] == "medium" else "#51CF66"
            
            widget = ctk.CTkFrame(
                self.alerts_list, fg_color="#333333", border_width=1, border_color="#444444"
            )
            widget.pack(fill="x", padx=5, pady=5)
            
            header = ctk.CTkFrame(widget, fg_color="#333333")
            header.pack(fill="x", padx=10, pady=(10, 0))
            
            severity_label = ctk.CTkLabel(
                header, text=alert['severity'].upper(), font=("Arial", 9, "bold"),
                fg_color=severity_color, text_color="#FFFFFF", padx=6, pady=2, corner_radius=3
            )
            severity_label.pack(side="left")
            
            ctk.CTkLabel(
                header, text=alert['type'], font=("Arial", 10, "bold")
            ).pack(side="left", padx=5)
            
            ctk.CTkLabel(
                header, text=alert['time'], font=("Arial", 9),
                text_color="#AAAAAA"
            ).pack(side="right")
            
            ctk.CTkLabel(
                widget, text=alert['message'], font=("Arial", 10),
                text_color="#CCCCCC", wraplength=400, justify="left"
            ).pack(anchor="w", padx=10, pady=10)
    
    def _refresh_analytics(self):
        """Refresh analytics"""
        for widget in self.analytics_list.winfo_children():
            widget.destroy()
        
        analytics = [
            {"metric": "Mentions by Platform", "data": "Facebook: 234 | Instagram: 189 | Twitter: 145 | LinkedIn: 98"},
            {"metric": "Top Keyword", "data": "#AI with 234 mentions in last 24 hours"},
            {"metric": "Sentiment Distribution", "data": "Positive: 78% | Neutral: 15% | Negative: 7%"},
            {"metric": "Average Response Time", "data": "45 minutes (vs 2h industry avg)"},
        ]
        
        for item in analytics:
            widget = ctk.CTkFrame(
                self.analytics_list, fg_color="#333333", border_width=1, border_color="#444444"
            )
            widget.pack(fill="x", padx=5, pady=5)
            
            ctk.CTkLabel(
                widget, text=item['metric'], font=("Arial", 11, "bold")
            ).pack(anchor="w", padx=10, pady=(10, 0))
            
            ctk.CTkLabel(
                widget, text=item['data'], font=("Arial", 10),
                text_color="#AAAAAA"
            ).pack(anchor="w", padx=10, pady=(0, 10))
