"""
OAuth Server for Facebook/Instagram Authentication
Handles OAuth callbacks and token exchange via ngrok
"""
import os
import json
from pathlib import Path
from datetime import datetime
from flask import Flask, request, redirect, abort
import requests
import secrets

from logger_config import get_logger
from config import get_config
from account_manager import get_account_manager, Account

logger = get_logger(__name__)
config = get_config()
account_manager = get_account_manager()

app = Flask(__name__)

# State management for OAuth security
STATE_FILE = config.data_dir / '.oauth_state'

def save_state() -> str:
    """Generate and save OAuth state nonce"""
    state = secrets.token_urlsafe(32)
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(state)
    return state

def verify_state(received: str) -> bool:
    """Verify OAuth state to prevent CSRF attacks"""
    try:
        expected = STATE_FILE.read_text().strip()
        STATE_FILE.unlink()  # Delete after use
        return secrets.compare_digest(received or '', expected)
    except:
        return False

@app.route('/')
def index():
    """Server home page"""
    return """<!DOCTYPE html>
<html>
<head>
    <title>FYI Uploader - OAuth Server</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            margin: 0;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
        }
        .container {
            background: white;
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 500px;
            text-align: center;
        }
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        .status {
            display: inline-block;
            padding: 8px 16px;
            background: #4CAF50;
            color: white;
            border-radius: 20px;
            font-size: 14px;
            margin: 20px 0;
        }
        .info {
            color: #666;
            line-height: 1.6;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>OAuth Server Running</h1>
        <span class="status">Active</span>
        <div class="info">
            <p>Waiting for authentication callbacks.</p>
            <p>Close this if not needed.</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/callback')
def callback():
    """Handle OAuth callback"""
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')

    if error:
        return f"Authentication failed: {error}", 400

    if not verify_state(state):
        return "Invalid state - possible CSRF attack", 403

    if not code:
        return "No code provided", 400

    # Exchange code for access token
    token_url = "https://graph.facebook.com/v20.0/oauth/access_token"
    params = {
        'client_id': config.fb_app_id,
        'client_secret': config.fb_app_secret,
        'redirect_uri': config.redirect_uri,
        'code': code
    }

    try:
        response = requests.get(token_url, params=params, timeout=30)
        response.raise_for_status()
        token_data = response.json()
        user_access_token = token_data.get('access_token')

        if not user_access_token:
            return "No access token received", 400

        # Get long-lived token
        long_lived_url = "https://graph.facebook.com/v20.0/oauth/access_token"
        long_params = {
            'grant_type': 'fb_exchange_token',
            'client_id': config.fb_app_id,
            'client_secret': config.fb_app_secret,
            'fb_exchange_token': user_access_token
        }
        long_response = requests.get(long_lived_url, params=long_params, timeout=30)
        long_response.raise_for_status()
        long_token_data = long_response.json()
        long_access_token = long_token_data.get('access_token')
        expires_in = long_token_data.get('expires_in')

        expires_at = int(datetime.now().timestamp()) + expires_in if expires_in else None

        # Get all pages the user manages
        page_token_url = "https://graph.facebook.com/v20.0/me/accounts"
        page_params = {'access_token': long_access_token}
        page_response = requests.get(page_token_url, params=page_params, timeout=30)
        page_response.raise_for_status()
        page_data = page_response.json()
        pages = page_data.get('data', []) or []

        if not pages:
            return "No managed pages found. Ensure the selected profile has the correct permissions.", 400

        now_ts = int(datetime.now().timestamp())
        linked_pages = []
        linked_instagram = []

        def upsert_account(platform: str, page_id: str, name: str, token: str):
            matches = [
                acc for acc in account_manager.get_accounts_by_platform(platform)
                if acc.page_id == page_id
            ]
            if matches:
                account_manager.update_account(
                    matches[0].account_id,
                    name=name,
                    access_token=token,
                    token_expires_at=expires_at,
                    linked_at=now_ts,
                    is_active=True
                )
                return matches[0].account_id
            account = Account(
                account_id="",
                platform=platform,
                name=name,
                page_id=page_id,
                access_token=token,
                token_expires_at=expires_at
            )
            return account_manager.add_account(account)

        for page in pages:
            page_id = page.get('id')
            page_token = page.get('access_token')
            page_name = page.get('name') or page_id

            if not page_id or not page_token:
                logger.warning("Skipping page with missing token or ID")
                continue

            upsert_account("facebook", page_id, page_name, page_token)
            linked_pages.append(page_name)

            ig_url = f"https://graph.facebook.com/v20.0/{page_id}"
            ig_params = {
                'fields': 'instagram_business_account',
                'access_token': page_token
            }
            ig_response = requests.get(ig_url, params=ig_params, timeout=30)
            ig_response.raise_for_status()
            ig_data = ig_response.json()
            ig_account = ig_data.get("instagram_business_account")
            ig_id = ig_account.get('id') if ig_account else None

            if ig_id:
                ig_details = {}
                try:
                    details_resp = requests.get(
                        f"https://graph.facebook.com/v20.0/{ig_id}",
                        params={'fields': 'username,name', 'access_token': page_token},
                        timeout=30
                    )
                    details_resp.raise_for_status()
                    ig_details = details_resp.json()
                except requests.exceptions.RequestException as ig_err:
                    logger.warning(f"Instagram lookup failed for {ig_id}: {ig_err}")
                ig_name = ig_details.get('username') or ig_details.get('name') or page_name
                upsert_account("instagram", ig_id, ig_name, page_token)
                linked_instagram.append(ig_name)
                logger.info(f"Linked Instagram account: {ig_id}")

        # TRIGGER UI REFRESH
        refresh_file = config.data_dir / ".refresh_ui"
        refresh_file.touch(exist_ok=True)

        fb_summary = ''.join(f'<li>{name}</li>' for name in linked_pages) or '<li>No pages detected</li>'
        ig_summary = ''.join(f'<li>{name}</li>' for name in linked_instagram) or '<li>No Instagram accounts detected</li>'

        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Success</title>
</head>
<body>
    <h1>Authentication Successful</h1>
    <p>The following Facebook pages were linked:</p>
    <ul>{fb_summary}</ul>
    <p>Instagram accounts:</p>
    <ul>{ig_summary}</ul>
    <p>You can close this window.</p>
</body>
</html>""", 200

    except requests.exceptions.RequestException as e:
        logger.error(f"Token exchange failed: {e}")
        return f"Network error during token exchange: {str(e)}", 502

def get_login_url() -> str:
    """Get Facebook OAuth login URL"""
    state = save_state()
    permissions = "pages_show_list,pages_read_engagement,pages_manage_posts,instagram_basic,instagram_content_publish"
    return (
        f"https://www.facebook.com/v20.0/dialog/oauth?"
        f"client_id={config.fb_app_id}&redirect_uri={config.redirect_uri}"
        f"&scope={permissions}&state={state}"
    )

def get_login_url_for_ig() -> str:
    """Get Instagram OAuth login URL (same as Facebook)"""
    return get_login_url()

def start_server():
    """Start the OAuth server"""
    logger.info(f"Starting OAuth server on {config.server_host}:{config.server_port}")
    app.run(
        host=config.server_host,
        port=config.server_port,
        debug=False
    )

if __name__ == '__main__':
    start_server()