@echo off
echo Running pre-unlink script for osdagbridge...

set PIP_EXE=%PREFIX%\python.exe -m pip

%PIP_EXE% uninstall -y openseespy opsvis

echo Pre-unlink completed.