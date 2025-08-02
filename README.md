# TempDrop - Desktop File Widget

TempDrop is a transparent desktop widget for Windows that helps you manage temporary files. Instead of cluttering your desktop with files you need temporarily, TempDrop provides a dedicated space that automatically cleans up old files.

## Features

- **Transparent Widget**: Appears as a semi-transparent window on your desktop
- **Drag & Drop**: Simply drag files into the widget to store them
- **Auto-Cleanup**: Files are automatically deleted after a configurable number of days (default: 7 days)
- **File Management**: Double-click files to open them, or use the delete button to remove them manually
- **Draggable Window**: Move the widget anywhere on your desktop
- **Settings**: Configure auto-deletion period and storage folder
- **Always on Top**: Widget stays visible above other windows

## Installation

1. Install Python 3.7 or higher
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. For full drag-and-drop support, also install:
   ```bash
   pip install tkinterdnd2
   ```

## Usage

1. Run the application:
   ```bash
   python tempdrop.py
   ```

2. The widget will appear on your desktop as a transparent window

3. **Adding Files**:
   - Drag files from your desktop or file explorer into the widget
   - Files are automatically moved to the TempDrop folder

4. **Managing Files**:
   - Double-click any file in the widget to open it
   - Click the trash icon (🗑) next to a file to delete it manually
   - Files are automatically deleted after the configured number of days

5. **Settings**:
   - Click the gear icon (⚙) in the title bar to open settings
   - Configure auto-deletion period (default: 7 days)
   - Change the storage folder location
   - Right-click the widget for additional options

6. **Window Controls**:
   - Drag the title bar to move the widget
   - Click the × button to close the application
   - Right-click for context menu

## Configuration

The application creates a `tempdrop_config.json` file in the same directory to store your settings:
- `auto_delete_days`: Number of days before files are auto-deleted
- `temp_folder`: Path to the folder where files are stored

## File Storage

By default, files are stored in `~/TempDrop` (your user directory). You can change this location in the settings.

## Requirements

- Python 3.7+
- tkinter (usually included with Python)
- watchdog (for file monitoring)
- pillow (for image handling)
- tkinterdnd2 (optional, for enhanced drag-and-drop)

## Troubleshooting

- If drag-and-drop doesn't work, install `tkinterdnd2`
- If the widget doesn't appear transparent, try running as administrator
- Files are stored in the configured folder and can be accessed directly

## Future Enhancements

- Support for other operating systems (macOS, Linux)
- File type filtering
- Custom themes
- System tray integration
- Startup with Windows option 