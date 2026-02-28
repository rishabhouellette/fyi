"""Account management: AccountManager, account helpers, active accounts."""
import json
from datetime import datetime
from typing import List, Optional

from core.config import ACCOUNTS_FILE, ACTIVE_ACCOUNTS_FILE, db


# ═══════════════════════════════════════════════════════════════════════════════
# AccountManager
# ═══════════════════════════════════════════════════════════════════════════════

class AccountManager:
    """Simple account management backed by accounts.json + SQLite."""

    def load_accounts(self) -> List[dict]:
        if ACCOUNTS_FILE.exists():
            try:
                with open(ACCOUNTS_FILE, "r") as f:
                    data = json.load(f)
                    return data.get("accounts", [])
            except Exception:
                return []
        return []

    def save_accounts(self, accounts: List[dict]):
        ACCOUNTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(ACCOUNTS_FILE, "w") as f:
            json.dump({"accounts": accounts}, f, indent=2)

    def add_account(self, platform: str, name: str, username: str) -> dict:
        accounts = self.load_accounts()
        account = {
            "id": f"{platform}_{len(accounts) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "platform": platform,
            "name": name,
            "username": username,
            "status": "connected",
            "connected_at": datetime.now().isoformat(),
            "followers": 0,
            "total_posts": 0,
        }
        accounts.append(account)
        self.save_accounts(accounts)
        try:
            db.upsert_account(account)
        except Exception:
            pass
        return account

    def remove_account(self, account_id: str) -> bool:
        accounts = self.load_accounts()
        accounts = [a for a in accounts if a.get("id") != account_id]
        self.save_accounts(accounts)
        try:
            db.delete_account(account_id)
        except Exception:
            pass
        return True


account_manager = AccountManager()


# ═══════════════════════════════════════════════════════════════════════════════
# Account helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _load_accounts_raw() -> list[dict]:
    if ACCOUNTS_FILE.exists():
        try:
            with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("accounts", []) if isinstance(data, dict) else []
        except Exception:
            return []
    return []


def _find_account_by_id(account_id: str) -> Optional[dict]:
    for acct in _load_accounts_raw():
        if acct.get("id") == account_id:
            return acct
    return None


def _upsert_account_raw(acct: dict) -> None:
    accounts = _load_accounts_raw()
    accounts = [a for a in accounts if a.get("id") != acct.get("id")]
    accounts.append(acct)
    account_manager.save_accounts(accounts)
    try:
        db.upsert_account(acct)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════════
# Active Accounts
# ═══════════════════════════════════════════════════════════════════════════════

def _load_active_accounts() -> dict:
    if ACTIVE_ACCOUNTS_FILE.exists():
        try:
            with open(ACTIVE_ACCOUNTS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and isinstance(data.get("active"), dict):
                return data["active"]
            if isinstance(data, dict):
                return data
        except Exception:
            return {}
    return {}


def _save_active_accounts(active: dict) -> None:
    ACTIVE_ACCOUNTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ACTIVE_ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump({"active": active}, f, indent=2)
