import tkinter as tk
from tkinter import ttk
from tkinter import filedialog, messagebox
from datetime import datetime
import os
import csv
import glob

download_folder = os.path.join(os.path.expanduser("~"), "Downloads")

# Function to get the most recent files based on creation time
def get_recent_files(download_folder):
    # Get all files in the Downloads folder
    files = glob.glob(os.path.join(download_folder, "*"))
    
    # Filter only files (ignore directories)
    files = [f for f in files if os.path.isfile(f)]
    
    # Sort files by the creation time (descending)
    files.sort(key=lambda x: os.path.getctime(x), reverse=True)
    
    # Group files by the same creation date (same date added)
    if not files:
        return []

    most_recent_time = os.path.getctime(files[0])
    recent_files = [f for f in files if abs(os.path.getctime(f) - most_recent_time) < 1]

    return recent_files


def get_files(folder_path):
    files = os.listdir(folder_path)
    return files


def rename_file(folder_path, old_name, new_name, index):
    old_ext = os.path.splitext(old_name)[1]
    new_file_path = os.path.join(folder_path, new_name + old_ext)  # Append the original extension
    return new_file_path


def select_folder():
    global selected_folder
    folder_path = filedialog.askdirectory()
    if folder_path:
        selected_folder = folder_path
         # Remove hidden files, folders, and .csv
        files = [file for file in get_files(folder_path) if not file.startswith('.') and not os.path.isdir(os.path.join(folder_path, file)) and not file.endswith('.csv')] # EXCLUDE HIDDEN FILES AND FOLDERS

        # Configure 'blue' tag to set foreground color to blue
        renamed_tree.tag_configure('blue', foreground='blue')

        original_tree.delete(*original_tree.get_children())  # Clear the original treeview
        renamed_tree.delete(*renamed_tree.get_children())  # Clear the renamed treeview

        for i, file in enumerate(files, start=1):
            original_tree.insert('', 'end', values=(i, file))
            new_name = file
            last_dot_index = new_name.rfind('.')  # Find the index of the last occurrence of "."
            just_name = new_name[:last_dot_index]
            just_ext = new_name[last_dot_index:]

            if "." in just_name:                    
                vol, pg = (just_name).split(".")
                rename = f'Volume {vol} - Page {pg}{just_ext}'
                item = renamed_tree.insert('', 'end', values=(i, rename))
                renamed_tree.item(item, tags=('blue',))  # Tag item with 'blue' tag
            elif just_name.isdigit():
                rename = f'Map #{new_name}'
                item = renamed_tree.insert('', 'end', values=(i, rename))
                renamed_tree.item(item, tags=('blue',))  # Tag item with 'blue' tag
            else:
                item = renamed_tree.insert('', 'end', values=(i, new_name))
                renamed_tree.item(item, tags=('blue',))  # Tag item with 'blue' tag

        execute_button.config(state=tk.NORMAL, command=lambda: execute_rename(folder_path))
        select_button.config(state=tk.DISABLED)


def save_changes_to_csv(folder_path, original_name, new_name):
    csv_file_path = os.path.join(folder_path, 'renaming_changes.csv')

    # Check if the CSV file already exists
    file_exists = os.path.isfile(csv_file_path)

    with open(csv_file_path, 'a', newline='') as csvfile:
        fieldnames = ['Date', 'Time', 'Folder Path', 'Original Name', 'New Name']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # If the CSV file doesn't exist, write the header
        if not file_exists:
            writer.writeheader()

        # Get current date and time
        current_datetime = datetime.now()
        date = current_datetime.strftime('%Y-%m-%d')
        time = current_datetime.strftime('%H:%M:%S')

        # Write the renaming changes to the CSV file
        writer.writerow({'Date': date, 'Time': time, 'Folder Path': folder_path, 'Original Name': original_name, 'New Name': new_name})


def execute_rename(folder_path):
    for item in renamed_tree.get_children():  # Iterate over treeview rows
        old_name = original_tree.item(item, 'values')[1]
        new_name = renamed_tree.set(item, 'New Name')

        new_file_path = rename_file(folder_path, old_name, new_name, item)
        try:
            os.rename(os.path.join(folder_path, old_name), new_file_path)
            renamed_tree.set(item, 'New Name', os.path.basename(new_file_path))
            renamed_tree.item(item, tags=('renamed',))

            # Save the renaming changes to CSV
            save_changes_to_csv(folder_path, old_name, os.path.basename(new_file_path))
        except FileExistsError:
            messagebox.showerror("Error", f"A file with name '{new_name}' already exists in the directory.")


