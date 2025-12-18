"""Account storage + token management for FYI Social.

This module exists because multiple parts of the repo import
`backend.services.account_manager`, and `account_manager.py` at the repo root
is a thin compatibility shim that re-exports these symbols.

Storage format is compatible with `accounts/accounts.json` used elsewhere in
this repo.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class Account:
    id: str
    platform: str
    name: str
    access_token: str
    page_id: Optional[str] = None
    page_name: Optional[str] = None
    user_id: Optional[str] = None
    connected_at: Optional[str] = None
    status: str = "connected"

    def is_token_valid(self) -> bool:
        # This repo stores long-lived tokens without a reliable expires_at in accounts.json.
        # Treat missing expiry as valid.
        return bool(self.access_token)


class AccountManager:
    def __init__(self, accounts_file: Path | str = "accounts/accounts.json"):
        self.accounts_file = Path(accounts_file)
        self.accounts_file.parent.mkdir(parents=True, exist_ok=True)

    def _read_raw(self) -> Dict[str, Any]:
        if not self.accounts_file.exists():
            return {"accounts": []}
        try:
            payload = json.loads(self.accounts_file.read_text(encoding="utf-8"))
        except Exception:
            return {"accounts": []}

        if isinstance(payload, list):
            return {"accounts": payload}
        if isinstance(payload, dict):
            return {"accounts": payload.get("accounts", [])}
        return {"accounts": []}

    def _write_raw(self, accounts: List[Dict[str, Any]]) -> None:
        self.accounts_file.write_text(
            json.dumps({"accounts": accounts}, indent=2), encoding="utf-8"
        )

    def get_all_accounts(self) -> List[Account]:
        raw = self._read_raw().get("accounts", [])
        results: List[Account] = []
        for idx, item in enumerate(raw):
            if not isinstance(item, dict):
                continue
            acc_id = str(item.get("id") or (idx + 1))
            platform = str(item.get("platform") or "")
            name = str(item.get("account_name") or item.get("username") or item.get("name") or acc_id)
            token = str(item.get("access_token") or "")
            results.append(
                Account(
                    id=acc_id,
                    platform=platform,
                    name=name,
                    access_token=token,
                    page_id=item.get("page_id"),
                    page_name=item.get("page_name"),
                    user_id=item.get("user_id"),
                    connected_at=item.get("connected_at"),
                    status=str(item.get("status") or "connected"),
                )
            )
        return results

    def get_account(self, account_id: str) -> Optional[Account]:
        for account in self.get_all_accounts():
            if str(account.id) == str(account_id):
                return account
        return None

    def add_account(self, data: Dict[str, Any]) -> Account:
        raw_accounts = self._read_raw().get("accounts", [])
        new_id = str(max([int(a.get("id", 0)) for a in raw_accounts if isinstance(a, dict)] + [0]) + 1)

        record = {
            "id": new_id,
            "platform": data.get("platform"),
            "account_name": data.get("account_name") or data.get("name") or new_id,
            "username": data.get("username") or data.get("account_name") or data.get("name") or new_id,
            "user_id": data.get("user_id"),
            "page_id": data.get("page_id"),
            "page_name": data.get("page_name"),
            "access_token": data.get("access_token"),
            "connected_at": data.get("connected_at") or datetime.now().isoformat(),
            "status": data.get("status") or "connected",
        }

        raw_accounts.append(record)
        self._write_raw(raw_accounts)
        return Account(
            id=new_id,
            platform=str(record.get("platform") or ""),
            name=str(record.get("account_name") or record.get("username") or new_id),
            access_token=str(record.get("access_token") or ""),
            page_id=record.get("page_id"),
            page_name=record.get("page_name"),
            user_id=record.get("user_id"),
            connected_at=record.get("connected_at"),
            status=str(record.get("status") or "connected"),
        )


_account_manager: Optional[AccountManager] = None


def get_account_manager() -> AccountManager:
    global _account_manager
    if _account_manager is None:
        _account_manager = AccountManager()
    return _account_manager
