# TempDrop - Cross-Platform Desktop Widget

TempDrop is a cross-platform desktop widget for managing temporary files. It works on Windows, macOS, and Linux, providing a unified experience across all platforms.

## 🌍 **Cross-Platform Support**

- ✅ **Windows** - Full support with native drag-and-drop
- ✅ **macOS** - Full support with file dialog fallback
- ✅ **Linux** - Full support with file dialog fallback

## 🚀 **Features**

- **Transparent Widget**: Semi-transparent window that doesn't stay on top
- **Cross-Platform File Operations**: Works consistently across all platforms
- **Desktop-Style Icons**: Files appear as desktop shortcuts
- **Auto-Cleanup**: Files automatically deleted after configurable days
- **Folder Integration**: Quick access to temp folder
- **Settings Management**: Configure auto-deletion and storage location

## 📦 **Installation**

### Prerequisites
- Python 3.7 or higher
- tkinter (usually included with Python)

### Quick Start
1. **Clone or download** the project
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run the application**:
   ```bash
   python tempdrop_cross_platform.py
   ```

## 🛠 **Building Executables**

### Windows
```bash
# Run the Windows build script
build_cross_platform.bat
```

### macOS/Linux
```bash
# Make the script executable
chmod +x build_cross_platform.sh

# Run the build script
./build_cross_platform.sh
```

### Manual Build
```bash
# Install cx_Freeze
pip install cx_Freeze

# Build for current platform
python setup_cross_platform.py build
```

## 🎯 **Usage**

### Adding Files
- **Windows**: Drag files directly into the widget
- **macOS/Linux**: Click "Add File" button to select files
- **All Platforms**: Files are moved to the TempDrop folder

### Managing Files
- **Double-click** any file icon to open it
- **Right-click** for context menu (Open/Delete)
- **Folder button (📁)** to open the temp folder
- **Settings button (⚙)** to configure options

### Window Controls
- **Drag** anywhere on the window to move it
- **Right-click** for context menu
- **Close button (×)** to exit

## 🔧 **Configuration**

The app creates a `tempdrop_config.json` file with:
- `auto_delete_days`: Days before files are auto-deleted (default: 7)
- `temp_folder`: Path to storage folder (default: `~/TempDrop`)

## 📁 **File Storage**

- **Windows**: `C:\Users\YourName\TempDrop`
- **macOS**: `/Users/YourName/TempDrop`
- **Linux**: `/home/YourName/TempDrop`

## 🌐 **Platform-Specific Features**

### Windows
- Native drag-and-drop support
- Windows-specific file operations
- Full integration with Windows Explorer

### macOS
- Native file dialog integration
- macOS-specific file operations
- Integration with Finder

### Linux
- Native file dialog integration
- Linux-specific file operations
- Integration with file managers

## 🚀 **Windows Store Compatibility**

The app includes Windows Store packaging files:
- `appxmanifest.xml` - Windows Store manifest
- `setup.py` - Windows Store packaging setup

To package for Windows Store:
1. Install Windows App SDK
2. Use the provided manifest file
3. Build with Windows Store tools

## 🔧 **Development**

### Project Structure
```
TempDrop/
├── tempdrop_cross_platform.py    # Main cross-platform app
├── setup_cross_platform.py       # Cross-platform build setup
├── build_cross_platform.bat      # Windows build script
├── build_cross_platform.sh       # macOS/Linux build script
├── requirements.txt              # Dependencies
└── README_CROSS_PLATFORM.md     # This file
```

### Dependencies
- **Core**: `watchdog`, `pillow`
- **Windows**: `pywin32` (optional)
- **Build**: `cx_Freeze`

## 🐛 **Troubleshooting**

### Common Issues

**Drag-and-drop not working on macOS/Linux**
- Use the "Add File" button instead
- Full drag-and-drop requires additional libraries

**Window not visible**
- Check if it's behind other windows
- Look for a small black widget on your desktop

**Permission errors**
- Ensure you have write permissions to the temp folder
- Try running as administrator (Windows)

### Platform-Specific Issues

**Windows**
- If drag-and-drop fails, install `pywin32`
- For transparency issues, run as administrator

**macOS**
- May need to grant accessibility permissions
- File operations use native macOS commands

**Linux**
- May need to install additional packages
- File operations use `xdg-open`

## 📝 **License**

This project is open source. Feel free to modify and distribute.

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test on multiple platforms
5. Submit a pull request

## 📞 **Support**

For issues or questions:
1. Check the troubleshooting section
2. Test on different platforms
3. Create an issue with platform details

---

**TempDrop** - Your cross-platform temporary file manager! 🎉 