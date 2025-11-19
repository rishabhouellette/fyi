"""
Premium Theme Manager - Futuristic Dark and Red/Black Light Modes
Provides cyberpunk-inspired dark theme and aggressive red/black light theme
"""

class ThemeManager:
    """Manage application themes"""
    
    # ========== DARK MODE (Cyberpunk/Premium) ==========
    DARK_MODE = {
        "name": "dark",
        "bg_primary": "#0a0a0a",      # Pure black background
        "bg_secondary": "#2a2a4e",    # Slightly brighter navy for better contrast
        "bg_tertiary": "#16213e",     # Darker navy
        "accent_primary": "#00d4ff",  # Neon cyan (cyberpunk)
        "accent_secondary": "#0099ff", # Neon blue
        "accent_danger": "#ff0055",   # Neon pink/red
        "accent_success": "#00ff88",  # Neon green
        "accent_warning": "#ffaa00",  # Neon orange
        "text_primary": "#ffffff",    # Pure white
        "text_secondary": "#a0a0a0",  # Dim gray
        "text_tertiary": "#707070",   # Dark gray
        "sidebar_bg": "#0d0d1a",      # Pure black sidebar
        "sidebar_hover": "#2a2a4e",   # Brighter for buttons
        "card_bg": "#0f1525",         # Card background
        "border": "#00d4ff",          # Neon border
        "header_bg": "#0a0a14",       # Header background
    }
    
    # ========== LIGHT MODE (Red/Black Aggressive) ==========
    LIGHT_MODE = {
        "name": "light",
        "bg_primary": "#ffffff",      # Pure white background
        "bg_secondary": "#f5f5f5",    # Light gray
        "bg_tertiary": "#efefef",     # Slightly darker gray
        "accent_primary": "#dc2626",  # Aggressive red
        "accent_secondary": "#991b1b", # Dark red
        "accent_danger": "#1f1f1f",   # Pure black for danger
        "accent_success": "#059669",  # Dark green
        "accent_warning": "#d97706",  # Dark orange
        "text_primary": "#000000",    # Pure black
        "text_secondary": "#4a4a4a",  # Dark gray
        "text_tertiary": "#808080",   # Medium gray
        "sidebar_bg": "#1a1a1a",      # Pure black sidebar (contrast)
        "sidebar_hover": "#333333",   # Lighter gray for buttons (more visible)
        "card_bg": "#f9f9f9",         # Slightly off-white
        "border": "#dc2626",          # Red border
        "header_bg": "#000000",       # Black header
    }
    
    @staticmethod
    def get_theme(mode="dark"):
        """Get theme based on mode"""
        if mode.lower() == "light":
            return ThemeManager.LIGHT_MODE
        return ThemeManager.DARK_MODE
    
    @staticmethod
    def apply_dark_mode():
        """Apply dark mode theme"""
        import customtkinter as ctk
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")
    
    @staticmethod
    def apply_light_mode():
        """Apply light mode theme"""
        import customtkinter as ctk
        ctk.set_appearance_mode("Light")
        ctk.set_default_color_theme("red")


# Singleton instance
_theme_manager = None

def get_theme_manager():
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager
