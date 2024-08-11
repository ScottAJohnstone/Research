import tkinter as tk

# Relative Imports
from UTILITY import date_time as dt
from UTILITY import other as o


def prelim():
    # Set Constants
    TODAY = dt.TODAY
    CDATE = f'{TODAY}'                                      # Current Date
    USR = o.usr                                             # Computer User
    COM_COUNTER = 1  # -Find out what this was used for
    DELAY_DEFAULT = 2500                                    # Default delay for Notifications
    FOCUS_DEFAULT = "[SUBJECT]"                             # Default property focus [subject or abutter]
    APPENDED_DEFAULT = "NULL"                               # Default file amendment status
    global JBNUM_RAW
    JBNUM_RAW = ""                                          # Raw user input from start window entry widget

def start():
    start = tk.Tk()
    start.title("Welcome - Research Log")
    stht = 150
    stwi = 280
    screenht = start.winfo_screenheight()
    screenwi = start.winfo_screenwidth()
    x = (screenwi / 2) - (stwi / 2)
    y = (screenht / 2) - (stht / 2)
    start.geometry(f'{stwi}x{stht}+{int(x)}+{int(y)}')
    start.resizable(False, False)
    
    placeholder_text = "Enter job number..."
    jbnumraw = tk.StringVar()

    def start_save():        # Save
        global JBNUM_RAW
        JBNUM_RAW = e_raw.get()
        start_destroy()
        init()

    def start_destroy():        # Remove all existing widgets
        for widget in start.winfo_children():
            widget.destroy()

    def on_key(event, entry, placeholder_text, default_fg):     # Handle the first key press e_raw
        if entry.get() == placeholder_text:
            entry.delete(0, tk.END)     # Clear entry
            entry.config(fg=default_fg)

    def placeholder(entry, placeholder_text="Enter job number...", placeholder_fg='grey', default_fg='white'):      # Create an Entry & placeholder
        entry.insert(0, placeholder_text)
        entry.focus_set()
        entry.icursor(0)
        entry.bind("<KeyPress>", lambda event: on_key(event, entry, placeholder_text, default_fg))
        entry.pack(pady=(15, 5))
        return entry

    #/l1 = tk.Label(start, text="Please enter the commission #", width="300", height="2", font=("Calibri", 13))
    #/l1.pack()
    e_raw = tk.Entry(start, fg='grey')
    e_raw = placeholder(e_raw, placeholder_text)
    b_save = tk.Button(start, text="Research", height="1", width="15", command=start_save)
    b_save.pack()
    b_help = tk.Button(start, text="Help", height="1", width="15")      #- work on help command
    b_help.pack()
    b_close = tk.Button(start, text="Exit", height="1", width="15", command=start_save)
    b_close.pack()

    start.mainloop()

def init():
    print(JBNUM_RAW)

start()
