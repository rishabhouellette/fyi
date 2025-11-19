"""
Social Inbox Module for FYI Social Media Management Platform
Unified messaging interface for DMs, comments, and mentions
"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from typing import List, Dict
from database_manager import get_db_manager
from logger_config import get_logger

logger = get_logger(__name__)

# Platform colors
PLATFORM_COLORS = {
    "facebook": "#1877F2",
    "instagram": "#E4405F",
    "twitter": "#1DA1F2",
    "linkedin": "#0A66C2",
}

class SocialInboxFrame(ctk.CTkFrame):
    """Unified social inbox for messages, comments, and mentions"""
    
    def __init__(self, parent, team_id: int, **kwargs):
        super().__init__(parent, **kwargs)
        self.team_id = team_id
        self.db = get_db_manager()
        self.selected_message = None
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """Create inbox UI components"""
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Social Inbox", font=("Arial", 18, "bold")).pack(side="left")
        
        ctk.CTkButton(
            header_frame, text="🔄 Refresh", width=100,
            command=self.refresh
        ).pack(side="right", padx=5)
        
        # Filter buttons
        filter_frame = ctk.CTkFrame(self)
        filter_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            filter_frame, text="All", width=60,
            command=lambda: self._filter_messages(None)
        ).pack(side="left", padx=2)
        
        for platform in ["facebook", "instagram", "twitter", "linkedin"]:
            ctk.CTkButton(
                filter_frame, text=platform.capitalize(), width=80,
                fg_color=PLATFORM_COLORS.get(platform, "#666666"),
                command=lambda p=platform: self._filter_messages(p)
            ).pack(side="left", padx=2)
        
        # Messages list
        list_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.messages_frame = ctk.CTkScrollableFrame(list_frame)
        self.messages_frame.pack(fill="both", expand=True)
        
        # Message detail panel
        detail_frame = ctk.CTkFrame(self, fg_color="#2B2B2B")
        detail_frame.pack(fill="both", side="right", padx=10, pady=10)
        
        self.detail_label = ctk.CTkLabel(
            detail_frame, text="Select a message to view details",
            font=("Arial", 12), wraplength=300
        )
        self.detail_label.pack(padx=10, pady=10, fill="both", expand=True)
        
        # Reply section
        reply_frame = ctk.CTkFrame(self)
        reply_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(reply_frame, text="Reply:", font=("Arial", 12, "bold")).pack(anchor="w")
        
        self.reply_text = ctk.CTkTextbox(reply_frame, height=80)
        self.reply_text.pack(fill="both", padx=5, pady=5)
        
        ctk.CTkButton(
            reply_frame, text="Send Reply", fg_color="#51CF66",
            command=self._send_reply
        ).pack(side="left", padx=5, pady=5)
    
    def refresh(self):
        """Refresh inbox messages"""
        self._filter_messages(None)
    
    def _filter_messages(self, platform: str = None):
        """Filter and display messages"""
        for widget in self.messages_frame.winfo_children():
            widget.destroy()
        
        messages = self.db.get_inbox_messages(self.team_id, unread_only=False)
        
        if platform:
            messages = [m for m in messages if m['platform'] == platform]
        
        if not messages:
            ctk.CTkLabel(
                self.messages_frame, text="No messages",
                text_color="#AAAAAA"
            ).pack(pady=20)
            return
        
        for msg in messages:
            self._create_message_widget(msg)
    
    def _create_message_widget(self, message: Dict):
        """Create message widget"""
        msg_frame = ctk.CTkFrame(
            self.messages_frame, fg_color="#333333", border_width=1, border_color="#444444"
        )
        msg_frame.pack(fill="x", padx=5, pady=5)
        
        # Message header
        header = ctk.CTkFrame(msg_frame, fg_color="#333333")
        header.pack(fill="x", padx=10, pady=5)
        
        platform_color = PLATFORM_COLORS.get(message['platform'], "#666666")
        platform_label = ctk.CTkLabel(
            header, text=message['platform'].upper(), font=("Arial", 9, "bold"),
            fg_color=platform_color, text_color="#FFFFFF", padx=5, pady=2,
            corner_radius=3
        )
        platform_label.pack(side="left", padx=5)
        
        ctk.CTkLabel(
            header, text=message['from_user_name'], font=("Arial", 11, "bold")
        ).pack(side="left", padx=5)
        
        ctk.CTkLabel(
            header, text=message['received_at'][:10], font=("Arial", 9),
            text_color="#AAAAAA"
        ).pack(side="right", padx=5)
        
        # Message content
        content_label = ctk.CTkLabel(
            msg_frame, text=message['message_content'][:100], font=("Arial", 10),
            text_color="#CCCCCC", wraplength=300, justify="left"
        )
        content_label.pack(anchor="w", padx=10, pady=5)
        
        # Click to view details
        msg_frame.bind(
            "<Button-1>",
            lambda e: self._show_message_details(message)
        )
        for child in msg_frame.winfo_children():
            child.bind(
                "<Button-1>",
                lambda e: self._show_message_details(message)
            )
    
    def _show_message_details(self, message: Dict):
        """Show full message details"""
        self.selected_message = message
        
        details = f"From: {message['from_user_name']}\n"
        details += f"Platform: {message['platform']}\n"
        details += f"Type: {message['message_type']}\n"
        details += f"Received: {message['received_at']}\n\n"
        details += f"Message:\n{message['message_content']}"
        
        self.detail_label.configure(text=details)
        self.reply_text.delete("1.0", "end")
    
    def _send_reply(self):
        """Send reply to selected message"""
        if not self.selected_message:
            messagebox.showwarning("Warning", "Select a message first")
            return
        
        reply_text = self.reply_text.get("1.0", "end").strip()
        if not reply_text:
            messagebox.showwarning("Warning", "Reply cannot be empty")
            return
        
        try:
            # In real implementation, this would send via the platform's API
            self.db.log_activity(
                self.team_id, 1, "reply_message",
                "social_inbox", self.selected_message['id'],
                {"reply": reply_text, "platform": self.selected_message['platform']}
            )
            
            messagebox.showinfo("Success", "Reply sent!")
            self.reply_text.delete("1.0", "end")
            logger.info(f"Reply sent to {self.selected_message['from_user_name']}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send reply: {e}")
            logger.error(f"Reply error: {e}")
