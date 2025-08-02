@echo off
echo Creating TempDrop desktop shortcut...

REM Get the current directory where tempdrop.py is located
set "SCRIPT_DIR=%~dp0"
set "PYTHON_PATH=python"
set "SCRIPT_PATH=%SCRIPT_DIR%tempdrop.py"

REM Create desktop shortcut
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\TempDrop.lnk'); $Shortcut.TargetPath = '%PYTHON_PATH%'; $Shortcut.Arguments = '%SCRIPT_PATH%'; $Shortcut.WorkingDirectory = '%SCRIPT_DIR%'; $Shortcut.Description = 'TempDrop - Desktop file management widget'; $Shortcut.IconLocation = '%SCRIPT_DIR%icons\file.png'; $Shortcut.Save()"

echo.
echo TempDrop desktop shortcut created!
echo You can now double-click the shortcut on your desktop to start TempDrop.
echo.
pause 