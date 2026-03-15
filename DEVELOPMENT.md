# FYIXT Development Guide

## Architecture Overview

FYIXT follows a modular, layered architecture:

```
FastAPI (web_server.py)
    ↓
Routes (routes/) - HTTP endpoints
    ↓
Services (services/) - Business logic
    ↓
Core (core/) - Configuration & utilities
    ↓
Database (app_db.py) - SQLite persistence
```

## Key Modules

### `core/config.py`
- **Purpose:** Centralized configuration management
- **Key Functions:**
  - `_load_env_files()` - Load `.env` file
  - `_get_byok_key(service)` - Get API keys (user → env → defaults)
  - `_get_platform_credential(platform, key)` - Get OAuth credentials
- **Globals:** `db` (AppDB singleton), encryption key management

### `core/utils.py`
- **Purpose:** Shared utilities across modules
- **Key Functions:**
  - `_progress_set(job_id, ...)` - Track job progress
  - `_parse_iso_loose(value)` - Parse ISO timestamps
  - `_ollama_generate(prompt, model)` - LLM inference
  - `_ffmpeg_*` - Video processing wrappers

### `services/accounts.py`
- **Purpose:** Social media account management
- **Key Functions:**
  - `find_account_by_id(account_id)` - Lookup account
  - `get_active_account(platform)` - Get currently selected account
  - `save_active_account(platform, account_id)` - Persist selection

### `services/platforms.py`
- **Purpose:** Platform-specific upload/publish logic
- **Key Functions:**
  - `_facebook_resumable_upload()` - Upload to Facebook
  - `_youtube_resumable_upload()` - Upload to YouTube
  - `_instagram_resumable_upload()` - Upload to Instagram
  - `_ensure_youtube_access_token()` - OAuth token refresh

### `services/scheduler.py`
- **Purpose:** Background post scheduling
- **Key Functions:**
  - `_scheduler_loop()` - Main background loop
  - `_execute_due_post(post)` - Execute scheduled post

### `routes/api_routes.py`
- **Purpose:** Core API endpoints
- **Endpoints:**
  - `GET /api/health` - Health check
  - `POST /api/accounts` - Account CRUD
  - `GET /oauth/start/{platform}` - OAuth initiation
  - `POST /api/schedule/post` - Schedule single post
  - `POST /api/schedule/bulk` - Bulk schedule posts

### `routes/ai_routes.py`
- **Purpose:** AI-powered content generation
- **Endpoints:**
  - `POST /api/ai/caption` - Generate captions
  - `POST /api/ai/hashtags` - Generate hashtags
  - `POST /api/ai/image/generate` - Generate images
  - `POST /api/ai/video/generate` - Generate videos
  - `POST /api/xy-ai/trends` - Fetch XY-AI trends

### `routes/media_routes.py`
- **Purpose:** File uploads, video processing, analytics
- **Endpoints:**
  - `POST /api/upload` - Upload file
  - `POST /api/video/process` - Process video
  - `POST /api/video/faceless` - Create faceless video
  - `GET /l/{slug}` - Short link redirect
  - `GET /api/analytics/{link_id}` - Analytics

### `app_db.py`
- **Purpose:** SQLite database abstraction
- **Key Methods:**
  - `insert_scheduled_post(post)` - Add scheduled post
  - `list_due_scheduled_posts()` - Get posts to execute
  - `mark_scheduled_post_result()` - Update post status

## Adding a New Feature

### Example: Add a New Platform (TikTok)

1. **Update `services/accounts.py`:**
   ```python
   def _load_tiktok_account(account_id: str) -> dict:
       # Load TikTok-specific credentials
       pass
   ```

2. **Add upload logic to `services/platforms.py`:**
   ```python
   async def _tiktok_resumable_upload(
       file_path: Path,
       upload_url: str,
       access_token: str,
       ...
   ) -> dict:
       # Upload to TikTok
       pass
   ```

