import tkinter as tk

def info(window, text, yes_command=None, no_command=None):
    global delay

    # Create or get the info frame
    for widget in window.winfo_children():
        if isinstance(widget, tk.Frame):
            info_frame = widget
            break
    else:
        info_frame = tk.Frame(window)
        info_frame.pack(side=tk.BOTTOM, fill=tk.X)

    # Clear any existing widgets in the info frame
    for widget in info_frame.winfo_children():
        widget.destroy()

    # Create and add the message label to the frame
    message_label = tk.Label(info_frame, text=text, font=('Helvetica', 10))
    message_label.pack(side=tk.TOP, anchor=tk.SE, padx=10, pady=5)

    # Create Yes and No buttons
    yes_button = tk.Button(info_frame, text="Yes", command=lambda: yes_action(yes_command, info_frame))
    yes_button.pack(side=tk.LEFT, padx=10, pady=10)

    no_button = tk.Button(info_frame, text="No", command=lambda: no_action(no_command, info_frame))
    no_button.pack(side=tk.RIGHT, padx=10, pady=10)

    # Force the window to update its display
    window.update_idletasks()

def yes_action(yes_command, info_frame):
    if yes_command:
        yes_command()
    info_frame.destroy()  # Remove the frame after the action is taken

def no_action(no_command, info_frame):
    if no_command:
        no_command()
    info_frame.destroy()  # Remove the frame after the action is taken

# Example usage
def on_yes():
    print("Yes was clicked")

def on_no():
    print("No was clicked")

def create_window():
    root = tk.Tk()
    root.title("Example Window")

    # Trigger the info function with Yes/No buttons
    info(root, "Do you want to proceed?", yes_command=on_yes, no_command=on_no)

    root.mainloop()

create_window()
