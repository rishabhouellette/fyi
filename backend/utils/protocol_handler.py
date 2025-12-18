"""
FYI Social ∞ - Protocol Handler Registration
Registers fyi:// custom protocol for OAuth callbacks
Eliminates need for ngrok/tunneling!
"""

import sys
import os
import subprocess
from pathlib import Path

from backend.config import get_config

config = get_config()


class ProtocolHandler:
    """Register custom protocol handler for fyi://"""
    
    PROTOCOL = "fyi"
    
    @staticmethod
    def is_registered() -> bool:
        """Check if protocol handler is already registered"""
        if sys.platform == 'win32':
            return ProtocolHandler._is_registered_windows()
        elif sys.platform == 'darwin':
            return ProtocolHandler._is_registered_macos()
        else:
            return ProtocolHandler._is_registered_linux()
    
    @staticmethod
    def register():
        """Register the protocol handler"""
        if sys.platform == 'win32':
            ProtocolHandler._register_windows()
        elif sys.platform == 'darwin':
            ProtocolHandler._register_macos()
        else:
            ProtocolHandler._register_linux()
    
    @staticmethod
    def unregister():
        """Unregister the protocol handler"""
        if sys.platform == 'win32':
            ProtocolHandler._unregister_windows()
        elif sys.platform == 'darwin':
            ProtocolHandler._unregister_macos()
        else:
            ProtocolHandler._unregister_linux()
    
    # ========================================================================
    # WINDOWS
    # ========================================================================
    
    @staticmethod
    def _is_registered_windows() -> bool:
        """Check if registered on Windows"""
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{ProtocolHandler.PROTOCOL}", 0, winreg.KEY_READ)
            winreg.CloseKey(key)
            return True
        except:
            return False
    
    @staticmethod
    def _register_windows():
        """Register protocol on Windows"""
        try:
            import winreg
            
            # Get executable path
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
            else:
                exe_path = sys.executable
                script_path = config.PROJECT_DIR / "main.py"
                exe_path = f'"{exe_path}" "{script_path}"'
            
            # Create registry keys
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{ProtocolHandler.PROTOCOL}")
            winreg.SetValue(key, "", winreg.REG_SZ, f"URL:{ProtocolHandler.PROTOCOL} Protocol")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
            
            # Set command
            command_key = winreg.CreateKey(key, "shell\\open\\command")
            winreg.SetValue(command_key, "", winreg.REG_SZ, f'{exe_path} "%1"')
            
            winreg.CloseKey(command_key)
            winreg.CloseKey(key)
            
            print(f"✅ Registered {ProtocolHandler.PROTOCOL}:// protocol handler")
            
        except Exception as e:
            print(f"⚠️ Failed to register protocol handler: {e}")
    
    @staticmethod
    def _unregister_windows():
        """Unregister protocol on Windows"""
        try:
            import winreg
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{ProtocolHandler.PROTOCOL}\\shell\\open\\command")
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{ProtocolHandler.PROTOCOL}\\shell\\open")
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{ProtocolHandler.PROTOCOL}\\shell")
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, f"Software\\Classes\\{ProtocolHandler.PROTOCOL}")
        except:
            pass
    
    # ========================================================================
    # MACOS
    # ========================================================================
    
    @staticmethod
    def _is_registered_macos() -> bool:
        """Check if registered on macOS"""
        # TODO: Implement macOS detection
        return False
    
    @staticmethod
    def _register_macos():
        """Register protocol on macOS"""
        print("⚠️ macOS protocol registration not yet implemented")
        print("   OAuth will use localhost:5000 callback instead")
    
    @staticmethod
    def _unregister_macos():
        """Unregister protocol on macOS"""
        pass
    
    # ========================================================================
    # LINUX
    # ========================================================================
    
    @staticmethod
    def _is_registered_linux() -> bool:
        """Check if registered on Linux"""
        desktop_file = Path.home() / ".local/share/applications/fyi-social.desktop"
        return desktop_file.exists()
    
    @staticmethod
    def _register_linux():
        """Register protocol on Linux"""
        try:
            # Get executable path
            if getattr(sys, 'frozen', False):
                exe_path = sys.executable
            else:
                exe_path = f'{sys.executable} {config.PROJECT_DIR / "main.py"}'
            
            # Create .desktop file
            desktop_dir = Path.home() / ".local/share/applications"
            desktop_dir.mkdir(parents=True, exist_ok=True)
            
            desktop_file = desktop_dir / "fyi-social.desktop"
            
            content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=FYI Social Infinity
Comment=Social Media Management Tool
Exec={exe_path} %u
Icon=application-x-executable
Terminal=false
MimeType=x-scheme-handler/{ProtocolHandler.PROTOCOL};
"""
            
            desktop_file.write_text(content)
            
            # Update MIME database
            subprocess.run(['xdg-mime', 'default', 'fyi-social.desktop', f'x-scheme-handler/{ProtocolHandler.PROTOCOL}'])
            
            print(f"✅ Registered {ProtocolHandler.PROTOCOL}:// protocol handler")
            
        except Exception as e:
            print(f"⚠️ Failed to register protocol handler: {e}")
    
    @staticmethod
    def _unregister_linux():
        """Unregister protocol on Linux"""
        try:
            desktop_file = Path.home() / ".local/share/applications/fyi-social.desktop"
            if desktop_file.exists():
                desktop_file.unlink()
        except:
            pass


def register_protocol_handler():
    """Convenience function to register protocol handler"""
    handler = ProtocolHandler()
    if not handler.is_registered():
        handler.register()
    else:
        print(f"✓ {ProtocolHandler.PROTOCOL}:// protocol already registered")
