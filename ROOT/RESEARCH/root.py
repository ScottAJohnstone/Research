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

        # Create right-click menu
        self.create_right_click_menu()
        self.root.bind("<Button-2>", self.show_right_click_menu)

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
        # Forcing a UI refresh when switching tabs.
        self.root.update_idletasks()
        self.root.update()

    def create_right_click_menu(self):
        self.rcm_menu = tk.Menu(self.root, tearoff=0)
        # Basic menu... re-added dynamically 
        self.generic_options = [
            ("Cut", self.cut_text),
            ("Copy", self.copy_text),
            ("Paste", self.paste_text),
                                ]
        # alt menu... re-added dynamically 
        self.alt_options = [
            ("Jump To", self.jump_to),
                                ]

    def show_right_click_menu(self, event):
        # Clear old menu items
        self.rcm_menu.delete(0, 'end')

        # Add generic rcm options
        for label, command in self.generic_options:
            self.rcm_menu.add_command(label=label, command=command)

        self.rcm_menu.add_separator()

        # Add alt rcm options
        for label, command in self.alt_options:
            self.rcm_menu.add_command(label=label, command=command)

        self.rcm_menu.add_separator()

        # get activ tab
        current_tab = self.notebook.index(self.notebook.select())

        # Add tab-specific  right click options
        if current_tab == 0:
            self.rcm_menu.add_command(label="Add Research Entry", command=self.add_research_entry)
        elif current_tab == 1:
            self.rcm_menu.add_command(label="Revert to Default Filenames", command=self.revert_filenames)
        elif current_tab == 2:
            self.rcm_menu.add_command(label="Open File", command=self.open_file_viewer)
        elif current_tab == 3:
            self.rcm_menu.add_command(label="Open Help Docs", command=self.open_help)

        # Show menu
        self.rcm_menu.tk_popup(event.x_root, event.y_root)

    # Placeholder methods for actions
    def cut_text(self):
        self.root.focus_get().event_generate("<<Cut>>")

    def copy_text(self):
        self.root.focus_get().event_generate("<<Copy>>")

    def paste_text(self):
        self.root.focus_get().event_generate("<<Paste>>")

    def jump_to(self):
        print("Jumping to Job Nmber...")                                                                #-Needs Work

    # Tab-specific example functions
    def add_research_entry(self):
        print("Adding research entry...")                                                               #-Needs Work

    def revert_filenames(self):
        print("Reverting...")                                                                           #-Needs Work

    def open_file_viewer(self):
        print("Reset View...")                                                                          #-Needs Work

    def open_help(self):
        pass                                                                                            #-Needs Work

if __name__ == "__main__":
    root = tk.Tk()
    app = TabbedApp(root)
    root.mainloop()
