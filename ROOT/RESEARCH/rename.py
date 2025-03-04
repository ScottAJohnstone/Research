from encodings import johab
import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinter.simpledialog import askstring
from datetime import datetime, timedelta
import time

jobnum="5700"
class BulkRenamer:
    def __init__(self, root):
        self.root = root
        self.root.title("Renaning Suite")
        stht = 400
        stwi = 800
        screenht = self.root.winfo_screenheight()
        screenwi = self.root.winfo_screenwidth()
        x = (screenwi / 2) - (stwi / 2)
        y = (screenht / 2) - (stht / 2)
        self.root.geometry(f'{stwi}x{stht}+{int(x)}+{int(y)}')
        self.root.resizable(False, False)

        
        # Set window size
        #self.root.geometry("800x400")
        
        # Initialize variables for prefix, suffix, and checkbox state
        self.prefix = tk.StringVar(value=f'{jobnum}_')                    #- need to set default values ; job num
        self.suffix = tk.StringVar(value="")                    #- need to set default values ; 
        self.custom_attributes = tk.BooleanVar(value=False)  # Variable for the custom attributes toggle
        
        # Set default folder path to Downloads
        self.default_folder = os.path.expanduser('~') + '/Downloads'
        self.files = []  # To store recent files (files loaded from the default folder)
        self.selected_files = []  # To store manually selected files

        # Set up UI
        self.setup_ui()

        # Automatically load recent files from the Downloads folder
        self.load_recent_files()

    def setup_ui(self):
        # Create buttons (place them next to each other)
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        # Button frame alignment to the right
        self.configure_button = tk.Button(button_frame, text="Configure", command=self.open_configure_window)
        self.configure_button.pack(side=tk.RIGHT, padx=10)

        self.execute_button = tk.Button(button_frame, text="Execute Bulk Renaming", command=self.execute_rename, state=tk.DISABLED)
        self.execute_button.pack(side=tk.RIGHT, padx=10)

        self.select_files_button = tk.Button(button_frame, text="Select Files", command=self.select_files)
        self.select_files_button.pack(side=tk.RIGHT, padx=10)

        # Create Treeview to show file names
        self.treeview = ttk.Treeview(self.root, columns=("Original", "Proposed"), show="headings")
        self.treeview.heading("Original", text="Original Filename")
        self.treeview.heading("Proposed", text="Proposed Filename")
        self.treeview.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Bind double-click on proposed file names to manually rename them
        self.treeview.bind("<Double-1>", self.on_proposed_name_click)

    def select_files(self):
        # Allow user to manually select files using a file dialog
        file_paths = [f for f in filedialog.askopenfilenames(title="Select Files", filetypes=[("All Files", "*.*")]) 
              if not os.path.basename(f).startswith(".") and not os.path.basename(f) == ".DS_Store"]

        if file_paths:
            # Clear the current files list and save the manually selected files
            self.selected_files = [(file_path, os.path.basename(file_path)) for file_path in file_paths]
            self.files = []  # Clear recent files as we are working only with the manually selected files
            self.apply_rename_logic()  # Apply renaming logic automatically
            self.populate_treeview()

    def open_configure_window(self):
        # Check if the window already exists and is still open
        if hasattr(self, "configure_window") and self.configure_window.winfo_exists():
            self.configure_window.lift()  # Bring existing window to front
            return  # Stop from opening another window

        self.configure_window = tk.Toplevel(self.root)  # Store as an instance attribute
        self.configure_window.title("Configure Default Settings")
        self.configure_window.geometry("590x180")  # Adjusted for compact view

        # Create a frame to hold everything in a grid layout
        config_frame = tk.Frame(self.configure_window)
        config_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Path selection (Row 0)
        path_label = tk.Label(config_frame, text="Default Folder Path:")
        path_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

        self.path_entry = tk.Entry(config_frame, width=30)
        self.path_entry.grid(row=0, column=1, padx=5, pady=5)
        self.path_entry.insert(0, self.default_folder if self.default_folder else "")

        browse_button = tk.Button(config_frame, text="Browse Folders", command=self.browse_folder)
        browse_button.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)

        # Prefix setting (Row 1)
        self.prefix_label = tk.Label(config_frame, text="Default Prefix:")
        self.prefix_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)

        self.prefix_entry = tk.Entry(config_frame, textvariable=self.prefix, width=30)
        self.prefix_entry.grid(row=1, column=1, padx=5, pady=5)

        self.apply_button = tk.Button(config_frame, text="Apply Changes", command=self.apply_changes)
        self.apply_button.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W, ipadx=1)

        # Suffix setting (Row 2)
        self.suffix_label = tk.Label(config_frame, text="Default Suffix:")
        self.suffix_label.grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)

        self.suffix_entry = tk.Entry(config_frame, textvariable=self.suffix, width=30)
        self.suffix_entry.grid(row=2, column=1, padx=5, pady=5)

        self.cancel_button = tk.Button(config_frame, text="Cancel", command=self.configure_window.destroy)
        self.cancel_button.grid(row=2, column=2, padx=5, pady=5, ipadx=26, sticky=tk.W)

        # Checkbox to enable custom prefix/suffix (Row 3)
        self.custom_attributes_checkbox = tk.Checkbutton(config_frame, text="Enable Custom Prefix/Suffix", variable=self.custom_attributes)
        self.custom_attributes_checkbox.grid(row=3, columnspan=3, padx=5, pady=5, sticky=tk.W)

    def browse_folder(self):
        folder_path = filedialog.askdirectory(title="Select Folder")
        if folder_path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder_path)
            self.default_folder = folder_path  # Update the folder path
            self.load_recent_files()  # Reload files based on the new folder path

    def apply_changes(self):
        folder_path = self.path_entry.get()
        if not folder_path:
            messagebox.showwarning("No Folder", "Please select a folder.")
            return

        # Update the default folder path
        self.default_folder = folder_path

        # Apply prefix and suffix based on checkbox state
        if self.custom_attributes.get():
            self.apply_prefix_suffix()
        else:
            self.remove_prefix_suffix()

        # Repopulate the treeview with updated filenames
        self.populate_treeview()

        # Destroy the configure_window if it exists
        if hasattr(self, "configure_window") and self.configure_window.winfo_exists():
            self.configure_window.destroy()

    def apply_prefix_suffix(self):
        # Apply renaming logic based on prefix and suffix
        all_files = self.selected_files + self.files  # Combine both lists for processing
        for i, (file_path, original_name) in enumerate(all_files):
            name, ext = os.path.splitext(original_name)

            # Apply prefix and suffix if the checkbox is checked
            prefix = self.prefix.get() if self.prefix.get() else ""
            suffix = self.suffix.get() if self.suffix.get() else ""

            # Add prefix and suffix if they are not already present
            if not name.startswith(prefix):
                name = prefix + name
            if not name.endswith(suffix):
                name = name + suffix

            # Update the filenames
            proposed_name = name + ext

            if i < len(self.selected_files):
                self.selected_files[i] = (file_path, proposed_name)
            else:
                self.files[i - len(self.selected_files)] = (file_path, proposed_name)

    def remove_prefix_suffix(self):
        # Remove the prefix and suffix only if they exist and are not empty
        all_files = self.selected_files + self.files  # Combine both lists for processing
        for i, (file_path, original_name) in enumerate(all_files):
            name, ext = os.path.splitext(original_name)

            # Only remove the prefix if it is set and present
            if self.prefix.get() and name.startswith(self.prefix.get()):
                name = name[len(self.prefix.get()):]

            # Only remove the suffix if it is set and present
            if self.suffix.get() and name.endswith(self.suffix.get()):
                name = name[:-len(self.suffix.get())]

            # Update the filenames
            proposed_name = name + ext

            if i < len(self.selected_files):
                self.selected_files[i] = (file_path, proposed_name)
            else:
                self.files[i - len(self.selected_files)] = (file_path, proposed_name)

    def apply_rename_logic(self):
        # Only apply renaming to manually selected files or recently loaded files
        all_files = self.selected_files + self.files  # Combine both lists for processing
        for i, (file_path, original_name) in enumerate(all_files):
            name, ext = os.path.splitext(original_name)

            # First, apply special renaming logic for number-only and hyphen filenames
            if name.isdigit():
                proposed_name = f"Map #{name}" + ext
            elif '-' in name:
                parts = name.split('-')
                # Ensures both parts before and after the "-" are numeric
                if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                    proposed_name = f"Vol.{parts[0]} - Pg.{parts[1]}" + ext
                else:
                    # Default renaming behavior
                    proposed_name = name + ext
            else:
                # Default renaming behavior
                proposed_name = name + ext

            # Update the filenames in the appropriate list
            if i < len(self.selected_files):
                self.selected_files[i] = (file_path, proposed_name)
            else:
                self.files[i - len(self.selected_files)] = (file_path, proposed_name)

    def load_recent_files(self):
        # Load files from the last hour in the specified folder ; default is downloads
        if not self.default_folder:
            messagebox.showwarning("No Folder", "Please set a default folder.")
            return
        try:
            current_time = datetime.now()
            time_limit = current_time - timedelta(hours=1)

            files_in_folder = [
                os.path.join(self.default_folder, f) for f in os.listdir(self.default_folder)
                if os.path.isfile(os.path.join(self.default_folder, f)) and not f.startswith('.')
            ]

            # Filter files based on their creation time (only files added within the last hour)
            self.files = [
                (f, os.path.basename(f)) for f in files_in_folder
                if datetime.fromtimestamp(os.path.getctime(f)) > time_limit
            ]

            if not self.files:
                response = messagebox.askyesno("No recent files found", "No recent files found.Would you like to select files manually?")
                if response is True:
                    self.select_files()                
                elif response is False:
                    return
                else:
                    return
                
            # Automatically apply rename logic to loaded files
            self.apply_rename_logic()
            self.populate_treeview()

        except FileNotFoundError:
            messagebox.showerror("Error", "Selected folder not found!")

    def populate_treeview(self):
        # Clear the existing data in the treeview
        for row in self.treeview.get_children():
            self.treeview.delete(row)

        # Use either selected or recent files
        all_files = self.selected_files + self.files

        for file_path, proposed_name in all_files:
            original_name = os.path.basename(file_path)
            self.treeview.insert("", "end", values=(original_name, proposed_name))

        # Enable the execute button once files are selected
        self.execute_button.config(state=tk.NORMAL)

    def execute_rename(self):
        # Execute the renaming logic
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
def main():
    root = tk.Tk()
    app = BulkRenamer(root)
    root.mainloop()
    
if __name__ == "__main__":
    main()
