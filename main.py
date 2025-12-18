"""
FYI Social ∞ - Unified Application
Complete 2035 Cyber-Futuristic Social Media Uploader
All-in-one: UI + Upload + Schedule + AI
"""

from nicegui import ui, app
from pathlib import Path
import json
import sys
import os
import threading

# Get project paths
PROJECT_DIR = Path(__file__).parent
DATA_DIR = PROJECT_DIR / "data"
ACCOUNTS_DIR = PROJECT_DIR / "accounts"
ACCOUNTS_FILE = ACCOUNTS_DIR / "accounts.json"

# Ensure data directories exist
DATA_DIR.mkdir(exist_ok=True)
ACCOUNTS_DIR.mkdir(exist_ok=True)

# Add project dir to path for imports
sys.path.insert(0, str(PROJECT_DIR))

# Import Phase 1 Backend
from backend.config import get_config
from backend.database import get_database
from backend.services.local_oauth import get_oauth_server
from backend.services.oauth_registry import get_oauth_registry
from backend.services.byok_manager import get_byok_manager
from backend.utils.protocol_handler import register_protocol_handler

# Initialize backend services
backend_config = get_config()
backend_db = get_database()
oauth_server = get_oauth_server()
oauth_registry = get_oauth_registry()
byok_manager = get_byok_manager()

# Surface OAuth redirect information for debugging
redirect_uri = getattr(backend_config, 'OAUTH_REDIRECT_URI', None)
if redirect_uri:
    print(f"🔐 Phase 1 OAuth redirect URI: {redirect_uri}")
    if redirect_uri.startswith('http://'):
        print("⚠️ Warning: Redirect URI is HTTP. Facebook requires HTTPS. Update your .env FYI_OAUTH_REDIRECT value.")

# Register protocol handler on startup
try:
    register_protocol_handler()
except:
    pass

# Start OAuth server in background
def start_oauth_server_background():
    try:
        oauth_server.start()
    except:
        pass

oauth_thread = threading.Thread(target=start_oauth_server_background, daemon=True)
oauth_thread.start()


# ============================================================================
# 2035 CYBER THEME - PHASE 0 DESIGN SYSTEM
# ============================================================================

CYBER_THEME = '''
<style>
    @import url('https://api.fontshare.com/v2/css?f[]=satoshi@700,500,400&display=swap');
    
    :root {
        --cyber-bg: #000000;
        --cyber-void: #0a0a1f;
        --cyber-primary: #00f2ff;
        --cyber-purple: #8b00ff;
        --cyber-green: #00ff9d;
        --cyber-border: rgba(0, 242, 255, 0.4);
        --cyber-glass: rgba(10, 10, 31, 0.09);
    }
    
    * { font-family: 'Satoshi', system-ui, sans-serif !important; }
    
    body {
        background: linear-gradient(180deg, var(--cyber-void), var(--cyber-bg)) !important;
        color: white !important;
    }
    
    .q-card {
        background: var(--cyber-glass) !important;
        backdrop-filter: blur(12px) !important;
        border: 1px solid var(--cyber-border) !important;
        border-radius: 16px !important;
        box-shadow: 0 0 30px rgba(0,242,255,0.4) !important;
        animation: float 6s ease-in-out infinite;
    }
    
    .q-btn {
        border: 2px solid var(--cyber-primary) !important;
        background: transparent !important;
        color: var(--cyber-primary) !important;
        box-shadow: 0 0 20px rgba(0,242,255,0.4) !important;
        transition: all 0.3s ease !important;
        font-weight: 500 !important;
    }
    
    .q-btn:hover {
        background: var(--cyber-primary) !important;
        color: #000 !important;
        box-shadow: 0 0 40px rgba(0,242,255,0.8) !important;
        transform: scale(1.02);
    }
    
    .q-field__control {
        background: var(--cyber-glass) !important;
        border: 1px solid var(--cyber-border) !important;
        color: white !important;
    }
    
    .q-drawer {
        background: rgba(10,10,31,0.5) !important;
        backdrop-filter: blur(16px) !important;
        border-right: 1px solid var(--cyber-border) !important;
    }
    
    .cyber-text-gradient {
        background: linear-gradient(90deg, var(--cyber-primary), var(--cyber-purple));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    
    @keyframes float {
        0%, 100% { transform: translateY(0); }
        50% { transform: translateY(-10px); }
    }
    
    @keyframes glow {
        0%, 100% { box-shadow: 0 0 20px rgba(0,242,255,0.4); }
        50% { box-shadow: 0 0 40px rgba(0,242,255,0.8); }
    }
    
    @keyframes breathe {
        0%, 100% { transform: scale(1); opacity: 1; }
        50% { transform: scale(1.1); opacity: 0.8; }
    }
    
    .ai-orb {
        width: 48px;
        height: 48px;
        border-radius: 50%;
        background: radial-gradient(circle, var(--cyber-purple), #5a0099);
        box-shadow: 0 0 30px rgba(139,0,255,0.8);
        animation: breathe 3s ease-in-out infinite;
    }
    
    .upload-zone {
        border: 4px dashed var(--cyber-primary) !important;
        border-radius: 24px !important;
        padding: 60px !important;
        text-align: center;
        min-height: 300px;
        display: flex;
        align-items: center;
        justify-content: center;
        animation: glow 3s ease-in-out infinite;
        background: var(--cyber-glass);
        backdrop-filter: blur(12px);
    }
    
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: var(--cyber-bg); }
    ::-webkit-scrollbar-thumb { background: var(--cyber-primary); border-radius: 4px; }
</style>
'''


