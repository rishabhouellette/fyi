"""Authorable Theme Studio tab for FYI Uploader."""

from __future__ import annotations

import customtkinter as ctk
from tkinter import colorchooser, messagebox
from typing import Dict

from theme_manager import get_theme_manager


class ThemeStudioTab(ctk.CTkFrame):
    """Interactive panel for editing theme overrides."""

    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.theme_manager = get_theme_manager()
        self.mode_var = ctk.StringVar(value="dark")
        self.scope_var = ctk.StringVar(value="global")
        self.platform_var = ctk.StringVar(value=self.theme_manager.PLATFORM_CHOICES[0])
        self.entries: Dict[str, ctk.CTkEntry] = {}
        self.preview_frame = None
        self._build_layout()
        self._refresh_fields()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_layout(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 0))
        ctk.CTkLabel(
            header,
            text="🎨 Theme Studio",
            font=("Helvetica", 20, "bold")
        ).pack(anchor="w")
        ctk.CTkLabel(
            header,
            text=(
                "Create custom palettes for dark/light mode and override accents per platform. "
                "Saved colors persist for the entire desktop app and the compact mode window."
            ),
            font=("Helvetica", 12),
            text_color="#9ca3af",
            justify="left",
        ).pack(anchor="w", pady=(4, 12))

        control_frame = ctk.CTkFrame(self)
        control_frame.pack(fill="x", pady=5)
        ctk.CTkLabel(control_frame, text="Theme Mode:").grid(row=0, column=0, sticky="w", padx=6, pady=6)
        mode_selector = ctk.CTkSegmentedButton(
            control_frame,
            values=["dark", "light"],
            variable=self.mode_var,
            command=lambda _: self._refresh_fields(),
        )
        mode_selector.grid(row=0, column=1, padx=6, pady=6, sticky="w")

        ctk.CTkLabel(control_frame, text="Override Scope:").grid(row=1, column=0, sticky="w", padx=6, pady=6)
        scope_selector = ctk.CTkSegmentedButton(
            control_frame,
            values=["global", "platform"],
            variable=self.scope_var,
            command=lambda _: self._refresh_fields(),
        )
        scope_selector.grid(row=1, column=1, padx=6, pady=6, sticky="w")

        platform_frame = ctk.CTkFrame(self)
        platform_frame.pack(fill="x", pady=(4, 12))
        ctk.CTkLabel(platform_frame, text="Platform override target:").pack(side="left", padx=6, pady=8)
        platform_combo = ctk.CTkComboBox(
            platform_frame,
            values=list(self.theme_manager.PLATFORM_CHOICES),
            variable=self.platform_var,
            command=lambda _: self._refresh_fields(),
            state="readonly",
            width=200,
        )
        platform_combo.pack(side="left", padx=6)

        self.form_frame = ctk.CTkFrame(self)
        self.form_frame.pack(fill="both", expand=True, padx=4, pady=8)
        self._build_form_fields()

        action_frame = ctk.CTkFrame(self)
        action_frame.pack(fill="x", pady=(8, 0))
        ctk.CTkButton(
            action_frame,
            text="💾 Save overrides",
            command=self._save_overrides,
            fg_color="#0ea5e9",
        ).pack(side="left", padx=8, pady=8)
        ctk.CTkButton(
            action_frame,
            text="↩ Reset to defaults",
            command=self._reset_overrides,
            fg_color="#fb7185",
        ).pack(side="left", padx=8, pady=8)

        self.preview_frame = ctk.CTkFrame(self, corner_radius=14, border_width=2)
        self.preview_frame.pack(fill="x", pady=(12, 16), padx=4)
        self.preview_header = ctk.CTkLabel(
            self.preview_frame,
            text="Preview",
            font=("Helvetica", 14, "bold"),
        )
        self.preview_header.pack(anchor="w", padx=16, pady=(10, 4))
        self.preview_body = ctk.CTkLabel(
            self.preview_frame,
            text="Buttons, tabs, and compact mode widgets adopt these colors.",
            font=("Helvetica", 12),
            justify="left",
        )
        self.preview_body.pack(anchor="w", padx=16, pady=(0, 12))

    def _build_form_fields(self):
        for child in self.form_frame.winfo_children():
            child.destroy()
        self.entries.clear()
        for idx, field in enumerate(self.theme_manager.EDITABLE_FIELDS):
            row_frame = ctk.CTkFrame(self.form_frame)
            row_frame.pack(fill="x", pady=4, padx=8)
            ctk.CTkLabel(row_frame, text=field, width=130, anchor="w").pack(side="left", padx=6)
            entry = ctk.CTkEntry(row_frame, width=200)
            entry.pack(side="left", padx=6)
            self.entries[field] = entry
            ctk.CTkButton(
                row_frame,
                text="Pick",
                width=70,
                command=lambda f=field: self._open_color_picker(f),
            ).pack(side="left", padx=6)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _current_selection(self):
        scope = self.scope_var.get()
        platform = self.platform_var.get() if scope == "platform" else None
        return {
            "mode": self.mode_var.get(),
            "scope": scope,
            "platform": platform,
        }

    def _refresh_fields(self):
        selection = self._current_selection()
        theme = self.theme_manager.get_theme(selection["mode"], selection["platform"])
        for field, entry in self.entries.items():
            entry.delete(0, "end")
            entry.insert(0, theme.get(field, ""))
        self._update_preview(theme)

    def _open_color_picker(self, field):
        initial = self.entries[field].get()
        chosen, _ = colorchooser.askcolor(color=initial or "#ffffff")
        if chosen:
            hex_value = "#%02x%02x%02x" % tuple(int(v) for v in chosen)
            self.entries[field].delete(0, "end")
            self.entries[field].insert(0, hex_value)
            self._update_preview_from_entries()

    def _collect_entry_values(self) -> Dict[str, str]:
        values = {}
        for field, entry in self.entries.items():
            value = entry.get().strip()
            if value:
                if not value.startswith("#") or len(value) not in (4, 7):
                    raise ValueError(f"{field} must be a hex color (e.g., #ff00ff)")
                values[field] = value
        return values

    def _save_overrides(self):
        selection = self._current_selection()
        try:
            values = self._collect_entry_values()
        except ValueError as exc:
            messagebox.showerror("Invalid color", str(exc))
            return
        self.theme_manager.save_overrides(
            mode=selection["mode"],
            scope=selection["scope"],
            platform=selection["platform"],
            values=values,
        )
        self._update_preview_from_entries()
        if hasattr(self.controller, "apply_runtime_theme"):
            self.controller.apply_runtime_theme()
        messagebox.showinfo("Theme Studio", "Overrides saved and applied.")

    def _reset_overrides(self):
        selection = self._current_selection()
        self.theme_manager.reset_overrides(
            mode=selection["mode"],
            scope=selection["scope"],
            platform=selection["platform"],
        )
        self._refresh_fields()
        if hasattr(self.controller, "apply_runtime_theme"):
            self.controller.apply_runtime_theme()
        messagebox.showinfo("Theme Studio", "Overrides cleared; defaults restored.")

    def _update_preview_from_entries(self):
        values = {field: entry.get() for field, entry in self.entries.items()}
        self._update_preview(values)

    def _update_preview(self, theme):
        if not self.preview_frame:
            return
        border_color = theme.get("border", "#0ea5e9")
        accent = theme.get("accent_primary", "#0ea5e9")
        bg = theme.get("bg_primary", "#0f172a")
        text = theme.get("text_primary", "#f8fafc")
        secondary = theme.get("text_secondary", "#9ca3af")
        self.preview_frame.configure(border_color=border_color, fg_color=bg)
        self.preview_header.configure(text_color=accent)
        self.preview_body.configure(text_color=secondary)
        if hasattr(self.controller, "preview_theme"):
            self.controller.preview_theme(theme)
*** End of File