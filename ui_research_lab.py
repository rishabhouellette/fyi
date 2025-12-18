"""Creative Research Lab UI (Phase 2)."""

from __future__ import annotations

import customtkinter as ctk
from tkinter import messagebox

from brand_kit_service import get_brand_kit_service
from creative_library import get_hook_prompt_library
from viral_inspiration_service import get_viral_inspiration_service


class CreativeResearchFrame(ctk.CTkFrame):
    """Data-backed ideation hub for Viral Inspiration + Prompt Library."""

    def __init__(self, parent, team_id: int = 1):
        super().__init__(parent)
        self.team_id = team_id
        self.inspiration_service = get_viral_inspiration_service()
        self.library = get_hook_prompt_library()
        self.brand_service = get_brand_kit_service()
        self._build_ui()

    # ------------------------------------------------------------------
    def _build_ui(self):
        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=10, pady=10)

        self.viral_tab = tabs.add("🔥 Viral Feed")
        self.hook_tab = tabs.add("🪝 Hook Lab")
        self.brand_tab = tabs.add("🎨 Brand Kits")

        self._build_viral_tab()
        self._build_hook_tab()
        self._build_brand_tab()

    # ------------------------------------------------------------------
    def _build_viral_tab(self):
        filter_frame = ctk.CTkFrame(self.viral_tab)
        filter_frame.pack(fill="x", padx=10, pady=10)

        niches = sorted({post.niche.title() for post in self.inspiration_service.posts}) or ["All"]
        platforms = sorted({post.platform.title() for post in self.inspiration_service.posts}) or ["All"]
        niches.insert(0, "All")
        platforms.insert(0, "All")

        ctk.CTkLabel(filter_frame, text="Niche:").pack(side="left", padx=5)
        self.viral_niche = ctk.CTkComboBox(filter_frame, values=niches, state="readonly", width=150)
        self.viral_niche.set(niches[0])
        self.viral_niche.pack(side="left", padx=5)

        ctk.CTkLabel(filter_frame, text="Platform:").pack(side="left", padx=5)
        self.viral_platform = ctk.CTkComboBox(filter_frame, values=platforms, state="readonly", width=150)
        self.viral_platform.set(platforms[0])
        self.viral_platform.pack(side="left", padx=5)

        ctk.CTkButton(
            filter_frame,
            text="Update Feed",
            command=self._render_viral_feed,
            width=140,
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            filter_frame,
            text="Inject Fresh Sample",
            command=self._refresh_sample,
            fg_color="#FF6F61",
        ).pack(side="left")

        self.viral_feed = ctk.CTkScrollableFrame(self.viral_tab, fg_color="transparent")
        self.viral_feed.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self._render_viral_feed()

    def _render_viral_feed(self):
        for widget in self.viral_feed.winfo_children():
            widget.destroy()

        posts = self.inspiration_service.get_trending(
            niche=self.viral_niche.get(),
            platform=self.viral_platform.get(),
            limit=8,
        )
        if not posts:
            ctk.CTkLabel(self.viral_feed, text="No data yet.", text_color="gray").pack(pady=20)
            return

        for post in posts:
            card = ctk.CTkFrame(self.viral_feed)
            card.pack(fill="x", padx=5, pady=6)

            header = f"{post.hook}"
            ctk.CTkLabel(card, text=header, font=("Arial", 13, "bold"), wraplength=560).pack(anchor="w", padx=10, pady=(8, 2))
            subtitle = f"{post.platform.title()} • {post.niche.title()} • by {post.creator}"
            ctk.CTkLabel(card, text=subtitle, text_color="gray", font=("Arial", 10)).pack(anchor="w", padx=10)
            ctk.CTkLabel(card, text=post.summary, wraplength=620, font=("Arial", 10)).pack(anchor="w", padx=10, pady=4)

            metrics_text = (
                f"👁️ {int(post.metrics.get('views', 0)):,}  |  ❤️ {int(post.metrics.get('likes', 0)):,}  |  "
                f"💬 {int(post.metrics.get('comments', 0)):,}  |  📌 Saves {int(post.metrics.get('saves', 0)):,}  |  "
                f"⚡ Engagement {post.metrics.get('engagement_rate', 0)*100:.1f}%"
            )
            ctk.CTkLabel(card, text=metrics_text, text_color="#00E0B8", font=("Arial", 10)).pack(anchor="w", padx=10, pady=(0, 8))

    def _refresh_sample(self):
        self.inspiration_service.refresh_sample_data()
        messagebox.showinfo("Viral Feed", "Sample refreshed. Showing latest records.")
        self._render_viral_feed()

    # ------------------------------------------------------------------
    def _build_hook_tab(self):
        top_frame = ctk.CTkFrame(self.hook_tab)
        top_frame.pack(fill="x", padx=10, pady=10)

        audiences = sorted({hook.audience.title() for hook in self.library.hooks}) or ["All"]
        use_cases = sorted({hook.use_case.title() for hook in self.library.hooks}) or ["All"]
        audiences.insert(0, "All")
        use_cases.insert(0, "All")

        ctk.CTkLabel(top_frame, text="Audience:").pack(side="left", padx=5)
        self.hook_audience = ctk.CTkComboBox(top_frame, values=audiences, state="readonly", width=150)
        self.hook_audience.set(audiences[0])
        self.hook_audience.pack(side="left", padx=5)

        ctk.CTkLabel(top_frame, text="Use Case:").pack(side="left", padx=5)
        self.hook_use_case = ctk.CTkComboBox(top_frame, values=use_cases, state="readonly", width=150)
        self.hook_use_case.set(use_cases[0])
        self.hook_use_case.pack(side="left", padx=5)

        ctk.CTkButton(top_frame, text="Show Hooks", command=self._render_hooks).pack(side="left", padx=10)

        self.hook_feed = ctk.CTkScrollableFrame(self.hook_tab, fg_color="transparent")
        self.hook_feed.pack(fill="both", expand=True, padx=10, pady=5)

        prompt_frame = ctk.CTkFrame(self.hook_tab)
        prompt_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(prompt_frame, text="Prompt Library", font=("Arial", 12, "bold")).pack(anchor="w")
        self.prompt_output = ctk.CTkTextbox(prompt_frame, height=140)
        self.prompt_output.pack(fill="x", pady=5)
        ctk.CTkButton(prompt_frame, text="List Prompts", command=self._render_prompts).pack(anchor="e")

        self._render_hooks()
        self._render_prompts()

    def _render_hooks(self):
        for widget in self.hook_feed.winfo_children():
            widget.destroy()

        hooks = self.library.list_hooks(
            audience=self.hook_audience.get(),
            use_case=self.hook_use_case.get(),
        )
        if not hooks:
            ctk.CTkLabel(self.hook_feed, text="No hooks yet.", text_color="gray").pack(pady=20)
            return

        for hook in hooks:
            frame = ctk.CTkFrame(self.hook_feed)
            frame.pack(fill="x", padx=5, pady=4)
            header = f"{hook.label} • {hook.audience.title()}"
            ctk.CTkLabel(frame, text=header, font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=(6, 2))
            ctk.CTkLabel(frame, text=hook.text, wraplength=640).pack(anchor="w", padx=10, pady=(0, 4))
            metric = f"Save Rate {hook.metrics.get('save_rate', 0)*100:.1f}% • Avg Watch {hook.metrics.get('avg_watch', 0)*100:.1f}%"
            ctk.CTkLabel(frame, text=metric, text_color="#00E0B8", font=("Arial", 9)).pack(anchor="w", padx=10, pady=(0, 6))

    def _render_prompts(self):
        prompts = self.library.list_prompts()
        lines = []
        for prompt in prompts:
            lines.append(f"[{prompt.goal.title()} | Tone: {prompt.tone}]\n{prompt.instruction}\nVariables: {', '.join(prompt.variables)}\n")
        if not lines:
            lines = ["No prompts stored yet."]
        self.prompt_output.delete("1.0", "end")
        self.prompt_output.insert("1.0", "\n".join(lines))

    # ------------------------------------------------------------------
    def _build_brand_tab(self):
        wrapper = ctk.CTkFrame(self.brand_tab)
        wrapper.pack(fill="both", expand=True, padx=10, pady=10)

        kits = self.brand_service.list_kits(self.team_id)
        kit_names = [kit.name for kit in kits]
        if not kit_names:
            kit_names = ["No kits configured"]
        state = "readonly" if kits else "disabled"
        self.brand_selector = ctk.CTkComboBox(
            wrapper,
            values=kit_names,
            state=state,
            width=220,
        )
        default_label = kit_names[0]
        self.brand_selector.set(default_label)
        self.brand_selector.pack(anchor="w", pady=5)
        if kits:
            self.brand_selector.bind("<<ComboboxSelected>>", lambda _e: self._render_brand_kit())

        self.brand_detail = ctk.CTkFrame(wrapper)
        self.brand_detail.pack(fill="both", expand=True, pady=10)

        stock_frame = ctk.CTkFrame(wrapper)
        stock_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(stock_frame, text="Stock Lookup", font=("Arial", 12, "bold")).pack(anchor="w")
        self.stock_query = ctk.CTkEntry(stock_frame, placeholder_text="Search Pexels (workspace, creator, fitness...)" )
        self.stock_query.pack(fill="x", pady=5)
        ctk.CTkButton(stock_frame, text="Search", command=self._search_stock).pack(anchor="e")
        self.stock_results = ctk.CTkFrame(stock_frame)
        self.stock_results.pack(fill="x", pady=5)

        self._render_brand_kit()

    def _render_brand_kit(self):
        for widget in self.brand_detail.winfo_children():
            widget.destroy()
        kits = {kit.name: kit for kit in self.brand_service.list_kits(self.team_id)}
        selected = kits.get(self.brand_selector.get())
        if not selected:
            ctk.CTkLabel(self.brand_detail, text="No brand kits configured.").pack(pady=20)
            return

        ctk.CTkLabel(self.brand_detail, text=selected.name, font=("Arial", 14, "bold")).pack(anchor="w", padx=10, pady=(6, 2))
        ctk.CTkLabel(self.brand_detail, text=selected.voice_notes, wraplength=600).pack(anchor="w", padx=10, pady=(0, 8))

        color_frame = ctk.CTkFrame(self.brand_detail)
        color_frame.pack(fill="x", padx=10, pady=5)
        for label, color in [
            ("Primary", selected.primary_color),
            ("Secondary", selected.secondary_color),
            ("Accent", selected.accent_color),
        ]:
            swatch = ctk.CTkFrame(color_frame, width=120, height=50, fg_color=color)
            swatch.pack(side="left", padx=6, pady=5)
            swatch.pack_propagate(False)
            ctk.CTkLabel(swatch, text=f"{label}\n{color}", text_color="#FFFFFF").pack(expand=True)

        font_text = "Fonts: " + ", ".join(selected.fonts)
        ctk.CTkLabel(self.brand_detail, text=font_text).pack(anchor="w", padx=10, pady=(5, 0))

    def _search_stock(self):
        query = self.stock_query.get().strip() or "workspace"
        assets = self.brand_service.search_stock(query)
        for widget in self.stock_results.winfo_children():
            widget.destroy()
        if not assets:
            ctk.CTkLabel(self.stock_results, text="No stock assets found.").pack()
            return
        for asset in assets:
            frame = ctk.CTkFrame(self.stock_results)
            frame.pack(fill="x", padx=4, pady=4)
            meta = f"#{asset.get('id')} • {asset.get('type', '').title()}"
            ctk.CTkLabel(frame, text=meta, font=("Arial", 10, "bold")).pack(anchor="w", padx=8)
            ctk.CTkLabel(frame, text=asset.get("preview", ""), text_color="#00BFA6", font=("Arial", 10)).pack(anchor="w", padx=8, pady=(0, 4))
            photographer = asset.get("photographer") or asset.get("url", "")
            ctk.CTkLabel(frame, text=str(photographer), text_color="gray", font=("Arial", 9)).pack(anchor="w", padx=8, pady=(0, 6))
