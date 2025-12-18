"""
AI-Powered Content Generation UI for FYI Platform
Caption generation, hashtag suggestions, best time prediction, content analysis
"""
import customtkinter as ctk
from datetime import datetime
from tkinter import filedialog, messagebox
from pathlib import Path
import threading
import os
import sys
import subprocess

from ai_engine import get_ai_engine
from database_manager import get_db_manager
from remix_service import get_remix_service
from video_ai_service import get_video_ai_generator

db_manager = get_db_manager()
ai_engine = get_ai_engine()
remix_service = get_remix_service()
video_ai_generator = get_video_ai_generator()


class AIContentGeneratorFrame(ctk.CTkFrame):
    """AI-powered content generation and recommendations"""
    
    def __init__(self, parent, team_id=1):
        super().__init__(parent)
        self.team_id = team_id
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup UI layout"""
        # Create scrollable main frame
        main_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create tabs inside scrollable frame
        self.tab_view = ctk.CTkTabview(main_frame, height=600)
        self.tab_view.pack(fill="both", expand=True)
        
        # Tab 1: Caption Generator
        self.caption_tab = self.tab_view.add("✍️ Caption Generator")
        self._setup_caption_tab()
        
        # Tab 2: Hashtag Generator
        self.hashtag_tab = self.tab_view.add("#️⃣ Hashtag Generator")
        self._setup_hashtag_tab()
        
        # Tab 3: Best Time Predictor
        self.time_tab = self.tab_view.add("⏰ Best Time to Post")
        self._setup_time_tab()
        
        # Tab 4: Content Analyzer
        self.analyzer_tab = self.tab_view.add("🔍 Content Analyzer")
        self._setup_analyzer_tab()
        
        # Tab 5: Recommendations
        self.recommendations_tab = self.tab_view.add("💡 Recommendations")
        self._setup_recommendations_tab()

        # Tab 6: Remix Lab
        self.remix_tab = self.tab_view.add("🌀 Remix Lab")
        self._setup_remix_tab()
        self.remix_file_path = None

        # Tab 7: Video Lab
        self.video_tab = self.tab_view.add("🎬 Video Lab")
        self._setup_video_tab()
        self.generated_video_path = None
    
    def _setup_caption_tab(self):
        """Setup caption generator tab"""
        # Create scrollable container for this tab
        scroll_frame = ctk.CTkScrollableFrame(self.caption_tab, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header
        header_frame = ctk.CTkFrame(scroll_frame)
        header_frame.pack(fill="x", padx=0, pady=10)
        
        ctk.CTkLabel(header_frame, text="AI Caption Generator", font=("Arial", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="Generate engaging captions for your social media posts", text_color="gray", font=("Arial", 10)).pack(anchor="w")
        
        # Input section
        input_frame = ctk.CTkFrame(scroll_frame)
        input_frame.pack(fill="x", padx=0, pady=10)
        
        # Platform selection
        platform_frame = ctk.CTkFrame(input_frame)
        platform_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(platform_frame, text="Platform:", font=("Arial", 11)).pack(side="left", padx=5)
        self.caption_platform = ctk.CTkComboBox(
            platform_frame,
            values=["Instagram", "Facebook", "Twitter", "TikTok"],
            state="readonly",
            width=150
        )
        self.caption_platform.set("Instagram")
        self.caption_platform.pack(side="left", padx=5)
        
        # Tone selection
        tone_frame = ctk.CTkFrame(input_frame)
        tone_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(tone_frame, text="Tone:", font=("Arial", 11)).pack(side="left", padx=5)
        self.caption_tone = ctk.CTkComboBox(
            tone_frame,
            values=["Professional", "Casual", "Funny", "Inspirational"],
            state="readonly",
            width=150
        )
        self.caption_tone.set("Casual")
        self.caption_tone.pack(side="left", padx=5)
        
        # Content type
        type_frame = ctk.CTkFrame(input_frame)
        type_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(type_frame, text="Content Type:", font=("Arial", 11)).pack(side="left", padx=5)
        self.caption_type = ctk.CTkComboBox(
            type_frame,
            values=["Photo", "Video", "Article", "Product"],
            state="readonly",
            width=150
        )
        self.caption_type.set("Photo")
        self.caption_type.pack(side="left", padx=5)
        
        # Topic input
        topic_frame = ctk.CTkFrame(input_frame)
        topic_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(topic_frame, text="Topic/Description:", font=("Arial", 11)).pack(anchor="w", pady=3)
        self.caption_topic = ctk.CTkTextbox(topic_frame, height=60)
        self.caption_topic.pack(fill="x")
        
        # Generate button
        ctk.CTkButton(
            input_frame,
            text="🤖 Generate Caption",
            command=self._generate_caption,
            fg_color="blue",
            height=40
        ).pack(fill="x", pady=10)
        
        # Output section
        output_frame = ctk.CTkFrame(self.caption_tab)
        output_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        ctk.CTkLabel(output_frame, text="Generated Caption:", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        
        self.caption_output = ctk.CTkTextbox(output_frame, height=80)
        self.caption_output.pack(fill="both", expand=True, pady=5)
        
        # Action buttons
        action_frame = ctk.CTkFrame(output_frame)
        action_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(action_frame, text="📋 Copy", command=self._copy_caption, fg_color="green", width=100).pack(side="left", padx=3)
        ctk.CTkButton(action_frame, text="❤️ Favorite", fg_color="red", width=100).pack(side="left", padx=3)
        ctk.CTkButton(action_frame, text="🔄 Regenerate", command=self._generate_caption, width=100).pack(side="left", padx=3)
    
    def _setup_hashtag_tab(self):
        """Setup hashtag generator tab"""
        # Header
        header_frame = ctk.CTkFrame(self.hashtag_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="AI Hashtag Generator", font=("Arial", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="Generate trending hashtags for maximum reach", text_color="gray", font=("Arial", 10)).pack(anchor="w")
        
        # Input section
        input_frame = ctk.CTkFrame(self.hashtag_tab)
        input_frame.pack(fill="x", padx=15, pady=10)
        
        # Platform selection
        platform_frame = ctk.CTkFrame(input_frame)
        platform_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(platform_frame, text="Platform:", font=("Arial", 11)).pack(side="left", padx=5)
        self.hashtag_platform = ctk.CTkComboBox(
            platform_frame,
            values=["Instagram", "Facebook", "Twitter", "TikTok"],
            state="readonly",
            width=150
        )
        self.hashtag_platform.set("Instagram")
        self.hashtag_platform.pack(side="left", padx=5)
        
        # Hashtag count
        count_frame = ctk.CTkFrame(input_frame)
        count_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(count_frame, text="Number of Hashtags:", font=("Arial", 11)).pack(side="left", padx=5)
        self.hashtag_count = ctk.CTkComboBox(
            count_frame,
            values=["5", "10", "15", "20", "30"],
            state="readonly",
            width=150
        )
        self.hashtag_count.set("10")
        self.hashtag_count.pack(side="left", padx=5)
        
        # Topic
        topic_frame = ctk.CTkFrame(input_frame)
        topic_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(topic_frame, text="Content Topic:", font=("Arial", 11)).pack(anchor="w", pady=3)
        self.hashtag_topic = ctk.CTkEntry(topic_frame, placeholder_text="e.g., Summer Fashion")
        self.hashtag_topic.pack(fill="x")
        
        # Include trending
        trending_frame = ctk.CTkFrame(input_frame)
        trending_frame.pack(fill="x", pady=5)
        self.hashtag_trending = ctk.CTkCheckBox(trending_frame, text="Include trending hashtags", onvalue=True, offvalue=False)
        self.hashtag_trending.pack(side="left")
        
        # Generate button
        ctk.CTkButton(
            input_frame,
            text="🤖 Generate Hashtags",
            command=self._generate_hashtags,
            fg_color="blue",
            height=40
        ).pack(fill="x", pady=10)
        
        # Output section
        output_frame = ctk.CTkFrame(self.hashtag_tab)
        output_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        ctk.CTkLabel(output_frame, text="Generated Hashtags:", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        
        self.hashtag_output = ctk.CTkTextbox(output_frame, height=100)
        self.hashtag_output.pack(fill="both", expand=True, pady=5)
        
        # Action buttons
        action_frame = ctk.CTkFrame(output_frame)
        action_frame.pack(fill="x", pady=5)
        
        ctk.CTkButton(action_frame, text="📋 Copy All", command=self._copy_hashtags, fg_color="green", width=100).pack(side="left", padx=3)
        ctk.CTkButton(action_frame, text="❤️ Favorite", fg_color="red", width=100).pack(side="left", padx=3)
        ctk.CTkButton(action_frame, text="🔄 Regenerate", command=self._generate_hashtags, width=100).pack(side="left", padx=3)
    
    def _setup_time_tab(self):
        """Setup best time to post tab"""
        # Header
        header_frame = ctk.CTkFrame(self.time_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Best Time to Post Predictor", font=("Arial", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="AI predicts optimal posting time for maximum engagement", text_color="gray", font=("Arial", 10)).pack(anchor="w")
        
        # Input section
        input_frame = ctk.CTkFrame(self.time_tab)
        input_frame.pack(fill="x", padx=15, pady=10)
        
        # Platform
        platform_frame = ctk.CTkFrame(input_frame)
        platform_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(platform_frame, text="Platform:", font=("Arial", 11)).pack(side="left", padx=5)
        self.time_platform = ctk.CTkComboBox(
            platform_frame,
            values=["Instagram", "Facebook", "Twitter", "TikTok"],
            state="readonly",
            width=150
        )
        self.time_platform.set("Instagram")
        self.time_platform.pack(side="left", padx=5)
        
        # Audience
        audience_frame = ctk.CTkFrame(input_frame)
        audience_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(audience_frame, text="Target Audience:", font=("Arial", 11)).pack(side="left", padx=5)
        self.time_audience = ctk.CTkEntry(audience_frame, placeholder_text="e.g., Young professionals, 25-35")
        self.time_audience.pack(side="left", padx=5, fill="x", expand=True)
        
        # Content type
        type_frame = ctk.CTkFrame(input_frame)
        type_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(type_frame, text="Content Type:", font=("Arial", 11)).pack(side="left", padx=5)
        self.time_type = ctk.CTkComboBox(
            type_frame,
            values=["Photo", "Video", "Article", "Reel"],
            state="readonly",
            width=150
        )
        self.time_type.set("Photo")
        self.time_type.pack(side="left", padx=5)
        
        # Predict button
        ctk.CTkButton(
            input_frame,
            text="🤖 Predict Best Time",
            command=self._predict_time,
            fg_color="blue",
            height=40
        ).pack(fill="x", pady=10)
        
        # Results section
        results_frame = ctk.CTkFrame(self.time_tab)
        results_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        # Best time result
        best_time_label = ctk.CTkLabel(results_frame, text="Optimal Time:", font=("Arial", 12, "bold"))
        best_time_label.pack(anchor="w", pady=5)
        
        self.best_time_result = ctk.CTkLabel(
            results_frame,
            text="Select platform and click Predict",
            font=("Arial", 14, "bold"),
            text_color="cyan"
        )
        self.best_time_result.pack(anchor="w", pady=5)
        
        # Additional insights
        insights_label = ctk.CTkLabel(results_frame, text="📊 Engagement Insights:", font=("Arial", 11, "bold"))
        insights_label.pack(anchor="w", pady=(20, 5))
        
        self.time_insights = ctk.CTkTextbox(results_frame, height=150)
        self.time_insights.pack(fill="both", expand=True, pady=5)
    
    def _setup_analyzer_tab(self):
        """Setup content analyzer tab"""
        # Header
        header_frame = ctk.CTkFrame(self.analyzer_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Content Analyzer", font=("Arial", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="Analyze your content for optimization opportunities", text_color="gray", font=("Arial", 10)).pack(anchor="w")
        
        # Input section
        input_frame = ctk.CTkFrame(self.analyzer_tab)
        input_frame.pack(fill="x", padx=15, pady=10)
        
        # Platform
        platform_frame = ctk.CTkFrame(input_frame)
        platform_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(platform_frame, text="Target Platform:", font=("Arial", 11)).pack(side="left", padx=5)
        self.analyzer_platform = ctk.CTkComboBox(
            platform_frame,
            values=["Instagram", "Facebook", "Twitter", "TikTok"],
            state="readonly",
            width=150
        )
        self.analyzer_platform.set("Instagram")
        self.analyzer_platform.pack(side="left", padx=5)
        
        # Content input
        content_frame = ctk.CTkFrame(input_frame)
        content_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(content_frame, text="Content to Analyze:", font=("Arial", 11)).pack(anchor="w", pady=3)
        self.analyzer_content = ctk.CTkTextbox(content_frame, height=100)
        self.analyzer_content.pack(fill="x")
        
        # Analyze button
        ctk.CTkButton(
            input_frame,
            text="🔍 Analyze Content",
            command=self._analyze_content,
            fg_color="blue",
            height=40
        ).pack(fill="x", pady=10)
        
        # Results section
        results_frame = ctk.CTkFrame(self.analyzer_tab)
        results_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        ctk.CTkLabel(results_frame, text="Analysis Results:", font=("Arial", 12, "bold")).pack(anchor="w", pady=5)
        
        self.analyzer_output = ctk.CTkTextbox(results_frame, height=200)
        self.analyzer_output.pack(fill="both", expand=True, pady=5)
    
    def _setup_recommendations_tab(self):
        """Setup recommendations tab"""
        # Header
        header_frame = ctk.CTkFrame(self.recommendations_tab)
        header_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(header_frame, text="Content Recommendations", font=("Arial", 16, "bold")).pack(anchor="w")
        ctk.CTkLabel(header_frame, text="AI-powered suggestions for your content strategy", text_color="gray", font=("Arial", 10)).pack(anchor="w")
        
        # Input section
        input_frame = ctk.CTkFrame(self.recommendations_tab)
        input_frame.pack(fill="x", padx=15, pady=10)
        
        # Platform
        platform_frame = ctk.CTkFrame(input_frame)
        platform_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(platform_frame, text="Platform:", font=("Arial", 11)).pack(side="left", padx=5)
        self.rec_platform = ctk.CTkComboBox(
            platform_frame,
            values=["Instagram", "Facebook", "Twitter", "TikTok"],
            state="readonly",
            width=150
        )
        self.rec_platform.set("Instagram")
        self.rec_platform.pack(side="left", padx=5)
        
        # Industry
        industry_frame = ctk.CTkFrame(input_frame)
        industry_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(industry_frame, text="Industry:", font=("Arial", 11)).pack(side="left", padx=5)
        self.rec_industry = ctk.CTkComboBox(
            industry_frame,
            values=["Tech", "Fashion", "Fitness", "Food", "Finance", "General"],
            state="readonly",
            width=150
        )
        self.rec_industry.set("Tech")
        self.rec_industry.pack(side="left", padx=5)
        
        # Get recommendations button
        ctk.CTkButton(
            input_frame,
            text="💡 Get Recommendations",
            command=self._get_recommendations,
            fg_color="blue",
            height=40
        ).pack(fill="x", pady=10)
        
        # Recommendations display
        rec_frame = ctk.CTkFrame(self.recommendations_tab)
        rec_frame.pack(fill="both", expand=True, padx=15, pady=10)
        
        rec_scroll = ctk.CTkScrollableFrame(rec_frame)
        rec_scroll.pack(fill="both", expand=True)
        
        self.recommendations_container = rec_scroll

    def _setup_remix_tab(self):
        """Setup Remix Lab tab UI"""
        main_frame = ctk.CTkFrame(self.remix_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        header = ctk.CTkLabel(
            main_frame,
            text="Remix Lab – turn one asset into many",
            font=("Arial", 16, "bold")
        )
        header.pack(anchor="w", pady=(0, 6))

        subheader = ctk.CTkLabel(
            main_frame,
            text="Paste a URL, drop a file, or type your script to generate platform-ready drafts.",
            text_color="gray"
        )
        subheader.pack(anchor="w")

        input_frame = ctk.CTkFrame(main_frame)
        input_frame.pack(fill="x", pady=10)

        # Source selection
        selection_frame = ctk.CTkFrame(input_frame)
        selection_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(selection_frame, text="Source Type:").pack(side="left", padx=5)

        self.remix_source_selector = ctk.CTkComboBox(
            selection_frame,
            values=["URL", "Text", "File"],
            state="readonly",
            width=120
        )
        self.remix_source_selector.set("URL")
        self.remix_source_selector.pack(side="left", padx=5)

        # URL input
        self.remix_url_entry = ctk.CTkEntry(input_frame, placeholder_text="https://youtube.com/... or TikTok link")
        self.remix_url_entry.pack(fill="x", padx=5, pady=5)

        # Text input
        self.remix_text_input = ctk.CTkTextbox(input_frame, height=120)
        self.remix_text_input.pack(fill="x", padx=5, pady=5)

        # File picker
        file_frame = ctk.CTkFrame(input_frame)
        file_frame.pack(fill="x", pady=5)
        ctk.CTkButton(file_frame, text="📁 Choose File", command=self._choose_remix_file, width=140).pack(side="left", padx=5)
        self.remix_file_label = ctk.CTkLabel(file_frame, text="No file selected", text_color="gray")
        self.remix_file_label.pack(side="left", padx=10)

        # Target platforms
        targets_frame = ctk.CTkFrame(main_frame)
        targets_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(targets_frame, text="Targets:", font=("Arial", 12, "bold")).pack(anchor="w", padx=5, pady=(0, 4))

        platform_row = ctk.CTkFrame(targets_frame)
        platform_row.pack(fill="x")
        self.remix_target_vars = {}
        target_names = [
            ("Instagram", True),
            ("TikTok", True),
            ("YouTube", False),
            ("LinkedIn", False),
            ("Twitter", False),
            ("Threads", False),
            ("Facebook", False),
            ("Pinterest", False),
        ]
        for name, default in target_names:
            var = ctk.BooleanVar(value=default)
            cb = ctk.CTkCheckBox(platform_row, text=name, variable=var)
            cb.pack(side="left", padx=4, pady=2)
            self.remix_target_vars[name.lower()] = var

        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", pady=10)
        ctk.CTkLabel(options_frame, text="Call-to-Action:").pack(anchor="w", padx=5)
        self.remix_cta_entry = ctk.CTkEntry(options_frame, placeholder_text="Drop your thoughts below ⬇️")
        self.remix_cta_entry.pack(fill="x", padx=5, pady=5)

        ctk.CTkButton(
            main_frame,
            text="🌀 Generate Remix",
            fg_color="#7C4DFF",
            command=self._generate_remix,
            height=45
        ).pack(fill="x", pady=5)

        # Output
        output_frame = ctk.CTkFrame(main_frame)
        output_frame.pack(fill="both", expand=True, pady=10)
        ctk.CTkLabel(output_frame, text="Outputs", font=("Arial", 12, "bold")).pack(anchor="w", padx=5, pady=5)

        self.remix_output = ctk.CTkTextbox(output_frame, height=260)
        self.remix_output.pack(fill="both", expand=True, padx=5, pady=5)

        history_label = ctk.CTkLabel(main_frame, text="Recent Remix Jobs", font=("Arial", 12, "bold"))
        history_label.pack(anchor="w", pady=(10, 0))

        self.remix_history_container = ctk.CTkScrollableFrame(main_frame, height=150)
        self.remix_history_container.pack(fill="both", expand=False, pady=5)
        self._render_remix_history()

    def _setup_video_tab(self):
        """Build faceless video lab tab."""
        main_frame = ctk.CTkFrame(self.video_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            main_frame,
            text="Faceless Video Lab",
            font=("Arial", 16, "bold")
        ).pack(anchor="w")

        ctk.CTkLabel(
            main_frame,
            text="Feed a script, pick a style, and auto-generate a short-form video with voiceover.",
            text_color="gray"
        ).pack(anchor="w", pady=(0, 10))

        input_frame = ctk.CTkFrame(main_frame)
        input_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(input_frame, text="Video Style:").pack(side="left", padx=5)
        styles = [style.title() for style in video_ai_generator.list_styles()]
        self.video_style_selector = ctk.CTkComboBox(
            input_frame,
            values=styles,
            state="readonly",
            width=160
        )
        self.video_style_selector.set(styles[0] if styles else "Motivation")
        self.video_style_selector.pack(side="left", padx=5)

        self.video_duration_label = ctk.CTkLabel(input_frame, text="Est. Duration: --")
        self.video_duration_label.pack(side="right", padx=5)

        options_frame = ctk.CTkFrame(main_frame)
        options_frame.pack(fill="x", pady=5)

        ctk.CTkLabel(options_frame, text="Voice:").pack(side="left", padx=5)
        self.video_voice_map = {}
        voice_profiles = video_ai_generator.list_voices()
        voice_labels = []
        for profile in voice_profiles:
            label = profile.get("label", profile.get("key", "Voice"))
            self.video_voice_map[label] = profile.get("key")
            voice_labels.append(label)
        if not voice_labels:
            voice_labels = ["Creator Female"]
            self.video_voice_map = {"Creator Female": "creator_female"}
        self.video_voice_selector = ctk.CTkComboBox(
            options_frame,
            values=voice_labels,
            state="readonly",
            width=200
        )
        self.video_voice_selector.set(voice_labels[0])
        self.video_voice_selector.pack(side="left", padx=5)

        try:
            self.video_subtitles_var = ctk.BooleanVar(value=True)
        except AttributeError:  # Fallback for older customtkinter
            import tkinter as tk
            self.video_subtitles_var = tk.BooleanVar(value=True)
        self.video_subtitle_check = ctk.CTkCheckBox(
            options_frame,
            text="Burn subtitles",
            variable=self.video_subtitles_var
        )
        self.video_subtitle_check.pack(side="left", padx=10)

        self.video_script_input = ctk.CTkTextbox(main_frame, height=220)
        self.video_script_input.pack(fill="both", expand=False, pady=10)
        self.video_script_input.insert(
            "1.0",
            "Hook your viewer with 3-6 short sentences. Each sentence becomes a beat in the video.\n"
            "Example: 'AI creators are scaling to $10k/month without showing their face.'"
        )

        button_frame = ctk.CTkFrame(main_frame)
        button_frame.pack(fill="x", pady=5)
        self.video_generate_btn = ctk.CTkButton(
            button_frame,
            text="🎬 Generate Video",
            fg_color="#FF6F61",
            command=self._generate_video,
            height=45
        )
        self.video_generate_btn.pack(fill="x")

        self.video_status_label = ctk.CTkLabel(main_frame, text="Idle", text_color="gray")
        self.video_status_label.pack(anchor="w", pady=(5, 0))

        output_frame = ctk.CTkFrame(main_frame)
        output_frame.pack(fill="both", expand=True, pady=10)
        ctk.CTkLabel(output_frame, text="Generation Output", font=("Arial", 12, "bold")).pack(anchor="w", padx=5, pady=5)

        self.video_output_text = ctk.CTkTextbox(output_frame, height=200)
        self.video_output_text.pack(fill="both", expand=True, padx=5, pady=5)

        self.video_open_button = ctk.CTkButton(
            main_frame,
            text="Open Video",
            state="disabled",
            command=self._open_generated_video
        )
        self.video_open_button.pack(fill="x", pady=(0, 10))
    
    # ===== ACTION HANDLERS =====
    
    def _generate_caption(self):
        """Generate caption using AI"""
        context = {
            "platform": self.caption_platform.get().lower(),
            "tone": self.caption_tone.get().lower(),
            "content_type": self.caption_type.get().lower(),
            "topic": self.caption_topic.get("1.0", "end-1c"),
            "max_length": 280 if self.caption_platform.get() == "Twitter" else 2200
        }
        
        caption = ai_engine.generate_caption(context)
        self.caption_output.delete("1.0", "end")
        self.caption_output.insert("1.0", caption)
    
    def _copy_caption(self):
        """Copy caption to clipboard"""
        caption = self.caption_output.get("1.0", "end-1c")
        self.copy_to_clipboard(caption)
    
    def _generate_hashtags(self):
        """Generate hashtags using AI"""
        context = {
            "platform": self.hashtag_platform.get().lower(),
            "topic": self.hashtag_topic.get(),
            "count": int(self.hashtag_count.get()),
            "trending": self.hashtag_trending.get()
        }
        
        hashtags = ai_engine.generate_hashtags(context)
        hashtag_text = " ".join(hashtags)
        
        self.hashtag_output.delete("1.0", "end")
        self.hashtag_output.insert("1.0", hashtag_text)
    
    def _copy_hashtags(self):
        """Copy hashtags to clipboard"""
        hashtags = self.hashtag_output.get("1.0", "end-1c")
        self.copy_to_clipboard(hashtags)
    
    def _predict_time(self):
        """Predict best posting time"""
        context = {
            "platform": self.time_platform.get().lower(),
            "audience": self.time_audience.get(),
            "content_type": self.time_type.get().lower(),
            "timezone": "UTC"
        }
        
        best_time, metadata = ai_engine.predict_best_time(context)
        
        self.best_time_result.configure(text=f"🕐 {best_time}")
        
        insights_text = f"""Peak Hours: {metadata.get('peak', 'N/A')}

