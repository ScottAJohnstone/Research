import tkinter as tk
from tkinter import ttk
from idlelib.tooltip import Hovertip
import rename  # rename.py
import research  # research.py

class TabbedApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Research Log")
        
        stht = 400
        stwi = 850
        screenht = self.root.winfo_screenheight()
        screenwi = self.root.winfo_screenwidth()
        x = (screenwi / 2) - (stwi / 2)
        y = (screenht / 2) - (stht / 2)
        self.root.geometry(f'{stwi}x{stht}+{int(x)}+{int(y)}')
        self.root.resizable(False, False)

        # Create Notebook (Tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        # Create Tabs
        self.create_tabs()

        # Bind the tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self.refresh_display)

    def create_tabs(self):
        # Tab 1 - Research Logger
        self.tab1 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab1, text="Research Logger")
        research.main(self.tab1)

        # Tab 2 - Renaming Suite
        self.tab2 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab2, text="Renaming Suite")
        rename.main(self.tab2)  # Load rename.py into tab

        # Tab 3 - File Viewer
        self.tab3 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab3, text="File Viewer")

        # Tab 4 - Help
        self.tab4 = ttk.Frame(self.notebook)
        self.notebook.add(self.tab4, text="Help")

    def refresh_display(self, event):
        #Forces a UI refresh when switching tabs.
        self.root.update_idletasks()
        self.root.update()

if __name__ == "__main__":
    root = tk.Tk()
    app = TabbedApp(root)
    root.mainloop()
