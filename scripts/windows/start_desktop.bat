@echo off
echo ====================================
echo FYI Social Infinity - Development Mode
echo ====================================
echo.

cd desktop

echo Starting development server...
echo Frontend: http://localhost:5173
echo.

call npm run tauri:dev
