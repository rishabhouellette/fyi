"""
Run quick Graph API diagnostics for accounts in `accounts/accounts.json`.

What it checks:
- `me/permissions` for each access token (which permissions are granted)
- for pages: `/{page_id}?fields=instagram_business_account` to check Page->IG linkage

Usage:
    python fb_diagnostics.py

This script prints JSON responses to help diagnose why cross-posting to Instagram fails.
"""
import json
import os
import sys
from pathlib import Path
import requests

WORKDIR = Path(__file__).resolve().parent
ACCOUNTS_FILE = WORKDIR / 'accounts' / 'accounts.json'
API_VERSION = 'v24.0'
BASE = f'https://graph.facebook.com/{API_VERSION}'


def load_accounts():
    if not ACCOUNTS_FILE.exists():
        print(f"accounts file not found: {ACCOUNTS_FILE}")
        sys.exit(1)
    with open(ACCOUNTS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # accounts.json might be a list or a dict keyed by an id; normalize to list of account entries
    if isinstance(data, dict):
        # keep original key for debugging if present
        items = []
        for k, v in data.items():
            if isinstance(v, dict):
                v['_entry_key'] = k
                items.append(v)
        return items
    return data


def get(url, params=None):
    try:
        r = requests.get(url, params=params, timeout=15)
        try:
            j = r.json()
        except Exception:
            j = {'http_status': r.status_code, 'text': r.text}
        return r.status_code, j
    except Exception as e:
        return None, {'error': str(e)}


def check_token(token):
    print('\n== Token check ==')
    print('Token (first 8 chars):', token[:8] + '...')
    # me
    st, me = get(f"{BASE}/me", params={'access_token': token})
    print('\n/me ->', st)
    print(json.dumps(me, indent=2))

    # permissions
    st, perms = get(f"{BASE}/me/permissions", params={'access_token': token})
    print('\n/me/permissions ->', st)
    print(json.dumps(perms, indent=2))

    # accounts (pages) the user can access
    st, accounts = get(f"{BASE}/me/accounts", params={'access_token': token})
    print('\n/me/accounts ->', st)
    print(json.dumps(accounts, indent=2))
    return me, perms, accounts


def check_page_linkage(token, page_id):
    print(f"\n== Page {page_id} linkage ==")
    fields = 'instagram_business_account,connected_instagram_account,name'
    st, data = get(f"{BASE}/{page_id}", params={'access_token': token, 'fields': fields})
    print(f"GET /{page_id}?fields={fields} ->", st)
    print(json.dumps(data, indent=2))
    # also list page's videos/scheduled posts count (quick probe)
    st_v, vids = get(f"{BASE}/{page_id}/videos", params={'access_token': token, 'limit': 5})
    print(f"GET /{page_id}/videos ->", st_v)
    print(json.dumps(vids, indent=2))
    st_s, sched = get(f"{BASE}/{page_id}/scheduled_posts", params={'access_token': token, 'limit': 5})
    print(f"GET /{page_id}/scheduled_posts ->", st_s)
    print(json.dumps(sched, indent=2))
    return data, vids, sched


def main():
    accounts = load_accounts()
    if not isinstance(accounts, list):
        print('Expected accounts.json to be a list of account objects. Found:', type(accounts))
        print('Content preview (first 200 chars):')
        print(json.dumps(accounts)[:200])
        return

    for acct in accounts:
        print('\n' + '=' * 60)
        name = acct.get('name') or acct.get('page_name') or acct.get('page_id') or '<unnamed>'
        token = acct.get('access_token') or acct.get('token')
        page_id = acct.get('page_id') or acct.get('id') or acct.get('page')
        print(f"Account: {name}")
        if not token:
            print('  NO access_token found in this account entry; skipping')
            continue
        me, perms, accounts_list = check_token(token)
        if page_id:
            check_page_linkage(token, page_id)
        else:
            # if page id isn't in account entry, attempt to use first page from /me/accounts
            data_pages = accounts_list.get('data') if isinstance(accounts_list, dict) else None
            if data_pages:
                first = data_pages[0]
                pid = first.get('id')
                print(f"No page_id in account entry; probing first accessible page: {pid}")
                check_page_linkage(token, pid)

    print('\nDiagnostics complete.')


if __name__ == '__main__':
    main()
