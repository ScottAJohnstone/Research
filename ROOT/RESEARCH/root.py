
#. Research V2:	ROOT 
#. Command line program to handle the organization and implementation of Title/Land Record documents and files.	

#/                                                                                                               #/
#/                                                                                                               #/

#!Fix combo boxes

from curses import window
from curses.ascii import FF
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import re
import sqlite3
import webbrowser
import os
from idlelib.tooltip import Hovertip
import socket

# Relative Imports
from UTILITY import date_time as dt
from UTILITY import other as o
from UTILITY import Hovertip


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


def prop_log(JBNUM, address, city_town, state, parcel_id, db_file):
    conn = sqlite3.connect(db_file)  # Connect to the specified database file
    cursor = conn.cursor()
    cursor.execute("INSERT INTO property (address, city_town, state, parcel_id) VALUES (?, ?, ?, ?)",
                   (address, city_town, state, parcel_id))
    conn.commit()
    conn.close()


def prop_history(history_type):
    db_file = 'SAJHIST.db'
    if not os.path.isfile(db_file):
        return []
    
    try:
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            if history_type == "city_town":
                query = """
                    SELECT DISTINCT city_town 
                    FROM property 
                    ORDER BY id DESC 
                    LIMIT 5
                """
            elif history_type == "address":
                query = """
                    SELECT DISTINCT address 
                    FROM property 
                    ORDER BY id DESC 
                    LIMIT 5
                """
            elif history_type == "parcel_id":
                query = """
                    SELECT DISTINCT parcel_id 
                    FROM property 
                    ORDER BY id DESC 
                    LIMIT 5
                """
            else:
                return []

            cursor.execute(query)
            history = [row[0] for row in cursor.fetchall() if row[0]]  # Filter out empty/null values
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    return history


def prop_validate(address, city_town, state, parcel_id):
    if not address or not city_town or state == "" or not parcel_id:
        return False
    return True


def prop_maps(address, city_town, state,event=None):
    query = f"{address}, {city_town}, {state}"
    url = f"https://www.google.com/maps/search/?api=1&query={query.replace(' ', '+')}"
    webbrowser.open(url)


def prop(JBNUM):
    def submit_info():
        address = e_addy.get()
        city_town = e_town.get()
        state = e_state.get()
        parcel_id = e_pid.get()

        if not prop_validate(address, city_town, state, parcel_id):
            messagebox.showerror("Error", "All fields must be filled out correctly!")
        else:
            create_db(JBNUM)
            prop_log(JBNUM, address, city_town, state, parcel_id, f'{JBNUM}.res')
            prop_log(JBNUM, address, city_town, state, parcel_id, 'SAJHIST.db')
            messagebox.showinfo("Success", "Property information recorded!")
            clear_form()

    def clear_form(event=None):
        # Clear and update combobox values
        e_addy.set('')  
        e_town.set('')  
        e_state.set('')
        e_pid.set('')  

        # Update comboboxes with the latest history
        e_addy['values'] = prop_history("address")
        e_town['values'] = prop_history("city_town")
        e_pid['values'] = prop_history("parcel_id")

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

    def clear_history():
        db_file = 'SAJHIST.db'                                                      #- fix this to change per person
        if os.path.isfile(db_file):
            try:
                with sqlite3.connect(db_file) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM property")
                    conn.commit()
                # Clear the values in the combo boxes
                e_addy['values'] = []
                e_town['values'] = []
                e_pid['values'] = []
                messagebox.showinfo("Success", "History cleared successfully!")
            except sqlite3.Error as e:
                print(f"Database error: {e}")
                messagebox.showerror("Error", "Failed to clear history!")
        else:
            messagebox.showinfo("No History", "No history found to clear.")

    def prop_do_rightclk(event):
        rcm = tk.Menu(prop, tearoff=0)  # Create a context menu
        rcm.add_command(label="Cut", command=lambda: print("Cut selected"))
        rcm.add_command(label="Copy", command=lambda: print("Copy selected"))
        rcm.add_command(label="Paste", command=lambda: print("Paste selected"))
        rcm.add_separator()
        rcm.add_command(label="Clear History", command=clear_history)
        
        # Display the menu at the mouse cursor position
        try:
            rcm.tk_popup(event.x_root, event.y_root)
        finally:
            rcm.grab_release()  # Release the grab when done
  
    prop.bind("<Button-2>", prop_do_rightclk)  # Bind the right-click event
    prop.bind("<Control-BackSpace>", clear_form)
    #prop.bind("<Control-m>", prop_maps)                                                                    #! fix



    # Labels and entry fields for property information
    tk.Label(prop, text="Address:").pack(pady=5)
    e_addy = ttk.Combobox(prop, values=prop_history("address"), width=37)
    e_addy.pack()

    tk.Label(prop, text="City/Town:").pack(pady=5)
    e_town = ttk.Combobox(prop, values=prop_history("city_town"), width=37)
    e_town.pack()

    tk.Label(prop, text="State:").pack(pady=5)
    states = ["Select State", "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
              "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
              "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan", "Minnesota", "Mississippi", "Missouri",
              "Montana", "Nebraska", "Nevada", "New Hampshire", "New Jersey", "New Mexico", "New York", "North Carolina",
              "North Dakota", "Ohio", "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina",
              "South Dakota", "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia",
              "Wisconsin", "Wyoming"]
    e_state = ttk.Combobox(prop, values=states, width=37)
    e_state.pack()
    #state_combo.set("Select State")

    tk.Label(prop, text="Parcel ID:").pack(pady=5)
    e_pid = ttk.Combobox(prop, values=prop_history("parcel_id"), width=37)
    e_pid.pack()

    # Frame to hold buttons horizontally
    f_btn = tk.Frame(prop)
    f_btn.pack(pady=20)

    # Uniform button width
    button_width = 8
    pad_x = 2

    # Submit button
    b_submit = tk.Button(f_btn, text="Submit", command=submit_info, width=button_width)
    b_submit.pack(side=tk.LEFT, padx=pad_x)

    # Button to open the address in Google Maps
    b_map = tk.Button(f_btn, text="Open in Maps",command=lambda: prop_maps(e_addy.get(), e_town.get(), e_state.get()),
                            width=button_width)
    b_map.pack(side=tk.LEFT, padx=pad_x)

    # Clear button to reset the form
    b_clear = tk.Button(f_btn, text="Clear", command=clear_form, width=button_width)
    b_clear.pack(side=tk.LEFT, padx=pad_x)

    # Exit button to close the application
    b_exit = tk.Button(f_btn, text="Exit", command=terminate, width=button_width)
    b_exit.pack(side=tk.LEFT, padx=pad_x)

    b_submit_Tip = Hovertip(b_submit,'Hotkey = [Enter]')
    b_map_Tip = Hovertip(b_map,'Open in Google Maps: \nHotkey = [cntrl + M]')
    b_clear_Tip = Hovertip(b_clear,'Clear Contents: \nHotkey = [cntrl + Backspace]')                              # - work on help command/shortcut
    b_exit_Tip = Hovertip(b_exit,'Exit: \n[Hotkey = [Esc]')

    prop.mainloop()


