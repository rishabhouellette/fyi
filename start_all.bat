@echo off
REM Start Flask backend server
start "Flask API" cmd /k "cd /d %~dp0 & call D:\FYIUploader\venv\Scripts\activate && python desktop_api.py"

REM Start Tauri desktop app
start "Tauri App" cmd /k "cd /d %~dp0desktop && npm run tauri:dev"
