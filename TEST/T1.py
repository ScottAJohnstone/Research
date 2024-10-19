import tkinter as tk

def cut_text(event=None):
    try:
        # Check if there's a selection and cut the selected text
        window.clipboard_clear()
        selected_text = text_area.get("sel.first", "sel.last")
        window.clipboard_append(selected_text)
        text_area.delete("sel.first", "sel.last")
    except tk.TclError:
        pass  # If nothing is selected, do nothing

def copy_text(event=None):
    try:
        # Check if there's a selection and copy the selected text
        window.clipboard_clear()
        selected_text = text_area.get("sel.first", "sel.last")
        window.clipboard_append(selected_text)
    except tk.TclError:
        pass  # If nothing is selected, do nothing

def paste_text(event=None):
    try:
        # Get the clipboard content and insert it at the current cursor position
        cursor_position = text_area.index(tk.INSERT)
        clipboard_text = window.clipboard_get()
        text_area.insert(cursor_position, clipboard_text)
    except tk.TclError:
        pass  # If the clipboard is empty, do nothing

# Create the main window
window = tk.Tk()
window.geometry("400x300")

# Create a text widget
text_area = tk.Text(window, wrap="word")
text_area.pack(expand=True, fill="both")

# Add cut, copy, and paste commands to the context menu
context_menu = tk.Menu(window, tearoff=0)
context_menu.add_command(label="Cut", command=cut_text)
context_menu.add_command(label="Copy", command=copy_text)
context_menu.add_command(label="Paste", command=paste_text)

# Right-click menu binding
def show_context_menu(event):
    context_menu.post(event.x_root, event.y_root)

text_area.bind("<Button-3>", show_context_menu)

# Bind keyboard shortcuts for cut, copy, and paste
window.bind("<Control-x>", cut_text)
window.bind("<Control-c>", copy_text)
window.bind("<Control-v>", paste_text)

window.mainloop()