3. **Add API endpoint in `routes/api_routes.py`:**
   ```python
   @router.post("/api/platforms/tiktok/upload")
   async def upload_to_tiktok(request: TikTokUploadRequest):
       # Call service layer
       pass
   ```

4. **Update models in `core/models.py`:**
   ```python
   class TikTokUploadRequest(BaseModel):
       video_path: str
       caption: str
       # ...
   ```

## Testing Guidelines

### Unit Tests
Create tests in `tests/test_<module>.py`:
```python
import pytest
from services.accounts import find_account_by_id

@pytest.mark.asyncio
async def test_find_account():
    result = find_account_by_id("test_id")
    assert result is not None
```

### Integration Tests
Test end-to-end flows (use `scripts/smoke_test_web_server.py` as reference):
```python
async with httpx.AsyncClient(app=app, base_url="http://test") as client:
    response = await client.post("/api/schedule/post", json=payload)
    assert response.status_code == 200
```

### Running Tests
```bash
pytest tests/ -v  # Run all tests
pytest tests/test_accounts.py -v  # Run specific test file
```

## Performance Considerations

### Database
- SQLite suitable for up to ~10k concurrent users
- For higher load, migrate to PostgreSQL
- Index frequently queried columns (e.g., `scheduled_posts.status`, `scheduled_posts.due_at`)

### API Concurrency
- FastAPI uses async/await for concurrent requests
- Use `asyncio.gather()` for parallel operations (e.g., multi-platform uploads)
- Rate limiting: 120 req/min per IP (configurable via `slowapi`)

### Background Tasks
- Scheduler polls every 60s by default (set `FYI_SCHEDULER_POLL_SECONDS`)
- Use AsyncIO for long-running tasks to avoid blocking
- Consider Celery for distributed task queue if scaling beyond single server

## Security Best Practices

1. **Credential Storage:**
   - BYOK keys encrypted with Fernet
   - OAuth tokens stored in secure DB
   - Never log credentials or tokens

2. **API Authentication:**
   - Token-based middleware validates all requests
   - Token generated and injected into React frontend
   - Regenerate tokens on sensitive operations

3. **CORS & HTTPS:**
   - CORS origins whitelisted via `FYI_ALLOWED_ORIGINS`
   - HTTPS enforced in production
   - Self-signed certs for development

4. **Input Validation:**
   - All endpoints use Pydantic models for validation
   - No SQL injection possible (using parameterized queries)
   - HTML/script injection prevented in content fields

## Debugging Tips

### Enable Verbose Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Inspector Database
```python
from app_db import AppDB
db = AppDB("data/fyi_webportal.db")
posts = db.list_scheduled_posts()
for post in posts:
    print(post)
```

### Test OAuth Flow
```bash
curl -X GET "http://localhost:5050/oauth/start/facebook" -H "Authorization: Bearer <token>"
```

### Monitor Scheduler
Check logs for lines like:
```
[SCHEDULER] Found 3 due posts
[SCHEDULER] Executing post 12345 → facebook
[SCHEDULER] Post published successfully
```

## Common Issues

| Problem | Solution |
|---------|----------|
| "Token required" | Ensure `API_TOKEN` is in `.env` or use browser (auto-injected) |
| "Platform not connected" | Create account via `/api/accounts` endpoint first |
| "Video processing failed" | Check ffmpeg installed: `ffmpeg -version` |
| "Database locked" | Close other instances, delete `*.db-wal` files |
| "CORS error" | Add origin to `FYI_ALLOWED_ORIGINS` in `.env` |

## Deployment Checklist

- [ ] Set production environment variables
- [ ] Build React frontend: `cd desktop && npm run build`
- [ ] Run smoke tests: `python scripts/smoke_test_web_server.py`
- [ ] Generate HTTPS cert (or use Let's Encrypt)
- [ ] Set up reverse proxy (nginx)
- [ ] Enable database backups
- [ ] Monitor scheduler logs
- [ ] Setup error alerting

