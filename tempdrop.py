#!/usr/bin/env python3
"""
TempDrop - A true desktop file explorer widget with system tray integration.
"""

import sys
import os
import json
import shutil
import subprocess
from pathlib import Path

# Windows-specific imports are required for desktop parenting and tray icon
import win32gui
import win32con

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListView, QAbstractItemView, QMenu, QMessageBox,
    QFileIconProvider, QSystemTrayIcon, QStyle, QInputDialog
)
from PyQt6.QtCore import (
    Qt, QSize, QPoint, QRect, QFileSystemWatcher
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
        else:
            self.update_cursor(pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.drag_position = None
        self.resizing = False
        self.unsetCursor()
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

    def update_cursor(self, pos: QPoint):
        left, top, right, bottom = self.get_edge(pos)
        if (left and top) or (right and bottom):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        elif (right and top) or (left and bottom):
            self.setCursor(Qt.CursorShape.SizeBDiagCursor)
        elif left or right:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
        elif top or bottom:
            self.setCursor(Qt.CursorShape.SizeVerCursor)
        else:
            self.unsetCursor()

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
        self.tempdrop_folder = self.get_tempdrop_folder()
        self.is_dragging = False

        os.makedirs(self.tempdrop_folder, exist_ok=True)
        
        # Drag and drop is handled by the view, not the main window
        # self.setAcceptDrops(True)
        self.setup_ui()
        self.setup_window_properties()
        self.setup_file_system_model()
        self.pin_to_desktop()
        
    def get_tempdrop_folder(self) -> str:
        return str(Path.home() / 'TempDrop')
    
    def load_config(self) -> dict:
        config_path = Path.home() / '.tempdrop_config.json'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f: return json.load(f)
            except json.JSONDecodeError: return {}
        return {}
    
    def save_config(self):
        config_path = Path.home() / '.tempdrop_config.json'
        config = {'window_geometry': self.saveGeometry().data().hex()}
        try:
            with open(config_path, 'w') as f: json.dump(config, f, indent=2)
        except Exception as e: print(f"Error saving config: {e}")
    
    def setup_ui(self):
        self.setWindowTitle("TempDrop")
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
        
        title_label = QLabel("📁 TempDrop")
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
        if 'window_geometry' in self.config:
            self.restoreGeometry(bytes.fromhex(self.config['window_geometry']))
        else:
            screen = QApplication.primaryScreen().geometry()
            self.resize(500, 350)
            self.move(screen.width() - self.width() - 20, 40)
        
        # Set window to stay on top of desktop but below other applications
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
    
    def setup_file_system_model(self):
        self.model = QFileSystemModel()
        self.model.setRootPath(self.tempdrop_folder)
        self.model.iconProvider().setOptions(QFileIconProvider.Option.DontUseCustomDirectoryIcons)
        self.view.setModel(self.model)
        self.view.setRootIndex(self.model.index(self.tempdrop_folder))
        self.watcher = QFileSystemWatcher([self.tempdrop_folder])
        self.watcher.directoryChanged.connect(self.directory_changed)
    
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
        self.model.setRootPath(""); self.model.setRootPath(self.tempdrop_folder)
        self.view.setRootIndex(self.model.index(self.tempdrop_folder))
    
    def open_item(self, index):
        try: os.startfile(self.model.filePath(index))
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

    def show_in_explorer(self):
        subprocess.Popen(f'explorer "{self.tempdrop_folder}"')
        
    def show_settings_dialog(self):
        # Using a QMessageBox for simplicity
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("TempDrop Settings")
        msg_box.setText(f"<b>TempDrop Folder:</b><br>{self.tempdrop_folder}")
        msg_box.addButton("Open Folder", QMessageBox.ButtonRole.ActionRole).clicked.connect(self.show_in_explorer)
        msg_box.addButton("Clear All Items...", QMessageBox.ButtonRole.ActionRole).clicked.connect(self.clear_tempdrop_folder)
        msg_box.addButton("Close", QMessageBox.ButtonRole.RejectRole)
        msg_box.exec()
        
    def clear_tempdrop_folder(self):
        reply = QMessageBox.warning(self, "Confirm Clear", "Permanently delete ALL items in TempDrop?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel, QMessageBox.StandardButton.Cancel)
        if reply == QMessageBox.StandardButton.Yes:
            for item in os.listdir(self.tempdrop_folder):
                try:
                    item_path = os.path.join(self.tempdrop_folder, item)
                    if os.path.isfile(item_path): os.unlink(item_path)
                    elif os.path.isdir(item_path): shutil.rmtree(item_path)
                except Exception as e: print(f"Failed to delete {item_path}: {e}")

    def update_stylesheet(self):
        border_color = "#0078D7" if self.is_dragging else "#888"
        self.view.setStyleSheet(f"QListView#fileView {{ background-color: rgba(240, 240, 240, 0.95); border-radius: 8px; border: 2px dashed {border_color}; padding: 10px; }}")

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
                target_path = os.path.join(self.tempdrop_folder, filename)
                
                # Handle duplicate filenames
                counter = 1
                base_name, ext = os.path.splitext(filename)
                while os.path.exists(target_path):
                    new_filename = f"{base_name}_{counter}{ext}"
                    target_path = os.path.join(self.tempdrop_folder, new_filename)
                    counter += 1
                
                shutil.move(source_path, target_path)
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
                target_path = os.path.join(self.tempdrop_folder, filename)
                
                # Handle duplicate filenames
                counter = 1
                base_name, ext = os.path.splitext(filename)
                while os.path.exists(target_path):
                    new_filename = f"{base_name}_{counter}{ext}"
                    target_path = os.path.join(self.tempdrop_folder, new_filename)
                    counter += 1
                
                shutil.move(source_path, target_path)
            except Exception as e:
                QMessageBox.warning(self, "Move Error", f"Could not move file:\n{e}")

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
            
            if mime_data.hasUrls():
                for url in mime_data.urls():
                    source_path = url.toLocalFile()
                    if os.path.exists(source_path):
                        filename = os.path.basename(source_path)
                        target_path = os.path.join(self.tempdrop_folder, filename)
                        
                        # Handle duplicate filenames
                        counter = 1
                        base_name, ext = os.path.splitext(filename)
                        while os.path.exists(target_path):
                            new_filename = f"{base_name}_{counter}{ext}"
                            target_path = os.path.join(self.tempdrop_folder, new_filename)
                            counter += 1
                        
                        # Check if this was a cut operation
                        if mime_data.hasFormat("application/x-qt-windows-mime;value=\"Preferred DropEffect\""):
                            shutil.move(source_path, target_path)
                        else:
                            shutil.copy2(source_path, target_path)
                            
        except Exception as e:
            QMessageBox.warning(self, "Paste Error", f"Could not paste items:\n{e}")

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

    def closeEvent(self, event):
        self.save_config(); event.accept(); QApplication.instance().quit()

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    widget = DesktopWidget()

    # --- System Tray Icon Setup ---
    tray_icon = QSystemTrayIcon(QIcon(app.style().standardPixmap(QStyle.StandardPixmap.SP_DriveHDIcon)), parent=app)
    tray_icon.setToolTip("TempDrop")
    
    def toggle_visibility():
        widget.setVisible(not widget.isVisible())

    def tray_activated(reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            toggle_visibility()

    tray_icon.activated.connect(tray_activated)

    tray_menu = QMenu()
    tray_menu.addAction("Show/Hide TempDrop", toggle_visibility)
    tray_menu.addSeparator()
    tray_menu.addAction("Quit", app.quit)
    tray_icon.setContextMenu(tray_menu)
    
    tray_icon.show()
    widget.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
