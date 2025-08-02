@echo off
set VENV_DIR=.venv

IF NOT EXIST "%VENV_DIR%" (
    echo Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

echo Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"

echo Installing dependencies...
pip install -r requirements.txt

echo Starting TempDrop...
python tempdrop.py

echo Deactivating virtual environment...
call "%VENV_DIR%\Scripts\deactivate.bat"

pause
