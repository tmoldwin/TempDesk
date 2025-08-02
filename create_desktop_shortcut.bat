@echo off
echo Creating TempDesk desktop shortcut...

REM Get the current directory where TempDesk.py is located
set "SCRIPT_DIR=%~dp0"
set "PYTHON_PATH=python"
set "SCRIPT_PATH=%SCRIPT_DIR%TempDesk.py"

REM Create desktop shortcut
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\TempDesk.lnk'); $Shortcut.TargetPath = '%PYTHON_PATH%'; $Shortcut.Arguments = '%SCRIPT_PATH%'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.Description = 'TempDesk - Desktop file management widget'; $Shortcut.IconLocation = '%SCRIPT_DIR%icons\file.png'; $Shortcut.Save()"

echo.
echo TempDesk desktop shortcut created!
echo You can now double-click the shortcut on your desktop to start TempDesk.
echo.
pause 