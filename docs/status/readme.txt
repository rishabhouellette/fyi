FYI Uploader — Quick Start (November 2025)
=========================================

This repo now ships with the embedded OAuth handler and a menu-driven
startup script, so you no longer need ngrok or extra terminals.

Recommended workflow
--------------------

1. Open PowerShell and switch to the project folder:
	 ````powershell
	 cd /d D:\FYIUploader
	 ````
2. Activate the virtual environment:
	 ````powershell
	 venv\Scripts\activate
	 ````
3. Launch the desktop app (no tunnels required):
	 ````powershell
	 python main.py
	 ````
	 or simply double-click `start.bat` and choose option **1**.

Need the API or web UI too?
--------------------------
- `start.bat` option **2** launches the REST API + desktop app.
- `start.bat` option **3** launches the desktop app + Web Control Center.
- `start.bat` option **4** launches only the Web Control Center
	(FastAPI + NiceGUI at http://127.0.0.1:8080).

Connecting Facebook/Instagram
-----------------------------
- Click **Connect** inside the Accounts panel.
- Your browser opens Facebook's OAuth page.
- After approving, a local `Success!` tab loads (served from 127.0.0.1).
- Close the tab and the desktop UI updates immediately.

If you ever need to adjust the callback origin, set
`OAUTH_REDIRECT_ORIGIN` in `.env` (defaults to `http://127.0.0.1:5000`).

Running tests (optional)
------------------------
````powershell
cd /d D:\FYIUploader
venv\Scripts\activate
python test_e2e.py --verbose
````
Expect all 82 flows to pass.

What changed in this upgrade?
----------------------------
- Embedded OAuth handler (`oauth_handler.py`) replaces ngrok+Flask.
- `start.bat` now offers five curated launch options.
- Desktop app includes Research Lab + Automation Lab tabs by default.
- Documentation refreshed (`README.md`, `WEB_FRONTEND.md`, etc.).

Diagnostics
-----------
- Need to keep the OAuth server running for troubleshooting?
	Run `python oauth_handler.py` (single callback per run).
- Want to sanity-check the Smart Scheduler? Use
	`Automation Lab -> Smart Timing` inside the desktop UI or the Web Control
	Center.

Everything else remains the same: 36 Python files load cleanly, 82 tests
pass, and the desktop UI continues to be the canonical surface.

