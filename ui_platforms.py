"""
Additional Platforms UI for FYI Social Media Management
Twitter, LinkedIn, TikTok, Pinterest, WhatsApp, Telegram management
"""
import customtkinter as ctk
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox

from platform_integrations import (
    get_twitter_uploader, get_linkedin_uploader, get_tiktok_uploader,
    get_pinterest_uploader, get_whatsapp_uploader, get_telegram_uploader
)
from database_manager import get_db_manager
from account_manager import get_account_manager

db_manager = get_db_manager()
account_manager = get_account_manager()


class AdditionalPlatformsFrame(ctk.CTkFrame):
    """Management interface for additional social platforms"""
    
    def __init__(self, parent, team_id=1):
        super().__init__(parent)
        self.team_id = team_id
        self.tiktok_video_path = None
        self.tiktok_account_map = {}
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI layout"""
        # Create scrollable main frame
        main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs for each platform
        self.tab_view = ctk.CTkTabview(main_frame, height=600)
        self.tab_view.pack(fill="both", expand=True)
        
        # Tab 1: Twitter
        self.twitter_tab = self.tab_view.add("𝕏 Twitter")
        self._setup_twitter_tab()
        
        # Tab 2: LinkedIn
        self.linkedin_tab = self.tab_view.add("💼 LinkedIn")
        self._setup_linkedin_tab()
        
        # Tab 3: TikTok
        self.tiktok_tab = self.tab_view.add("🎵 TikTok")
        self._setup_tiktok_tab()
        
        # Tab 4: Pinterest
        self.pinterest_tab = self.tab_view.add("📌 Pinterest")
        self._setup_pinterest_tab()
        
        # Tab 5: WhatsApp & Telegram
        self.messaging_tab = self.tab_view.add("💬 Messaging")
        self._setup_messaging_tab()
    
    def _setup_twitter_tab(self):
        """Setup Twitter/X tab"""
        # Create scrollable container
        scroll_frame = ctk.CTkScrollableFrame(self.twitter_tab, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        header_frame = ctk.CTkFrame(scroll_frame)
        header_frame.pack(fill="x", padx=0, pady=10)
        
        ctk.CTkLabel(header_frame, text="𝕏 Twitter/X Management", font=("Arial", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="Post tweets, schedule content, and manage engagement", text_color="gray", font=("Arial", 10)).pack(anchor="w")
        
        # Account info
        account_frame = ctk.CTkFrame(scroll_frame)
        account_frame.pack(fill="x", padx=0, pady=10)
        
        ctk.CTkLabel(account_frame, text="🔗 Connected Account:", font=("Arial", 11)).pack(anchor="w", pady=3)
        ctk.CTkLabel(account_frame, text="@YourHandle (125K followers)", text_color="cyan", font=("Arial", 11, "bold")).pack(anchor="w")
        
        # Tweet compose
        compose_frame = ctk.CTkFrame(self.twitter_tab)
        compose_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(compose_frame, text="📝 Compose Tweet:", font=("Arial", 11, "bold")).pack(anchor="w", pady=3)
        
        self.twitter_text = ctk.CTkTextbox(compose_frame, height=80)
        self.twitter_text.pack(fill="x", pady=5)
        
        # Tweet info
        info_frame = ctk.CTkFrame(compose_frame)
        info_frame.pack(fill="x", pady=5)
        
        self.twitter_char_count = ctk.CTkLabel(info_frame, text="0/280 characters", text_color="gray", font=("Arial", 9))
        self.twitter_char_count.pack(anchor="e")
        self.twitter_text.bind("<KeyRelease>", lambda e: self._update_twitter_count())
        
        # Media upload
        media_frame = ctk.CTkFrame(self.twitter_tab)
        media_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkButton(media_frame, text="📸 Add Image/Video", fg_color="blue", width=150).pack(side="left", padx=5)
        ctk.CTkButton(media_frame, text="🔗 Add Link", width=150).pack(side="left", padx=5)
        
        # Schedule/Post buttons
        action_frame = ctk.CTkFrame(self.twitter_tab)
        action_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkButton(
            action_frame,
            text="📤 Post Now",
            command=self._post_twitter,
            fg_color="green",
            height=40
        ).pack(fill="x", pady=5)
        
        ctk.CTkButton(
            action_frame,
            text="⏰ Schedule Tweet",
            fg_color="orange",
            height=40
        ).pack(fill="x", pady=5)
        
        # Recent tweets
        recent_frame = ctk.CTkFrame(self.twitter_tab)
        recent_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        ctk.CTkLabel(recent_frame, text="📊 Recent Tweets:", font=("Arial", 11, "bold")).pack(anchor="w", pady=5)
        
        tweets = [
            {"text": "Just launched our new feature! 🚀", "engagements": 234, "time": "2h ago"},
            {"text": "Join us for webinar tomorrow at 2PM EST", "engagements": 156, "time": "4h ago"},
        ]
        
        for tweet in tweets:
            self._create_tweet_card(tweet, recent_frame)
    
    def _setup_linkedin_tab(self):
        """Setup LinkedIn tab"""
        # Header
        header_frame = ctk.CTkFrame(self.linkedin_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="💼 LinkedIn Management", font=("Arial", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="Share updates on personal profile and company page", text_color="gray", font=("Arial", 10)).pack(anchor="w")
        
        # Post type selection
        type_frame = ctk.CTkFrame(self.linkedin_tab)
        type_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(type_frame, text="Post Type:", font=("Arial", 11)).pack(side="left", padx=5)
        post_type = ctk.CTkComboBox(
            type_frame,
            values=["Personal Profile", "Company Page"],
            state="readonly",
            width=200
        )
        post_type.set("Personal Profile")
        post_type.pack(side="left", padx=5)
        
        # Article preview
        article_frame = ctk.CTkFrame(self.linkedin_tab)
        article_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(article_frame, text="📰 Post Content:", font=("Arial", 11, "bold")).pack(anchor="w", pady=3)
        
        self.linkedin_text = ctk.CTkTextbox(article_frame, height=100)
        self.linkedin_text.pack(fill="x", pady=5)
        
        # Post actions
        action_frame = ctk.CTkFrame(self.linkedin_tab)
        action_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkButton(action_frame, text="📤 Share Now", command=self._post_linkedin, fg_color="green", height=40).pack(fill="x", pady=5)
        ctk.CTkButton(action_frame, text="⏰ Schedule", fg_color="orange", height=40).pack(fill="x", pady=5)
        
        # Analytics
        analytics_frame = ctk.CTkFrame(self.linkedin_tab)
        analytics_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        ctk.CTkLabel(analytics_frame, text="📈 Top Posts (This Month):", font=("Arial", 11, "bold")).pack(anchor="w", pady=5)
        
        posts = [
            {"title": "Industry insights...", "views": 2150, "likes": 45},
            {"title": "Company announcement...", "views": 1890, "likes": 32},
        ]
        
        for post in posts:
            card = ctk.CTkFrame(analytics_frame, fg_color="gray25")
            card.pack(fill="x", padx=5, pady=5)
            ctk.CTkLabel(card, text=post["title"], font=("Arial", 10)).pack(anchor="w", padx=10, pady=(8, 3))
            ctk.CTkLabel(card, text=f"👁️ {post['views']} views | ❤️ {post['likes']} likes", 
                        text_color="cyan", font=("Arial", 9)).pack(anchor="w", padx=10, pady=(0, 8))
    
    def _setup_tiktok_tab(self):
        """Setup TikTok tab"""
        # Header
        header_frame = ctk.CTkFrame(self.tiktok_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="🎵 TikTok Management", font=("Arial", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="Upload and schedule TikTok videos", text_color="gray", font=("Arial", 10)).pack(anchor="w")
        
        # Video upload
        upload_frame = ctk.CTkFrame(self.tiktok_tab)
        upload_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(upload_frame, text="🎬 Video Upload:", font=("Arial", 11, "bold")).pack(anchor="w", pady=5)
        
        ctk.CTkButton(
            upload_frame,
            text="📁 Choose Video (Max 10 min)",
            fg_color="blue",
            height=40,
            command=self._choose_tiktok_video
        ).pack(fill="x", pady=5)
        self.tiktok_video_label = ctk.CTkLabel(upload_frame, text="No file selected", text_color="gray")
        self.tiktok_video_label.pack(anchor="w", pady=(2, 0))

        account_frame = ctk.CTkFrame(self.tiktok_tab)
        account_frame.pack(fill="x", padx=15, pady=10)
        ctk.CTkLabel(account_frame, text="Linked TikTok Account:", font=("Arial", 11)).pack(anchor="w", pady=3)

        accounts = account_manager.get_accounts_by_platform("tiktok")
        combo_values = []
        self.tiktok_account_map = {}
        for acc in accounts:
            label = f"{acc.name or acc.username} · {acc.account_id[-6:]}"
            self.tiktok_account_map[label] = acc.account_id
            combo_values.append(label)
        if not combo_values:
            combo_values = ["No TikTok accounts linked"]
        self.tiktok_account_combo = ctk.CTkComboBox(
            account_frame,
            values=combo_values,
            state="readonly" if accounts else "disabled"
        )
        self.tiktok_account_combo.set(combo_values[0])
        self.tiktok_account_combo.pack(fill="x", pady=5)
        
        # Video details
        details_frame = ctk.CTkFrame(self.tiktok_tab)
        details_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(details_frame, text="Caption:", font=("Arial", 11)).pack(anchor="w", pady=3)
        self.tiktok_caption = ctk.CTkTextbox(details_frame, height=60)
        self.tiktok_caption.pack(fill="x", pady=5)
        
        ctk.CTkLabel(details_frame, text="Hashtags:", font=("Arial", 11)).pack(anchor="w", pady=3)
        self.tiktok_hashtags = ctk.CTkEntry(details_frame, placeholder_text="#trending #viral #fyp")
        self.tiktok_hashtags.pack(fill="x", pady=5)

        ctk.CTkLabel(details_frame, text="Schedule (optional, YYYY-MM-DD HH:MM)", font=("Arial", 11)).pack(anchor="w", pady=3)
        self.tiktok_schedule_entry = ctk.CTkEntry(details_frame, placeholder_text="2024-07-04 15:30")
        self.tiktok_schedule_entry.pack(fill="x", pady=5)
        
        # Cover image
        cover_frame = ctk.CTkFrame(self.tiktok_tab)
        cover_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkButton(cover_frame, text="🖼️ Choose Cover Image", fg_color="blue").pack(fill="x", pady=5)
        
        # Upload/Schedule
        action_frame = ctk.CTkFrame(self.tiktok_tab)
        action_frame.pack(fill="x", padx=15, pady=15)
        
        self.tiktok_upload_btn = ctk.CTkButton(action_frame, text="📤 Upload Now", command=self._post_tiktok, fg_color="green", height=40)
        self.tiktok_upload_btn.pack(fill="x", pady=5)
        ctk.CTkButton(action_frame, text="⏰ Schedule", fg_color="orange", height=40).pack(fill="x", pady=5)
        self.tiktok_status_label = ctk.CTkLabel(action_frame, text="", text_color="gray")
        self.tiktok_status_label.pack(anchor="w", pady=(5, 0))
        
        # Performance
        perf_frame = ctk.CTkFrame(self.tiktok_tab)
        perf_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        ctk.CTkLabel(perf_frame, text="📊 Top Videos:", font=("Arial", 11, "bold")).pack(anchor="w", pady=5)
        
        videos = [
            {"caption": "Behind the scenes...", "views": 125000, "likes": 8500},
            {"caption": "Trending sound...", "views": 89000, "likes": 6200},
        ]
        
        for video in videos:
            card = ctk.CTkFrame(perf_frame, fg_color="gray25")
            card.pack(fill="x", padx=5, pady=5)
            ctk.CTkLabel(card, text=video["caption"], font=("Arial", 10)).pack(anchor="w", padx=10, pady=(8, 3))
            ctk.CTkLabel(card, text=f"👁️ {video['views']:,} views | ❤️ {video['likes']:,} likes", 
                        text_color="cyan", font=("Arial", 9)).pack(anchor="w", padx=10, pady=(0, 8))
    
    def _setup_pinterest_tab(self):
        """Setup Pinterest tab"""
        # Header
        header_frame = ctk.CTkFrame(self.pinterest_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="📌 Pinterest Management", font=("Arial", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="Create and schedule Pins", text_color="gray", font=("Arial", 10)).pack(anchor="w")
        
        # Pin creation
        pin_frame = ctk.CTkFrame(self.pinterest_tab)
        pin_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(pin_frame, text="📸 Pin Image:", font=("Arial", 11, "bold")).pack(anchor="w", pady=5)
        ctk.CTkButton(pin_frame, text="📁 Upload Image (1000x1500 recommended)", fg_color="blue", height=40).pack(fill="x", pady=5)
        
        # Pin details
        details_frame = ctk.CTkFrame(self.pinterest_tab)
        details_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(details_frame, text="Title:", font=("Arial", 11)).pack(anchor="w", pady=3)
        ctk.CTkEntry(details_frame, placeholder_text="Pin title").pack(fill="x", pady=5)
        
        ctk.CTkLabel(details_frame, text="Description:", font=("Arial", 11)).pack(anchor="w", pady=3)
        ctk.CTkTextbox(details_frame, height=60).pack(fill="x", pady=5)
        
        ctk.CTkLabel(details_frame, text="Destination URL:", font=("Arial", 11)).pack(anchor="w", pady=3)
        ctk.CTkEntry(details_frame, placeholder_text="https://example.com").pack(fill="x", pady=5)
        
        # Board selection
        board_frame = ctk.CTkFrame(self.pinterest_tab)
        board_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(board_frame, text="Board:", font=("Arial", 11)).pack(side="left", padx=5)
        board_combo = ctk.CTkComboBox(
            board_frame,
            values=["Fashion & Style", "Home Decor", "Travel", "Food & Recipes"],
            state="readonly"
        )
        board_combo.set("Fashion & Style")
        board_combo.pack(side="left", padx=5)
        
        # Create/Schedule
        action_frame = ctk.CTkFrame(self.pinterest_tab)
        action_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkButton(action_frame, text="📌 Create Pin", command=self._create_pin, fg_color="green", height=40).pack(fill="x", pady=5)
        ctk.CTkButton(action_frame, text="⏰ Schedule", fg_color="orange", height=40).pack(fill="x", pady=5)
    
    def _setup_messaging_tab(self):
        """Setup messaging platforms (WhatsApp & Telegram)"""
        # Header
        header_frame = ctk.CTkFrame(self.messaging_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="💬 Messaging Platforms", font=("Arial", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="WhatsApp and Telegram broadcast messaging", text_color="gray", font=("Arial", 10)).pack(anchor="w")
        
        # Platform selection
        platform_frame = ctk.CTkFrame(self.messaging_tab)
        platform_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(platform_frame, text="Select Platform:", font=("Arial", 11)).pack(side="left", padx=5)
        platform_combo = ctk.CTkComboBox(
            platform_frame,
            values=["WhatsApp", "Telegram"],
            state="readonly",
            width=150
        )
        platform_combo.set("WhatsApp")
        platform_combo.pack(side="left", padx=5)
        
        # Message compose
        compose_frame = ctk.CTkFrame(self.messaging_tab)
        compose_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(compose_frame, text="📝 Message:", font=("Arial", 11, "bold")).pack(anchor="w", pady=3)
        
        self.message_text = ctk.CTkTextbox(compose_frame, height=80)
        self.message_text.pack(fill="x", pady=5)
        
        # Recipients
        recipients_frame = ctk.CTkFrame(self.messaging_tab)
        recipients_frame.pack(fill="x", padx=15, pady=10)
        
        ctk.CTkLabel(recipients_frame, text="Recipients:", font=("Arial", 11)).pack(anchor="w", pady=3)
        recipients_list = ctk.CTkTextbox(recipients_frame, height=80)
        recipients_list.pack(fill="x", pady=5)
        ctk.CTkLabel(recipients_frame, text="Enter phone numbers or group IDs (one per line)", text_color="gray", font=("Arial", 9)).pack(anchor="w")
        
        # Send button
        action_frame = ctk.CTkFrame(self.messaging_tab)
        action_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkButton(
            action_frame,
            text="📤 Send Message",
            command=self._send_message,
            fg_color="green",
            height=40
        ).pack(fill="x", pady=5)
    
    # ===== ACTION HANDLERS =====
    
    def _update_twitter_count(self):
        """Update Twitter character count"""
        text = self.twitter_text.get("1.0", "end-1c")
        char_count = len(text)
        color = "red" if char_count > 280 else "gray"
        self.twitter_char_count.configure(text=f"{char_count}/280 characters", text_color=color)
    
    def _post_twitter(self):
        """Post tweet"""
        text = self.twitter_text.get("1.0", "end-1c")
        if text:
            uploader = get_twitter_uploader()
            result = uploader.post_tweet(text)
            db_manager.log_activity(
                team_id=self.team_id,
                user_id=1,
                action="post_twitter",
                target_type="posts",
                target_id=None,
                metadata={"text_length": len(text)}
            )
    
    def _post_linkedin(self):
        """Post to LinkedIn"""
        text = self.linkedin_text.get("1.0", "end-1c")
        if text:
            uploader = get_linkedin_uploader()
            result = uploader.post_personal(text)
            db_manager.log_activity(
                team_id=self.team_id,
                user_id=1,
                action="post_linkedin",
                target_type="posts",
                target_id=None,
                metadata={"text_length": len(text)}
            )
    
    def _post_tiktok(self):
        """Upload to TikTok"""
        caption = self.tiktok_caption.get("1.0", "end-1c").strip()
        if not caption:
            messagebox.showerror("Missing caption", "Write a caption for your TikTok video.")
            return

        if not self.tiktok_video_path:
            messagebox.showerror("Missing video", "Choose a video to upload.")
            return

        selected_account = self.tiktok_account_combo.get()
        account_id = self.tiktok_account_map.get(selected_account)
        if not account_id:
            messagebox.showerror("No TikTok account", "Link a TikTok account in Accounts > TikTok.")
            return

        schedule_str = self.tiktok_schedule_entry.get().strip()
        schedule_ts = None
        if schedule_str:
            try:
                dt = datetime.strptime(schedule_str, "%Y-%m-%d %H:%M")
                schedule_ts = int(dt.timestamp())
            except ValueError:
                messagebox.showerror("Invalid schedule", "Use format YYYY-MM-DD HH:MM")
                return

        hashtags = [tag for tag in self.tiktok_hashtags.get().split() if tag]

        self.tiktok_upload_btn.configure(state="disabled", text="Uploading…")
        self.tiktok_status_label.configure(text="Uploading to TikTok…", text_color="#00BCD4")

        threading.Thread(
            target=self._run_tiktok_upload,
            args=(account_id, caption, hashtags, schedule_ts),
            daemon=True
        ).start()

    def _choose_tiktok_video(self):
        """Open file picker for TikTok video."""
        file_path = filedialog.askopenfilename(
            title="Select TikTok video",
            filetypes=[("Video files", "*.mp4 *.mov *.mkv *.avi"), ("All files", "*.*")]
        )
        if not file_path:
            return
        self.tiktok_video_path = file_path
        self.tiktok_video_label.configure(text=Path(file_path).name)

    def _run_tiktok_upload(self, account_id, caption, hashtags, schedule_ts):
        """Execute TikTok upload off the UI thread."""
        uploader = get_tiktok_uploader()
        try:
            result = uploader.upload_video(
                account_id=account_id,
                video_path=self.tiktok_video_path,
                caption=caption,
                hashtags=hashtags,
                schedule_time=schedule_ts
            )
        except Exception as exc:  # pragma: no cover - UI runtime
            self.after(0, lambda: self._handle_tiktok_result(False, str(exc), hashtags))
            return

        self.after(0, lambda: self._handle_tiktok_result(True, result, hashtags))

    def _handle_tiktok_result(self, success, payload, hashtags):
        """Update UI after upload attempt."""
        self.tiktok_upload_btn.configure(state="normal", text="📤 Upload Now")
        if success:
            self.tiktok_status_label.configure(text="TikTok upload complete", text_color="#4CAF50")
            db_manager.log_activity(
                team_id=self.team_id,
                user_id=1,
                action="post_tiktok",
                target_type="posts",
                target_id=None,
                metadata={
                    "caption_length": len(self.tiktok_caption.get("1.0", "end-1c")),
                    "hashtag_count": len(hashtags)
                }
            )
            messagebox.showinfo("TikTok", "Upload completed successfully." if isinstance(payload, dict) else payload)
        else:
            self.tiktok_status_label.configure(text="TikTok upload failed", text_color="#FF7043")
            messagebox.showerror("TikTok", payload)
    
    def _create_pin(self):
        """Create Pinterest pin"""
        db_manager.log_activity(
            team_id=self.team_id,
            user_id=1,
            action="create_pin",
            target_type="posts",
            target_id=None,
            metadata={}
        )
    
    def _send_message(self):
        """Send messaging app message"""
        message = self.message_text.get("1.0", "end-1c")
        if message:
            db_manager.log_activity(
                team_id=self.team_id,
                user_id=1,
                action="send_message",
                target_type="messages",
                target_id=None,
                metadata={"message_length": len(message)}
            )
    
    def _create_tweet_card(self, tweet, parent):
        """Create tweet card widget"""
        card = ctk.CTkFrame(parent, fg_color="gray25")
        card.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkLabel(card, text=tweet["text"], font=("Arial", 10)).pack(anchor="w", padx=10, pady=(8, 3))
        ctk.CTkLabel(card, text=f"❤️ {tweet['engagements']} engagements • {tweet['time']}", 
                    text_color="cyan", font=("Arial", 9)).pack(anchor="w", padx=10, pady=(0, 8))
