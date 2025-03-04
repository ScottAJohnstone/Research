import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
import sqlite3
import os
import re
import webbrowser
import socket
from datetime import datetime

# Import custom utilities if needed
try:
    from UTILITY import date_time as dt
    from UTILITY import other as o
    from UTILITY import Hovertip
    from UTILITY import string_test as st
except ImportError:
    print("UTILITY modules not found! Make sure they are available.")

# Global Variables
JBNUM_RAW = ""
current_window = None
delay = 3500  # Default delay for notifications


def create_db(JBNUM):
    """Create a database for the given JBNUM if it does not exist."""
    conn = sqlite3.connect(f'{JBNUM}.res')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS property (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        address TEXT NOT NULL,
                        city_town TEXT NOT NULL,
                        state TEXT NOT NULL,
                        parcel_id TEXT NOT NULL)''')
    conn.commit()
    conn.close()


def prop_log(JBNUM, address, city_town, state, parcel_id, db_file):
    """Log property data into the given database file."""
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO property (address, city_town, state, parcel_id) VALUES (?, ?, ?, ?)",
                   (address, city_town, state, parcel_id))
    conn.commit()
    conn.close()


def prop_history(history_type):
    """Fetch property history based on type (city_town, address, parcel_id)."""
    db_file = 'SAJHIST.db'
    if not os.path.isfile(db_file):
        return []
    
    try:
        with sqlite3.connect(db_file) as conn:
            cursor = conn.cursor()
            query = f"SELECT DISTINCT {history_type} FROM property ORDER BY id DESC LIMIT 5"
            cursor.execute(query)
            history = [row[0] for row in cursor.fetchall() if row[0]]
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return []
    
    return history


def prop_validate(address, city_town, state, parcel_id):
    """Validate property input fields."""
    return all([address, city_town, state, parcel_id])


def prop_maps(address, city_town, state, event=None):
    """Open property location in Google Maps."""
    query = f"{address}, {city_town}, {state}"
    url = f"https://www.google.com/maps/search/?api=1&query={query.replace(' ', '+')}"
    webbrowser.open(url)


def prop(JBNUM):
    """Create the Property Information logging UI."""
    prop_window = tk.Tk()
    prop_window.title("Property Information - Research Log")
    prop_window.geometry("475x325")
    prop_window.resizable(False, False)

    def submit_info():
        """Submit property info to the database."""
        address, city_town, state, parcel_id = e_addy.get(), e_town.get(), e_state.get(), e_pid.get()
        if not prop_validate(address, city_town, state, parcel_id):
            messagebox.showerror("Error", "All fields must be filled out correctly!")
            return
        
        create_db(JBNUM)
        prop_log(JBNUM, address, city_town, state, parcel_id, f'{JBNUM}.res')
        prop_log(JBNUM, address, city_town, state, parcel_id, 'SAJHIST.db')
        messagebox.showinfo("Success", "Property information recorded!")
        clear_form()

    def clear_form():
        """Clear the property entry form."""
        e_addy.set('')
        e_town.set('')
        e_state.set('')
        e_pid.set('')
        e_addy['values'] = prop_history("address")
        e_town['values'] = prop_history("city_town")
        e_pid['values'] = prop_history("parcel_id")

    # UI Elements
    tk.Label(prop_window, text="Address:").pack()
    e_addy = ttk.Combobox(prop_window, values=prop_history("address"), width=37)
    e_addy.pack()

    tk.Label(prop_window, text="City/Town:").pack()
    e_town = ttk.Combobox(prop_window, values=prop_history("city_town"), width=37)
    e_town.pack()

    tk.Label(prop_window, text="State:").pack()
    states = ["Alabama", "Alaska", "Arizona", "Arkansas", "California"]  # Add all states
    e_state = ttk.Combobox(prop_window, values=states, width=37)
    e_state.pack()

    tk.Label(prop_window, text="Parcel ID:").pack()
    e_pid = ttk.Combobox(prop_window, values=prop_history("parcel_id"), width=37)
    e_pid.pack()

    # Buttons
    frame = tk.Frame(prop_window)
    frame.pack()
    
    tk.Button(frame, text="Submit", command=submit_info).pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="Clear", command=clear_form).pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="Open in Maps", command=lambda: prop_maps(e_addy.get(), e_town.get(), e_state.get())).pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="Exit", command=prop_window.destroy).pack(side=tk.LEFT, padx=5)

    prop_window.mainloop()


def start():
    """Create the start window UI."""
    start_window = tk.Tk()
    start_window.title("Welcome - Research Log")
    start_window.geometry("325x182")
    start_window.resizable(False, False)

    def start_save():
        """Handle entry validation and open Property Info window."""
        job_num = e_raw.get().strip()
        if not job_num or job_num == "Enter job number...":
            messagebox.showerror("Error", "Entry cannot be left blank!")
            return
        if re.search(r'[!@#$%^&*(),.":{}|<>+=\[\]\\/;\'`~]', job_num):
            messagebox.showerror("Error", "Only hyphens are allowed as special characters!")
            return
        
        start_window.destroy()
        prop(job_num)

    # UI Elements
    e_raw = tk.Entry(start_window, width=17, fg='grey')
    e_raw.insert(0, "Enter job number...")
    e_raw.pack(pady=10)

    tk.Button(start_window, text="Research", width=15, command=start_save).pack()
    tk.Button(start_window, text="Exit", width=15, command=start_window.destroy).pack()

    start_window.mainloop()


if __name__ == "__main__":
    start()
