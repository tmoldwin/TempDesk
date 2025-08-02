#!/usr/bin/env python3
"""
TempDrop - Simple File Explorer for Temporary Files
Just a normal file list window that stays on desktop.
"""

import sys
import os
import json
import shutil
import datetime
from pathlib import Path
import platform

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QMenu, QMessageBox, QFileDialog,
    QListWidget, QListWidgetItem
)
from PyQt6.QtCore import (
    Qt, QTimer
)
from PyQt6.QtGui import (
    QAction, QIcon
)


class TempDropWidget(QMainWindow):
    """Simple file list window for TempDrop."""
    
    def __init__(self):
        super().__init__()
        self.config = self.load_config()
        self.temp_folder = self.config.get('temp_folder', self.get_default_temp_folder())
        self.auto_delete_days = self.config.get('auto_delete_days', 7)
        
        self.setup_ui()
        self.setup_window_properties()
        self.load_files()
        self.start_cleanup_timer()
        
    def load_config(self) -> dict:
        """Load configuration from file."""
        config_path = Path.home() / '.tempdrop_config.json'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_config(self):
        """Save configuration to file."""
        config_path = Path.home() / '.tempdrop_config.json'
        config = {
            'temp_folder': self.temp_folder,
            'auto_delete_days': self.auto_delete_days
        }
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_default_temp_folder(self) -> str:
        """Get default temp folder path."""
        return str(Path.home() / 'TempDrop')
    
    def setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("TempDrop")
        self.setMinimumSize(600, 400)
        self.resize(800, 500)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Toolbar
        toolbar_layout = QHBoxLayout()
        
        self.title_label = QLabel("TempDrop")
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        
        # Control buttons
        self.folder_btn = QPushButton("📁 Open Folder")
        self.folder_btn.clicked.connect(self.open_temp_folder)
        
        self.settings_btn = QPushButton("⚙ Settings")
        self.settings_btn.clicked.connect(self.show_settings)
        
        self.close_btn = QPushButton("× Close")
        self.close_btn.clicked.connect(self.close)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: #ff4444;
                border: none;
                border-radius: 4px;
                color: white;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background: #ff6666;
            }
        """)
        
        toolbar_layout.addWidget(self.title_label)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.folder_btn)
        toolbar_layout.addWidget(self.settings_btn)
        toolbar_layout.addWidget(self.close_btn)
        
        layout.addLayout(toolbar_layout)
        
        # File list
        self.file_list = QListWidget()
        self.file_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.file_list.customContextMenuRequested.connect(self.show_context_menu)
        self.file_list.itemDoubleClicked.connect(self.open_file)
        
        layout.addWidget(self.file_list)
        
    def setup_window_properties(self):
        """Setup window properties."""
        # Keep it always on top
        self.setWindowFlags(
            Qt.WindowType.WindowStaysOnTopHint
        )
        
        # Position window on desktop
        screen = QApplication.primaryScreen()
        screen_rect = screen.geometry()
        self.move(screen_rect.width() - self.width() - 20, 100)
        
    def load_files(self):
        """Load existing files from temp folder."""
        # Ensure temp folder exists
        os.makedirs(self.temp_folder, exist_ok=True)
        
        self.file_list.clear()
        try:
            for file_path in os.listdir(self.temp_folder):
                full_path = os.path.join(self.temp_folder, file_path)
                if os.path.isfile(full_path):
                    self.add_file_item(full_path)
        except Exception as e:
            print(f"Error loading files: {e}")
    
    def add_file_item(self, file_path: str):
        """Add a file item to the list."""
        filename = os.path.basename(file_path)
        item = QListWidgetItem(filename)
        item.setData(Qt.ItemDataRole.UserRole, file_path)
        self.file_list.addItem(item)
    
    def open_temp_folder(self):
        """Open the temp folder in file explorer."""
        try:
            if platform.system() == "Windows":
                os.startfile(self.temp_folder)
            elif platform.system() == "Darwin":  # macOS
                os.system(f'open "{self.temp_folder}"')
            else:  # Linux
                os.system(f'xdg-open "{self.temp_folder}"')
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open folder: {e}")
    
    def show_context_menu(self, position):
        """Show context menu for file operations."""
        menu = QMenu(self)
        
        # Add file action
        add_action = QAction("Add Files...", self)
        add_action.triggered.connect(self.add_files_dialog)
        menu.addAction(add_action)
        
        menu.addSeparator()
        
        # File-specific actions
        item = self.file_list.itemAt(position)
        if item:
            file_path = item.data(Qt.ItemDataRole.UserRole)
            
            open_action = QAction("Open", self)
            open_action.triggered.connect(lambda: self.open_file(item))
            menu.addAction(open_action)
            
            delete_action = QAction("Delete", self)
            delete_action.triggered.connect(lambda: self.delete_file(item))
            menu.addAction(delete_action)
        
        menu.addSeparator()
        
        # Settings
        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)
        
        menu.exec(self.file_list.mapToGlobal(position))
    
    def add_files_dialog(self):
        """Show file dialog to add files."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Add Files to TempDrop", "", "All Files (*.*)"
        )
        for file_path in files:
            self.add_file(file_path)
    
    def add_file(self, file_path: str):
        """Add a file to the temp folder."""
        try:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(self.temp_folder, filename)
            
            # Handle duplicate filenames
            counter = 1
            while os.path.exists(dest_path):
                name, ext = os.path.splitext(filename)
                dest_path = os.path.join(self.temp_folder, f"{name}_{counter}{ext}")
                counter += 1
            
            shutil.copy2(file_path, dest_path)
            self.add_file_item(dest_path)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not add file: {e}")
    
    def open_file(self, item):
        """Open the file with default application."""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        try:
            if platform.system() == "Windows":
                os.startfile(file_path)
            elif platform.system() == "Darwin":  # macOS
                os.system(f'open "{file_path}"')
            else:  # Linux
                os.system(f'xdg-open "{file_path}"')
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open file: {e}")
    
    def delete_file(self, item):
        """Delete the file."""
        file_path = item.data(Qt.ItemDataRole.UserRole)
        filename = os.path.basename(file_path)
        
        reply = QMessageBox.question(
            self, "Delete File", 
            f"Are you sure you want to delete {filename}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                os.remove(file_path)
                self.file_list.takeItem(self.file_list.row(item))
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not delete file: {e}")
    
    def show_settings(self):
        """Show settings dialog."""
        from PyQt6.QtWidgets import QDialog, QFormLayout, QSpinBox, QLineEdit
        
        dialog = QDialog(self)
        dialog.setWindowTitle("TempDrop Settings")
        dialog.setModal(True)
        
        layout = QFormLayout(dialog)
        
        # Auto-delete days
        days_spin = QSpinBox()
        days_spin.setRange(1, 365)
        days_spin.setValue(self.auto_delete_days)
        layout.addRow("Auto-delete after (days):", days_spin)
        
        # Temp folder
        folder_edit = QLineEdit(self.temp_folder)
        layout.addRow("Temp folder:", folder_edit)
        
        # Buttons
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        
        ok_btn.clicked.connect(dialog.accept)
        cancel_btn.clicked.connect(dialog.reject)
        
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)
        layout.addRow(button_layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.auto_delete_days = days_spin.value()
            self.temp_folder = folder_edit.text()
            self.save_config()
    
    def start_cleanup_timer(self):
        """Start timer for automatic file cleanup."""
        self.cleanup_timer = QTimer()
        self.cleanup_timer.timeout.connect(self.cleanup_old_files)
        self.cleanup_timer.start(3600000)  # Check every hour
        self.cleanup_old_files()  # Initial cleanup
    
    def cleanup_old_files(self):
        """Remove files older than the specified days."""
        try:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=self.auto_delete_days)
            
            for file_path in os.listdir(self.temp_folder):
                full_path = os.path.join(self.temp_folder, file_path)
                if os.path.isfile(full_path):
                    file_time = datetime.datetime.fromtimestamp(os.path.getmtime(full_path))
                    if file_time < cutoff_date:
                        try:
                            os.remove(full_path)
                            print(f"Auto-deleted old file: {file_path}")
                        except Exception as e:
                            print(f"Error deleting old file {file_path}: {e}")
        except Exception as e:
            print(f"Error during cleanup: {e}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        self.save_config()
        event.accept()


def main():
    """Main application entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("TempDrop")
    app.setApplicationVersion("1.0.0")
    
    widget = TempDropWidget()
    widget.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 