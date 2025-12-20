@echo off
setlocal
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%"

REM Activate virtual environment
call "%ROOT%\venv\Scripts\activate.bat"

REM Show redirect URI being used
python -c "from config import Config; print('Redirect URI:', Config.from_env().redirect_uri)"

REM Start backend server with logging
python desktop_api.py

endlocal
