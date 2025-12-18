"""
FYI Social ∞ - Desktop Application
Native desktop window wrapper for the web interface
"""

import webview
import subprocess
import time
import socket
from pathlib import Path
import sys
import os

# Add project to path
PROJECT_DIR = Path(__file__).parent
VENV_PYTHON = PROJECT_DIR / "venv" / "Scripts" / "python.exe"

def is_server_ready(port=8081, timeout=30):
    """Check if server is ready to accept connections"""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            if result == 0:
                return True
        except:
            pass
        time.sleep(0.5)
    return False

def main_desktop():
    """Launch desktop application"""
    
    print("=" * 60)
    print("FYI Social ∞ - Desktop Application")
    print("=" * 60)
    print()
    
    # Start server in background process
    print("[1/3] Starting backend server on port 8081...")
    env = os.environ.copy()
    env['NICEGUI_NO_BROWSER'] = '1'
    env['NICEGUI_PORT'] = '8081'
    
    server_process = subprocess.Popen(
        [str(VENV_PYTHON), "main.py"],
        env=env,
        cwd=str(PROJECT_DIR),
        creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
    )
    
    # Wait for server to be ready
    print("[2/3] Waiting for server to be ready...")
    if not is_server_ready(8081, timeout=30):
        print("ERROR: Server failed to start!")
        server_process.terminate()
        input("Press Enter to exit...")
        sys.exit(1)
    
    print("[3/3] Opening desktop window...")
    time.sleep(1)
    
    # Create native desktop window
    try:
        window = webview.create_window(
            'FYI Social ∞ - Desktop',
            'http://localhost:8081',
            width=1400,
            height=900,
            resizable=True,
            fullscreen=False,
            min_size=(1024, 768),
            background_color='#000000',
            text_select=True
        )
        
        print()
        print("✓ Desktop window opened successfully!")
        print("  Close the window to shut down the app")
        print()
        
        # Start the desktop window (blocking)
        webview.start(debug=False)
        
    finally:
        # Clean up server process
        print("Shutting down server...")
        server_process.terminate()
        server_process.wait(timeout=5)
        print("✓ Shutdown complete")

if __name__ == '__main__':
    try:
        main_desktop()
    except KeyboardInterrupt:
        print("\nShutdown requested...")
    except Exception as e:
        print(f"\nERROR: {e}")
        input("Press Enter to exit...")
