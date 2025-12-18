@echo off
REM FYI Social Infinity - Quick Launch Script
REM Starts the 2035 Cyber-Futuristic UI

title FYI Social Infinity

cd /d %~dp0

echo.
echo ================================================================================
echo FYI SOCIAL INFINITY - 2035 CYBER-FUTURISTIC INTERFACE
echo ================================================================================
echo.
echo Starting the application...
echo.
echo Access at: http://127.0.0.1:8080
echo.
echo Press Ctrl+C to stop the application
echo.

REM Activate venv
call venv\Scripts\activate.bat

REM Launch the cyber UI
python main_cyber.py

pause
