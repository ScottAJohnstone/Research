import tkinter as tk
from tkinter import ttk

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
        
        self.notebook.add(self.tab1, text="Records")
        self.notebook.add(self.tab2, text="Tab 2")
        self.notebook.add(self.tab3, text="Tab 3")
        self.notebook.add(self.tab4, text="Tab 4")
        self.notebook.pack(expand=True, fill="both")
        
        # Widgets for the first tab
        self.setup_tab1()
        
        # UUID tracking
        self.root_uuid = 1
        self.current_selected_uuid = None

    def setup_tab1(self):
        # Entry for document name
        self.document_entry = ttk.Entry(self.tab1)
        self.document_entry.pack(pady=5)
        
        # Text widget for comments
        self.comments_text = tk.Text(self.tab1, height=4)
        self.comments_text.pack(pady=5)
        
        # Buttons
        self.add_button = ttk.Button(self.tab1, text="Add Record", command=self.add_record)
        self.remove_button = ttk.Button(self.tab1, text="Remove Record", command=self.remove_record)
        self.edit_button = ttk.Button(self.tab1, text="Edit Record", command=self.edit_record)
        self.add_button.pack(side="left", padx=5)
        self.remove_button.pack(side="left", padx=5)
        self.edit_button.pack(side="left", padx=5)
        
        # Treeview for displaying records
        self.tree = ttk.Treeview(self.tab1, columns=("Document", "Comments"), show="tree")
        self.tree.heading("#0", text="UUID")  # Setting the first column for UUID
        self.tree.heading("Document", text="Document Name")
        self.tree.heading("Comments", text="Comments")
        self.tree.pack(expand=True, fill="both")
        
        self.tree.bind("<<TreeviewSelect>>", self.on_treeview_select)
        self.tree.bind("<Double-1>", self.deselect_item)  # Bind double-click event

    def generate_uuid(self):
        if self.current_selected_uuid:
            base_uuid = self.current_selected_uuid
            index = 1
            while True:
                new_uuid = f"{base_uuid}.{index}"
                if not self.tree.exists(new_uuid):
                    return new_uuid
                index += 1
        else:
            base_uuid = self.root_uuid
            while True:
                if not self.tree.exists(str(base_uuid)):
                    return str(base_uuid)
                base_uuid += 1

    def add_record(self):
        doc_name = self.document_entry.get()
        comments = self.comments_text.get("1.0", tk.END).strip()
        uuid_value = self.generate_uuid()
        
        # Collapse all items before adding a new record
        self.collapse_all_items()

        # Insert the new record
        if '.' in uuid_value:  # Child item
            parent_uuid = '.'.join(uuid_value.split('.')[:-1])
            self.tree.insert(parent_uuid, "end", iid=uuid_value, text=uuid_value, values=(doc_name, comments))
        else:  # Root item
            self.tree.insert("", "end", iid=uuid_value, text=uuid_value, values=(doc_name, comments))
        
        # Automatically expand parent if it's a child                                               #- is this still needed
        if '.' in uuid_value:
            self.tree.item(parent_uuid, open=True)

        # Expand only the current selected item
        if self.current_selected_uuid:
            self.tree.item(self.current_selected_uuid, open=True)

        self.sort_treeview()  # Sort items after adding a record
        
        # Clear the input fields
        self.document_entry.delete(0, tk.END)
        self.comments_text.delete("1.0", tk.END)
        
        if not self.current_selected_uuid:
            self.root_uuid += 1

    def collapse_all_items(self):
        """Collapse all items in the Treeview."""
        for item in self.tree.get_children():
            self.tree.item(item, open=False)
            self._collapse_children(item)

    def _collapse_children(self, item):
        """Recursively collapse all child items."""
        children = self.tree.get_children(item)
        for child in children:
            self.tree.item(child, open=False)
            self._collapse_children(child)

    def remove_record(self):
        selected_item = self.tree.selection()
        if selected_item:
            self.tree.delete(selected_item)
            self.sort_treeview()  # Re-sort items after removing a record

    def edit_record(self):
        selected_item = self.tree.selection()
        if selected_item:
            doc_name = self.document_entry.get()
            comments = self.comments_text.get("1.0", tk.END).strip()
            self.tree.item(selected_item, values=(doc_name, comments))
        
    def on_treeview_select(self, event):
        selected_item = self.tree.selection()
        if selected_item:
            self.current_selected_uuid = selected_item[0]
        else:
            self.current_selected_uuid = None

    def deselect_item(self, event):
        """Deselect the currently selected item on double-click."""
        self.tree.selection_remove(self.tree.selection())  # Remove selection

    def sort_treeview(self):
        def recursive_sort(parent=""):
            children = self.tree.get_children(parent)
            sorted_children = sorted(children, key=lambda x: list(map(int, x.split('.'))))
            
            for index, child in enumerate(sorted_children):
                self.tree.move(child, parent, index)
                recursive_sort(child)  # Sort the children recursively

        recursive_sort()

if __name__ == "__main__":
    root = tk.Tk()
    app = LandRecordOrganizer(root)
    root.mainloop()
