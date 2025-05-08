import tkinter as tk
from tkinter import ttk, messagebox

class TabContextMenuApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Right-Click Menu in Tabs")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill='both')

        self.shared_menu = tk.Menu(root, tearoff=0)
        self.shared_menu.add_command(label="Cut", command=lambda: self.shared_action("Cut"))
        self.shared_menu.add_command(label="Copy", command=lambda: self.shared_action("Copy"))
        self.shared_menu.add_command(label="Paste", command=lambda: self.shared_action("Paste"))
        self.shared_menu.add_separator()

        # Dictionary to hold tab-specific options
        self.tab_specific_options = {}

        # Create tabs with unique options
        self.create_tab("Tab 1", [("Rename", lambda: self.tab_action("Rename in Tab 1"))])
        self.create_tab("Tab 2", [("Export", lambda: self.tab_action("Export from Tab 2"))])
        self.create_tab("Tab 3", [("Generate Report", lambda: self.tab_action("Report from Tab 3"))])

    def create_tab(self, title, unique_options):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=title)

        tree = ttk.Treeview(frame, columns=("A", "B"), show="headings")
        tree.heading("A", text="Column A")
        tree.heading("B", text="Column B")
        tree.pack(expand=True, fill='both')

        for i in range(5):
            tree.insert("", "end", values=(f"{title} Row {i}", f"Value {i}"))

        tree.bind("<Button-3>", self.show_context_menu)  # Right-click
        self.tab_specific_options[frame] = unique_options

    def show_context_menu(self, event):
        widget = event.widget
        current_tab = self.notebook.nametowidget(self.notebook.select())

        # Clear tab-specific items if already appended
        index = self.shared_menu.index("end")
        while index is not None:
            label = self.shared_menu.entrycget(index, "label")
            if label == "Paste":
                break
            self.shared_menu.delete(index)
            index -= 1

        # Add current tab's specific options
        for label, command in self.tab_specific_options.get(current_tab, []):
            self.shared_menu.add_command(label=label, command=command)

        # Optional: select row under cursor
        if isinstance(widget, ttk.Treeview):
            row_id = widget.identify_row(event.y)
            if row_id:
                widget.selection_set(row_id)
            else:
                widget.selection_remove(widget.selection())

        self.shared_menu.tk_popup(event.x_root, event.y_root)

    def shared_action(self, action_name):
        messagebox.showinfo("Shared Action", f"{action_name} selected")

    def tab_action(self, action_name):
        messagebox.showinfo("Tab-Specific Action", f"{action_name} selected")

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = TabContextMenuApp(root)
    root.mainloop()
