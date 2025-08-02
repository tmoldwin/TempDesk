@echo off
echo Building TempDrop executable...
pip install cx_Freeze pywin32
python setup.py build
echo Build complete! Check the build directory for TempDrop.exe
pause 