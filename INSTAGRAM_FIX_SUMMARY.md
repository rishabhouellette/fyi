# Instagram Cross-Post Fix - Implementation Summary

## Issue Resolved
**OAuthException #10: Permission Denied** - Instagram cross-posting and direct uploads were failing due to missing OAuth scopes.

## Root Cause
The Facebook Page access token was missing the required `instagram_content_publish` scope needed for Instagram publishing operations. This scope must be explicitly requested during the OAuth flow.

## Solution Implemented

### 1. Enhanced Error Detection
- **instagram_uploader.py**: Added `_check_oauth_scopes()` method to detect missing scopes early
- **facebook_uploader.py**: Enhanced error handling to identify OAuth scope issues during cross-posting
- Both modules now provide clear guidance (reference to OAUTH_SCOPES_FIX.md) when scope errors occur

### 2. Scope Validation
Added automatic validation that:
- Checks if the access token has required Instagram publishing scopes
- Uses Facebook's `debug_token` endpoint to verify scopes
- Logs detailed scope information for debugging
- Gracefully handles timeout/API errors without blocking upload

### 3. Code Changes

#### instagram_uploader.py
```python
REQUIRED_SCOPES = [
    'instagram_content_publish',
    'instagram_business_content_publish',
]

def _check_oauth_scopes(self) -> Tuple[bool, str]:
    """Verify OAuth scopes before upload attempt"""
    # Uses debug_token to check granted scopes
    # Returns (success_bool, message_string)
```

#### facebook_uploader.py
```python
def _cross_post_to_instagram(self, video_id: str, description: str) -> None:
    """Enhanced with scope validation and better error messages"""
    # Detects OAuthException #10
    # Provides guidance for OAuth scope fix
    # Logs clear error messages
```

### 4. Documentation
Created `OAUTH_SCOPES_FIX.md` with:
- Problem explanation
- Required OAuth scopes list
- Step-by-step fix instructions
- How to verify scopes using `check_token_scopes.py`
- Testing procedures

## How to Fix (User Instructions)

### Quick Fix Steps:
1. **Go to Facebook Developers**: https://developers.facebook.com/
2. **Select Your App** (ID: 2221888558294490)
3. **Add OAuth Scopes**:
   - Navigate to Settings > Apps and Websites
   - Add these scopes to your OAuth configuration:
     - `instagram_content_publish`
     - `instagram_business_content_publish`
     - `pages_manage_posts`
4. **Set App to Live Mode**:
   - Go to Settings > Basic
   - Change from "Development" to "Live"
5. **Re-authenticate Accounts**:
   - Disconnect all Instagram/Facebook accounts in FYI
   - Re-login - you'll see new permission prompts
6. **Verify Scopes**:
   ```bash
   python check_token_scopes.py
   ```
   - Should show ✓ for `instagram_content_publish`

## Testing

### Test Instagram Upload:
```python
from instagram_uploader import InstagramUploader

uploader = InstagramUploader(account_id)
success, msg, video_id = uploader.upload_video(
    "path/to/video.mp4",
    "Test caption",
    lambda x: print(x)
)
print(f"Success: {success}, Message: {msg}")
```

### Test Cross-posting from Facebook:
```python
from facebook_uploader import FacebookUploader

uploader = FacebookUploader(account_id)
success, msg, video_id = uploader.upload_video(
    "path/to/video.mp4",
    "Test title",
    "Test description",
    lambda x: print(x),
    cross_post_to_instagram=True
)
```

## Files Modified
1. **instagram_uploader.py**
   - Added REQUIRED_SCOPES class variable
   - Added _check_oauth_scopes() method
   - Enhanced upload_video() with scope checking
   - Enhanced error messages for scope issues

2. **facebook_uploader.py**
   - Updated docstring with scope requirements
   - Enhanced _cross_post_to_instagram() with better error detection
   - Added specific guidance for OAuthException #10

3. **check_token_scopes.py** (existing)
   - Can be used to verify scopes are correctly granted

## Files Created
1. **OAUTH_SCOPES_FIX.md**
   - Comprehensive troubleshooting guide
   - Step-by-step fix instructions
   - References to official Facebook API docs

## Expected Behavior After Fix

### ✓ Successful Upload
```
Starting Instagram upload: video.mp4
✓ Required OAuth scopes verified
Video uploaded to Instagram: 1234567890
```

### ✓ Successful Cross-post
```
Cross-posting FB video 1234567890 to IG account 98765432100
✓ Successfully cross-posted to Instagram via feed
```

### ✗ Before Fix (Error)
```
OAuthException: (#10, [{...}]) An error occurred while performing a call to the Facebook API.
This appears to be an OAuth scope issue. See OAUTH_SCOPES_FIX.md for help.
```

## Scope Details

### instagram_content_publish
- **Purpose**: Publish media to Instagram
- **Required for**: Direct Instagram uploads, Reels
- **Type**: User + Page token scope

### instagram_business_content_publish  
- **Purpose**: Publish media via Instagram Business API
- **Required for**: Business account publishing
- **Type**: User + Page token scope

### pages_manage_posts
- **Purpose**: Create and manage posts on Facebook pages
- **Required for**: Cross-posting functionality
- **Type**: Page token scope

## Verification Steps

1. **Check Token Scopes**:
   ```bash
   python check_token_scopes.py
   ```
   Expected: ✓ instagram_content_publish is PRESENT!

2. **Check App Settings**:
   - App ID: 2221888558294490
   - App Mode: Live (not Development)
   - Valid OAuth redirect URIs configured

3. **Test Upload**:
   - Try uploading a test video to Instagram
   - Check logs for scope validation messages
   - Should see "✓ Required OAuth scopes verified"

## Troubleshooting

### Still Getting OAuthException #10?
1. Verify you re-authenticated after changing app settings
2. Check that app is in "Live" mode (not "Development")
3. Run `check_token_scopes.py` to see current scopes
4. Check app review status if in production
5. Ensure all required scopes are in your OAuth redirect URI

### Scope Check Timeout?
- This is non-critical - upload will proceed anyway
- Check network connectivity to graph.facebook.com
- Retry later if too many API calls

### Can't Find Instagram Account?
- Ensure Facebook page is linked to Instagram business account
- Verify Instagram account exists and is accessible
- Try re-linking the accounts through FYI UI

## Next Steps
1. Apply the fix following OAUTH_SCOPES_FIX.md
2. Re-authenticate your accounts
3. Run `check_token_scopes.py` to verify
4. Test Instagram upload and cross-posting
5. Proceed to end-to-end testing (Task 12)

## References
- [Instagram Graph API Documentation](https://developers.facebook.com/docs/instagram-api)
- [Content Publishing](https://developers.facebook.com/docs/instagram-api/guides/content-publishing)
- [OAuth Permissions](https://developers.facebook.com/docs/facebook-login/permissions)
- [Token Debug Endpoint](https://developers.facebook.com/docs/facebook-login/security#debug-token)
