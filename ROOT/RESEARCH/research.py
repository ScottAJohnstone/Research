import tkinter as tk
from tkinter import ttk, messagebox
import json

class LandRecordOrganizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Reseach Log - Logger")
        self.root.geometry("600x500")  # Set a more compact window size
        
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", background="#4CAF50", font=('Arial', 10))
        self.style.configure("TLabel", font=('Arial', 10))
        
        # Treeview with compact size
        self.tree = ttk.Treeview(root, columns=("#1", "#2", "#3"), show='headings', selectmode='browse')
        self.tree.heading("#1", text="UUID")
        self.tree.heading("#2", text="Document Name")
        self.tree.heading("#3", text="Comments")
        self.tree.column("#1", width=100, anchor="w")
        self.tree.column("#2", width=180, anchor="w")
        self.tree.column("#3", width=220, anchor="w")
        self.tree.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")
        
        # Adding grid configuration
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)
        
        # Entry fields with compact style
        self.entry_name = ttk.Entry(root)
        self.entry_name.grid(row=1, column=0, columnspan=4, sticky="ew", padx=10, pady=5)
        self.entry_name.insert(0, "Document Name")
        self.entry_name.bind("<FocusIn>", self.clear_placeholder)
        self.entry_name.bind("<FocusOut>", self.restore_placeholder)
        
        self.entry_comments = ttk.Entry(root)
        self.entry_comments.grid(row=2, column=0, columnspan=4, sticky="ew", padx=10, pady=5)
        self.entry_comments.insert(0, "Comments")
        self.entry_comments.bind("<FocusIn>", self.clear_placeholder)
        self.entry_comments.bind("<FocusOut>", self.restore_placeholder)
        
        # Buttons with a compact layout
        btn_frame = ttk.Frame(root)
        btn_frame.grid(row=3, column=0, columnspan=4, padx=10, pady=10, sticky="ew")
        
        self.btn_add = ttk.Button(btn_frame, text="Enter Record", command=self.add_record)
        self.btn_add.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.btn_edit = ttk.Button(btn_frame, text="Edit Record", command=self.edit_record)
        self.btn_edit.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.btn_delete = ttk.Button(btn_frame, text="Delete Record", command=self.delete_record)
        self.btn_delete.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        self.btn_log = ttk.Button(btn_frame, text="Log to File", command=self.log_to_file)
        self.btn_log.grid(row=0, column=3, padx=5, pady=5, sticky="ew")
        
        self.btn_help = ttk.Button(btn_frame, text="?", command=self.show_help)
        self.btn_help.grid(row=0, column=4, padx=5, pady=5, sticky="ew")
        
        self.records = {}
        self.root.bind("<Return>", lambda event: self.add_record())
        
        self.entry_name.focus()  # Focus on the document name entry at startup
    
    def clear_placeholder(self, event):
        """Clear placeholder text when the user starts typing"""
        if event.widget.get() == "Document Name" or event.widget.get() == "Comments":
            event.widget.delete(0, tk.END)
    
    def restore_placeholder(self, event):
        """Restore placeholder text if the user didn't type anything"""
        if not event.widget.get():
            if event.widget == self.entry_name:
                event.widget.insert(0, "Document Name")
            elif event.widget == self.entry_comments:
                event.widget.insert(0, "Comments")
    
    def generate_uuid(self, parent_uuid):
        if parent_uuid is None:
            top_level = [k for k in self.records.keys() if '.' not in k]
            return str(len(top_level) + 1)
        else:
            children = sorted([k for k in self.records.keys() if k.startswith(parent_uuid + '.')])
            return f"{parent_uuid}.{len(children) + 1}"
    
    def add_record(self):
        selected = self.tree.selection()
        parent_uuid = self.tree.item(selected[0], "values")[0] if selected else None
        new_uuid = self.generate_uuid(parent_uuid)
        
        doc_name = self.entry_name.get()
        comments = self.entry_comments.get()
        
        self.records[new_uuid] = {"name": doc_name, "comments": comments}
        
        if selected:
            self.tree.insert(selected[0], "end", iid=new_uuid, text=new_uuid, values=(new_uuid, doc_name, comments))
            self.tree.item(selected[0], open=True)  # Automatically expand parent
        else:
            self.tree.insert("", "end", iid=new_uuid, text=new_uuid, values=(new_uuid, doc_name, comments))
        
    def edit_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No record selected!")
            return
        
        uuid = self.tree.item(selected[0], "values")[0]
        doc_name = self.entry_name.get()
        comments = self.entry_comments.get()
        
        self.records[uuid] = {"name": doc_name, "comments": comments}
        self.tree.item(selected[0], values=(uuid, doc_name, comments))
    
    def delete_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No record selected!")
            return
        
        uuid = self.tree.item(selected[0], "values")[0]
        
        # Confirm with the user about deleting the parent and its children
        confirm = messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this parent record and its children?")
        
        if confirm:
            parent_uuid = '.'.join(uuid.split('.')[:-1]) if '.' in uuid else None
            self.delete_children(uuid)  # Delete the children
            del self.records[uuid]  # Delete the parent record
            self.tree.delete(selected[0])  # Remove from the treeview
            
            self.reorder_branch(parent_uuid)
            
            if parent_uuid:
                self.tree.item(parent_uuid, open=True)  # Ensure parent remains expanded
    
    def delete_children(self, uuid):
        # Find all children of the given uuid and delete them
        children = [k for k in self.records.keys() if k.startswith(uuid + '.')]
        for child in children:
            self.tree.delete(child)
            del self.records[child]
            self.delete_children(child)  # Recursively delete child records
    
    def reorder_branch(self, parent_uuid):
        children = sorted([k for k in self.records.keys() if (parent_uuid is None and '.' not in k) or k.startswith(parent_uuid + '.')])
        updated_records = {}
        
        for i, child in enumerate(children, start=1):
            new_uuid = f"{parent_uuid}.{i}" if parent_uuid else str(i)
            updated_records[new_uuid] = self.records.pop(child)
            updated_records[new_uuid]['uuid'] = new_uuid
            
        self.records.update(updated_records)
        
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for uuid, data in sorted(self.records.items()):
            parent = '.'.join(uuid.split('.')[:-1]) if '.' in uuid else ""
            self.tree.insert(parent, "end", iid=uuid, text=uuid, values=(uuid, data["name"], data["comments"]))
            self.tree.item(uuid, open=True)  # Ensure all items are expanded
    
    def log_to_file(self):
        with open("land_records.json", "w") as file:
            json.dump(self.records, file, indent=4)
        messagebox.showinfo("Info", "Records logged to land_records.json")
    
    def show_help(self):
        messagebox.showinfo("Help", "This application helps organize land record documents. You can add, edit, delete records and log them to a file.")

if __name__ == "__main__":
    root = tk.Tk()
    app = LandRecordOrganizer(root)
    root.mainloop()