def exit(window):
    # Create a messagebox popup to confirm exit
    if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
        window.destroy()  # Exit the program


def start():
    global current_window
    global delay
    delay = 3500    # Set the delay for notifications

    def focusset():
        e_raw.select_range(0, tk.END)
        e_raw.focus_set()

    def start_save():         
        badchars = re.compile(r'[!@#$%^&*(),.":{}|<>+=\[\]\\/;\'`~]')       # Define unwanted characters
        if e_raw.get() == "SAJ":
            info(current_window, text=None, Settings=True)
            info(current_window, "")
            #print("Scott add Settings")
            focusset()
        elif e_raw.get() == "":                                                           #* fail
            info(current_window, "Entry can not be left blank...")
            focusset()
        elif e_raw.get() == "Enter job number...":                                      #* fail
            info(current_window, "Entry can not be left blank...")
            focusset()
        elif e_raw.get() == "?":                                                        #* pass
            info(current_window, "Entry accepted...")
            JBNUM = e_raw.get()
            DASH=""
            start.destroy()
            prop(JBNUM)
        elif e_raw.get() == "-":                                                        #* fail
            info(current_window, "Please enter a number...")
            focusset()
        elif e_raw.get().isalpha():                                                     #* fail
            info(current_window, "Please enter a number...")
            focusset()
        elif badchars.search(e_raw.get()):                                              #* fail
            info(current_window, "The only special character allowed is a hyphen...")
            focusset()
        else:
            if e_raw.get().isnumeric() and float(e_raw.get()) > 0:                  #* pass     if is num greater than 0 only
                info(current_window, "Entry accepted...")
                focusset()
                JBNUM = e_raw.get()
                DASH=""
                start.destroy()
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
                        start.destroy()
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
                    start.destroy()
                    prop(JBNUM)
                def no():
                    f_info.destroy()
                    f_btn.destroy()
                JBNUM = re.sub(r'[a-zA-Z]', '', JBNUM)
                prop(JBNUM)
                info(current_window, text=f'Please confirm base job number [{JBNUM}]...', show_buttons=True, yes_command=yes, no_command=no)
            
    def on_key(event, entry, placeholder_text, default_fg):
        if event.keysym == "Return":   # Handle the Enter key
            start_save()                                    
        if entry.get() == placeholder_text:
            entry.delete(0, tk.END)
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

    def feedback(feedback_type):
        # Get the current date and time
        current_time = dt.TODAY#datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get the computer name
        computer_name = socket.gethostname()
        
        # Create a simple dialog to get user input
        feedback = simpledialog.askstring("Feedback", f"Please leave a brief description of your {feedback_type}:")
        
        if feedback:
            # Define the log file name
            log_file = "Feedback.txt"
            
            # Append the feedback to the log file with date, time, and computer name
            with open(log_file, "a") as f:
                f.write(f"{current_time} | {computer_name} | {feedback_type.capitalize()}: {feedback}\n")
            
            # Show a confirmation message
            messagebox.showinfo("Submission Successful", f"Your {feedback_type} has been submitted.")
        else:
            messagebox.showwarning("No Input", "You must enter a feedback before submitting.")

    def start_do_rightclk(event):
        rcm = tk.Menu(start, tearoff=0)  # Create a context menu
        rcm.add_command(label="Cut", command=lambda: print("Cut selected"))                             #-Add function in all windows
        rcm.add_command(label="Copy", command=lambda: print("Copy selected"))                           #-Add function in all windows
        rcm.add_command(label="Paste", command=lambda: print("Paste selected"))                         #-Add function in all windows
        rcm.add_separator()
        rcm.add_command(label="Jump to Network", command=lambda: print("Jumping"))
        rcm.add_separator()
        rcm.add_command(label="Report an Error", command=lambda: feedback("error"))
        rcm.add_command(label="Leave a Comment", command=lambda: feedback("comment"))
        rcm.add_separator()
        rcm.add_command(label="Exit", command=rcm.destroy)
        
        # Display the menu at the mouse cursor position
        try:
            rcm.tk_popup(event.x_root, event.y_root)
        finally:
            rcm.grab_release()  # Release the grab when done
  
    start.bind("<Button-2>", start_do_rightclk)  # Bind the right-click event
    #start.bind('<Return>', on_key)                                              #! fix


    placeholder_text = "Enter job number..."
    jbnumraw = tk.StringVar()

    # Create a frame for the info label
    f_info = tk.Frame(start)
    f_info.pack(side=tk.BOTTOM, fill=tk.X)
    f_info.lift()

    current_window = start

    e_raw = tk.Entry(start, fg='grey',width=17)
    e_raw = placeholder(e_raw, placeholder_text)
    b_save = tk.Button(start, text="Research", height="1", width="15", command=start_save,foreground="black")
    b_save.pack()
    b_help = tk.Button(start, text="Help", height="1", width="15")                                      # - work on help command
    b_help.pack()
    b_close = tk.Button(start, text="Exit", height="1", width="15", command=terminate)
    b_close.pack()

    e_raw_Tip = Hovertip(e_raw,'Enter [?] to research without a Commission Number')
    b_save_Tip = Hovertip(b_save,'Start Research: \nHotkey = [Enter]')
    b_help_Tip = Hovertip(b_help,'Start Research: \nHotkey = [cntrl + H]')                              # - work on help command/shortcut
    b_close_Tip = Hovertip(b_close,'Start Research: \nHotkey = [Esc x2]')

    start.mainloop()

