"""Automation Intelligence Lab UI for Phase 3."""

from __future__ import annotations

import customtkinter as ctk
from tkinter import filedialog, messagebox

from ai_engine import get_ai_engine
from automation_insights import get_auto_scheduler
from viral_coach import get_viral_coach

ai_engine = get_ai_engine()
auto_scheduler = get_auto_scheduler()
viral_coach = get_viral_coach()


class AutomationIntelligenceFrame(ctk.CTkFrame):
    """Dashboard for smart scheduling, recycling, generators, and coaching."""

    def __init__(self, parent, team_id: int = 1):
        super().__init__(parent)
        self.team_id = team_id
        self._build_ui()

    def _build_ui(self):
        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=10, pady=10)

        self.timing_tab = tabs.add("Smart Timing")
        self.recycling_tab = tabs.add("Recycling")
        self.generators_tab = tabs.add("Generators")
        self.coach_tab = tabs.add("Viral Coach")

        self._build_timing_tab()
        self._build_recycling_tab()
        self._build_generators_tab()
        self._build_coach_tab()

    # ------------------------------------------------------------------
    def _build_timing_tab(self):
        control = ctk.CTkFrame(self.timing_tab)
        control.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(control, text="Platform:").pack(side="left", padx=5)
        self.timing_platform = ctk.CTkComboBox(control, values=["All", "facebook", "instagram", "tiktok", "twitter"], state="readonly", width=160)
        self.timing_platform.set("All")
        self.timing_platform.pack(side="left", padx=5)
        ctk.CTkButton(control, text="Refresh Insights", command=self._refresh_timing).pack(side="left", padx=10)
        ctk.CTkButton(control, text="Generate Auto Queue", command=self._suggest_queue).pack(side="left")

        self.timing_results = ctk.CTkFrame(self.timing_tab)
        self.timing_results.pack(fill="both", expand=True, padx=10, pady=5)
        self.queue_box = ctk.CTkTextbox(self.timing_tab, height=120)
        self.queue_box.pack(fill="x", padx=10, pady=(0, 10))
        self._refresh_timing()

    def _refresh_timing(self):
        for widget in self.timing_results.winfo_children():
            widget.destroy()
        platform = self.timing_platform.get()
        windows = auto_scheduler.best_windows(platform=None if platform == "All" else platform)
        if not windows:
            ctk.CTkLabel(self.timing_results, text="No scheduling data yet.", text_color="gray").pack(pady=30)
            return
        for slot in windows:
            card = ctk.CTkFrame(self.timing_results)
            card.pack(fill="x", padx=5, pady=4)
            label = f"{slot['weekday']} @ {slot['hour']:02d}:00 — Confidence {slot['score']} (samples {slot['samples']})"
            ctk.CTkLabel(card, text=label, font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=6)

    def _suggest_queue(self):
        platform = self.timing_platform.get()
        platform_key = None if platform == "All" else platform
        queue = auto_scheduler.auto_reschedule(platform=platform_key or "instagram")
        if not queue:
            self.queue_box.delete("1.0", "end")
            self.queue_box.insert("1.0", "No scheduling data available yet.")
            return
        lines = []
        for item in queue:
            lines.append(
                f"{item['weekday']} {item['scheduled_at'][:16]} • confidence {item['confidence']}"
            )
        self.queue_box.delete("1.0", "end")
        self.queue_box.insert("1.0", "\n".join(lines))

    # ------------------------------------------------------------------
    def _build_recycling_tab(self):
        header = ctk.CTkFrame(self.recycling_tab)
        header.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(header, text="Top performers ready to recycle", font=("Arial", 13, "bold")).pack(anchor="w")
        ctk.CTkButton(header, text="Refresh", command=self._refresh_recycling).pack(anchor="e")

        self.recycling_results = ctk.CTkFrame(self.recycling_tab)
        self.recycling_results.pack(fill="both", expand=True, padx=10, pady=5)
        self._refresh_recycling()

    def _refresh_recycling(self):
        for widget in self.recycling_results.winfo_children():
            widget.destroy()
        queue = auto_scheduler.recycling_queue()
        if not queue:
            ctk.CTkLabel(self.recycling_results, text="No recycled posts recommended yet.", text_color="gray").pack(pady=25)
            return
        for item in queue:
            frame = ctk.CTkFrame(self.recycling_results)
            frame.pack(fill="x", padx=5, pady=5)
            title = f"{item['title']} ({item['platform']})"
            ctk.CTkLabel(frame, text=title, font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=(6, 2))
            details = f"Score {item['score']} • Suggest rerun on {item['suggested_date']}"
            ctk.CTkLabel(frame, text=details, text_color="#00E0B8").pack(anchor="w", padx=10)
            ctk.CTkLabel(frame, text=item['recommendation']).pack(anchor="w", padx=10, pady=(0, 6))

    # ------------------------------------------------------------------
    def _build_generators_tab(self):
        columns = ctk.CTkFrame(self.generators_tab)
        columns.pack(fill="both", expand=True, padx=10, pady=10)

        # Thread generator
        thread_frame = ctk.CTkFrame(columns)
        thread_frame.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(thread_frame, text="Thread Generator", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=5)
        self.thread_topic = ctk.CTkEntry(thread_frame, placeholder_text="Topic (eg. 5-step automation playbook)")
        self.thread_topic.pack(fill="x", padx=10, pady=5)
        self.thread_audience = ctk.CTkEntry(thread_frame, placeholder_text="Audience (eg. SaaS founders)")
        self.thread_audience.pack(fill="x", padx=10, pady=5)
        self.thread_beats = ctk.CTkEntry(thread_frame, placeholder_text="Beats (default 7)")
        self.thread_beats.pack(fill="x", padx=10, pady=5)
        self.thread_output = ctk.CTkTextbox(thread_frame, height=220)
        self.thread_output.pack(fill="both", expand=True, padx=10, pady=5)
        ctk.CTkButton(thread_frame, text="Generate Thread", command=self._generate_thread).pack(fill="x", padx=10, pady=5)

        # Carousel generator
        carousel_frame = ctk.CTkFrame(columns)
        carousel_frame.pack(side="left", fill="both", expand=True, padx=5)
        ctk.CTkLabel(carousel_frame, text="Carousel Generator", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=5)
        self.carousel_topic = ctk.CTkEntry(carousel_frame, placeholder_text="Topic (eg. Failed hooks to avoid)")
        self.carousel_topic.pack(fill="x", padx=10, pady=5)
        self.carousel_slides = ctk.CTkEntry(carousel_frame, placeholder_text="Slides (default 5)")
        self.carousel_slides.pack(fill="x", padx=10, pady=5)
        self.carousel_tone = ctk.CTkEntry(carousel_frame, placeholder_text="Tone (bold, friendly, etc)")
        self.carousel_tone.pack(fill="x", padx=10, pady=5)
        self.carousel_output = ctk.CTkTextbox(carousel_frame, height=220)
        self.carousel_output.pack(fill="both", expand=True, padx=10, pady=5)
        ctk.CTkButton(carousel_frame, text="Generate Carousel", command=self._generate_carousel).pack(fill="x", padx=10, pady=5)

    def _generate_thread(self):
        topic = self.thread_topic.get().strip()
        if not topic:
            messagebox.showerror("Missing topic", "Enter a topic to generate thread outline.")
            return
        beats = self.thread_beats.get().strip()
        try:
            beats_val = int(beats) if beats else 7
        except ValueError:
            beats_val = 7
        outline = ai_engine.generate_thread_outline(topic, audience=self.thread_audience.get().strip() or "general", beats=beats_val)
        text = [f"{step['step']}. {step['headline']}\n{step['detail']}" for step in outline["outline"]]
        self.thread_output.delete("1.0", "end")
        self.thread_output.insert("1.0", "\n\n".join(text))

    def _generate_carousel(self):
        topic = self.carousel_topic.get().strip()
        if not topic:
            messagebox.showerror("Missing topic", "Enter a topic for the carousel.")
            return
        try:
            slides = int(self.carousel_slides.get().strip() or 5)
        except ValueError:
            slides = 5
        result = ai_engine.generate_carousel_outline(topic, slides=slides, tone=self.carousel_tone.get().strip() or "bold")
        text = []
        for slide in result["slides"]:
            text.append(f"Slide {slide['slide']}: {slide['headline']}\n- " + "\n- ".join(slide['bullets']))
        self.carousel_output.delete("1.0", "end")
        self.carousel_output.insert("1.0", "\n\n".join(text))

    # ------------------------------------------------------------------
    def _build_coach_tab(self):
        layout = ctk.CTkFrame(self.coach_tab)
        layout.pack(fill="both", expand=True, padx=10, pady=10)

        script_frame = ctk.CTkFrame(layout)
        script_frame.pack(fill="both", expand=True, padx=5, pady=5)
        ctk.CTkLabel(script_frame, text="Script Review", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=5)
        self.coach_script_input = ctk.CTkTextbox(script_frame, height=150)
        self.coach_script_input.pack(fill="both", expand=True, padx=10, pady=5)
        self.coach_script_output = ctk.CTkTextbox(script_frame, height=140)
        self.coach_script_output.pack(fill="both", expand=True, padx=10, pady=5)
        ctk.CTkButton(script_frame, text="Evaluate Script", command=self._review_script).pack(anchor="e", padx=10, pady=5)

        video_frame = ctk.CTkFrame(layout)
        video_frame.pack(fill="both", expand=True, padx=5, pady=5)
        ctk.CTkLabel(video_frame, text="Video Diagnostics", font=("Arial", 12, "bold")).pack(anchor="w", padx=10, pady=5)
        self.video_path_entry = ctk.CTkEntry(video_frame, placeholder_text="Choose a video file")
        self.video_path_entry.pack(fill="x", padx=10, pady=5)
        ctk.CTkButton(video_frame, text="Browse", command=self._pick_video).pack(anchor="w", padx=10)
        self.video_report = ctk.CTkTextbox(video_frame, height=120)
        self.video_report.pack(fill="both", expand=True, padx=10, pady=5)
        ctk.CTkButton(video_frame, text="Run Validator", command=self._run_video_review).pack(anchor="e", padx=10, pady=5)

    def _review_script(self):
        script = self.coach_script_input.get("1.0", "end-1c")
        report = viral_coach.review_script(script)
        if "error" in report:
            messagebox.showerror("Script", report["error"])
            return
        lines = [f"Hook: {report['scores']['hook']}", f"Pacing: {report['scores']['pacing']}", f"Clarity: {report['scores']['clarity']}", f"CTA: {report['scores']['cta']}"]
        lines.append("\nSuggestions:")
        lines.extend([f"- {s}" for s in report["suggestions"]])
        self.coach_script_output.delete("1.0", "end")
        self.coach_script_output.insert("1.0", "\n".join(lines))

    def _pick_video(self):
        path = filedialog.askopenfilename(title="Select video", filetypes=[("Video", "*.mp4 *.mov *.mkv"), ("All", "*.*")])
        if path:
            self.video_path_entry.delete(0, "end")
            self.video_path_entry.insert(0, path)

    def _run_video_review(self):
        path = self.video_path_entry.get().strip()
        report = viral_coach.review_video(path)
        if "error" in report and not report.get("info"):
            messagebox.showerror("Video", report["error"])
            return
        lines = [f"Valid: {report['valid']}" if 'valid' in report else ""]
        if report.get("error"):
            lines.append(f"Error: {report['error']}")
        info = report.get("info", {})
        for key, value in info.items():
            lines.append(f"{key}: {value}")
        self.video_report.delete("1.0", "end")
        self.video_report.insert("1.0", "\n".join(line for line in lines if line))
