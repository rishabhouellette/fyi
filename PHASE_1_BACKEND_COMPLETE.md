# FYI Social ∞ - Phase 1 Backend Architecture

## 🎯 What We Built

A **unified, professional backend** that eliminates fragmentation and provides:

### ✅ Core Features

1. **Unified Configuration** (`backend/config.py`)
   - Auto-detects mode: Desktop, Web, API, or Hybrid
   - Single source of truth for all settings
   - Environment variable support

2. **Robust Database Layer** (`backend/database.py`)
   - SQLite for local storage
   - Optional Supabase sync for cloud backup
   - Clean API for accounts, posts, analytics, settings

3. **Security First** (`backend/services/encryption.py`)
   - Fernet encryption for sensitive data
   - Hardware key support
   - Secure key storage

4. **BYOK (Bring Your Own Key)** (`backend/services/byok_manager.py`)
   - Users control their own API keys
   - Encrypted storage for OpenAI, Grok, Claude, Gemini
   - No vendor lock-in

5. **THE NGROK KILLER** (`backend/services/local_oauth.py`)
   - Local OAuth server on localhost:5000
   - Custom `fyi://` protocol handler
   - No tunneling needed!
   - Beautiful OAuth success/error pages with cyber theme

6. **OAuth Registry** (`backend/services/oauth_registry.py`)
   - Facebook, Instagram, YouTube OAuth flows
   - Token management
   - Automatic account creation

7. **Protocol Handler** (`backend/utils/protocol_handler.py`)
   - Registers `fyi://` on Windows/macOS/Linux
   - Enables deep linking for OAuth callbacks
   - Auto-registration on first run

## 📁 File Structure

```
backend/
├── main.py                  # Unified entry point
├── config.py                # Configuration management
├── database.py              # Database layer
├── services/
│   ├── encryption.py        # Encryption service
│   ├── byok_manager.py      # API key management
│   ├── local_oauth.py       # Local OAuth server
│   └── oauth_registry.py    # Platform OAuth flows
└── utils/
    └── protocol_handler.py  # Protocol registration
```

## 🚀 How to Use

### Start Web Portal
```bash
python backend/main.py
# Opens at http://localhost:8080
```

### Start Desktop App
```bash
set FYI_MODE=desktop
python backend/main.py
# No browser, runs on localhost:8081
```

### API Only Mode
```bash
set FYI_MODE=api
python backend/main.py
# Only OAuth server on localhost:5000
```

### Hybrid Mode (All Services)
```bash
set FYI_MODE=hybrid
python backend/main.py
```

## 🔐 OAuth Flow (NGROK-FREE!)

1. User clicks "Connect Facebook" in UI
2. Backend starts OAuth server on `localhost:5000`
3. Opens browser to Facebook OAuth with redirect to `http://localhost:5000/oauth/callback`
4. User authorizes
5. Facebook redirects back to `localhost:5000/oauth/callback`
6. Backend exchanges code for token
7. Stores encrypted token in database
8. Shows beautiful success page
9. **NO NGROK NEEDED!**

## 🔑 BYOK Setup

```python
from backend.services.byok_manager import get_byok_manager

byok = get_byok_manager()

# Set API keys
byok.set_api_key('openai', 'sk-...')
byok.set_api_key('anthropic', 'sk-ant-...')
byok.set_api_key('grok', '...')

# Get API keys
openai_key = byok.get_api_key('openai')

# List configured services
services = byok.list_configured_services()
# {'openai': 'OpenAI', 'anthropic': 'Anthropic (Claude)'}
```

## 💾 Database Usage

```python
from backend.database import get_database

db = get_database()

# Create account
db.create_account({
    'account_id': 'fb_123',
    'platform': 'facebook',
    'name': 'My Page',
    'access_token': '...',
    ...
})

# List accounts
accounts = db.list_accounts(platform='facebook')

# Create post
db.create_post({
    'post_id': 'post_123',
    'account_id': 'fb_123',
    'platform': 'facebook',
    'title': 'My Video',
    ...
})

# Settings
db.set_setting('theme', 'dark')
theme = db.get_setting('theme')
```

## 🎨 Integration with Existing UI

The backend is designed to work seamlessly with your existing `main.py` UI:

```python
from backend.config import get_config
from backend.database import get_database
from backend.services.oauth_registry import get_oauth_registry

config = get_config()
db = get_database()
oauth = get_oauth_registry()

# In your UI
def connect_facebook():
    oauth.initiate_oauth('facebook', 'My Account')
    # Opens browser, handles OAuth, stores account
```

## 🔧 Environment Variables

```bash
# Mode
FYI_MODE=web|desktop|api|hybrid

# Ports
FYI_WEB_PORT=8080
FYI_DESKTOP_PORT=8081
FYI_API_PORT=5000

# Database
FYI_USE_SUPABASE=true
SUPABASE_URL=...
SUPABASE_KEY=...

# Encryption
FYI_ENCRYPTION_KEY=...

# Platform API Keys
FACEBOOK_APP_ID=...
FACEBOOK_APP_SECRET=...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# AI Keys (optional, can use BYOK instead)
OPENAI_API_KEY=...
ANTHROPIC_API_KEY=...
GROK_API_KEY=...
```

## 🎯 Next Steps (Phase 2)

- [ ] Integrate with existing uploader classes
- [ ] Add scheduling engine
- [ ] Real-time analytics sync
- [ ] AI content generation
- [ ] Team collaboration features

## 🚀 Benefits

✅ **No more fragmentation** - One unified backend
✅ **No more ngrok** - Local OAuth with protocol handler
✅ **Secure by default** - Encryption for all sensitive data
✅ **User owns data** - BYOK approach, SQLite local storage
✅ **Mode flexibility** - Web, Desktop, API, or Hybrid
✅ **Professional architecture** - Clean, maintainable, scalable

---

**Phase 1 Complete!** 🎉

You now have a rock-solid backend that's ready to scale.