def init():
    print(JBNUM_RAW)                                           # Need to complete
    

def terminate():
    global current_window
    if current_window is not None:
        current_window.destroy()  # Close the window
        current_window = None  # Reset the reference

def info(window, text, show_buttons=False, Settings=False, yes_command=None, no_command=None):
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
    l_inf = tk.Label(f_info, text=text, font=('Helvetica', 10))                                 #! fix duplicates info labels here
    l_inf.pack(side=tk.BOTTOM, anchor=tk.SE, padx=10, pady=(0, 5))

    if show_buttons:
        # Create Yes and No buttons
        f_btn = tk.Frame(f_info)
        f_btn.pack(side=tk.BOTTOM)

        b_y = tk.Button(f_btn, text="Yes", width=5, command=lambda: [l_inf.destroy()]) #b_y = tk.Button(f_btn, text="Yes", width=5, command=lambda: [l_inf.destroy(), yes_command()])

        b_y.pack(side=tk.RIGHT, padx=(1,0))

        b_n = tk.Button(f_btn, text="No", width=5, command=lambda: [l_inf.destroy()]) #b_n = tk.Button(f_btn, text="No", width=5, command=lambda: [l_inf.destroy(), no_command()])

        b_n.pack(side=tk.LEFT, anchor=tk.SE, padx=(1,0))

    if Settings:

        def SettingsMenu(event):
            # Create the popup menu
            Settings_menu = tk.Menu(window, tearoff=0)
            Settings_menu.add_command(label="Configure", command=lambda: print("Option 2 selected"))                    #- Add Settings
            Settings_menu.add_command(label="Clear History", command=lambda: print("Option 2 selected"))               #- Add Settings

            Settings_menu.add_separator()
            Settings_menu.add_command(label="Exit", command=Settings_menu.destroy)

            # Show the Settings menu at the cursor's location
            Settings_menu.post(event.x_root, event.y_root)

        f_btn = tk.Frame(window)
        f_btn.pack(side=tk.BOTTOM)
        f_btn.lower()
        f_btn.config(width=6, height=2)
        b_Settings = tk.Button(f_btn, text="Settings", width=5)
        b_Settings.pack()
        b_Settings.bind("<Button-1>", SettingsMenu)

    window.update_idletasks()  # Force the window to update its display

    # # If no buttons are shown, destroy the info label after a delay
    # if not show_buttons:
    #     window.after(delay, lambda: l_inf.destroy())

start()                                              