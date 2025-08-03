@echo off
cd /d "%~dp0"
start "" /min "%~dp0.venv\Scripts\python.exe" "%~dp0TempDesk.py"
