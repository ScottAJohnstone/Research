import tkinter as tk

# Function to show right-click menu
def show_right_click_menu(event):
    print("Right-click detected at:", event.x, event.y)

# Create the main window
root = tk.Tk()
root.title("Right-Click Test")
root.geometry("400x300")

# Bind the right-click event to show position
root.bind("<Button-2>", show_right_click_menu)

# Run the Tkinter main loop
root.mainloop()
