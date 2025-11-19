"""
First Comments Module for FYI Social Media Management Platform
Auto-post branded first comments and boost post engagement
"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from typing import List, Dict
from database_manager import get_db_manager
from logger_config import get_logger

logger = get_logger(__name__)

class FirstCommentsFrame(ctk.CTkFrame):
    """Automated first comments to boost engagement and brand presence"""
    
    def __init__(self, parent, team_id: int, **kwargs):
        super().__init__(parent, **kwargs)
        self.team_id = team_id
        self.db = get_db_manager()
        self.selected_template = None
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """Create first comments UI"""
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="First Comments Strategy", font=("Arial", 18, "bold")).pack(side="left")
        
        ctk.CTkButton(
            header_frame, text="➕ New Template", width=120,
            command=self._create_template
        ).pack(side="right", padx=5)
        
        # Main tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tabview.add("Templates")
        self.tabview.add("Scheduled Comments")
        self.tabview.add("Analytics")
        
        # ===== TEMPLATES TAB =====
        templates_tab = self.tabview.tab("Templates")
        
        # Filter frame
        filter_frame = ctk.CTkFrame(templates_tab)
        filter_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(filter_frame, text="Filter by platform:", font=("Arial", 10)).pack(side="left", padx=5)
        
        self.platform_filter = ctk.CTkComboBox(
            filter_frame, values=["All", "Facebook", "Instagram", "Twitter", "LinkedIn"],
            state="readonly", width=120
        )
        self.platform_filter.set("All")
        self.platform_filter.pack(side="left", padx=5)
        self.platform_filter.configure(command=self.refresh)
        
        # Templates list
        self.templates_list = ctk.CTkScrollableFrame(templates_tab, fg_color="#1a1a1a")
        self.templates_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ===== SCHEDULED COMMENTS TAB =====
        scheduled_tab = self.tabview.tab("Scheduled Comments")
        
        self.scheduled_list = ctk.CTkScrollableFrame(scheduled_tab, fg_color="#1a1a1a")
        self.scheduled_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ===== ANALYTICS TAB =====
        analytics_tab = self.tabview.tab("Analytics")
        
        # Metrics
        metrics_frame = ctk.CTkFrame(analytics_tab)
        metrics_frame.pack(fill="x", padx=10, pady=10)
        
        self.metric_comments = self._create_metric_card(metrics_frame, "Total Comments", "0")
        self.metric_comments.pack(side="left", padx=5, fill="both", expand=True)
        
        self.metric_engagement = self._create_metric_card(metrics_frame, "Engagement Rate", "0%")
        self.metric_engagement.pack(side="left", padx=5, fill="both", expand=True)
        
        self.metric_reach = self._create_metric_card(metrics_frame, "Additional Reach", "0")
        self.metric_reach.pack(side="left", padx=5, fill="both", expand=True)
        
        # Analytics table
        self.analytics_list = ctk.CTkScrollableFrame(analytics_tab, fg_color="#1a1a1a")
        self.analytics_list.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _create_metric_card(self, parent, label: str, value: str):
        """Create metric card widget"""
        card = ctk.CTkFrame(parent, fg_color="#333333", border_width=1, border_color="#444444")
        
        ctk.CTkLabel(card, text=label, font=("Arial", 10), text_color="#AAAAAA").pack(pady=(10, 5))
        ctk.CTkLabel(card, text=value, font=("Arial", 18, "bold")).pack(pady=(0, 10))
        
        return card
    
    def refresh(self):
        """Refresh first comments data"""
        self._refresh_templates()
        self._refresh_scheduled()
        self._refresh_analytics()
    
    def _refresh_templates(self):
        """Display comment templates"""
        for widget in self.templates_list.winfo_children():
            widget.destroy()
        
        # Mock templates
        templates = [
            {"id": 1, "platform": "Facebook", "text": "Great content! 🎉 Check out our page for more.", "used": 15},
            {"id": 2, "platform": "Instagram", "text": "Love this! 💯 Follow us for more updates.", "used": 23},
            {"id": 3, "platform": "Twitter", "text": "This is awesome! Thanks for sharing. 🚀", "used": 8},
            {"id": 4, "platform": "LinkedIn", "text": "Excellent post! Great insights. 👍", "used": 12},
        ]
        
        platform_filter = self.platform_filter.get()
        if platform_filter != "All":
            templates = [t for t in templates if t['platform'] == platform_filter]
        
        if not templates:
            ctk.CTkLabel(
                self.templates_list, text="No templates",
                text_color="#AAAAAA"
            ).pack(pady=20)
            return
        
        for template in templates:
            self._create_template_widget(template)
    
    def _create_template_widget(self, template: Dict):
        """Create template widget"""
        widget = ctk.CTkFrame(
            self.templates_list, fg_color="#333333", border_width=1, border_color="#444444"
        )
        widget.pack(fill="x", padx=5, pady=5)
        
        # Platform badge
        platform_colors = {
            "Facebook": "#1877F2",
            "Instagram": "#E4405F",
            "Twitter": "#1DA1F2",
            "LinkedIn": "#0A66C2"
        }
        
        header = ctk.CTkFrame(widget, fg_color="#333333")
        header.pack(fill="x", padx=10, pady=(10, 0))
        
        platform_label = ctk.CTkLabel(
            header, text=template['platform'].upper(), font=("Arial", 10, "bold"),
            fg_color=platform_colors.get(template['platform'], "#666666"),
            text_color="#FFFFFF", padx=8, pady=4, corner_radius=3
        )
        platform_label.pack(side="left")
        
        usage_label = ctk.CTkLabel(
            header, text=f"Used {template['used']} times", font=("Arial", 9),
            text_color="#AAAAAA"
        )
        usage_label.pack(side="right")
        
        # Template text
        text_label = ctk.CTkLabel(
            widget, text=template['text'], font=("Arial", 10),
            wraplength=400, justify="left", text_color="#CCCCCC"
        )
        text_label.pack(anchor="w", padx=10, pady=10)
        
        # Actions
        action_frame = ctk.CTkFrame(widget, fg_color="#333333")
        action_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        ctk.CTkButton(
            action_frame, text="Edit", width=60,
            command=lambda: self._edit_template(template)
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            action_frame, text="Delete", width=60, fg_color="#FF6B6B",
            command=lambda: self._delete_template(template)
        ).pack(side="left", padx=2)
        
        ctk.CTkButton(
            action_frame, text="Test", width=60, fg_color="#51CF66",
            command=lambda: self._test_template(template)
        ).pack(side="left", padx=2)
    
    def _create_template(self):
        """Create new comment template"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("New Comment Template")
        dialog.geometry("500x400")
        
        # Platform selection
        ctk.CTkLabel(dialog, text="Platform:", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(15, 0))
        platform_combo = ctk.CTkComboBox(
            dialog, values=["Facebook", "Instagram", "Twitter", "LinkedIn"],
            state="readonly"
        )
        platform_combo.set("Facebook")
        platform_combo.pack(fill="x", padx=15, pady=5)
        
        # Comment text
        ctk.CTkLabel(dialog, text="Comment Text (max 500 chars):", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(10, 0))
        text_box = ctk.CTkTextbox(dialog, height=150)
        text_box.pack(fill="both", expand=True, padx=15, pady=5)
        
        # Options
        options_frame = ctk.CTkFrame(dialog)
        options_frame.pack(fill="x", padx=15, pady=10)
        
        auto_post_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            options_frame, text="Auto-post first comment on new posts",
            variable=auto_post_var
        ).pack(anchor="w", pady=5)
        
        delay_var = ctk.StringVar(value="5")
        ctk.CTkLabel(options_frame, text="Delay before posting (seconds):", font=("Arial", 10)).pack(anchor="w", pady=(10, 0))
        ctk.CTkEntry(options_frame, textvariable=delay_var, width=100).pack(anchor="w", pady=5)
        
        def save_template():
            text = text_box.get("1.0", "end").strip()
            if not text:
                messagebox.showwarning("Warning", "Enter comment text")
                return
            
            platform = platform_combo.get()
            delay = delay_var.get()
            
            self.db.log_activity(
                self.team_id, 1, "create_first_comment_template",
                "first_comments", None,
                {
                    "platform": platform,
                    "text": text,
                    "auto_post": auto_post_var.get(),
                    "delay_seconds": delay
                }
            )
            
            messagebox.showinfo("Success", f"Template created for {platform}")
            dialog.destroy()
            self._refresh_templates()
        
        ctk.CTkButton(dialog, text="Save Template", command=save_template).pack(pady=10)
    
    def _edit_template(self, template: Dict):
        """Edit comment template"""
        dialog = ctk.CTkToplevel(self)
        dialog.title(f"Edit {template['platform']} Template")
        dialog.geometry("500x300")
        
        ctk.CTkLabel(dialog, text="Comment Text:", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(15, 0))
        text_box = ctk.CTkTextbox(dialog, height=150)
        text_box.insert("1.0", template['text'])
        text_box.pack(fill="both", expand=True, padx=15, pady=5)
        
        def save_changes():
            text = text_box.get("1.0", "end").strip()
            if not text:
                messagebox.showwarning("Warning", "Enter comment text")
                return
            
            self.db.log_activity(
                self.team_id, 1, "edit_first_comment_template",
                "first_comments", template['id'],
                {"text": text}
            )
            
            messagebox.showinfo("Success", "Template updated")
            dialog.destroy()
            self._refresh_templates()
        
        ctk.CTkButton(dialog, text="Save", command=save_changes).pack(pady=10)
    
    def _delete_template(self, template: Dict):
        """Delete template"""
        if messagebox.askyesno("Confirm", f"Delete {template['platform']} template?"):
            self.db.log_activity(
                self.team_id, 1, "delete_first_comment_template",
                "first_comments", template['id'],
                {"platform": template['platform']}
            )
            messagebox.showinfo("Success", "Template deleted")
            self._refresh_templates()
    
    def _test_template(self, template: Dict):
        """Test comment template"""
        messagebox.showinfo("Preview", f"Comment:\n\n{template['text']}")
    
    def _refresh_scheduled(self):
        """Refresh scheduled comments"""
        for widget in self.scheduled_list.winfo_children():
            widget.destroy()
        
        # Mock scheduled
        scheduled = [
            {"id": 1, "post": "Product Launch Video", "platform": "Facebook", "comment": "Great content! 🎉", "scheduled_for": "2024-01-20 10:00 AM", "status": "pending"},
            {"id": 2, "post": "Monthly Update", "platform": "Instagram", "comment": "Love this! 💯", "scheduled_for": "2024-01-20 2:30 PM", "status": "pending"},
        ]
        
        if not scheduled:
            ctk.CTkLabel(
                self.scheduled_list, text="No scheduled comments",
                text_color="#AAAAAA"
            ).pack(pady=20)
            return
        
        for item in scheduled:
            widget = ctk.CTkFrame(
                self.scheduled_list, fg_color="#333333", border_width=1, border_color="#444444"
            )
            widget.pack(fill="x", padx=5, pady=5)
            
            ctk.CTkLabel(
                widget, text=f"{item['post']} • {item['platform']}", font=("Arial", 11, "bold")
            ).pack(anchor="w", padx=10, pady=(10, 0))
            
            ctk.CTkLabel(
                widget, text=item['comment'], font=("Arial", 10),
                text_color="#CCCCCC"
            ).pack(anchor="w", padx=10, pady=5)
            
            status_color = "#FFD43B" if item['status'] == "pending" else "#51CF66"
            ctk.CTkLabel(
                widget, text=f"{item['scheduled_for']} • {item['status'].upper()}",
                font=("Arial", 9), text_color="#AAAAAA", fg_color=status_color,
                padx=6, pady=3, corner_radius=3
            ).pack(anchor="w", padx=10, pady=(0, 10))
    
    def _refresh_analytics(self):
        """Refresh first comments analytics"""
        for widget in self.analytics_list.winfo_children():
            widget.destroy()
        
        analytics = [
            {"platform": "Facebook", "comments": 45, "engagement": "12.3%", "reach": 1250},
            {"platform": "Instagram", "comments": 67, "engagement": "18.5%", "reach": 2100},
            {"platform": "Twitter", "comments": 23, "engagement": "8.1%", "reach": 580},
            {"platform": "LinkedIn", "comments": 34, "engagement": "15.2%", "reach": 890},
        ]
        
        for item in analytics:
            widget = ctk.CTkFrame(
                self.analytics_list, fg_color="#333333", border_width=1, border_color="#444444"
            )
            widget.pack(fill="x", padx=5, pady=5)
            
            info_frame = ctk.CTkFrame(widget, fg_color="#333333")
            info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            
            ctk.CTkLabel(
                info_frame, text=item['platform'], font=("Arial", 12, "bold")
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                info_frame, text=f"Comments: {item['comments']} | Engagement: {item['engagement']} | Reach: {item['reach']:,}",
                font=("Arial", 10), text_color="#AAAAAA"
            ).pack(anchor="w")
