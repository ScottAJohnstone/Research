
#. Research V2:	ROOT 
#. Command line program to handle the organization and implementation of Title/Land Record documents and files.	

#/                                                                                                               #/
#/                                                                                                               #/

#- fix history







import tkinter as tk
from tkinter import ttk, messagebox
import re
import sqlite3
import webbrowser
import os

# Relative Imports
from UTILITY import date_time as dt
from UTILITY import other as o

def prelim():
    global JBNUM_RAW
    global current_window
    TODAY = dt.TODAY
    CDATE = f'{TODAY}'                                      # Current Date
    NM='SAJ'
    USR = o.usr                                             # Computer User
    COM_COUNTER = 1                                         # -Find out what this was used for
    DELAY_DEFAULT = 2500                                    # Default delay for Notifications
    FOCUS_DEFAULT = "[SUBJECT]"                             # Default property focus [subject or abutter]
    APPENDED_DEFAULT = "NULL"                               # Default file amendment status
    JBNUM_RAW = ""                                          # Raw user input from start window entry widget
    current_window = None                                   # Initialize the global variable

def create_db(JBNUM):
    conn = sqlite3.connect(f'{JBNUM}.res')  # Create the database file if it does not exist
    cursor = conn.cursor()
    
    # Create the table only if it does not exist
    cursor.execute('''CREATE TABLE IF NOT EXISTS property (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        address TEXT NOT NULL,
                        city_town TEXT NOT NULL,
                        state TEXT NOT NULL,
                        parcel_id TEXT NOT NULL)''')
    
    conn.commit()
    conn.close()

def log_property_info(JBNUM, address, city_town, state, parcel_id, db_file):
    conn = sqlite3.connect(db_file)  # Connect to the specified database file
    cursor = conn.cursor()
    cursor.execute("INSERT INTO property (address, city_town, state, parcel_id) VALUES (?, ?, ?, ?)",
                   (address, city_town, state, parcel_id))
    conn.commit()
    conn.close()

def load_history(history_type):
    db_file = 'SAJHIST.db'
    if not os.path.isfile(db_file):
        return []
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    if history_type == "city_town":
        cursor.execute("SELECT DISTINCT city_town FROM property")
    elif history_type == "address":
        cursor.execute("SELECT DISTINCT address FROM property")
    elif history_type == "parcel_id":
        cursor.execute("SELECT DISTINCT parcel_id FROM property")
    else:
        return []
    history = [row[0] for row in cursor.fetchall()]
    conn.close()
    return history



def validate_inputs(address, city_town, state, parcel_id):
    if not address or not city_town or state == "Select State" or not parcel_id:
        return False
    return True

def open_google_maps(address, city_town, state):
    query = f"{address}, {city_town}, {state}"
    url = f"https://www.google.com/maps/search/?api=1&query={query.replace(' ', '+')}"
    webbrowser.open(url)

def prop(JBNUM):
    def submit_info():
        address = address_entry.get()
        city_town = city_town_entry.get()
        state = state_combo.get()
        parcel_id = parcel_id_entry.get()

        if not validate_inputs(address, city_town, state, parcel_id):
            messagebox.showerror("Error", "All fields must be filled out correctly!")
        else:
            create_db(JBNUM)
            log_property_info(JBNUM, address, city_town, state, parcel_id, f'{JBNUM}.res')
            log_property_info(JBNUM, address, city_town, state, parcel_id, 'SAJHIST.db')
            messagebox.showinfo("Success", "Property information recorded!")
            clear_form()

    def clear_form():
        # Clear and update combobox values
        address_entry.set('')  
        city_town_entry.set('')  
        state_combo.set('Select State')
        parcel_id_entry.set('')  

        # Update comboboxes with the latest history
        address_entry['values'] = load_history("address")
        city_town_entry['values'] = load_history("city_town")
        parcel_id_entry['values'] = load_history("parcel_id")

    # Initialize the main application window
    prop = tk.Tk()
    prop.title("Property Information - Research Log")
    stht = 325
    stwi = 475
    screenht = prop.winfo_screenheight()
    screenwi = prop.winfo_screenwidth()
    x = (screenwi / 2) - (stwi / 2)
    y = (screenht / 2) - (stht / 2)
    prop.geometry(f'{stwi}x{stht}+{int(x)}+{int(y)}')
    prop.resizable(False, False)

    # Labels and entry fields for property information
    tk.Label(prop, text="Address:").pack(pady=5)
    address_entry = ttk.Combobox(prop, values=load_history("address"), width=37)
    address_entry.pack()

    tk.Label(prop, text="City/Town:").pack(pady=5)
    city_town_entry = ttk.Combobox(prop, values=load_history("city_town"), width=37)
    city_town_entry.pack()

    tk.Label(prop, text="State:").pack(pady=5)
    states = ["Select State", "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
              "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
              "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri",
              "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina",
              "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
              "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia",
              "Wisconsin", "Wyoming"]
    state_combo = ttk.Combobox(prop, values=states, width=37)
    state_combo.pack()
    state_combo.set("Select State")

    tk.Label(prop, text="Parcel ID:").pack(pady=5)
    parcel_id_entry = ttk.Combobox(prop, values=load_history("parcel_id"), width=37)
    parcel_id_entry.pack()

    # Frame to hold buttons horizontally
    button_frame = tk.Frame(prop)
    button_frame.pack(pady=20)

    # Uniform button width
    button_width = 8
    pad_x = 2

    # Submit button
    submit_button = tk.Button(button_frame, text="Submit", command=submit_info, width=button_width)
    submit_button.pack(side=tk.LEFT, padx=pad_x)

    # Button to open the address in Google Maps
    maps_button = tk.Button(button_frame, text="Open in Maps",
                            command=lambda: open_google_maps(address_entry.get(), city_town_entry.get(), state_combo.get()),
                            width=button_width)
    maps_button.pack(side=tk.LEFT, padx=pad_x)

    # Clear button to reset the form
    clear_button = tk.Button(button_frame, text="Clear", command=clear_form, width=button_width)
    clear_button.pack(side=tk.LEFT, padx=pad_x)

    # Exit button to close the application
    exit_button = tk.Button(button_frame, text="Exit", command=terminate, width=button_width)
    exit_button.pack(side=tk.LEFT, padx=pad_x)

    prop.mainloop()



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

    def start_save():         
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
                start_destroy()
                prop(JBNUM)

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
                        prop(JBNUM)
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
                    prop(JBNUM)
                def no():
                    f_info.destroy()
                    f_btn.destroy()
                JBNUM = re.sub(r'[a-zA-Z]', '', JBNUM)
                prop(JBNUM)
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
        elif event.keysym == 'Escape':                                                      # takes 2 'escape' to exit... yes/no?
            exit(start)

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
    
    def do_help(event=None):                                                             # need to figure this out
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
    # start.bind("<Key-?>",do_help)                                                             # need to figure this out

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
    print(JBNUM_RAW)                                           # Need to complete
    
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
