using System;
using System.IO;
using System.Windows.Forms;
using System.Drawing;
using System.Runtime.InteropServices;
using System.ComponentModel;
using System.Diagnostics;

namespace TempDesk
{
    public partial class TempDeskForm : Form
    {
        private string tempFolder = "";
        private System.Windows.Forms.Timer? cleanupTimer;
        private int autoDeleteDays = 7;
        private ListView? fileListView;

        public TempDeskForm()
        {
            LoadConfig();
            SetupForm();
            StartCleanupTimer();
        }

        private void LoadConfig()
        {
            string configPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".TempDesk_config.json");
            if (File.Exists(configPath))
            {
                try
                {
                    string json = File.ReadAllText(configPath);
                    // Simple JSON parsing for config
                    if (json.Contains("\"temp_folder\""))
                    {
                        int start = json.IndexOf("\"temp_folder\":\"") + 15;
                        int end = json.IndexOf("\"", start);
                        tempFolder = json.Substring(start, end - start);
                    }
                    if (json.Contains("\"auto_delete_days\""))
                    {
                        int start = json.IndexOf("\"auto_delete_days\":") + 18;
                        int end = json.IndexOf(",", start);
                        if (end == -1) end = json.IndexOf("}", start);
                        int.TryParse(json.Substring(start, end - start), out autoDeleteDays);
                    }
                }
                catch { }
            }
            
