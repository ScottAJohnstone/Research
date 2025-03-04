# external_script.py
import tkinter as tk

def run_program(parent):
    """This function creates a GUI inside the given parent frame."""
    label = tk.Label(parent, text="This is the external program!", font=("Arial", 14))
    label.pack(pady=20)

    button = tk.Button(parent, text="Click Me", command=lambda: print("Button Clicked"))
    button.pack(pady=10)
