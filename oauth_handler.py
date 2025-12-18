"""Compatibility shim for legacy oauth_handler import path."""

from backend.services.oauth_handler import (  # noqa: F401
    OAuthCallbackHandler,
    OAuthResult,
    get_login_url,
    run_debug_server,
    start_oauth_flow,
)

__all__ = [
    "OAuthCallbackHandler",
    "OAuthResult",
    "get_login_url",
    "run_debug_server",
    "start_oauth_flow",
]
