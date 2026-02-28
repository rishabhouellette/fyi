@echo off
setlocal ENABLEEXTENSIONS

REM Helper: run another .bat from repo root (no venv activation)
REM Usage: _run_script.bat <relative-script-path> [args...]

REM scripts\windows is two levels below repo root
for %%I in ("%~dp0..\..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%" || exit /b 1

if "%~1"=="" (
  echo [ERROR] Missing script path.
  echo Usage: %~nx0 ^<relative-script-path^> [args...]
  exit /b 2
)

set "SCRIPT=%~1"
shift

call "%ROOT%\%SCRIPT%" %*
endlocal
exit /b %ERRORLEVEL%
