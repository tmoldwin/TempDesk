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
    
    # Create main icon if it doesn't exist
    if not os.path.exists("icons/tempdesk_icon.ico"):
        print("Creating TempDesk icon...")
        subprocess.check_call([sys.executable, "create_icon.py"])
    
    # Build command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name=TempDesk",
        "--add-data=icons;icons",
        "--icon=icons/tempdesk_icon.ico",
        "TempDesk.py"
    ]
    
    print("Running PyInstaller...")
    subprocess.check_call(cmd)
    
    print("\nBuild completed!")
    print("Executable created in: dist/TempDesk.exe")
    print("\nYou can now run TempDesk by double-clicking the executable.")

if __name__ == "__main__":
    main() 