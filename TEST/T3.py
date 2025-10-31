import tkinter as tk

root = tk.Tk()
root.geometry("300x150")

# Use tk.LabelFrame
lf_tk = tk.LabelFrame(root, text="My Settings", padx=10, pady=10)
lf_tk.pack(padx=10, pady=10, fill="both", expand=True)

tk.Label(lf_tk, text="This uses tk.LabelFrame").pack()

root.mainloop()