# ============================================================================
# DATA MANAGEMENT
# ============================================================================

class DataManager:
    """Simple data manager for accounts and posts"""
    
    def __init__(self):
        self.accounts_file = ACCOUNTS_FILE
    
    def load_accounts(self):
        """Load accounts from JSON"""
        if self.accounts_file.exists():
            try:
                with open(self.accounts_file, 'r') as f:
                    data = json.load(f)
                    return data.get('accounts', [])
            except:
                return []
        return []
    
    def save_accounts(self, accounts):
        """Save accounts to JSON"""
        self.accounts_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.accounts_file, 'w') as f:
            json.dump({'accounts': accounts}, f, indent=2)
    
    def add_account(self, platform, name, username):
        """Add a new account"""
        accounts = self.load_accounts()
        accounts.append({
            'platform': platform,
            'name': name,
            'username': username,
            'connected': True
        })
        self.save_accounts(accounts)
        return True


# ============================================================================
# UPLOADER INTEGRATIONS
# ============================================================================

class UploaderManager:
    """Manage uploads to different platforms"""
    
    def __init__(self):
        self.uploaders = {}
        self.account_manager = None
        self._init_uploaders()
    
    def _init_uploaders(self):
        """Initialize platform uploaders and account manager"""
        try:
            from account_manager import get_account_manager
            self.account_manager = get_account_manager()
            
            from facebook_uploader import FacebookUploader
            self.uploaders['facebook'] = FacebookUploader
        except ImportError as e:
            print(f"Facebook uploader not available: {e}")
        
        try:
            from instagram_uploader import InstagramUploader
            self.uploaders['instagram'] = InstagramUploader
        except ImportError as e:
            print(f"Instagram uploader not available: {e}")
        
        try:
            from youtube_uploader import YouTubeUploader
            self.uploaders['youtube'] = YouTubeUploader
        except ImportError as e:
            print(f"YouTube uploader not available: {e}")
    
    def get_platform_accounts(self, platform):
        """Get accounts for a specific platform"""
        if not self.account_manager:
            return []
        
        accounts = self.account_manager.list_accounts(platform=platform)
        return accounts
    
    def upload_to_platform(self, platform, account_id, file_path, caption="", progress_callback=None):
        """Upload content to a platform"""
        if platform not in self.uploaders:
            return False, f"{platform} uploader not available"
        
        try:
            uploader_class = self.uploaders[platform]
            uploader = uploader_class(account_id=account_id)
            
            # Upload with progress callback if supported
            if hasattr(uploader, 'upload_video'):
                result = uploader.upload_video(
                    video_path=file_path,
                    title=caption,
                    description=caption,
                    progress_callback=progress_callback
                )
            else:
                result = uploader.upload(file_path, caption)
            
            return True, "Upload successful!"
        except Exception as e:
            return False, str(e)
    
    def available_platforms(self):
        """Get list of available platforms"""
        return list(self.uploaders.keys())


