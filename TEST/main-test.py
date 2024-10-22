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
        self.current_selected_uuid = None

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

        # Frame for the Treeview and scrollbar
        tree_frame = ttk.Frame(self.tab1)
        tree_frame.pack(expand=True, fill="both", padx=5, pady=(5, 0))

        # Scrollbar
        self.tree_scroll = ttk.Scrollbar(tree_frame)
        self.tree_scroll.pack(side="right", fill="y")

        # Treeview for displaying records
        self.tree = ttk.Treeview(tree_frame, columns=("Document", "Comments"), show="tree", yscrollcommand=self.tree_scroll.set)
        self.tree.heading("#0", text="UUID")  # Setting the first column for UUID
        self.tree.heading("Document", text="Document Name")
        self.tree.heading("Comments", text="Comments")
        self.tree.pack(expand=True, fill="both")

        self.tree_scroll.config(command=self.tree.yview)  # Configure the scrollbar

        self.tree.bind("<<TreeviewSelect>>", self.on_treeview_select)  # Bind the selection event
        self.tree.bind("<Double-1>", self.deselect_item)  # Bind double-click event

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

    def clear_placeholder(self, event):
        if event.widget.get() == "Enter Document Name" or event.widget.get() == "Enter Comments":
            event.widget.delete(0, tk.END)
            #event.widget.config(fg="black")  # Change text color to black when typing

    def set_placeholder(self, event):
        if event.widget.get() == "":
            if event.widget is self.document_entry:
                event.widget.insert(0, "Enter Document Name")
            else:
                event.widget.insert(0, "Enter Comments")
            #event.widget.config(fg="lightgrey")  # Set placeholder text color to light grey

    def on_treeview_select(self, event):
        selected_item = self.tree.selection()
        
        if selected_item:
            self.current_selected_uuid = selected_item[0]
            
            # Get the current values of the selected item
            doc_name, comments = self.tree.item(self.current_selected_uuid, 'values')
            
            # Populate the entry fields with the selected values
            self.document_entry.delete(0, tk.END)
            self.document_entry.insert(0, doc_name)
            self.comments_entry.delete(0, tk.END)
            self.comments_entry.insert(0, comments)
            
            # Set focus back to the document entry
            self.document_entry.focus_set()
        else:
            self.current_selected_uuid = None

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

    def add_record(self, event=None):
        doc_name = self.document_entry.get()
        comments = self.comments_entry.get()
        
        # Prevent adding empty records
        if doc_name == "Enter Document Name" or comments == "Enter Comments":
            doc_name = ""
            comments = ""
        
        uuid_value = self.generate_uuid()
        
        # Insert the new record
        if '.' in uuid_value:  # Child item
            parent_uuid = '.'.join(uuid_value.split('.')[:-1])
            self.tree.insert(parent_uuid, "end", iid=uuid_value, text=uuid_value, values=(doc_name, comments))
        else:  # Root item
            self.tree.insert("", "end", iid=uuid_value, text=uuid_value, values=(doc_name, comments))
        
        # Automatically expand parent if it's a child
        if '.' in uuid_value:
            self.tree.item(parent_uuid, open=True)

        # Expand only the current selected item
        if self.current_selected_uuid:
            self.tree.item(self.current_selected_uuid, open=True)

        self.tree.see(uuid_value)  # Make sure the new entry is visible       #- maybe i want to change it so the parent entry is always in view?


        self.sort_treeview()  # Sort items after adding a record
        
        # Clear the input fields
        self.document_entry.delete(0, tk.END)
        self.comments_entry.delete(0, tk.END)
        
        # Set focus back to the document entry
        self.document_entry.focus_set()
        
        if not self.current_selected_uuid:
            self.root_uuid += 1

    def remove_record(self):
        selected_item = self.tree.selection()
        if selected_item:
            self.tree.delete(selected_item)
            self.sort_treeview()  # Re-sort items after removing a record
            self.document_entry.focus_set()


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
            self.tree.item(selected_uuid, values=(doc_name, comments))

            # Clear the input fields and set focus back to the document entry
            self.document_entry.delete(0, tk.END)
            self.comments_entry.delete(0, tk.END)
            self.document_entry.focus_set()
        else:
            messagebox.showwarning("Warning", "No record selected for editing.")

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