
#. Research V2:	ROOT 
#. Command line program to handle the organization and implementation of Title/Land Record documents and files.	

#/                                                                                                               #/
#/                                                                                                               #/



import tkinter as tk
import re

# Relative Imports
from UTILITY import date_time as dt
from UTILITY import other as o

def prelim():
    global JBNUM_RAW
    global current_window
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
    delay = 3500    # Set the delay for notifications

    def start_save():
        badchars = re.compile(r'[!@#$%^&*(),.?":{}|<>]')     # Define unwanted characters
        if e_raw.get() == "":                                                         #* fail
            info(current_window, "Entry can not be left blank...")
            e_raw.select_range(0, tk.END)                       
            e_raw.focus_set() 
        elif e_raw.get() == "Enter job number...":                                    #* fail
            info(current_window, "Entry can not be left blank...")
            e_raw.select_range(0, tk.END)
            e_raw.focus_set() 
        elif e_raw.get() == "-":                                                      #* fail
            info(current_window, "Please enter a number...")
            e_raw.select_range(0, tk.END)
            e_raw.focus_set()
        elif e_raw.get().isalpha():                                                 #* fail
            info(current_window, "Please enter a number...")
            e_raw.select_range(0, tk.END)
            e_raw.focus_set()
        elif badchars.search(e_raw.get()):                                          #* fail     
            info(current_window, "The only special character allowed is a hyphen...")
            e_raw.select_range(0, tk.END)
            e_raw.focus_set()
        else:
            if e_raw.get().isnumeric() and float(e_raw.get()) > 0:                  #* pass
                info(current_window, "Entry accepted...")
                e_raw.select_range(0, tk.END)
                e_raw.focus_set()
            elif "-" in e_raw.get():
                JBNUM, DASH = e_raw.get().split("-")                                   
                if JBNUM == "":                                                    #* fail
                    info(current_window, "Base job number must be greater than zero...")
                elif JBNUM.isalpha():                                               #* fail
                    info(current_window, "Base job number must contain a number...")
                else:
                    def yes():
                        start_destroy()
                    def no():                                                       #- fix the broken loop here
                        for widget in f_info.winfo_children():
                            widget.destroy()
                        for widget in f.winfo_children():
                            widget.destroy()
                    JBNUM = re.sub(r'[a-zA-Z]', '', JBNUM)
                    f = tk.Frame(start)
                    f.pack()
                    l = tk.Label(f_info, text=f'Please confirm base job number [{JBNUM}]...', font=('Helvetica', 10))
                    l.pack(side=tk.BOTTOM, anchor=tk.S, padx=10, pady=(0, 5))
                    b_y = tk.Button(f, text="Yes", width=4, command=yes)
                    b_y.pack(side=tk.RIGHT, anchor=tk.SE, padx=10)
                    b_n = tk.Button(f, text="No", width=4, command=no)
                    b_n.pack(side=tk.RIGHT, anchor=tk.SW, padx=10)
            else:                                                                   #* fail
                info(current_window, "Please enter a number greater than zero...") 
                e_raw.select_range(0, tk.END)
                e_raw.focus_set()

    def start_destroy():  # Remove all existing widgets
        for widget in f_info.winfo_children():
            widget.destroy()
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

    def do_rightclk(event):
        rcm = tk.Menu(start, tearoff=0)  # Create a context menu
        rcm.add_command(label="Cut", command=lambda: print("Cut selected"))
        rcm.add_command(label="Copy", command=lambda: print("Copy selected"))
        rcm.add_command(label="Paste", command=lambda: print("Paste selected"))
        rcm.add_separator()
        rcm.add_command(label="Jump to Network", command=lambda: print("Jumping"))
        
        # Display the menu at the mouse cursor position
        try:
            rcm.tk_popup(event.x_root, event.y_root)
        finally:
            rcm.grab_release()  # Release the grab when done

    # Create the main window
    start = tk.Tk()
    start.title("Welcome - Research Log")
    stht = 175
    stwi = 325
    screenht = start.winfo_screenheight()
    screenwi = start.winfo_screenwidth()
    x = (screenwi / 2) - (stwi / 2)
    y = (screenht / 2) - (stht / 2)
    start.geometry(f'{stwi}x{stht}+{int(x)}+{int(y)}')
    start.resizable(False, False)
  
    start.bind("<Button-2>", do_rightclk)  # Bind the right-click event

    placeholder_text = "Enter job number..."
    jbnumraw = tk.StringVar()

    # Create a frame for the info label
    f_info = tk.Frame(start)
    f_info.pack(side=tk.BOTTOM, fill=tk.X)

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
    print(JBNUM_RAW)                                           #- Need to complete
    
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
            f_info = widget
            break
    else:
        f_info = tk.Frame(window)
        f_info.pack(side=tk.BOTTOM, fill=tk.X)

    # Create the info label and add it to the frame
    info_label = tk.Label(f_info, text=text, font=('Helvetica', 10))
    info_label.pack(side=tk.BOTTOM, anchor=tk.SE, padx=10, pady=10)
    window.update_idletasks()    # Force the window to update its display
    window.after(delay, lambda: info_label.destroy())

# Call start function to run the application
start()
