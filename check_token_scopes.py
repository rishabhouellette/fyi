"""
Check the scopes granted to a Page access token using Graph API debug_token.
"""
import requests
import json
from pathlib import Path

# Load accounts to get page token
accounts_file = Path('accounts/accounts.json')
with open(accounts_file, 'r', encoding='utf-8') as f:
    accounts_data = json.load(f)

# Get the page token from the first facebook account
page_token = None
page_name = None
page_id = None

if isinstance(accounts_data, dict):
    for key, account in accounts_data.items():
        if account.get('platform') == 'facebook':
            page_token = account.get('access_token')
            page_name = account.get('name', 'Unknown')
            page_id = account.get('page_id')
            break
else:
    for account in accounts_data:
        if account.get('platform') == 'facebook':
            page_token = account.get('access_token')
            page_name = account.get('name', 'Unknown')
            page_id = account.get('page_id')
            break

if not page_token:
    print("No facebook access token found in accounts.json")
    exit(1)

# App credentials from .env
app_id = "2221888558294490"
app_secret = "6f1c65510e626e9bb45fd5d2f52f8565"
app_token = f"{app_id}|{app_secret}"

print(f"Checking scopes for Page: {page_name} ({page_id})")
print(f"Token (first 20 chars): {page_token[:20]}...")
print()

# Call debug_token endpoint
r = requests.get(
    "https://graph.facebook.com/debug_token",
    params={
        "input_token": page_token,
        "access_token": app_token
    }
)

result = r.json()
print("Graph API Response:")
print(json.dumps(result, indent=2))

# Extract and highlight key info
if 'data' in result:
    data = result['data']
    print("\n" + "="*60)
    print("SUMMARY:")
    print("="*60)
    print(f"Token valid: {data.get('is_valid', False)}")
    print(f"User ID: {data.get('user_id', 'N/A')}")
    print(f"App ID: {data.get('app_id', 'N/A')}")
    print(f"Issued at: {data.get('issued_at', 'N/A')}")
    print(f"Expires at: {data.get('expires_at', 'N/A')}")
    
    scopes = data.get('scopes', [])
    print(f"\nGranted Scopes ({len(scopes)} total):")
    for scope in scopes:
        marker = "✓ " if scope == "instagram_content_publish" else "  "
        print(f"{marker}{scope}")
    
    if 'instagram_content_publish' in scopes:
        print("\n✓ instagram_content_publish is PRESENT!")
    else:
        print("\n✗ instagram_content_publish is MISSING!")
        print("\nThis is likely why cross-posting to Instagram fails with OAuthException code 10.")
