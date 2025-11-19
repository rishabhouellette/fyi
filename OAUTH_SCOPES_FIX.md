# Instagram Cross-Post OAuth Scope Fix

## Problem
Instagram cross-posting fails with **OAuthException #10 (Permission Denied)**.

## Root Cause
The Facebook Page access token lacks the required `instagram_content_publish` scope needed for Instagram publishing operations.

## Required OAuth Scopes

### For Instagram Business Account Publishing:
```
- instagram_business_content_publish
- instagram_content_publish
```

### For Facebook Page Management:
```
- pages_manage_metadata
- pages_read_engagement
- pages_read_user_profile
- pages_manage_posts
```

## How to Fix (For App Setup)

### Step 1: Update Your Facebook App Settings
1. Go to [Facebook Developers](https://developers.facebook.com/)
2. Select your app (ID: 2221888558294490)
3. Navigate to **Settings > Basic**
4. Under "App Roles", ensure you have **Admin** or **Developer** role

### Step 2: Configure OAuth Scopes
1. Go to your app's **Permissions**
2. Add these scopes to your OAuth login flow:
   - `instagram_business_content_publish`
   - `instagram_content_publish`
   - `pages_manage_posts`
   - `pages_read_engagement`

### Step 3: Update Your App to Live Mode
1. Go to **Settings > Basic**
2. Change **App Mode** from "Development" to "Live"
   - This enables cross-app Instagram publishing
3. Submit app for review if required

### Step 4: Re-authenticate All Accounts
1. Open FYI Uploader
2. Disconnect all Facebook/Instagram accounts
3. Re-authenticate with new OAuth scopes
4. The app will now request the new permissions

## How to Verify Scopes

Run the scope checker:
```bash
python check_token_scopes.py
```

Expected output showing ✓ for:
- `instagram_content_publish`
- `pages_manage_posts`
- `pages_read_engagement`

## Account Manager Configuration (account_manager.py)

The account manager should request these scopes during OAuth:

```python
REQUIRED_SCOPES = [
    'pages_manage_posts',
    'pages_read_engagement',
    'pages_read_user_profile',
    'pages_manage_metadata',
    'instagram_business_content_publish',
    'instagram_content_publish',
]
```

## Instagram Uploader Scope Validation (instagram_uploader.py)

Enhanced with scope checking:

```python
def _check_required_scopes(self) -> bool:
    """Verify required scopes are granted"""
    required = ['instagram_content_publish', 'instagram_business_content_publish']
    
    # This would be called during upload to catch scope issues early
    # Implementation: Use debug_token endpoint to verify
```

## Testing the Fix

1. **Verify Scopes**: Run `python check_token_scopes.py`
2. **Upload to Instagram**: Use the Instagram uploader UI
3. **Cross-post from Facebook**: Upload video with cross-post enabled
4. **Check Logs**: Look for "✓ Successfully cross-posted to Instagram"

## References
- [Instagram Content Publishing API](https://developers.facebook.com/docs/instagram-api/guides/content-publishing)
- [Facebook Graph API Permissions](https://developers.facebook.com/docs/facebook-login/permissions)
- [OAuth Debug Token](https://developers.facebook.com/docs/facebook-login/security#debug-token)

## Status
- Issue: OAuthException #10 - Missing `instagram_content_publish` scope
- Fix Required: Re-authenticate with new OAuth scopes after app configuration
- Temporary Workaround: Use Facebook crossposter instead (less optimal)
