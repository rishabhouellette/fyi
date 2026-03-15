# 🚀 FYIXT Production Deployment Guide

## ✅ Deployment Ready

Your FYIXT application is fully built and ready for production deployment to viralclip.tech.

**Commit:** `fd17685` - Production Ready  
**Dashboard:** Built and optimized (940 KB)  
**Status:** ✅ Ready for deployment

---

## 📦 What's Been Built

✅ **Backend (Python FastAPI)**
- All dependencies listed in `requirements.txt`
- Python 3.9+ compatible
- Production-ready with CORS, rate limiting, authentication

✅ **Frontend (React SPA)**
- Built and optimized in `desktop/dist/`
- 875 KB minified (243 KB gzipped)
- All assets included

✅ **Database (SQLite)**
- Auto-initializes on first run
- Includes schema for accounts, posts, links, analytics

✅ **Scheduler**
- Background task processing
- Post scheduling and execution
- Enabled by default

---

## 🌐 Deployment Options

### **Option A: Docker Deployment (Recommended)** 

If your viralclip.tech server has Docker installed:

```bash
# 1. SSH to your server
ssh user@viralclip.tech

# 2. Clone the repository
git clone https://github.com/rishabhouellette/fyi.git
cd fyi

# 3. Create/update .env with your credentials
cat > .env << 'EOF'
FYI_PUBLIC_BASE_URL=https://viralclip.tech
FYI_ALLOWED_ORIGINS=https://viralclip.tech,https://www.viralclip.tech
FYI_SCHEDULER_ENABLED=1
FB_APP_ID=your_facebook_app_id
FB_APP_SECRET=your_facebook_app_secret
YT_CLIENT_ID=your_youtube_client_id
YT_CLIENT_SECRET=your_youtube_client_secret
EOF

# 4. Deploy
cd deploy
docker-compose up -d

# 5. Verify
docker-compose ps
docker-compose logs -f app
```

**Access:** https://viralclip.tech ✅

---

### **Option B: Manual Python Deployment**

If your server doesn't have Docker:

```bash
# 1. SSH to server
ssh user@viralclip.tech

# 2. Install dependencies
git clone https://github.com/rishabhouellette/fyi.git
cd fyi
python3.9 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Create .env
cat > .env << 'EOF'
FYI_WEB_PORTAL_PORT=8000
FYI_PUBLIC_BASE_URL=https://viralclip.tech
FYI_ALLOWED_ORIGINS=https://viralclip.tech,https://www.viralclip.tech
# ... add your API keys
EOF

# 4. Start with systemd service
sudo tee /etc/systemd/system/fyixt.service > /dev/null << 'EOF'
[Unit]
Description=FYIXT Web Portal
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/home/user/fyi
ExecStart=/home/user/fyi/.venv/bin/python web_server.py --https --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 5. Enable and start
sudo systemctl daemon-reload
sudo systemctl enable fyixt
sudo systemctl start fyixt

# 6. Configure nginx reverse proxy
sudo tee /etc/nginx/sites-available/viralclip.tech > /dev/null << 'EOF'
server {
    listen 80;
    listen 443 ssl;
    server_name viralclip.tech www.viralclip.tech;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    if ($scheme != "https") {
        return 301 https://$server_name$request_uri;
    }

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_request_buffering off;
    }
}
EOF

sudo ln -s /etc/nginx/sites-available/viralclip.tech /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

**Access:** https://viralclip.tech ✅

---

### **Option C: Cloud Deployment (AWS/Heroku/DigitalOcean)**

**For AWS EC2:**
```bash
# Use Option B (Manual) with Ubuntu/Amazon Linux AMI
# Install: Python 3.9, nginx, git
```

**For Heroku:**
```bash
# 1. Create Procfile
echo "web: python web_server.py --port \$PORT --https" > Procfile

# 2. Deploy
heroku create fyixt
git push heroku main
heroku config:set FYI_PUBLIC_BASE_URL=https://fyixt.herokuapp.com
```

**For DigitalOcean:**
- Same as Option B (Manual)
- Create droplet with Python 3.9 preinstalled
- Follow manual deployment steps

---

## 🔒 SSL/TLS Configuration

### Let's Encrypt (Free)
```bash
# 1. Install certbot
sudo apt-get install certbot python3-certbot-nginx

# 2. Get certificate
sudo certbot certonly --nginx -d viralclip.tech -d www.viralclip.tech

# 3. Update nginx config to point to:
#   ssl_certificate /etc/letsencrypt/live/viralclip.tech/fullchain.pem;
#   ssl_certificate_key /etc/letsencrypt/live/viralclip.tech/privkey.pem;

