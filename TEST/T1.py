import tkinter as tk
from tkinter import messagebox



# Example usage within any portion of your program
def some_function():
    # Perform some actions
    print("Performing some actions...")
    # Call the exit function to confirm exit
    exit(root)

# Create the main Tkinter window
root = tk.Tk()
root.title("Reusable Exit Function Example")

# Button to trigger the exit function
exit_button = tk.Button(root, text="Exit", command=lambda: exit(root))
exit_button.pack(pady=20)

# Run the Tkinter event loop
root.mainloop()
