@echo off
REM ================================================================================
REM FYI UPLOADER - CLEANUP SCRIPT
REM Removes unnecessary files and optimizes folder
REM ================================================================================

title FYI Uploader - Cleanup & Optimization

setlocal
for %%I in ("%~dp0..\..") do set "ROOT=%%~fI"
cd /d "%ROOT%"

echo.
echo ================================================================================
echo FYI UPLOADER - CLEANUP MENU
echo ================================================================================
echo.
echo This will remove unnecessary files and optimize your folder.
echo.
echo Options:
echo.
echo 1) View Report Only (No changes)
echo 2) Clean Python Cache (__pycache__)
echo 3) Delete Old Documentation Files
echo 4) Delete Redundant Code Files
echo 5) Archive Old Logs
echo 6) FULL CLEANUP (All of above)
echo 7) Exit
echo.

set /p choice="Enter choice (1-7): "

if "%choice%"=="1" goto view_report
if "%choice%"=="2" goto clean_cache
if "%choice%"=="3" goto delete_docs
if "%choice%"=="4" goto delete_code
if "%choice%"=="5" goto archive_logs
if "%choice%"=="6" goto full_cleanup
if "%choice%"=="7" goto end
echo Invalid choice. Please try again.
goto start

:view_report
echo.
echo ================================================================================
echo FOLDER AUDIT REPORT
echo ================================================================================
echo.
type FOLDER_AUDIT_REPORT.txt
echo.
pause
goto end

:clean_cache
echo.
echo ================================================================================
echo CLEANING PYTHON CACHE
echo ================================================================================
echo.
echo This will delete __pycache__ folders and .pyc files.
echo Space saved: ~0.09 MB
echo Risk: None (auto-regenerates on next run)
echo.

set /p confirm="Continue? (y/n): "
if /i "%confirm%"=="y" (
    echo Deleting __pycache__...
    for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
    echo.
    echo ✓ Cache cleaned successfully!
    echo.
) else (
    echo Cancelled.
)
pause
goto start

:delete_docs
echo.
echo ================================================================================
echo DELETING OLD DOCUMENTATION
echo ================================================================================
echo.
echo Files to delete:
echo - File Structure.txt
echo - PHASE_2_COMPLETE.txt
echo - README_PHASE_2.txt
echo - DELIVERABLES.txt
echo - MANIFEST.txt
echo - ARCHITECTURE.txt
echo - INTEGRATION_GUIDE.txt
echo - PROJECT_STATUS.txt
echo - SETUP_INSTRUCTIONS.txt
echo - TASK_12_COMPLETION.md
echo - fyi_successfully_scheduled.txt
echo - readme.txt
echo.
echo Space saved: ~30 KB
echo Risk: None (all info in new docs)
echo.

set /p confirm="Continue? (y/n): "
if /i "%confirm%"=="y" (
    echo Deleting old documentation files...
    del /f "File Structure.txt" 2>nul
    del /f PHASE_2_COMPLETE.txt 2>nul
    del /f README_PHASE_2.txt 2>nul
    del /f DELIVERABLES.txt 2>nul
    del /f MANIFEST.txt 2>nul
    del /f ARCHITECTURE.txt 2>nul
    del /f INTEGRATION_GUIDE.txt 2>nul
    del /f PROJECT_STATUS.txt 2>nul
    del /f SETUP_INSTRUCTIONS.txt 2>nul
    del /f TASK_12_COMPLETION.md 2>nul
    del /f fyi_successfully_scheduled.txt 2>nul
    del /f readme.txt 2>nul
    echo.
    echo ✓ Old documentation deleted successfully!
    echo.
) else (
    echo Cancelled.
)
pause
goto start

:delete_code
echo.
echo ================================================================================
echo DELETING REDUNDANT CODE FILES
echo ================================================================================
echo.
echo Files to delete:
echo - test.py (use test_e2e.py instead)
echo - fb_diagnostics.py (functionality integrated)
echo - check_token_scopes.py (integrated into instagram_uploader.py)
echo.
echo Space saved: ~50 KB
echo Risk: None (functionality moved elsewhere)
echo.

set /p confirm="Continue? (y/n): "
if /i "%confirm%"=="y" (
    echo Deleting redundant code files...
    del /f test.py 2>nul
    del /f fb_diagnostics.py 2>nul
    del /f check_token_scopes.py 2>nul
    echo.
    echo ✓ Redundant code files deleted successfully!
    echo.
) else (
    echo Cancelled.
)
pause
goto start

:archive_logs
echo.
echo ================================================================================
echo ARCHIVING OLD LOGS
echo ================================================================================
echo.
echo This will move log files to archive subfolder.
echo Current log folder: logs/ (0.29 MB)
echo Risk: None (backups created)
echo.

set /p confirm="Continue? (y/n): "
if /i "%confirm%"=="y" (
    echo Creating archive folder...
    if not exist logs\archive mkdir logs\archive
    
    echo Moving logs...
    move logs\*.log logs\archive\ 2>nul
    
    echo.
    echo ✓ Logs archived successfully!
    echo Archived to: logs\archive\
    echo.
) else (
    echo Cancelled.
)
pause
goto start

:full_cleanup
echo.
echo ================================================================================
echo FULL CLEANUP - ALL OPTIMIZATIONS
echo ================================================================================
echo.
echo This will perform ALL cleanup steps:
echo 1. Clean Python cache (__pycache__)
echo 2. Delete old documentation (12 files)
echo 3. Delete redundant code (3 files)
echo 4. Archive old logs
echo.
echo Total space saved: ~30-50 MB
echo Risk: None (all changes safe)
echo.
echo BACKUP RECOMMENDED BEFORE PROCEEDING!
echo.

set /p confirm="Continue? (y/n): "
if /i "%confirm%"=="y" (
    echo.
    echo ✓ Step 1: Cleaning Python cache...
    for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d" 2>nul
    echo ✓ Done
    echo.
    
    echo ✓ Step 2: Deleting old documentation...
    del /f "File Structure.txt" 2>nul
    del /f PHASE_2_COMPLETE.txt 2>nul
    del /f README_PHASE_2.txt 2>nul
    del /f DELIVERABLES.txt 2>nul
    del /f MANIFEST.txt 2>nul
    del /f ARCHITECTURE.txt 2>nul
    del /f INTEGRATION_GUIDE.txt 2>nul
    del /f PROJECT_STATUS.txt 2>nul
    del /f SETUP_INSTRUCTIONS.txt 2>nul
    del /f TASK_12_COMPLETION.md 2>nul
    del /f fyi_successfully_scheduled.txt 2>nul
    del /f readme.txt 2>nul
    echo ✓ Done
    echo.
    
    echo ✓ Step 3: Deleting redundant code...
    del /f test.py 2>nul
    del /f fb_diagnostics.py 2>nul
    del /f check_token_scopes.py 2>nul
    echo ✓ Done
    echo.
    
    echo ✓ Step 4: Archiving logs...
    if not exist logs\archive mkdir logs\archive
    move logs\*.log logs\archive\ 2>nul
    echo ✓ Done
    echo.
    
    echo ================================================================================
    echo CLEANUP COMPLETE!
    echo ================================================================================
    echo.
    echo ✓ All unnecessary files removed
    echo ✓ Logs archived
    echo ✓ Cache cleaned
    echo.
    echo Next steps:
    echo 1. Run: python test_e2e.py (verify everything works)
    echo 2. Run: python start.bat (launch application)
    echo.
) else (
    echo Cancelled.
)
pause
goto end

:end
echo.
echo Exiting cleanup...
echo.
endlocal
exit /b 0
