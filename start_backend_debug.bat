@echo off
setlocal
cd /d %~dp0

REM Activate virtual environment
call D:\FYIUploader\venv\Scripts\activate.bat

REM Show redirect URI being used
python -c "from config import Config; print('Redirect URI:', Config.from_env().redirect_uri)"

REM Start backend server with logging
python desktop_api.py
