@echo off
REM Auto-Sync Script für TouchDesigner (Batch-Version)
REM Läuft im Hintergrund und holt automatisch neue Änderungen

set BRANCH=claude/debug-dmx-conversion-011CUSwRp8ggwNj6TPricrUc
set INTERVAL=5

echo === TouchDesigner Auto-Sync gestartet ===
echo Branch: %BRANCH%
echo Prueft alle %INTERVAL% Sekunden auf Aenderungen...
echo Druecke Ctrl+C zum Beenden
echo.

:loop
    REM Fetch neueste Commits
    git fetch origin %BRANCH% >nul 2>&1

    REM Prüfe auf Updates
    for /f %%i in ('git rev-parse HEAD') do set LOCAL=%%i
    for /f %%i in ('git rev-parse origin/%BRANCH%') do set REMOTE=%%i

    if not "%LOCAL%"=="%REMOTE%" (
        echo [%TIME%] Neue Aenderungen gefunden! Synchronisiere...
        git pull origin %BRANCH%
        echo [%TIME%] Synchronisiert! Bitte TouchDesigner neu laden.
        echo.
    )

    REM Warte
    timeout /t %INTERVAL% /nobreak >nul

goto loop
