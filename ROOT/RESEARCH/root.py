
#. Research V2:	ROOT 
#. Command line program to handle the organization and implementation of Title/Land Record documents and files.	

#/                                                                                                               #/
#/                                                                                                               #/

import tkinter as tk
from tkinter import messagebox
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

def exit(start):
    # Create a messagebox popup to confirm exit
    if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
        start.destroy()  # Exit the program

def start():
    global current_window
    global delay
    delay = 3500    # Set the delay for notifications

    def focusset():
        e_raw.select_range(0, tk.END)
        e_raw.focus_set()

    def start_save():                                                                               #- FIX DASH CAPABILITY
        badchars = re.compile(r'[!@#$%^&*(),.?":{}|<>+=\[\]\\/;\'`~]')       # Define unwanted characters
        if e_raw.get() == "":                                                         #* fail
            info(current_window, "Entry can not be left blank...")
            focusset()
        elif e_raw.get() == "Enter job number...":                                    #* fail
            info(current_window, "Entry can not be left blank...")
            focusset() 
        elif e_raw.get() == "-":                                                      #* fail
            info(current_window, "Please enter a number...")
            focusset()
        elif e_raw.get().isalpha():                                                 #* fail
            info(current_window, "Please enter a number...")
            focusset()
        elif badchars.search(e_raw.get()):                                          #* fail     
            info(current_window, "The only special character allowed is a hyphen...")
            focusset()
        else:
            if e_raw.get().isnumeric() and float(e_raw.get()) > 0:                  #* pass     if is num greater than 0 only
                info(current_window, "Entry accepted...")
                focusset()
                JBNUM = e_raw.get()
                DASH=""
            elif "-" in e_raw.get():
                JBNUM, DASH = e_raw.get().split("-")                                   
                if JBNUM == "":                                                    #* fail
                    info(current_window, "Base job number must be greater than zero...")
                if DASH == "":                                                    #* fail
                    info(current_window, "Please enter a dash or remove the '-'...")
                elif JBNUM.isalpha():                                               #* fail
                    info(current_window, "Base job number must contain a number...")
                else:                                                              #* pass
                    def yes():
                        start_destroy()
                    def no():
                        focusset()
                        f_info.destroy()
                        f_btn.destroy()
                    JBNUM, DASH = e_raw.get().split("-")                                   
                    JBNUM = re.sub(r'[a-zA-Z]', '', JBNUM)
                    info(current_window, text=f'Please confirm base job number [{JBNUM}]...', show_buttons=True, yes_command=yes, no_command=no)
            elif not e_raw.get().isnumeric() and not e_raw.get().isalpha():
                JBNUM = re.sub(r'[a-zA-Z]', '', e_raw.get())
                DASH = re.sub(r'\d+', '', e_raw.get())
                def yes():
                    start_destroy()
                def no():
                    f_info.destroy()
                    f_btn.destroy()
                JBNUM = re.sub(r'[a-zA-Z]', '', JBNUM)
                print(JBNUM)
                print(DASH)
                info(current_window, text=f'Please confirm base job number [{JBNUM}]...', show_buttons=True, yes_command=yes, no_command=no)
   
    def start_destroy():  # Remove all existing widgets
        for widget in start.winfo_children():
            widget.destroy()
        
    def on_key(event, entry, placeholder_text, default_fg):
        if event.keysym == "Return":   # Handle the Enter key (Return key)
            start_save()                                    
        if entry.get() == placeholder_text:
            entry.delete(0, tk.END)  # Clear entry
            entry.config(fg=default_fg)
        elif event.keysym == 'Escape':                                                      #- takes 2 'escape' to exit... yes/no?
            exit(start)
        # elif event.keysym == 'a':
        #       print("The 'a' key was pressed")


    # def on_key(event, entry, pla1 q56ceholder_text, default_fg):
    #     # Handle the first key press to clear placeholder text
    #     if entry.get() == placeholder_text:
    #         entry.delete(0, tk.END)  # Clear entry
    #         entry.config(fg=default_fg)                                                   #- this is broken needs work

#     #key bindings
#     if event.keysym == "Return":  # Handle the Enter key (Return key)
#         print("Enter key pressed - submit action")
#         # You can add a call to a submit function here
#     elif event.keysym == "Escape":  # Handle the Escape key
#         print("Escape key pressed - cancel action")
#         entry.delete(0, tk.END)  # Clear entry or perform another action
#     elif event.keysym == "F1":  # Handle the F1 key
#         print("F1 key pressed - show help")
#         # Call a function to show help or any other task

#     # Add more key bindings as needed


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
    
    def do_help(event=None):                                                             #- need to figure this out
        print("help")
        return "break"  # Prevents the '?' from being entered into the Entry widget
    
    # Create the main window
    start = tk.Tk()
    start.title("Welcome - Research Log")
    stht = 182
    stwi = 325
    screenht = start.winfo_screenheight()
    screenwi = start.winfo_screenwidth()
    x = (screenwi / 2) - (stwi / 2)
    y = (screenht / 2) - (stht / 2)
    start.geometry(f'{stwi}x{stht}+{int(x)}+{int(y)}')
    start.resizable(False, False)
  
    start.bind("<Button-2>", do_rightclk)  # Bind the right-click event
    start.bind('<Return>', on_key)
    # start.bind("<Key-?>",do_help)                                                             #- need to figure this out

    #start.bind('<Control-c>', _help)  # Ctrl+C key combination


    placeholder_text = "Enter job number..."
    jbnumraw = tk.StringVar()

    # Create a frame for the info label
    f_info = tk.Frame(start)
    f_info.pack(side=tk.BOTTOM, fill=tk.X)

    current_window = start

    e_raw = tk.Entry(start, fg='grey',width=17)
    e_raw = placeholder(e_raw, placeholder_text)
    b_save = tk.Button(start, text="Research", height="1", width="15", command=start_save)
    b_save.pack()
    b_help = tk.Button(start, text="Help", height="1", width="15")                                      # - work on help command
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

def info(window, text, show_buttons=False, yes_command=None, no_command=None):
    global delay
    global f_btn

    # Create or get the info frame
    for widget in window.winfo_children():
        if isinstance(widget, tk.Frame):
            f_info = widget
            break
    else:
        f_info = tk.Frame(window)
        f_info.pack(side=tk.BOTTOM, fill=tk.X)

    # Create the info label and add it to the frame
    l_inf = tk.Label(f_info, text=text, font=('Helvetica', 10))
    l_inf.pack(side=tk.BOTTOM, anchor=tk.SE, padx=10, pady=(0, 5))

    if show_buttons:
        # Create Yes and No buttons
        f_btn = tk.Frame(f_info)
        f_btn.pack(side=tk.BOTTOM)

        b_y = tk.Button(f_btn, text="Yes", width=5, command=lambda: [l_inf.destroy(), yes_command()])
        b_y.pack(side=tk.RIGHT, padx=(1,0))

        b_n = tk.Button(f_btn, text="No", width=5, command=lambda: [l_inf.destroy(), no_command()])
        b_n.pack(side=tk.LEFT, anchor=tk.SE, padx=(1,0))

    window.update_idletasks()  # Force the window to update its display

    # If no buttons are shown, destroy the info label after a delay
    if not show_buttons:
        window.after(delay, lambda: l_inf.destroy())



start()                                                             # Call start function to run the application
