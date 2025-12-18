"""Compact mode window with collapsible sections for platform controls."""

from __future__ import annotations

import customtkinter as ctk


class CollapsibleSection(ctk.CTkFrame):
    """Simple collapsible container used by compact mode."""

    def __init__(self, parent, title: str):
        super().__init__(parent, fg_color="#111827", corner_radius=12, border_width=1)
        self._body_visible = True
        self.header = ctk.CTkButton(
            self,
            text=f"▼  {title}",
            fg_color="#1f2937",
            hover_color="#111827",
            corner_radius=12,
            command=self.toggle,
            font=("Helvetica", 14, "bold"),
        )
        self.header.pack(fill="x", padx=4, pady=4)
        self.body = ctk.CTkFrame(self, fg_color="#0f172a", corner_radius=10)
        self.body.pack(fill="x", padx=8, pady=(0, 10))

    def toggle(self):
        self._body_visible = not self._body_visible
        symbol = "▼" if self._body_visible else "▶"
        existing_text = self.header.cget("text")
        self.header.configure(text=f"{symbol}{existing_text[1:]}")
        if self._body_visible:
            self.body.pack(fill="x", padx=8, pady=(0, 10))
        else:
            self.body.pack_forget()


class CompactModeWindow(ctk.CTkToplevel):
    """Standalone compact layout optimized for sub-1000px screens."""

    def __init__(self, controller):
        super().__init__(controller)
        self.controller = controller
        self.title("FYI Uploader – Compact Mode")
        self.geometry("900x620")
        self.minsize(720, 520)
        self.configure(fg_color="#0b1120")
        self.protocol("WM_DELETE_WINDOW", self.close)

        header = ctk.CTkFrame(self, fg_color="#0f172a")
        header.pack(fill="x", pady=(10, 4), padx=10)
        ctk.CTkLabel(
            header,
            text="Compact command center",
            font=("Helvetica", 20, "bold"),
            text_color="#38bdf8",
        ).pack(side="left", padx=6, pady=6)
        ctk.CTkButton(
            header,
            text="↩ Return to full UI",
            command=self.close,
            fg_color="#fb7185",
        ).pack(side="right", padx=6, pady=6)

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="#0b1120")
        self.scroll.pack(fill="both", expand=True, padx=10, pady=(0, 12))

        for platform in ("Facebook", "Instagram", "YouTube"):
            section = CollapsibleSection(self.scroll, platform)
            section.pack(fill="x", pady=6)
            self._populate_platform_section(section.body, platform)

        footer = ctk.CTkFrame(self, fg_color="#0f172a")
        footer.pack(fill="x", padx=10, pady=(0, 10))
        self.queue_label = ctk.CTkLabel(
            footer,
            text="Queue: 0 videos",
            font=("Helvetica", 12),
            text_color="#e5e7eb",
        )
        self.queue_label.pack(side="left", padx=10, pady=8)
        ctk.CTkButton(
            footer,
            text="Add Videos",
            command=lambda: controller._shortcut_add_videos(platform=controller._active_platform_safe()),
            fg_color="#0ea5e9",
        ).pack(side="right", padx=6, pady=8)
        self.refresh_queue_summary()

    def _populate_platform_section(self, body, platform: str):
        info = ctk.CTkLabel(
            body,
            text=f"Active Platform: {platform}",
            font=("Helvetica", 12),
            text_color="#a5b4fc",
        )
        info.pack(anchor="w", padx=12, pady=(10, 6))

        button_frame = ctk.CTkFrame(body, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=(0, 12))

        ctk.CTkButton(
            button_frame,
            text="📁 Add Videos",
            command=lambda p=platform: self.controller._shortcut_add_videos(platform=p),
            fg_color="#0ea5e9",
        ).pack(fill="x", pady=4)
        ctk.CTkButton(
            button_frame,
            text="⚡ Instant Upload",
            command=lambda p=platform: self.controller.fb_scheduler(p),
            fg_color="#f97316",
        ).pack(fill="x", pady=4)
        ctk.CTkButton(
            button_frame,
            text="🧠 Smart Scheduler",
            command=lambda p=platform: self.controller.smart_scheduler(p),
            fg_color="#a855f7",
        ).pack(fill="x", pady=4)
        ctk.CTkButton(
            button_frame,
            text="🔗 Link Account",
            command=lambda p=platform.lower(): self.controller.link_account(p),
            fg_color="#22c55e",
        ).pack(fill="x", pady=4)
        ctk.CTkButton(
            button_frame,
            text="🔄 Refresh Accounts",
            command=lambda: self.controller._shortcut_refresh_accounts(),
            fg_color="#14b8a6",
        ).pack(fill="x", pady=4)

    def refresh_queue_summary(self):
        queue_len = len(getattr(self.controller, "video_queue", []))
        self.queue_label.configure(text=f"Queue: {queue_len} video(s)")

    def close(self):
        if hasattr(self.controller, "_exit_compact_mode"):
            self.controller._exit_compact_mode()
        else:
            self.destroy()
*** End of File