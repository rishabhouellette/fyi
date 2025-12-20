@echo off
echo ====================================
echo FYI Social Infinity - Development Mode
echo ====================================
echo.

setlocal
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%\desktop"

echo Starting development server...
echo Frontend: http://localhost:5173
echo.

call npm run tauri:dev

endlocal
