import tkinter as tk
from tkinter import ttk, messagebox
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
        self.tk_img = None
        self.files = []
        self.pan_start = None

        self.sidebar.bind("<<ListboxSelect>>", self.on_file_select)
        self.canvas.bind("<ButtonPress-1>", self.start_pan)
        self.canvas.bind("<B1-Motion>", self.do_pan)

        # Zoom bindings for different platforms
        self.canvas.bind("<MouseWheel>", self.zoom)         # Windows/macOS
        self.canvas.bind("<Button-4>", self.zoom)           # Linux scroll up
        self.canvas.bind("<Button-5>", self.zoom)           # Linux scroll down

        self.load_files()

    def load_files(self):
        extensions = ('.png', '.jpg', '.jpeg', '.tiff', '.pdf')
        self.files = [f for f in os.listdir(DIR) if f.lower().endswith(extensions)]
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
                page = doc.load_page(0)
                pix = page.get_pixmap()
                img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
            else:
                img = Image.open(path).convert("RGBA")
        except Exception as e:
            messagebox.showerror("File Load Error", f"Could not load file:\n{e}")
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
                messagebox.showerror("Render Error", f"Could not render image:\n{e}")

    def start_pan(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def do_pan(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def zoom(self, event):
        # Determine zoom factor and location
        if hasattr(event, 'delta'):
            factor = 1.1 if event.delta > 0 else 0.9
        elif event.num == 4:
            factor = 1.1
        elif event.num == 5:
            factor = 0.9
        else:
            return

        new_scale = self.scale * factor
        if not (self.min_scale <= new_scale <= self.max_scale):
            return

        # Coordinates before zoom
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        rel_x = canvas_x / (self.img.width * self.scale)
        rel_y = canvas_y / (self.img.height * self.scale)

        self.scale = new_scale
        self.render_image()

        # Coordinates after zoom, center view
        new_canvas_x = self.img.width * self.scale * rel_x
        new_canvas_y = self.img.height * self.scale * rel_y
        self.canvas.xview_moveto((new_canvas_x - event.x) / (self.canvas.bbox("all")[2]))
        self.canvas.yview_moveto((new_canvas_y - event.y) / (self.canvas.bbox("all")[3]))

if __name__ == "__main__":
    root = tk.Tk()
    app = FileViewerApp(root)
    root.geometry("1000x700")
    root.mainloop()
