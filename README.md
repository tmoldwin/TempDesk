# TempDesk Desktop Widget

## What is TempDesk?

TempDesk is a Windows desktop widget that solves a common problem: you have files you need temporarily but want easy access to, so you put them on your desktop. But then they stay there forever, creating clutter.

TempDesk gives you a transparent window on your desktop where you can store these temporary files. They automatically get hidden from view after a configurable time period, keeping your desktop clean while preserving your files.

## Features

- **Transparent Desktop Widget**: Semi-transparent window that stays on your desktop
- **Drag & Drop Support**: Simply drag files into the widget to add them
- **Windows-Only**: Currently optimized for Windows with native desktop integration
- **Smart Filtering**: Files automatically hidden from view after configurable time (default: 1 day)
- **File Icons**: Files display with appropriate icons based on type
- **Context Menus**: Right-click files for open, delete, and properties
- **Settings**: Configure filtering time and storage location
- **File Watcher**: Automatically detects files added to the TempDesk folder
- **System Tray**: Minimize to system tray and toggle visibility
- **Resizable**: Drag edges to resize the widget
- **Movable**: Drag the title bar to move the widget around

## Quick Start

### Windows

1. **Download and extract** the project
2. **Double-click `run.bat`** to start TempDesk
3. **Drag files** into the transparent widget on your desktop
4. **Configure settings** by clicking the gear icon (⚙)

### Manual Installation

1. **Install Python 3.7+** from [python.org](https://python.org)
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application**:
   ```bash
   python TempDesk.py
   ```

### Build Executable and Installer

To create a standalone executable and Windows installer:

```bash
# Build everything (recommended)
python build_installer.py

# Or build just the executable
python build.py

# Or use the batch file
build_all.bat
```

The files will be created in:
- `dist/TempDesk.exe` - Standalone executable
- `TempDesk-Setup.exe` - Windows installer (if NSIS is installed)

**Note:** To create the installer, you need NSIS installed. Download from: https://nsis.sourceforge.io/Download

## How It Works

### The Widget
- A semi-transparent window appears on your desktop
- It stays behind other windows - only visible when you're on the desktop
- You can drag it anywhere on your desktop using the title bar
- You can resize it by dragging the edges
- It doesn't appear in your taskbar or Alt-Tab list - it's just part of your desktop
- System tray icon allows you to show/hide the widget

### Adding Files
- **Drag and Drop**: Simply drag any file from your computer into the TempDesk window
- **Auto-Detection**: If you save files directly to the TempDesk folder, they automatically appear in the widget

### File Display
Files appear as desktop shortcuts/icons (not a boring file list):
- Each file shows with its proper icon (PDFs look like PDFs, images look like images, etc.)
- Files are arranged in a grid like desktop shortcuts
- You can see file names clearly
- Right-click any file for options (open, delete, properties)

### Managing Files
- **Open**: Double-click any file to open it with its default program
- **Delete**: Right-click and select "Delete" or use the trash icon
- **Properties**: Right-click to see file details
- **Smart Filtering**: Files automatically hidden from view after the number of days you set (default: 1 day)
- **Keyboard Shortcuts**: Ctrl+C (copy), Ctrl+X (cut), Ctrl+V (paste), Delete, F2 (rename)

### Widget Controls
- **Move**: Drag the title bar to move it around
- **Resize**: Drag the edges to resize the widget
- **Close**: Click the X button to close the widget
- **Settings**: Click the gear icon (⚙) to change filtering time, storage folder, etc.
- **System Tray**: Right-click the tray icon to show/hide or quit

### Settings
- **Filtering Time**: Set how many days before files are hidden from view (1 minute to 1 month)
- **Auto-Delete**: Optional setting to permanently delete files after the time period
- **Storage Location**: Files are stored in `C:\Users\YourName\TempDesk` (can be changed via folder picker)

## User Experience Flow

1. **Start**: Run TempDesk - a transparent window appears on your desktop
2. **Add Files**: Drag files into the window or save them to the TempDesk folder
3. **See Files**: Files appear as desktop-style icons in the widget
4. **Use Files**: Double-click to open, right-click for more options
5. **Smart Filtering**: Files automatically disappear from view after your set time period
6. **Configure**: Use settings to adjust behavior to your preferences

## What Makes It Special

- **Desktop Widget**: It's not a regular app - it's part of your desktop
- **Visual**: Files look like desktop shortcuts, not a boring list
- **Smart**: Files are filtered/hidden rather than deleted, so you can recover them if needed
- **Flexible**: Move it, resize it, configure it however you want
- **Non-Intrusive**: Semi-transparent so it doesn't block your desktop
- **Windows-Native**: Uses Windows APIs for true desktop integration

## Common Use Cases

- **Downloads**: Drag downloaded files here instead of leaving them on desktop
- **Screenshots**: Save screenshots here for temporary reference
- **Documents**: Store work-in-progress files that you'll delete later
- **Media**: Keep temporary images, videos, or audio files
- **Backups**: Store files you're about to delete but want to keep briefly

## Technical Details

### Technology Stack
- **Python 3.7+**: Core language
- **PyQt6**: Modern GUI framework with excellent drag-drop support
- **pywin32**: Windows-specific features for desktop integration
- **psutil**: System monitoring

### Windows Integration
- **Desktop Parenting**: Uses Windows APIs to attach to the desktop
- **Native Drag-Drop**: Full Windows drag-drop support
- **System Tray**: Native Windows system tray integration
- **File Operations**: Native Windows file operations

### File Storage
- **Location**: `C:\Users\YourName\TempDesk` (configurable via settings)
- **Hidden Files**: Old files are moved to `[folder]\old` folder
- **Configuration**: Settings stored in `C:\Users\YourName\.TempDesk_config.json`

## Getting Started

1. Download and install TempDesk
2. The widget appears on your desktop automatically
3. Start dragging files into it
4. Configure settings to your preference
5. Enjoy a cleaner desktop!

That's it - TempDesk works in the background, keeping your desktop organized without you having to think about it. 