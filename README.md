"# FYI Uploader - FIXED & COMPLETE VERSION

## What Was Fixed

### Critical Issues in Your New Code:
1. **Hardcoded Credentials** - FB_APP_ID, FB_APP_SECRET hardcoded in multiple files
2. **Broken Facebook Upload** - Simplified uploader missing proper chunked upload flow
3. **Missing Account Manager** - No multi-account system
4. **Missing Config System** - Direct os.getenv() calls
5. **Missing Logger** - No proper logging
6. **Missing Validator** - No video validation
7. **Missing Smart Scheduler** - Feature removed from new version

### Solution - Files Provided:
All working files from your OLD version have been restored and integrated with your NEW GUI:

1. **config.py** - Configuration management with .env support
2. **exceptions.py** - Custom exception classes
3. **logger_config.py** - Colored logging with file rotation
4. **account_manager.py** - Multi-account support with JSON storage
5. **facebook_uploader.py** - WORKING Facebook uploader with resumable uploads
6. **video_validator.py** - OpenCV-based video validation
7. **oauth_handler.py** - Embedded OAuth callback (no ngrok, secure state handling)
8. **scheduler_engine.py** - Background scheduler

## Phase 0 Stabilization Pack (Completed Now)

- **Legacy UI preserved**: `main.py` boots the battle-tested Tk interface by loading the compiled legacy module first, then layering the new services so every uploader keeps working while we refactor in Phase 1.
- **Embedded OAuth + HTTPS-ready**: `oauth_handler.py` now wraps the callback server with TLS whenever `SSL_CERT_FILE`/`SSL_KEY_FILE` are set and `OAUTH_REDIRECT_ORIGIN` uses `https://`. See the “OAuth HTTPS Setup” section in `HOW_TO_RUN.txt` for mkcert instructions.
- **Quality-of-life desktop upgrades**: Window geometry persistence (`data/window_state.json`), Theme Studio tab, runtime theme overrides, Ctrl/Cmd keyboard shortcuts, native drag-and-drop queue intake, and one-click compact mode are all wired into `main.py`.
- **Documentation + tests in sync**: This README and `HOW_TO_RUN.txt` describe the new flow, and `test_e2e.py` (82 checks) passes end-to-end so the branch is safe for upcoming aggressive refactors.

## Phase 1 FastAPI Spine (Active)

- **Backend folder**: `backend/` now houses the FastAPI app, NiceGUI preview, schemas, and shared services (`account_manager`, `scheduler_engine`, `oauth_handler`). See `backend/README.md` for commands.
- **REST endpoints**: `/api/accounts`, `/api/scheduler/summary`, `/queue/summary`, and `/api/oauth/login-url` expose current desktop data so future UIs can consume the same core without duplicating logic.
- **Desktop bridge**: `compat/backend_bridge.py` lets `main.py` auto-detect the backend. When the FastAPI server is online the desktop pulls queue/account snapshots; otherwise it runs in legacy mode with zero user intervention.

## Phase 2 AI Engine (In Progress)

