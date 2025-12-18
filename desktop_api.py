"""
Desktop App REST API
Provides endpoints for the Tauri desktop application
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from pathlib import Path
import json
from datetime import datetime
import webbrowser
import sys
import os
import subprocess
import threading
import time
import socket
import requests
from urllib.parse import urlencode
import ipaddress

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

app = Flask(__name__)
CORS(app)  # Enable CORS for desktop app

ACCOUNTS_FILE = Path("accounts/accounts.json")
ACCOUNTS_FILE.parent.mkdir(parents=True, exist_ok=True)

def load_accounts():
    """Load accounts from JSON file"""
    if ACCOUNTS_FILE.exists():
        with open(ACCOUNTS_FILE, 'r') as f:
            data = json.load(f)
            # Handle both array and object with "accounts" key
            if isinstance(data, dict):
                return data.get('accounts', [])
            return data if isinstance(data, list) else []
    return []

def save_accounts(accounts):
    """Save accounts to JSON file"""
    with open(ACCOUNTS_FILE, 'w') as f:
        json.dump({'accounts': accounts}, f, indent=2)

@app.route('/api/accounts', methods=['GET'])
def get_accounts():
    """Get all connected accounts"""
    try:
        accounts = load_accounts()
        
        # Enrich with stats from each platform
        enriched = []
        for idx, acc in enumerate(accounts):
            # Add ID if missing (for old accounts)
            if not acc.get('id'):
                acc['id'] = str(idx + 1)
            
            platform = acc.get('platform', '')
            
            # Get stats based on platform
            stats = {
                'followers': 0,
                'total_posts': 0
            }
            
            try:
                if platform == 'youtube':
                    # YouTube stats from tokens file
                    token_file = Path(f"accounts/youtube/{acc.get('account_name', 'default')}_token.json")
                    if token_file.exists():
                        with open(token_file, 'r') as f:
                            token_data = json.load(f)
                            stats['followers'] = token_data.get('subscriber_count', 0)
                            stats['total_posts'] = token_data.get('video_count', 0)
                
                elif platform == 'facebook':
                    # Facebook page stats
                    page_token_file = Path("data/fb_page_token.txt")
                    if page_token_file.exists():
                        stats['followers'] = 0  # Would need API call
                        stats['total_posts'] = 0
                
                elif platform == 'instagram':
                    # Instagram stats
                    ig_user_file = Path("data/ig_user_id.txt")
                    if ig_user_file.exists():
                        stats['followers'] = 0  # Would need API call
                        stats['total_posts'] = 0
            except Exception as stat_error:
                print(f"Error loading stats for {platform}: {stat_error}")
            
            enriched.append({
                **acc,
                **stats,
                'status': 'connected'
            })
        
        return jsonify({'accounts': enriched})
    except Exception as e:
        print(f"Error in get_accounts: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'accounts': []}), 200  # Return empty list instead of 500

@app.route('/oauth/start/<platform>', methods=['POST'])
def start_oauth(platform):
    """Initiate OAuth flow for a platform"""
    try:
        from config import Config
        cfg = Config.from_env()
        
        data = request.json or {}
        account_name = data.get('account_name', f'{platform}_account')
        
        # Start OAuth callback server if not running
        ensure_oauth_server_running()
        
        # Build OAuth URL based on platform
        auth_url = None
        
        if platform in ['facebook', 'instagram']:
            # Facebook OAuth - use existing configured redirect from .env
            redirect_uri = cfg.redirect_uri  # Gets from OAUTH_REDIRECT_ORIGIN
            params = {
                'client_id': cfg.fb_app_id,
                'redirect_uri': redirect_uri,
                'scope': 'pages_show_list,pages_read_engagement,pages_manage_posts,instagram_basic,instagram_content_publish',
                'response_type': 'code',
                'state': f'desktop_{platform}:{account_name}'
            }
            auth_url = f"https://www.facebook.com/v18.0/dialog/oauth?{urlencode(params)}"
            print(f"📱 Using redirect URI: {redirect_uri}")
            print(f"🌐 OAuth URL: {auth_url}")
        
        elif platform == 'youtube':
            return jsonify({
                'error': 'YouTube OAuth requires Google OAuth2 setup. Please configure YouTube credentials first.'
            }), 400
        
        else:
            return jsonify({
                'error': f'{platform} OAuth not yet implemented'
            }), 400
        
        if auth_url:
            # Open in browser
            webbrowser.open(auth_url)
            
            return jsonify({
                'success': True,
                'auth_url': auth_url,
                'platform': platform,
                'message': 'OAuth window opened. Complete authorization in your browser.'
            })
        
        return jsonify({'error': 'Failed to generate OAuth URL'}), 400
            
    except Exception as e:
        print(f"OAuth start error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# OAuth callback server management - Port 5000 for callbacks
callback_app = Flask('oauth_callback')
CORS(callback_app)
oauth_server_running = False


def _generate_self_signed_cert(cert_path: Path, key_path: Path, common_name: str, san_hosts: list[str]) -> bool:
    """Generate a self-signed certificate for local HTTPS."""
    try:
        from cryptography import x509
        from cryptography.x509.oid import NameOID
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.hazmat.backends import default_backend
        import datetime as dt

        key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
        subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])

        san_entries = []
        for host in san_hosts:
            try:
                san_entries.append(x509.IPAddress(ipaddress.ip_address(host)))
            except ValueError:
                san_entries.append(x509.DNSName(host))

        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(dt.datetime.utcnow())
            .not_valid_after(dt.datetime.utcnow() + dt.timedelta(days=365))
            .add_extension(x509.SubjectAlternativeName(san_entries), critical=False)
            .sign(key, hashes.SHA256(), default_backend())
        )

        key_path.write_bytes(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
        cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
        return True
    except Exception as e:
        print(f"⚠️ SSL certificate generation failed: {e}")
        import traceback

        traceback.print_exc()
        return False

def start_callback_server():
    """Start OAuth callback server on port 5000"""
    try:
        from config import Config
        cfg = Config.from_env()
        
        # Generate SSL certificate if needed
        cert_path = Path("desktop_callback_cert.pem")
        key_path = Path("desktop_callback_key.pem")
        
        if not cert_path.exists() or not key_path.exists():
            print("🔒 Generating SSL certificate for callback server...")
            ok = _generate_self_signed_cert(
                cert_path=cert_path,
                key_path=key_path,
                common_name="127.0.0.1",
                san_hosts=["localhost", "127.0.0.1"],
            )
            if not ok:
                return
            print("✅ SSL certificate generated for callback server")
        
        print(f"🔐 Starting OAuth callback server on https://127.0.0.1:5000/callback")
        callback_app.run(
            host='127.0.0.1',
            port=5000,
            ssl_context=(str(cert_path), str(key_path)),
            debug=False,
            use_reloader=False
        )
    except Exception as e:
        print(f"❌ Callback server error: {e}")
        import traceback
        traceback.print_exc()

def ensure_oauth_server_running():
    """Make sure OAuth callback endpoint is ready on port 5000"""
    global oauth_server_running
    if not oauth_server_running:
        oauth_server_running = True
        # Start callback server in background thread
        callback_thread = threading.Thread(target=start_callback_server, daemon=True)
        callback_thread.start()
        time.sleep(2)  # Give it time to start
        print("✅ OAuth callback server started on port 5000")

@callback_app.route('/callback', methods=['GET'])
def oauth_callback():
    """Handle OAuth callbacks from all platforms"""
    try:
        code = request.args.get('code')
        state = request.args.get('state', '')
        error = request.args.get('error')
        
        if error:
            return f'''
            <html>
            <head><title>FYI Social - OAuth Error</title></head>
            <body style="font-family: system-ui; padding: 40px; text-align: center; background: linear-gradient(180deg, #0a0a1f, #000000); color: white;">
                <div style="background: rgba(255, 0, 110, 0.1); padding: 40px; border-radius: 16px; border: 1px solid rgba(255, 0, 110, 0.4);">
                    <h1 style="color: #ff006e;">❌ Authentication Failed</h1>
                    <p>Error: {error}</p>
                    <p style="color: #888;">You can close this window.</p>
                </div>
            </body>
            </html>
            '''
        
        if not code:
            return jsonify({'error': 'No authorization code received'}), 400
        
        # Parse platform and account name from state
        platform = state.split(':', 1)[0] if ':' in state else 'unknown'
        account_name = state.split(':', 1)[1] if ':' in state else f'{platform}_account'
        
        # Exchange code for token and save account
        if platform in ['facebook', 'instagram']:
            handle_facebook_callback(code, platform, account_name)
        
        return f'''
        <html>
        <head><title>FYI Social - Connected!</title></head>
        <body style="font-family: system-ui; padding: 40px; text-align: center; background: linear-gradient(180deg, #0a0a1f, #000000); color: white;">
            <div style="background: rgba(0, 242, 255, 0.1); padding: 40px; border-radius: 16px; border: 1px solid rgba(0, 242, 255, 0.4);">
                <h1 style="background: linear-gradient(90deg, #00f2ff, #8b00ff); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">✅ Account Connected!</h1>
                <p>Successfully connected {platform.title()} account: {account_name}</p>
                <p style="color: #888;">You can close this window and return to the app.</p>
            </div>
            <script>setTimeout(() => window.close(), 3000);</script>
        </body>
        </html>
        '''
    except Exception as e:
        print(f"OAuth callback error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def handle_facebook_callback(code, platform, account_name):
    """Handle Facebook/Instagram OAuth callback"""
    try:
        from config import Config
        import requests
        
        cfg = Config.from_env()
        
        # Exchange code for access token
        token_url = 'https://graph.facebook.com/v18.0/oauth/access_token'
        params = {
            'client_id': cfg.fb_app_id,
            'client_secret': cfg.fb_app_secret,
            'redirect_uri': cfg.redirect_uri,
            'code': code
        }
        
        response = requests.get(token_url, params=params)
        token_data = response.json()
        
        if 'access_token' not in token_data:
            print(f"Token exchange failed: {token_data}")
            return
        
        access_token = token_data['access_token']
        
        # Get user/page info
        me_url = 'https://graph.facebook.com/me'
        me_response = requests.get(me_url, params={'access_token': access_token})
        user_data = me_response.json()
        
        # Save account
        accounts = load_accounts()
        new_id = str(max([int(acc.get('id', 0)) for acc in accounts] + [0]) + 1)
        
        new_account = {
            'id': new_id,
            'platform': platform,
            'account_name': account_name,
            'username': user_data.get('name', account_name),
            'user_id': user_data.get('id'),
            'access_token': access_token,
            'connected_at': datetime.now().isoformat(),
            'status': 'connected'
        }
        
        accounts.append(new_account)
        save_accounts(accounts)
        
        print(f"✅ Successfully connected {platform} account: {account_name}")
        
    except Exception as e:
        print(f"Error handling Facebook callback: {e}")
        import traceback
        traceback.print_exc()

@app.route('/api/accounts/<account_id>', methods=['DELETE'])
def disconnect_account(account_id):
    """Disconnect/remove an account"""
    try:
        accounts = load_accounts()
        # Handle both id and name-based matching (for old accounts)
        initial_count = len(accounts)
        accounts = [acc for acc in accounts 
                   if str(acc.get('id', '')) != str(account_id) 
                   and acc.get('username', '') != str(account_id)
                   and acc.get('name', '') != str(account_id)]
        
        if len(accounts) == initial_count:
            print(f"No account found with identifier: {account_id}")
        else:
            print(f"Removed account: {account_id}")
        
        save_accounts(accounts)
        return jsonify({'message': 'Account disconnected'})
    except Exception as e:
        print(f"Error disconnecting account: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/accounts/<account_id>/refresh', methods=['POST'])
def refresh_account(account_id):
    """Refresh account stats"""
    try:
        accounts = load_accounts()
        
        # Find account and update last_refreshed
        for acc in accounts:
            if str(acc.get('id')) == str(account_id):
                acc['last_refreshed'] = datetime.now().isoformat()
        
        save_accounts(accounts)
        
        return jsonify({'message': 'Account refreshed'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/oauth/check/<platform>', methods=['GET'])
def check_oauth_status(platform):
    """Check if OAuth flow completed for a platform"""
    try:
        # Check if there are any new accounts for this platform
        accounts = load_accounts()
        platform_accounts = [acc for acc in accounts if acc.get('platform') == platform]
        
        return jsonify({
            'completed': len(platform_accounts) > 0,
            'accounts': platform_accounts
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def start_oauth_callback_server():
    """Legacy wrapper retained for compatibility."""
    ensure_oauth_server_running()

def run_desktop_api(port=8080):
    """Start the desktop API server with HTTPS"""
    # Start OAuth callback server first
    ensure_oauth_server_running()
    
    print(f"🚀 Desktop API running on https://localhost:{port}")
    print(f"📱 Desktop app can now connect to backend")
    
    # Create self-signed certificate if it doesn't exist
    cert_file = Path("desktop_cert.pem")
    key_file = Path("desktop_key.pem")
    
    if not cert_file.exists() or not key_file.exists():
        print("📜 Generating self-signed SSL certificate...")
        ok = _generate_self_signed_cert(
            cert_path=cert_file,
            key_path=key_file,
            common_name="localhost",
            san_hosts=["localhost", "127.0.0.1"],
        )
        if not ok:
            print("🚨 HTTPS is required for Facebook OAuth. Please install/repair 'cryptography' and rerun.")
            return
        print("✅ SSL certificate generated")
    
    try:
        # Run with SSL
        app.run(
            host='127.0.0.1', 
            port=port, 
            debug=False, 
            threaded=True, 
            use_reloader=False,
            ssl_context=(str(cert_file), str(key_file))
        )
    except Exception as e:
        print(f"❌ API server error: {e}")

if __name__ == '__main__':
    run_desktop_api()
