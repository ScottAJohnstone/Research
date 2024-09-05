import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import webbrowser

def create_db():
    conn = sqlite3.connect('property_info.res')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS property (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        address TEXT NOT NULL,
                        city_town TEXT NOT NULL,
                        state TEXT NOT NULL,
                        parcel_id TEXT NOT NULL)''')
    conn.commit()
    conn.close()













def log_property_info(address, city_town, state, parcel_id):
    conn = sqlite3.connect('property_info.res')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO property (address, city_town, state, parcel_id) VALUES (?, ?, ?, ?)",
                   (address, city_town, state, parcel_id))
    conn.commit()
    conn.close()






    

def load_city_town_history():
    conn = sqlite3.connect('property_info.res')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT city_town FROM property")
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

def create_property_recorder_with_maps():
    # Submit the form data
    def submit_info():
        address = address_entry.get()
        city_town = city_town_entry.get()
        state = state_combo.get()
        parcel_id = parcel_id_entry.get()

        if not validate_inputs(address, city_town, state, parcel_id):
            messagebox.showerror("Error", "All fields must be filled out correctly!")
        else:
            log_property_info(address, city_town, state, parcel_id)
            messagebox.showinfo("Success", "Property information recorded!")
            clear_form()

    # Clear the form fields
    def clear_form():
        address_entry.delete(0, tk.END)
        city_town_entry.delete(0, tk.END)
        state_combo.set('Select State')
        parcel_id_entry.delete(0, tk.END)
        city_town_entry['values'] = load_city_town_history()

    # Exit the application
    def exit_app():
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            prop.destroy()

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
    #prop.geometry("400x400")

    # Labels and entry fields for property information
    tk.Label(prop, text="Address:").pack(pady=5)
    address_entry = tk.Entry(prop, width=40)
    address_entry.pack()
    address_entry.focus_set()

    tk.Label(prop, text="City/Town:").pack(pady=5)
    city_town_history = load_city_town_history()
    city_town_entry = ttk.Combobox(prop, values=city_town_history, width=37)
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
    parcel_id_entry = tk.Entry(prop, width=40)
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
    exit_button = tk.Button(button_frame, text="Exit", command=exit_app, width=button_width)
    exit_button.pack(side=tk.LEFT, padx=pad_x)

    prop.mainloop()

# Ensure database is created before starting the application
create_db()

# Call the encapsulated function with Google Maps and additional features
create_property_recorder_with_maps()
