@echo off
setlocal
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%"
echo ========================================
echo FYI Social Infinity - Launcher
echo ========================================
echo.
echo Choose your launch mode:
echo.
echo [1] Web Portal (NiceGUI on localhost:8080)
echo [2] Desktop App (Coming Soon)
echo [3] Both Web + Desktop
echo [4] Exit
echo.
set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto web
if "%choice%"=="2" goto desktop
if "%choice%"=="3" goto both
if "%choice%"=="4" goto end

:web
echo.
echo ========================================
echo Starting Web Portal...
echo ========================================
echo Opening at http://localhost:8080
echo Press Ctrl+C to stop the server
echo ========================================
echo.
start http://localhost:8080
"%ROOT%\venv\Scripts\python.exe" main.py
goto end

:desktop
echo.
echo ========================================
echo Desktop App - Coming Soon
echo ========================================
echo.
echo The desktop app will use Tauri or PyQt.
echo For now, launching web portal instead...
echo.
timeout /t 3
goto web

:both
echo.
echo ========================================
echo Starting Both Web + Desktop...
echo ========================================
echo.
echo [1/2] Starting Web Portal in background...
start /B "%ROOT%\venv\Scripts\python.exe" main.py
timeout /t 3
echo [2/2] Opening browser...
start http://localhost:8080
echo.
echo ========================================
echo Both services running!
echo Web Portal: http://localhost:8080
echo.
echo Press any key to stop all services...
echo ========================================
pause >nul
taskkill /F /IM python.exe /T >nul 2>&1
echo Services stopped.
goto end

:end
echo.
echo Goodbye!
timeout /t 2
endlocal
exit
