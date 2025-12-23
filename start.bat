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
echo  [1] Desktop app (no browser)
echo      - Runs: NiceGUI desktop-style UI (main.py)
echo      - URL:  http://localhost:8080 (opened manually)
echo.
echo  [2] Start ALL APIs
echo      - Desktop API + OAuth callback (desktop_api.py)  [https://127.0.0.1:%FYI_API_PORT%/oauth/callback]
echo      - Integration API (api_server.py)               [http://127.0.0.1:5001/]
echo.
echo  [3] Browser app (Control Center)
echo      - Runs: backend.main (NiceGUI)
echo      - URL:  http://127.0.0.1:%FYI_WEB_PORT%/
echo.
echo  [4] Live errors (logs)
echo      - Tails logs in real-time (logs/*.log, test_e2e.log)
echo.
echo  [5] Desktop (Tauri dev)
echo      - Runs: desktop\ npm run tauri:dev
echo.
echo  [6] Safe cleanup (recommended)
echo      - Removes caches/log clutter; keeps data/accounts
echo.
echo  [7] End-to-end tests (verbose)
echo      - Runs: python test_e2e.py --verbose
echo.
echo  [X] Exit
echo.
set /p MENU_CHOICE="Select an option: "

if /I "%MENU_CHOICE%"=="1" goto desktop_app
if /I "%MENU_CHOICE%"=="2" goto all_apis
if /I "%MENU_CHOICE%"=="3" goto browser_app
if /I "%MENU_CHOICE%"=="4" goto live_errors
if /I "%MENU_CHOICE%"=="5" goto tauri_dev
if /I "%MENU_CHOICE%"=="6" goto cleanup_safe
if /I "%MENU_CHOICE%"=="7" goto run_tests
if /I "%MENU_CHOICE%"=="X" goto end

echo.
echo [WARN] Invalid selection: %MENU_CHOICE%
timeout /t 2 >nul
goto menu

REM ------------------------------------------------------------------------------
REM Launch targets
REM ------------------------------------------------------------------------------

:desktop_app
REM NiceGUI app with no auto browser
call :launch_python_env "Desktop App" "NICEGUI_NO_BROWSER=1 NICEGUI_PORT=8080" "python main.py"
goto post_launch

:all_apis
REM Desktop API (Flask) + Integration API (legacy HTTPServer)
call :launch_python_env "Desktop API + OAuth" "" "python desktop_api.py"
call :launch_python_env "Integration API" "" "python api_server.py"
goto post_launch

:browser_app
call :launch_python_env "Control Center" "" "python -m backend.main"
start "" http://127.0.0.1:%FYI_WEB_PORT%/
goto post_launch

:live_errors
call :tail_logs
goto post_launch

:tauri_dev
call :start_script "Tauri Dev" "start_desktop.bat"
goto post_launch

:cleanup_safe
call :start_script "Safe Cleanup" "cleanup_safe.bat"
goto post_launch

:run_tests
call :launch_python_env "End-to-End Tests" "" "python test_e2e.py --verbose"
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
start "%WINDOW_TITLE%" cmd /v:on /s /k ""cd /d ""%ROOT%"" ^& call ""%ROOT%\%SCRIPT%""""
exit /b 0

:launch_python_env
set "WINDOW_TITLE=%~1"
set "ENVVARS=%~2"
set "RUN_COMMAND=%~3"
set "ENV_CHAIN="
if defined ENVVARS (
    for %%A in (%ENVVARS%) do set "ENV_CHAIN=!ENV_CHAIN! ^& set %%~A"
)
start "%WINDOW_TITLE%" cmd /v:on /s /k ""cd /d ""%ROOT%"" ^& call ""%VENV_ACTIVATE%""!ENV_CHAIN! ^& %RUN_COMMAND%""
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

:tail_logs
REM Live log viewer: follow logs\*.log and test_e2e.log if present.
start "Live Errors" powershell -NoProfile -ExecutionPolicy Bypass -Command "Set-Location -LiteralPath '%ROOT%'; Write-Host '== FYI Live Errors ==' -ForegroundColor Cyan; Write-Host 'Tip: most live errors also appear in the service windows.'; $paths=@(); if(Test-Path 'test_e2e.log'){ $paths+= (Resolve-Path 'test_e2e.log').Path }; if(Test-Path 'logs'){ Get-ChildItem -Path 'logs' -Filter '*.log' -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 5 | ForEach-Object { $paths += $_.FullName } }; if($paths.Count -eq 0){ Write-Host 'No log files found yet (run an option first).' -ForegroundColor Yellow; Pause; exit }; Write-Host ('Tailing: ' + ($paths -join ', ')); Get-Content -Path $paths -Wait"
exit /b 0