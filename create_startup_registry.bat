@echo off
echo Setting up TempDrop to start automatically via Windows Registry...

REM Get the current directory where tempdrop.py is located
set "SCRIPT_DIR=%~dp0"
set "PYTHON_PATH=python"
set "SCRIPT_PATH=%SCRIPT_DIR%tempdrop.py"

REM Add to Windows Registry startup
echo Adding to Windows Registry...
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run" /v "TempDrop" /t REG_SZ /d "%PYTHON_PATH% \"%SCRIPT_PATH%\"" /f

echo.
echo TempDrop has been added to Windows Registry startup!
echo It will now start automatically when you log in.
echo.
echo To remove it from startup later, run:
echo reg delete "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run" /v "TempDrop" /f
echo.
pause 