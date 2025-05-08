import tkinter as tk

# Define the functions for the actions
def cut_action():
    print("Cut action selected")

def copy_action():
    print("Copy action selected")

def paste_action():
    print("Paste action selected")

# Function to display the context menu
def show_context_menu(event):
    # Show the context menu at the location of the right-click
    context_menu.post(event.x_root, event.y_root)

# Create the main window
root = tk.Tk()
root.title("Right-Click Menu Example")
root.geometry("400x300")  # Set window size

# Create a label to demonstrate right-click
label = tk.Label(root, text="Right-click anywhere inside this window.", width=40, height=10, relief="solid")
label.pack(padx=10, pady=10)

# Create the context menu with Cut, Copy, and Paste options
context_menu = tk.Menu(root, tearoff=0)
context_menu.add_command(label="Cut", command=cut_action)
context_menu.add_command(label="Copy", command=copy_action)
context_menu.add_command(label="Paste", command=paste_action)

# Bind right-click (Button-3) to show the context menu
root.bind("<Button-3>", show_context_menu)

# Start the main event loop
root.mainloop()
