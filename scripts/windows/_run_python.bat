@echo off
setlocal ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

REM Helper: run venv python from repo root with optional env vars
REM Usage: _run_python.bat [ENV=VALUE | ENV ...] [--] [python|py|pythonw] <python args...>
REM Example: _run_python.bat NICEGUI_NO_BROWSER=1 NICEGUI_PORT=8080 python main.py

REM scripts\windows is two levels below repo root
for %%I in ("%~dp0..\..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%" || exit /b 1

set "VENV_PY=%ROOT%\venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
  echo [ERROR] venv python not found: %VENV_PY%
  exit /b 3
)

:parse_env
if "%~1"=="" goto usage
if "%~1"=="--" (
  shift
  goto run
)
REM If the command starts here, stop parsing env vars.
if /I "%~1"=="python" goto run
if /I "%~1"=="py" goto run
if /I "%~1"=="pythonw" goto run

set "TOKEN=%~1"
echo(!TOKEN!| findstr /c:"=" >nul
if not errorlevel 1 (
  for /f "tokens=1* delims==" %%A in ('echo(!TOKEN!') do (
    set "ENV_NAME=%%~A"
    set "ENV_VAL=%%~B"
  )
  if "!ENV_VAL!"=="" (
    set "!ENV_NAME!=1"
  ) else (
    set "!ENV_NAME!=!ENV_VAL!"
  )
) else (
  REM Bare var names default to 1
  set "!TOKEN!=1"
)
shift
goto parse_env

:run
if "%~1"=="" goto usage
if defined FYI_RUNNER_DEBUG (
  echo [DEBUG] RAW_ARGS: %*
  echo [DEBUG] ARG1: %1
  echo [DEBUG] ARG2: %2
)
if /I "%~1"=="python" shift
if /I "%~1"=="py" shift
if /I "%~1"=="pythonw" shift
if "%~1"=="" goto usage
call "%VENV_PY%" %1 %2 %3 %4 %5 %6 %7 %8 %9
endlocal
exit /b %ERRORLEVEL%

:usage
echo Usage:
echo   %~nx0 [ENV=VALUE | ENV ...] [--] [python|py|pythonw] ^<python args...^>
echo Examples:
echo   %~nx0 python -m backend.main
echo   %~nx0 NICEGUI_NO_BROWSER NICEGUI_PORT=8080 -- python main.py
endlocal
exit /b 2
