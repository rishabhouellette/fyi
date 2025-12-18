# Complete Setup Instructions for FYI Uploader (Embedded OAuth Edition)



\## Files You Now Have



\### Core Modules (added/fixed in this drop)

\- ✅ `config.py` - Central configuration loader

\- ✅ `exceptions.py` - Custom exception hierarchy

\- ✅ `logger\_config.py` - Structured logging setup

\- ✅ `account\_manager.py` - Multi-account storage + Fernet encryption

\- ✅ `facebook\_uploader.py` - Chunked upload implementation

\- ✅ `video\_validator.py` - FPS/resolution guardrails

\- ✅ `oauth\_handler.py` - Embedded OAuth callback server (replaces ngrok)

\- ✅ `scheduler\_engine.py` - Background scheduler core

\- ✅ `main.py` - Desktop UI patched with Research/Automation tabs

\- ✅ `start.bat` - Menu-driven launcher (desktop, API, web, tests)



\### Keep Your Existing Files

\- `youtube\_uploader.py`

\- `instagram\_uploader.py`



\## Step-by-Step Setup



\### 1. Create the `.env`

```bash
cp .env.example .env
```

Populate it with your Facebook app values (adjust as needed):

```ini
FB_APP_ID=222188858294490
FB_APP_SECRET=6f1c65510e626e9bb45fd5d2f52f8565
OAUTH_REDIRECT_ORIGIN=http://127.0.0.1:5000  # change only if you bind to another host/port
```

No `NGROK_URL` is required anymore. The desktop app launches a local
callback server on demand.



\### 2. Install dependencies

```bash
pip install -r requirements.txt
```



\### 3. Launch FYI Uploader (choose one)

**Option A – Desktop only**

```powershell
cd /d D:\FYIUploader
venv\Scripts\activate
python main.py
```

**Option B – Use the startup menu (recommended)**

Double-click `start.bat` and pick the mode you need:

1. Desktop app only.
2. Desktop + REST API (`api_server.py`).
3. Desktop + Web Control Center (FastAPI + NiceGUI).
4. Web Control Center only (served at http://127.0.0.1:8080).
5. End-to-end tests.

Every option spawns its own terminal windows, so you no longer have to
manually juggle ngrok or Flask processes.



\### 4. Connect Facebook/Instagram (embedded OAuth)

1. Launch the desktop app and open **Accounts**.
2. Click **Connect Facebook** or **Connect Instagram**.
3. Your default browser opens Facebook's login + permissions screen.
4. Approve the prompts; a local `Success!` page (127.0.0.1) appears.
5. Close the tab — the desktop UI instantly shows `Connected as ...`.

Need to troubleshoot? Run `python oauth_handler.py` to keep the callback
server alive for a single request, or update `OAUTH_REDIRECT_ORIGIN` in
`.env` to bind to another host/port.



\## First-Time Usage



\### Upload a test video

1. Click **1. Select Videos** and choose a sample clip.
2. Use **INSTANT UPLOAD** (quick manual check) or **SMART SCHEDULER** for
	 auto-spacing.
3. Watch live status updates under the queue table.
4. Review `logs/facebook_uploader.log` if you need deeper traces.



\### Scheduler modes

1. **INSTANT UPLOAD** – Push immediately.
2. **SCHEDULER** – Interval-based scheduling (every X minutes).
3. **SMART SCHEDULER** – Reads your page's backlog, queues in parallel,
	 and tracks elapsed time per upload.

Use **Scheduler Settings** to toggle interval vs. specific timestamp.



\## Optional Extras

- `python test_e2e.py --verbose` — run all 82 regression tests.
- `python -m web.app` — launch the browser-based Control Center without
	using `start.bat`.
- `python cleanup.py` — remove cached build artifacts/logs if needed.

That's it — no ngrok tunnels, no extra terminals, and no manual OAuth
server required.



\## Testing Smart Scheduler:



\### To test the Smart Scheduler feature:

1\. Schedule 2-3 videos manually on Facebook (using regular scheduler)

2\. Click \*\*\\"SMART SCHEDULER\\"\*\*

3\. It will:

&nbsp;  - Check your last scheduled video time

&nbsp;  - Schedule new videos AFTER the last one

&nbsp;  - Use your configured interval



Example:

```

Last scheduled video: 3:00 PM

Interval: 30 minutes

Smart Scheduler will start at: 3:30 PM, 4:00 PM, 4:30 PM...

```



\## Troubleshooting:



\### \\"Missing environment variables\\"

→ Create `.env` file with FB\_APP\_ID, FB\_APP\_SECRET, NGROK\_URL



\### \\"No module named 'config'\\"

→ Make sure all provided files are in the same directory as main.py



\### \\"Account not found\\"

→ Link Facebook account first via the GUI



\### Facebook upload fails

→ Check:

1\. Is OAuth server running? (`python server.py`)

2\. Is ngrok running?

3\. Did you link account successfully?

4\. Check logs: `logs/facebook\_uploader.log`



\### Smart Scheduler not working

→ Make sure:

1\. Facebook account is linked

2\. Set interval in Scheduler Settings first

3\. Check logs for API errors



\## File Locations:



\- \*\*Accounts\*\*: `accounts/accounts.json`

\- \*\*Logs\*\*: `logs/` directory

\- \*\*Upload Log\*\*: `fyi\_successfully\_scheduled.txt`

\- \*\*Queue Log\*\*: `fyi\_queue\_log.csv`



\## What Changed from Your Old Code:



\### Same Features:

✅ Facebook upload with chunked resumable upload

✅ Smart Scheduler (checks last scheduled video)

✅ OAuth with state management

✅ Multi-account support

✅ Video validation



\### New Features:

✅ Better GUI (your CustomTkinter interface)

✅ Centralized config system

✅ Proper logging to files

✅ Modular architecture

✅ No hardcoded credentials



\### Key Difference:

\*\*Old\*\*: Credentials hardcoded in Python files

\*\*New\*\*: Credentials in `.env` file (secure \& proper)



\## Need Help?



Check the logs:

```bash

\# Main app log

tail -f logs/\_\_main\_\_.log



\# Facebook uploader log

tail -f logs/facebook\_uploader.log



\# Server log

tail -f logs/server.log

```



All errors will be logged there with full details.



---



\*\*You're all set! The Facebook uploader now uses your working old code with the new GUI.\*\*

"

