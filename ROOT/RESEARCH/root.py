import tkinter as tk
import re

# Relative Imports
from UTILITY import date_time as dt
from UTILITY import other as o

def prelim():
    global JBNUM_RAW
    global current_window
    # Set Constants
    TODAY = dt.TODAY
    CDATE = f'{TODAY}'                                      # Current Date
    USR = o.usr                                             # Computer User
    COM_COUNTER = 1                                         # -Find out what this was used for
    DELAY_DEFAULT = 2500                                    # Default delay for Notifications
    FOCUS_DEFAULT = "[SUBJECT]"                             # Default property focus [subject or abutter]
    APPENDED_DEFAULT = "NULL"                               # Default file amendment status
    JBNUM_RAW = ""                                          # Raw user input from start window entry widget
    current_window = None                                   # Initialize the global variable

def start():
    global current_window
    global delay
    delay = 2500  # Set the delay for notifications

    def start_save():  # Save
        pattern = re.compile(r'[!@#$%^&*(),.?":{}|<>]')     # Define unwanted characters
        if pattern.search(e_raw.get()):     # Search for special characters
            print("NOT GOOD")
        else:
            if int(e_raw.get()) > 0:
                print("good")
                info(current_window, "Job number accepted")  # Show info label
            else:
                print("NOT GOOD")

    def start_destroy():  # Remove all existing widgets
        for widget in start.winfo_children():
            widget.destroy()

    def on_key(event, entry, placeholder_text, default_fg):  # Handle the first key press e_raw
        if entry.get() == placeholder_text:
            entry.delete(0, tk.END)  # Clear entry
            entry.config(fg=default_fg)

    def placeholder(entry, placeholder_text="Enter job number...", placeholder_fg='grey', default_fg='white'):  # Create an Entry & placeholder
        entry.insert(0, placeholder_text)
        entry.focus_set()
        entry.icursor(0)
        entry.bind("<KeyPress>", lambda event: on_key(event, entry, placeholder_text, default_fg))
        entry.pack(pady=(15, 5))
        return entry

    # Create the main window
    global current_window
    start = tk.Tk()
    start.title("Welcome - Research Log")
    stht = 170
    stwi = 350
    screenht = start.winfo_screenheight()
    screenwi = start.winfo_screenwidth()
    x = (screenwi / 2) - (stwi / 2)
    y = (screenht / 2) - (stht / 2)
    start.geometry(f'{stwi}x{stht}+{int(x)}+{int(y)}')
    start.resizable(False, False)
    
    placeholder_text = "Enter job number..."
    jbnumraw = tk.StringVar()

    # Create a frame for the info label
    info_frame = tk.Frame(start)
    info_frame.pack(side=tk.BOTTOM, fill=tk.X)

    current_window = start

    e_raw = tk.Entry(start, fg='grey')
    e_raw = placeholder(e_raw, placeholder_text)
    b_save = tk.Button(start, text="Research", height="1", width="15", command=start_save)
    b_save.pack()
    b_help = tk.Button(start, text="Help", height="1", width="15")  # - work on help command
    b_help.pack()
    b_close = tk.Button(start, text="Exit", height="1", width="15", command=terminate)
    b_close.pack()

    start.mainloop()

def init():
    print(JBNUM_RAW)

def terminate():
    global current_window
    if current_window is not None:
        current_window.destroy()  # Close the window
        current_window = None  # Reset the reference

def info(window, text):
    global delay

    # Create or get the info frame
    for widget in window.winfo_children():
        if isinstance(widget, tk.Frame):
            info_frame = widget
            break
    else:
        info_frame = tk.Frame(window)
        info_frame.pack(side=tk.BOTTOM, fill=tk.X)

    # Create the info label and add it to the frame
    info_label = tk.Label(info_frame, text=text, font=('Helvetica', 10))
    info_label.pack(side=tk.BOTTOM, anchor=tk.SE, padx=10, pady=10)
    
    # Force the window to update its display
    window.update_idletasks()
    
    # Destroy the label after the delay
    window.after(delay, lambda: info_label.destroy())

start()
