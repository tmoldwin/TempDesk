#!/usr/bin/env python3
"""
TempDesk - A true desktop file explorer widget with system tray integration.
"""

import sys
import os
import json
import shutil
import subprocess
import re
from pathlib import Path
from urllib.parse import urlparse

# Windows-specific imports are required for desktop parenting and tray icon
import win32gui
import win32con

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListView, QAbstractItemView, QMenu, QMessageBox,
    QFileIconProvider, QSystemTrayIcon, QStyle, QInputDialog
)
from PyQt6.QtCore import (
    Qt, QSize, QPoint, QRect, QFileSystemWatcher, QSortFilterProxyModel, QTimer, QDir
)
from PyQt6.QtGui import (
    QFileSystemModel, QIcon, QAction, QMouseEvent, QKeyEvent, QKeySequence
)
from PyQt6.QtCore import QUrl

class ResizableFramelessWindow(QMainWindow):
    """
    A base class for a frameless window that can be resized by dragging its
    edges and corners, and moved by dragging the title bar.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.drag_position = None
        self.resizing = False
        self.resize_edge = None
        self.resize_margin = 8
        # This will be set by the child class
        self.title_bar = None

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            # Check if the press is on the title bar for dragging
            if self.title_bar and self.title_bar.geometry().contains(pos):
                 self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            # Check if the press is on an edge for resizing
            elif self.is_on_edge(pos):
                self.resizing = True
                self.resize_edge = self.get_edge(pos)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position().toPoint()
        if self.resizing:
            self.resize_window(event.globalPosition().toPoint())
        elif self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.drag_position = None
        self.resizing = False
        super().mouseReleaseEvent(event)

    def is_on_edge(self, pos: QPoint) -> bool:
        return any(self.get_edge(pos))

    def get_edge(self, pos: QPoint) -> tuple:
        return (
            pos.x() < self.resize_margin,
            pos.y() < self.resize_margin,
            pos.x() > self.width() - self.resize_margin,
            pos.y() > self.height() - self.resize_margin
        )



    def resize_window(self, global_pos: QPoint):
        rect = self.geometry()
        left, top, right, bottom = self.resize_edge

        if left: rect.setLeft(global_pos.x())
        if top: rect.setTop(global_pos.y())
        if right: rect.setRight(global_pos.x())
        if bottom: rect.setBottom(global_pos.y())
        
        # Enforce minimum size
        if rect.width() < self.minimumWidth(): rect.setWidth(self.minimumWidth())
        if rect.height() < self.minimumHeight(): rect.setHeight(self.minimumHeight())

        self.setGeometry(rect)


class DesktopWidget(ResizableFramelessWindow):
    """
    The main file explorer widget, inheriting resizability and providing
    all application functionality.
    """
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.TempDesk_folder = self.get_TempDesk_folder()
        self.is_dragging = False

        os.makedirs(self.TempDesk_folder, exist_ok=True)
        
        # Drag and drop is handled by the view, not the main window
        # self.setAcceptDrops(True)
        self.setup_ui()
        self.setup_window_properties()
        self.setup_file_system_model()
        self.pin_to_desktop()
        
    def get_TempDesk_folder(self) -> str:
        # Check if custom folder is set in config
        if hasattr(self, 'config') and self.config and self.config.get('tempdesk_folder'):
            return self.config['tempdesk_folder']
        return str(Path.home() / 'TempDesk')
    
    def load_config(self) -> dict:
        config_path = Path.home() / '.TempDesk_config.json'
        old_config_path = Path.home() / '.tempdrop_config.json'
        default_config = {
            'filter_period': 86400,  # 1 day in seconds
            'auto_delete': False,
            'window_geometry': None,
            'tempdesk_folder': None  # Will use default if None
        }
        
        # Try to load from new config file first
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    for key, value in default_config.items():
                        if key not in loaded_config:
                            loaded_config[key] = value
                    return loaded_config
            except json.JSONDecodeError:
                pass
        
        # If new config doesn't exist, try to migrate from old config
        if old_config_path.exists():
            try:
                with open(old_config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    for key, value in default_config.items():
                        if key not in loaded_config:
                            loaded_config[key] = value
                    
                    # Save to new config file
                    try:
                        with open(config_path, 'w') as f:
                            json.dump(loaded_config, f, indent=2)
                        print(f"Migrated config from {old_config_path} to {config_path}")
                    except Exception as e:
                        print(f"Warning: Could not save migrated config: {e}")
                    
                    return loaded_config
            except json.JSONDecodeError:
                pass
        
        return default_config
    
    def save_config(self):
        config_path = Path.home() / '.TempDesk_config.json'
        config = {
            'window_geometry': self.saveGeometry().data().hex(),
            'filter_period': self.config.get('filter_period', 86400),
            'auto_delete': self.config.get('auto_delete', False),
            'tempdesk_folder': self.config.get('tempdesk_folder', None)
        }
        try:
            with open(config_path, 'w') as f: json.dump(config, f, indent=2)
        except Exception as e: print(f"Error saving config: {e}")
    
    def setup_ui(self):
        self.setWindowTitle("TempDesk")
        self.setMinimumSize(300, 200)
        
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Create and assign the title bar
        self.title_bar = self.create_title_bar()
        self.main_layout.addWidget(self.title_bar)
        
        self.view = QListView()
        # Allow both dragging items OUT and dropping items IN
        self.view.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.view.setFlow(QListView.Flow.LeftToRight)
        self.view.setWrapping(True)
        self.view.setResizeMode(QListView.ResizeMode.Adjust)
        self.view.setMovement(QListView.Movement.Snap)
        self.view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.view.setViewMode(QListView.ViewMode.IconMode)
        self.view.setIconSize(QSize(64, 64))
        self.view.setGridSize(QSize(84, 84))
        self.view.setWordWrap(True)
        
        self.view.doubleClicked.connect(self.open_item)
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self.show_context_menu)
        
        # Enable drag and drop on the view
        self.view.setAcceptDrops(True)
        self.view.dragEnterEvent = self.view_drag_enter_event
        self.view.dragMoveEvent = self.view_drag_move_event
        self.view.dragLeaveEvent = self.view_drag_leave_event
        self.view.dropEvent = self.view_drop_event
        
        # Enable keyboard shortcuts
        self.view.keyPressEvent = self.view_key_press_event
        
        self.view.setObjectName("fileView")
        self.update_stylesheet()
        self.main_layout.addWidget(self.view)

    def create_title_bar(self) -> QWidget:
        title_bar = QWidget()
        title_bar.setFixedHeight(32)
        title_bar.setStyleSheet("""
            background-color: #333;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        """)
        
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 5, 0)
        
        title_label = QLabel("📁 TempDesk")
        title_label.setStyleSheet("color: white; font-weight: bold;")
        
        settings_btn = QPushButton("⚙️")
        settings_btn.setFixedSize(28, 28)
        settings_btn.clicked.connect(self.show_settings_dialog)
        settings_btn.setStyleSheet("QPushButton { border: none; color: white; font-size: 16px; } QPushButton:hover { background-color: #555; }")

        close_btn = QPushButton("×")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("QPushButton { border: none; color: white; font-size: 20px; } QPushButton:hover { background-color: #E81123; }")

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(settings_btn)
        title_layout.addWidget(close_btn)
        
        return title_bar

    def setup_window_properties(self):
        if 'window_geometry' in self.config and self.config['window_geometry'] is not None:
            try:
                self.restoreGeometry(bytes.fromhex(self.config['window_geometry']))
            except (ValueError, TypeError):
                # If geometry restoration fails, use default position
                screen = QApplication.primaryScreen().geometry()
                self.resize(500, 350)
                self.move(screen.width() - self.width() - 20, 40)
        else:
            screen = QApplication.primaryScreen().geometry()
            self.resize(500, 350)
            self.move(screen.width() - self.width() - 20, 40)
        
        # Set window to stay on top of desktop but below other applications
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
    
    def setup_file_system_model(self):
        self.model = QFileSystemModel()
        self.model.setRootPath(self.TempDesk_folder)
        self.model.iconProvider().setOptions(QFileIconProvider.Option.DontUseCustomDirectoryIcons)
        
        # Filter to only show files (not directories like "old")
        self.model.setFilter(QDir.Filter.Files | QDir.Filter.NoDotAndDotDot)
        
        print(f"[MODEL DEBUG] Model root path set to: {self.model.rootPath()}")
        print(f"[MODEL DEBUG] TempDesk folder: {self.TempDesk_folder}")
        
        self.view.setModel(self.model)
        self.view.setRootIndex(self.model.index(self.TempDesk_folder))
        
        print(f"[MODEL DEBUG] Using basic model with files-only filter")
        
        self.watcher = QFileSystemWatcher([self.TempDesk_folder])
        self.watcher.directoryChanged.connect(self.directory_changed)
        
        # Setup auto-cleanup timer
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.auto_cleanup)
        self.cleanup_timer.start(60000)  # Check every minute
        
        # Setup periodic refresh timer to ensure view stays updated
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.periodic_refresh)
        self.refresh_timer.start(60000)  # Refresh every minute
        
        # Apply initial filter after setup
        self.apply_file_filter()
    
    def pin_to_desktop(self):
        """Uses win32gui to set the parent of this window to the desktop."""
        try:
            # Find the Program Manager window
            progman = win32gui.FindWindow("Progman", None)
            if not progman:
                print("Warning: Could not find Progman window")
                return
                
            # Send message to make desktop visible
            win32gui.SendMessage(progman, 0x052C, 0, 0)
            
            # Find the WorkerW window that contains the desktop
            def enum_windows_callback(hwnd, windows):
                if win32gui.IsWindowVisible(hwnd):
                    class_name = win32gui.GetClassName(hwnd)
                    if class_name == "WorkerW":
                        # Check if this WorkerW has a child window
                        child = win32gui.FindWindowEx(hwnd, None, "SHELLDLL_DefView", None)
                        if child:
                            windows.append(hwnd)
                return True
            
            worker_windows = []
            win32gui.EnumWindows(enum_windows_callback, worker_windows)
            
            if worker_windows:
                desktop_workerw = worker_windows[0]
                # Set the window to be a child of the desktop
                window_handle = int(self.winId())
                win32gui.SetParent(window_handle, desktop_workerw)
                # Set window to be always on bottom
                win32gui.SetWindowPos(window_handle, win32con.HWND_BOTTOM, 0, 0, 0, 0, 
                                    win32con.SWP_NOMOVE | win32con.SWP_NOSIZE | win32con.SWP_NOACTIVATE)
            else:
                print("Warning: Could not find desktop WorkerW window")
        except Exception as e:
            print(f"Warning: Could not pin to desktop: {e}")
            # Continue without pinning to desktop

    def directory_changed(self):
        self.model.setRootPath(""); self.model.setRootPath(self.TempDesk_folder)
        self.view.setRootIndex(self.model.index(self.TempDesk_folder))
        print(f"[DIRECTORY] Directory changed, refreshed view")
    
    def periodic_refresh(self):
        """Periodic refresh to ensure view stays accurate."""
        print("🔄 PERIODIC REFRESH: Updating view and reapplying filter")
        
        # Force refresh the file system model
        self.model.setRootPath("")
        self.model.setRootPath(self.TempDesk_folder)
        self.view.setRootIndex(self.model.index(self.TempDesk_folder))
        
        # Reapply the filter to make sure everything is correct
        self.apply_file_filter()
        
        print("✅ PERIODIC REFRESH: Complete")
        
    def apply_file_filter(self):
        """Apply file filter by temporarily hiding old files from the folder."""
        import time
        import os
        
        filter_period = self.config.get('filter_period', 86400)  # Default 1 day
        current_time = time.time()
        
        print(f"\n🔍 APPLYING WORKING FILTER")
        print(f"[LOG] TempDesk folder: {self.TempDesk_folder}")
        print(f"[LOG] Filter period: {filter_period}s")
        print(f"[LOG] Current time: {current_time}")
        
        # Create a folder for old files (excluded from view)
        hidden_folder = os.path.join(self.TempDesk_folder, 'old')
        os.makedirs(hidden_folder, exist_ok=True)
        
        # Move old files to hidden folder, bring back recent files
        try:
            files_in_folder = os.listdir(self.TempDesk_folder)
            files_to_process = [f for f in files_in_folder if not f.startswith('.') and f != 'old']
            
            print(f"[FILTER] Processing {len(files_to_process)} files...")
            
            for file in files_to_process:
                file_path = os.path.join(self.TempDesk_folder, file)
                hidden_path = os.path.join(hidden_folder, file)
                
                if os.path.isfile(file_path):
                    # Get file creation time in this folder (when it was added to TempDesk)
                    # Note: os.path.getctime() returns when file was created in this location,
                    # which is when it was dragged/copied/moved here
                    ctime = os.path.getctime(file_path)
                    age = current_time - ctime  # Age in seconds since added to TempDesk
                    should_show = age <= filter_period
                    
                    if should_show:
                        # File should be visible - make sure it's in main folder
                        if not os.path.exists(file_path) and os.path.exists(hidden_path):
                            os.rename(hidden_path, file_path)
                            print(f"[FILTER] ✓ RESTORED: {file} (age: {age:.1f}s)")
                        else:
                            print(f"[FILTER] ✓ VISIBLE: {file} (age: {age:.1f}s)")
                    else:
                        # File should be hidden - move to hidden folder
                        if os.path.exists(file_path):
                            # Handle duplicates in hidden folder
                            counter = 1
                            final_hidden_path = hidden_path
                            base_name, ext = os.path.splitext(file)
                            while os.path.exists(final_hidden_path):
                                new_name = f"{base_name}_{counter}{ext}"
                                final_hidden_path = os.path.join(hidden_folder, new_name)
                                counter += 1
                            
                            os.rename(file_path, final_hidden_path)
                            print(f"[FILTER] ✗ HIDDEN: {file} (age: {age:.1f}s)")
            
            # Also check hidden folder for files that should now be visible
            if os.path.exists(hidden_folder):
                hidden_files = os.listdir(hidden_folder)
                for hidden_file in hidden_files:
                    hidden_file_path = os.path.join(hidden_folder, hidden_file)
                    if os.path.isfile(hidden_file_path):
                        ctime = os.path.getctime(hidden_file_path)
                        age = current_time - ctime
                        should_show = age <= filter_period
                        
                        if should_show:
                            # Move back to main folder
                            main_file_path = os.path.join(self.TempDesk_folder, hidden_file)
                            if not os.path.exists(main_file_path):
                                os.rename(hidden_file_path, main_file_path)
                                print(f"[FILTER] ✓ RESTORED: {hidden_file} (age: {age:.1f}s)")
                        
        except Exception as e:
            print(f"[FILTER] Error applying filter: {e}")
        
        # Refresh the view to show changes
        self.model.setRootPath("")
        self.model.setRootPath(self.TempDesk_folder)
        
        # Show what's actually visible now
        self.debug_visible_items()
        print(f"🔍 FILTER APPLICATION COMPLETE\n")
    
    def debug_visible_items(self):
        """Debug function to show what items are actually visible in the view."""
        try:
            import os
            
            # Get root index for counting
            root_index = self.view.rootIndex()
            visible_count = self.model.rowCount(root_index)
            
            print(f"📋 VISIBLE ITEMS IN VIEW: {visible_count}")
            
            if visible_count == 0:
                print("   (No items visible)")
            else:
                for row in range(visible_count):
                    item_index = self.model.index(row, 0, root_index)
                    file_path = self.model.filePath(item_index)
                    file_name = os.path.basename(file_path)
                    print(f"   {row + 1}. {file_name}")
                
        except Exception as e:
            print(f"[VIEW DEBUG] Error checking visible items: {e}")
    
    def open_item(self, index):
        try: 
            os.startfile(self.model.filePath(index))
        except Exception as e: QMessageBox.warning(self, "Error", f"Could not open item:\n{e}")
            
    def show_context_menu(self, position):
        indexes = self.view.selectedIndexes()
        
        menu = QMenu()
        
        if indexes:
            # File-specific actions
            menu.addAction("Open", lambda: self.open_item(indexes[0]))
            menu.addAction("Open with...", lambda: self.open_with_dialog(indexes[0]))
            menu.addSeparator()
            menu.addAction("Cut", lambda: self.cut_items(indexes))
            menu.addAction("Copy", lambda: self.copy_items(indexes))
            menu.addAction("Delete", lambda: self.delete_items(indexes))
            menu.addSeparator()
            menu.addAction("Rename", lambda: self.rename_item(indexes[0]))
            menu.addAction("Properties", lambda: self.show_properties(indexes[0]))
        else:
            # Empty area actions
            menu.addAction("Paste", self.paste_items)
            menu.addSeparator()
            menu.addAction("Select All", self.select_all)
        
        menu.addSeparator()
        menu.addAction("Show in Explorer", self.show_in_explorer)
        menu.addAction("Refresh", self.refresh_view)
        menu.addAction("Settings", self.show_settings_dialog)
        
        menu.exec(self.view.viewport().mapToGlobal(position))

    def delete_items(self, indexes):
        paths = [self.model.filePath(i) for i in indexes]
        reply = QMessageBox.question(self, "Confirm Delete", f"Permanently delete {len(paths)} item(s)?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            for path in paths:
                try:
                    if os.path.isfile(path): os.remove(path)
                    elif os.path.isdir(path): shutil.rmtree(path)
                except Exception as e: QMessageBox.warning(self, "Error", f"Could not delete '{path}':\n{e}")
            
            # Notify Windows that files were deleted
            try:
                import ctypes
                SHCNE_DELETE = 0x00000002
                SHCNF_PATH = 0x0001
                for path in paths:
                    ctypes.windll.shell32.SHChangeNotifyW(SHCNE_DELETE, SHCNF_PATH, path, None)
            except:
                pass  # If Windows API call fails, continue anyway
            
            # Refresh the file system model to show changes immediately
            self.model.setRootPath("")
            self.model.setRootPath(self.TempDesk_folder)

    def show_in_explorer(self):
        print(f"[DEBUG] Attempting to open folder: {self.TempDesk_folder}")
        try:
            # Use os.startfile which is more reliable for opening folders on Windows
            os.startfile(self.TempDesk_folder)
            print(f"[DEBUG] Successfully opened folder using os.startfile")
        except Exception as e:
            print(f"[DEBUG] os.startfile failed: {e}")
            # Fallback to subprocess if os.startfile fails
            try:
                subprocess.Popen(['explorer', self.TempDesk_folder], shell=False)
                print(f"[DEBUG] Successfully opened folder using subprocess")
            except Exception as e2:
                print(f"[DEBUG] subprocess failed: {e2}")
                # Final fallback with shell=True
                try:
                    subprocess.Popen(f'explorer "{self.TempDesk_folder}"', shell=True)
                    print(f"[DEBUG] Successfully opened folder using shell=True")
                except Exception as e3:
                    print(f"[DEBUG] All methods failed: {e3}")
                    QMessageBox.warning(self, "Error", f"Could not open folder:\n{self.TempDesk_folder}\n\nError: {e3}")
        
    def show_settings_dialog(self):
        """Show the settings dialog with filtering and deletion options."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QCheckBox, QPushButton, QGroupBox, QFileDialog
        
        dialog = QDialog(self)
        dialog.setWindowTitle("TempDesk Settings")
        dialog.setFixedSize(450, 350)
        
        layout = QVBoxLayout(dialog)
        
        # Folder section
        folder_group = QGroupBox("Storage Location")
        folder_layout = QVBoxLayout(folder_group)
        folder_label = QLabel(f"Current TempDesk Folder: {self.TempDesk_folder}")
        folder_label.setWordWrap(True)
        folder_layout.addWidget(folder_label)
        
        folder_buttons = QHBoxLayout()
        change_folder_btn = QPushButton("Change Folder...")
        change_folder_btn.clicked.connect(lambda: self.change_tempdesk_folder(dialog))
        folder_buttons.addWidget(change_folder_btn)
        
        open_folder_btn = QPushButton("Open Folder")
        open_folder_btn.clicked.connect(self.show_in_explorer)
        folder_buttons.addWidget(open_folder_btn)
        folder_layout.addLayout(folder_buttons)
        layout.addWidget(folder_group)
        
        # Filtering section
        filter_group = QGroupBox("File Filtering")
        filter_layout = QVBoxLayout(filter_group)
        
        filter_label = QLabel("Show files added to TempDesk within:")
        filter_layout.addWidget(filter_label)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItem("1 minute (for testing)", 60)
        self.filter_combo.addItem("1 day", 86400)
        self.filter_combo.addItem("1 week", 604800)
        self.filter_combo.addItem("1 month", 2592000)
        
        # Set current value
        current_period = self.config.get('filter_period', 86400)
        for i in range(self.filter_combo.count()):
            if self.filter_combo.itemData(i) == current_period:
                self.filter_combo.setCurrentIndex(i)
                break
        
        self.filter_combo.currentIndexChanged.connect(self.on_filter_changed)
        filter_layout.addWidget(self.filter_combo)
        layout.addWidget(filter_group)
        
        # Auto-delete section
        delete_group = QGroupBox("Auto-Cleanup")
        delete_layout = QVBoxLayout(delete_group)
        
        self.auto_delete_checkbox = QCheckBox("Also delete files after they've been in TempDesk for this period")
        self.auto_delete_checkbox.setChecked(self.config.get('auto_delete', False))
        self.auto_delete_checkbox.stateChanged.connect(self.on_auto_delete_changed)
        delete_layout.addWidget(self.auto_delete_checkbox)
        
        delete_warning = QLabel("⚠️ Warning: This will permanently delete files!")
        delete_warning.setStyleSheet("color: red;")
        delete_layout.addWidget(delete_warning)
        layout.addWidget(delete_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        clear_btn = QPushButton("Clear All Items...")
        clear_btn.clicked.connect(self.clear_TempDesk_folder)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        dialog.exec()
        
    def on_filter_changed(self):
        """Handle filter period change."""
        old_period = self.config.get('filter_period', 86400)
        new_period = self.filter_combo.currentData()
        
        print(f"\n🔄 FILTER SETTING CHANGED!")
        print(f"   Old period: {old_period}s")
        print(f"   New period: {new_period}s")
        print(f"   Change: {old_period} → {new_period}")
        
        self.config['filter_period'] = new_period
        self.save_config()
        
        print(f"   Config saved, applying filter...")
        self.apply_file_filter()
        print(f"   Filter change complete!\n")
        
    def on_auto_delete_changed(self):
        """Handle auto-delete checkbox change."""
        self.config['auto_delete'] = self.auto_delete_checkbox.isChecked()
        self.save_config()
        
    def change_tempdesk_folder(self, dialog):
        """Change the TempDesk folder location."""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        
        new_folder = QFileDialog.getExistingDirectory(
            self, 
            "Select TempDesk Folder", 
            self.TempDesk_folder,
            QFileDialog.Option.ShowDirsOnly
        )
        
        if new_folder:
            try:
                # Create the new folder if it doesn't exist
                os.makedirs(new_folder, exist_ok=True)
                
                # Update the folder path
                old_folder = self.TempDesk_folder
                self.TempDesk_folder = new_folder
                
                # Update the model to use the new folder
                self.model.setRootPath(self.TempDesk_folder)
                self.view.setRootIndex(self.model.index(self.TempDesk_folder))
                
                # Update the file watcher
                self.watcher.removePath(old_folder)
                self.watcher.addPath(self.TempDesk_folder)
                
                # Save the new folder path to config
                self.config['tempdesk_folder'] = self.TempDesk_folder
                self.save_config()
                
                # Show success message
                QMessageBox.information(
                    self, 
                    "Folder Changed", 
                    f"TempDesk folder changed to:\n{self.TempDesk_folder}\n\nFiles will now be stored in this new location."
                )
                
                # Close the settings dialog
                dialog.accept()
                
            except Exception as e:
                QMessageBox.warning(
                    self, 
                    "Error", 
                    f"Could not change folder:\n{e}"
                )
    
    def clear_TempDesk_folder(self):
        reply = QMessageBox.warning(self, "Confirm Clear", "Permanently delete ALL items in TempDesk?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel)
        if reply == QMessageBox.StandardButton.Yes:
            for item in os.listdir(self.TempDesk_folder):
                try:
                    item_path = os.path.join(self.TempDesk_folder, item)
                    if os.path.isfile(item_path): os.unlink(item_path)
                    elif os.path.isdir(item_path): shutil.rmtree(item_path)
                except Exception as e: print(f"Failed to delete {item_path}: {e}")

    def update_stylesheet(self):
        border_color = "#0078D7" if self.is_dragging else "#888"
        self.view.setStyleSheet(f"QListView#fileView {{ background-color: rgba(240, 240, 240, 0.85); border-radius: 0px 0px 8px 8px; border: 2px solid {border_color}; padding: 10px; }}")

    def view_drag_enter_event(self, event):
        if event.mimeData().hasUrls():
            self.is_dragging = True
            self.update_stylesheet()
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def view_drag_move_event(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def view_drag_leave_event(self, event):
        self.is_dragging = False
        self.update_stylesheet()
        
    def view_drop_event(self, event):
        self.is_dragging = False
        self.update_stylesheet()
        
        if not event.mimeData().hasUrls():
            event.ignore()
            return
            
        event.acceptProposedAction()
        
        for url in event.mimeData().urls():
            try:
                source_path = url.toLocalFile()
                filename = os.path.basename(source_path)
                target_path = os.path.join(self.TempDesk_folder, filename)
                
                # Handle duplicate filenames
                counter = 1
                base_name, ext = os.path.splitext(filename)
                while os.path.exists(target_path):
                    new_filename = f"{base_name}_{counter}{ext}"
                    target_path = os.path.join(self.TempDesk_folder, new_filename)
                    counter += 1
                
                shutil.move(source_path, target_path)
                
                # Log when file is added for debugging
                import time
                current_time = time.time()
                print(f"🗂️ FILE ADDED TO TempDesk via drag/drop:")
                print(f"   File: {filename}")
                print(f"   Time: {current_time}")
                print(f"   Path: {target_path}")
                
            except Exception as e:
                QMessageBox.warning(self, "Move Error", f"Could not move file:\n{e}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.is_dragging = True
            self.update_stylesheet()
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
    
    def dragLeaveEvent(self, event):
        self.is_dragging = False
        self.update_stylesheet()
        
    def dropEvent(self, event):
        self.is_dragging = False
        self.update_stylesheet()
        
        if not event.mimeData().hasUrls():
            event.ignore()
            return
            
        event.acceptProposedAction()
        
        for url in event.mimeData().urls():
            try:
                source_path = url.toLocalFile()
                filename = os.path.basename(source_path)
                target_path = os.path.join(self.TempDesk_folder, filename)
                
                # Handle duplicate filenames
                counter = 1
                base_name, ext = os.path.splitext(filename)
                while os.path.exists(target_path):
                    new_filename = f"{base_name}_{counter}{ext}"
                    target_path = os.path.join(self.TempDesk_folder, new_filename)
                    counter += 1
                
                # Use native Windows cut/paste operation
                try:
                    import ctypes
                    from ctypes import wintypes
                    
                    # Open clipboard
                    user32 = ctypes.windll.user32
                    kernel32 = ctypes.windll.kernel32
                    
                    if user32.OpenClipboard(None):
                        try:
                            # Clear clipboard
                            user32.EmptyClipboard()
                            
                            # Create DROPFILES structure for the file
                            # DROPFILES structure + file path + double null terminator
                            file_path_w = source_path + '\0\0'  # Double null terminated
                            file_path_bytes = file_path_w.encode('utf-16le')
                            
                            # DROPFILES structure: 20 bytes + file paths
                            dropfiles_size = 20 + len(file_path_bytes)
                            
                            # Allocate global memory
                            hglobal = kernel32.GlobalAlloc(0x2000, dropfiles_size)  # GMEM_MOVEABLE
                            if hglobal:
                                ptr = kernel32.GlobalLock(hglobal)
                                if ptr:
                                    # Fill DROPFILES structure
                                    ctypes.memmove(ptr, ctypes.c_uint32(20), 4)  # pFiles offset
                                    ctypes.memmove(ptr + 4, ctypes.c_uint32(0), 4)  # pt.x
                                    ctypes.memmove(ptr + 8, ctypes.c_uint32(0), 4)  # pt.y  
                                    ctypes.memmove(ptr + 12, ctypes.c_uint32(0), 4)  # fNC
                                    ctypes.memmove(ptr + 16, ctypes.c_uint32(1), 4)  # fWide (Unicode)
                                    
                                    # Copy file path
                                    ctypes.memmove(ptr + 20, file_path_bytes, len(file_path_bytes))
                                    
                                    kernel32.GlobalUnlock(hglobal)
                                    
                                    # Set clipboard data
                                    CF_HDROP = 15
                                    user32.SetClipboardData(CF_HDROP, hglobal)
                                    
                                    # Set "Preferred DropEffect" to MOVE (cut)
                                    dropeffect_format = user32.RegisterClipboardFormatW("Preferred DropEffect")
                                    if dropeffect_format:
                                        effect_data = ctypes.c_uint32(2)  # DROPEFFECT_MOVE
                                        hglobal_effect = kernel32.GlobalAlloc(0x2000, 4)
                                        if hglobal_effect:
                                            ptr_effect = kernel32.GlobalLock(hglobal_effect)
                                            if ptr_effect:
                                                ctypes.memmove(ptr_effect, ctypes.byref(effect_data), 4)
                                                kernel32.GlobalUnlock(hglobal_effect)
                                                user32.SetClipboardData(dropeffect_format, hglobal_effect)
                                    
                        finally:
                            user32.CloseClipboard()
                        
                        # Now do the actual move - this will be seen as a paste operation
                        shutil.move(source_path, target_path)
                        
                    else:
                        # Clipboard failed, use regular move
                        shutil.move(source_path, target_path)
                        
                except:
                    # If anything fails, use regular move
                    shutil.move(source_path, target_path)
                
                # Log when file is added for debugging - this sets the creation time
                import time
                print(f"🗂️ FILE ADDED TO TempDesk via drag/drop:")
                print(f"   File: {filename}")
                print(f"   Time: {time.time()}")
                print(f"   Path: {target_path}")
                    
            except Exception as e:
                QMessageBox.warning(self, "Move Error", f"Could not move file:\n{e}")
        
        # Refresh the file system model to show changes immediately
        self.model.setRootPath("")
        self.model.setRootPath(self.TempDesk_folder)

    def view_key_press_event(self, event: QKeyEvent):
        """Handle keyboard shortcuts for the view."""
        if event.key() == Qt.Key.Key_C and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.copy_selected_items()
        elif event.key() == Qt.Key.Key_X and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.cut_selected_items()
        elif event.key() == Qt.Key.Key_V and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.paste_items()
        elif event.key() == Qt.Key.Key_A and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.select_all()
        elif event.key() == Qt.Key.Key_Delete:
            self.delete_selected_items()
        elif event.key() == Qt.Key.Key_F2:
            indexes = self.view.selectedIndexes()
            if indexes:
                self.rename_item(indexes[0])
        else:
            # Call the original keyPressEvent
            QListView.keyPressEvent(self.view, event)

    def copy_selected_items(self):
        """Copy selected items to clipboard."""
        indexes = self.view.selectedIndexes()
        if indexes:
            self.copy_items(indexes)

    def cut_selected_items(self):
        """Cut selected items to clipboard."""
        indexes = self.view.selectedIndexes()
        if indexes:
            self.cut_items(indexes)

    def delete_selected_items(self):
        """Delete selected items."""
        indexes = self.view.selectedIndexes()
        if indexes:
            self.delete_items(indexes)

    def select_all(self):
        """Select all items in the view."""
        self.view.selectAll()

    def copy_items(self, indexes):
        """Copy items to clipboard."""
        try:
            paths = [self.model.filePath(i) for i in indexes]
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()
            mime_data.setUrls([QUrl.fromLocalFile(path) for path in paths])
            clipboard.setMimeData(mime_data)
        except Exception as e:
            QMessageBox.warning(self, "Copy Error", f"Could not copy items:\n{e}")

    def cut_items(self, indexes):
        """Cut items to clipboard."""
        try:
            paths = [self.model.filePath(i) for i in indexes]
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()
            mime_data.setUrls([QUrl.fromLocalFile(path) for path in paths])
            # Mark as cut operation
            mime_data.setData("application/x-qt-windows-mime;value=\"Preferred DropEffect\"", b"\x05\x00\x00\x00")
            clipboard.setMimeData(mime_data)
        except Exception as e:
            QMessageBox.warning(self, "Cut Error", f"Could not cut items:\n{e}")

    def paste_items(self):
        """Paste items from clipboard."""
        try:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()
            
            # Check for URLs first (web links)
            if mime_data.hasText():
                text = mime_data.text().strip()
                if self.is_url(text):
                    self.create_url_shortcut(text)
                    return
            
            # Handle file URLs
            if mime_data.hasUrls():
                for url in mime_data.urls():
                    source_path = url.toLocalFile()
                    if os.path.exists(source_path):
                        filename = os.path.basename(source_path)
                        target_path = os.path.join(self.TempDesk_folder, filename)
                        
                        # Handle duplicate filenames
                        counter = 1
                        base_name, ext = os.path.splitext(filename)
                        while os.path.exists(target_path):
                            new_filename = f"{base_name}_{counter}{ext}"
                            target_path = os.path.join(self.TempDesk_folder, new_filename)
                            counter += 1
                        
                        # Check if this was a cut operation
                        if mime_data.hasFormat("application/x-qt-windows-mime;value=\"Preferred DropEffect\""):
                            shutil.move(source_path, target_path)
                            
                            # Notify Windows that the file was deleted from source location
                            try:
                                import ctypes
                                SHCNE_DELETE = 0x00000002
                                SHCNF_PATH = 0x0001
                                ctypes.windll.shell32.SHChangeNotifyW(SHCNE_DELETE, SHCNF_PATH, source_path, None)
                            except:
                                pass  # If Windows API call fails, continue anyway
                        else:
                            shutil.copy2(source_path, target_path)
                
                # Refresh the file system model to show changes immediately
                self.model.setRootPath("")
                self.model.setRootPath(self.TempDesk_folder)
                            
        except Exception as e:
            QMessageBox.warning(self, "Paste Error", f"Could not paste items:\n{e}")
    
    def is_url(self, text):
        """Check if text looks like a URL."""
        import re
        # Simple URL pattern matching
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return bool(url_pattern.match(text))
    
    def create_url_shortcut(self, url):
        """Create a Windows shortcut file for a URL."""
        try:
            import win32com.client
            
            # Generate a filename from the URL
            parsed = urlparse(url)
            domain = parsed.netloc.replace('www.', '').replace('.', '_')
            filename = f"{domain}.url"
            
            # Handle duplicate filenames
            counter = 1
            base_name, ext = os.path.splitext(filename)
            target_path = os.path.join(self.TempDesk_folder, filename)
            while os.path.exists(target_path):
                new_filename = f"{base_name}_{counter}{ext}"
                target_path = os.path.join(self.TempDesk_folder, new_filename)
                counter += 1
            
            # Create the .url file
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write("[InternetShortcut]\n")
                f.write(f"URL={url}\n")
                f.write("IconIndex=0\n")
            
            print(f"🔗 URL SHORTCUT CREATED: {filename}")
            print(f"   URL: {url}")
            print(f"   Path: {target_path}")
            
            # Refresh the file system model to show changes immediately
            self.model.setRootPath("")
            self.model.setRootPath(self.TempDesk_folder)
            
        except Exception as e:
            print(f"Error creating URL shortcut: {e}")
            QMessageBox.warning(self, "Error", f"Could not create URL shortcut:\n{e}")

    def open_with_dialog(self, index):
        """Open file with default application dialog."""
        try:
            file_path = self.model.filePath(index)
            os.startfile(file_path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open file:\n{e}")

    def rename_item(self, index):
        """Rename the selected item."""
        try:
            file_path = self.model.filePath(index)
            filename = os.path.basename(file_path)
            new_name, ok = QInputDialog.getText(self, "Rename", "Enter new name:", text=filename)
            if ok and new_name and new_name != filename:
                new_path = os.path.join(os.path.dirname(file_path), new_name)
                if not os.path.exists(new_path):
                    os.rename(file_path, new_path)
                else:
                    QMessageBox.warning(self, "Error", "A file with that name already exists.")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not rename file:\n{e}")

    def show_properties(self, index):
        """Show file properties dialog."""
        try:
            file_path = self.model.filePath(index)
            subprocess.Popen(['explorer', '/select,', file_path])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not show properties:\n{e}")

    def refresh_view(self):
        """Refresh the file view."""
        self.directory_changed()
        
    def auto_cleanup(self):
        """Automatically delete old files if auto-delete is enabled."""
        if not self.config.get('auto_delete', False):
            return
            
        import time
        current_time = time.time()
        filter_period = self.config.get('filter_period', 86400)
        
        try:
            for item in os.listdir(self.TempDesk_folder):
                item_path = os.path.join(self.TempDesk_folder, item)
                if os.path.exists(item_path):
                    try:
                        # Use creation time to match the filtering logic
                        ctime = os.path.getctime(item_path)
                        if (current_time - ctime) > filter_period:
                            if os.path.isfile(item_path):
                                os.remove(item_path)
                            elif os.path.isdir(item_path):
                                shutil.rmtree(item_path)
                    except Exception as e:
                        print(f"Failed to delete {item_path}: {e}")
        except Exception as e:
            print(f"Auto-cleanup error: {e}")

    def closeEvent(self, event):
        self.save_config(); event.accept(); QApplication.instance().quit()

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    widget = DesktopWidget()

    # --- System Tray Icon Setup ---
    tray_icon = QSystemTrayIcon(QIcon(app.style().standardPixmap(QStyle.StandardPixmap.SP_DriveHDIcon)), parent=app)
    tray_icon.setToolTip("TempDesk")
    
    def toggle_visibility():
        widget.setVisible(not widget.isVisible())

    def tray_activated(reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            toggle_visibility()

    tray_icon.activated.connect(tray_activated)

    tray_menu = QMenu()
    tray_menu.addAction("Show/Hide TempDesk", toggle_visibility)
    tray_menu.addSeparator()
    tray_menu.addAction("Quit", app.quit)
    tray_icon.setContextMenu(tray_menu)
    
    tray_icon.show()
    widget.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
