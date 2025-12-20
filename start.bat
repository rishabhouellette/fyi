@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION
REM ==============================================================================
REM FYIUploader - Main Launcher (December 2025)
REM Use this file. Other .bat files at repo root are mostly wrappers.
REM ==============================================================================

title FYIUploader Launcher
color 0A

for %%I in ("%~dp0.") do set "ROOT=%%~fI"
cd /d "%ROOT%"

set "VENV_ACTIVATE=%ROOT%\venv\Scripts\activate.bat"

REM Default ports/env for child processes
set "FYI_WEB_PORT=8000"
set "FYI_API_PORT=5000"
set "FYI_OAUTH_REDIRECT=https://127.0.0.1:5000/oauth/callback"
set "OAUTH_REDIRECT_ORIGIN=https://127.0.0.1:5000"

if not exist "%VENV_ACTIVATE%" (
    echo [ERROR] Virtual environment not found at: %VENV_ACTIVATE%
    echo Create it with: python -m venv venv
    pause
    exit /b 1
)

:menu
cls
call :banner
echo  [1] Web Portal (NiceGUI UI)            (start_web_portal.bat)
echo  [2] Web Control Center (backend.main)  (python -m backend.main)
echo  [3] Desktop API debug (Flask)          (start_backend_debug.bat)
echo  [4] Desktop dev (Tauri)                (start_desktop.bat)
echo  [5] Start ALL (Flask + Tauri)          (start_all.bat)
echo  [6] Infinity launcher menu             (start_fyi_infinity.bat)
echo  [7] Safe cleanup (recommended)         (cleanup_safe.bat)
echo  [8] Cleanup (non-destructive)          (cleanup.bat)
echo  [9] End-to-end tests                   (test_e2e.py --verbose)
echo  [X] Exit
echo.
set /p MENU_CHOICE="Select an option: "

if /I "%MENU_CHOICE%"=="1" goto web_portal
if /I "%MENU_CHOICE%"=="2" goto web_control_center
if /I "%MENU_CHOICE%"=="3" goto backend_debug
if /I "%MENU_CHOICE%"=="4" goto tauri_dev
if /I "%MENU_CHOICE%"=="5" goto start_all
if /I "%MENU_CHOICE%"=="6" goto infinity_menu
if /I "%MENU_CHOICE%"=="7" goto cleanup_safe
if /I "%MENU_CHOICE%"=="8" goto cleanup
if /I "%MENU_CHOICE%"=="9" goto run_tests
if /I "%MENU_CHOICE%"=="X" goto end

echo.
echo [WARN] Invalid selection: %MENU_CHOICE%
timeout /t 2 >nul
goto menu

:web_portal
call :start_script "Web Portal" "start_web_portal.bat"
goto post_launch

:web_control_center
call :launch_python "Web Control Center" "python -m backend.main"
start "" http://127.0.0.1:%FYI_WEB_PORT%/
goto post_launch

:backend_debug
call :start_script "Desktop API Debug" "start_backend_debug.bat"
goto post_launch

:tauri_dev
call :start_script "Tauri Dev" "start_desktop.bat"
goto post_launch

:start_all
call :start_script "Start All" "start_all.bat"
goto post_launch

:infinity_menu
call :start_script "Infinity Launcher" "start_fyi_infinity.bat"
goto post_launch

:cleanup_safe
call :start_script "Safe Cleanup" "cleanup_safe.bat"
goto post_launch

:cleanup
call :start_script "Cleanup" "cleanup.bat"
goto post_launch

:run_tests
call :launch_python "End-to-End Tests" "python test_e2e.py --verbose"
goto post_launch

:post_launch
echo.
echo [INFO] Selected processes are starting in their own windows.
echo       Close those windows to stop the services.
timeout /t 2 >nul
goto menu

:start_script
set "WINDOW_TITLE=%~1"
set "SCRIPT=%~2"
start "%WINDOW_TITLE%" cmd /k ""cd /d "%ROOT%" && call "%ROOT%\%SCRIPT%"""
exit /b 0

:launch_python
set "WINDOW_TITLE=%~1"
set "RUN_COMMAND=%~2"
start "%WINDOW_TITLE%" cmd /k ""cd /d "%ROOT%" && call "%VENV_ACTIVATE%" && %RUN_COMMAND%"""
exit /b 0

:banner
echo ================================================================================
echo FYI SOCIAL - CHOOSE WHAT TO LAUNCH
echo ================================================================================
echo  Repo: %ROOT%
echo  Web/UI port: %FYI_WEB_PORT%    API port: %FYI_API_PORT%
echo  OAuth redirect: %FYI_OAUTH_REDIRECT%
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