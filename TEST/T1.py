import tkinter as tk
from tkinter import simpledialog, messagebox
import os
import socket
from datetime import datetime

def feedback(feedback_type):
    # Get the current date and time
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Get the computer name
    computer_name = socket.gethostname()
    
    # Create a simple dialog to get user input
    feedback = simpledialog.askstring("Feedback", f"Please enter your {feedback_type}:")
    
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

# Sample usage in a Tkinter window
def feedbackwindow(window):
    error_button = tk.Button(window, text="Report Error", command=lambda: feedback("error"))
    error_button.pack(pady=10)

    comment_button = tk.Button(window, text="Add Comment", command=lambda: feedback("comment"))
    comment_button.pack(pady=10)

if __name__ == "__main__":
    window = tk.Tk()
    window.title("Feedback System")
    feedbackwindow(window)
    window.mainloop()
