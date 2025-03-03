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
        
        # Initialize variables for prefix, suffix, and checkbox state
        self.prefix = tk.StringVar()
        self.suffix = tk.StringVar()
        self.custom_attributes = tk.BooleanVar(value=False)  # Variable for the custom attributes toggle
        self.default_folder = None
        self.files = []

        # Set up UI
        self.setup_ui()

        # Automatically load recent files from the Downloads folder
        self.load_recent_files()

    def setup_ui(self):
        # Create buttons (place them next to each other)
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)

        self.select_files_button = tk.Button(button_frame, text="Select Files", command=self.select_files)
        self.select_files_button.pack(side=tk.LEFT, padx=10)

        self.execute_button = tk.Button(button_frame, text="Execute Bulk Renaming", command=self.execute_rename, state=tk.DISABLED)
        self.execute_button.pack(side=tk.LEFT, padx=10)

        self.configure_button = tk.Button(button_frame, text="Configure", command=self.open_configure_window)
        self.configure_button.pack(side=tk.LEFT, padx=10)

        # Create Treeview to show file names
        self.treeview = ttk.Treeview(self.root, columns=("Original", "Proposed"), show="headings")
        self.treeview.heading("Original", text="Original Filename")
        self.treeview.heading("Proposed", text="Proposed Filename")
        self.treeview.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Bind double-click on proposed file names to manually rename them
        self.treeview.bind("<Double-1>", self.on_proposed_name_click)

    def select_files(self):
        # Allow user to manually select files using a file dialog
        file_paths = filedialog.askopenfilenames(title="Select Files", filetypes=[("All Files", "*.*")])
        if file_paths:
            self.files = file_paths  # Completely replace the old list with new files
            self.populate_treeview()

    def open_configure_window(self):
        configure_window = tk.Toplevel(self.root)
        configure_window.title("Configure Default Settings")
        configure_window.geometry("300x300")

        # Path selection
        path_label = tk.Label(configure_window, text="Default Folder Path:")
        path_label.pack(pady=10)

        self.path_entry = tk.Entry(configure_window, width=30)
        self.path_entry.pack(pady=5)
        self.path_entry.insert(0, self.default_folder if self.default_folder else "")

        # Prefix and Suffix settings
        prefix_label = tk.Label(configure_window, text="Default Prefix:")
        prefix_label.pack(pady=5)
        self.prefix_entry = tk.Entry(configure_window, textvariable=self.prefix, width=30)
        self.prefix_entry.pack(pady=5)

        suffix_label = tk.Label(configure_window, text="Default Suffix:")
        suffix_label.pack(pady=5)
        self.suffix_entry = tk.Entry(configure_window, textvariable=self.suffix, width=30)
        self.suffix_entry.pack(pady=5)

        # Checkbox to enable custom prefix/suffix
        custom_attributes_checkbox = tk.Checkbutton(configure_window, text="Enable Custom Prefix/Suffix", variable=self.custom_attributes)
        custom_attributes_checkbox.pack(pady=5)

        # Buttons to apply and cancel
        apply_button = tk.Button(configure_window, text="Apply Changes", command=self.apply_changes)
        apply_button.pack(side=tk.LEFT, padx=20, pady=10)

        cancel_button = tk.Button(configure_window, text="Cancel", command=configure_window.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=20, pady=10)

    def apply_changes(self):
        # Apply changes to the current files based on new prefix/suffix and path
        folder_path = self.path_entry.get()
        if not folder_path:
            messagebox.showwarning("No Folder", "Please select a folder.")
            return

        # Set the default folder path
        self.default_folder = folder_path

        # Reload the recent files based on the new folder path
        self.load_recent_files()

        # Apply renaming logic with the new prefix/suffix
        self.apply_rename_logic()

        # Repopulate the treeview with updated filenames
        self.populate_treeview()

    def apply_rename_logic(self):
        for i, file_path in enumerate(self.files):
            original_name = os.path.basename(file_path)
            name, ext = os.path.splitext(original_name)

            # Apply the prefix and suffix if the checkbox is checked
            if self.custom_attributes.get():
                prefix = self.prefix.get() if self.prefix.get() else ""
                suffix = self.suffix.get() if self.suffix.get() else ""
            else:
                prefix = ""
                suffix = ""

            # Construct the new proposed name
            proposed_name = prefix + name + suffix + ext
            self.files[i] = (file_path, proposed_name)

    def load_recent_files(self):
        # Load files from the last hour in the specified folder
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
                f for f in files_in_folder
                if datetime.fromtimestamp(os.path.getctime(f)) > time_limit
            ]

            if not self.files:
                messagebox.showwarning("No Recent Files", "No files found from the last hour.")

        except FileNotFoundError:
            messagebox.showerror("Error", "Selected folder not found!")

    def populate_treeview(self):
        # Clear the existing data in the treeview
        for row in self.treeview.get_children():
            self.treeview.delete(row)

        for file_path, proposed_name in self.files:
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
