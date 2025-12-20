@echo off
setlocal

REM Resolve repo root (this script lives in scripts\windows)
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"

REM Start Flask backend server
start "Flask API" cmd /k "cd /d \"%ROOT%\" ^& call \"%ROOT%\venv\Scripts\activate.bat\" ^& python desktop_api.py"

REM Start Tauri desktop app
start "Tauri App" cmd /k "cd /d \"%ROOT%\desktop\" ^& npm run tauri:dev"

endlocal
