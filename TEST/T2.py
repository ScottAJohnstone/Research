import tkinter as tk

def on_spinbox_change():
    value = spinbox.get()
    print("Value changed to:", value)

root = tk.Tk()
root.geometry("300x200")

# Creating a Spinbox
spinbox = tk.Spinbox(root, from_=0, to=100, width=10, relief="sunken", repeatdelay=500, repeatinterval=100,
                     font=("Arial", 12), bg="lightgrey", fg="blue", command=on_spinbox_change)

# Setting options for the Spinbox
spinbox.config(state="normal", cursor="hand2", bd=3, justify="center", wrap=True)

# Placing the Spinbox in the window
spinbox.pack(padx=20, pady=20)

root.mainloop()