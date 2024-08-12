import tkinter as tk

# Assuming 'start' is your root window
start = tk.Tk()

def do_rightclk(event):
    rcm = tk.Menu(start, tearoff=0)  # Use tk.Menu and associate it with 'start'
    rcm.add_command(label="Cut", command=lambda: print("Cut selected"))
    rcm.add_command(label="Copy", command=lambda: print("Copy selected"))
    rcm.add_command(label="Paste", command=lambda: print("Paste selected"))
    
    try:
        rcm.tk_popup(event.x_root, event.y_root)  # Display the popup menu
    finally:
        rcm.grab_release()  # Release the grab when done

# Bind the right-click (Button-3) event to the do_rightclk function
start.bind("<Button-3>", do_rightclk)

# Start the Tkinter event loop
start.mainloop()
