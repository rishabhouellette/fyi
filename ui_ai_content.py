"""
AI-Powered Content Generation UI for FYI Platform
Caption generation, hashtag suggestions, best time prediction, content analysis
"""
import customtkinter as ctk
from datetime import datetime
from ai_engine import get_ai_engine
from database_manager import get_db_manager

db_manager = get_db_manager()
ai_engine = get_ai_engine()


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
    
    def copy_to_clipboard(self, text):
        """Copy text to clipboard"""
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        root.clipboard_clear()
        root.clipboard_append(text)
        root.update()
        root.destroy()
