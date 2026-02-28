# Deploy FYIUploader to viralclip.tech (Docker + Nginx + Let's Encrypt)

This runs the FastAPI backend (`web_server.py`) on a VPS so Instagram “scheduling” works even when the browser is closed.

## Prereqs
- A VPS with Docker + Docker Compose
- DNS A records:
  - `viralclip.tech` -> your VPS IP
  - `www.viralclip.tech` -> your VPS IP (optional)
- Meta Developer Console updated to use public HTTPS redirect(s).

## Server setup (Ubuntu example)
```bash
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-plugin
sudo usermod -aG docker $USER
# log out/in
```

## Deploy steps
1) Copy repo to server
```bash
git clone <your repo url>
cd FYIUploader/deploy
```

2) Create env file
```bash
cp .env.example .env
nano .env
```
Fill `FB_APP_ID` and `FB_APP_SECRET`.

3) First-time TLS certificate issue
Run nginx first so the ACME challenge path is served:
```bash
docker compose up -d nginx
```
Then request certs:
```bash
docker compose run --rm certbot certonly \
  --webroot -w /var/www/certbot \
  -d viralclip.tech -d www.viralclip.tech \
  --email you@viralclip.tech --agree-tos --no-eff-email
```
Now start everything:
```bash
docker compose up -d --build
```

4) Verify
- Open `https://viralclip.tech/`
- API docs: `https://viralclip.tech/docs`

## Important notes
- Instagram publishing requires `FYI_PUBLIC_BASE_URL=https://viralclip.tech` so Meta can fetch uploaded media.
- Files persist via mounts:
  - `../data` (SQLite + uploads)
  - `../accounts` (tokens)
- If you use OAuth connect flows, update Meta dev console redirect URI to:
  - `https://viralclip.tech/oauth/callback`

## Troubleshooting
- See logs:
```bash
docker compose logs -f app
```
- If uploads fail via reverse proxy, ensure `client_max_body_size` is large enough in `nginx.conf`.
