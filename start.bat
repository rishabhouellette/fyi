@echo off
setlocal ENABLEEXTENSIONS

REM ==============================================================================
REM FYIUploader - Single Launcher (Web Portal)
REM - Builds React UI (desktop/dist) if needed
REM - Starts FastAPI server (web_server.py)
REM - Opens the browser automatically
REM ==============================================================================

title FYIUploader - Web Portal
color 0A

cd /d "%~dp0" || goto fatal
set "ROOT=%CD%"

set "HOST=localhost"
if "%FYI_WEB_PORTAL_PORT%"=="" set "FYI_WEB_PORTAL_PORT=5050"
set "PORT=%FYI_WEB_PORTAL_PORT%"

set "SCHEME=https"
set "HTTPS_ARGS=--https"
if /I "%FYI_DISABLE_HTTPS%"=="1" (
	set "SCHEME=http"
	set "HTTPS_ARGS="
)

REM ============================================================================
REM Optional: Auto-start ngrok and set FYI_PUBLIC_BASE_URL to public HTTPS.
REM Instagram publishing requires a publicly reachable HTTPS base URL.
REM
REM Controls:
REM  - FYI_USE_NGROK=1 (default) to enable
REM  - FYI_USE_NGROK=0 to disable
REM  - FYI_NGROK_BIN to override the ngrok executable path
REM ============================================================================
if "%FYI_USE_NGROK%"=="" set "FYI_USE_NGROK=1"

