# Copilot instructions (FYIUploader)

## Golden path (run/debug)
- **Primary launcher (Windows):** run `start.bat` (spawns venv-activated terminals and exports FYI_* env vars).
- **Manual equivalent:** `python main.py` (UI) + `python -m backend.main` (backend spine). See `HOW_TO_RUN.txt`.
- **Regression suite:** `python test_e2e.py --verbose` (logs to `test_e2e.log`). See `TESTING_GUIDE.md`.

## Architecture map (what talks to what)
- **NiceGUI UI shell:** `main.py` (serves UI and boots OAuth server thread).
- **Backend spine:** `backend/main.py` initializes DB, OAuth registry, BYOK manager, then starts OAuth + NiceGUI.
- **Local OAuth service (source of truth):** `backend/services/local_oauth.py` runs HTTPS callback at `FYI_OAUTH_REDIRECT` (default `https://127.0.0.1:5000/oauth/callback`).
- **Legacy/compat:** `server.py` and top-level `oauth_handler.py`/`account_manager.py` are shims; prefer edits under `backend/services/*`.
- **Standalone legacy integration API:** `api_server.py` (HTTPServer) reads/writes via `database_manager.py`.
- **Tauri bridge API:** `desktop_api.py` is a separate Flask API and also hosts `https://127.0.0.1:5000/callback` for older desktop flows.

## Config & ports (two config systems)
- **Backend config:** `backend/config.py` reads `.env` keys like `FYI_WEB_PORT` (default `8080`), `FYI_API_PORT` (default `5000`), `FYI_OAUTH_REDIRECT`.
- **Legacy uploader/OAuth config:** top-level `config.py` expects `FB_APP_ID`, `FB_APP_SECRET`, `OAUTH_REDIRECT_ORIGIN` and builds `${OAUTH_REDIRECT_ORIGIN}/callback`.
- **Port convention (per `start.bat`):** backend UI `:8000`, NiceGUI UI `:8080`, OAuth callback `:5000`.

## Data & state conventions
- **SQLite source of truth:** `database_manager.py` with schema applied from `database_schema.sql`; DB file `data/fyi_social_media.db`.
- **Multi-tenant filtering:** many DB calls take `team_id`; keep it consistent (see `ARCHITECTURE.txt`).
- **Accounts/tokens:** accounts commonly in `accounts/accounts.json`; platform token artifacts often in `data/`.

## Project-specific code patterns
- **UI modules:** feature tabs live in `ui_*.py` (e.g. `ui_calendar.py`, `ui_bulk_upload.py`, `ui_analytics.py`).
- **Per-platform uploaders:** `facebook_uploader.py`, `instagram_uploader.py`, `youtube_uploader.py`.

## Gotchas (common agent mistakes here)
- **Editing a shim:** top-level `oauth_handler.py`/`account_manager.py` mainly re-export from `backend/services/*`; change the backend implementation unless you’re intentionally patching legacy imports.
- **Two DB layers exist:** `database_manager.py` (schema from `database_schema.sql`, team_id-centric) vs `backend/database.py` (its own tables, optional Supabase). Don’t mix APIs accidentally.
- **OAuth callback paths differ:** backend OAuth default is `/oauth/callback` (`FYI_OAUTH_REDIRECT`), while legacy desktop flow in `config.py` uses `/callback` (`OAUTH_REDIRECT_ORIGIN`). Verify which flow you’re touching before changing URLs.
