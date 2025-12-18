"""Central theme management with persistence and per-platform accents."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Dict, Optional


class ThemeManager:
    """Manage application themes and authorable overrides."""

    DATA_DIR = Path(__file__).resolve().parent / "data"
    OVERRIDES_FILE = DATA_DIR / "themes.json"
    EDITABLE_FIELDS = (
        "bg_primary",
        "bg_secondary",
        "bg_tertiary",
        "card_bg",
        "accent_primary",
        "accent_secondary",
        "accent_success",
        "accent_warning",
        "accent_danger",
        "text_primary",
        "text_secondary",
        "border",
    )
    PLATFORM_CHOICES = ("Facebook", "Instagram", "YouTube", "LinkedIn", "TikTok")

    # ========== DARK MODE (Cyberpunk/Premium) ==========
    DARK_MODE = {
        "name": "dark",
        "bg_primary": "#0a0a0a",
        "bg_secondary": "#2a2a4e",
        "bg_tertiary": "#16213e",
        "accent_primary": "#00d4ff",
        "accent_secondary": "#0099ff",
        "accent_danger": "#ff0055",
        "accent_success": "#00ff88",
        "accent_warning": "#ffaa00",
        "text_primary": "#ffffff",
        "text_secondary": "#a0a0a0",
        "text_tertiary": "#707070",
        "sidebar_bg": "#0d0d1a",
        "sidebar_hover": "#2a2a4e",
        "card_bg": "#0f1525",
        "border": "#00d4ff",
        "header_bg": "#0a0a14",
    }

    # ========== LIGHT MODE (Red/Black Aggressive) ==========
    LIGHT_MODE = {
        "name": "light",
        "bg_primary": "#ffffff",
        "bg_secondary": "#f5f5f5",
        "bg_tertiary": "#efefef",
        "accent_primary": "#dc2626",
        "accent_secondary": "#991b1b",
        "accent_danger": "#1f1f1f",
        "accent_success": "#059669",
        "accent_warning": "#d97706",
        "text_primary": "#000000",
        "text_secondary": "#4a4a4a",
        "text_tertiary": "#808080",
        "sidebar_bg": "#1a1a1a",
        "sidebar_hover": "#333333",
        "card_bg": "#f9f9f9",
        "border": "#dc2626",
        "header_bg": "#000000",
    }

    def __init__(self):
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._overrides = self._load_overrides()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_theme(self, mode: str = "dark", platform: Optional[str] = None) -> Dict[str, str]:
        """Return merged theme dictionary for the given mode/platform."""

        mode_key = (mode or "dark").lower()
        base = copy.deepcopy(self.DARK_MODE if mode_key == "dark" else self.LIGHT_MODE)
        overrides = self._overrides.get("global", {}).get(mode_key, {})
        if overrides:
            base.update(overrides)
        if platform:
            platform_key = str(platform).lower()
            platform_overrides = (
                self._overrides.get("platforms", {})
                .get(platform_key, {})
                .get(mode_key, {})
            )
            if platform_overrides:
                base.update(platform_overrides)
        return base

    def list_platforms(self):
        return self.PLATFORM_CHOICES

    def save_overrides(
        self,
        *,
        mode: str,
        values: Dict[str, str],
        scope: str = "global",
        platform: Optional[str] = None,
    ) -> None:
        """Persist overrides for the given scope/mode."""

        mode_key = (mode or "dark").lower()
        scope_key = (scope or "global").lower()
        valid_values = {
            field: value
            for field, value in values.items()
            if field in self.EDITABLE_FIELDS and value
        }
        if scope_key == "platform":
            if not platform:
                raise ValueError("Platform override requires platform name")
            platform_key = platform.lower()
            platforms = self._overrides.setdefault("platforms", {})
            plat_block = platforms.setdefault(platform_key, {})
            plat_block[mode_key] = valid_values
        else:
            global_block = self._overrides.setdefault("global", {})
            global_block[mode_key] = valid_values
        self._write_overrides()

    def reset_overrides(self, *, mode: str, scope: str = "global", platform: Optional[str] = None) -> None:
        mode_key = (mode or "dark").lower()
        scope_key = (scope or "global").lower()
        if scope_key == "platform" and platform:
            platform_key = platform.lower()
            try:
                self._overrides["platforms"][platform_key].pop(mode_key, None)
                if not self._overrides["platforms"][platform_key]:
                    self._overrides["platforms"].pop(platform_key, None)
            except KeyError:
                return
        else:
            try:
                self._overrides["global"].pop(mode_key, None)
            except KeyError:
                return
        self._write_overrides()

    @staticmethod
    def apply_dark_mode():
        import customtkinter as ctk

        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

    @staticmethod
    def apply_light_mode():
        import customtkinter as ctk

        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("red")

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------
    def _load_overrides(self) -> Dict[str, Dict]:
        try:
            with self.OVERRIDES_FILE.open("r", encoding="utf-8") as fp:
                data = json.load(fp)
                if isinstance(data, dict):
                    return data
        except FileNotFoundError:
            pass
        except Exception:  # pragma: no cover - defensive read path
            pass
        return {"global": {}, "platforms": {}}

    def _write_overrides(self) -> None:
        payload = json.dumps(self._overrides, indent=2)
        self.OVERRIDES_FILE.write_text(payload, encoding="utf-8")


# Singleton instance
_theme_manager = None


def get_theme_manager():
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
