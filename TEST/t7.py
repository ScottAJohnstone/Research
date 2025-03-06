import tkinter as tk
from tkinter import ttk, messagebox
import os
import glob
import datetime

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

# Function to update the preview filename
def update_preview_filename(tree):
    for item in tree.get_children():
        original_filename = tree.item(item)["text"]
        new_name = tree.item(item)["values"][0]
        preview_filename = os.path.join(os.path.dirname(original_filename), new_name)
        tree.item(item, values=(new_name, preview_filename))

# Function to handle file renaming
def rename_files(tree):
    selected_files = [tree.item(item)["text"] for item in tree.selection()]
    
    if not selected_files:
        messagebox.showwarning("No Selection", "No files selected.")
        return
    
    # Confirm rename action
    if messagebox.askyesno("Confirm Rename", f"Do you want to rename the selected files?"):
        for item in tree.selection():
            original_file = tree.item(item)["text"]
            new_filename = tree.item(item)["values"][1]  # Previewed filename (new name)
            
            try:
                os.rename(original_file, new_filename)
                tree.item(item, values=(os.path.basename(new_filename), new_filename))
            except Exception as e:
                messagebox.showerror("Error", f"Error renaming file {original_file}: {e}")
                
        messagebox.showinfo("Success", "Selected files have been renamed.")

# Function to populate the treeview with the recent files
def populate_treeview(tree, recent_files):
    # Clear the current items in the treeview
    for i in tree.get_children():
        tree.delete(i)
    
    # Insert the new files into the treeview
    for file in recent_files:
        filename = os.path.basename(file)
        preview_filename = filename  # Initially, the preview is the same as the original name
        tree.insert("", "end", text=file, values=(filename, preview_filename))

# Function to handle file selection
def handle_selection(tree):
    selected_files = [tree.item(item)["text"] for item in tree.selection()]
    if selected_files:
        messagebox.showinfo("Selected Files", f"Selected files:\n" + "\n".join(selected_files))
    else:
        messagebox.showwarning("No Selection", "No files selected.")

# Main Tkinter window
def main():
    download_folder = os.path.join(os.path.expanduser("~"), "Downloads")

    # Create the root Tkinter window
    root = tk.Tk()
    root.title("Bulk File Renamer - Recent Files in Downloads")
    root.geometry("800x500")

    # Create the Treeview with an additional Preview Filename column
    tree = ttk.Treeview(root, columns=("Filename", "Preview Filename"), show="headings")
    tree.heading("Filename", text="Filename")
    tree.heading("Preview Filename", text="Preview Filename")
    tree.pack(fill=tk.BOTH, expand=True)

    # Create buttons
    refresh_button = tk.Button(root, text="Refresh", command=lambda: refresh_files(tree, download_folder))
    refresh_button.pack(pady=10)
    
    rename_button = tk.Button(root, text="Rename Selected Files", command=lambda: rename_files(tree))
    rename_button.pack(pady=10)

    # Initially populate the tree with recent files
    refresh_files(tree, download_folder)

    # Start the Tkinter event loop
    root.mainloop()

def refresh_files(tree, download_folder):
    """ Refresh the file list in the treeview """
    recent_files = get_recent_files(download_folder)
    populate_treeview(tree, recent_files)
    update_preview_filename(tree)  # Update the previewed filenames after refreshing

if __name__ == "__main__":
    main()




# import tkinter as tk
# from tkinter import ttk, messagebox
# import os
# import glob
# import datetime

# # Function to get the most recent files based on creation time
# def get_recent_files(download_folder):
#     # Get all files in the Downloads folder
#     files = glob.glob(os.path.join(download_folder, "*"))
    
#     # Filter only files (ignore directories)
#     files = [f for f in files if os.path.isfile(f)]
    
#     # Sort files by the creation time (descending)
#     files.sort(key=lambda x: os.path.getctime(x), reverse=True)
    
#     # Group files by the same creation date (same date added)
#     if not files:
#         return []

#     most_recent_time = os.path.getctime(files[0])
#     recent_files = [f for f in files if abs(os.path.getctime(f) - most_recent_time) < 1]

#     return recent_files

# # Function to populate the treeview with the recent files
# def populate_treeview(tree, recent_files):
#     # Clear the current items in the treeview
#     for i in tree.get_children():
#         tree.delete(i)
    
#     # Insert the new files into the treeview
#     for file in recent_files:
#         tree.insert("", "end", text=file, values=(os.path.basename(file), datetime.datetime.fromtimestamp(os.path.getctime(file)).strftime('%Y-%m-%d %H:%M:%S')))

# # Function to handle file selection
# def handle_selection(tree):
#     selected_files = [tree.item(item)["text"] for item in tree.selection()]
#     if selected_files:
#         messagebox.showinfo("Selected Files", f"Selected files:\n" + "\n".join(selected_files))
#     else:
#         messagebox.showwarning("No Selection", "No files selected.")

# # Main Tkinter window
# def main():
#     download_folder = os.path.join(os.path.expanduser("~"), "Downloads")

#     # Create the root Tkinter window
#     root = tk.Tk()
#     root.title("Recent Files in Downloads")
#     root.geometry("600x400")

#     # Create the Treeview
#     tree = ttk.Treeview(root, columns=("Filename", "Date Added"), show="headings")
#     tree.heading("Filename", text="Filename")
#     tree.heading("Date Added", text="Date Added")
#     tree.pack(fill=tk.BOTH, expand=True)

#     # Create buttons
#     refresh_button = tk.Button(root, text="Refresh", command=lambda: refresh_files(tree, download_folder))
#     refresh_button.pack(pady=10)
    
#     select_button = tk.Button(root, text="Select Files", command=lambda: handle_selection(tree))
#     select_button.pack(pady=10)

#     # Initially populate the tree with recent files
#     refresh_files(tree, download_folder)

#     # Start the Tkinter event loop
#     root.mainloop()

# def refresh_files(tree, download_folder):
#     """ Refresh the file list in the treeview """
#     recent_files = get_recent_files(download_folder)
#     populate_treeview(tree, recent_files)

# if __name__ == "__main__":
#     main()