Recommended Days:
{', '.join(metadata.get('days', []))}

Engagement Score: {metadata.get('engagement_score', 0)}/10

Tips:
• Post when your audience is most active
• Use scheduling tools for consistency
• Monitor analytics to refine timing
• Video content performs 2.3x better in peak hours"""
        
        self.time_insights.delete("1.0", "end")
        self.time_insights.insert("1.0", insights_text)
    
    def _analyze_content(self):
        """Analyze content"""
        content = self.analyzer_content.get("1.0", "end-1c")
        platform = self.analyzer_platform.get().lower()
        
        analysis = ai_engine.analyze_content(content, platform)
        
        analysis_text = f"""Content Analysis for {platform.upper()}

📊 Metrics:
  • Word Count: {analysis.get('word_count', 0)}
  • Character Count: {analysis.get('char_count', 0)} / {analysis.get('max_chars', 'N/A')}
  
✓ Features Detected:
  • Has CTA: {'Yes ✓' if analysis.get('has_cta') else 'No ✗'}
  • Has Hashtags: {'Yes ✓' if analysis.get('has_hashtags') else 'No ✗'}
  • Has Emojis: {'Yes ✓' if analysis.get('has_emojis') else 'No ✗'}

📈 Scores:
  • Length Score: {analysis.get('length_score', 0)}/10
  • CTA Score: {analysis.get('cta_score', 0)}/10
  • Hashtag Score: {analysis.get('hashtag_score', 0)}/10
  • Emoji Score: {analysis.get('emoji_score', 0)}/10
  
