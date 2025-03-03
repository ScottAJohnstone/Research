import os
import tkinter as tk
from tkinter import ttk
from tkinter import ttk, filedialog, messagebox

class BulkRenameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Bulk File Renamer")
        self.root.geometry("990x400")

        # Counter for active entry widgets
        self.active_entry_count = 0

        # Frame for organizing layout
        self.frame = tk.Frame(root)
        self.frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Directory and file selection
        self.dir_label = tk.Label(self.frame, text="Select Directory or Files for Renaming:")
        self.dir_label.grid(row=0, column=0, sticky="w")

        self.dir_entry = tk.Entry(self.frame, width=50)
        self.dir_entry.grid(row=0, column=1, padx=5)

        self.browse_files_button = tk.Button(self.frame, text="Add Files", command=self.browse_files)
        self.browse_files_button.grid(row=0, column=2, pady=(0, 5), padx=5, ipadx=16)

        self.browse_dir_button = tk.Button(self.frame, text="Add Directory", command=self.browse_directory)
        self.browse_dir_button.grid(row=0, column=3, pady=(0, 5), padx=(0, 5))

        # Treeview for original and new file names
        self.treeview = ttk.Treeview(self.frame, columns=("Original", "New"), show="headings", height=15)
        self.treeview.heading("Original", text="Original Filename")
        self.treeview.heading("New", text="Previewed New Filename")
        self.treeview.column("Original", width=350, anchor="w")
        self.treeview.column("New", width=350, anchor="w")
        self.treeview.grid(row=1, column=0, columnspan=4, sticky="nsew")

        # Scrollbar
        self.scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.treeview.yview)
        self.treeview.configure(yscroll=self.scrollbar.set)
        self.scrollbar.grid(row=1, column=4, sticky="ns")

        # Rename button
        self.rename_button = tk.Button(self.frame, text="Rename Files", command=self.rename_files)
        self.rename_button.grid(row=2, column=0, columnspan=5, pady=10)

        # Track selected files
        self.selected_files = []

        # Variables for editing new filenames
        self.new_name_entry = None
        self.current_item = None

        # Binding double-click for editing
        self.treeview.bind("<Double-1>", self.start_edit)

    def browse_directory(self):
        """Open a dialog to select a directory."""
        dir_path = filedialog.askdirectory()
        if dir_path:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(tk.END, dir_path)
            self.populate_treeview(dir_path)

    def browse_files(self):
        """Open a dialog to select multiple files."""
        files = filedialog.askopenfilenames(title="Select Files")
        if files:
            self.populate_treeview(files)

    def populate_treeview(self, paths):
        """Populate the treeview with filenames from the selected directory or files."""
        self.treeview.delete(*self.treeview.get_children())
        self.selected_files = []  # Reset selected files

        if isinstance(paths, str):  # If a directory was selected
            for filename in os.listdir(paths):
                if os.path.isfile(os.path.join(paths, filename)):
                    new_name = self.generate_new_name(filename)
                    self.treeview.insert("", "end", values=(filename, new_name))
                    self.selected_files.append(os.path.join(paths, filename))
        else:  # If files were selected
            for filepath in paths:
                filename = os.path.basename(filepath)
                new_name = self.generate_new_name(filename)
                self.treeview.insert("", "end", values=(filename, new_name))
                self.selected_files.append(filepath)  # Track the full file paths

    def generate_new_name(self, filename):
        """Generate a new name for the file."""
        name, ext = os.path.splitext(filename)
        return f"{name}_new{ext}"

    def start_edit(self, event):
        """Start editing the selected new filename in the Treeview."""
        item = self.treeview.selection()
        if not item:
            return  # No item selected; avoid potential errors

        # Check if there's already an active entry
        if self.active_entry_count > 0:
            messagebox.showwarning("Warning", "Please finish editing the current entry before starting a new one.")
            return

        self.current_item = item[0]
        column = self.treeview.identify_column(event.x)
        x, y, width, height = self.treeview.bbox(self.current_item, column)
        value = self.treeview.item(self.current_item, "values")[1]

        # Create and track the entry widget
        self.new_name_entry = tk.Entry(self.treeview, width=30)
        self.new_name_entry.insert(0, value)
        self.new_name_entry.select_range(0, tk.END)
        self.new_name_entry.focus()
        self.active_entry_count += 1  # Increment active entry count

        # Place the entry widget and bind the return key
        self.new_name_entry.place(x=x, y=y, width=width, height=height)
        self.new_name_entry.bind("<Return>", self.save_edit)
        self.new_name_entry.bind("<FocusOut>", self.save_edit)

    def save_edit(self, event=None):
        """Save edited name back to the Treeview and remove the Entry widget."""
        if self.new_name_entry is not None:
            new_name = self.new_name_entry.get()
            self.treeview.item(self.current_item, values=(self.treeview.item(self.current_item, "values")[0], new_name))
            self.treeview.item(self.current_item, tags=('edited',))

            # Clean up the entry widget
            self.new_name_entry.destroy()
            self.new_name_entry = None
            self.current_item = None
            self.active_entry_count -= 1  # Decrement active entry count

    def rename_files(self):
        """Rename the files based on the new names in the Treeview."""
        if not self.selected_files:
            messagebox.showerror("Error", "No files selected for renaming.")
            return

        for i, item in enumerate(self.treeview.get_children()):
            original_name = self.treeview.item(item, "values")[0]
            new_name = self.treeview.item(item, "values")[1]
            original_path = self.selected_files[i]
            new_path = os.path.join(os.path.dirname(original_path), new_name)

            if original_path != new_path:
                try:
                    os.rename(original_path, new_path)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to rename {original_name} to {new_name}: {e}")

        messagebox.showinfo("Success", "Files renamed successfully.")
        # Refresh the treeview
        self.populate_treeview(os.path.dirname(self.selected_files[0]))

# Running the app
if __name__ == "__main__":
    root = tk.Tk()
    app = BulkRenameApp(root)
    root.mainloop()




'''i need a python tkinter treeview program. it should function as a bulk file renamer. it should allow the user to navigate to a folder or sekect individual files to allow the renaming of them. once files are selected. it should show a treeview of all the files as is as well as a preview of what the new file names should be. the existing names shpuld be locked for editing but the previewed names should allow the user to individually edit each file name. please display the file name previews in blue'''