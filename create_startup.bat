@echo off
echo Setting up TempDrop to start automatically on Windows login...

REM Get the current directory where tempdrop.py is located
set "SCRIPT_DIR=%~dp0"
set "PYTHON_PATH=python"
set "SCRIPT_PATH=%SCRIPT_DIR%tempdrop.py"

REM Create the startup folder shortcut
echo Creating startup shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\TempDrop.lnk'); $Shortcut.TargetPath = '%PYTHON_PATH%'; $Shortcut.Arguments = '%SCRIPT_PATH%'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.Description = 'TempDrop - Desktop file management widget'; $Shortcut.Save()"

echo.
echo TempDrop has been added to Windows startup!
echo It will now start automatically when you log in.
echo.
echo To remove it from startup later, delete the shortcut from:
echo %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\
echo.
pause 