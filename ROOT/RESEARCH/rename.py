import re
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from tkinter.simpledialog import askstring
import os
from datetime import datetime, timedelta

jobnum = "5700"

class BulkRenamer:
    def __init__(self, root):
        self.root = root

        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", background="#4CAF50", font=('Arial', 10))
        self.style.configure("TLabel", font=('Arial', 10))

        self.prefix = tk.StringVar(value=f'{jobnum}_')                    
        self.suffix = tk.StringVar(value="")
        self.custom_attributes = tk.BooleanVar(value=False)

        self.default_folder = os.path.expanduser('~') + '/Downloads'
        self.files = []
        self.selected_files = []

        self.setup_ui()
        #self.load_recent_files()

    def setup_ui(self):
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=10)
        #button_frame.cget()
        #button_frame.configure(background=notebook.cget("background"))


        self.configure_button = tk.Button(button_frame, text="Configure", command=self.open_configure_window)
        self.configure_button.pack(side=tk.RIGHT, padx=10)

        self.execute_button = tk.Button(button_frame, text="Execute Bulk Renaming", command=self.execute_rename)#, state=tk.DISABLED
        self.execute_button.pack(side=tk.RIGHT, padx=10)

        self.select_files_button = tk.Button(button_frame, text="Select Files", command=self.select_files)
        self.select_files_button.pack(side=tk.RIGHT, padx=10)
        self.select_files_button.bind("<Button-2>", self.load_recent_files)


        self.treeview = ttk.Treeview(self.root, columns=("Original", "Proposed"), show="headings")
        self.treeview.heading("Original", text="Original Filename")
        self.treeview.heading("Proposed", text="Proposed Filename")
        self.treeview.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.treeview.bind("<Double-1>", self.on_proposed_name_click)
        self.treeview.tag_configure("rename_valid", foreground="blue")
        self.treeview.tag_configure("rename_invalid", foreground="red")

    def select_files(self):
        file_paths = [f for f in filedialog.askopenfilenames(title="Select Files", filetypes=[("All Files", "*.*")]) 
                      if not os.path.basename(f).startswith(".") and not os.path.basename(f) == ".DS_Store"]

        if file_paths:
            self.selected_files = [(file_path, os.path.basename(file_path)) for file_path in file_paths]
            self.files = []
            self.apply_rename_logic()
            self.populate_treeview()

    def open_configure_window(self):
        if hasattr(self, "configure_window") and self.configure_window.winfo_exists():
            self.configure_window.lift()
            return

        self.configure_window = tk.Toplevel(self.root)
        self.configure_window.title("Configure Default Settings")
        self.configure_window.geometry("590x180")
        config_frame = tk.Frame(self.configure_window)
        config_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        path_label = tk.Label(config_frame, text="Default Folder Path:")
        path_label.grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)

        self.path_entry = tk.Entry(config_frame, width=30)
        self.path_entry.grid(row=0, column=1, padx=5, pady=5)
        self.path_entry.insert(0, self.default_folder if self.default_folder else "")

        browse_button = tk.Button(config_frame, text="Browse Folders", command=self.browse_folder)
        browse_button.grid(row=0, column=2, padx=5, pady=5, sticky=tk.W)

        self.prefix_label = tk.Label(config_frame, text="Default Prefix:")
        self.prefix_label.grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)

        self.prefix_entry = tk.Entry(config_frame, textvariable=self.prefix, width=30)
        self.prefix_entry.grid(row=1, column=1, padx=5, pady=5)

        self.apply_button = tk.Button(config_frame, text="Apply Changes", command=self.apply_changes)
        self.apply_button.grid(row=1, column=2, padx=5, pady=5, sticky=tk.W, ipadx=1)

        self.suffix_label = tk.Label(config_frame, text="Default Suffix:")
        self.suffix_label.grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)

        self.suffix_entry = tk.Entry(config_frame, textvariable=self.suffix, width=30)
        self.suffix_entry.grid(row=2, column=1, padx=5, pady=5)

        self.cancel_button = tk.Button(config_frame, text="Cancel", command=self.configure_window.destroy)
        self.cancel_button.grid(row=2, column=2, padx=5, pady=5, ipadx=26, sticky=tk.W)

        self.custom_attributes_checkbox = tk.Checkbutton(config_frame, text="Enable Custom Prefix/Suffix", variable=self.custom_attributes)
        self.custom_attributes_checkbox.grid(row=3, columnspan=3, padx=5, pady=5, sticky=tk.W)

    def browse_folder(self):
        folder_path = filedialog.askdirectory(title="Select Folder")
        if folder_path:
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, folder_path)
            self.default_folder = folder_path
            self.load_recent_files()

    def apply_changes(self):
        folder_path = self.path_entry.get()
        if not folder_path:
            messagebox.showwarning("No Folder", "Please select a folder.")
            return
        self.default_folder = folder_path
        if self.custom_attributes.get():
            self.apply_prefix_suffix()
        else:
            self.remove_prefix_suffix()
        self.populate_treeview()
        if hasattr(self, "configure_window") and self.configure_window.winfo_exists():
            self.configure_window.destroy()

    def apply_prefix_suffix(self):
        all_files = self.selected_files + self.files
        for i, (file_path, original_name) in enumerate(all_files):
            name, ext = os.path.splitext(original_name)
            prefix = self.prefix.get() if self.prefix.get() else ""
            suffix = self.suffix.get() if self.suffix.get() else ""
            if not name.startswith(prefix):
                name = prefix + name
            if not name.endswith(suffix):
                name = name + suffix
            proposed_name = name + ext
            if i < len(self.selected_files):
                self.selected_files[i] = (file_path, proposed_name)
            else:
                self.files[i - len(self.selected_files)] = (file_path, proposed_name)

    def remove_prefix_suffix(self):
        all_files = self.selected_files + self.files
        for i, (file_path, original_name) in enumerate(all_files):
            name, ext = os.path.splitext(original_name)
            if self.prefix.get() and name.startswith(self.prefix.get()):
                name = name[len(self.prefix.get()):]
            if self.suffix.get() and name.endswith(self.suffix.get()):
                name = name[:-len(self.suffix.get())]
            proposed_name = name + ext
            if i < len(self.selected_files):
                self.selected_files[i] = (file_path, proposed_name)
            else:
                self.files[i - len(self.selected_files)] = (file_path, proposed_name)

    def load_recent_files(self,event=None):
        if not self.default_folder:
            messagebox.showwarning("No Folder", "Please set a default folder.")
            return
        try:
            current_time = datetime.now()
            time_limit = current_time - timedelta(hours=1)
            files_in_folder = [os.path.join(self.default_folder, f) for f in os.listdir(self.default_folder)
                               if os.path.isfile(os.path.join(self.default_folder, f)) and not f.startswith('.')]
            self.files = [(f, os.path.basename(f)) for f in files_in_folder
                          if datetime.fromtimestamp(os.path.getctime(f)) > time_limit]
            if not self.files:
                response = messagebox.askyesno("No recent files found", "No recent files found. Would you like to select files manually?")
                if response:
                    self.select_files()
                return
            self.apply_rename_logic()
            self.populate_treeview()
        except FileNotFoundError:
            messagebox.showerror("Error", "Selected folder not found!")


    def apply_rename_logic(self):
        all_files = self.selected_files + self.files

        for i, (file_path, original_name) in enumerate(all_files):
            name, ext = os.path.splitext(original_name)

            # Default to keeping the original name unless we match a pattern
            proposed_name = name + ext

            # Case 1: Entire name is just digits
            if name.isdigit():
                proposed_name = f"Map #{name}" + ext

            # Case 2: Name is digits followed directly by letters, e.g. "123abc"
            elif re.fullmatch(r'\d+[a-zA-Z]+', name):
                match = re.fullmatch(r'(\d+)([a-zA-Z]+)', name)
                if match:
                    number, letters = match.groups()
                    proposed_name = f"Map #{number}({letters.capitalize()})" + ext

            # Case 3: Name is of the form "123-456" or similar
            elif '-' in name:
                parts = name.split('-')
                if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                    proposed_name = f"Vol.{parts[0]} - Pg.{parts[1]}" + ext
                else:
                    proposed_name = name + ext  # fallback for non-matching dash cases

            # Store the renamed file in the appropriate list
            if i < len(self.selected_files):
                self.selected_files[i] = (file_path, proposed_name)
            else:
                self.files[i - len(self.selected_files)] = (file_path, proposed_name)


    def populate_treeview(self):
        for row in self.treeview.get_children():
            self.treeview.delete(row)
        all_files = self.selected_files + self.files
        for file_path, proposed_name in all_files:
            original_name = os.path.basename(file_path)
            self.treeview.insert("", "end", values=(original_name, proposed_name))
        self.execute_button.config(state=tk.NORMAL)

    def execute_rename(self):
        for item in self.treeview.get_children():
            original_name, proposed_name = self.treeview.item(item, "values")

            # Try to find the full path for the original file
            match = next(
                (fp for fp, _ in self.selected_files + self.files if os.path.basename(fp) == original_name),
                None
                        )

            if not match:
                messagebox.showerror("Error", f"Original file path for {original_name} not found.")
                continue

            original_path = match
            proposed_path = os.path.join(os.path.dirname(original_path), proposed_name)

            if original_path != proposed_path:
                try:
                    os.rename(original_path, proposed_path)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to rename {original_name}: {e}")
                    return

        messagebox.showinfo("Success", "Files renamed successfully.")

        
    def on_proposed_name_click(self, event):                                #- NEED TO FIX FAST CLICK ISSUES
        region = self.treeview.identify("region", event.x, event.y)
        if region != "cell":
            return

        row_id = self.treeview.identify_row(event.y)
        column = self.treeview.identify_column(event.x)
        if column != "#2":
            return

        x, y, width, height = self.treeview.bbox(row_id, column)
        proposed_name = self.treeview.set(row_id, column)

        entry = tk.Entry(self.treeview)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, proposed_name)

        name, ext = os.path.splitext(proposed_name)

        def save_edit(event=None):
            new_name = entry.get()
            self.treeview.set(row_id, column, new_name)
            entry.destroy()
            self.treeview.focus_set()
            self.treeview.item(row_id, tags="updated")
            self.treeview.update_idletasks()

        def cancel_edit(event=None):
            entry.destroy()
            self.treeview.focus_set()

        entry.bind("<Return>", save_edit)
        entry.bind("<Escape>", cancel_edit)
        entry.bind("<FocusOut>", save_edit)            #! nnot working


        # Focus and grab first, then selection in after()
        entry.focus_set()
        entry.grab_set()

        def set_cursor_and_selection():
            entry.selection_range(0, len(name))
            entry.icursor(len(name))

        # Delay the selection so it's applied correctly after grab.... this feels dumb
        self.treeview.after(50, set_cursor_and_selection)


def main(parent=None):
    if parent is None:
        root = tk.Tk()
        root.title("Renaming Suite")
        stht = 400
        stwi = 800
        screenht = root.winfo_screenheight()
        screenwi = root.winfo_screenwidth()
        x = (screenwi / 2) - (stwi / 2)
        y = (screenht / 2) - (stht / 2)

        root.geometry(f'{stwi}x{stht}+{int(x)}+{int(y)}')
        root.resizable(False, False)

        app = BulkRenamer(root)
        root.mainloop()
    else:
        app = BulkRenamer(parent)

if __name__ == "__main__":
    main()
