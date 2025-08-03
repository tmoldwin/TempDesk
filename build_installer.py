#!/usr/bin/env python3
"""
Build script for TempDesk executable and installer
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def main():
    """Build TempDesk executable and installer."""
    print("Building TempDesk executable and installer...")
    
    # Step 1: Create the icon
    print("\n1. Creating TempDesk icon...")
    if not os.path.exists("tempdesk_icon.ico"):
        subprocess.check_call([sys.executable, "create_icon.py"])
    else:
        print("   Icon already exists, skipping...")
    
    # Step 2: Build the executable
    print("\n2. Building executable...")
    subprocess.check_call([sys.executable, "build.py"])
    
    # Step 3: Check if NSIS is available for installer
    print("\n3. Building installer...")
    try:
        # Try to find NSIS compiler
        nsis_paths = [
            r"C:\Program Files\NSIS\makensis.exe",
            r"C:\Program Files (x86)\NSIS\makensis.exe",
            "makensis.exe"  # If it's in PATH
        ]
        
        nsis_found = False
        for nsis_path in nsis_paths:
            if os.path.exists(nsis_path):
                print(f"   Found NSIS at: {nsis_path}")
                nsis_found = True
                break
        
        if nsis_found:
            # Build the installer
            subprocess.check_call([nsis_path, "installer.nsi"])
            print("   ✅ Installer created: TempDesk-Setup.exe")
        else:
            print("   ⚠️  NSIS not found. Installer not created.")
            print("   To create installer, install NSIS from: https://nsis.sourceforge.io/Download")
            print("   Then run: makensis installer.nsi")
    
    except Exception as e:
        print(f"   ❌ Error building installer: {e}")
        print("   You can still use the executable directly: dist/TempDesk.exe")
    
    print("\n✅ Build completed!")
    print("\nFiles created:")
    print("   - dist/TempDesk.exe (standalone executable)")
    if os.path.exists("TempDesk-Setup.exe"):
        print("   - TempDesk-Setup.exe (Windows installer)")
    
    print("\nNext steps:")
    print("   1. Test the executable: dist/TempDesk.exe")
    if os.path.exists("TempDesk-Setup.exe"):
        print("   2. Test the installer: TempDesk-Setup.exe")
    print("   3. Distribute the files to users")

if __name__ == "__main__":
    main() 