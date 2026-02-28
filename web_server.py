"""
FYI Social ∞ — Unified Web Server (modular)

Serves React frontend + FastAPI backend on a single port.
All business logic lives in core/, services/ and routes/.
This file only wires them together with middleware and static-file serving.
"""
import os
import sys
import asyncio
import argparse
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Ensure project root is importable so `core.*`, `services.*`, `routes.*` resolve.
PROJECT_DIR = Path(__file__).parent
sys.path.insert(0, str(PROJECT_DIR))

# Importing core.config triggers env-file loading, directory creation and DB init.
import core.config as cfg                      # noqa: E402
from core.config import _ensure_dev_https_cert  # noqa: E402
from routes import register_routes              # noqa: E402
from services.scheduler import _scheduler_loop  # noqa: E402
from core.auth import TokenAuthMiddleware, API_TOKEN  # noqa: E402

# ─── FastAPI app ──────────────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])
app = FastAPI(title="FYIXT API", version="2.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ─── CORS ─────────────────────────────────────────────────────────────────────

def _get_allowed_origins() -> list[str]:
    raw = os.getenv("FYI_ALLOWED_ORIGINS", "").strip()
    if not raw:
        return ["http://localhost:5050", "https://localhost:5050",
                "http://127.0.0.1:5050", "https://127.0.0.1:5050"]
    return [o.strip() for o in raw.split(",") if o.strip()]

_allowed_origins = _get_allowed_origins()
_allow_credentials = _allowed_origins != ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Token authentication (add after CORS so pre-flight OPTIONS works)
app.add_middleware(TokenAuthMiddleware)


# ─── Routes ──────────────────────────────────────────────────────────────────

register_routes(app)


# ─── Scheduler ────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def _startup_scheduler() -> None:
    asyncio.create_task(_scheduler_loop())


# ─── React SPA serving ───────────────────────────────────────────────────────

REACT_BUILD_DIR = PROJECT_DIR / "desktop" / "dist"

if REACT_BUILD_DIR.exists():
    app.mount("/assets", StaticFiles(directory=REACT_BUILD_DIR / "assets"), name="assets")


@app.get("/{path:path}")
async def serve_react(path: str):
    """Serve React app for all non-API routes."""
    if REACT_BUILD_DIR.exists():
        file_path = (REACT_BUILD_DIR / path).resolve()
        # Prevent path traversal — file must stay inside the build dir
        if file_path.is_relative_to(REACT_BUILD_DIR.resolve()) and file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
        index_path = REACT_BUILD_DIR / "index.html"
        if index_path.exists():
            # Inject API token into the HTML so the SPA can authenticate
            html = index_path.read_text(encoding="utf-8")
            token_script = f'<script>window.__FYI_TOKEN="{API_TOKEN}";</script>'
            html = html.replace("</head>", f"{token_script}</head>", 1)
            return HTMLResponse(content=html)

    return JSONResponse(
        content={
            "message": "FYIXT API is running. Build the React app to see the UI.",
            "api_docs": "/docs",
            "health": "/api/health",
        }
    )


# ─── Entrypoint ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", 5000)))
    parser.add_argument("--https", action="store_true", help="Serve HTTPS with a self-signed localhost cert")
    parser.add_argument("--ssl-certfile", type=str, default=os.getenv("FYI_SSL_CERTFILE", ""))
    parser.add_argument("--ssl-keyfile", type=str, default=os.getenv("FYI_SSL_KEYFILE", ""))
    args = parser.parse_args()

    ssl_certfile = args.ssl_certfile.strip() if args.ssl_certfile else ""
    ssl_keyfile = args.ssl_keyfile.strip() if args.ssl_keyfile else ""
    if args.https:
        if not ssl_certfile or not ssl_keyfile:
            ssl_certfile, ssl_keyfile = _ensure_dev_https_cert()

    bind_host = os.getenv("FYI_BIND_HOST", "127.0.0.1").strip()
    uvicorn.run(
        app,
        host=bind_host,
        port=args.port,
        reload=False,
        ssl_certfile=ssl_certfile or None,
        ssl_keyfile=ssl_keyfile or None,
    )
