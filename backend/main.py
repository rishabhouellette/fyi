"""
FYI Social ∞ - Unified Backend Entry Point
Single file that handles:
- API server (Flask)
- NiceGUI web interface
- Tauri bridge
- OAuth flows
- Database management
"""

import sys
import os
from pathlib import Path

# Add backend to path
BACKEND_DIR = Path(__file__).parent
sys.path.insert(0, str(BACKEND_DIR.parent))

from backend.config import get_config, AppMode
from backend.database import get_database
from backend.services.local_oauth import get_oauth_server
from backend.services.oauth_registry import get_oauth_registry
from backend.services.byok_manager import get_byok_manager
from backend.utils.protocol_handler import register_protocol_handler

# Initialize config first
config = get_config()


def start_api_server():
    """Start Flask API server for OAuth and API endpoints"""
    oauth_server = get_oauth_server()
    oauth_server.start()
    
    print(f"✅ API Server running on http://localhost:{config.API_PORT}")
    print(f"   OAuth callbacks: https://127.0.0.1:{config.API_PORT}/oauth/callback")


def start_nicegui_interface():
    """Start NiceGUI web interface"""
    from nicegui import ui
    
    # Import the main UI app
    sys.path.insert(0, str(config.PROJECT_DIR))
    from main import FYISocialInfinity
    
    app_instance = FYISocialInfinity()
    
    @ui.page('/')
    def main_page():
        app_instance.run()
    
    show_browser = not config.is_desktop_mode()
    port = config.get_port()
    
    print(f"✅ NiceGUI Interface starting on http://localhost:{port}")
    
    ui.run(
        title='FYI Social ∞',
        dark=True,
        reload=False,
        show=show_browser,
        port=port,
        favicon='🚀'
    )


def start_hybrid_mode():
    """Start both API and NiceGUI"""
    import threading
    
    # Start API server in background
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()
    
    # Start NiceGUI in main thread
    start_nicegui_interface()


def initialize_backend():
    """Initialize backend services"""
    print("=" * 60)
    print("FYI Social ∞ - Backend Initialization")
    print("=" * 60)
    print()
    
    # Initialize database
    db = get_database()
    print(f"✅ Database initialized: {config.DB_PATH}")
    
    # Register protocol handler (for OAuth)
    register_protocol_handler()
    
    # Initialize OAuth registry
    oauth_registry = get_oauth_registry()
    print(f"✅ OAuth registry initialized")
    
    # Initialize BYOK manager
    byok_manager = get_byok_manager()
    configured_services = byok_manager.list_configured_services()
    if configured_services:
        print(f"✅ API keys configured for: {', '.join(configured_services.values())}")
    
    print()
    print(f"Mode: {config.mode.value}")
    print(f"Port: {config.get_port()}")
    print()


def main():
    """Main entry point"""
    # Initialize backend
    initialize_backend()
    
    # Start appropriate mode
    if config.mode == AppMode.API:
        start_api_server()
        # Keep running
        import time
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Shutting down...")
    
    elif config.mode == AppMode.WEB or config.mode == AppMode.DESKTOP:
        # Start API server in background for OAuth
        import threading
        api_thread = threading.Thread(target=start_api_server, daemon=True)
        api_thread.start()
        
        # Start NiceGUI interface
        start_nicegui_interface()
    
    elif config.mode == AppMode.HYBRID:
        start_hybrid_mode()


if __name__ == "__main__":
    main()
