#!/usr/bin/env python3
"""
TempDrop - A custom file explorer widget for the desktop.
"""

import sys
import os
import json
import shutil
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListView, QAbstractItemView, QMenu, QMessageBox,
    QFileIconProvider, QDialog, QDialogButtonBox, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QSize, QPoint, QRect, QFileSystemWatcher
)
from PyQt6.QtGui import (
    QFileSystemModel, QIcon, QAction, QMouseEvent
)

class ResizableFramelessWindow(QMainWindow):
    """
    A base class for a frameless window that can be resized by dragging its
    edges and corners.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.drag_position = None
        self.resizing = False
        self.resize_edge = None
        self.resize_margin = 8

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            if self.is_on_edge(pos):
                self.resizing = True
                self.resize_edge = self.get_edge(pos)
            else:
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        pos = event.position().toPoint()
        if self.resizing:
            self.resize_window(event.globalPosition().toPoint())
        elif self.drag_position:
             if self.title_bar.underMouse():
                self.move(event.globalPosition().toPoint() - self.drag_position)
        else:
            self.update_cursor(pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        self.drag_position = None
        self.resizing = False
        self.resize_edge = None
        self.unsetCursor()
        super().mouseReleaseEvent(event)

    def is_on_edge(self, pos: QPoint) -> bool:
        return any(self.get_edge(pos))

    def get_edge(self, pos: QPoint) -> tuple:
        left = pos.x() < self.resize_margin
        top = pos.y() < self.resize_margin
        right = pos.x() > self.width() - self.resize_margin
        bottom = pos.y() > self.height() - self.resize_margin
        return left, top, right, bottom

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

        if left:
            rect.setLeft(global_pos.x())
        if top:
            rect.setTop(global_pos.y())
        if right:
            rect.setRight(global_pos.x())
        if bottom:
            rect.setBottom(global_pos.y())
        
        if rect.width() < self.minimumWidth():
            rect.setWidth(self.minimumWidth())
        if rect.height() < self.minimumHeight():
            rect.setHeight(self.minimumHeight())

        self.setGeometry(rect)


class DesktopWidget(ResizableFramelessWindow):
    """
    The main file explorer widget, inheriting resizability.
    """
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.tempdrop_folder = self.get_tempdrop_folder()
        self.is_dragging = False

        os.makedirs(self.tempdrop_folder, exist_ok=True)
        
        self.setAcceptDrops(True)
        self.setup_ui()
        self.setup_window_properties()
        self.setup_file_system_model()
        
    def get_tempdrop_folder(self) -> str:
        return str(Path.home() / 'TempDrop')
    
    def load_config(self) -> dict:
        config_path = Path.home() / '.tempdrop_config.json'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def save_config(self):
        config_path = Path.home() / '.tempdrop_config.json'
        config = {'window_geometry': self.saveGeometry().data().hex()}
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def setup_ui(self):
        self.setWindowTitle("TempDrop")
        self.setMinimumSize(300, 200)
        
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        central_widget.setObjectName("centralWidget")
        central_widget.setStyleSheet("#centralWidget { background-color: transparent; }")

        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self.title_bar = self.create_title_bar()
        self.main_layout.addWidget(self.title_bar)
        
        self.view = QListView()
        self.view.setFlow(QListView.Flow.LeftToRight)
        self.view.setWrapping(True)
        self.view.setResizeMode(QListView.ResizeMode.Adjust)
        self.view.setMovement(QListView.Movement.Snap)
        self.view.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.view.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.view.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.view.setViewMode(QListView.ViewMode.IconMode)
        self.view.setIconSize(QSize(64, 64))
        self.view.setGridSize(QSize(84, 84))
        self.view.setWordWrap(True)
        
        self.view.doubleClicked.connect(self.open_item)
        self.view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.view.customContextMenuRequested.connect(self.show_context_menu)
        
        self.view.setObjectName("fileView")
        self.update_stylesheet() # Set initial stylesheet
        self.main_layout.addWidget(self.view)

    def create_title_bar(self) -> QWidget:
        self.title_bar = QWidget() # Make title_bar an instance attribute
        self.title_bar.setFixedHeight(32)
        self.title_bar.setStyleSheet("""
            background-color: #0078D7;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
        """)
        
        title_layout = QHBoxLayout(self.title_bar)
        title_layout.setContentsMargins(10, 0, 5, 0)
        
        title_label = QLabel(f"📁 TempDrop")
        title_label.setStyleSheet("color: white; font-weight: bold;")
        
        settings_btn = QPushButton("⚙️")
        settings_btn.setFixedSize(28, 28)
        settings_btn.clicked.connect(self.show_settings_dialog)
        settings_btn.setStyleSheet("""
            QPushButton { border: none; color: white; font-size: 16px; }
            QPushButton:hover { background-color: #3a93de; }
        """)

        close_btn = QPushButton("×")
        close_btn.setFixedSize(28, 28)
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton { border: none; color: white; font-size: 20px; }
            QPushButton:hover { background-color: #E81123; }
        """)

        title_layout.addWidget(title_label)
        title_layout.addStretch()
        title_layout.addWidget(settings_btn)
        title_layout.addWidget(close_btn)
        
        return self.title_bar

    def setup_window_properties(self):
        if 'window_geometry' in self.config:
            self.restoreGeometry(bytes.fromhex(self.config['window_geometry']))
        else:
            screen = QApplication.primaryScreen().geometry()
            self.resize(500, 350)
            self.move(screen.width() - self.width() - 20, 40)
    
    def setup_file_system_model(self):
        self.model = QFileSystemModel()
        self.model.setRootPath(self.tempdrop_folder)
        self.model.iconProvider().setOptions(QFileIconProvider.Option.DontUseCustomDirectoryIcons)

        self.view.setModel(self.model)
        self.view.setRootIndex(self.model.index(self.tempdrop_folder))

        self.watcher = QFileSystemWatcher([self.tempdrop_folder])
        self.watcher.directoryChanged.connect(self.directory_changed)
    
    def directory_changed(self):
        self.model.setRootPath("") # Force refresh
        self.model.setRootPath(self.tempdrop_folder)
        self.view.setRootIndex(self.model.index(self.tempdrop_folder))
    
    def open_item(self, index):
        file_path = self.model.filePath(index)
        try:
            os.startfile(file_path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open '{file_path}':\n{e}")
            
    def show_context_menu(self, position):
        indexes = self.view.selectedIndexes()
        if not indexes:
            return

        menu = QMenu()
        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self.open_item(indexes[0]))
        menu.addAction(open_action)

        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self.delete_items(indexes))
        menu.addAction(delete_action)
        
        menu.addSeparator()

        show_in_folder_action = QAction("Show in Explorer", self)
        show_in_folder_action.triggered.connect(self.show_in_explorer)
        menu.addAction(show_in_folder_action)
        
        menu.exec(self.view.viewport().mapToGlobal(position))

    def delete_items(self, indexes):
        count = len(indexes)
        file_paths = [self.model.filePath(i) for i in indexes]
        
        reply = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to permanently delete {count} item(s)?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            for path in file_paths:
                try:
                    if os.path.isfile(path): os.remove(path)
                    elif os.path.isdir(path): shutil.rmtree(path)
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Could not delete '{path}':\n{e}")

    def show_in_explorer(self):
        subprocess.Popen(f'explorer "{self.tempdrop_folder}"')
        
    def show_settings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Settings")
        layout = QVBoxLayout()
        
        info_label = QLabel(f"<b>TempDrop Folder:</b><br>{self.tempdrop_folder}")
        info_label.setTextFormat(Qt.TextFormat.RichText)
        info_label.setWordWrap(True)
        
        open_folder_btn = QPushButton("Open Folder Location")
        open_folder_btn.clicked.connect(self.show_in_explorer)
        
        clear_folder_btn = QPushButton("Clear All Items...")
        clear_folder_btn.clicked.connect(self.clear_tempdrop_folder)
        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(dialog.reject)
        
        layout.addWidget(info_label)
        layout.addWidget(open_folder_btn)
        layout.addWidget(clear_folder_btn)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        dialog.exec()
        
    def clear_tempdrop_folder(self):
        reply = QMessageBox.warning(
            self, "Confirm Clear",
            "Are you sure you want to permanently delete ALL items in the TempDrop folder?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel
        )
        if reply == QMessageBox.StandardButton.Yes:
            for item in os.listdir(self.tempdrop_folder):
                item_path = os.path.join(self.tempdrop_folder, item)
                try:
                    if os.path.isfile(item_path): os.unlink(item_path)
                    elif os.path.isdir(item_path): shutil.rmtree(item_path)
                except Exception as e:
                    print(f"Failed to delete {item_path}: {e}")

    def update_stylesheet(self):
        """Updates the stylesheet to provide visual feedback for drag-and-drop."""
        border_color = "#0078D7" if self.is_dragging else "#ccc"
        self.view.setStyleSheet(f"""
            QListView#fileView {{
                background-color: rgba(255, 255, 255, 0.9);
                border-bottom-left-radius: 8px;
                border-bottom-right-radius: 8px;
                border: 2px solid {border_color};
                padding: 10px;
            }}
            QListView#fileView::item {{
                width: 70px;
                height: 70px;
                color: #333;
                text-align: center;
            }}
        """)

    # --- Drag/Drop Events ---

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            self.is_dragging = True
            self.update_stylesheet()
            event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        self.is_dragging = False
        self.update_stylesheet()
        
    def dropEvent(self, event):
        self.is_dragging = False
        self.update_stylesheet()
        urls = event.mimeData().urls()
        for url in urls:
            src_path = url.toLocalFile()
            dest_path = os.path.join(self.tempdrop_folder, os.path.basename(src_path))
            try:
                shutil.move(src_path, dest_path)
            except Exception as e:
                QMessageBox.warning(self, "Move Error", f"Could not move file:\n{e}")

    def closeEvent(self, event):
        self.save_config()
        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName("TempDrop")
    app.setApplicationName("TempDrop")
    app.setWindowIcon(QFileIconProvider().icon(QFileIconProvider.IconType.Folder))
    
    widget = DesktopWidget()
    widget.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
