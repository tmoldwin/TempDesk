#!/usr/bin/env python3
"""
Build script for TempDesk
Creates a standalone executable using PyInstaller.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    """Build the TempDesk executable."""
    print("Building TempDesk executable...")
    
    # Install PyInstaller if not already installed
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Create icons if they don't exist
    if not os.path.exists("icons"):
        print("Creating icons...")
        subprocess.check_call([sys.executable, "create_icons.py"])
    
    # Build command
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name=TempDesk",
        "--add-data=icons;icons",
        "--icon=icons/file.png",
        "TempDesk.py"
    ]
    
    print("Running PyInstaller...")
    subprocess.check_call(cmd)
    
    print("\nBuild completed!")
    print("Executable created in: dist/TempDesk.exe")
    print("\nYou can now run TempDesk by double-clicking the executable.")

if __name__ == "__main__":
    main() 