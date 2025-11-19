"""
Hashtag Tools Module for FYI Social Media Management Platform
Smart hashtag recommendations, trending analysis, and performance tracking
"""
import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime, timedelta
from typing import List, Dict
from database_manager import get_db_manager
from logger_config import get_logger

logger = get_logger(__name__)

class HashtagToolsFrame(ctk.CTkFrame):
    """Smart hashtag recommendations and trending analysis"""
    
    def __init__(self, parent, team_id: int, **kwargs):
        super().__init__(parent, **kwargs)
        self.team_id = team_id
        self.db = get_db_manager()
        
        self._create_widgets()
        self.refresh()
    
    def _create_widgets(self):
        """Create hashtag tools UI"""
        # Header
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Hashtag Tools", font=("Arial", 18, "bold")).pack(side="left")
        
        ctk.CTkButton(
            header_frame, text="🔄 Refresh Trending", width=140,
            command=self.refresh
        ).pack(side="right", padx=5)
        
        # Main tabs
        self.tabview = ctk.CTkTabview(self)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tabview.add("Smart Recommendations")
        self.tabview.add("Trending Hashtags")
        self.tabview.add("Saved Sets")
        self.tabview.add("Performance")
        
        # ===== SMART RECOMMENDATIONS TAB =====
        rec_tab = self.tabview.tab("Smart Recommendations")
        
        # Input section
        input_frame = ctk.CTkFrame(rec_tab)
        input_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(input_frame, text="Post Content:", font=("Arial", 10)).pack(anchor="w", pady=(0, 5))
        
        self.content_input = ctk.CTkTextbox(input_frame, height=80)
        self.content_input.pack(fill="both", padx=5, pady=5)
        
        # Platform and niche selection
        options_frame = ctk.CTkFrame(rec_tab)
        options_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(options_frame, text="Platform:", font=("Arial", 10)).pack(side="left", padx=5)
        self.platform_combo = ctk.CTkComboBox(
            options_frame, values=["Facebook", "Instagram", "Twitter", "LinkedIn", "TikTok"],
            state="readonly", width=120
        )
        self.platform_combo.set("Instagram")
        self.platform_combo.pack(side="left", padx=5)
        
        ctk.CTkLabel(options_frame, text="Niche:", font=("Arial", 10)).pack(side="left", padx=5)
        self.niche_combo = ctk.CTkComboBox(
            options_frame, values=["Tech", "Lifestyle", "Fashion", "Food", "Travel", "Business", "Other"],
            state="readonly", width=120
        )
        self.niche_combo.set("Tech")
        self.niche_combo.pack(side="left", padx=5)
        
        ctk.CTkButton(
            options_frame, text="Get Recommendations", fg_color="#51CF66",
            command=self._get_recommendations
        ).pack(side="left", padx=5)
        
        # Recommendations display
        ctk.CTkLabel(rec_tab, text="Recommended Hashtags:", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=(10, 5))
        
        self.recommendations_frame = ctk.CTkScrollableFrame(rec_tab, fg_color="#1a1a1a")
        self.recommendations_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ===== TRENDING HASHTAGS TAB =====
        trending_tab = self.tabview.tab("Trending Hashtags")
        
        # Platform filter
        platform_frame = ctk.CTkFrame(trending_tab)
        platform_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(platform_frame, text="Platform:", font=("Arial", 10)).pack(side="left", padx=5)
        
        self.trending_platform = ctk.CTkComboBox(
            platform_frame, values=["All", "Instagram", "Twitter", "TikTok", "YouTube"],
            state="readonly", width=120
        )
        self.trending_platform.set("Instagram")
        self.trending_platform.pack(side="left", padx=5)
        self.trending_platform.configure(command=self._show_trending)
        
        self.trending_list = ctk.CTkScrollableFrame(trending_tab, fg_color="#1a1a1a")
        self.trending_list.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ===== SAVED SETS TAB =====
        sets_tab = self.tabview.tab("Saved Sets")
        
        button_frame = ctk.CTkFrame(sets_tab)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            button_frame, text="➕ New Set", width=100,
            command=self._create_hashtag_set
        ).pack(side="left", padx=5)
        
        self.hashtag_sets = ctk.CTkScrollableFrame(sets_tab, fg_color="#1a1a1a")
        self.hashtag_sets.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ===== PERFORMANCE TAB =====
        perf_tab = self.tabview.tab("Performance")
        
        # Metrics
        metrics_frame = ctk.CTkFrame(perf_tab)
        metrics_frame.pack(fill="x", padx=10, pady=10)
        
        self.metric_top_hashtag = self._create_metric_card(metrics_frame, "Top Hashtag", "#TechLife")
        self.metric_top_hashtag.pack(side="left", padx=5, fill="both", expand=True)
        
        self.metric_avg_reach = self._create_metric_card(metrics_frame, "Avg Reach", "4.2K")
        self.metric_avg_reach.pack(side="left", padx=5, fill="both", expand=True)
        
        self.metric_engagement = self._create_metric_card(metrics_frame, "Avg Engagement", "8.5%")
        self.metric_engagement.pack(side="left", padx=5, fill="both", expand=True)
        
        # Performance table
        self.perf_list = ctk.CTkScrollableFrame(perf_tab, fg_color="#1a1a1a")
        self.perf_list.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _create_metric_card(self, parent, label: str, value: str):
        """Create metric card"""
        card = ctk.CTkFrame(parent, fg_color="#333333", border_width=1, border_color="#444444")
        
        ctk.CTkLabel(card, text=label, font=("Arial", 10), text_color="#AAAAAA").pack(pady=(10, 5))
        ctk.CTkLabel(card, text=value, font=("Arial", 16, "bold")).pack(pady=(0, 10))
        
        return card
    
    def refresh(self):
        """Refresh hashtag data"""
        self._show_trending()
        self._refresh_hashtag_sets()
        self._refresh_performance()
    
    def _get_recommendations(self):
        """Get smart hashtag recommendations"""
        content = self.content_input.get("1.0", "end").strip()
        if not content:
            messagebox.showwarning("Warning", "Enter post content")
            return
        
        platform = self.platform_combo.get()
        niche = self.niche_combo.get()
        
        # Clear previous recommendations
        for widget in self.recommendations_frame.winfo_children():
            widget.destroy()
        
        # Mock recommendations based on content analysis
        # In real app, would use hashtag API or ML analysis
        mock_hashtags = {
            "Tech": ["#Technology", "#Innovation", "#TechNews", "#SoftwareDevelopment", "#AI", "#CodeLife", "#StartUp", "#DevCommunity"],
            "Lifestyle": ["#LifestyleGoals", "#DailyLife", "#WellnessJourney", "#Mindfulness", "#SelfCare", "#HealthyLiving", "#Balance", "#Inspiration"],
            "Fashion": ["#FashionTrends", "#StyleInspiration", "#OOTDDaily", "#FashionWeek", "#DesignerLife", "#Runway", "#PersonalStyle", "#VintageVibes"],
            "Food": ["#FoodBlogger", "#Foodie", "#RecipeIdeas", "#CookingAtHome", "#HealthyRecipes", "#FoodPhotography", "#RestaurantLife", "#CulinaryArts"],
            "Travel": ["#TravelGram", "#Wanderlust", "#AdventureAwaits", "#ExploreMore", "#TravelBlogger", "#JourneyOfLife", "#DiscoverTheWorld", "#BucketList"],
        }
        
        hashtags = mock_hashtags.get(niche, mock_hashtags["Tech"])
        
        # Add engagement metrics
        hashtag_data = [
            {"tag": "#Technology", "volume": 450000, "engagement": 8.2},
            {"tag": "#Innovation", "volume": 320000, "engagement": 7.5},
            {"tag": "#TechNews", "volume": 280000, "engagement": 6.9},
            {"tag": "#SoftwareDevelopment", "volume": 150000, "engagement": 9.2},
            {"tag": "#AI", "volume": 520000, "engagement": 7.8},
            {"tag": "#CodeLife", "volume": 85000, "engagement": 10.1},
            {"tag": "#StartUp", "volume": 220000, "engagement": 8.7},
            {"tag": "#DevCommunity", "volume": 120000, "engagement": 9.5},
        ]
        
        self.db.log_activity(
            self.team_id, 1, "get_hashtag_recommendations",
            "hashtag_tools", None,
            {
                "platform": platform,
                "niche": niche,
                "content_length": len(content),
                "hashtags_count": len(hashtag_data)
            }
        )
        
        # Display recommendations
        for hashtag_info in hashtag_data:
            self._create_hashtag_widget(hashtag_info, self.recommendations_frame)
    
    def _create_hashtag_widget(self, hashtag_info: Dict, parent):
        """Create hashtag recommendation widget"""
        widget = ctk.CTkFrame(
            parent, fg_color="#333333", border_width=1, border_color="#444444"
        )
        widget.pack(fill="x", padx=5, pady=5)
        
        # Left side - hashtag and stats
        info_frame = ctk.CTkFrame(widget, fg_color="#333333")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(
            info_frame, text=hashtag_info['tag'], font=("Arial", 12, "bold"),
            text_color="#51CF66"
        ).pack(anchor="w")
        
        stats_text = f"Posts: {hashtag_info['volume']:,} | Engagement: {hashtag_info['engagement']}%"
        ctk.CTkLabel(
            info_frame, text=stats_text, font=("Arial", 9),
            text_color="#AAAAAA"
        ).pack(anchor="w")
        
        # Right side - actions
        action_frame = ctk.CTkFrame(widget, fg_color="#333333")
        action_frame.pack(side="right", padx=10, pady=10)
        
        ctk.CTkButton(
            action_frame, text="+ Add", width=60, fg_color="#51CF66",
            command=lambda: self._add_to_clipboard(hashtag_info['tag'])
        ).pack(side="left", padx=2)
        
        # Volume indicator (visual bar)
        volume_percent = min(hashtag_info['volume'] / 500000 * 100, 100)
        volume_bar = ctk.CTkProgressBar(
            action_frame, value=volume_percent / 100, width=80, height=20
        )
        volume_bar.pack(side="left", padx=5)
    
    def _add_to_clipboard(self, hashtag: str):
        """Add hashtag to content"""
        current = self.content_input.get("1.0", "end").strip()
        if current:
            self.content_input.insert("end", f" {hashtag}")
        else:
            self.content_input.insert("1.0", hashtag)
        
        self.db.log_activity(
            self.team_id, 1, "add_hashtag_to_post",
            "hashtag_tools", None,
            {"hashtag": hashtag}
        )
    
    def _show_trending(self):
        """Display trending hashtags"""
        for widget in self.trending_list.winfo_children():
            widget.destroy()
        
        platform = self.trending_platform.get()
        
        # Mock trending hashtags
        trending = [
            {"tag": "#TrendingNow", "position": 1, "momentum": "📈 +45%", "posts": 250000},
            {"tag": "#ViralContent", "position": 2, "momentum": "📈 +32%", "posts": 180000},
            {"tag": "#HotTopic", "position": 3, "momentum": "📈 +28%", "posts": 150000},
            {"tag": "#NewWave", "position": 4, "momentum": "📉 -5%", "posts": 95000},
            {"tag": "#SocialBuzz", "position": 5, "momentum": "📈 +18%", "posts": 120000},
        ]
        
        for hashtag in trending:
            widget = ctk.CTkFrame(
                self.trending_list, fg_color="#333333", border_width=1, border_color="#444444"
            )
            widget.pack(fill="x", padx=5, pady=5)
            
            # Rank badge
            rank_label = ctk.CTkLabel(
                widget, text=f"#{hashtag['position']}", font=("Arial", 14, "bold"),
                fg_color="#FFD43B", text_color="#000000", width=50
            )
            rank_label.pack(side="left", padx=10, pady=10)
            
            # Hashtag info
            info_frame = ctk.CTkFrame(widget, fg_color="#333333")
            info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            
            ctk.CTkLabel(
                info_frame, text=hashtag['tag'], font=("Arial", 12, "bold"),
                text_color="#51CF66"
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                info_frame, text=f"{hashtag['momentum']} • {hashtag['posts']:,} posts",
                font=("Arial", 9), text_color="#AAAAAA"
            ).pack(anchor="w")
            
            # Copy button
            ctk.CTkButton(
                widget, text="Copy", width=60,
                command=lambda: self._add_to_clipboard(hashtag['tag'])
            ).pack(side="right", padx=10, pady=10)
    
    def _refresh_hashtag_sets(self):
        """Refresh saved hashtag sets"""
        for widget in self.hashtag_sets.winfo_children():
            widget.destroy()
        
        # Mock saved sets
        sets = [
            {"id": 1, "name": "Tech Stack", "tags": "#Technology #Innovation #CodeLife #DevCommunity", "count": 4},
            {"id": 2, "name": "Brand Standard", "tags": "#Company #Official #News #Updates", "count": 4},
            {"id": 3, "name": "Engagement Boost", "tags": "#FollowUs #LikeAndShare #TagAFriend #Comment", "count": 4},
        ]
        
        if not sets:
            ctk.CTkLabel(
                self.hashtag_sets, text="No saved sets. Create one to get started!",
                text_color="#AAAAAA"
            ).pack(pady=20)
            return
        
        for set_item in sets:
            widget = ctk.CTkFrame(
                self.hashtag_sets, fg_color="#333333", border_width=1, border_color="#444444"
            )
            widget.pack(fill="x", padx=5, pady=5)
            
            info_frame = ctk.CTkFrame(widget, fg_color="#333333")
            info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
            
            ctk.CTkLabel(
                info_frame, text=set_item['name'], font=("Arial", 12, "bold")
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                info_frame, text=set_item['tags'], font=("Arial", 9),
                text_color="#AAAAAA", wraplength=300, justify="left"
            ).pack(anchor="w", pady=(5, 0))
            
            # Actions
            action_frame = ctk.CTkFrame(widget, fg_color="#333333")
            action_frame.pack(side="right", padx=10, pady=10)
            
            ctk.CTkButton(
                action_frame, text="Use", width=50,
                command=lambda s=set_item: self._use_hashtag_set(s)
            ).pack(side="left", padx=2)
            
            ctk.CTkButton(
                action_frame, text="Edit", width=50,
                command=lambda: messagebox.showinfo("Info", "Edit set")
            ).pack(side="left", padx=2)
            
            ctk.CTkButton(
                action_frame, text="Delete", width=50, fg_color="#FF6B6B",
                command=lambda: messagebox.showinfo("Info", "Delete set")
            ).pack(side="left", padx=2)
    
    def _create_hashtag_set(self):
        """Create new hashtag set"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("New Hashtag Set")
        dialog.geometry("400x300")
        
        ctk.CTkLabel(dialog, text="Set Name:", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(15, 0))
        name_entry = ctk.CTkEntry(dialog, placeholder_text="e.g., Brand Standard")
        name_entry.pack(fill="x", padx=15, pady=5)
        
        ctk.CTkLabel(dialog, text="Hashtags (space separated):", font=("Arial", 10)).pack(anchor="w", padx=15, pady=(10, 0))
        tags_box = ctk.CTkTextbox(dialog, height=150)
        tags_box.pack(fill="both", expand=True, padx=15, pady=5)
        
        def save_set():
            name = name_entry.get().strip()
            tags = tags_box.get("1.0", "end").strip()
            
            if not name or not tags:
                messagebox.showwarning("Warning", "Fill all fields")
                return
            
            self.db.log_activity(
                self.team_id, 1, "create_hashtag_set",
                "hashtag_tools", None,
                {"name": name, "tags": tags}
            )
            
            messagebox.showinfo("Success", f"Set '{name}' created")
            dialog.destroy()
            self._refresh_hashtag_sets()
        
        ctk.CTkButton(dialog, text="Save Set", command=save_set).pack(pady=10)
    
    def _use_hashtag_set(self, set_item: Dict):
        """Use hashtag set in content"""
        self.content_input.insert("end", f"\n{set_item['tags']}")
        messagebox.showinfo("Success", f"Added {set_item['name']} hashtags")
    
    def _refresh_performance(self):
        """Refresh hashtag performance"""
        for widget in self.perf_list.winfo_children():
            widget.destroy()
        
        # Mock performance data
        performance = [
            {"hashtag": "#Technology", "posts": 45, "reach": 125000, "engagement": "8.2%", "growth": "📈 +12%"},
            {"hashtag": "#Innovation", "posts": 32, "reach": 98000, "engagement": "7.5%", "growth": "📈 +8%"},
            {"hashtag": "#CodeLife", "posts": 28, "reach": 85000, "engagement": "10.1%", "growth": "📈 +15%"},
            {"hashtag": "#DevCommunity", "posts": 24, "reach": 72000, "engagement": "9.5%", "growth": "📈 +6%"},
        ]
        
        for item in performance:
            widget = ctk.CTkFrame(
                self.perf_list, fg_color="#333333", border_width=1, border_color="#444444"
            )
            widget.pack(fill="x", padx=5, pady=5)
            
            ctk.CTkLabel(
                widget, text=item['hashtag'], font=("Arial", 11, "bold"),
                text_color="#51CF66"
            ).pack(anchor="w", padx=10, pady=(10, 0))
            
            stats = f"Posts: {item['posts']} | Reach: {item['reach']:,} | Engagement: {item['engagement']} | {item['growth']}"
            ctk.CTkLabel(
                widget, text=stats, font=("Arial", 9),
                text_color="#AAAAAA"
            ).pack(anchor="w", padx=10, pady=(0, 10))
