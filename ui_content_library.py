"""
Content Library Module for FYI Social Media Management Platform
Centralized media storage, organization, and reusability
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from datetime import datetime
from typing import List, Dict
import os
from PIL import Image, ImageTk
from database_manager import get_db_manager
from logger_config import get_logger

logger = get_logger(__name__)

class ContentLibraryFrame(ctk.CTkFrame):
    """Centralized content library for media organization and reuse"""
    
    def __init__(self, parent, team_id: int, **kwargs):
        super().__init__(parent, **kwargs)
        self.team_id = team_id
        self.db = get_db_manager()
        self.selected_media = None
        self.library_path = Path("data/library")
        self.library_path.mkdir(parents=True, exist_ok=True)
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """Create library UI components"""
        # Header with buttons
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Content Library", font=("Arial", 18, "bold")).pack(side="left")
        
        button_frame = ctk.CTkFrame(header_frame)
        button_frame.pack(side="right")
        
        ctk.CTkButton(
            button_frame, text="📁 Import Media", width=120,
            command=self._import_media
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame, text="🔄 Refresh", width=100,
            command=self.refresh
        ).pack(side="left", padx=5)
        
        # Search and filter
        search_frame = ctk.CTkFrame(self)
        search_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(search_frame, text="Search:", font=("Arial", 10)).pack(side="left", padx=5)
        
        self.search_entry = ctk.CTkEntry(search_frame, width=200, placeholder_text="Search by tag or name...")
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", lambda e: self._search_library())
        
        # Filter by type
        ctk.CTkLabel(search_frame, text="Type:", font=("Arial", 10)).pack(side="left", padx=5)
        
        self.type_filter = ctk.CTkComboBox(
            search_frame, values=["All", "Image", "Video", "Document"],
            state="readonly", width=100
        )
        self.type_filter.set("All")
        self.type_filter.pack(side="left", padx=5)
        self.type_filter.configure(command=lambda: self._search_library())
        
        # Main content area
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Library grid (scrollable)
        self.library_scroll = ctk.CTkScrollableFrame(main_frame, fg_color="#1a1a1a")
        self.library_scroll.pack(fill="both", expand=True, side="left")
        
        # Preview panel
        preview_frame = ctk.CTkFrame(main_frame, fg_color="#2B2B2B", width=250)
        preview_frame.pack(fill="both", side="right", padx=10)
        preview_frame.pack_propagate(False)
        
        self.preview_label = ctk.CTkLabel(
            preview_frame, text="Select media to preview",
            font=("Arial", 12), text_color="#AAAAAA"
        )
        self.preview_label.pack(padx=10, pady=10)
        
        # Preview image
        self.preview_image_label = ctk.CTkLabel(preview_frame, text="")
        self.preview_image_label.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Preview details
        self.preview_details = ctk.CTkTextbox(preview_frame, height=100)
        self.preview_details.pack(fill="x", padx=10, pady=10)
        self.preview_details.configure(state="disabled")
        
        # Tags
        self.tags_entry = ctk.CTkEntry(
            preview_frame, placeholder_text="Add tags (comma separated)",
            height=35
        )
        self.tags_entry.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkButton(
            preview_frame, text="Save Tags", fg_color="#51CF66",
            command=self._save_tags
        ).pack(fill="x", padx=10, pady=5)
        
        # Delete button
        ctk.CTkButton(
            preview_frame, text="🗑️ Delete", fg_color="#FF6B6B",
            command=self._delete_media
        ).pack(fill="x", padx=10, pady=5)
    
    def _import_media(self):
        """Import media files to library"""
        files = filedialog.askopenfiles(
            title="Select media files",
            filetypes=[
                ("All Files", "*.jpg *.jpeg *.png *.gif *.mp4 *.mov *.avi *.pdf *.docx"),
                ("Images", "*.jpg *.jpeg *.png *.gif"),
                ("Videos", "*.mp4 *.mov *.avi"),
                ("Documents", "*.pdf *.docx"),
            ]
        )
        
        if not files:
            return
        
        for file in files:
            try:
                filename = Path(file.name).name
                dest_path = self.library_path / filename
                
                # Copy file to library
                import shutil
                shutil.copy(file.name, dest_path)
                
                # Store in database
                self.db.log_activity(
                    self.team_id, 1, "import_media",
                    "content_library", None,
                    {
                        "filename": filename,
                        "size": os.path.getsize(dest_path),
                        "type": filename.split('.')[-1].lower(),
                        "path": str(dest_path)
                    }
                )
                
                logger.info(f"Imported media: {filename}")
            except Exception as e:
                logger.error(f"Failed to import {file.name}: {e}")
        
        messagebox.showinfo("Success", f"Imported {len(files)} file(s)")
        self.refresh()
    
    def refresh(self):
        """Refresh library view"""
        for widget in self.library_scroll.winfo_children():
            widget.destroy()
        
        media_files = list(self.library_path.glob("*"))
        
        if not media_files:
            ctk.CTkLabel(
                self.library_scroll, text="No media in library. Click 'Import Media' to start.",
                text_color="#AAAAAA"
            ).pack(pady=20)
            return
        
        # Create grid of media items
        for i, media_file in enumerate(media_files):
            self._create_media_widget(media_file)
    
    def _create_media_widget(self, media_path: Path):
        """Create media item widget"""
        item_frame = ctk.CTkFrame(
            self.library_scroll, fg_color="#333333", height=100,
            border_width=1, border_color="#444444"
        )
        item_frame.pack(fill="x", padx=5, pady=5)
        item_frame.pack_propagate(False)
        
        # File info
        info_frame = ctk.CTkFrame(item_frame, fg_color="#333333")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            info_frame, text=media_path.name, font=("Arial", 11, "bold"),
            wraplength=200, justify="left"
        ).pack(anchor="w")
        
        file_size = os.path.getsize(media_path) / 1024  # KB
        ctk.CTkLabel(
            info_frame, text=f"Size: {file_size:.1f} KB", font=("Arial", 9),
            text_color="#AAAAAA"
        ).pack(anchor="w")
        
        # Select button
        ctk.CTkButton(
            item_frame, text="Preview", width=80,
            command=lambda: self._select_media(media_path)
        ).pack(side="right", padx=10)
    
    def _select_media(self, media_path: Path):
        """Select media for preview"""
        self.selected_media = media_path
        
        # Update preview label
        self.preview_label.configure(text=media_path.name)
        
        # Try to load image thumbnail
        try:
            if media_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
                img = Image.open(media_path)
                img.thumbnail((220, 200))
                photo = ImageTk.PhotoImage(img)
                self.preview_image_label.configure(image=photo, text="")
                self.preview_image_label.image = photo
            else:
                self.preview_image_label.configure(text=f"📄 {media_path.suffix.upper()}")
        except Exception as e:
            self.preview_image_label.configure(text="Preview not available")
            logger.error(f"Failed to load preview: {e}")
        
        # Update details
        self.preview_details.configure(state="normal")
        self.preview_details.delete("1.0", "end")
        
        file_size = os.path.getsize(media_path) / 1024  # KB
        created = datetime.fromtimestamp(os.path.getctime(media_path)).strftime("%Y-%m-%d %H:%M")
        
        details = f"File: {media_path.name}\n"
        details += f"Type: {media_path.suffix.upper()}\n"
        details += f"Size: {file_size:.1f} KB\n"
        details += f"Created: {created}"
        
        self.preview_details.insert("1.0", details)
        self.preview_details.configure(state="disabled")
    
    def _save_tags(self):
        """Save tags for selected media"""
        if not self.selected_media:
            messagebox.showwarning("Warning", "Select media first")
            return
        
        tags = self.tags_entry.get().strip()
        if not tags:
            return
        
        try:
            self.db.log_activity(
                self.team_id, 1, "add_tags",
                "content_library", None,
                {
                    "filename": self.selected_media.name,
                    "tags": tags
                }
            )
            messagebox.showinfo("Success", "Tags saved!")
            logger.info(f"Tags saved for {self.selected_media.name}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save tags: {e}")
    
    def _delete_media(self):
        """Delete selected media"""
        if not self.selected_media:
            messagebox.showwarning("Warning", "Select media first")
            return
        
        if messagebox.askyesno("Confirm", f"Delete {self.selected_media.name}?"):
            try:
                self.selected_media.unlink()
                self.db.log_activity(
                    self.team_id, 1, "delete_media",
                    "content_library", None,
                    {"filename": self.selected_media.name}
                )
                messagebox.showinfo("Success", "Media deleted")
                self.selected_media = None
                self.refresh()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete: {e}")
    
    def _search_library(self):
        """Search and filter library"""
        search_term = self.search_entry.get().lower()
        file_type = self.type_filter.get()
        
        for widget in self.library_scroll.winfo_children():
            widget.destroy()
        
        media_files = list(self.library_path.glob("*"))
        
        # Filter by search term and type
        filtered = []
        for f in media_files:
            if search_term and search_term not in f.name.lower():
                continue
            if file_type != "All":
                ext = f.suffix.lower()
                if file_type == "Image" and ext not in ['.jpg', '.jpeg', '.png', '.gif']:
                    continue
                elif file_type == "Video" and ext not in ['.mp4', '.mov', '.avi']:
                    continue
                elif file_type == "Document" and ext not in ['.pdf', '.docx']:
                    continue
            filtered.append(f)
        
        if not filtered:
            ctk.CTkLabel(
                self.library_scroll, text="No files match filter",
                text_color="#AAAAAA"
            ).pack(pady=20)
            return
        
        for media_file in filtered:
            self._create_media_widget(media_file)
