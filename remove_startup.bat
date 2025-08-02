@echo off
echo Removing TempDesk from Windows startup...

REM Remove from startup folder
if exist "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\TempDesk.lnk" (
    del "%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\TempDesk.lnk"
    echo Removed startup folder shortcut.
)

REM Remove from registry
reg delete "HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run" /v "TempDesk" /f 2>nul
if %errorlevel% equ 0 (
    echo Removed from Windows Registry.
) else (
    echo No registry entry found to remove.
)

echo.
echo TempDesk has been removed from Windows startup!
echo It will no longer start automatically when you log in.
echo.
pause 