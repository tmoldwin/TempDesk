@echo off
echo Setting up TempDrop to start automatically via Windows Registry...

REM Get the current directory where tempdrop.py is located
set "SCRIPT_DIR=%~dp0"
set "PYTHON_PATH=python"
set "SCRIPT_PATH=%SCRIPT_DIR%tempdrop.py"

REM Create a batch file for silent startup
echo Creating silent startup batch file...
(
echo @echo off
echo cd /d "%SCRIPT_DIR%"
echo start "" /min "%PYTHON_PATH%" "%SCRIPT_PATH%"
) > "%SCRIPT_DIR%start_tempdrop_silent.bat"

REM Add to Windows Registry startup pointing to the silent batch file
echo Adding to Windows Registry...
reg add "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run" /v "TempDrop" /t REG_SZ /d "%SCRIPT_DIR%start_tempdrop_silent.bat" /f

echo.
echo TempDrop has been added to Windows Registry startup!
echo It will now start automatically when you log in (silently).
echo.
echo To remove it from startup later, run:
echo reg delete "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run" /v "TempDrop" /f
echo.
pause 