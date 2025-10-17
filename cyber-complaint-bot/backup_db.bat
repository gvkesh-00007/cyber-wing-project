@echo off
REM Database Backup Script for CyberComplaintBot
REM Schedule this script with Windows Task Scheduler for nightly backups

REM Create backups directory if it doesn't exist
if not exist "backups" mkdir backups

REM Get current date and time in format YYYY-MM-DD_HH-MM-SS
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%-%MM%-%DD%_%HH%-%Min%-%Sec%"

REM Copy database with timestamp
if exist "complaints.db" (
    copy "complaints.db" "backups\complaints_%timestamp%.db"
    echo Backup created: complaints_%timestamp%.db
    echo Backup completed successfully at %date% %time%
) else (
    echo ERROR: complaints.db not found!
)

REM Optional: Keep only last 30 days of backups (cleanup old backups)
forfiles /p "backups" /m complaints_*.db /d -30 /c "cmd /c del @path" 2>nul

echo.
echo Backup process complete.
pause
