import tkinter as tk
from tkinter import ttk, messagebox
import json


def parse_string(s: str, strict: bool = True):
    """
    Returns: (volume, page, map_num, instrument, remainder, comment)
    """
    if s is None or str(s).strip() == "":
        if strict:
            raise ValueError("Input is empty.")
        return None, None, None, None, None, None

    s = str(s)
    volume = page = map_num = instrument = remainder = comment = None

    dash_count = s.count("-")
    if dash_count == 0:
        first, second = s, ""
    elif dash_count == 1:
        first, second = s.split("-", 1)
    else:
        first, second, comment = s.split("-", 2)

    first_norm = first.replace(".", "/")

    if "/" in first_norm:
        if first_norm.count("/") != 1:
            if strict:
                raise ValueError("Ambiguous volume/page: more than one '/' or '.' in left part.")
        else:
            left, right = first_norm.split("/", 1)
            if left.isdigit() and right.isdigit():
                volume, page = left, right
            else:
                if strict:
                    raise ValueError("Volume/Page must be numeric when '/' or '.' is present.")

    target = second if second else first

    if target:
        if target.isdigit():
            if dash_count == 0 and "/" not in s and "." not in s:
                map_num = target
            else:
                instrument = target
        else:
            nums, chars = [], []
            for ch in target:
                (nums if ch.isdigit() else chars).append(ch)
            instrument = "".join(nums) if nums else None
            remainder = "".join(chars) if chars else None

    return volume, page, map_num, instrument, remainder, comment


class LandRecordOrganizer:
    def __init__(self, root):
        self.root = root
        self.style = ttk.Style()
        self.style.configure("TButton", padding=6, relief="flat", background="#4CAF50", font=('Arial', 10))
        self.style.configure("TLabel", font=('Arial', 10))
        
        # 🔹 Treeview with an added Instrument column
        self.tree = ttk.Treeview(root, columns=("#1", "#2", "#3", "#4"), show="tree headings", selectmode="browse")
        self.tree.heading("#0", text="UUID")
        self.tree.heading("#1", text="")   # hidden
        self.tree.heading("#2", text="Document Name")
        self.tree.heading("#3", text="Comments")
        self.tree.heading("#4", text="Instrument")   # NEW COLUMN
        self.tree.column("#0", width=40)
        self.tree.column("#1", width=0, minwidth=0, stretch=tk.NO)  # hidden
        self.tree.column("#2", width=150, anchor="w")
        self.tree.column("#3", width=300, anchor="w")
        self.tree.column("#4", width=100, anchor="w")  # NEW COLUMN
        self.tree.grid(row=0, column=0, columnspan=5, padx=10, pady=10, sticky="nsew")

        root.grid_rowconfigure(0, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # Entry Fields
        self.entry_name = ttk.Entry(root)
        self.entry_name.grid(row=1, column=0, columnspan=5, sticky="ew", padx=10, pady=5)
        self.entry_name.insert(0, "Document Name")
        self.entry_name.bind("<FocusIn>", self.clear_placeholder)
        self.entry_name.bind("<FocusOut>", self.restore_placeholder)

        self.entry_comments = ttk.Entry(root)
        self.entry_comments.grid(row=2, column=0, columnspan=5, sticky="ew", padx=10, pady=5)
        self.entry_comments.insert(0, "Comments")
        self.entry_comments.bind("<FocusIn>", self.clear_placeholder)
        self.entry_comments.bind("<FocusOut>", self.restore_placeholder)

        # Buttons
        btn_frame = ttk.Frame(root)
        btn_frame.grid(row=3, column=0, columnspan=5, padx=10, pady=10, sticky="ew")

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

        self.records = {}
        self.root.bind("<Return>", lambda event: self.add_record())
        self.entry_name.focus()

    def clear_placeholder(self, event):
        if event.widget.get() in ("Document Name", "Comments"):
            event.widget.delete(0, tk.END)

    def restore_placeholder(self, event):
        if not event.widget.get():
            event.widget.insert(0, "Document Name" if event.widget == self.entry_name else "Comments")

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
        comments_entry = self.entry_comments.get()

        if doc_name == "Document Name":
            messagebox.showwarning("Warning", "Must Enter a Document Number.")
            return
        if comments_entry == "Comments":
            comments_entry = ""

        try:
            volume, page, map_num, instrument, remainder, trailing_comment = parse_string(doc_name, strict=True)
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e))
            return

        final_comments = comments_entry if comments_entry else (trailing_comment or "")

        # 🔹 Store instrument explicitly
        self.records[new_uuid] = {
            "name": doc_name,
            "comments": final_comments,
            "volume": volume,
            "page": page,
            "map": map_num,
            "instrument": instrument,
            "remainder": remainder,
            "parsed_comment": trailing_comment,
        }

        # 🔹 Insert instrument into the Treeview
        values = (new_uuid, doc_name, final_comments, instrument if instrument else "")
        if selected:
            self.tree.insert(selected[0], "end", iid=new_uuid, text=new_uuid, values=values)
            self.tree.item(selected[0], open=True)
        else:
            self.tree.insert("", "end", iid=new_uuid, text=new_uuid, values=values)

        if self.entry_comments.get() == "Comments":
            self.entry_comments.delete(0, tk.END)
        self.entry_name.focus()

    def edit_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No record selected!")
            return

        uuid = self.tree.item(selected[0], "values")[0]
        doc_name = self.entry_name.get()
        comments = self.entry_comments.get()

        # Re-parse for instrument updates
        try:
            _, _, _, instrument, _, _ = parse_string(doc_name, strict=False)
        except Exception:
            instrument = ""

        self.records[uuid] = {"name": doc_name, "comments": comments, "instrument": instrument}
        self.tree.item(selected[0], values=(uuid, doc_name, comments, instrument if instrument else ""))

    def delete_record(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No record selected!")
            return
        uuid = self.tree.item(selected[0], "values")[0]
        del self.records[uuid]
        self.tree.delete(selected[0])

    def log_to_file(self):
        with open("land_records.json", "w") as file:
            json.dump(self.records, file, indent=4)
        messagebox.showinfo("Info", "Records logged to land_records.json")

    def show_help(self):
        messagebox.showinfo("Help", "This application organizes land record documents.\n"
                             "You can add, edit, delete records and log them to a file.\n"
                             "Now includes Instrument Number column!")


def main(parent=None):
    if parent is None:
        root = tk.Tk()
        root.title("Logger")
        stht, stwi = 400, 900
        screenht, screenwi = root.winfo_screenheight(), root.winfo_screenwidth()
        x, y = (screenwi / 2) - (stwi / 2), (screenht / 2) - (stht / 2)

        root.geometry(f"{stwi}x{stht}+{int(x)}+{int(y)}")
        root.resizable(False, False)

        app = LandRecordOrganizer(root)
        root.mainloop()
    else:
        app = LandRecordOrganizer(parent)


if __name__ == "__main__":
    main()
