import tkinter as tk
from tkinter import ttk, messagebox

class LandRecordOrganizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Land Record Research Organizer")
        
        # Setting up the notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.tab1 = ttk.Frame(self.notebook)
        self.tab2 = ttk.Frame(self.notebook)
        self.tab3 = ttk.Frame(self.notebook)
        self.tab4 = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab1, text="Record Logger")
        self.notebook.add(self.tab2, text="Renaming Suite")
        self.notebook.add(self.tab3, text="File Viewer")
        self.notebook.add(self.tab4, text="About")
        self.notebook.pack(expand=True, fill="both")
        
        # UUID tracking
        self.root_uuid = 1

        # Widgets for the first tab
        self.setup_tab1()

    def setup_tab1(self):
        # Frame for entries
        entry_frame = ttk.Frame(self.tab1)
        entry_frame.pack(pady=5)

        # Entry for document name with placeholder
        self.document_entry = ttk.Entry(entry_frame, width=30)
        self.document_entry.insert(0, "Enter Document Name")
        self.document_entry.bind("<FocusIn>", self.clear_placeholder)
        self.document_entry.bind("<FocusOut>", self.set_placeholder)
        self.document_entry.pack(side="left", padx=5)

        # Entry for comments with placeholder
        self.comments_entry = ttk.Entry(entry_frame, width=30)
        self.comments_entry.insert(0, "Enter Comments")
        self.comments_entry.bind("<FocusIn>", self.clear_placeholder)
        self.comments_entry.bind("<FocusOut>", self.set_placeholder)
        self.comments_entry.pack(side="left", padx=5)

        # Bind Enter key to add record for both entry fields
        self.document_entry.bind("<Return>", self.add_record)
        self.comments_entry.bind("<Return>", self.add_record)

        # Frame for the header
        header_frame = ttk.Frame(self.tab1)
        header_frame.pack(fill="x")

        # Header labels
        ttk.Label(header_frame, text="Expand", width=10).pack(side="left")
        ttk.Label(header_frame, text="Document Name", width=30).pack(side="left")
        ttk.Label(header_frame, text="Comments", width=30).pack(side="left")

        # Frame for the Treeview and scrollbar
        tree_frame = ttk.Frame(self.tab1)
        tree_frame.pack(expand=True, fill="both", padx=5, pady=(5, 0))

        # Scrollbar
        self.tree_scroll = ttk.Scrollbar(tree_frame)
        self.tree_scroll.pack(side="right", fill="y")

        # Treeview for displaying records
        self.tree = ttk.Treeview(tree_frame, columns=("Document", "Comments"), show="tree")
        
        # Configure the Treeview
        self.tree.heading("#0", text="Expand")  # Caret placeholder
        self.tree.heading("Document", text="Document Name")
        self.tree.heading("Comments", text="Comments")

        # Set column widths
        self.tree.column("#0", width=50)  # For expand/collapse icon
        self.tree.column("Document", width=150)
        self.tree.column("Comments", width=150)

        # Pack the Treeview
        self.tree.pack(expand=True, fill="both")

        # Configure the scrollbar
        self.tree_scroll.config(command=self.tree.yview)
        self.tree.config(yscrollcommand=self.tree_scroll.set)

        # Frame for buttons
        button_frame = ttk.Frame(self.tab1)
        button_frame.pack(pady=5)

        # Buttons
        self.add_button = ttk.Button(button_frame, text="Add Record", command=self.add_record)
        self.remove_button = ttk.Button(button_frame, text="Remove Record", command=self.remove_record)
        self.edit_button = ttk.Button(button_frame, text="Edit Record", command=self.edit_record)
        self.add_button.pack(side="left", padx=5)
        self.remove_button.pack(side="left", padx=5)
        self.edit_button.pack(side="left", padx=5)

        # Add bindings for caret click
        self.tree.bind("<ButtonRelease-1>", self.on_caret_click)

    def clear_placeholder(self, event):
        if event.widget.get() == "Enter Document Name" or event.widget.get() == "Enter Comments":
            event.widget.delete(0, tk.END)

    def set_placeholder(self, event):
        if event.widget.get() == "":
            if event.widget is self.document_entry:
                event.widget.insert(0, "Enter Document Name")
            else:
                event.widget.insert(0, "Enter Comments")

    def on_caret_click(self, event):
        # Get the item at the clicked position
        item = self.tree.identify_row(event.y)
        if item:  # Check if an item was clicked
            # Toggle the expansion state of the clicked item
            is_open = self.tree.item(item, "open")
            self.tree.item(item, open=not is_open)  # Toggle open state

    def generate_uuid(self):
        base_uuid = self.root_uuid
        while True:
            if not self.tree.exists(str(base_uuid)):
                return str(base_uuid)
            base_uuid += 1

    def add_record(self, event=None):
        doc_name = self.document_entry.get()
        comments = self.comments_entry.get()
        
        # Prevent adding empty records
        if doc_name == "Enter Document Name" or comments == "Enter Comments":
            doc_name = ""
            comments = ""
        
        uuid_value = self.generate_uuid()
        
        # Insert the new record
        self.tree.insert("", "end", iid=uuid_value, text="", values=("", doc_name, comments))
        
        # Automatically expand parent if it's a child
        if '.' in uuid_value:
            parent_uuid = '.'.join(uuid_value.split('.')[:-1])
            self.tree.item(parent_uuid, open=True)

        self.tree.see(uuid_value)  # Make sure the new entry is visible

        # Clear the input fields
        self.document_entry.delete(0, tk.END)
        self.comments_entry.delete(0, tk.END)
        
        # Set focus back to the document entry
        self.document_entry.focus_set()

    def remove_record(self):
        selected_item = self.tree.selection()
        if selected_item:
            self.tree.delete(selected_item)

    def edit_record(self):
        selected_item = self.tree.selection()
        
        if selected_item:
            # Get the selected item (there should only be one)
            selected_uuid = selected_item[0]
            
            # Get the current values in the entry fields
            doc_name = self.document_entry.get()
            comments = self.comments_entry.get()
            
            # Check if the entries are not just placeholders
            if doc_name == "Enter Document Name" or comments == "Enter Comments":
                messagebox.showwarning("Warning", "Please enter valid document name and comments.")
                return

            # Update the selected record in the Treeview with the new values
            self.tree.item(selected_uuid, values=("", doc_name, comments))

            # Clear the input fields and set focus back to the document entry
            self.document_entry.delete(0, tk.END)
            self.comments_entry.delete(0, tk.END)
            self.document_entry.focus_set()
        else:
            messagebox.showwarning("Warning", "No record selected for editing.")

if __name__ == "__main__":
    root = tk.Tk()
    app = LandRecordOrganizer(root)
    root.mainloop()



#BROKENNNNNNNNNNNNNN