            if (string.IsNullOrEmpty(tempFolder))
            {
                tempFolder = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "TempDesk");
            }
        }

        private void SaveConfig()
        {
            string configPath = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), ".TempDesk_config.json");
            string json = $"{{\n  \"temp_folder\": \"{tempFolder}\",\n  \"auto_delete_days\": {autoDeleteDays}\n}}";
            try
            {
                File.WriteAllText(configPath, json);
            }
            catch { }
        }

        private NotifyIcon trayIcon;
        private ContextMenuStrip trayMenu;

        private void SetupForm()
        {
            this.Text = "TempDesk";
            this.Size = new Size(800, 500);
            this.MinimumSize = new Size(600, 400);
            this.StartPosition = FormStartPosition.Manual;
            this.Location = new Point(Screen.PrimaryScreen.WorkingArea.Width - this.Width - 20, 100);
            this.ShowInTaskbar = false;
            this.WindowState = FormWindowState.Normal;
            this.FormBorderStyle = FormBorderStyle.None;
            this.BackColor = Color.White;
            this.TransparencyKey = Color.White;
            this.Opacity = 0.95;

            // Create tray icon
            CreateTrayIcon();

            // Create toolbar
            Panel toolbar = new Panel
            {
                Height = 40,
                Dock = DockStyle.Top,
                BackColor = Color.LightGray
            };

            Label titleLabel = new Label
            {
                Text = "TempDesk",
                Font = new Font("Arial", 12, FontStyle.Bold),
                Location = new Point(10, 10),
                AutoSize = true
            };

            Button openFolderBtn = new Button
            {
                Text = "📁 Open Folder",
                Location = new Point(200, 8),
                Size = new Size(100, 25)
            };
            openFolderBtn.Click += (s, e) => OpenTempFolder();

            Button addFilesBtn = new Button
            {
                Text = "📄 Add Files",
                Location = new Point(310, 8),
                Size = new Size(80, 25)
            };
            addFilesBtn.Click += (s, e) => ShowAddFilesDialog();

            Button settingsBtn = new Button
            {
                Text = "⚙ Settings",
                Location = new Point(400, 8),
                Size = new Size(80, 25)
            };
            settingsBtn.Click += (s, e) => ShowSettings();

            Button minimizeBtn = new Button
            {
                Text = "− Minimize",
                Location = new Point(490, 8),
                Size = new Size(80, 25)
            };
            minimizeBtn.Click += (s, e) => MinimizeToTray();

            toolbar.Controls.AddRange(new Control[] { titleLabel, openFolderBtn, addFilesBtn, settingsBtn, minimizeBtn });
            this.Controls.Add(toolbar);

            // Create native file list view
            CreateFileListView();
        }

        private void CreateTrayIcon()
        {
            trayMenu = new ContextMenuStrip();
            
            var showItem = new ToolStripMenuItem("Show TempDesk");
            showItem.Click += (s, e) => ShowFromTray();
            trayMenu.Items.Add(showItem);
            
            trayMenu.Items.Add(new ToolStripSeparator());
            
            var openFolderItem = new ToolStripMenuItem("Open Folder");
            openFolderItem.Click += (s, e) => OpenTempFolder();
            trayMenu.Items.Add(openFolderItem);
            
            var addFilesItem = new ToolStripMenuItem("Add Files...");
            addFilesItem.Click += (s, e) => ShowAddFilesDialog();
            trayMenu.Items.Add(addFilesItem);
            
            var settingsItem = new ToolStripMenuItem("Settings");
            settingsItem.Click += (s, e) => ShowSettings();
            trayMenu.Items.Add(settingsItem);
            
            trayMenu.Items.Add(new ToolStripSeparator());
            
            var exitItem = new ToolStripMenuItem("Exit");
            exitItem.Click += (s, e) => ExitApplication();
            trayMenu.Items.Add(exitItem);

            trayIcon = new NotifyIcon();
            trayIcon.Icon = SystemIcons.Application;
            trayIcon.Text = "TempDesk";
            trayIcon.ContextMenuStrip = trayMenu;
            trayIcon.Visible = true;
            trayIcon.DoubleClick += (s, e) => ShowFromTray();
        }

        private void MinimizeToTray()
        {
            this.Hide();
            trayIcon.ShowBalloonTip(1000, "TempDesk", "Minimized to tray", ToolTipIcon.Info);
        }

        private void ShowFromTray()
        {
            this.Show();
            this.WindowState = FormWindowState.Normal;
            this.BringToFront();
        }

        private void ExitApplication()
        {
            trayIcon.Visible = false;
            trayIcon.Dispose();
            this.Close();
        }



        private void CreateFileListView()
        {
            // Ensure temp folder exists
            Directory.CreateDirectory(tempFolder);

            // Create simple list view
            fileListView = new ListView
            {
                Dock = DockStyle.Fill,
                View = View.Details,
                FullRowSelect = true,
                AllowDrop = true
            };

            fileListView.Columns.Add("Name", 200);
            fileListView.Columns.Add("Size", 100);
            fileListView.Columns.Add("Type", 100);
            fileListView.Columns.Add("Date Modified", 150);

            fileListView.DragEnter += FileListView_DragEnter;
            fileListView.DragDrop += FileListView_DragDrop;
            fileListView.DoubleClick += FileListView_DoubleClick;
            fileListView.KeyDown += FileListView_KeyDown;

            this.Controls.Add(fileListView);
            fileListView.BringToFront();

            LoadFiles();
        }



        private void FileListView_DragEnter(object sender, DragEventArgs e)
        {
            if (e.Data.GetDataPresent(DataFormats.FileDrop))
            {
                // Check if Ctrl is pressed for copy, otherwise move
                if ((e.KeyState & 8) == 8) // Ctrl key
                    e.Effect = DragDropEffects.Copy;
                else
                    e.Effect = DragDropEffects.Move;
            }
        }

        private void FileListView_DragDrop(object sender, DragEventArgs e)
        {
            if (e.Data.GetDataPresent(DataFormats.FileDrop))
            {
                string[] files = (string[])e.Data.GetData(DataFormats.FileDrop);
                bool isCopy = (e.KeyState & 8) == 8; // Ctrl key pressed
                
                foreach (string file in files)
                {
                    if (isCopy)
                        CopyFile(file);
                    else
                        MoveFile(file);
                }
            }
        }

        private void MoveFile(string sourcePath)
        {
            try
            {
                string fileName = Path.GetFileName(sourcePath);
                string destPath = Path.Combine(tempFolder, fileName);
                
                // Handle duplicate filenames
                int counter = 1;
                while (File.Exists(destPath))
                {
                    string name = Path.GetFileNameWithoutExtension(fileName);
                    string ext = Path.GetExtension(fileName);
                    destPath = Path.Combine(tempFolder, $"{name}_{counter}{ext}");
                    counter++;
                }
                
                File.Move(sourcePath, destPath);
                LoadFiles(); // Refresh the list
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Could not move file: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void CopyFile(string sourcePath)
        {
            try
            {
                string fileName = Path.GetFileName(sourcePath);
                string destPath = Path.Combine(tempFolder, fileName);
                
                // Handle duplicate filenames
                int counter = 1;
                while (File.Exists(destPath))
                {
                    string name = Path.GetFileNameWithoutExtension(fileName);
                    string ext = Path.GetExtension(fileName);
                    destPath = Path.Combine(tempFolder, $"{name}_{counter}{ext}");
                    counter++;
                }
                
                File.Copy(sourcePath, destPath);
                LoadFiles(); // Refresh the list
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Could not copy file: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void AddFile(string sourcePath)
        {
            CopyFile(sourcePath); // Default to copy behavior
        }

        private void FileListView_DoubleClick(object sender, EventArgs e)
        {
            if (fileListView.SelectedItems.Count > 0)
            {
                string filePath = fileListView.SelectedItems[0].Tag.ToString();
                OpenFile(filePath);
            }
        }

        private void OpenFile(string filePath)
        {
            try
            {
                System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                {
                    FileName = filePath,
                    UseShellExecute = true
                });
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Could not open file: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void LoadFiles()
        {
            fileListView.Items.Clear();
            
            try
            {
                foreach (string filePath in Directory.GetFiles(tempFolder))
                {
                    var fileInfo = new FileInfo(filePath);
                    var item = new ListViewItem(fileInfo.Name);
                    item.SubItems.Add(FormatFileSize(fileInfo.Length));
                    item.SubItems.Add(GetFileType(fileInfo.Extension));
                    item.SubItems.Add(fileInfo.LastWriteTime.ToString("g"));
                    item.Tag = filePath;
                    fileListView.Items.Add(item);
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error loading files: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private string FormatFileSize(long bytes)
        {
            string[] sizes = { "B", "KB", "MB", "GB" };
            int order = 0;
            double size = bytes;
            
            while (size >= 1024 && order < sizes.Length - 1)
            {
                order++;
                size /= 1024;
            }
            
            return $"{size:0.##} {sizes[order]}";
        }

        private string GetFileType(string extension)
        {
            return extension.ToUpper().TrimStart('.') + " File";
        }

        private void FileListView_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Control)
            {
                switch (e.KeyCode)
                {
                    case Keys.V: // Paste
                        PasteFiles();
                        e.Handled = true;
                        break;
                    case Keys.C: // Copy selected files
                        CopySelectedFiles();
                        e.Handled = true;
                        break;
                    case Keys.X: // Cut selected files
                        CutSelectedFiles();
                        e.Handled = true;
                        break;
                }
            }
        }

        private void PasteFiles()
        {
            if (Clipboard.ContainsFileDropList())
            {
                var files = Clipboard.GetFileDropList();
                foreach (string file in files)
                {
                    CopyFile(file);
                }
            }
        }

        private void CopySelectedFiles()
        {
            if (fileListView.SelectedItems.Count > 0)
            {
                var files = new System.Collections.Specialized.StringCollection();
                foreach (ListViewItem item in fileListView.SelectedItems)
                {
                    files.Add(item.Tag.ToString());
                }
                Clipboard.SetFileDropList(files);
            }
        }

        private void CutSelectedFiles()
        {
            if (fileListView.SelectedItems.Count > 0)
            {
                var files = new System.Collections.Specialized.StringCollection();
                foreach (ListViewItem item in fileListView.SelectedItems)
                {
                    files.Add(item.Tag.ToString());
                }
                Clipboard.SetFileDropList(files);
                
                // Mark files for deletion after paste
                foreach (ListViewItem item in fileListView.SelectedItems)
                {
                    item.Tag = "DELETE:" + item.Tag.ToString();
                }
            }
        }



        private void ShowAddFilesDialog()
        {
            using (var dialog = new OpenFileDialog())
            {
                dialog.Multiselect = true;
                dialog.Title = "Add Files to TempDesk";
                
                if (dialog.ShowDialog() == DialogResult.OK)
                {
                    foreach (string file in dialog.FileNames)
                    {
                        AddFile(file);
                    }
                }
            }
        }

        private void DeleteFile(string filePath)
        {
            string fileName = Path.GetFileName(filePath);
            
            var result = MessageBox.Show(
                $"Are you sure you want to delete {fileName}?",
                "Delete File",
                MessageBoxButtons.YesNo,
                MessageBoxIcon.Question
            );
            
            if (result == DialogResult.Yes)
            {
                try
                {
                    File.Delete(filePath);
                    LoadFiles(); // Refresh the list
                }
                catch (Exception ex)
                {
                    MessageBox.Show($"Could not delete file: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }
            }
        }

        private void OpenTempFolder()
        {
            try
            {
                System.Diagnostics.Process.Start(new System.Diagnostics.ProcessStartInfo
                {
                    FileName = "explorer.exe",
                    Arguments = tempFolder,
                    UseShellExecute = true
                });
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Could not open folder: {ex.Message}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error);
            }
        }

        private void ShowSettings()
        {
            using (var form = new Form())
            {
                form.Text = "TempDesk Settings";
                form.Size = new Size(500, 300);
                form.StartPosition = FormStartPosition.CenterParent;
                form.FormBorderStyle = FormBorderStyle.FixedDialog;
                form.MaximizeBox = false;
                form.MinimizeBox = false;

                var layout = new TableLayoutPanel
                {
                    Dock = DockStyle.Fill,
                    ColumnCount = 2,
                    RowCount = 6,
                    Padding = new Padding(10)
                };

                // Auto-delete setting
                layout.Controls.Add(new Label { Text = "Auto-delete files after:", Font = new Font("Arial", 9, FontStyle.Bold) }, 0, 0);
                layout.SetColumnSpan(layout.Controls[layout.Controls.Count - 1], 2);
                
                var daysSpinner = new NumericUpDown
                {
                    Minimum = 1,
                    Maximum = 365,
                    Value = Math.Max(1, autoDeleteDays),
                    Location = new Point(10, 30)
                };
                layout.Controls.Add(daysSpinner, 0, 1);
                layout.Controls.Add(new Label { Text = "days", Location = new Point(80, 30) }, 1, 1);

                // Folder setting
                layout.Controls.Add(new Label { Text = "Storage folder:", Font = new Font("Arial", 9, FontStyle.Bold) }, 0, 2);
                layout.SetColumnSpan(layout.Controls[layout.Controls.Count - 1], 2);
                
                var folderBox = new TextBox { Text = tempFolder, Width = 400 };
                layout.Controls.Add(folderBox, 0, 3);
                layout.SetColumnSpan(layout.Controls[layout.Controls.Count - 1], 2);

                // Browse button
                var browseBtn = new Button { Text = "Browse...", Width = 80 };
                browseBtn.Click += (s, e) => {
                    using (var dialog = new FolderBrowserDialog())
                    {
                        dialog.SelectedPath = tempFolder;
                        if (dialog.ShowDialog() == DialogResult.OK)
                        {
                            folderBox.Text = dialog.SelectedPath;
                        }
                    }
                };
                layout.Controls.Add(browseBtn, 0, 4);
                layout.SetColumnSpan(layout.Controls[layout.Controls.Count - 1], 2);

                // Buttons
                var okBtn = new Button { Text = "OK", DialogResult = DialogResult.OK, Width = 80 };
                var cancelBtn = new Button { Text = "Cancel", DialogResult = DialogResult.Cancel, Width = 80 };

                layout.Controls.Add(okBtn, 0, 5);
                layout.Controls.Add(cancelBtn, 1, 5);

                form.Controls.Add(layout);

                if (form.ShowDialog() == DialogResult.OK)
                {
                    autoDeleteDays = (int)daysSpinner.Value;
                    tempFolder = folderBox.Text;
                    SaveConfig();
                    CreateFileListView(); // Refresh explorer
                }
            }
        }

        private void StartCleanupTimer()
        {
            cleanupTimer = new System.Windows.Forms.Timer();
            cleanupTimer.Interval = 3600000; // 1 hour
            cleanupTimer.Tick += CleanupOldFiles;
            cleanupTimer.Start();
            CleanupOldFiles(this, EventArgs.Empty); // Initial cleanup
        }

        private void CleanupOldFiles(object sender, EventArgs e)
        {
            try
            {
                DateTime cutoffDate = DateTime.Now.AddDays(-autoDeleteDays);
                foreach (string filePath in Directory.GetFiles(tempFolder))
                {
                    DateTime fileTime = File.GetLastWriteTime(filePath);
                    if (fileTime < cutoffDate)
                    {
                        try
                        {
                            File.Delete(filePath);
                            Console.WriteLine($"Auto-deleted old file: {Path.GetFileName(filePath)}");
                        }
                        catch (Exception ex)
                        {
                            Console.WriteLine($"Error deleting old file {Path.GetFileName(filePath)}: {ex.Message}");
                        }
                    }
                }
                LoadFiles(); // Refresh the list after cleanup
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error during cleanup: {ex.Message}");
            }
        }

        protected override void OnFormClosing(FormClosingEventArgs e)
        {
            SaveConfig();
            trayIcon.Visible = false;
            trayIcon.Dispose();
            base.OnFormClosing(e);
        }

        protected override void OnResize(EventArgs e)
        {
            if (this.WindowState == FormWindowState.Minimized)
            {
                MinimizeToTray();
            }
            base.OnResize(e);
        }
    }

    static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new TempDeskForm());
        }
    }
} 