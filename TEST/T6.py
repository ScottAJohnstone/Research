import os
import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime, timedelta  # Added timedelta here

class FileSelectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Selector")
        
        # Add button to select directory
        self.select_dir_button = tk.Button(self.root, text="Select Directory", command=self.select_directory)
        self.select_dir_button.pack(pady=10)

        # Listbox to display the most recent files
        self.file_listbox = tk.Listbox(self.root, selectmode=tk.MULTIPLE, width=50, height=10)
        self.file_listbox.pack(pady=10)

        # Button to confirm file selection
        self.select_button = tk.Button(self.root, text="Select Files", command=self.select_files)
        self.select_button.pack(pady=10)

        # Directory path and file list
        self.directory = ""
        self.files = []

    def select_directory(self):
        # Ask user to select directory
        directory = filedialog.askdirectory(title="Select a Directory")
        
        if directory:
            self.directory = directory
            self.list_recent_files()

    def list_recent_files(self):
        # Get files from the selected directory
        self.files = []
        try:
            for filename in os.listdir(self.directory):
                file_path = os.path.join(self.directory, filename)
                if os.path.isfile(file_path):
                    modified_time = os.path.getmtime(file_path)
                    modified_time = datetime.fromtimestamp(modified_time)
                    # Only consider files modified in the last 24 hours (change the delta as needed)
                    if modified_time > datetime.now() - timedelta(days=1):
                        self.files.append((filename, modified_time))

            # Sort files by modification time, descending
            self.files.sort(key=lambda x: x[1], reverse=True)

            # Update listbox with the most recent files
            self.file_listbox.delete(0, tk.END)
            for file, mod_time in self.files:
                formatted_time = mod_time.strftime("%Y-%m-%d %H:%M:%S")
                self.file_listbox.insert(tk.END, f"{file} - {formatted_time}")

        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while listing files: {str(e)}")

    def select_files(self):
        # Get selected files from the listbox
        selected_indices = self.file_listbox.curselection()
        selected_files = [self.files[i][0] for i in selected_indices]
        
        if selected_files:
            messagebox.showinfo("Selected Files", f"You selected: {', '.join(selected_files)}")
        else:
            messagebox.showwarning("No Selection", "No files selected.")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileSelectorApp(root)
    root.mainloop()