- **ai_engine/**: Houses Ollama manager, clip scoring heuristics, hook generator (LLM-backed with fallback), thumbnail stubs, and template registry.
- **video_lab/**: Contains auto-editor pipeline, caption burner, b-roll suggester, and audio detector scaffolds that currently run in dry-run mode (mock outputs).
- **New APIs**: `/api/ai/hooks`, `/api/ai/thumbnails`, `/api/ai/pipeline/long-to-short` now return structured data so desktop/web can preview AI output before full GPU integration.
- **Workers**: `backend/workers/pipeline.py` provides a thread-based queue for pipelines until Celery lands.

## File Structure

```
/app/backend/
\u251c\u2500\u2500 config.py                 # Configuration management
\u251c\u2500\u2500 exceptions.py             # Custom exceptions
\u251c\u2500\u2500 logger_config.py          # Logging setup
\u251c\u2500\u2500 account_manager.py        # Multi-account management
\u251c\u2500\u2500 facebook_uploader.py      # Facebook upload logic (FIXED)
\u251c\u2500\u2500 video_validator.py        # Video validation
\u251c\u2500\u2500 server.py                 # Legacy shim (proxies to oauth_handler)
\u251c\u2500\u2500 scheduler_engine.py       # Upload scheduler
\u251c\u2500\u2500 .env.example             # Environment variables template
\u251c\u2500\u2500 main.py                   # YOUR GUI (keep your existing one)
\u251c\u2500\u2500 youtube_uploader.py       # YouTube uploader (keep your existing one)
\u2514\u2500\u2500 instagram_uploader.py     # Instagram uploader (keep your existing one)
```

## Installation Steps

### 1. Copy All Files
Copy all the files I provided to your project directory.

### 2. Create .env File
```bash
cp .env.example .env
```

Edit `.env` and add your credentials:
```ini
FB_APP_ID=222188858294490
FB_APP_SECRET=6f1c65510e626e9bb45fd5d2f52f8565
OAUTH_REDIRECT_ORIGIN=http://127.0.0.1:5000  # defaults to localhost
```

### 3. Remove Hardcoded Credentials from main.py
If your legacy UI hard-coded credentials inside `main.py`, **delete the block** that forced env vars, e.g.:
```python
# DELETE THIS ENTIRE BLOCK:
os.environ['FB_APP_ID'] = '222188858294490'
os.environ['FB_APP_SECRET'] = '6f1c65510e626e9bb45fd5d2f52f8565' 
os.environ['FB_PAGE_ID'] = '786958508088541'
os.environ['FB_REDIRECT_URI'] = 'http://127.0.0.1:5000/callback'
```

Replace with:
```python
from config import get_config
config = get_config()  # This loads from .env automatically
```

### 4. Update main.py Imports
At the top of `main.py`, add:
```python
from config import get_config
from account_manager import get_account_manager
from logger_config import get_logger

logger = get_logger(__name__)
config = get_config()
account_manager = get_account_manager()
```

### 5. Install Dependencies
```bash
pip install -r requirements.txt
```

## How to Use

### Step 1: Launch FYI Social
- Double-click `start.bat` and choose option **1** (Desktop) or run `python main.py` from the venv.
- The embedded OAuth handler spins up automatically when you click any **Connect** button.

### Step 2: Connect Accounts (Embedded OAuth)
1. Click **Connect Facebook/Instagram** inside the Accounts panel.
2. Your default browser opens to Facebook's login + permission screen.
3. After granting access, a `Success!` tab appears (served from `127.0.0.1`).
4. Close that tab — the desktop app instantly shows “Connected as …”.

No ngrok, second terminal, or manual server startup is required. Each OAuth run opens the local callback server on demand and shuts it down automatically.

Need to troubleshoot? Run `python oauth_handler.py` to keep the callback server alive for a single request. Override `OAUTH_REDIRECT_ORIGIN` in `.env` if you need to test a different port or hostname.

# FYI Uploader (November 2025)

Self-hosted, open-source social media control center for creators, agencies, and automation builders who want Blotato-level power without monthly fees.

## 1. Production-Ready Today

- **Multi-platform uploaders**: Facebook, Instagram, YouTube, X/Twitter, LinkedIn, Pinterest, WhatsApp, Telegram (TikTok stub).
- **Scheduling suite**: Instant, interval, and Smart Scheduler with failure recovery (`scheduler_engine.py`).
- **Team & security**: Role-based access, audit logs, encrypted tokens (Fernet), centralized config + logging.
- **Content operations**: Library with tagging/search, analytics dashboards (`ui_analytics.py`), first-comment + hashtag automation, REST API/webhooks.
- **Remix Lab**: URL/text/file ingestion that auto-generates platform-specific drafts with history tracking (`remix_service.py`, `ui_ai_content.py`).
- **Faceless Video Lab**: Script-to-video generation with synthesized voiceovers and slide automation (`video_ai_service.py`, `ui_ai_content.py`).
- **Testing**: `test_e2e.py` regression suite covering 80+ flows.
- **Browser control center**: FastAPI + NiceGUI interface (`python -m web.app`) exposing Automation Lab, Research Lab, and Viral Coach for remote teams.

## November 2025 Desktop Upgrade

- **Research Lab tab** now renders the Viral Inspiration feed, Hook Library, and Brand Kits directly inside the CustomTkinter app (see `ui_research_lab.py`).
- **Automation Lab tab** brings Smart Timing, Recycling Queue, thread/carousel generators, and the Viral Coach into the desktop UI (see `ui_automation_lab.py`).
- **Access**: Run `python main.py` (or `start.bat` option 1/2) and the tabs appear alongside the legacy surfaces without extra config.
- **Web parity**: Browser UI (`python -m web.app`) remains available for teams that prefer NiceGUI, but both surfaces now show the same labs.
- **Dependencies**: `requirements.txt` already ships CustomTkinter + AI helpers; reinstall (`pip install -r requirements.txt`) if the new tabs log missing modules.

## 2. Blotato Feature Parity Checklist

| # | Feature | FYI Status | Gap Plan |
| - | ------- | ---------- | -------- |
| 1 | Unlimited AI Writing | Grok/Ollama hooks shipped via `ui_ai_content.py`. | ✅ |
| 2 | Remix Engine | Not built. | Phase 1 |
| 3 | Faceless Video Generator | Not built. | Phase 1 |
| 4 | AI Image Generator | Uses local SD pipelines. | ✅ |
| 5 | Native 9-platform posting | 8/9 live (TikTok pending). | Phase 1 |
| 6 | Content Calendar | CustomTkinter calendar done. | ✅ |
| 7 | Viral Inspiration DB | **New:** Creative Research Lab with viral feed + heatmaps. | ✅ |
| 8 | Auto Hashtag Generator | `ui_hashtag_tools.py`. | ✅ |
| 9 | First Comment Automation | `ui_first_comments.py`. | ✅ |
|10 | Caption Variations | Basic rewrite support. | Iterate |
|11 | Hook Library | **New:** Hook + Prompt library JSON store + UI. | ✅ |
|12 | Voice Library | Limited voices; extend via ElevenLabs. | Phase 1.5 |
|13 | Stock Footage Integration | Brand Kit service + Pexels-ready stock search. | Beta |
|14 | Auto Subtitles | Burn-in + SRT export shipping in Video Lab. | ✅ |
|15 | Analytics Dashboard | Live. | ✅ |
|16 | Team Collaboration | Live (roles + approvals). | ✅ |
|17 | n8n/Make Nodes | Importable n8n collection + Make blueprint/connection templates. | ✅ |
|18 | Weekly Office Hours | Playbook + log templates (`OFFICE_HOURS_PLAYBOOK.md`, `office-hours-log.md`). | ✅ |
|19 | Prompt Library | Missing. | Phase 2 |
|20 | Auto-Scheduling | Smart timing matrix (`automation_insights.py`). | ✅ |
|21 | Content Recycling | Recycling queue + auto reschedule suggestions. | ✅ |
|22 | Thread Generator | Thread/Carousel lab inside Automation tab. | ✅ |
|23 | Carousel Generator | Thread/Carousel lab inside Automation tab. | ✅ |

## 3. Execution Roadmap

### Phase 1 – Feature Parity Blockers (Now → Week 2)
- **Remix Service**: `services/remix_service.py` + Whisper + Grok; output drafts to content library.
- **Faceless Video Lab**: `services/video_ai.py` integrating HeyGen/ComfyUI + moviepy subtitles.
- **TikTok Native Uploader**: Complete OAuth + upload chunks, add fallback instructions.
- **Voice & Subtitle Enhancements**: ElevenLabs/XTTS integration, inline subtitle burn-in.

### Phase 2 – Research & Ideation (Week 3)
- **Viral Inspiration DB**: *Shipped via `viral_inspiration_service.py` + `ui_research_lab.py`.* Surfaced top-performing hooks, metrics heatmap, and nightly refresh button.
- **Hook + Prompt Library**: *Shipped via `creative_library.py`.* JSON-backed hooks/prompts rendered inside the Research Lab for quick copy/paste.
- **Stock + Brand Kits**: *Shipped via `brand_kit_service.py` with optional Pexels key.* Brand palette viewer + stock lookup embedded in the Research Lab.

### Phase 3 – Automation Intelligence (Week 4)
- **Auto-Scheduling & Recycling**: *Delivered via `automation_insights.py` + `ui_automation_lab.py`.* Learns hourly windows, produces auto-queue drafts, and flags high-performing posts for recycling.
- **Thread/Carousel Generators**: *Delivered in Automation Lab Generators tab.* Uses updated `ai_engine.py` helpers to spit out thread beats + 10-slide outlines.
- **Viral AI Coach**: *Delivered via `viral_coach.py` with UI hooks.* Scores hooks/pacing/CTA and reuses `video_validator.py` for technical checks.

### Phase 4 – Integrations & Web Parity (Week 5)
- **Official n8n/Make Nodes** *(shipped in `integrations/n8n` and `integrations/make/`)*: importable workflow packs plus reusable HTTP credentials for both automation suites. Includes `.env` template + `integrations/smoke_test.py` so partners can verify keys before distributing the packs.
- **Web/Tauri Frontend** *(NiceGUI parity in `backend/app.py` + shell in `tauri/`)*: Content Calendar + Bulk Upload tabs now mirror the desktop experience, and the Tauri scaffold ships a desktop window that boots `python -m backend.main` automatically. See `tauri/DISTRIBUTION.md` for signing, lab build, and rollout instructions.
- **Next.js Pro Portal** *(new in `web/next-portal/`)*: Calendar view now reads `/api/v1/posts`, and the Bulk Upload page parses CSVs client-side before calling the secured endpoints. Tailwind + Vitest scaffolding keeps SaaS-facing experiences aligned with the desktop/NiceGUI surfaces.
- **API Hardening**: Centralized API-key middleware plus a per-key rate limiter protect `/api/v1/*` and the legacy `api_server.py`. All clients (portal, websocket, CLI, integrations) send `X-FYI-Key` + `X-Team-ID` and transparently support `?key=` fallbacks for browsers.

### Phase 5 – Community Layer (Complete)
- **Office Hours Live**: Playbook + log templates (`OFFICE_HOURS_PLAYBOOK.md`, `office-hours-log.md`) codify cadence, tooling, escalation paths, and metrics.
- **Knowledge Base Refresh**: Persona navigation finalized in `DOCUMENTATION_INDEX.md`, `PHASE_5_PLAN.md`, and the new `docs/` folder (customers, ops, developers, partners) ready for Notion/static exports.
- **Release Notes Feed**: `RELEASE_NOTES.md` now tracks per-phase drops + QA snapshots so leadership can skim deltas quickly.
- **Partner Enablement**: `tauri/DISTRIBUTION.md` updated with signed-build workflow, and integrations docs reference smoke tests + KB links for marketplace submissions.
- **Release Notes Feed** (`RELEASE_NOTES.md`): Timestamped summary of each Phase delivery and QA snapshot for stakeholders.

## 4. Setup & Operation (Quick Reference)

```bash
# 1) Install dependencies
pip install -r requirements.txt

# 2) Launch the new FastAPI backend (serves REST + NiceGUI shell)
python backend/main.py

# 3) Launch desktop UI (fires embedded OAuth when needed)
python main.py

# 4) Launch the legacy browser UI (optional)
python -m web.app

# 5) Launch the Next.js Pro portal (Phase 3 web surface)
cd web/next-portal && npm install && npm run dev

# 6) Optional: launch the new Tauri shell (Phase 4 desktop wrapper)
cd tauri && npm install && npm run dev

# 7) Run the OAuth handler manually (debug only)
python oauth_handler.py
```

- Environment lives in `.env` (see `.env.example`). Add `API_RATE_LIMIT_PER_MINUTE` if you need tighter throttling for public deployments.
- Accounts + tokens stored under `accounts/` (encrypted via Fernet key in config).
- Logs drop into `logs/*.log`; scheduler + uploader errors surface in UI as well.

## 5. Testing & Quality Gates

- `python -m pytest test_e2e.py` before shipping UI or uploader changes.
- Lint via `ruff check .` (see `requirements.txt`).
- Each new feature (Remix, Video Lab, etc.) must add unit tests + e2e coverage.
- Use `python -m web.app` locally plus `uvicorn web.app:fastapi_app` during deployment drills to ensure the browser UI stays green. Run `npm run dev` inside `web/next-portal` for the App Router dashboard once Node deps are installed.
- Read `WEB_FRONTEND.md` for design notes and endpoint references when extending the browser UI.
- **Latest QA snapshot (2025-11-22)**: `D:/FYIUploader/venv/Scripts/python.exe -m pytest` (6 backend API tests) and `npm run test` inside `web/next-portal` (Vitest suite) both pass.
- See `RELEASE_NOTES.md` for historical QA snapshots and feature drops.

## 6. Contributing Notes

- Keep modules ASCII-only unless legacy file already uses Unicode.
- Prefer new services in `services/` with docstrings explaining threading/async expectations.
- Update this README when roadmap milestones move or new features land.

---

FYI Uploader already replaces $1k+/mo worth of SaaS. This roadmap documents exactly how we reach full Blotato parity without sacrificing the self-hosted advantage.