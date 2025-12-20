# Scripts

This repo has many `.bat` files. The recommended entrypoint is:

- `start.bat` (main launcher)

Most other `.bat` files at repo root are *wrappers kept for backwards compatibility* that forward to `scripts/windows/*`.

## Windows

- `scripts/windows/start_web_portal.bat` — runs the NiceGUI UI (`main.py`) and opens `http://localhost:8080`.
- `scripts/windows/start_backend_debug.bat` — runs the legacy Flask desktop API (`desktop_api.py`) for debugging.
- `scripts/windows/start_desktop.bat` — runs Tauri dev (`npm run tauri:dev`) from `desktop/`.
- `scripts/windows/start_all.bat` — starts Flask API + Tauri dev.
- `scripts/windows/start_fyi_infinity.bat` — legacy menu launcher.
- `scripts/windows/cleanup_safe.bat` — safe cleanup (caches/logs/node_modules). Recommended.
- `scripts/windows/cleanup.bat` — legacy cleanup menu; destructive options are disabled.
- `scripts/windows/setup_phase2.bat` — installs Python deps + AI tooling (FFmpeg/Ollama).
- `scripts/windows/build_desktop.bat` — builds desktop installer via `npm run tauri build`.

## Unix

- `scripts/unix/build_desktop.sh` — desktop build helper.
