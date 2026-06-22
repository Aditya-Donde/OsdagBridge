@echo off
echo Running post-link script for osdagbridge...

set "PIP_EXE=%PREFIX%\python.exe -m pip"

REM Upgrade pip (optional, don't break install)
%PIP_EXE% install --upgrade pip || echo pip upgrade skipped

REM Install pip-only dependencies
%PIP_EXE% install --no-cache-dir "openseespy>=3.2.2.6" opsvis

REM Never fail conda/constructor install because of pip
if errorlevel 1 (
    echo WARNING: Optional pip dependencies failed to install.
    echo Please run manually: pip install openseespy opsvis
    exit /b 0
)

echo Post-link completed.
exit /b 0