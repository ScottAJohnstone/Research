import tkinter as tk
from tkinter import ttk
import rename  # Import the external program

class TabbedApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tabbed Interface with External Program")

        # Create Notebook (Tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        # Create Tabs
        self.create_tabs()

    def create_tabs(self):
        # Tab 1
        tab1 = ttk.Frame(self.notebook)
        self.notebook.add(tab1, text="Home")
        tk.Label(tab1, text="Welcome to the Home Tab!", font=("Arial", 14)).pack(pady=20)

        # Tab 2 - Load external program here
        tab2 = ttk.Frame(self.notebook)
        self.notebook.add(tab2, text="External Program")
        
        # Run external script inside Tab 2
        rename.main(tab2)  # Pass tab2 as the parent

if __name__ == "__main__":
    root = tk.Tk()
    app = TabbedApp(root)
    root.mainloop()