def on_double_click(event):
    item = renamed_tree.selection()[0]
    column = renamed_tree.identify_column(event.x)
    row = renamed_tree.identify_row(event.y)
    
    if column == '#2' and row == item:
        rename_entry.delete(0, tk.END)
        new_name = renamed_tree.set(item, 'New Name')
        rename_entry.insert(0, new_name)
        rename_entry.pack()
        rename_entry.focus_set()
         # Get the index of the end of the text
        end_index = len(rename_entry.get())
        # Calculate the index to exclude the last 4 characters (".pdf")
        start_index = 0
        end_index_adjusted = end_index - 4

        dot_index = rename_entry.get().find(".")
        if dot_index != -1:
            rename_entry.icursor(dot_index)
             # Select all text except for the last 4 characters (".pdf")
            rename_entry.selection_range(start_index, end_index_adjusted)
        
        else:
            end_index_adjusted = end_index - 4
             # Select all text except for the last 4 characters (".pdf")
            rename_entry.selection_range(start_index, end_index)


def save_new_name(event, item):
    new_name = rename_entry.get()
    original_name = original_tree.set(item, 'Original Name')
    # Remove any existing extension from the new name
    new_name, _ = os.path.splitext(new_name)
    # Append the extension from the original name to the new name
    _, old_ext = os.path.splitext(original_name)
    new_name += old_ext
    renamed_tree.set(item, 'New Name', new_name)


def scroll(*args):
    renamed_tree.yview(*args)
    original_tree.yview(*args)


# Create main tkinter window
RENAME = tk.Tk()
RENAME.title("File Renamer")

download_folder = os.path.join(os.path.expanduser("~"), "Downloads")
selected_folder = None

# Initialize with recent files from the Downloads folder
recent_files = get_recent_files(download_folder)
if recent_files:
    initial_files = [os.path.basename(f) for f in recent_files]
else:
    initial_files = []

# Create original_tree and renamed_tree
frame = tk.Frame(RENAME, borderwidth=2, relief="groove")
frame.pack(padx=10, pady=10)

original_tree_frame = tk.Frame(frame)
original_tree_frame.pack(side="left")

# Create a vertical scrollbar
vsb = ttk.Scrollbar(original_tree_frame, orient="vertical")
vsb.pack(side="right", fill="y")

original_tree = ttk.Treeview(original_tree_frame, columns=('#', 'Original Name'), show='headings', yscrollcommand=vsb.set)
original_tree.heading('#', text='#')
original_tree.heading('Original Name', text='EXISTING FILE NAMES', anchor="w")
original_tree.column('#', stretch=True, width=40, anchor="w")
original_tree.column('Original Name', width=300, anchor="w")
original_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

renamed_tree = ttk.Treeview(frame, columns=('#', 'New Name'), show='headings', yscrollcommand=vsb.set)
renamed_tree.heading('#', text='#')
renamed_tree.heading('New Name', text='NEW FILE NAMES', anchor="w")
renamed_tree.column('#', stretch=True, width=40, anchor="w")
renamed_tree.column('New Name', width=300, anchor="w")
renamed_tree.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

# Populate the trees with the initial files
for i, file in enumerate(initial_files, start=1):
    original_tree.insert('', 'end', values=(i, file))
    renamed_tree.insert('', 'end', values=(i, file))

# Select Folder Button
select_button = tk.Button(RENAME, text="Select Folder", command=select_folder)
select_button.pack(pady=10)

rename_entry = tk.Entry(RENAME, justify='center', width=41)
rename_entry.pack_forget()

execute_button = tk.Button(RENAME, text="Execute Renaming", state=tk.DISABLED)
execute_button.pack(pady=10)

renamed_tree.tag_configure('renamed', foreground='red')  # Change font color for renamed files

renamed_tree.bind("<Double-1>", on_double_click)

RENAME.mainloop()
