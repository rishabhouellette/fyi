"""Legacy OAuth helpers kept for backwards compatibility.

FYI Social no longer needs Ngrok or a dedicated Flask server. When older
scripts import :mod:`server` we proxy every call to the new
``oauth_handler`` module so the workflow keeps functioning while we ship
the embedded 127.0.0.1 callback experience.
"""
from __future__ import annotations

from oauth_handler import get_login_url, run_debug_server, start_oauth_flow

__all__ = [
    "get_login_url",
    "get_login_url_for_ig",
    "start_oauth_flow",
    "start_server",
    "run_debug_server",
]


def get_login_url_for_ig() -> str:
    """Instagram shares the same OAuth dialog as Facebook."""

    return get_login_url()


def start_server():
    """Legacy entry point – mirrors ``run_debug_server``."""

    run_debug_server()


if __name__ == "__main__":
    run_debug_server()