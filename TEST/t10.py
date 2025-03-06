import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinter.simpledialog import askstring
from datetime import datetime, timedelta


class BulkRenamer:
    def __init__(self, root):
        self.root = root
        self.root.title("Bulk File Renamer")
        
        # Set window size (wider than tall)
        self.root.geometry("800x400")  # Width is 800px, Height is 400px
        
        # Set the default download folder path (can be changed by the user)
        self.default_folder = os.path.expanduser('~') + '/Downloads'
        
        # Set up UI
        self.setup_ui()
        
        # Default list of files
        self.files = []

        # Load files from the default folder
        self.load_files_from_folder()

    def setup_ui(self):
        # Create buttons (place them next to each other)
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        
        self.select_files_button = tk.Button(button_frame, text="Select Alternate Files", command=self.select_files)
        self.select_files_button.pack(side=tk.LEFT, padx=10)
        
        self.execute_button = tk.Button(button_frame, text="Execute Bulk Renaming", command=self.execute_rename, state=tk.DISABLED)
        self.execute_button.pack(side=tk.LEFT, padx=10)
        
        self.set_folder_button = tk.Button(button_frame, text="Set Default Folder", command=self.set_default_folder)
        self.set_folder_button.pack(side=tk.LEFT, padx=10)
        
        # Create Treeview to show file names
        self.treeview = ttk.Treeview(self.root, columns=("Original", "Proposed"), show="headings")
        self.treeview.heading("Original", text="Original Filename")
        self.treeview.heading("Proposed", text="Proposed Filename")
        self.treeview.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Bind double-click on proposed file names to manually rename them
        self.treeview.bind("<Double-1>", self.on_proposed_name_click)
    
    def load_files_from_folder(self):
        # Load files from the default folder
        downloads_folder = self.default_folder
        
        try:
            # Get the current time and subtract 1 hour to define the time range
            current_time = datetime.now()
            time_limit = current_time - timedelta(hours=1)

            files_in_folder = [
                os.path.join(downloads_folder, f) for f in os.listdir(downloads_folder)
                if os.path.isfile(os.path.join(downloads_folder, f)) and not f.startswith('.')
            ]
            
            # Filter files based on their creation time (only files added within the last hour)
            recent_files = [
                f for f in files_in_folder
                if datetime.fromtimestamp(os.path.getctime(f)) > time_limit
            ]
            
            if recent_files:
                self.files = recent_files
                self.populate_treeview()
                return
            
        except FileNotFoundError:
            messagebox.showerror("Error", f"Folder {downloads_folder} not found!")
            return

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

        # Check if the filename contains only numbers (excluding the extension)
        if name.isdigit():
            return f"Map #{name}" + ext
        
        # Check if the filename contains a "-"
        elif '-' in name:
            # Split the name around the "-"
            parts = name.split('-')
            
            # Ensure the parts before and after the "-" are numeric
            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                return f"Vol.{parts[0]} - Pg.{parts[1]}" + ext
        
        # Default renaming behavior (add "_rnm" to the file name)
        return name + ext

    def select_files(self):
        # Allow user to manually select files using a file dialog
        file_paths = filedialog.askopenfilenames(title="Select Files", filetypes=[("All Files", "*.*")])
        if file_paths:
            self.files = file_paths  # Completely replace the old list with new files
            self.populate_treeview()

    def execute_rename(self):
        for item in self.treeview.get_children():
            original_name, proposed_name = self.treeview.item(item, "values")
            original_path = os.path.join(self.default_folder, original_name)
            proposed_path = os.path.join(self.default_folder, proposed_name)
            
            if original_name != proposed_name:  # Rename only if changed
                try:
                    os.rename(original_path, proposed_path)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to rename {original_name}: {e}")
                    return
        
        messagebox.showinfo("Success", "Bulk renaming executed successfully!")

        # Clear the Treeview contents after renaming
        self.files = []
        self.populate_treeview()

    def on_proposed_name_click(self, event):
        item = self.treeview.identify('item', event.x, event.y)
        if item:
            original_name, proposed_name = self.treeview.item(item, "values")
            
            # Get the file name and extension
            name, ext = os.path.splitext(proposed_name)

            # Show the full filename, but highlight only the name part (not the extension)
            new_name = askstring("Edit Filename", "Edit the proposed name:", initialvalue=name)
            
            if new_name is not None:
                # Update the proposed name with the new value, keep the extension unchanged
                self.treeview.item(item, values=(original_name, new_name + ext))

                # Update the execution button state if filenames have changed
                self.execute_button.config(state=tk.NORMAL)

    def set_default_folder(self):
        # Ask the user to select a new default folder
        folder_path = filedialog.askdirectory(title="Select Default Folder")
        if folder_path:
            self.default_folder = folder_path
            messagebox.showinfo("Folder Set", f"Default folder set to: {folder_path}")
            
            # Clear the current files list and reload files from the new folder
            self.files = []
            self.load_files_from_folder()


def main():
    root = tk.Tk()
    app = BulkRenamer(root)
    root.mainloop()

if __name__ == "__main__":
    main()
