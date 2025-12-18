@echo off
setlocal

REM ================================================================================
REM FYIUploader - SAFE CLEANUP (does NOT delete user accounts or database)
REM Removes common large junk folders (node_modules, caches) and log clutter.
REM ================================================================================

cd /d %~dp0

echo.
echo ==========================
echo FYIUploader SAFE CLEANUP
echo ==========================
echo.
echo This will remove:
echo   - desktop\node_modules
echo   - Python __pycache__ folders
echo   - logs\*.log (keeps folder)
echo   - test_e2e.log
echo.
echo This will NOT remove:
echo   - accounts\accounts.json
echo   - data\ databases/uploads
echo   - your .env
echo.
echo Press Ctrl+C to cancel.
echo.
pause

if exist "desktop\node_modules" (
  echo Removing desktop\node_modules ...
  rmdir /s /q "desktop\node_modules"
) else (
  echo desktop\node_modules not found.
)

echo Removing __pycache__ folders ...
for /d /r %%D in (__pycache__) do (
  rmdir /s /q "%%D" 2>nul
)

if exist "logs" (
  echo Clearing logs\*.log ...
  del /q "logs\*.log" 2>nul
) else (
  echo logs folder not found.
)

if exist "test_e2e.log" (
  echo Deleting test_e2e.log ...
  del /q "test_e2e.log" 2>nul
)

echo.
echo Done.
echo.
pause
endlocal
exit /b 0