set "NGROK_PUBLIC="
if /I "%FYI_USE_NGROK%"=="1" (
	set "NGROK_EXE=%FYI_NGROK_BIN%"
	if "%NGROK_EXE%"=="" (
		for /f "delims=" %%G in ('where ngrok 2^>nul') do (
			set "NGROK_EXE=%%G"
			goto :ngrok_found
		)
	)
	:ngrok_found
	if not "%NGROK_EXE%"=="" (
		REM If ngrok API is already up, try to reuse an existing tunnel.
		for /f "usebackq delims=" %%U in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $t = Invoke-RestMethod -TimeoutSec 2 http://127.0.0.1:4040/api/tunnels; $u = ($t.tunnels | Where-Object { $_.proto -eq 'https' } | Select-Object -First 1 -ExpandProperty public_url); if ($u) { $u } } catch { }"`) do set "NGROK_PUBLIC=%%U"

		if "%NGROK_PUBLIC%"=="" (
			echo [INFO] Starting ngrok tunnel for port %PORT%...
			REM Note: ngrok should forward to https://localhost when our portal uses HTTPS.
			if /I "%SCHEME%"=="https" (
				start "ngrok" /min "%NGROK_EXE%" http https://localhost:%PORT% --log=stdout
			) else (
				start "ngrok" /min "%NGROK_EXE%" http %PORT% --log=stdout
			)

			REM Wait up to ~15s for ngrok to publish the URL.
			for /f "usebackq delims=" %%U in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$u=''; for($i=0;$i -lt 30 -and -not $u;$i++){ try { $t=Invoke-RestMethod -TimeoutSec 2 http://127.0.0.1:4040/api/tunnels; $u = ($t.tunnels | Where-Object { $_.proto -eq 'https' } | Select-Object -First 1 -ExpandProperty public_url); } catch {} ; Start-Sleep -Milliseconds 500 }; if($u){$u}"`) do set "NGROK_PUBLIC=%%U"
		)

		if not "%NGROK_PUBLIC%"=="" (
			REM Only set if not already provided by the user/environment.
			if "%FYI_PUBLIC_BASE_URL%"=="" set "FYI_PUBLIC_BASE_URL=%NGROK_PUBLIC%"
		) else (
			echo [WARN] ngrok did not return a public URL.
			echo [WARN] FYI_PUBLIC_BASE_URL will remain unset unless provided by your .env or environment.
		)
	) else (
		echo [WARN] ngrok not found on PATH. Set FYI_NGROK_BIN or install ngrok to enable Instagram publishing.
	)
)

REM Only fall back to a local base URL when ngrok is explicitly disabled.
REM When FYI_USE_NGROK=1, leaving this unset allows web_server.py to load it from .env.
if "%FYI_PUBLIC_BASE_URL%"=="" (
	if /I "%FYI_USE_NGROK%"=="0" set "FYI_PUBLIC_BASE_URL=%SCHEME%://%HOST%:%PORT%"
)

echo.
echo ==============================================================================
echo FYIUploader Web Portal Launcher
echo ------------------------------------------------------------------------------
echo Local URL          : %SCHEME%://%HOST%:%PORT%/
echo FYI_PUBLIC_BASE_URL: %FYI_PUBLIC_BASE_URL%
echo HTTPS mode         : %SCHEME%
echo.
echo Notes:
echo  - Instagram publish REQUIRES FYI_PUBLIC_BASE_URL = public HTTPS URL.
echo    Example (ngrok): set FYI_PUBLIC_BASE_URL=https://xxxx.ngrok-free.app
echo  - OAuth redirect URLs you must allow in provider consoles:
echo    Facebook/Instagram: %FYI_PUBLIC_BASE_URL%/oauth/callback/facebook
echo    YouTube          : %FYI_PUBLIC_BASE_URL%/oauth/callback/youtube
echo ==============================================================================
echo.

set "PY=%ROOT%\venv\Scripts\python.exe"
if not exist "%PY%" goto no_venv
if not exist "%ROOT%\web_server.py" goto no_server
if not exist "%ROOT%\desktop\package.json" goto no_frontend

node -v >nul 2>nul
if errorlevel 1 goto no_node
call npm -v >nul 2>nul
if errorlevel 1 goto no_npm

if /I "%FYI_FORCE_REACT_BUILD%"=="1" goto build
if /I "%FYI_SKIP_REACT_BUILD%"=="1" goto run

if not exist "%ROOT%\desktop\dist\index.html" (
	echo [INFO] No existing React build found.
	goto build
)

REM If source files changed since last build, rebuild automatically.
echo [INFO] Checking whether React build is up-to-date...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
	"$dist = Join-Path '%ROOT%\desktop\dist' 'index.html';" ^
	"$srcRoot = Join-Path '%ROOT%\desktop' 'src';" ^
	"if (!(Test-Path $dist)) { exit 2 }" ^
	"if (!(Test-Path $srcRoot)) { exit 0 }" ^
	"$outTime = (Get-Item $dist).LastWriteTimeUtc;" ^
	"$latest = Get-ChildItem -LiteralPath $srcRoot -Recurse -File -ErrorAction SilentlyContinue | Sort-Object LastWriteTimeUtc -Descending | Select-Object -First 1;" ^
	"if ($latest -and $latest.LastWriteTimeUtc -gt $outTime) { exit 1 } else { exit 0 }"
if errorlevel 2 goto build
if errorlevel 1 (
	echo [INFO] React source changed since last build.
	goto build
)
echo [INFO] React build is up-to-date.
goto run

:build
cd /d "%ROOT%\desktop" || goto bad_frontend
if exist "%ROOT%\desktop\node_modules" goto deps_ok
echo [INFO] Installing frontend deps (first run)...
call npm install
if errorlevel 1 goto npm_failed

:deps_ok
echo [INFO] Building frontend...
call npm run build
if errorlevel 1 goto npm_failed
cd /d "%ROOT%"
goto run

:run
echo.
echo [INFO] Starting Web Portal: %SCHEME%://%HOST%:%PORT%/
echo [INFO] If the browser opens before the server is ready, refresh once.
start "" "%SCHEME%://%HOST%:%PORT%/"
"%PY%" "%ROOT%\web_server.py" --port %PORT% %HTTPS_ARGS%
echo.
echo [INFO] Server stopped.
pause
goto end

:no_node
echo [ERROR] Node.js not found. Install Node LTS first.
echo         https://nodejs.org/
pause
exit /b 10

:no_npm
echo [ERROR] npm not found (Node install looks incomplete).
pause
exit /b 11

:no_venv
echo [ERROR] Python venv not found: %PY%
echo         Create it with: python -m venv venv
pause
exit /b 1

:no_server
echo [ERROR] Missing web_server.py in repo root.
pause
exit /b 2

:no_frontend
echo [ERROR] Missing desktop\package.json (React app).
pause
exit /b 3

:bad_frontend
echo [ERROR] Failed to open desktop folder.
pause
exit /b 12

:npm_failed
echo [ERROR] Frontend build failed.
pause
exit /b 13

:fatal
echo [ERROR] Failed to set working directory.
pause
exit /b 99

:end
endlocal
exit /b 0