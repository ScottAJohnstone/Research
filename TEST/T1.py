from idlelib.tooltip import Hovertip
import tkinter as tk
from tkinter import ttk

root = tk.Tk()

b_save = ttk.Button(root, text="Save")
b_save.pack(padx=20, pady=20)

# Create the tooltip with custom styles
addTip = Hovertip(b_save, 'Start Research:\nHotkey = [Enter]')
addTip.text = "Start Research:\nHotkey = [Enter]"  # Ensure text is explicitly set

root.mainloop()
