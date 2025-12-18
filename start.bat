@echo off
setlocal ENABLEDELAYEDEXPANSION
REM ==============================================================================
REM FYI UPLOADER - STARTUP MENU (December 2025)
REM Launch desktop, API, web UI, tests, or backend debug utilities
REM ==============================================================================

title FYI Uploader Startup
color 0A

set "PROJECT_DIR=D:\FYIUploader"
set "VENV_SCRIPTS=%PROJECT_DIR%\venv\Scripts"
set "VENV_ACTIVATE=%VENV_SCRIPTS%\activate.bat"
set "SERVER_HOST=127.0.0.1"
set "SERVER_PORT=8000"
set "OAUTH_REDIRECT_ORIGIN=https://127.0.0.1:5000"
set "NICEGUI_PORT=8080"
set "NICEGUI_NO_BROWSER=0"

REM Export env vars for all spawned processes
set "FYI_WEB_PORT=%SERVER_PORT%"
set "FYI_API_PORT=5000"
set "FYI_OAUTH_REDIRECT=https://127.0.0.1:5000/oauth/callback"
set "OAUTH_REDIRECT_ORIGIN=%OAUTH_REDIRECT_ORIGIN%"

if not exist "%PROJECT_DIR%" (
    echo [ERROR] Project directory not found: %PROJECT_DIR%
    pause
    exit /b 1
)

if not exist "%VENV_ACTIVATE%" (
    echo [ERROR] Virtual environment not found at: %VENV_ACTIVATE%
    echo Create it with: python -m venv venv
    pause
    exit /b 1
)

:menu
cls
call :banner
echo  [1] Desktop app only (python main.py)
echo  [1D] Desktop app only (no browser)
echo  [2] Desktop + REST API (api_server.py)
echo  [3] Desktop + Web Control Center (backend.main)
echo  [4] Web Control Center only (backend.main)
echo  [5] End-to-end tests (test_e2e.py --verbose)
echo  [6] Desktop backend debugger (start_backend_debug.bat)
echo  [X] Exit
echo.
set /p MENU_CHOICE="Select an option: "

if /I "%MENU_CHOICE%"=="1" goto desktop_only
if /I "%MENU_CHOICE%"=="1D" goto desktop_only_no_browser
if /I "%MENU_CHOICE%"=="2" goto desktop_api
if /I "%MENU_CHOICE%"=="3" goto desktop_web
if /I "%MENU_CHOICE%"=="4" goto web_only
if /I "%MENU_CHOICE%"=="5" goto run_tests
if /I "%MENU_CHOICE%"=="6" goto backend_debug
if /I "%MENU_CHOICE%"=="X" goto end

echo.
echo [WARN] Invalid selection: %MENU_CHOICE%
timeout /t 2 >nul
goto menu

:desktop_only
call :launch "FYI Desktop" "set NICEGUI_NO_BROWSER=0 & set NICEGUI_PORT=%NICEGUI_PORT% & python main.py"
goto post_launch

:desktop_only_no_browser
call :launch "FYI Desktop (No Browser)" "set NICEGUI_NO_BROWSER=1 & set NICEGUI_PORT=%NICEGUI_PORT% & python main.py"
goto post_launch

:desktop_api
call :launch "FYI Desktop" "python main.py"
call :launch "REST API" "python api_server.py"
goto post_launch

:desktop_web
call :launch "FYI Desktop" "python main.py"
call :launch "Web Control Center" "python -m backend.main"
start "" http://127.0.0.1:8000/ui/
goto post_launch

:web_only
call :launch "Web Control Center" "python -m backend.main"
start "" http://127.0.0.1:8000/ui/
goto post_launch

:run_tests
call :launch "End-to-End Tests" "python test_e2e.py --verbose"
goto post_launch

:backend_debug
start "Desktop Backend Debug" cmd /k "cd /d %PROJECT_DIR% && call start_backend_debug.bat"
goto post_launch

:post_launch
echo.
echo [INFO] Selected processes are starting in their own windows.
echo       Close those windows to stop the services.
timeout /t 2 >nul
goto menu

:launch
set "WINDOW_TITLE=%~1"
set "RUN_COMMAND=%~2"
start "%WINDOW_TITLE%" cmd /k "cd /d %PROJECT_DIR% && call ""%VENV_ACTIVATE%"" && %RUN_COMMAND%"
exit /b 0

:banner
echo ================================================================================
echo FYI SOCIAL - CHOOSE WHAT TO LAUNCH
echo ================================================================================
echo  FastAPI backend host: %SERVER_HOST%:%SERVER_PORT%
echo  OAuth redirect origin: %OAUTH_REDIRECT_ORIGIN%
echo -------------------------------------------------------------------------------
echo  Press Ctrl+C in any spawned window to stop that service.
echo -------------------------------------------------------------------------------
echo.
exit /b 0

:end
echo.
echo [INFO] Exiting launcher.
echo.
endlocal
exit /b 0