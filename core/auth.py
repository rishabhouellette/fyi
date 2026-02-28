"""API token authentication middleware.

On first run, generates a random 32-byte Bearer token stored in data/api_token.
All /api/* routes require the token in the Authorization header.
Static files, health, docs and OAuth callbacks are exempt.

Disable auth entirely by setting FYI_DISABLE_AUTH=1 in .env.
"""
import os
import secrets
from pathlib import Path
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

from core.config import DATA_DIR

_TOKEN_FILE = DATA_DIR / "api_token"

# Paths that are always accessible without a token.
_PUBLIC_PREFIXES = (
    "/api/health",
    "/docs",
    "/openapi.json",
    "/redoc",
    "/oauth/",
    "/l/",          # short-link redirects
    "/assets/",     # React static assets
    "/uploads/",    # media files (used by Meta preflight)
)
_PUBLIC_EXACT = {"/", "/favicon.ico"}


def _load_or_create_token() -> str:
    """Return the API token, generating one on first run."""
    if _TOKEN_FILE.exists():
        token = _TOKEN_FILE.read_text(encoding="utf-8").strip()
        if token:
            return token
    token = secrets.token_urlsafe(32)
    _TOKEN_FILE.write_text(token, encoding="utf-8")
    return token


API_TOKEN: str = _load_or_create_token()


def _is_public(path: str) -> bool:
    """Return True if *path* should bypass token auth."""
    if path in _PUBLIC_EXACT:
        return True
    for prefix in _PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return True
    # The SPA catch-all (non /api/* paths) is also public
    if not path.startswith("/api/"):
        return True
    return False


class TokenAuthMiddleware(BaseHTTPMiddleware):
    """Require ``Authorization: Bearer <token>`` on protected routes."""

    async def dispatch(self, request: Request, call_next):
        # Allow bypass via env var for development convenience
        if os.getenv("FYI_DISABLE_AUTH", "").strip() in ("1", "true", "yes"):
            return await call_next(request)

        if _is_public(request.url.path):
            return await call_next(request)

        auth = request.headers.get("authorization", "")
        if auth == f"Bearer {API_TOKEN}":
            return await call_next(request)

        return JSONResponse(
            status_code=401,
            content={"detail": "Missing or invalid API token. Pass Authorization: Bearer <token>."},
        )
