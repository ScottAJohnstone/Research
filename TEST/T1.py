import tkinter as tk
from tkinter import ttk, messagebox

class LandRecordOrganizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Land Record Research Organizer")
        
        # UUID tracking
        self.root_uuid = 1
        self.current_selected_uuid = None

        # Setup main UI
        self.setup_ui()

    def setup_ui(self):
        # Frame for entries
        entry_frame = ttk.Frame(self.root)
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

        # Bind Enter key to add record
        self.document_entry.bind("<Return>", self.add_record)
        self.comments_entry.bind("<Return>", self.add_record)

        # Frame for the Treeview and scrollbar
        tree_frame = ttk.Frame(self.root)
        tree_frame.pack(expand=True, fill="both", padx=5, pady=(5, 0))

        # Scrollbar
        self.tree_scroll = ttk.Scrollbar(tree_frame)
        self.tree_scroll.pack(side="right", fill="y")

        # Treeview
        self.tree = ttk.Treeview(tree_frame, columns=("Document", "Comments"), show="tree", yscrollcommand=self.tree_scroll.set)
        self.tree.heading("#0", text="UUID")
        self.tree.heading("Document", text="Document Name")
        self.tree.heading("Comments", text="Comments")
        self.tree.pack(expand=True, fill="both")

        self.tree_scroll.config(command=self.tree.yview)

        self.tree.bind("<<TreeviewSelect>>", self.on_treeview_select)
        self.tree.bind("<Double-1>", self.deselect_item)

        # Frame for buttons
        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=5)

        # Buttons
        ttk.Button(button_frame, text="Add Record", command=self.add_record).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Remove Record", command=self.remove_record).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Edit Record", command=self.edit_record).pack(side="left", padx=5)

    def clear_placeholder(self, event):
        if event.widget.get() in ("Enter Document Name", "Enter Comments"):
            event.widget.delete(0, tk.END)

    def set_placeholder(self, event):
        if not event.widget.get():
            event.widget.insert(0, "Enter Document Name" if event.widget is self.document_entry else "Enter Comments")

    def on_treeview_select(self, event):
        selected_item = self.tree.selection()
        if selected_item:
            self.current_selected_uuid = selected_item[0]
            doc_name, comments = self.tree.item(self.current_selected_uuid, 'values')
            self.document_entry.delete(0, tk.END)
            self.document_entry.insert(0, doc_name)
            self.comments_entry.delete(0, tk.END)
            self.comments_entry.insert(0, comments)
            self.document_entry.focus_set()
        else:
            self.current_selected_uuid = None

    def generate_uuid(self):
        base_uuid = self.root_uuid if not self.current_selected_uuid else self.current_selected_uuid
        index = 1
        while True:
            new_uuid = f"{base_uuid}.{index}" if self.current_selected_uuid else str(base_uuid)
            if not self.tree.exists(new_uuid):
                return new_uuid
            index += 1

    def add_record(self, event=None):
        doc_name = self.document_entry.get().strip()
        comments = self.comments_entry.get().strip()
        if not doc_name or not comments:
            return

        uuid_value = self.generate_uuid()
        parent_uuid = "" if '.' not in uuid_value else '.'.join(uuid_value.split('.')[:-1])
        self.tree.insert(parent_uuid, "end", iid=uuid_value, text=uuid_value, values=(doc_name, comments))
        if parent_uuid:
            self.tree.item(parent_uuid, open=True)
        self.tree.see(uuid_value)
        self.sort_treeview()
        self.document_entry.delete(0, tk.END)
        self.comments_entry.delete(0, tk.END)
        self.document_entry.focus_set()
        if not self.current_selected_uuid:
            self.root_uuid += 1

    def remove_record(self):
        selected_item = self.tree.selection()
        if selected_item:
            self.tree.delete(selected_item)
            self.sort_treeview()
            self.document_entry.focus_set()

    def edit_record(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "No record selected for editing.")
            return

        selected_uuid = selected_item[0]
        doc_name = self.document_entry.get().strip()
        comments = self.comments_entry.get().strip()
        if not doc_name or not comments:
            messagebox.showwarning("Warning", "Please enter valid document name and comments.")
            return

        self.tree.item(selected_uuid, values=(doc_name, comments))
        self.document_entry.delete(0, tk.END)
        self.comments_entry.delete(0, tk.END)
        self.document_entry.focus_set()

    def deselect_item(self, event):
        self.tree.selection_remove(self.tree.selection())

    def sort_treeview(self):
        def recursive_sort(parent=""):
            children = self.tree.get_children(parent)
            sorted_children = sorted(children, key=lambda x: list(map(int, x.split('.'))))
            for index, child in enumerate(sorted_children):
                self.tree.move(child, parent, index)
                recursive_sort(child)
        recursive_sort()

if __name__ == "__main__":
    root = tk.Tk()
    app = LandRecordOrganizer(root)
    root.mainloop()
