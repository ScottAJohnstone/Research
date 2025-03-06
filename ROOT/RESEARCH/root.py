import tkinter as tk
from tkinter import ttk
import rename  #rename.py

class TabbedApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Research Log")
        stht = 350
        stwi = 800
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

    def create_tabs(self):
        # Tab 1
        tab1 = ttk.Frame(self.notebook)
        self.notebook.add(tab1, text="Research Logger")
        #tk.Label(tab1, text="Welcome to the Home Tab!", font=("Arial", 14)).pack(pady=20)

        # Tab 2 - Load rename.py
        tab2 = ttk.Frame(self.notebook)
        self.notebook.add(tab2, text="Renaming Suite")
        # Run external script inside Tab 2
        rename.main(tab2)  # Pass tab2 as the parent

        # Tab 3 - Load fileviewer.py
        tab3 = ttk.Frame(self.notebook)
        self.notebook.add(tab3, text="File Viewer")

        # Tab 4 - Load fileviewer.py
        tab4 = ttk.Frame(self.notebook)
        self.notebook.add(tab4, text="Help") 

if __name__ == "__main__":
    root = tk.Tk()
    app = TabbedApp(root)
    root.mainloop()