# 4. Auto-renewal
sudo systemctl enable certbot.timer
```

### Self-Signed (Development Only)
```bash
# Already generated at: data/certs/localhost.crt|.key
# App uses these automatically with --https flag
```

---

## 🔑 Environment Variables

Create `.env` file with:

```env
# Server Configuration
FYI_WEB_PORTAL_PORT=8000
FYI_BIND_HOST=0.0.0.0
FYI_PUBLIC_BASE_URL=https://viralclip.tech

# CORS
FYI_ALLOWED_ORIGINS=https://viralclip.tech,https://www.viralclip.tech

# Scheduler
FYI_SCHEDULER_ENABLED=1
FYI_SCHEDULER_POLL_SECONDS=60

# OAuth Credentials (from https://developers.facebook.com)
FB_APP_ID=your_app_id_here
FB_APP_SECRET=your_app_secret_here

# YouTube (from https://console.cloud.google.com)
YT_CLIENT_ID=your_client_id_here
YT_CLIENT_SECRET=your_client_secret_here

# AI Services (optional, BYOK)
GOOGLE_API_KEY=your_gemini_key
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
```

---

## ✅ Verification Checklist

After deployment, verify:

```bash
# 1. Server responds
curl -I https://viralclip.tech/

# 2. API health
curl https://viralclip.tech/api/health

# 3. Swagger docs
curl https://viralclip.tech/docs

# 4. Dashboard loads
curl https://viralclip.tech/ | grep -o "<title>.*</title>"

# 5. Check logs
docker-compose logs app  # If using Docker
# or
journalctl -u fyixt -f  # If using systemd
```

---

## 📊 Performance Tuning

### Database Optimization
```bash
# Add indices for frequently queried columns
sqlite3 data/fyi_webportal.db << 'SQL'
CREATE INDEX IF NOT EXISTS idx_posts_status ON scheduled_posts(status);
CREATE INDEX IF NOT EXISTS idx_posts_due_at ON scheduled_posts(due_at);
CREATE INDEX IF NOT EXISTS idx_posts_account ON scheduled_posts(account_id);
SQL
```

### Nginx Caching
```nginx
location /assets/ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}

location /api/ {
    add_header Cache-Control "no-store, no-cache, must-revalidate";
}
```

### Gzip Compression
```nginx
gzip on;
gzip_types application/json text/css application/javascript;
gzip_min_length 1000;
```

---

## 🔍 Monitoring & Logs

### View Logs
```bash
# Docker
docker-compose logs -f app --tail 100

# Systemd
journalctl -u fyixt -f

# Application logs
tail -f data/fyi_webportal.db  # Database activity
```

### Check Health
```bash
# API status
curl https://viralclip.tech/api/health

# Container status
docker-compose ps

# Service status
systemctl status fyixt
```

---

## 🛑 Stopping/Restarting

### With Docker
```bash
# Stop
docker-compose down

# Restart
docker-compose up -d

# Rebuild
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### With Systemd
```bash
# Stop
sudo systemctl stop fyixt

# Restart
sudo systemctl restart fyixt

# View status
sudo systemctl status fyixt
```

---

## 🚨 Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs app

# Common issues:
# - Port 8000 already in use
# - .env file missing or invalid
# - Database file permissions
```

### API returns 401 Unauthorized
```bash
# Token should be auto-injected
# Check browser DevTools for window.__FYI_TOKEN
# Verify index.html is being served correctly
```

### Database locked
```bash
# Delete lock files
rm data/fyi_webportal.db-wal data/fyi_webportal.db-shm

# Restart
docker-compose restart app
```

### CORS errors
```bash
# Add domain to FYI_ALLOWED_ORIGINS in .env
# Restart to apply changes
```

---

## 📞 Support

**For deployment help:**
- See [SETUP.md](../SETUP.md) - Installation
- See [DEVELOPMENT.md](../DEVELOPMENT.md) - Architecture
- See [DASHBOARD_INTEGRATION.md](../DASHBOARD_INTEGRATION.md) - Integration guide

**Files:**
- Repository: https://github.com/rishabhouellette/fyi
- Dashboard: `desktop/dist/`
- Backend: Python files in root directory
- Config: `.env` file (create on deployment)

---

## 🎉 Deployment Summary

**Status:** ✅ Ready for Production  
**Built:** March 15, 2026  
**Version:** 2.0.0 (Production)  

**Components:**
- ✅ Backend: FastAPI + SQLite
- ✅ Frontend: React SPA
- ✅ Scheduler: Background tasks
- ✅ Database: SQLite
- ✅ Authentication: Token-based

**Next Step:** Choose your deployment option (Docker recommended) and follow the steps above.

