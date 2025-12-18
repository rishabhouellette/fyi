@echo off
title FYI Social Infinity - Web Portal
color 0B
echo.
echo  ███████╗██╗   ██╗██╗    ███████╗ ██████╗  ██████╗██╗ █████╗ ██╗     
echo  ██╔════╝╚██╗ ██╔╝██║    ██╔════╝██╔═══██╗██╔════╝██║██╔══██╗██║     
echo  █████╗   ╚████╔╝ ██║    ███████╗██║   ██║██║     ██║███████║██║     
echo  ██╔══╝    ╚██╔╝  ██║    ╚════██║██║   ██║██║     ██║██╔══██║██║     
echo  ██║        ██║   ██║    ███████║╚██████╔╝╚██████╗██║██║  ██║███████╗
echo  ╚═╝        ╚═╝   ╚═╝    ╚══════╝ ╚═════╝  ╚═════╝╚═╝╚═╝  ╚═╝╚══════╝
echo                                   INFINITY - Phase 0
echo.
echo ========================================================================
echo  Starting 2035 Cyber-Futuristic Web Portal...
echo ========================================================================
echo.
echo  [*] Activating virtual environment...
echo  [*] Loading Phase 0 design system...
echo  [*] Initializing NiceGUI server...
echo.
echo ========================================================================
echo  Web Portal will open at: http://localhost:8080
echo ========================================================================
echo.
echo  Press Ctrl+C to stop the server
echo.

REM Open browser after 2 seconds
start "" cmd /c "timeout /t 2 >nul && start http://localhost:8080"

REM Start the application
D:\FYIUploader\venv\Scripts\python.exe main.py

echo.
echo Server stopped.
pause
