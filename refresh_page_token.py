"""Helper script to convert a short-lived Facebook User token into
an extended Page access token and store it in accounts.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Any

import requests

APP_ID = "2221888558294490"
APP_SECRET = "6f1c65510e626e9bb45fd5d2f52f8565"
API_VERSION = "v20.0"
ACCOUNTS_FILE = Path("accounts/accounts.json")


def prompt(prompt_text: str) -> str:
    try:
        return input(prompt_text)
    except KeyboardInterrupt:
        print("\nAborted by user.")
        sys.exit(1)


def exchange_for_long_lived_token(short_token: str) -> str:
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": APP_ID,
        "client_secret": APP_SECRET,
        "fb_exchange_token": short_token,
    }
    resp = requests.get(
        f"https://graph.facebook.com/{API_VERSION}/oauth/access_token",
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    long_token = data.get("access_token")
    if not long_token:
        raise RuntimeError(f"No access_token returned: {data}")
    return long_token


def fetch_pages(long_lived_token: str) -> Any:
    resp = requests.get(
        f"https://graph.facebook.com/{API_VERSION}/me/accounts",
        params={"access_token": long_lived_token},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json().get("data", [])
    if not data:
        raise RuntimeError("No pages found. Make sure the token has pages_show_list.")
    return data


def load_accounts() -> Dict[str, Any]:
    if not ACCOUNTS_FILE.exists():
        return {}
    with open(ACCOUNTS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_accounts(data: Dict[str, Any]) -> None:
    ACCOUNTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ACCOUNTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def update_account_tokens(accounts: Dict[str, Any], page_id: str, new_token: str) -> None:
    updated = False
    for account in accounts.values():
        if account.get("page_id") == page_id:
            account["access_token"] = new_token
            account["last_used"] = None
            account["token_expires_at"] = None
            updated = True
    if updated:
        save_accounts(accounts)
        print(f"✓ Updated accounts.json for page {page_id}")
    else:
        print("⚠ No matching accounts found in accounts.json. Add the page in-app first.")


def main() -> None:
    if len(sys.argv) > 1:
        short_token = sys.argv[1]
    else:
        short_token = prompt("Paste the SHORT user token from Graph API Explorer: ")
    if not short_token:
        print("No token provided.")
        return

    print("\n1) Exchanging for long-lived user token...")
    long_token = exchange_for_long_lived_token(short_token)
    print(f"   ✓ Long-lived user token (first 25 chars): {long_token[:25]}...")

    print("\n2) Fetching Facebook Pages tied to this token...")
    pages = fetch_pages(long_token)
    for idx, page in enumerate(pages, start=1):
        print(f"   [{idx}] {page.get('name')} | ID: {page.get('id')}")
    choice = prompt("Select page number to update: ")
    try:
        choice_idx = int(choice) - 1
        selected = pages[choice_idx]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    page_token = selected.get("access_token")
    if not page_token:
        print("Selected page did not return a token.")
        return

    print("\n   ✓ Page token retrieved. Updating local accounts...")
    accounts = load_accounts()
    update_account_tokens(accounts, selected.get("id"), page_token)

    print("\nDone! Restart FYI Uploader and retry the upload.")


if __name__ == "__main__":
    try:
        main()
    except requests.HTTPError as http_err:
        print(f"HTTP error: {http_err.response.text}")
    except Exception as err:
        print(f"Error: {err}")