🎯 Overall Score: {analysis.get('overall_score', 0)}/10

💡 Suggestions:
{chr(10).join('  • ' + s for s in analysis.get('suggestions', []))}"""
        
        self.analyzer_output.delete("1.0", "end")
        self.analyzer_output.insert("1.0", analysis_text)
    
    def _get_recommendations(self):
        """Get content recommendations"""
        # Clear container
        for widget in self.recommendations_container.winfo_children():
            widget.destroy()
        
        context = {
            "platform": self.rec_platform.get().lower(),
            "industry": self.rec_industry.get().lower(),
            "audience_size": 10000
        }
        
        recommendations = ai_engine.get_content_recommendations(context)
        
        for rec in recommendations:
            card = ctk.CTkFrame(self.recommendations_container, fg_color="gray25")
            card.pack(fill="x", padx=5, pady=8)
            
            # Title
            ctk.CTkLabel(
                card,
                text=rec.get("type", ""),
                font=("Arial", 12, "bold")
            ).pack(anchor="w", padx=10, pady=(8, 3))
            
            # Description
            ctk.CTkLabel(
                card,
                text=rec.get("description", ""),
                text_color="gray",
                font=("Arial", 10)
            ).pack(anchor="w", padx=10, pady=3)
            
            # Stats
            stats_frame = ctk.CTkFrame(card)
            stats_frame.pack(fill="x", padx=10, pady=(3, 8))
            
            stats_text = f"🚀 +{rec.get('engagement_boost', '0%')} engagement | Effort: {rec.get('effort', 'N/A')} | Priority: {rec.get('priority', 'N/A')}"
            ctk.CTkLabel(
                stats_frame,
                text=stats_text,
                text_color="cyan",
                font=("Arial", 9)
            ).pack(anchor="w")

    # ===== Remix Tab Helpers =====

    def _choose_remix_file(self):
        """Prompt user to pick a file for remixing."""
        file_path = filedialog.askopenfilename(
            title="Select source document",
            filetypes=[
                ("Text files", "*.txt *.md"),
                ("Documents", "*.pdf *.docx"),
                ("All files", "*.*"),
            ]
        )
        if not file_path:
            return
        self.remix_file_path = file_path
        self.remix_file_label.configure(text=Path(file_path).name)

    def _generate_remix(self):
        """Run remix generation and show results."""
        source_type = self.remix_source_selector.get().lower()
        source_payload = {"type": "text", "value": ""}

        if source_type == "url":
            url = self.remix_url_entry.get().strip()
            if not url:
                messagebox.showerror("Missing URL", "Paste a URL to remix.")
                return
            source_payload = {"type": "url", "value": url}
        elif source_type == "file":
            if not self.remix_file_path:
                messagebox.showerror("Missing File", "Choose a file to remix.")
                return
            source_payload = {"type": "file", "value": self.remix_file_path}
        else:
            text_value = self.remix_text_input.get("1.0", "end-1c").strip()
            if not text_value:
                messagebox.showerror("Missing Text", "Enter some text to remix.")
                return
            source_payload = {"type": "text", "value": text_value}

        targets = [name for name, var in self.remix_target_vars.items() if var.get()]
        if not targets:
            targets = ["instagram", "tiktok", "twitter"]

        options = {"cta": self.remix_cta_entry.get().strip() or "Drop your thoughts below ⬇️"}

        try:
            job = remix_service.remix(source_payload, targets, options)
        except Exception as exc:
            messagebox.showerror("Remix failed", str(exc))
            return

        self._display_remix_output(job)
        messagebox.showinfo("Remix complete", "Drafts generated for selected platforms.")
        self._render_remix_history()

    def _generate_video(self):
        """Trigger faceless video generation in a background thread."""
        script = self.video_script_input.get("1.0", "end-1c").strip()
        if not script:
            messagebox.showerror("Missing Script", "Enter a script to convert into video.")
            return

        style = self.video_style_selector.get().lower()
        voice_label = self.video_voice_selector.get()
        voice_key = self.video_voice_map.get(voice_label, "creator_female")
        burn_subtitles = bool(self.video_subtitles_var.get())
        self.video_generate_btn.configure(state="disabled", text="Generating…")
        self.video_status_label.configure(text="Synthesizing voice + slides…", text_color="#00BCD4")
        self.video_output_text.delete("1.0", "end")
        threading.Thread(
            target=self._run_video_generation,
            args=(script, style, voice_key, burn_subtitles),
            daemon=True,
        ).start()

    def _run_video_generation(self, script: str, style: str, voice: str, burn_subtitles: bool):
        try:
            job = video_ai_generator.generate_video(script, style, voice=voice, burn_subtitles=burn_subtitles)
            self.after(0, lambda: self._handle_video_result(job, None))
        except Exception as exc:  # pragma: no cover - UI feedback
            self.after(0, lambda: self._handle_video_result(None, exc))

    def _handle_video_result(self, job, error):
        self.video_generate_btn.configure(state="normal", text="🎬 Generate Video")
        if error:
            self.video_status_label.configure(text=str(error), text_color="#FF6B6B")
            messagebox.showerror("Video generation failed", str(error))
            return

        self.generated_video_path = job.get("video_path")
        duration = sum(segment["duration"] for segment in job.get("segments", []))
        self.video_duration_label.configure(text=f"Est. Duration: {duration:.1f}s")
        status_note = f"Video ready • Voice: {job.get('voice', 'N/A')}"
        if job.get("subtitle_file"):
            status_note += " • Subtitles saved"
        self.video_status_label.configure(text=status_note, text_color="#51CF66")
        self.video_open_button.configure(state="normal")

        summary_lines = ["Segments:"]
        for idx, segment in enumerate(job.get("segments", []), start=1):
            summary_lines.append(f"  {idx}. {segment['duration']}s – {segment['text']}")
        summary_lines.append("")
        summary_lines.append(f"Video saved to: {self.generated_video_path}")
        if job.get("subtitle_file"):
            summary_lines.append(f"Subtitles (.srt): {job['subtitle_file']}")
        self.video_output_text.insert("1.0", "\n".join(summary_lines))

    def _open_generated_video(self):
        """Open the generated video using the OS default player."""
        if not self.generated_video_path:
            return
        path = Path(self.generated_video_path)
        if not path.exists():
            messagebox.showerror("Missing file", "Generated video file was not found.")
            return
        try:
            if sys.platform.startswith("win"):
                os.startfile(str(path))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.call(["open", str(path)])
            else:
                subprocess.call(["xdg-open", str(path)])
        except Exception as exc:
            messagebox.showerror("Unable to open", str(exc))

    def _display_remix_output(self, job):
        """Render remix results in the output textbox."""
        self.remix_output.delete("1.0", "end")
        for platform, data in job.outputs.items():
            header = f"## {platform.upper()}\n"
            body = data.get("content", data.get("error", "No content"))
            extra = data.get("metadata")
            if extra:
                body += f"\n\nMetadata: {extra}"
            self.remix_output.insert("end", header)
            self.remix_output.insert("end", body + "\n\n")

    def _render_remix_history(self):
        """Display recent remix jobs in history list."""
        for widget in self.remix_history_container.winfo_children():
            widget.destroy()

        history = remix_service.recent_jobs(limit=5)
        if not history:
            ctk.CTkLabel(
                self.remix_history_container,
                text="No remix jobs yet.",
                text_color="gray"
            ).pack(anchor="w", padx=5, pady=5)
            return

        for job in history:
            frame = ctk.CTkFrame(self.remix_history_container)
            frame.pack(fill="x", pady=4, padx=4)
            timestamp = job.get("created_at", "")
            source_type = job.get("source", {}).get("type", "text")
            targets = ", ".join(job.get("targets", []))
            label = ctk.CTkLabel(
                frame,
                text=f"{timestamp[:16]} • {source_type} → {targets}",
                font=("Arial", 10)
            )
            label.pack(anchor="w", padx=5, pady=3)
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
