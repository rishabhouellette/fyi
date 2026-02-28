@echo off
setlocal ENABLEEXTENSIONS

if defined FYI_DEBUG (
  echo on
)

title FYI Social Infinity - React (Prod Build) + API
color 0B

for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%" || exit /b 1

set "APP_DIR=%ROOT%"
set "DESKTOP_DIR=%APP_DIR%\desktop"

REM Dedicated port/host for the React+FastAPI bundle (do NOT inherit FYI_WEB_PORT=8000)
REM Default to 5050 to avoid clashing with legacy OAuth/API port 5000.
if "%FYI_REPLIT_PORT%"=="" set "FYI_REPLIT_PORT=5050"
if "%FYI_REPLIT_HOST%"=="" set "FYI_REPLIT_HOST=127.0.0.1"

echo.
echo ========================================================================
echo  FYI Social Infinity - React UI (Prod Build) + FastAPI
echo ========================================================================
echo  UI+API URL: http://%FYI_REPLIT_HOST%:%FYI_REPLIT_PORT%/
echo.
echo  Notes:
echo   - This builds React to desktop\dist
echo   - Then FastAPI serves it from one port
echo   - For real business launch, set FYI_PUBLIC_BASE_URL to your HTTPS domain
echo ========================================================================
echo.

if defined FYI_DEBUG echo [DEBUG] Starting prereq checks...

node -v >nul 2>nul || goto no_node
call npm -v >nul 2>nul || goto no_npm
goto prereq_ok

:no_node
echo [ERROR] Node.js not found. Install Node LTS first.
echo         https://nodejs.org/
pause
exit /b 2

:no_npm
echo [ERROR] npm not found (Node install looks incomplete).
pause
exit /b 2

:prereq_ok
echo [INFO] Node/npm OK.

if not exist "%DESKTOP_DIR%\package.json" goto no_frontend

pushd "%DESKTOP_DIR%" || exit /b 4
echo [INFO] Frontend dir: %DESKTOP_DIR%

if exist "%DESKTOP_DIR%\node_modules" goto have_node_modules
echo [INFO] Installing frontend deps (first run)...
call npm install
if errorlevel 1 goto npm_install_failed

:have_node_modules
if /I "%FYI_FORCE_REACT_BUILD%"=="1" goto do_build
if /I "%FYI_SKIP_REACT_BUILD%"=="1" goto skip_build
if exist "%DESKTOP_DIR%\dist\index.html" goto skip_build

:do_build
echo [INFO] Building React UI...
call npm run build
if errorlevel 1 goto npm_build_failed
goto after_build

:skip_build
echo [INFO] Skipping build (desktop\dist already present). Set FYI_FORCE_REACT_BUILD=1 to rebuild.

:after_build

popd

goto after_frontend

:no_frontend
echo [ERROR] React desktop folder not found: %DESKTOP_DIR%
pause
exit /b 3

:npm_install_failed
echo [ERROR] npm install failed.
popd
pause
exit /b 5

:npm_build_failed
echo [ERROR] npm run build failed.
popd
pause
exit /b 6

:after_frontend

REM Port preflight: if something is already listening, ask what to do.
set "LISTEN_PID="
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%FYI_REPLIT_PORT% .*LISTENING"') do (
  if not "%%P"=="0" set "LISTEN_PID=%%P"
)

if "%LISTEN_PID%"=="" goto port_ok

echo.
echo [WARN] Port %FYI_REPLIT_PORT% is already in use (PID=%LISTEN_PID%).
echo.
tasklist /FI "PID eq %LISTEN_PID%"
echo.
echo   [O] Open existing app in browser and exit
echo   [R] Restart (kill PID and start a fresh server)
echo   [A] Abort
set /p _port_choice="Choose (O/R/A): "
if /I "%_port_choice%"=="O" goto open_existing
if /I "%_port_choice%"=="R" goto kill_existing
if /I "%_port_choice%"=="A" exit /b 10
echo [WARN] Unknown choice. Aborting.
exit /b 11

:kill_existing
echo [INFO] Killing PID %LISTEN_PID%...
taskkill /F /PID %LISTEN_PID% >nul 2>nul
goto port_ok

:open_existing
start "" powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process ('http://%FYI_REPLIT_HOST%:%FYI_REPLIT_PORT%/')"
exit /b 0

:port_ok

REM Open browser once the server is reachable
start "" powershell -NoProfile -ExecutionPolicy Bypass -Command "$h='%FYI_REPLIT_HOST%'; $p=%FYI_REPLIT_PORT%; for($i=0;$i -lt 30;$i++){ try{ $c=New-Object Net.Sockets.TcpClient; $c.Connect($h,$p); $c.Close(); Start-Process ('http://' + $h + ':' + $p + '/'); break } catch { Start-Sleep -Seconds 1 } }"

set "PORT=%FYI_REPLIT_PORT%"
if "%FYI_PUBLIC_BASE_URL%"=="" set "FYI_PUBLIC_BASE_URL=http://%FYI_REPLIT_HOST%:%FYI_REPLIT_PORT%"

echo [INFO] Starting FastAPI server...
"%ROOT%\venv\Scripts\python.exe" "%APP_DIR%\web_server.py" --port %FYI_REPLIT_PORT%

echo.
echo Server stopped.
pause
endlocal
