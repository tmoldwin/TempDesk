@echo off
echo Building TempDrop...

REM Check if .NET is installed
dotnet --version >nul 2>&1
if errorlevel 1 (
    echo .NET 6.0 or later is required. Please install it from https://dotnet.microsoft.com/download
    pause
    exit /b 1
)

REM Build the application
dotnet build --configuration Release

if errorlevel 1 (
    echo Build failed!
    pause
    exit /b 1
)

echo Build successful!
echo Running TempDrop...

REM Run the application
dotnet run --configuration Release

pause 