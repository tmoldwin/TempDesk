import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import shutil
import threading
import time
from datetime import datetime, timedelta
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import sys

class TempDropWidget:
    def __init__(self):
        print("Initializing TempDrop...")
        self.root = tk.Tk()
        self.root.title("TempDrop")
        self.root.geometry("300x400")
        self.root.configure(bg='black')
        print("Window created successfully")
        
        # Make window semi-transparent but not always on top
        self.root.attributes('-alpha', 0.9)
        
        # Remove window decorations for widget-like appearance
        self.root.overrideredirect(True)
        
        # Configuration
        self.config_file = "tempdrop_config.json"
        self.temp_folder = os.path.join(os.path.expanduser("~"), "TempDrop")
        self.auto_delete_days = 7
        self.load_config()
        
        # Create temp folder if it doesn't exist
        os.makedirs(self.temp_folder, exist_ok=True)
        
        # Setup UI
        self.setup_ui()
        
        # Setup file monitoring
        self.setup_file_monitoring()
        
        # Start auto-deletion thread
        self.start_auto_deletion()
        
        # Bind events
        self.bind_events()
        
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.auto_delete_days = config.get('auto_delete_days', 7)
                    self.temp_folder = config.get('temp_folder', self.temp_folder)
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def save_config(self):
        """Save configuration to file"""
        try:
            config = {
                'auto_delete_days': self.auto_delete_days,
                'temp_folder': self.temp_folder
            }
            with open(self.config_file, 'w') as f:
                json.dump(config, f)
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def setup_ui(self):
        """Setup the user interface"""
        print("Setting up UI...")
        # Title bar
        title_frame = tk.Frame(self.root, bg='#2c2c2c', height=30)
        title_frame.pack(fill='x')
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="TempDrop", bg='#2c2c2c', fg='white', font=('Arial', 10, 'bold'))
        title_label.pack(side='left', padx=10, pady=5)
        
        # Close button
        close_btn = tk.Label(title_frame, text="×", bg='#2c2c2c', fg='white', font=('Arial', 16, 'bold'), cursor='hand2')
        close_btn.pack(side='right', padx=10, pady=5)
        close_btn.bind('<Button-1>', lambda e: self.root.quit())
        
        # Folder button
        folder_btn = tk.Label(title_frame, text="📁", bg='#2c2c2c', fg='white', font=('Arial', 12), cursor='hand2')
        folder_btn.pack(side='right', padx=5, pady=5)
        folder_btn.bind('<Button-1>', lambda e: self.open_temp_folder())
        
        # Settings button
        settings_btn = tk.Label(title_frame, text="⚙", bg='#2c2c2c', fg='white', font=('Arial', 12), cursor='hand2')
        settings_btn.pack(side='right', padx=5, pady=5)
        settings_btn.bind('<Button-1>', lambda e: self.show_settings())
        
        # Main content area
        self.content_frame = tk.Frame(self.root, bg='black')
        self.content_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Drop zone
        self.drop_label = tk.Label(self.content_frame, 
                                 text="Drop files here\nor click 'Add File'", 
                                 bg='#1a1a1a', fg='white', 
                                 font=('Arial', 12),
                                 relief='solid', borderwidth=2)
        self.drop_label.pack(fill='both', expand=True, pady=10)
        
        # Add file button
        add_file_btn = tk.Button(self.content_frame, text="Add File", 
                                bg='#2c2c2c', fg='white',
                                command=self.add_file_manually)
        add_file_btn.pack(pady=5)
        
        # Files grid (for desktop icon appearance)
        self.files_canvas = tk.Canvas(self.content_frame, bg='black', highlightthickness=0)
        self.files_canvas.pack(fill='both', expand=True, pady=5)
        
        # Scrollbar for files
        scrollbar = tk.Scrollbar(self.content_frame, orient="vertical", command=self.files_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        self.files_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Frame inside canvas for files
        self.files_frame = tk.Frame(self.files_canvas, bg='black')
        self.files_canvas.create_window((0, 0), window=self.files_frame, anchor="nw")
        
        self.update_files_list()
        print("UI setup complete")
    
    def open_temp_folder(self):
        """Open the temp folder in file explorer"""
        try:
            os.startfile(self.temp_folder)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder: {e}")
    
    def add_file_manually(self):
        """Add file manually through file dialog"""
        file_path = filedialog.askopenfilename(title="Select file to add to TempDrop")
        if file_path:
            self.move_file_to_temp(file_path)
            self.update_files_list()
    
    def move_file_to_temp(self, file_path):
        """Move a file to the temp folder"""
        try:
            filename = os.path.basename(file_path)
            dest_path = os.path.join(self.temp_folder, filename)
            
            # Handle duplicate filenames
            counter = 1
            name, ext = os.path.splitext(filename)
            while os.path.exists(dest_path):
                filename = f"{name}_{counter}{ext}"
                dest_path = os.path.join(self.temp_folder, filename)
                counter += 1
            
            shutil.move(file_path, dest_path)
            print(f"Moved {file_path} to {dest_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to move file: {e}")
    
    def setup_file_monitoring(self):
        """Setup file system monitoring"""
        try:
            self.observer = Observer()
            event_handler = FileChangeHandler(self)
            self.observer.schedule(event_handler, self.temp_folder, recursive=False)
            self.observer.start()
            print("File monitoring started")
        except Exception as e:
            print(f"File monitoring setup failed: {e}")
    
    def update_files_list(self):
        """Update the files list display"""
        # Clear existing files
        for widget in self.files_frame.winfo_children():
            widget.destroy()
        
        # Get files from temp folder
        files = []
        if os.path.exists(self.temp_folder):
            for file in os.listdir(self.temp_folder):
                file_path = os.path.join(self.temp_folder, file)
                if os.path.isfile(file_path):
                    files.append(file)
        
        # Create file items in a grid layout (like desktop icons)
        if files:
            # Calculate grid layout
            cols = 3  # 3 columns
            for i, file in enumerate(files):
                row = i // cols
                col = i % cols
                self.create_file_icon(file, row, col)
        
        # Update canvas scroll region
        self.files_frame.update_idletasks()
        self.files_canvas.configure(scrollregion=self.files_canvas.bbox("all"))
    
    def create_file_icon(self, filename, row, col):
        """Create a file icon widget (like desktop icon)"""
        # Icon frame
        icon_frame = tk.Frame(self.files_frame, bg='black', width=80, height=100)
        icon_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
        icon_frame.grid_propagate(False)
        
        # File icon (emoji)
        icon_label = tk.Label(icon_frame, text="📄", bg='black', fg='white', 
                            font=('Arial', 24), cursor='hand2')
        icon_label.pack(pady=(5, 2))
        
        # File name (truncated if too long)
        display_name = filename
        if len(display_name) > 12:
            display_name = display_name[:9] + "..."
        
        name_label = tk.Label(icon_frame, text=display_name, bg='black', fg='white', 
                            font=('Arial', 8), wraplength=70, justify='center')
        name_label.pack(pady=2)
        
        # Bind events
        icon_label.bind('<Double-Button-1>', lambda e, f=filename: self.open_file(f))
        name_label.bind('<Double-Button-1>', lambda e, f=filename: self.open_file(f))
        
        # Right-click menu for delete
        icon_label.bind('<Button-3>', lambda e, f=filename: self.show_file_menu(e, f))
        name_label.bind('<Button-3>', lambda e, f=filename: self.show_file_menu(e, f))
    
    def show_file_menu(self, event, filename):
        """Show context menu for file"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Open", command=lambda: self.open_file(filename))
        menu.add_command(label="Delete", command=lambda: self.delete_file(filename))
        menu.tk_popup(event.x_root, event.y_root)
    
    def open_file(self, filename):
        """Open a file"""
        file_path = os.path.join(self.temp_folder, filename)
        try:
            os.startfile(file_path)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open file: {e}")
    
    def delete_file(self, filename):
        """Delete a file"""
        file_path = os.path.join(self.temp_folder, filename)
        try:
            os.remove(file_path)
            self.update_files_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete file: {e}")
    
    def start_auto_deletion(self):
        """Start the auto-deletion thread"""
        def auto_delete_worker():
            while True:
                try:
                    self.cleanup_old_files()
                    time.sleep(3600)  # Check every hour
                except Exception as e:
                    print(f"Auto-deletion error: {e}")
        
        thread = threading.Thread(target=auto_delete_worker, daemon=True)
        thread.start()
        print("Auto-deletion thread started")
    
    def cleanup_old_files(self):
        """Clean up files older than the specified days"""
        cutoff_date = datetime.now() - timedelta(days=self.auto_delete_days)
        
        if os.path.exists(self.temp_folder):
            for filename in os.listdir(self.temp_folder):
                file_path = os.path.join(self.temp_folder, filename)
                if os.path.isfile(file_path):
                    file_time = datetime.fromtimestamp(os.path.getctime(file_path))
                    if file_time < cutoff_date:
                        try:
                            os.remove(file_path)
                            print(f"Auto-deleted old file: {filename}")
                        except Exception as e:
                            print(f"Failed to auto-delete {filename}: {e}")
    
    def show_settings(self):
        """Show settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("TempDrop Settings")
        settings_window.geometry("400x350")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Auto-delete days
        tk.Label(settings_window, text="Auto-delete after (days):").pack(pady=10)
        days_var = tk.StringVar(value=str(self.auto_delete_days))
        days_entry = tk.Entry(settings_window, textvariable=days_var)
        days_entry.pack(pady=5)
        
        # Temp folder
        tk.Label(settings_window, text="Temp folder:").pack(pady=10)
        folder_var = tk.StringVar(value=self.temp_folder)
        folder_entry = tk.Entry(settings_window, textvariable=folder_var, width=50)
        folder_entry.pack(pady=5)
        
        def browse_folder():
            folder = filedialog.askdirectory(initialdir=self.temp_folder)
            if folder:
                folder_var.set(folder)
        
        browse_btn = tk.Button(settings_window, text="Browse", command=browse_folder)
        browse_btn.pack(pady=5)
        
        # Open folder button
        open_folder_btn = tk.Button(settings_window, text="Open Temp Folder", 
                                  command=self.open_temp_folder)
        open_folder_btn.pack(pady=10)
        
        def save_settings():
            try:
                self.auto_delete_days = int(days_var.get())
                self.temp_folder = folder_var.get()
                os.makedirs(self.temp_folder, exist_ok=True)
                self.save_config()
                self.update_files_list()
                settings_window.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number for days")
        
        save_btn = tk.Button(settings_window, text="Save", command=save_settings)
        save_btn.pack(pady=20)
    
    def bind_events(self):
        """Bind additional events"""
        # Right-click menu
        self.root.bind('<Button-3>', self.show_context_menu)
        
        # Window dragging
        self.root.bind('<Button-1>', self.start_drag)
        self.root.bind('<B1-Motion>', self.on_drag)
        self.root.bind('<ButtonRelease-1>', self.stop_drag)
        
        # Mouse wheel for scrolling
        self.files_canvas.bind('<MouseWheel>', self.on_mousewheel)
        
        self.drag_start_x = 0
        self.drag_start_y = 0
    
    def on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        self.files_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def start_drag(self, event):
        """Start window dragging"""
        self.drag_start_x = event.x
        self.drag_start_y = event.y
    
    def on_drag(self, event):
        """Handle window dragging"""
        x = self.root.winfo_x() + (event.x - self.drag_start_x)
        y = self.root.winfo_y() + (event.y - self.drag_start_y)
        self.root.geometry(f"+{x}+{y}")
    
    def stop_drag(self, event):
        """Stop window dragging"""
        pass
    
    def show_context_menu(self, event):
        """Show context menu"""
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Settings", command=self.show_settings)
        menu.add_command(label="Open Folder", command=self.open_temp_folder)
        menu.add_separator()
        menu.add_command(label="Exit", command=self.root.quit)
        menu.tk_popup(event.x_root, event.y_root)
    
    def run(self):
        """Run the application"""
        print("Starting main loop...")
        try:
            self.root.mainloop()
        finally:
            if hasattr(self, 'observer'):
                self.observer.stop()
                self.observer.join()

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, widget):
        self.widget = widget
    
    def on_created(self, event):
        if not event.is_directory:
            self.widget.root.after(100, self.widget.update_files_list)
    
    def on_deleted(self, event):
        if not event.is_directory:
            self.widget.root.after(100, self.widget.update_files_list)
    
    def on_moved(self, event):
        if not event.is_directory:
            self.widget.root.after(100, self.widget.update_files_list)

if __name__ == "__main__":
    print("Starting TempDrop application...")
    app = TempDropWidget()
    app.run() 