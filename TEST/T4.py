import tkinter as tk
from tkinter import ttk
from idlelib.tooltip import Hovertip

def show_message():
    print("Button clicked!")

# Create the root window
root = tk.Tk()
root.title("Hovertip Example")

# Create a button
btn_add = ttk.Button(root, text="Enter Record", command=show_message)

# Attach a Hovertip to the button
Hovertip(btn_add, "Click to enter a new record.")

# Place the button on the window
btn_add.pack(padx=20, pady=20)

# Run the Tkinter event loop
root.mainloop()
