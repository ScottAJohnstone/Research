import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinter.simpledialog import askstring
from datetime import datetime

class BulkRenamer:
    def __init__(self, root):
        self.root = root
        self.root.title("Bulk File Renamer")
        
        # Set up UI
        self.setup_ui()
        
        # Default list of files
        self.files = []

        # Automatically load recent files from Downloads folder
        self.load_recent_files()

    def setup_ui(self):
        # Create buttons
        self.select_files_button = tk.Button(self.root, text="Select Alternate Files", command=self.select_files)
        self.select_files_button.pack(pady=10)
        
        self.execute_button = tk.Button(self.root, text="Execute Bulk Renaming", command=self.execute_rename, state=tk.DISABLED)
        self.execute_button.pack(pady=10)
        
        # Create Treeview to show file names
        self.treeview = ttk.Treeview(self.root, columns=("Original", "Proposed"), show="headings")
        self.treeview.heading("Original", text="Original Filename")
        self.treeview.heading("Proposed", text="Proposed Filename")
        self.treeview.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Bind double-click on proposed file names to manually rename them
        self.treeview.bind("<Double-1>", self.on_proposed_name_click)
        
    def load_recent_files(self):
        # Attempt to auto-select recent files from Downloads folder
        downloads_folder = os.path.expanduser('~') + '/Downloads'
        
        try:
            files_in_downloads = [os.path.join(downloads_folder, f) for f in os.listdir(downloads_folder) if os.path.isfile(os.path.join(downloads_folder, f))]
            files_in_downloads.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Check if there are recent files with the same timestamp
            recent_files = self.get_recent_files_with_same_timestamp(files_in_downloads)
            if recent_files:
                self.files = recent_files
                self.populate_treeview()
                return
            
        except FileNotFoundError:
            messagebox.showerror("Error", "Downloads folder not found!")
            return

    def get_recent_files_with_same_timestamp(self, files):
        if not files:
            return []
        
        # Get the most recent file's timestamp
        latest_time = os.path.getmtime(files[0])
        
        # Filter out files that have the same timestamp as the most recent file
        recent_files = [f for f in files if abs(os.path.getmtime(f) - latest_time) < 1]
        
        return recent_files
    
    def populate_treeview(self):
        # Clear the existing data in the treeview
        for row in self.treeview.get_children():
            self.treeview.delete(row)
        
        for file in self.files:
            original_name = os.path.basename(file)
            proposed_name = self.rename_file(original_name)
            self.treeview.insert("", "end", values=(original_name, proposed_name))

        # Enable the execute button once files are selected
        self.execute_button.config(state=tk.NORMAL)

    def rename_file(self, original_name):
        name, ext = os.path.splitext(original_name)
        return name + "_rnm" + ext
    
    def select_files(self):
        # Allow user to manually select files using a file dialog
        file_paths = filedialog.askopenfilenames(title="Select Files", filetypes=[("All Files", "*.*")])
        if file_paths:
            self.files = file_paths  # Completely replace the old list with new files
            self.populate_treeview()

    def execute_rename(self):
        for item in self.treeview.get_children():
            original_name, proposed_name = self.treeview.item(item, "values")
            original_path = os.path.join(os.path.expanduser('~'), 'Downloads', original_name)
            proposed_path = os.path.join(os.path.expanduser('~'), 'Downloads', proposed_name)
            
            if original_name != proposed_name:  # Rename only if changed
                try:
                    os.rename(original_path, proposed_path)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to rename {original_name}: {e}")
                    return
        
        messagebox.showinfo("Success", "Bulk renaming executed successfully!")
    
    def on_proposed_name_click(self, event):
        item = self.treeview.identify('item', event.x, event.y)
        if item:
            original_name, proposed_name = self.treeview.item(item, "values")
            
            # Prompt user for new proposed filename
            new_name = askstring("Rename Proposed Filename", f"Edit the proposed name for {original_name}:", initialvalue=proposed_name)
            if new_name:
                self.treeview.item(item, values=(original_name, new_name))
    
def main():
    root = tk.Tk()
    app = BulkRenamer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
