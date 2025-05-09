import tkinter as tk
from tkinter import ttk, messagebox
from idlelib.tooltip import Hovertip                    #- fix this?
import json

class LandRecordOrganizer:
    def __init__(self, root):
        self.root = root
        #hello world
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", background="#4CAF50", font=('Arial', 10))
        self.style.configure("TLabel", font=('Arial', 10))
        
        # Treeview with hierarchical structure
        self.tree = ttk.Treeview(root, columns=("#1", "#2", "#3"), show="tree headings", selectmode="browse")
        self.tree.heading("#0", text="UUID")
        self.tree.heading("#1", text="")
        self.tree.heading("#2", text="Document Name")
        self.tree.heading("#3", text="Comments")
        self.tree.column("#0", width=25)
        self.tree.column("#1", width=0, minwidth=0, stretch=tk.NO)  # Hide this
        self.tree.column("#2", width=80, anchor="w")
        self.tree.column("#3", width=300, anchor="w")
        self.tree.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="nsew")

        # Grid Configuration
        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # Entry Fields
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

        # Button Frame
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

        self.btn_help = ttk.Button(btn_frame, text="    ?    ", command=self.show_help)
        self.btn_help.grid(row=0, column=4, padx=5, pady=5, sticky="ew")

        def is_abutter():
            if abut.get():
                print("Researching for Abutting Property")
            else:
                print("Researching for Subject Property")

        abut = tk.IntVar()
        abut.set(0)  # This makes the checkbox checked by default
        self.cbox_abutter = ttk.Checkbutton(btn_frame, text="Abutter", variable=abut, command=is_abutter)
        self.cbox_abutter.grid(row=0, column=4, padx=5, pady=5, sticky="ew")

        self.records = {}
        self.root.bind("<Return>", lambda event: self.add_record())
        self.entry_name.focus()

    def clear_placeholder(self, event):
        """Clear placeholder text when user starts typing"""
        if event.widget.get() in ("Document Name", "Comments"):
            event.widget.delete(0, tk.END)

    def restore_placeholder(self, event):
        """Restore placeholder text if the user didn't type anything"""
        if not event.widget.get():
            event.widget.insert(0, "Document Name" if event.widget == self.entry_name else "Comments")

    def generate_uuid(self, parent_uuid):
        """Generate a new UUID following a hierarchical pattern"""
        if parent_uuid is None:
            top_level = [k for k in self.records.keys() if '.' not in k]    # Counts the number of top-level records.

            return str(len(top_level) + 1)
        else:
            children = sorted([k for k in self.records.keys() if k.startswith(parent_uuid + '.')])
            return f"{parent_uuid}.{len(children) + 1}"

    def add_record(self):
        """Add a new record to the Treevew with proper hierarchy"""
        selected = self.tree.selection()
        parent_uuid = self.tree.item(selected[0], "values")[0] if selected else None
        new_uuid = self.generate_uuid(parent_uuid)

        doc_name = self.entry_name.get()
        comments = self.entry_comments.get()

        self.records[new_uuid] = {"name": doc_name, "comments": comments}

        if self.entry_name.get() == "Document Name":#TTTTTTTTTTTTTT
            messagebox.showwarning("Warning", "Must Enter a Document.")
            return
        if self.entry_comments.get() == "Comments":
            self.entry_comments.delete(0, tk.END)
        
        if selected:
            self.tree.insert(selected[0], "end", iid=new_uuid, text=new_uuid, values=(new_uuid, doc_name, comments))
            self.tree.item(selected[0], open=True)  # Expand parent node
        else:
            self.tree.insert("", "end", iid=new_uuid, text=new_uuid, values=(new_uuid, doc_name, comments))

    def edit_record(self):
        """Edit an existing record"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No record selected!")
            return

        uuid = self.tree.item(selected[0], "values")[0]
        doc_name = self.entry_name.get()
        comments = self.entry_comments.get()

        self.records[uuid] = {"name": doc_name, "comments": comments}
        self.tree.item(selected[0], values=(uuid, doc_name, comments))

    def has_children(self, uuid):
        """Check if the given UUID has children in the Treeview"""
        children = self.tree.get_children(uuid)  # Get children of the specified UUID
        return len(children) > 0  # Return True if children exist, False otherwise

    def delete_record(self):
        """Delete a record and its children, then reorder remaining records"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No record selected!")
            return

        elif selected:
            uuid = self.tree.item(selected[0], "values")[0]
            if self.has_children(uuid):
                confirm = messagebox.askyesno("Warning", f"Node {uuid} has child documents!\n\nAre you sure you want to delete these documents?")

                uuid = self.tree.item(selected[0], "values")[0]

                if confirm:
                    parent_uuid = ".".join(uuid.split(".")[:-1]) if "." in uuid else None  # Get parent UUID
                    self.delete_children(uuid)  # Delete all child records
                    del self.records[uuid]  # Delete from records dictionary
                    self.tree.delete(selected[0])  # Remove from the Treeview

                    self.reorder_branch(parent_uuid)  # Renumber the remaining records

                    if parent_uuid:
                        self.tree.item(parent_uuid, open=True)  # Keep parent expanded
            else:
                parent_uuid = ".".join(uuid.split(".")[:-1]) if "." in uuid else None  # Get parent UUID
                self.delete_children(uuid)  # Delete all child records
                del self.records[uuid]  # Delete from records dictionary
                self.tree.delete(selected[0])  # Remove from the Treeview

                self.reorder_branch(parent_uuid)  # Renumber the remaining records

                if parent_uuid:
                    self.tree.item(parent_uuid, open=True)  # Keep parent expanded


    def delete_children(self, uuid):
        """Recursively delete children of a given UUID"""
        children = [k for k in self.records.keys() if k.startswith(uuid + '.')]
        for child in children:
            self.tree.delete(child)
            del self.records[child]
            self.delete_children(child)

    def reorder_branch(self, parent_uuid):
        """Reorder child records under the given parent UUID"""
        children = sorted(
            [k for k in self.records.keys() if (parent_uuid is None and "." not in k) or k.startswith(parent_uuid + ".")],
            key=lambda x: list(map(int, x.split(".")))  # Sort numerically
                        )

        updated_records = {}

        for i, child in enumerate(children, start=1):
            new_uuid = f"{parent_uuid}.{i}" if parent_uuid else str(i)

            # Update Treeview
            old_values = self.tree.item(child, "values")
            self.tree.item(child, text=new_uuid, values=(new_uuid, old_values[1], old_values[2]))
            self.tree.move(child, parent_uuid if parent_uuid else "", "end")  # Ensure proper placement

            # Update records dictionary
            updated_records[new_uuid] = self.records.pop(child)
            updated_records[new_uuid]["uuid"] = new_uuid

        # Apply changes to self.records
        self.records.update(updated_records)

    def log_to_file(self):
        """Save records to a JSON file"""
        with open("land_records.json", "w") as file:
            json.dump(self.records, file, indent=4)
        messagebox.showinfo("Info", "Records logged to land_records.json")

    def show_help(self):
        """Display help information"""
        messagebox.showinfo("Help", "This application organizes land record documents. You can add, edit, delete records and log them to a file.")

def main(parent=None):
    """Run the application in standalone mode or as a part of another program"""
    if parent is None:
        root = tk.Tk()
        root.title("Logger")
        stht = 400
        stwi = 800
        screenht = root.winfo_screenheight()
        screenwi = root.winfo_screenwidth()
        x = (screenwi / 2) - (stwi / 2)
        y = (screenht / 2) - (stht / 2)

        root.geometry(f"{stwi}x{stht}+{int(x)}+{int(y)}")
        root.resizable(False, False)

        app = LandRecordOrganizer(root)
        root.mainloop()
    else:
        app = LandRecordOrganizer(parent)

if __name__ == "__main__":
    main()
