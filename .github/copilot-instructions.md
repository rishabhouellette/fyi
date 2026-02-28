# Copilot instructions (FYIXT)

## Golden path (run/debug)
- **Primary launcher (Windows):** run `start.bat` — activates venv, optionally starts ngrok, builds React frontend (`desktop/dist`), then starts FastAPI via `web_server.py`.
- **Manual equivalent:** `python web_server.py --https --port 5050`
- **Smoke test:** `python scripts/smoke_test_web_server.py`

## Architecture (modular single-server)
- **Entry point:** `web_server.py` (~120 lines) — creates the FastAPI app, wires CORS, registers routes, starts the scheduler, serves the React SPA. All business logic has been extracted into modules.
- **Module layout:**
  - `core/config.py` — paths, env loading, DB singleton, credential helpers (BYOK, platform creds, usage tracking)
  - `core/models.py` — all Pydantic request/response models
  - `core/utils.py` — progress tracking, text/URL helpers, scheduled-posts I/O, Ollama helpers, ffmpeg wrappers
  - `services/accounts.py` — `AccountManager`, account lookup helpers, active-account persistence
  - `services/platforms.py` — Facebook, YouTube, Instagram upload/publish implementations
  - `services/scheduler.py` — background scheduler loop (`_scheduler_loop`, `_execute_due_post`)
  - `routes/api_routes.py` — health, accounts, OAuth, scheduling, BYOK, platform credentials, usage
  - `routes/ai_routes.py` — AI captions, hashtags, XY-AI engine (prompts, trends, chat, content plan), image/video/voice generation, translation
  - `routes/media_routes.py` — file uploads, video processing, links, content ingestion, templates, guides, analytics
  - `routes/__init__.py` — `register_routes(app)` wires all routers
- **Dependency graph:** `core/` ← `services/` ← `routes/` ← `web_server.py` (no circular imports)
- **Database layer:** `app_db.py` — `AppDB` class wrapping SQLite (`data/fyi_webportal.db`). Handles accounts, scheduled posts, links, click tracking.
- **No separate backend/frontend servers.** One process on one port.
- **Backups:** `web_server_backup.py` and `web_server_original.py` are archived copies of the pre-split monolith.

## Config & ports
- **Environment:** `.env` at project root, loaded by `core/config.py` on import via `python-dotenv` (with manual fallback parser).
- **Default port:** `5050` (HTTPS with self-signed cert). Set via `FYI_WEB_PORTAL_PORT` env var.
- **Key env vars:** `FB_APP_ID`, `FB_APP_SECRET` (Facebook/Instagram OAuth), `YT_CLIENT_ID`, `YT_CLIENT_SECRET` (YouTube OAuth), `GOOGLE_API_KEY` (Gemini AI), `FYI_PUBLIC_BASE_URL` (ngrok public URL for Instagram).
- **HTTPS:** Self-signed cert auto-generated at `data/certs/localhost.crt|.key`. Disable with `FYI_DISABLE_HTTPS=1`.

## Data & state
- **SQLite DB:** `data/fyi_webportal.db` — accounts, scheduled posts, links, clicks (via `app_db.py`).
- **JSON files (read/written by services & routes):**
  - `accounts/accounts.json` — connected social media accounts
  - `data/active_accounts.json` — currently selected account per platform
  - `data/byok_keys.json` — BYOK API keys (OpenAI, Gemini, xAI, Anthropic, ElevenLabs, etc.)
  - `data/scheduled_posts.json` — backup mirror of scheduled posts (SQLite is source of truth)
  - `data/usage_credits.json` — AI usage/credits tracking
- **Credential backup:** `data/credentials/youtube_client_secret.json` (Google Console download, not read by code — values are in `.env`)
- **Runtime dirs:** `data/uploads/`, `data/library/`, `data/ai_jobs/`

## API route domains
- `/api/health`, `/api/config`, `/api/growth` — health & config → `routes/api_routes.py`
- `/api/accounts/*`, `/api/active-accounts` — account CRUD → `routes/api_routes.py`
- `/oauth/start/{platform}`, `/oauth/callback/*` — Facebook + YouTube OAuth → `routes/api_routes.py`
- `/api/schedule/*`, `/api/publish/*`, `/api/scheduled-posts/*` — scheduling & publishing → `routes/api_routes.py`
- `/api/platforms/facebook/upload`, `/api/platforms/youtube/upload`, `/api/platforms/instagram/publish` — platform uploads → `routes/api_routes.py`
- `/api/byok/*`, `/api/platform-credentials/*`, `/api/usage/*` — settings & keys → `routes/api_routes.py`
- `/api/xy-ai/*` — XY-AI engine (prompts, trends, content plan, chat, niches) → `routes/ai_routes.py`
- `/api/ai/*` — AI studio (caption, hashtags, image, video, voice, translate) → `routes/ai_routes.py`
- `/api/content/*`, `/api/templates/*` — content ingestion & templates → `routes/media_routes.py`
- `/api/video/*` — video processing, faceless video, scoring → `routes/media_routes.py`
- `/api/links/*`, `/l/{slug}` — short links → `routes/media_routes.py`
- `/api/analytics/*` — analytics & CSV export → `routes/media_routes.py`
- `/api/upload`, `/uploads/{file_id}` — file uploads → `routes/media_routes.py`
- `/api/guides/*` — social media guides → `routes/media_routes.py`

## AI integration
- **BYOK system:** 12 services (openai, anthropic, gemini, xai, elevenlabs, stability, replicate, runway, pika, kling, flux, ideogram). Keys stored in `data/byok_keys.json`.
- **Key priority:** BYOK store → environment variables → bundled default (Gemini only, obfuscated in `_get_default_key()`).
- **Chat cascade:** Ollama → OpenAI → Gemini (with Google Search grounding) → xAI → Anthropic → offline fallback.
- **Gemini model:** `gemini-2.5-flash` (free tier). Google Search grounding enabled via `"tools": [{"google_search": {}}]`.

## Gotchas
- **Global credential mutation:** `set_platform_credentials` in `routes/api_routes.py` writes to `cfg.FB_APP_ID` etc. via `import core.config as cfg`.
- **OAuth callbacks:** Facebook uses `/oauth/callback/facebook` and `/callback` (both registered). YouTube uses `/oauth/callback/youtube`.
- **Scheduled posts dual storage:** SQLite is source of truth, but `scheduled_posts.json` is kept as a backup mirror and one-time migration source.
- **No frontend source code in repo:** React app is built externally and served from `desktop/dist/`. If `desktop/` doesn't exist, the server runs API-only.
- **`data/.encryption_key`** is used for credential encryption — do not delete.
- **Cross-route import:** `routes/media_routes.py` imports `ai_generate_voice` from `routes/ai_routes.py` for the faceless-with-voice endpoint. No circular dependency exists.
