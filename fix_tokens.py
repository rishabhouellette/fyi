"""
Token Refresh Helper
Helps you get fresh, valid tokens for Facebook and Instagram
"""
import webbrowser
import sys

print("=" * 60)
print("TOKEN REFRESH REQUIRED")
print("=" * 60)
print()
print("Your tokens are expired. You need to re-authenticate.")
print()
print("STEPS TO FIX:")
print()
print("1. Open FYI Uploader app")
print("2. Go to Upload → Facebook tab")
print("3. Click 'Unlink' to remove old Facebook account")
print("4. Click 'Link New Account' to get fresh token")
print("5. Go to Upload → Instagram tab")
print("6. Click 'Unlink' to remove old Instagram account")
print("7. Click 'Link New Account' to get fresh token")
print()
print("=" * 60)
print("IMPORTANT: Make sure your app is in Development Mode")
print("=" * 60)
print()
print("Go to: https://developers.facebook.com/apps/2221888558294490/")
print()
print("Check if:")
print("  - App is in 'Development' mode (top of page)")
print("  - You are added as a Test User")
print("  - Required permissions are enabled:")
print("    • instagram_content_publish")
print("    • instagram_business_content_publish")
print("    • pages_manage_posts")
print("    • pages_read_engagement")
print()
print("=" * 60)
print()

open_browser = input("Open Facebook App Dashboard? (y/n): ").lower()
if open_browser == 'y':
    webbrowser.open("https://developers.facebook.com/apps/2221888558294490/settings/basic/")
    print("✓ Opened in browser")
else:
    print("Manual URL: https://developers.facebook.com/apps/2221888558294490/")

print()
print("After fixing app settings, restart FYI Uploader and re-link accounts.")
print()
