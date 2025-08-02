# TempDesk - Desktop Widget

## What is TempDesk?

TempDesk is a desktop widget that solves a common problem: you have files you need temporarily but want easy access to, so you put them on your desktop. But then they stay there forever, creating clutter.

TempDesk gives you a transparent window on your desktop where you can store these temporary files. They automatically get deleted after a few days, keeping your desktop clean.

## Features

- **Transparent Desktop Widget**: Semi-transparent window that stays on your desktop
- **Drag & Drop Support**: Simply drag files into the widget to add them
- **Cross-Platform**: Works on Windows, macOS, and Linux
- **Auto-Cleanup**: Files automatically deleted after configurable days (default: 7 days)
- **File Icons**: Files display with appropriate icons based on type
- **Context Menus**: Right-click files for open, delete, and properties
- **Settings**: Configure auto-deletion time and storage location
- **File Watcher**: Automatically detects files added to the temp folder

## Quick Start

### Windows (Recommended)

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
3. **Create icons**:
   ```bash
   python create_icons.py
   ```
4. **Run the application**:
   ```bash
   python TempDesk.py
   ```

### Build Executable

To create a standalone executable:

```bash
# Windows
build.bat

# Or manually
python build.py
```

The executable will be created in the `dist/` folder.

## How It Works

### The Widget
- A semi-transparent window appears on your desktop
- It stays behind other windows - only visible when you're on the desktop
- You can drag it anywhere on your desktop
- You can resize it to fit more or fewer files
- It doesn't appear in your taskbar or Alt-Tab list - it's just part of your desktop

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
- **Auto-Cleanup**: Files automatically disappear after the number of days you set (default: 7 days)

### Widget Controls
- **Move**: Drag anywhere on the window to move it around
- **Close**: Click the X button to close the widget
- **Settings**: Click the gear icon (⚙) to change auto-deletion time, storage folder, etc.
- **Open Folder**: Click the folder icon (📁) to open the TempDesk storage folder directly

### Settings
- **Auto-deletion**: Set how many days before files are automatically deleted (1-30 days)
- **Storage Location**: Choose where files are stored (default: your Documents folder)

## User Experience Flow

1. **Start**: Run TempDesk - a transparent window appears on your desktop
2. **Add Files**: Drag files into the window or save them to the TempDesk folder
3. **See Files**: Files appear as desktop-style icons in the widget
4. **Use Files**: Double-click to open, right-click for more options
5. **Auto-Cleanup**: Files automatically disappear after your set time period
6. **Configure**: Use settings to adjust behavior to your preferences

## What Makes It Special

- **Desktop Widget**: It's not a regular app - it's part of your desktop
- **Visual**: Files look like desktop shortcuts, not a boring list
- **Automatic**: Set it and forget it - files clean themselves up
- **Flexible**: Move it, resize it, configure it however you want
- **Non-Intrusive**: Semi-transparent so it doesn't block your desktop
- **Cross-Platform**: Works consistently across Windows, macOS, and Linux

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
- **watchdog**: File system monitoring
- **Pillow**: Image processing for icons
- **pywin32**: Windows-specific features (Windows only)

### Cross-Platform Support
- **Windows**: Full native drag-drop support
- **macOS**: Full support with file dialog fallback
- **Linux**: Full support with file dialog fallback

### File Storage
- **Windows**: `C:\Users\YourName\TempDesk`
- **macOS**: `/Users/YourName/TempDesk`
- **Linux**: `/home/YourName/TempDesk`

## Getting Started

1. Download and install TempDesk
2. The widget appears on your desktop automatically
3. Start dragging files into it
4. Configure settings to your preference
5. Enjoy a cleaner desktop!

That's it - TempDesk works in the background, keeping your desktop organized without you having to think about it. 