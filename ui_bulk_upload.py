"""
Bulk Upload Module for FYI Social Media Management Platform
CSV import and folder upload for mass content scheduling
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
import csv
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict
from database_manager import get_db_manager, Post
from logger_config import get_logger

logger = get_logger(__name__)

class BulkUploadFrame(ctk.CTkFrame):
    """Bulk upload interface for CSV and folder imports"""
    
    def __init__(self, parent, team_id: int, account_id: int = None, **kwargs):
        super().__init__(parent, **kwargs)
        self.team_id = team_id
        self.account_id = account_id
        self.db = get_db_manager()
        self.uploaded_posts = []
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create bulk upload UI components"""
        # Title
        title_label = ctk.CTkLabel(self, text="Bulk Upload", font=("Arial", 18, "bold"))
        title_label.pack(pady=20)
        
        # Upload options
        options_frame = ctk.CTkFrame(self)
        options_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(
            options_frame, text="📥 Upload CSV", width=150,
            command=self._upload_csv
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            options_frame, text="📁 Upload Folder", width=150,
            command=self._upload_folder
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            options_frame, text="📋 Template", width=150,
            command=self._download_template
        ).pack(side="left", padx=10)
        
        # CSV format info
        info_frame = ctk.CTkFrame(self, fg_color="#2B2B2B")
        info_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(
            info_frame,
            text="CSV Format: platform,title,content,media_path,scheduled_time\n"
                 "Example: facebook,My Post,Check this out!,/path/to/image.jpg,2025-11-17 14:00:00",
            font=("Arial", 10),
            text_color="#AAAAAA",
            justify="left"
        ).pack(anchor="w", padx=10, pady=10)
        
        # Preview table
        preview_label = ctk.CTkLabel(self, text="Preview", font=("Arial", 14, "bold"))
        preview_label.pack(anchor="w", padx=20, pady=(20, 10))
        
        self.preview_frame = ctk.CTkFrame(self, fg_color="#1a1a1a")
        self.preview_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Action buttons
        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkButton(
            action_frame, text="✓ Schedule All", fg_color="#51CF66",
            command=self._schedule_all
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            action_frame, text="✕ Clear", fg_color="#FF6B6B",
            command=self._clear_preview
        ).pack(side="left", padx=10)
    
    def _upload_csv(self):
        """Upload and parse CSV file"""
        file_path = filedialog.askopenfilename(
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Select CSV file"
        )
        
        if not file_path:
            return
        
        try:
            posts = self._parse_csv(file_path)
            self.uploaded_posts = posts
            self._show_preview(posts)
            messagebox.showinfo("Success", f"Loaded {len(posts)} posts from CSV")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse CSV: {e}")
            logger.error(f"CSV parsing error: {e}")
    
    def _upload_folder(self):
        """Upload all media files from folder"""
        folder_path = filedialog.askdirectory(title="Select folder with media files")
        
        if not folder_path:
            return
        
        try:
            posts = self._scan_folder(folder_path)
            self.uploaded_posts = posts
            self._show_preview(posts)
            messagebox.showinfo("Success", f"Found {len(posts)} media files")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to scan folder: {e}")
            logger.error(f"Folder scan error: {e}")
    
    def _parse_csv(self, file_path: str) -> List[Post]:
        """Parse CSV file into posts"""
        posts = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                post = Post(
                    team_id=self.team_id,
                    account_id=self.account_id,
                    platform=row.get('platform', 'facebook'),
                    title=row.get('title', ''),
                    content=row.get('content', ''),
                    media_paths=[row.get('media_path')] if row.get('media_path') else [],
                    scheduled_time=row.get('scheduled_time'),
                    status='draft'
                )
                posts.append(post)
        
        return posts
    
    def _scan_folder(self, folder_path: str) -> List[Post]:
        """Scan folder for media files and create posts"""
        posts = []
        media_extensions = {'.mp4', '.avi', '.mov', '.jpg', '.png', '.gif', '.webp'}
        
        for file_path in Path(folder_path).iterdir():
            if file_path.suffix.lower() in media_extensions:
                # Create post with auto-scheduled time (evenly spaced)
                scheduled_time = datetime.now() + timedelta(hours=len(posts))
                
                post = Post(
                    team_id=self.team_id,
                    account_id=self.account_id,
                    platform='facebook',
                    title=file_path.stem,
                    content=f"Check out: {file_path.stem}",
                    media_paths=[str(file_path)],
                    scheduled_time=scheduled_time.isoformat(),
                    status='draft'
                )
                posts.append(post)
        
        return posts
    
    def _show_preview(self, posts: List[Post]):
        """Show preview of posts to be uploaded"""
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
        
        if not posts:
            ctk.CTkLabel(self.preview_frame, text="No posts to preview").pack()
            return
        
        # Table header
        headers = ["Platform", "Title", "Scheduled Time", "Status"]
        for col, header in enumerate(headers):
            label = ctk.CTkLabel(
                self.preview_frame, text=header, font=("Arial", 10, "bold"),
                text_color="#CCCCCC"
            )
            label.grid(row=0, column=col, sticky="w", padx=5, pady=5)
        
        # Table rows
        for row, post in enumerate(posts[:20], 1):  # Show first 20
            data = [
                post.platform,
                post.title[:30],
                post.scheduled_time[:16] if post.scheduled_time else "Now",
                post.status
            ]
            
            for col, value in enumerate(data):
                label = ctk.CTkLabel(
                    self.preview_frame, text=value, font=("Arial", 9),
                    text_color="#AAAAAA"
                )
                label.grid(row=row, column=col, sticky="w", padx=5, pady=3)
    
    def _schedule_all(self):
        """Schedule all posts"""
        if not self.uploaded_posts:
            messagebox.showwarning("Warning", "No posts to schedule")
            return
        
        try:
            for post in self.uploaded_posts:
                post.created_by_user_id = 1  # Default user (will be improved with auth)
                self.db.create_post(post)
            
            messagebox.showinfo("Success", f"Scheduled {len(self.uploaded_posts)} posts")
            self._clear_preview()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to schedule posts: {e}")
            logger.error(f"Scheduling error: {e}")
    
    def _clear_preview(self):
        """Clear preview"""
        self.uploaded_posts = []
        for widget in self.preview_frame.winfo_children():
            widget.destroy()
    
    def _download_template(self):
        """Download CSV template"""
        save_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="bulk_upload_template.csv"
        )
        
        if not save_path:
            return
        
        try:
            with open(save_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['platform', 'title', 'content', 'media_path', 'scheduled_time'])
                writer.writerow(['facebook', 'My First Post', 'Check this out!', '/path/to/image.jpg', '2025-11-17 14:00:00'])
                writer.writerow(['instagram', 'Another Post', 'Amazing content', '/path/to/video.mp4', '2025-11-17 15:00:00'])
            
            messagebox.showinfo("Success", f"Template saved to {save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save template: {e}")
