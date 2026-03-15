# FYIXT Dashboard Integration Guide for viralclip.tech

## Overview

The FYIXT dashboard has been built and is ready for integration into the viralclip-website repository. This guide will help you replace the current dashboard with the new FYIXT dashboard.

## Built Dashboard

**Location:** `/Users/mac/Downloads/FYIXT/desktop/dist/`

**Files:**
- `index.html` - Main entry point (0.48 kB)
- `assets/index-CZXBg62c.js` - Main app (875.29 kB minified, 243.36 kB gzipped)
- `assets/SchedulerPro-iTJq2exB.js` - Scheduler component (31.90 kB)
- `assets/index-KrdvIFbF.css` - Styles (48.61 kB)

## Integration Steps

### Option 1: Direct Replacement (Recommended)

If viralclip-website is a simple website serving static files:

```bash
# 1. Backup current dashboard
cp -r /path/to/viralclip-website/public /path/to/viralclip-website/public.backup

# 2. Copy FYIXT dashboard to public folder
cp -r /Users/mac/Downloads/FYIXT/desktop/dist/* /path/to/viralclip-website/public/

# 3. Update web server to serve from public/
# Make sure your web server (nginx/Apache) points to the public folder
```

### Option 2: Subdirectory Integration

If viralclip-website has other content:

```bash
# 1. Create dashboard subdirectory
mkdir -p /path/to/viralclip-website/dashboard

# 2. Copy FYIXT dashboard
cp -r /Users/mac/Downloads/FYIXT/desktop/dist/* /path/to/viralclip-website/dashboard/

# 3. Update nginx/web server to route requests
# Add to nginx.conf:
location /dashboard/ {
    alias /var/www/viralclip-website/dashboard/;
    try_files $uri $uri/ /dashboard/index.html;
}
```

### Option 3: Full FYIXT Backend + Dashboard (Recommended for Production)

Replace entire viralclip.tech with full FYIXT:

```bash
# 1. Deploy FYIXT backend using Docker
cd /Users/mac/Downloads/FYIXT/deploy
docker-compose up -d

# 2. FYIXT automatically serves the dashboard from desktop/dist/
# Everything will be available at: https://viralclip.tech
```

## Environment Configuration

Update `.env` in FYIXT for production:

```env
# Server
FYI_WEB_PORTAL_PORT=8000
FYI_BIND_HOST=0.0.0.0
FYI_PUBLIC_BASE_URL=https://viralclip.tech

# CORS
FYI_ALLOWED_ORIGINS=https://viralclip.tech,https://www.viralclip.tech

# Scheduler
FYI_SCHEDULER_ENABLED=1
FYI_SCHEDULER_POLL_SECONDS=60

# OAuth (from your Meta/Google developer console)
FB_APP_ID=your_facebook_app_id
FB_APP_SECRET=your_facebook_app_secret
YT_CLIENT_ID=your_youtube_client_id
YT_CLIENT_SECRET=your_youtube_client_secret

# AI Services (BYOK)
GOOGLE_API_KEY=your_gemini_key (optional)
OPENAI_API_KEY=your_openai_key (optional)
```

## Nginx Configuration Example

```nginx
server {
    listen 80;
    listen 443 ssl;
    server_name viralclip.tech www.viralclip.tech;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Redirect HTTP to HTTPS
    if ($scheme != "https") {
        return 301 https://$server_name$request_uri;
    }

    # Proxy to FYIXT backend
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Docker Deployment

```bash
# From FYIXT directory
cd /Users/mac/Downloads/FYIXT

# Build and deploy
cd deploy
docker-compose -f docker-compose.yml up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f app
```

## Verification

After deployment, verify:

```bash
# 1. Check if dashboard loads
curl -I https://viralclip.tech/

# 2. Check API endpoints
curl https://viralclip.tech/api/health

# 3. View Swagger docs
# Visit: https://viralclip.tech/docs
```

## Features Included in Dashboard

✅ **Account Management**
- Connect Facebook, Instagram, YouTube
- Manage multiple accounts per platform

✅ **Content Scheduling**
- Schedule posts for future publishing
- Smart scheduling suggestions
- Bulk scheduling

✅ **AI Studio**
- Generate captions
- Generate hashtags
- Image generation
- Video generation
- Voice synthesis
- Content translation

✅ **Analytics**
- Link tracking
- Click analytics
- CSV exports
- Engagement metrics

✅ **Media Management**
- Upload and process videos
- Faceless video creation
- Content library
- Templates

✅ **Settings**
- Platform credentials
- BYOK (Bring Your Own Key) for AI services
- Usage tracking
- Account preferences

## Troubleshooting

### Dashboard Shows "API is running" Message
- React frontend not built or not in `desktop/dist/`
- Check that `npm run build` completed successfully
- Ensure web server is serving from correct directory

### API Token Errors
- Token is automatically injected by the server into the React HTML
- Make sure `desktop/dist/index.html` is being served correctly

### CORS Errors
- Add your domain to `FYI_ALLOWED_ORIGINS` env variable
- Restart the server after changing env vars

### Database Issues
- First startup auto-initializes SQLite at `data/fyi_webportal.db`
- Check file permissions on `data/` directory
- Ensure `data/` is writable

## File Structure

```
viralclip-website/
├── dashboard/                    # FYIXT frontend (copied from desktop/dist/)
│   ├── index.html
│   ├── assets/
│   │   ├── index-*.js
│   │   ├── index-*.css
│   │   └── SchedulerPro-*.js
├── api/                          # FYIXT backend (Python)
├── docker-compose.yml
├── nginx.conf
└── .env
```

## Performance Notes

- Dashboard size: ~875 KB (243 KB gzipped) - loaded once
- Gzip compression recommended for bandwidth
- Consider CDN for static assets
- API response times optimized with FastAPI

## Security Considerations

1. **HTTPS Only**: Dashboard requires HTTPS (self-signed or Let's Encrypt)
2. **Token-based Auth**: All API requests require authentication token
3. **Environment Variables**: Keep secrets in `.env`, never commit
4. **CORS Whitelisting**: Only allow trusted origins
5. **Rate Limiting**: 120 requests/minute per IP by default

## Next Steps

1. ✅ Dashboard built and ready
2. Choose deployment option (1, 2, or 3)
3. Configure environment variables
4. Deploy using Docker or manual deployment
5. Test all features at https://viralclip.tech
6. Monitor logs for errors

## Support

For issues or questions:
- See [DEVELOPMENT.md](../DEVELOPMENT.md) for architecture details
- Check [SETUP.md](../SETUP.md) for setup issues
- Review API docs at `/docs` endpoint after deployment

