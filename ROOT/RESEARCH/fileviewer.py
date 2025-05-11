import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from PIL.Image import Resampling
import os
import fitz  # PyMuPDF


DIR = "/Users/sjohnstone/Python/RESEARCHV2/RENAME"

class FileViewerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Multi-file Viewer")

        self.frame = ttk.Frame(root)
        self.frame.pack(fill="both", expand=True)

        self.sidebar = tk.Listbox(self.frame, width=40)
        self.sidebar.pack(side="left", fill="y")

        self.canvas_frame = ttk.Frame(self.frame)
        self.canvas_frame.pack(side="right", fill="both", expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg="gray")
        self.canvas.pack(fill="both", expand=True)

        self.scroll_x = tk.Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.scroll_x.pack(side="bottom", fill="x")
        self.scroll_y = tk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.scroll_y.pack(side="right", fill="y")
        self.canvas.configure(xscrollcommand=self.scroll_x.set, yscrollcommand=self.scroll_y.set)

        self.image_id = None
        self.scale = 1.0
        self.min_scale = 0.1
        self.max_scale = 5.0
        self.img = None
        self.tk_img = None  # To prevent garbage #TRASH
        self.files = []

        self.sidebar.bind("<<ListboxSelect>>", self.on_file_select)
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.do_pan)
        self.canvas.bind("<MouseWheel>", self.zoom)

        self.load_files()
        self.pan_start = None

    def load_files(self):
        extensions = ('.png', '.jpg', '.jpeg', '.tiff', '.pdf')
        self.files = [f for f in os.listdir(DIR)
                      if f.lower().endswith(extensions)]
        self.sidebar.delete(0, tk.END)
        for file in self.files:
            self.sidebar.insert("end", file)

    def on_file_select(self, event):
        selection = self.sidebar.curselection()
        if not selection:
            return
        filename = self.files[selection[0]]
        path = os.path.join(DIR, filename)
        self.display_file(path)

    def display_file(self, path):
        try:
            if path.lower().endswith('.pdf'):
                doc = fitz.open(path)
                page = doc.load_page(0)  # Correct way to access the first page
                try:
                    pix = page.get_pixmap()  # Extract image
                except AttributeError as e:
                    print(f"Error getting pixmap: {e}")
                    return
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            else:
                img = Image.open(path).convert("RGBA")
        except Exception as e:
            print(f"Error loading file: {e}")
            return

        self.img = img
        self.scale = 1.0
        self.render_image()

    def render_image(self):
        if self.img:
            width = int(self.img.width * self.scale)
            height = int(self.img.height * self.scale)
            try:
                img_scaled = self.img.resize((width, height), Resampling.LANCZOS)
                self.tk_img = ImageTk.PhotoImage(img_scaled)
                self.canvas.delete("all")
                self.image_id = self.canvas.create_image(0, 0, image=self.tk_img, anchor="nw")
                self.canvas.config(scrollregion=self.canvas.bbox("all"))
            except Exception as e:
                print(f"Render error: {e}")

    def start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def do_pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def zoom(self, event):
        factor = 1.1 if event.delta > 0 else 0.9
        new_scale = self.scale * factor
        if self.min_scale <= new_scale <= self.max_scale:
            self.scale = new_scale
            self.render_image()

if __name__ == "__main__":
    root = tk.Tk()
    app = FileViewerApp(root)
    root.geometry("1000x700")
    root.mainloop()
