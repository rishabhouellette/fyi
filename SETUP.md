# FYIXT Setup Guide

## Quick Start

### Prerequisites
- Python 3.9+ (tested on 3.9.6)
- pip or conda for package management
- Git (for repository management)

### Installation Steps

#### 1. Create Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\Activate.ps1  # On Windows PowerShell
```

#### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

#### 3. Set Up Environment Variables
Create a `.env` file in the project root with your credentials:
```bash
# Facebook/Instagram OAuth
FB_APP_ID=your_app_id
FB_APP_SECRET=your_app_secret

# YouTube OAuth
YT_CLIENT_ID=your_client_id
YT_CLIENT_SECRET=your_client_secret

# AI Services (optional - BYOK)
GOOGLE_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key

# Server Configuration
FYI_WEB_PORTAL_PORT=5050
FYI_PUBLIC_BASE_URL=https://your-domain.com
```

#### 4. Initialize Database
The SQLite database (`data/fyi_webportal.db`) is created automatically on first run.

### Running the Server

#### Development Mode (with HTTPS self-signed cert)
```bash
python web_server.py --https --port 5050
```

#### Production Mode (Docker)
```bash
cd deploy
docker-compose up -d
```

#### Running Tests
```bash
python scripts/smoke_test_web_server.py
```

### Building the React Frontend

```bash
cd desktop
npm install
npm run build  # Creates dist/ folder
cd ..
```

The React build will be served from `desktop/dist/` at the root path.

## Project Structure

```
├── web_server.py           # Main FastAPI entry point
├── app_db.py               # SQLite database layer
├── core/                   # Configuration, models, utilities
├── services/               # Business logic (accounts, platforms, scheduler)
├── routes/                 # API endpoints (api, ai, media)
├── desktop/                # React frontend (Vite + Tauri)
├── scripts/                # Utilities (smoke_test)
├── deploy/                 # Docker & deployment configs
└── data/                   # Runtime directory (created on first run)
    ├── fyi_webportal.db    # SQLite database
    ├── uploads/            # User uploads
    ├── accounts.json       # Connected social accounts
    ├── byok_keys.json      # Encrypted API keys
    └── certs/              # HTTPS certificates
```

## Troubleshooting

### Import Errors
- Ensure virtual environment is activated
- Run: `pip install -r requirements.txt`
- Check Python version: `python --version` (should be 3.9+)

### "ffmpeg not found"
- Install ffmpeg: `brew install ffmpeg` (macOS) or `apt-get install ffmpeg` (Linux)
- Windows: Download from https://ffmpeg.org/

### Database Locked Error
- Close all other instances of the app
- Delete `data/fyi_webportal.db-wal` and `data/fyi_webportal.db-shm` if they exist

### OAuth Not Working
- Verify `.env` credentials are correct
- Ensure `FYI_PUBLIC_BASE_URL` matches your domain
- Check platform developer consoles for whitelisted redirect URLs

### CORS Errors
- Set `FYI_ALLOWED_ORIGINS` in `.env` (comma-separated list)
- Default: `http://localhost:5050,https://localhost:5050`

## API Documentation

Once the server is running, visit:
- **Swagger UI:** `http://localhost:5050/docs`
- **ReDoc:** `http://localhost:5050/redoc`
- **Health Check:** `http://localhost:5050/api/health`

## Development Workflow

1. **Making Changes:**
   - Edit Python files in `core/`, `services/`, `routes/`
   - No restart needed - uvicorn supports hot reload in dev mode

2. **Testing Changes:**
   - Run smoke test: `python scripts/smoke_test_web_server.py`
   - Check API logs for errors

3. **Building for Production:**
   - Build React: `cd desktop && npm run build`
   - Build Docker: `cd deploy && docker build -t fyi:latest ..`

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `FYI_WEB_PORTAL_PORT` | `5000` | Server port |
| `FYI_BIND_HOST` | `127.0.0.1` | Bind address |
| `FYI_PUBLIC_BASE_URL` | `` | Public domain (required for Instagram) |
| `FYI_ALLOWED_ORIGINS` | `localhost:5050` | CORS origins (comma-separated) |
| `FYI_SCHEDULER_ENABLED` | `1` | Enable post scheduler |
| `FYI_SCHEDULER_POLL_SECONDS` | `60` | Scheduler check interval |
| `FYI_DISABLE_HTTPS` | `` | Disable HTTPS self-signed certs |

## Support

For issues or questions:
1. Check `.github/copilot-instructions.md` for architecture details
2. Review API endpoints in `/docs`
3. Check server logs for error messages

