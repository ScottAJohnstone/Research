import tkinter as tk

def change_contents():
    # Remove all existing widgets
    for widget in root.winfo_children():
        widget.destroy()
    
    # Add new widgets
    new_label = tk.Label(root, text="New Content Added!", font=('Arial', 16))
    new_label.pack(pady=20)
    
    new_button = tk.Button(root, text="New Button", command=change_contents)
    new_button.pack(pady=20)
    
    new_text = tk.Text(root, height=5, width=40)
    new_text.insert(tk.END, "This is some new text content.")
    new_text.pack(pady=20)

# Create the main window
root = tk.Tk()
root.title("Change Contents Example")

# Create an initial button to trigger content change
initial_button = tk.Button(root, text="Change Content", command=change_contents)
initial_button.pack(pady=20)

# Run the application
root.mainloop()
