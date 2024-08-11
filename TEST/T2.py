import tkinter as tk

def show_context_menu(event, menu):
    """Display the context menu at the mouse pointer's location."""
    menu.post(event.x_root, event.y_root)

def create_context_menu(root, items):
    """Create a context menu with the given items."""
    menu = tk.Menu(root, tearoff=0)
    for label, command in items:
        menu.add_command(label=label, command=command)
    return menu

def attach_context_menu(widget, menu):
    """Attach the context menu to the given widget."""
    widget.bind("<Button-3>", lambda event: show_context_menu(event, menu))

def on_copy():
    print("Copy selected")

def on_paste():
    print("Paste selected")

def create_window_with_widgets():
    """Create a new window with widgets that share the same context menu."""
    window = tk.Toplevel()
    window.title("Right Click Menu Example")

    label = tk.Label(window, text="Right-click on this label")
    label.pack(pady=10)

    entry = tk.Entry(window)
    entry.pack(pady=10)

    # Create the context menu
    context_menu = create_context_menu(window, [
        ("Copy", on_copy),
        ("Paste", on_paste),
    ])

    # Attach the context menu to the widgets
    attach_context_menu(label, context_menu)
    attach_context_menu(entry, context_menu)

# Main application
root = tk.Tk()
root.title("Tkinter Right Click Menu")

# Create a context menu for the main window's widgets
context_menu = create_context_menu(root, [
    ("Copy", on_copy),
    ("Paste", on_paste),
])

# Attach the context menu to a widget in the main window
main_label = tk.Label(root, text="Right-click on this label in the main window")
main_label.pack(pady=10)
attach_context_menu(main_label, context_menu)

# Button to create a new window
create_window_button = tk.Button(root, text="Open New Window", command=create_window_with_widgets)
create_window_button.pack(pady=10)

root.mainloop()