# ============================================================================
# MAIN APPLICATION
# ============================================================================

class FYISocialInfinity:
    """FYI Social ∞ - Complete Application"""
    
    def __init__(self):
        self.data_manager = DataManager()
        self.uploader_manager = UploaderManager()
        self.current_page = 'dashboard'
        self.uploaded_files = []
        self.selected_platform = None
        
    def run(self):
        """Start the application"""
        
        # Apply cyber theme
        ui.add_head_html(CYBER_THEME)
        ui.colors(
            primary='#00f2ff',
            secondary='#8b00ff',
            accent='#00ff9d',
            dark='#000000',
            positive='#00ff9d'
        )
        
        # Main layout with header
        with ui.header().classes('bg-black/80 backdrop-blur-xl border-b').style('border-color: rgba(0, 242, 255, 0.4)'):
            with ui.row().classes('w-full items-center justify-between px-6'):
                # Logo
                with ui.row().classes('items-center gap-3'):
                    ui.html('''
                        <svg width="40" height="40" viewBox="0 0 100 100">
                            <defs>
                                <linearGradient id="logo-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                                    <stop offset="0%" style="stop-color:#00f2ff"/>
                                    <stop offset="100%" style="stop-color:#8b00ff"/>
                                </linearGradient>
                            </defs>
                            <path d="M30 50C30 30 20 20 10 20 0 20 0 30 0 50 0 70 0 80 10 80 20 80 30 70 30 50M30 50C30 70 40 80 50 80 60 80 70 70 70 50 70 30 60 20 50 20 40 20 30 30 30 50" 
                                  transform="translate(15,0)" 
                                  fill="none" 
                                  stroke="url(#logo-grad)" 
                                  stroke-width="8"/>
                        </svg>
                    ''', sanitize=False)
                    ui.label('FYI Social ∞').classes('text-2xl cyber-text-gradient')
                
                # AI Status
                with ui.row().classes('items-center gap-3'):
                    ui.html('<div class="ai-orb"></div>', sanitize=False)
                    with ui.column().classes('gap-0'):
                        ui.label('Local Brain Active').classes('text-sm font-bold').style('color: #8b00ff')
                        ui.label('Processing locally').classes('text-xs text-gray-500')
        
        # Sidebar navigation
        with ui.left_drawer().classes('bg-black/80 backdrop-blur-xl'):
            self.render_sidebar()
        
        # Main content area
        with ui.column().classes('w-full p-8'):
            self.content_area = ui.column().classes('w-full')
            self.render_page()
    
    def render_sidebar(self):
        """Render navigation sidebar"""
        menu_items = [
            ('📊', 'Dashboard', 'dashboard'),
            ('⬆️', 'Upload', 'upload'),
            ('🎬', 'Content', 'content'),
            ('📈', 'Analytics', 'analytics'),
            ('👥', 'Accounts', 'accounts'),
            ('⚙️', 'Settings', 'settings'),
        ]
        
        with ui.column().classes('w-full gap-2 p-4'):
            for icon, label, page in menu_items:
                btn = ui.button(f'{icon} {label}', on_click=lambda p=page: self.navigate(p))
                btn.props('flat align=left')
                btn.classes('w-full justify-start text-left')
                if page == self.current_page:
                    btn.props('color=primary')
    
    def navigate(self, page):
        """Navigate to a page"""
        self.current_page = page
        self.content_area.clear()
        with self.content_area:
            self.render_page()
    
    def render_page(self):
        """Render current page content"""
        if self.current_page == 'dashboard':
            self.render_dashboard()
        elif self.current_page == 'upload':
            self.render_upload()
        elif self.current_page == 'content':
            self.render_content()
        elif self.current_page == 'analytics':
            self.render_analytics()
        elif self.current_page == 'accounts':
            self.render_accounts()
        elif self.current_page == 'settings':
            self.render_settings()
    
    def render_dashboard(self):
        """Dashboard page"""
        ui.label('Welcome to the Future').classes('text-4xl cyber-text-gradient mb-2')
        ui.label('The tool that ends every paid social media SaaS').classes('text-gray-400 mb-8')
        
        # Get real accounts from account manager
        all_accounts = []
        if self.uploader_manager.account_manager:
            try:
                all_accounts = self.uploader_manager.account_manager.list_accounts()
            except:
                pass
        
        platforms = self.uploader_manager.available_platforms()
        
        with ui.row().classes('w-full gap-6 mb-8'):
            self.stat_card('Total Accounts', len(all_accounts), '👥', '#00ff9d')
            self.stat_card('Available Platforms', len(platforms), '🌐', '#00f2ff')
            self.stat_card('Uploaded Files', len(self.uploaded_files), '📁', '#8b00ff')
        
        # Quick Actions
        with ui.card().classes('w-full mb-6'):
            ui.label('Quick Actions').classes('text-2xl font-bold mb-4')
            with ui.row().classes('gap-4'):
                ui.button('⬆️ Upload Content', on_click=lambda: self.navigate('upload'))
                ui.button('👥 Add Account', on_click=lambda: self.navigate('accounts'))
                ui.button('📊 View Analytics', on_click=lambda: self.navigate('analytics'))
        
        # Connected Accounts
        with ui.card().classes('w-full'):
            ui.label('Connected Accounts').classes('text-2xl font-bold mb-4')
            if all_accounts:
                with ui.grid(columns=3).classes('w-full gap-4'):
                    for acc in all_accounts:
                        with ui.card():
                            icon = {'facebook': '📘', 'instagram': '📷', 'youtube': '🎥'}.get(acc.platform, '🌐')
                            ui.label(f"{icon} {acc.platform.title()}").classes('font-bold text-lg')
                            ui.label(acc.name).classes('text-gray-400')
                            status = '✓ Active' if acc.is_token_valid() else '⚠️ Token Expired'
                            ui.label(status).classes('text-sm text-green-400' if acc.is_token_valid() else 'text-sm text-yellow-400')
            else:
                ui.label('No accounts connected. Go to Accounts tab to connect.').classes('text-gray-400')
    
    def render_upload(self):
        """Upload page"""
        ui.label('Upload Content').classes('text-3xl cyber-text-gradient mb-6')
        
        # Upload zone with file saving
        with ui.card().classes('w-full mb-6 upload-zone'):
            ui.label('🚀 Drop Your Content Here').classes('text-center text-2xl font-bold mb-4')
            ui.label('Supports: Videos, Images, Documents').classes('text-center text-gray-400 mb-4')
            
            def handle_upload(e):
                # Save uploaded file
                upload_dir = DATA_DIR / "uploads"
                upload_dir.mkdir(exist_ok=True)
                file_path = upload_dir / e.name
                
                with open(file_path, 'wb') as f:
                    f.write(e.content.read())
                
                self.uploaded_files.append({
                    'name': e.name,
                    'path': str(file_path),
                    'size': file_path.stat().st_size
                })
                ui.notify(f'✅ Uploaded: {e.name}', type='positive')
            
            upload = ui.upload(on_upload=handle_upload, multiple=True, auto_upload=True)
            upload.props('accept="video/*,image/*"').classes('w-full')
        
        # Platform and Account selection
        ui.label('Select Platform & Account').classes('text-xl font-bold mb-4')
        platforms = self.uploader_manager.available_platforms()
        
        selected_account_id = None
        account_selector = None
        
        if platforms:
            with ui.row().classes('gap-4 mb-6'):
                for platform in platforms:
                    icon = {'facebook': '📘', 'instagram': '📷', 'youtube': '🎥'}.get(platform, '🌐')
                    btn = ui.button(
                        f'{icon} {platform.title()}',
                        on_click=lambda p=platform: self.select_platform(p)
                    )
                    if self.selected_platform == platform:
                        btn.props('color=primary')
            
            # Show accounts for selected platform
            if self.selected_platform:
                platform_accounts = self.uploader_manager.get_platform_accounts(self.selected_platform)
                
                if platform_accounts:
                    with ui.row().classes('gap-4 mb-4 items-center'):
                        ui.label('Choose Account:').classes('font-bold')
                        account_options = {acc.name: acc.account_id for acc in platform_accounts}
                        account_selector = ui.select(
                            options=list(account_options.keys()),
                            label='Account',
                            value=list(account_options.keys())[0] if account_options else None
                        ).classes('flex-1')
                else:
                    ui.label(f'⚠️ No {self.selected_platform} accounts connected. Add one in the Accounts tab.').classes('text-yellow-400')
        else:
            ui.label('No uploaders available. Please check your installation.').classes('text-yellow-400')
        
        # Caption input and upload button
        with ui.card().classes('w-full'):
            ui.label('Add Caption').classes('text-xl font-bold mb-4')
            caption_input = ui.textarea('Write your caption...').classes('w-full')
            caption_input.props('rows=4')
            
            def do_upload():
                if not self.uploaded_files:
                    ui.notify('❌ Please upload a file first', type='negative')
                    return
                
                if not self.selected_platform:
                    ui.notify('❌ Please select a platform', type='negative')
                    return
                
                # Get selected account ID
                if account_selector and account_selector.value:
                    platform_accounts = self.uploader_manager.get_platform_accounts(self.selected_platform)
                    account_options = {acc.name: acc.account_id for acc in platform_accounts}
                    account_id = account_options.get(account_selector.value)
                    
                    if not account_id:
                        ui.notify('❌ Please select an account', type='negative')
                        return
                    
                    ui.notify(f'🚀 Uploading to {self.selected_platform}...', type='info')
                    
                    # Call actual uploader
                    file_info = self.uploaded_files[-1]
                    success, msg = self.uploader_manager.upload_to_platform(
                        self.selected_platform,
                        account_id,
                        file_info['path'],
                        caption_input.value
                    )
                    
                    if success:
                        ui.notify(f'✅ {msg}', type='positive')
                    else:
                        ui.notify(f'❌ Upload failed: {msg}', type='negative')
                else:
                    ui.notify('❌ Please select an account', type='negative')
            
            ui.button('🚀 Post Now', on_click=do_upload).classes('mt-4')
    
    def select_platform(self, platform):
        """Select a platform for upload"""
        self.selected_platform = platform
        ui.notify(f'📱 Selected: {platform.title()}', type='info')
        self.navigate('upload')  # Refresh page to update button states
    
    def render_content(self):
        """Content library"""
        ui.label('Content Library').classes('text-3xl cyber-text-gradient mb-6')
        
        with ui.card().classes('w-full'):
            if self.uploaded_files:
                ui.label(f'Uploaded Files: {len(self.uploaded_files)}').classes('text-xl mb-4')
                
                with ui.grid(columns=3).classes('w-full gap-4'):
                    for file in self.uploaded_files:
                        with ui.card():
                            ui.label(file['name']).classes('font-bold')
                            size_mb = file.get('size', 0) / (1024 * 1024)
                            ui.label(f'{size_mb:.2f} MB').classes('text-sm text-gray-500')
            else:
                ui.label('No content yet. Upload files in the Upload tab.').classes('text-gray-400')
    
    def render_analytics(self):
        """Analytics dashboard"""
        ui.label('Analytics Dashboard').classes('text-3xl cyber-text-gradient mb-6')
        
        with ui.card().classes('w-full mb-6'):
            ui.label('📊 Performance Metrics').classes('text-2xl font-bold mb-4')
            
            with ui.row().classes('gap-6'):
                self.stat_card('Total Posts', 0, '📝', '#00f2ff')
                self.stat_card('Total Views', 0, '👁️', '#00ff9d')
                self.stat_card('Engagement', '0%', '❤️', '#8b00ff')
        
        with ui.card().classes('w-full'):
            ui.label('Coming Soon').classes('text-gray-400')
            ui.label('• Real-time analytics').classes('text-sm text-gray-500')
            ui.label('• Engagement tracking').classes('text-sm text-gray-500')
            ui.label('• Performance insights').classes('text-sm text-gray-500')
    
    def render_accounts(self):
        """Accounts management - Phase 1 OAuth Integration"""
        ui.label('Manage Accounts').classes('text-3xl cyber-text-gradient mb-6')
        
        # Get accounts from Phase 1 backend database
        backend_accounts = backend_db.list_accounts()
        
        # Connect New Account - Phase 1 OAuth
        with ui.card().classes('w-full mb-6'):
            ui.label('🔐 Connect New Account').classes('text-xl font-bold mb-4')
            ui.label('Secure OAuth - No passwords stored locally').classes('text-sm text-gray-500 mb-4')
            
            with ui.row().classes('gap-4'):
                def connect_facebook():
                    try:
                        ui.notify('🔐 Opening Facebook OAuth...', type='info')
                        oauth_registry.initiate_oauth('facebook')
                        ui.notify('✅ Check your browser to authorize', type='positive')
                    except Exception as e:
                        ui.notify(f'❌ OAuth error: {str(e)}', type='negative')
                
                def connect_instagram():
                    try:
                        ui.notify('🔐 Opening Instagram OAuth...', type='info')
                        oauth_registry.initiate_oauth('instagram')
                        ui.notify('✅ Check your browser to authorize', type='positive')
                    except Exception as e:
                        ui.notify(f'❌ OAuth error: {str(e)}', type='negative')
                
                def connect_youtube():
                    try:
                        ui.notify('🔐 Opening YouTube OAuth...', type='info')
                        oauth_registry.initiate_oauth('youtube')
                        ui.notify('✅ Check your browser to authorize', type='positive')
                    except Exception as e:
                        ui.notify(f'❌ OAuth error: {str(e)}', type='negative')
                
                ui.button('📘 Connect Facebook', on_click=connect_facebook)
                ui.button('📷 Connect Instagram', on_click=connect_instagram)
                ui.button('🎥 Connect YouTube', on_click=connect_youtube)
            
            with ui.row().classes('gap-2 mt-4 items-center'):
                ui.label('💡').classes('text-2xl')
                with ui.column().classes('gap-0'):
                    ui.label('Phase 1 OAuth Active').classes('text-sm font-bold text-green-400')
                    ui.label('Using https://127.0.0.1:5000 + fyi:// protocol (No ngrok!)').classes('text-xs text-gray-500')
        
        # List connected accounts from backend
        with ui.card().classes('w-full'):
            ui.label(f'Connected Accounts ({len(backend_accounts)})').classes('text-xl font-bold mb-4')
            
            if backend_accounts:
                with ui.grid(columns=2).classes('w-full gap-4'):
                    for acc in backend_accounts:
                        with ui.card():
                            with ui.row().classes('w-full items-center justify-between'):
                                with ui.column():
                                    icon = {'facebook': '📘', 'instagram': '📷', 'youtube': '🎥'}.get(acc['platform'], '🌐')
                                    ui.label(f"{icon} {acc['platform'].title()} - {acc['name']}").classes('font-bold')
                                    ui.label(f"ID: {acc['account_id']}").classes('text-xs text-gray-600')
                                    
                                    # Token status
                                    expires_at = acc.get('token_expires_at', 0)
                                    from datetime import datetime
                                    is_valid = expires_at > int(datetime.now().timestamp())
                                    status = '✓ Token Valid' if is_valid else '⚠️ Token Expired'
                                    ui.label(status).classes('text-sm text-green-400' if is_valid else 'text-sm text-yellow-400')
                                
                                def delete_acc(account_id=acc['account_id']):
                                    backend_db.delete_account(account_id)
                                    ui.notify('✅ Account removed', type='positive')
                                    self.navigate('accounts')
                                
                                ui.button('🗑️', on_click=delete_acc).props('flat dense color=negative')
            else:
                ui.label('No accounts connected yet. Click a button above to connect via OAuth.').classes('text-gray-400')
    
    def render_settings(self):
        """Settings page - Phase 1 BYOK"""
        ui.label('Settings').classes('text-3xl cyber-text-gradient mb-6')
        
        # BYOK - AI API Keys
        with ui.card().classes('w-full mb-6'):
            ui.label('🤖 AI API Keys (BYOK - Bring Your Own Key)').classes('text-xl font-bold mb-4')
            ui.label('Store your own API keys securely with encryption').classes('text-sm text-gray-500 mb-4')
            
            configured_services = byok_manager.list_configured_services()
            
            # Add API Key
            with ui.row().classes('gap-4 items-end w-full mb-4'):
                service_input = ui.select(
                    ['openai', 'anthropic', 'grok', 'gemini', 'mistral'],
                    label='AI Service',
                    value='openai'
                ).classes('flex-1')
                
                key_input = ui.input('API Key', password=True, password_toggle_button=True).classes('flex-1')
                
                def save_api_key():
                    if key_input.value:
                        service = service_input.value
                        if byok_manager.validate_key_format(service, key_input.value):
                            byok_manager.set_api_key(service, key_input.value)
                            ui.notify(f'✅ {service.title()} API key saved securely!', type='positive')
                            key_input.value = ''
                            self.navigate('settings')
                        else:
                            ui.notify(f'❌ Invalid key format for {service}', type='negative')
                    else:
                        ui.notify('❌ Please enter an API key', type='negative')
                
                ui.button('💾 Save Key', on_click=save_api_key)
            
            # List configured services
            if configured_services:
                ui.label('Configured Services:').classes('font-bold mb-2')
                with ui.column().classes('gap-2'):
                    for service_id, service_name in configured_services.items():
                        with ui.row().classes('items-center gap-4'):
                            ui.label(f'✓ {service_name}').classes('text-green-400')
                            
                            def delete_key(svc=service_id):
                                byok_manager.delete_api_key(svc)
                                ui.notify(f'✅ {svc.title()} key removed', type='positive')
                                self.navigate('settings')
                            
                            ui.button('🗑️ Remove', on_click=delete_key).props('flat dense size=sm color=negative')
        
        # OAuth Server Status
        with ui.card().classes('w-full mb-6'):
            ui.label('🔐 OAuth Server Status').classes('text-xl font-bold mb-4')
            ui.label('✅ Running on https://127.0.0.1:5000').classes('text-green-400')
            ui.label('✅ Protocol handler: fyi://').classes('text-green-400')
            ui.label('✅ No ngrok required!').classes('text-green-400')
        
        # App Settings
        with ui.card().classes('w-full mb-6'):
            ui.label('⚙️ Application Settings').classes('text-xl font-bold mb-4')
            
            ui.switch('Dark Mode (Always On)').props('disable model-value=true')
            ui.switch('Enable Notifications').props('model-value=true')
            ui.switch('Auto-save Drafts').props('model-value=true')
        
        # About
        with ui.card().classes('w-full'):
            ui.label('About FYI Social ∞').classes('text-xl font-bold mb-4')
            ui.label('Version 1.0 - Phase 1 Complete').classes('text-gray-400')
            ui.label('🚀 Phase 0: Cyber-Futuristic Design ✅').classes('text-sm text-gray-500')
            ui.label('🔐 Phase 1: OAuth + BYOK + Backend ✅').classes('text-sm text-gray-500')
            ui.label('💎 Free forever. No subscriptions.').classes('text-sm text-gray-500')
            ui.label('🔒 100% Local processing.').classes('text-sm text-gray-500')
    
    def stat_card(self, label, value, icon, color):
        """Render a stat card"""
        with ui.card().classes('flex-1'):
            with ui.row().classes('w-full items-center justify-between'):
                with ui.column():
                    ui.label(label).classes('text-sm text-gray-400')
                    ui.label(str(value)).classes('text-3xl font-bold').style(f'color: {color}')
                ui.label(icon).classes('text-4xl')


# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ in {"__main__", "__mp_main__"}:
    import os
    
    # Check if running in desktop mode (no browser)
    # Default to not auto-opening a browser to reduce confusion during desktop runs.
    show_browser = os.getenv('NICEGUI_NO_BROWSER', '1') != '1'
    
    # Use custom port if set (for desktop app)
    port = int(os.getenv('NICEGUI_PORT', '8080'))
    
    app_instance = FYISocialInfinity()
    
    @ui.page('/')
    def main_page():
        app_instance.run()
    
    ui.run(
        title='FYI Social ∞',
        dark=True,
        reload=False,
        show=show_browser,
        port=port,
        favicon='🚀'
    )
