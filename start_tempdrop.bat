@echo off
REM Get the current directory where tempdrop.py is located
set "SCRIPT_DIR=%~dp0"
set "PYTHON_PATH=python"
set "SCRIPT_PATH=%SCRIPT_DIR%tempdrop.py"

REM Change to the script directory and run without showing console window
cd /d "%SCRIPT_DIR%"
start "" /min "%PYTHON_PATH%" "%SCRIPT_PATH%" 