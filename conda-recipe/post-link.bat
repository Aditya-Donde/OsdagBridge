@echo off
echo Running post-link script for osdagbridge...

set PIP_EXE=%PREFIX%\python.exe -m pip

REM Install pip-only dependencies
%PIP_EXE% install --no-cache-dir openseespy>=3.2.2.6 opsvis

@REM REM Save installed packages list for cleanup
@REM %PREFIX%\python.exe -m pip freeze > %PREFIX%\conda-meta\osdagbridge-pip.txt

echo Post-link completed.