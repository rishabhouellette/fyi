"""
Link Tracking Module for FYI Social Media Management Platform
Auto-shorten links, UTM parameters, and click analytics
"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta
from typing import List, Dict
import secrets
import string
from database_manager import get_db_manager
from logger_config import get_logger

logger = get_logger(__name__)

# Simple URL shortener (would use external service in production)
class LinkShortener:
    @staticmethod
    def generate_short_code(length=6):
        chars = string.ascii_letters + string.digits
        return ''.join(secrets.choice(chars) for _ in range(length))
    
    @staticmethod
    def shorten_url(original_url, custom_code=None):
        code = custom_code or LinkShortener.generate_short_code()
        return f"fyi.link/{code}", code


class LinkTrackingFrame(ctk.CTkFrame):
    """Link shortening and UTM tracking for analytics"""
    
    def __init__(self, parent, team_id: int, **kwargs):
        super().__init__(parent, **kwargs)
        self.team_id = team_id
        self.db = get_db_manager()
        self.shortener = LinkShortener()
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """Create link tracking UI"""
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Link Tracking & UTM Management", font=("Arial", 18, "bold")).pack(side="left")
        
        ctk.CTkButton(
            header_frame, text="🔄 Refresh", width=100,
            command=self.refresh
        ).pack(side="right", padx=5)
        
        # Main tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tabview.add("Shorten Link")
        self.tabview.add("Link List")
        self.tabview.add("Analytics")
        
        # ===== SHORTEN LINK TAB =====
        shorten_tab = self.tabview.tab("Shorten Link")
        
        # URL Input
        ctk.CTkLabel(shorten_tab, text="Original URL:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        
        self.url_entry = ctk.CTkEntry(shorten_tab, placeholder_text="https://example.com/page", height=40)
        self.url_entry.pack(fill="x", padx=10, pady=5)
        
        # UTM Parameters
        utmframe = ctk.CTkFrame(shorten_tab)
        utmframe.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(utmframe, text="UTM Parameters (Optional):", font=("Arial", 12, "bold")).pack(anchor="w")
        
        params_frame = ctk.CTkFrame(shorten_tab)
        params_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(params_frame, text="Source:", font=("Arial", 10)).pack(side="left", padx=5)
        self.utm_source = ctk.CTkComboBox(
            params_frame, values=["Facebook", "Instagram", "Twitter", "LinkedIn", "Email", "Other"],
            state="readonly", width=120
        )
        self.utm_source.set("Facebook")
        self.utm_source.pack(side="left", padx=5)
        
        ctk.CTkLabel(params_frame, text="Medium:", font=("Arial", 10)).pack(side="left", padx=5)
        self.utm_medium = ctk.CTkComboBox(
            params_frame, values=["Social", "Email", "CPC", "Direct", "Organic"],
            state="readonly", width=120
        )
        self.utm_medium.set("Social")
        self.utm_medium.pack(side="left", padx=5)
        
        campaign_frame = ctk.CTkFrame(shorten_tab)
        campaign_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(campaign_frame, text="Campaign:", font=("Arial", 10)).pack(side="left", padx=5)
        self.utm_campaign = ctk.CTkEntry(campaign_frame, placeholder_text="e.g., winter_sale", width=150)
        self.utm_campaign.pack(side="left", padx=5)
        
        ctk.CTkLabel(campaign_frame, text="Content:", font=("Arial", 10)).pack(side="left", padx=5)
        self.utm_content = ctk.CTkEntry(campaign_frame, placeholder_text="e.g., promo_banner", width=150)
        self.utm_content.pack(side="left", padx=5)
        
        # Custom code option
        custom_frame = ctk.CTkFrame(shorten_tab)
        custom_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(custom_frame, text="Custom Short Code (optional):", font=("Arial", 10)).pack(side="left", padx=5)
        self.custom_code = ctk.CTkEntry(custom_frame, placeholder_text="e.g., summer_sale", width=150)
        self.custom_code.pack(side="left", padx=5)
        
        # Generate button
        ctk.CTkButton(
            shorten_tab, text="🔗 Generate Short Link", height=40, fg_color="#51CF66",
            font=("Arial", 14, "bold"),
            command=self._generate_link
        ).pack(fill="x", padx=10, pady=10)
        
        # Result display
        self.result_frame = ctk.CTkFrame(shorten_tab, fg_color="#2B2B2B")
        self.result_frame.pack(fill="x", padx=10, pady=10)
        
        self.result_label = ctk.CTkLabel(
            self.result_frame, text="",
            font=("Arial", 12), wraplength=400
        )
        self.result_label.pack(padx=10, pady=10)
        
        # ===== LINK LIST TAB =====
        list_tab = self.tabview.tab("Link List")
        
        # Filter frame
        filter_frame = ctk.CTkFrame(list_tab)
        filter_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(filter_frame, text="Sort by:", font=("Arial", 10)).pack(side="left", padx=5)
        
        self.sort_combo = ctk.CTkComboBox(
            filter_frame, values=["Recent", "Most Clicks", "Least Clicks", "Active", "Expired"],
            state="readonly", width=120
        )
        self.sort_combo.set("Recent")
        self.sort_combo.pack(side="left", padx=5)
        self.sort_combo.configure(command=self._refresh_links)
        
        # Links list
        self.links_list = ctk.CTkScrollableFrame(list_tab, fg_color="#1a1a1a")
        self.links_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ===== ANALYTICS TAB =====
        analytics_tab = self.tabview.tab("Analytics")
        
        # Metrics
        metrics_frame = ctk.CTkFrame(analytics_tab)
        metrics_frame.pack(fill="x", padx=10, pady=10)
        
        self.metric_links = self._create_metric_card(metrics_frame, "Total Links", "0")
        self.metric_links.pack(side="left", padx=5, fill="both", expand=True)
        
        self.metric_clicks = self._create_metric_card(metrics_frame, "Total Clicks", "0")
        self.metric_clicks.pack(side="left", padx=5, fill="both", expand=True)
        
        self.metric_ctr = self._create_metric_card(metrics_frame, "Avg CTR", "0%")
        self.metric_ctr.pack(side="left", padx=5, fill="both", expand=True)
        
        # Performance table
        ctk.CTkLabel(analytics_tab, text="Top Performing Links:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.analytics_list = ctk.CTkScrollableFrame(analytics_tab, fg_color="#1a1a1a")
        self.analytics_list.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _create_metric_card(self, parent, label: str, value: str):
        """Create metric card"""
        card = ctk.CTkFrame(parent, fg_color="#333333", border_width=1, border_color="#444444")
        
        ctk.CTkLabel(card, text=label, font=("Arial", 10), text_color="#AAAAAA").pack(pady=(10, 5))
        ctk.CTkLabel(card, text=value, font=("Arial", 16, "bold")).pack(pady=(0, 10))
        
        return card
    
    def refresh(self):
        """Refresh link tracking data"""
        self._refresh_links()
        self._refresh_analytics()
    
    def _generate_link(self):
        """Generate shortened link with UTM parameters"""
        original_url = self.url_entry.get().strip()
        
        if not original_url:
            messagebox.showwarning("Warning", "Enter a URL")
            return
        
        if not original_url.startswith(("http://", "https://")):
            original_url = "https://" + original_url
        
        # Build UTM string
        utm_params = []
        if self.utm_source.get():
            utm_params.append(f"utm_source={self.utm_source.get().lower()}")
        if self.utm_medium.get():
            utm_params.append(f"utm_medium={self.utm_medium.get().lower()}")
        if self.utm_campaign.get():
            utm_params.append(f"utm_campaign={self.utm_campaign.get().lower()}")
        if self.utm_content.get():
            utm_params.append(f"utm_content={self.utm_content.get().lower()}")
        
        utm_string = "&".join(utm_params)
        final_url = f"{original_url}?{utm_string}" if utm_string else original_url
        
        # Generate short code
        short_code = self.custom_code.get().strip() or None
        short_url, code = self.shortener.shorten_url(final_url, short_code)
        
        # Log activity
        self.db.log_activity(
            self.team_id, 1, "create_short_link",
            "link_tracking", None,
            {
                "original_url": original_url,
                "short_url": short_url,
                "utm_source": self.utm_source.get(),
                "utm_medium": self.utm_medium.get(),
                "utm_campaign": self.utm_campaign.get(),
            }
        )
        
        # Display result
        self.result_label.configure(
            text=f"✅ Short Link: {short_url}\n\n🔗 Full URL: {final_url[:80]}...\n\n📋 Click to copy"
        )
        
        # Clear inputs
        self.url_entry.delete(0, "end")
        self.utm_campaign.delete(0, "end")
        self.utm_content.delete(0, "end")
        
        messagebox.showinfo("Success", f"Link shortened!\n\n{short_url}")
        self._refresh_links()
    
    def _refresh_links(self):
        """Refresh links list"""
        for widget in self.links_list.winfo_children():
            widget.destroy()
        
        sort_by = self.sort_combo.get()
        
        # Mock links
        links = [
            {"short": "fyi.link/summer", "original": "example.com/promo?utm_source=facebook", "clicks": 245, "created": "2 days ago", "status": "active"},
            {"short": "fyi.link/newyear", "original": "example.com/deals?utm_source=instagram", "clicks": 189, "created": "5 days ago", "status": "active"},
            {"short": "fyi.link/flash", "original": "example.com/flash-sale?utm_source=twitter", "clicks": 56, "created": "1 day ago", "status": "active"},
            {"short": "fyi.link/holiday", "original": "example.com/holiday?utm_source=email", "clicks": 423, "created": "1 week ago", "status": "expired"},
        ]
        
        # Sort
        if sort_by == "Most Clicks":
            links.sort(key=lambda x: x['clicks'], reverse=True)
        elif sort_by == "Least Clicks":
            links.sort(key=lambda x: x['clicks'])
        elif sort_by == "Active":
            links = [l for l in links if l['status'] == 'active']
        elif sort_by == "Expired":
            links = [l for l in links if l['status'] == 'expired']
        
        if not links:
            ctk.CTkLabel(
                self.links_list, text="No links",
                text_color="#AAAAAA"
            ).pack(pady=20)
            return
        
        for link in links:
            widget = ctk.CTkFrame(
                self.links_list, fg_color="#333333", border_width=1, border_color="#444444"
            )
            widget.pack(fill="x", padx=5, pady=5)
            
            info_frame = ctk.CTkFrame(widget, fg_color="#333333")
            info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            
            status_color = "#51CF66" if link['status'] == "active" else "#FF6B6B"
            ctk.CTkLabel(
                info_frame, text=link['short'], font=("Arial", 12, "bold"),
                text_color="#51CF66"
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                info_frame, text=f"→ {link['original'][:60]}...", font=("Arial", 9),
                text_color="#AAAAAA"
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                info_frame, text=f"Clicks: {link['clicks']} | Created: {link['created']} | Status: {link['status'].upper()}",
                font=("Arial", 9), text_color="#CCCCCC", fg_color=status_color, padx=6, pady=2, corner_radius=3
            ).pack(anchor="w", pady=(5, 0))
            
            # Actions
            action_frame = ctk.CTkFrame(widget, fg_color="#333333")
            action_frame.pack(side="right", padx=10, pady=10)
            
            ctk.CTkButton(
                action_frame, text="Copy", width=50,
                command=lambda: messagebox.showinfo("Copied", link['short'])
            ).pack(side="left", padx=2)
            
            ctk.CTkButton(
                action_frame, text="Stats", width=50,
                command=lambda: messagebox.showinfo("Link Stats", f"Clicks: {link['clicks']}\nStatus: {link['status']}")
            ).pack(side="left", padx=2)
            
            ctk.CTkButton(
                action_frame, text="Delete", width=50, fg_color="#FF6B6B",
                command=lambda: messagebox.showinfo("Deleted", "Link removed")
            ).pack(side="left", padx=2)
    
    def _refresh_analytics(self):
        """Refresh analytics"""
        for widget in self.analytics_list.winfo_children():
            widget.destroy()
        
        # Mock analytics
        analytics = [
            {"link": "fyi.link/holiday", "clicks": 423, "ctr": "8.5%", "conversions": 34, "revenue": "$1,020"},
            {"link": "fyi.link/summer", "clicks": 245, "ctr": "4.9%", "conversions": 18, "revenue": "$540"},
            {"link": "fyi.link/newyear", "clicks": 189, "ctr": "3.8%", "conversions": 12, "revenue": "$360"},
        ]
        
        for item in analytics:
            widget = ctk.CTkFrame(
                self.analytics_list, fg_color="#333333", border_width=1, border_color="#444444"
            )
            widget.pack(fill="x", padx=5, pady=5)
            
            ctk.CTkLabel(
                widget, text=item['link'], font=("Arial", 11, "bold"),
                text_color="#51CF66"
            ).pack(anchor="w", padx=10, pady=(10, 0))
            
            stats = f"Clicks: {item['clicks']} | CTR: {item['ctr']} | Conversions: {item['conversions']} | Revenue: {item['revenue']}"
            ctk.CTkLabel(
                widget, text=stats, font=("Arial", 10),
                text_color="#AAAAAA"
            ).pack(anchor="w", padx=10, pady=(0, 10))
