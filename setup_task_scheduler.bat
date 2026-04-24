@echo off
REM ============================================================
REM  setup_task_scheduler.bat
REM  Run this file ONCE as Administrator to register the daily
REM  6:00 PM stock fetch task in Windows Task Scheduler.
REM
REM  HOW TO USE:
REM    1. Right-click this file → "Run as administrator"
REM    2. Done — check Task Scheduler to confirm
REM ============================================================

REM ── PATHS (already updated for your machine) ──────────────────
SET PYTHON_PATH=C:\Users\skysu\anaconda3\python.exe
SET SCRIPT_PATH=C:\Users\skysu\Downloads\stock_pipeline\fetch_and_store.py
REM ─────────────────────────────────────────────────────────────

SET TASK_NAME=StockDataFetch

echo.
echo Registering Task Scheduler job...
echo   Task Name : %TASK_NAME%
echo   Python    : %PYTHON_PATH%
echo   Script    : %SCRIPT_PATH%
echo   Schedule  : Daily at 18:00 (6:00 PM)
echo.

REM Delete old task if exists
schtasks /Delete /TN "%TASK_NAME%" /F 2>nul

REM Create new task with correct path
schtasks /Create /TN "%TASK_NAME%" ^
    /TR "\"%PYTHON_PATH%\" \"%SCRIPT_PATH%\"" ^
    /SC DAILY ^
    /ST 18:00 ^
    /RU "%USERNAME%" ^
    /RL HIGHEST ^
    /F

IF %ERRORLEVEL% EQU 0 (
    echo.
    echo Task registered successfully!
    echo    Open Task Scheduler to verify: taskschd.msc
) ELSE (
    echo.
    echo Registration failed. Make sure you ran as Administrator.
)

echo.
pause
