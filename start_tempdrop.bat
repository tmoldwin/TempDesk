@echo off
echo Starting TempDrop...

REM Get the current directory where tempdrop.py is located
set "SCRIPT_DIR=%~dp0"
set "PYTHON_PATH=python"
set "SCRIPT_PATH=%SCRIPT_DIR%tempdrop.py"

REM Change to the script directory and run
cd /d "%SCRIPT_DIR%"
"%PYTHON_PATH%" "%SCRIPT_PATH%"

REM If there was an error, pause so user can see it
if %errorlevel% neq 0 (
    echo.
    echo Error starting TempDrop. Press any key to exit...
    pause
) 