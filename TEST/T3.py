
#Standard imports
import os
from re import U
import tkinter as tk
from tkinter import filedialog, ttk, messagebox



# #Relative imports
# from ...RESEARCHV2.ROOT.RESEARCH.UTILITY.string_test import str_contains #! fix

class FileRenamerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("File Renamer")
        self.geometry("800x400")
        
        # Set up a frame to hold the Treeviews without space in between
        self.tree_frame = tk.Frame(self)
        self.tree_frame.grid(row=0, column=0, sticky="nsew")

        # Left Treeview for original file names
        self.left_tree = ttk.Treeview(self.tree_frame, columns=("Filename"), show="headings", selectmode="none")
        self.left_tree.heading("Filename", text="Original Filename")
        self.left_tree.column("Filename", anchor="w")  # Align text to the left
        self.left_tree.grid(row=0, column=0, sticky="nsew")
        
        # Right Treeview for new file names
        self.right_tree = ttk.Treeview(self.tree_frame, columns=("NewFilename"), show="headings")
        self.right_tree.heading("NewFilename", text="New Filename Preview")
        self.right_tree.column("NewFilename", anchor="w")  # Align text to the left
        self.right_tree.grid(row=0, column=1, sticky="nsew")
        
        # Scrollbar for both Treeviews
        scroll = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.on_scroll)
        scroll.grid(row=0, column=2, sticky="ns")
        self.left_tree.configure(yscrollcommand=scroll.set)
        self.right_tree.configure(yscrollcommand=scroll.set)
        
        # Bottom buttons
        btn_frame = tk.Frame(self)
        btn_frame.grid(row=1, column=0, pady=10)
        
        tk.Button(btn_frame, text="Select Directory", command=self.select_directory).grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Rename Files", command=self.rename_files).grid(row=0, column=1, padx=5)
        
        # Variables
        self.file_paths = []  # To store the paths of files in the selected directory

        # Bind double-click to edit the right Treeview items
        self.right_tree.bind("<Double-1>", self.edit_item)
    
    def select_directory(self):
        folder_path = filedialog.askdirectory()
        if not folder_path:
            return  # If no folder was selected, return

        # Clear any existing data
        self.left_tree.delete(*self.left_tree.get_children())
        self.right_tree.delete(*self.right_tree.get_children())
        self.file_paths.clear()
        
        # Populate Treeviews with file names
        max_name_len = 0
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            if os.path.isfile(file_path):
                self.file_paths.append(file_path)
                self.left_tree.insert("", "end", values=(file_name,))

                # Apply custom renaming logic here
                new_name = self.apply_rename_logic(file_name)
                self.right_tree.insert("", "end", values=(new_name,))
                
                max_name_len = max(max_name_len, len(new_name))
        
        # Dynamically adjust column width based on the longest filename
        column_width = max(150, min(max_name_len * 8, 400))
        self.left_tree.column("Filename", width=column_width)
        self.right_tree.column("NewFilename", width=column_width)
    
    def rename_files(self):
        if not self.file_paths:
            messagebox.showwarning("No Files", "No files to rename. Please select a directory first.")
            return
        
        for i, file_path in enumerate(self.file_paths):
            original_name = os.path.basename(file_path)
            new_name = self.right_tree.item(self.right_tree.get_children()[i], "values")[0]
            if original_name != new_name:
                new_path = os.path.join(os.path.dirname(file_path), new_name)
                try:
                    os.rename(file_path, new_path)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to rename '{original_name}' to '{new_name}': {e}")
                    return

        messagebox.showinfo("Success", "Files renamed successfully!")
        self.select_directory()  # Refresh file list after renaming

    def edit_item(self, event):
        item = self.right_tree.selection()[0]
        column = self.right_tree.identify_column(event.x)
        
        if column == "#1":
            x, y, width, height = self.right_tree.bbox(item, column)
            entry = tk.Entry(self.right_tree)
            entry.place(x=x, y=y, width=width, height=height)
            entry.insert(0, self.right_tree.item(item, "values")[0])

            entry.bind("<Return>", lambda e: self.update_item(item, entry))
            entry.bind("<FocusOut>", lambda e: entry.destroy())
            entry.focus()
    
    def update_item(self, item, entry):
        new_value = entry.get()
        self.right_tree.item(item, values=(new_value,))
        entry.destroy()
    
    def on_scroll(self, *args):
        # Sync the scroll of both Treeviews
        self.left_tree.yview(*args)
        self.right_tree.yview(*args)

    def apply_rename_logic(self, filename):
        """
        Placeholder for custom renaming logic.
        This function should be modified or replaced to implement specific renaming criteria.
        """
        # # Example logic: append '_new' to files ending with '.txt'
        # if filename.endswith(".txt"):
        #     return filename.replace(".txt", "_new.txt")
        # return filename

# Run the application
if __name__ == "__main__":
    app = FileRenamerApp()
    app.mainloop()
