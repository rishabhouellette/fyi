# 🔧 Facebook OAuth Setup - QUICK FIX

## ⚠️ Error: "URL blocked - redirect URI not whitelisted"

You need to whitelist the OAuth callback URL in your Facebook App settings.

## 📋 Steps to Fix:

### 1. Go to Facebook Developers Console
https://developers.facebook.com/apps/2221888558294490/settings/basic/

### 2. Add OAuth Redirect URIs

**Click "Add Platform" or edit existing platform:**

Add these redirect URIs:
```
http://localhost:5000/oauth/callback
http://127.0.0.1:5000/oauth/callback
https://localhost:5000/oauth/callback
https://127.0.0.1:5000/oauth/callback
```

### 3. Save Changes

Click "Save Changes" at the bottom of the page.

### 4. Test Again

Go back to FYI Social ∞ → Accounts → Connect Facebook

---

## 🎯 Alternative: Use Existing Redirect URI

If you already have a redirect URI configured (like from your .env file), we can update the backend to use that instead.

Your `.env` file shows:
```
OAUTH_REDIRECT_ORIGIN=https://127.0.0.1:5000
```

This means Facebook expects: `https://127.0.0.1:5000/callback`

But our Phase 1 OAuth is using: `http://localhost:5000/oauth/callback`

**Quick Fix Option:**
Update Facebook app to allow `http://localhost:5000/oauth/callback`

**OR**

Keep using your old OAuth setup (which already works).

---

## 💡 Recommendation

For development, add BOTH:
- `http://localhost:5000/oauth/callback` (Phase 1 OAuth)
- `https://127.0.0.1:5000/callback` (Your existing setup)

This way both systems work!
