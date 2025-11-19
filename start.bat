@echo off
REM ================================================================================
REM FYI UPLOADER - STARTUP SCRIPT (Updated November 16, 2025)
REM Automatically starts all components in separate windows
REM ================================================================================

title FYI Uploader Startup
color 0A

REM Set project directory
cd /d D:\FYIUploader

echo.
echo ================================================================================
echo FYI UPLOADER - STARTUP MENU
echo ================================================================================
echo.
echo Choose startup option:
echo.
echo 1) GUI Only (No API, No Ngrok) - Fastest
echo 2) GUI + Ngrok (Recommended) - Production
echo 3) Full Setup (GUI + API + Ngrok) - All Features
echo 4) Run Tests Only (Verify everything works)
echo 5) Exit
echo.

set /p choice="Enter choice (1-5): "

if "%choice%"=="1" goto gui_only
if "%choice%"=="2" goto gui_ngrok
if "%choice%"=="3" goto full_setup
if "%choice%"=="4" goto run_tests
if "%choice%"=="5" goto end
echo Invalid choice. Please try again.
goto start

:gui_only
echo.
echo Starting GUI application only...
echo.
call venv\Scripts\activate.bat
python main.py
goto end

:gui_ngrok
echo.
echo ================================================================================
echo Starting FYI Uploader with Ngrok tunnel (Recommended Setup)
echo ================================================================================
echo.
echo Window 1: Ngrok tunnel will open
echo Window 2: Main GUI application
echo.
echo Keep both windows open for full functionality
echo.
pause

REM Start Ngrok in new window
echo Starting Ngrok tunnel on port 5000...
start "Ngrok Tunnel - FYI Uploader" cmd /k "cd /d D:\FYIUploader && venv\Scripts\activate.bat && ngrok http 5000"

REM Wait 3 seconds for ngrok to start
timeout /t 3 /nobreak

REM Start main app in new window
echo Starting main GUI application...
start "FYI Uploader GUI - Main App" cmd /k "cd /d D:\FYIUploader && venv\Scripts\activate.bat && python main.py"

echo.
echo ================================================================================
echo Startup complete!
echo ================================================================================
echo.
echo Ngrok Dashboard: http://127.0.0.1:4040 (view in browser)
echo Main Application: Now launching...
echo.
echo To stop: Close the windows or press Ctrl+C in each window
echo.
pause
goto end

:full_setup
echo.
echo ================================================================================
echo Starting FYI Uploader - FULL SETUP (GUI + API + Ngrok)
echo ================================================================================
echo.
echo Window 1: Ngrok tunnel will open
echo Window 2: REST API server
echo Window 3: Main GUI application
echo.
echo Keep all windows open for full functionality
echo.
pause

REM Start Ngrok in new window
echo Starting Ngrok tunnel on port 5000...
start "Ngrok Tunnel - FYI Uploader" cmd /k "cd /d D:\FYIUploader && venv\Scripts\activate.bat && ngrok http 5000"

REM Wait 2 seconds for ngrok to start
timeout /t 2 /nobreak

REM Start API server in new window
echo Starting REST API server on port 8000...
start "FYI API Server - Port 8000" cmd /k "cd /d D:\FYIUploader && venv\Scripts\activate.bat && python api_server.py"

REM Wait 2 seconds for API to start
timeout /t 2 /nobreak

REM Start main app in new window
echo Starting main GUI application...
start "FYI Uploader GUI - Main App" cmd /k "cd /d D:\FYIUploader && venv\Scripts\activate.bat && python main.py"

echo.
echo ================================================================================
echo Full startup complete!
echo ================================================================================
echo.
echo Ngrok Dashboard: http://127.0.0.1:4040
echo REST API: http://localhost:8000/api/health
echo Main Application: Now launching...
echo.
echo To stop: Close the windows or press Ctrl+C in each window
echo.
pause
goto end

:run_tests
echo.
echo ================================================================================
echo Running End-to-End Test Suite
echo ================================================================================
echo.

call venv\Scripts\activate.bat

echo Running all 82 tests...
echo.

python test_e2e.py --verbose

echo.
echo ================================================================================
echo Test run complete! Check output above for results.
echo Expected: 82 tests passing
echo ================================================================================
echo.
pause
goto start

:end
echo.
echo Exiting...
echo.
exit /b 0