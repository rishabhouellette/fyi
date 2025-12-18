"""Compatibility shim for legacy imports.

The real implementation now lives in backend.services.account_manager.
"""

from backend.services.account_manager import Account, AccountManager, get_account_manager  # noqa: F401

__all__ = ["Account", "AccountManager", "get_account_manager"]