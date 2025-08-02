@echo off
echo Setting up TempDesk to start automatically on Windows login...

REM Get the current directory where TempDesk.py is located
set "SCRIPT_DIR=%~dp0"
set "PYTHON_PATH=python"
set "SCRIPT_PATH=%SCRIPT_DIR%TempDesk.py"

REM Create a batch file for silent startup
echo Creating silent startup batch file...
(
echo @echo off
echo cd /d "%SCRIPT_DIR%"
echo start "" /min "%PYTHON_PATH%" "%SCRIPT_PATH%"
) > "%SCRIPT_DIR%start_TempDesk_silent.bat"

REM Create the startup folder shortcut pointing to the silent batch file
echo Creating startup shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\TempDesk.lnk'); $Shortcut.TargetPath = '%SCRIPT_DIR%start_TempDesk_silent.bat'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.Description = 'TempDesk - Desktop file management widget'; $Shortcut.Save()"

echo.
echo TempDesk has been added to Windows startup!
echo It will now start automatically when you log in (silently).
echo.
echo To remove it from startup later, delete the shortcut from:
echo %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\
echo.
pause 