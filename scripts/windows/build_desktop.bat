@echo off
echo ====================================
echo Building FYI Social Infinity Desktop
echo ====================================
echo.

setlocal
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%\desktop"

echo [1/4] Installing dependencies...
call npm install
if %errorlevel% neq 0 (
    echo ERROR: npm install failed
    pause
    exit /b %errorlevel%
)

echo.
echo [2/4] Building React frontend...
call npm run build
if %errorlevel% neq 0 (
    echo ERROR: Frontend build failed
    pause
    exit /b %errorlevel%
)

echo.
echo [3/4] Building Tauri desktop app...
call npm run tauri build
if %errorlevel% neq 0 (
    echo ERROR: Tauri build failed
    pause
    exit /b %errorlevel%
)

echo.
echo [4/4] Build complete!
echo.
echo Your installers are in: desktop\src-tauri\target\release\bundle\
echo - Windows MSI: desktop\src-tauri\target\release\bundle\msi\
echo - Windows NSIS: desktop\src-tauri\target\release\bundle\nsis\
echo.
pause

endlocal
