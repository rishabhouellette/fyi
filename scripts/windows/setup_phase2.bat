@echo off
REM FYI Social Infinity - Phase 2 AI Engine Setup
REM This script installs all dependencies for Phase 2

echo ====================================
echo FYI Social Infinity - Phase 2 Setup
echo ====================================
echo.

setlocal
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%"

set "PYTHON=python"
if exist "%ROOT%\venv\Scripts\python.exe" set "PYTHON=%ROOT%\venv\Scripts\python.exe"

REM Check if Python is available
"%PYTHON%" --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found! Please install Python 3.11+
    pause
    endlocal
    exit /b 1
)

echo [1/5] Installing Python dependencies...
"%PYTHON%" -m pip install -r "%ROOT%\requirements.txt"

echo.
echo [2/5] Checking FFmpeg installation...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] FFmpeg not found. Installing via winget...
    winget install FFmpeg
    if %errorlevel% neq 0 (
        echo [ERROR] FFmpeg installation failed!
        echo Please install manually: https://ffmpeg.org/download.html
    ) else (
        echo [OK] FFmpeg installed successfully
    )
) else (
    echo [OK] FFmpeg already installed
)

echo.
echo [3/5] Checking Ollama installation...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Ollama not found!
    echo.
    echo Please install Ollama manually:
    echo 1. Download from: https://ollama.ai
    echo 2. Run the installer
    echo 3. Run this script again
    echo.
    pause
    exit /b 1
) else (
    echo [OK] Ollama already installed
)

echo.
echo [4/5] Starting Ollama server...
start /B ollama serve >nul 2>&1
timeout /t 3 >nul

echo.
echo [5/5] Downloading recommended AI models...
echo This may take a while (downloading 50GB+)...
echo.

REM Download models using Python
"%PYTHON%" -c "from ai_engine import get_ollama_manager; m = get_ollama_manager(); m.setup_recommended_models()"

if %errorlevel% neq 0 (
    echo.
    echo [!] Model download failed or skipped
    echo You can download models later by running:
    echo   python -c "from ai_engine import get_ollama_manager; get_ollama_manager().setup_recommended_models()"
)

echo.
echo ====================================
echo Setup Complete!
echo ====================================
echo.
echo Next steps:
echo 1. Test the installation: python -c "from video_lab import get_auto_editor; print('OK')"
echo 2. Read docs\phases\PHASE_2_README.md for usage examples
echo 3. Process your first video!
echo.
pause

endlocal
