"""
. Research V2:	File Viewer 
. Image/PDF/Text File Viewer
. Runs fileviewer.py

- Sidebar file list, toolbar buttons (Open Folder, Add Files, Open Externally, Show in Folder, Prev/Next, Fit, Zoom +, Zoom −, Shortcuts)
- Multi-page docs (PDF, multi-frame TIFF): **pager below the preview, direct page jump entry
- Keyboard shortcuts dialog (F1)

#/                                                                                                               #/
#/                                                                                                               #/
"""
import os
import sys
import json
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from PIL.Image import Resampling

"""
T1.py — Image/PDF/Text File Viewer (Enhanced)

- No f-strings: all dynamic strings use concatenation or str.format to avoid parser issues
- Sidebar file list, toolbar (Open Folder, Add Files, Remove, Prev/Next, Fit, Zoom +, Zoom −, Shortcuts)
- Multi-page docs (PDF, multi-frame TIFF): pager below preview (bottom-left) with page jump
- Text viewer for .txt/.md/.csv/.log/.res
- Session persistence: remembers file list, current file, and page index
- Starts at Fit to Window; Zoom +/−; shortcuts dialog (F1)
"""

try:
    import fitz  # PyMuPDF for PDF rendering
except Exception:
    fitz = None

SUPPORTED_EXTS = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif", ".pdf")
TEXT_EXTS = (".txt", ".md", ".csv", ".log", ".res")


# ---------- helpers ----------
def _is_supported(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in SUPPORTED_EXTS


def _is_text(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in TEXT_EXTS


def _system_open(path: str):
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        messagebox.showerror("Open externally", "Could not open with system app:"+ str(e))


def _reveal_in_file_manager(path: str):
    try:
        if sys.platform.startswith("win"):
            subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", path])
        else:
            folder = os.path.dirname(path)
            subprocess.Popen(["xdg-open", folder])
    except Exception as e:
        messagebox.showerror("Show in folder", "Could not reveal file:" + str(e))


# ---------- app ----------
class FileViewerApp:
    def __init__(self, root, start_dir: str | None = None):
        self.root = root
        self.root.title("Multi-file Viewer")
        self.root.geometry("1200x800")

        # state
        self.current_dir = start_dir
        self.files = []  # type: list[str]
        self.current_index = None  # type: int | None
        self.current_path = None   # type: str | None
        self.mode = None           # type: str | None  # 'image' or 'text'

        # image/pdf render state
        self.base_image = None     # type: Image.Image | None
        self.tk_image = None       # type: ImageTk.PhotoImage | None
        self.scale = 1.0
        self.min_scale = 0.1
        self.max_scale = 8.0
        self.auto_fit = True

        # multi-page
        self.pdf_doc = None
        self.pdf_page_index = 0
        self.doc_page_index = 0
        self.doc_page_count = 1

        # ui
        self._build_menu()
        self._build_layout()
        self._bind_events()

        # session
        self._load_session()
        if self.current_dir and os.path.isdir(self.current_dir) and not self.files:
            self.load_directory(self.current_dir)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ----- UI -----
    def _build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Open Folder…", command=self.open_folder, accelerator="Ctrl+O")
        file_menu.add_command(label="Add Files…", command=self.add_files, accelerator="Ctrl+Shift+O")
        file_menu.add_command(label="Remove Selected", command=self.remove_selected, accelerator="Del")
        file_menu.add_separator()
        file_menu.add_command(label="Save Session", command=self._save_session, accelerator="Ctrl+S")
        file_menu.add_command(label="Clear Session", command=self._clear_session)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.root.quit, accelerator="Ctrl+Q")
        menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=False)
        view_menu.add_command(label="Fit to Window", command=self.fit_to_window, accelerator="F")
        view_menu.add_command(label="Zoom In", command=lambda: self._zoom(1.1), accelerator="+")
        view_menu.add_command(label="Zoom Out", command=lambda: self._zoom(1/1.1), accelerator="-")
        menubar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts, accelerator="F1")
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def _build_layout(self):
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(1, weight=1)

        # toolbar
        tb = ttk.Frame(self.root, padding=(8, 6))
        tb.grid(row=0, column=0, columnspan=2, sticky="ew")

        def B(text, cmd):
            b = ttk.Button(tb, text=text, command=cmd)
            b.pack(side=tk.LEFT, padx=4)
            return b

        B("Open Folder", self.open_folder)
        B("Add Files", self.add_files)
        B("Remove", self.remove_selected)
        ttk.Separator(tb, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=6)
        B("Prev ←", self.prev_file)
        B("Next →", self.next_file)
        ttk.Separator(tb, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=6)
        B("Fit", self.fit_to_window)
        B("Zoom +", lambda: self._zoom(1.1))
        B("Zoom -", lambda: self._zoom(1/1.1))
        ttk.Separator(tb, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=6)
        B("Shortcuts", self.show_shortcuts)

        # sidebar
        sidebar = ttk.Frame(self.root)
        sidebar.grid(row=1, column=0, sticky="nsw")
        sidebar.rowconfigure(1, weight=1)
        sidebar.columnconfigure(0, weight=1)
        ttk.Label(sidebar, text="Files", padding=(8, 6)).grid(row=0, column=0, sticky="w")
        self.listbox = tk.Listbox(sidebar, width=42, activestyle="dotbox")
        self.listbox.grid(row=1, column=0, sticky="nsew")
        sb = ttk.Scrollbar(sidebar, orient="vertical", command=self.listbox.yview)
        sb.grid(row=1, column=1, sticky="ns")
        self.listbox.configure(yscrollcommand=sb.set)

        # main frame (viewer + pager bar)
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=1, column=1, sticky="nsew")
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=0)
        self.main_frame.columnconfigure(0, weight=1)

        # canvas viewer
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.canvas_frame.grid(row=0, column=0, sticky="nsew")
        self.canvas_frame.rowconfigure(0, weight=1)
        self.canvas_frame.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(self.canvas_frame, bg="#303030", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.image_id = self.canvas.create_image(0, 0, anchor="nw")

        # text viewer
        self.text_frame = ttk.Frame(self.main_frame)
        self.text_frame.rowconfigure(0, weight=1)
        self.text_frame.columnconfigure(0, weight=1)
        self.text_widget = tk.Text(self.text_frame, wrap="none", font=("Consolas", 11))
        self.text_widget.configure(state="disabled")
        self.text_widget.grid(row=0, column=0, sticky="nsew")
        tvsb = ttk.Scrollbar(self.text_frame, orient="vertical", command=self.text_widget.yview)
        tvsb.grid(row=0, column=1, sticky="ns")
        thsb = ttk.Scrollbar(self.text_frame, orient="horizontal", command=self.text_widget.xview)
        thsb.grid(row=1, column=0, sticky="ew")
        self.text_widget.configure(yscrollcommand=tvsb.set, xscrollcommand=thsb.set)

        # pager bar (bottom-left)
        self.page_bar = ttk.Frame(self.main_frame, padding=(8, 6))
        self.page_bar.grid(row=1, column=0, sticky="w")
        self.page_prev_btn = ttk.Button(self.page_bar, text="◀ Prev", command=self.page_prev, width=8)
        self.page_entry_var = tk.StringVar(value="1")
        self.page_entry = ttk.Entry(self.page_bar, width=6, textvariable=self.page_entry_var)
        self.page_go_btn = ttk.Button(self.page_bar, text="Go", command=self.page_go)
        self.page_label = ttk.Label(self.page_bar, text="/ 1")
        self.page_next_btn = ttk.Button(self.page_bar, text="Next ▶", command=self.page_next, width=8)
        self.page_prev_btn.pack(side=tk.LEFT)
        ttk.Label(self.page_bar, text=" Page ").pack(side=tk.LEFT)
        self.page_entry.pack(side=tk.LEFT)
        self.page_label.pack(side=tk.LEFT, padx=(6, 6))
        self.page_go_btn.pack(side=tk.LEFT)
        self.page_next_btn.pack(side=tk.LEFT, padx=(8, 0))
        self._set_page_nav_visible(False)

        # status bar
        self.status = ttk.Label(self.root, text="Ready", anchor="w", padding=(8, 3))
        self.status.grid(row=2, column=0, columnspan=2, sticky="ew")

    def _bind_events(self):
        # global keys
        self.root.bind_all("<Control-o>", lambda e: self.open_folder())
        self.root.bind_all("<Control-Shift-o>", lambda e: self.add_files())
        self.root.bind_all("<Delete>", lambda e: self.remove_selected())
        self.root.bind_all("<Control-s>", lambda e: self._save_session())
        self.root.bind_all("<Left>", lambda e: self.prev_file())
        self.root.bind_all("<Right>", lambda e: self.next_file())
        self.root.bind_all("<Key-plus>", lambda e: self._zoom(1.1))
        self.root.bind_all("<Key-equal>", lambda e: self._zoom(1.1))
        self.root.bind_all("<Key-minus>", lambda e: self._zoom(1/1.1))
        self.root.bind_all("<Key-f>", lambda e: self.fit_to_window())
        self.root.bind_all("<F1>", lambda e: self.show_shortcuts())

        # listbox
        self.listbox.bind("<<ListboxSelect>>", self._on_select)
        self.listbox.bind("<Double-1>", lambda e: self.open_selected())
        self.listbox.bind("<Return>", lambda e: self.open_selected())
        # context
        self._ctx = tk.Menu(self.root, tearoff=False)
        self._ctx.add_command(label="Open", command=self.open_selected)
        self._ctx.add_command(label="Open Externally", command=self.open_external)
        self._ctx.add_command(label="Show in Folder", command=self.reveal_selected)
        self._ctx.add_separator()
        self._ctx.add_command(label="Remove", command=self.remove_selected)
        self.listbox.bind("<Button-3>", self._show_ctx)
        self.listbox.bind("<Control-Button-1>", self._show_ctx)

        # canvas
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<MouseWheel>", self._on_wheel)      # Win/mac
        self.canvas.bind("<Button-4>", self._on_wheel_linux)  # Linux up
        self.canvas.bind("<Button-5>", self._on_wheel_linux)  # Linux down

        # pager
        self.page_entry.bind("<Return>", lambda e: self.page_go())

    # ----- utils -----
    def _show_ctx(self, event):
        try:
            self._ctx.tk_popup(event.x_root, event.y_root)
        finally:
            self._ctx.grab_release()

    def _set_page_nav_visible(self, visible: bool):
        if visible:
            self.page_bar.grid()
        else:
            self.page_bar.grid_remove()

    def _update_status(self):
        name = os.path.basename(self.current_path) if self.current_path else "—"
        zoom = (" " + str(int(self.scale * 100)) + "%") if (self.mode == 'image' and self.base_image) else ""
        self.status.config(text=name + zoom)

    # ----- open / list ops -----
    def open_folder(self, initial_dir: str | None = None):
        dirpath = filedialog.askdirectory(initialdir=initial_dir or os.getcwd(), title="Select folder to view")
        if not dirpath:
            return
        self.load_directory(dirpath)

    def add_files(self):
        paths = filedialog.askopenfilenames(title="Add files to view", filetypes=[
            ("Supported", " ".join("*" + ext for ext in SUPPORTED_EXTS)),
            ("Text files", " ".join("*" + ext for ext in TEXT_EXTS)),
            ("All files", "*.*"),
        ])
        if not paths:
            return
        added = 0
        for p in paths:
            if (_is_supported(p) or _is_text(p)) and p not in self.files:
                self.files.append(os.path.abspath(p))
                self.listbox.insert(tk.END, os.path.basename(p))
                added += 1
        if added and self.current_index is None:
            self._open_index(0)
        if added:
            self._save_session()

    def remove_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = int(sel[0])
        if 0 <= idx < len(self.files):
            self.files.pop(idx)
            self.listbox.delete(idx)
            if self.files:
                new_idx = min(idx, len(self.files) - 1)
                self.listbox.selection_clear(0, tk.END)
                self.listbox.selection_set(new_idx)
                self.listbox.activate(new_idx)
                self._open_index(new_idx)
            else:
                self.current_index = None
                self.current_path = None
                self._clear_canvas()
                self._update_status()
        self._save_session()

    def load_directory(self, dirpath: str):
        self.current_dir = dirpath
        entries = []  # type: list[str]
        try:
            for f in os.listdir(dirpath):
                if f.lower().endswith(SUPPORTED_EXTS):
                    entries.append(os.path.join(dirpath, f))
        except Exception as e:
            messagebox.showerror("Error", "Could not list directory:" + str(e))
            return
        entries.sort(key=lambda p: os.path.basename(p).lower())
        self.files = entries
        self.listbox.delete(0, tk.END)
        for p in self.files:
            self.listbox.insert(tk.END, os.path.basename(p))
        self.current_index = 0 if self.files else None
        if self.files:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(0)
            self.listbox.activate(0)
            self._open_index(0)
        else:
            self._clear_canvas()
            self._update_status()
        self._save_session()

    def _on_select(self, _event=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        self._open_index(int(sel[0]))

    def _open_index(self, idx: int):
        if idx < 0 or idx >= len(self.files):
            return
        self.current_index = idx
        self.open_path(self.files[idx])

    def open_selected(self):
        sel = self.listbox.curselection()
        if sel:
            self._open_index(int(sel[0]))

    def prev_file(self):
        if self.current_index is None or not self.files:
            return
        self._open_index((self.current_index - 1) % len(self.files))

    def next_file(self):
        if self.current_index is None or not self.files:
            return
        self._open_index((self.current_index + 1) % len(self.files))

    def open_external(self):
        if self.current_path:
            _system_open(self.current_path)

    def reveal_selected(self):
        if self.current_path:
            _reveal_in_file_manager(self.current_path)

    # ----- view switching -----
    def _show_canvas_viewer(self):
        self.text_frame.grid_forget()
        self.canvas_frame.grid(row=0, column=0, sticky="nsew")

    def _show_text_viewer(self):
        self.canvas_frame.grid_forget()
        self.text_frame.grid(row=0, column=0, sticky="nsew")

    # ----- open path -----
    def open_path(self, path: str):
        self.current_path = path
        self.scale = 1.0
        self.auto_fit = True
        self.base_image = None
        self.pdf_doc = None
        self.pdf_page_index = 0
        self.doc_page_index = 0
        self.doc_page_count = 1

        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".pdf":
                if fitz is None:
                    raise RuntimeError("PyMuPDF (fitz) is not installed.")
                self.pdf_doc = fitz.open(path)
                self.doc_page_count = int(self.pdf_doc.page_count)
                self.pdf_page_index = 0
                self._render_pdf_page()
                self.mode = 'image'
                self._show_canvas_viewer()
                self._set_page_nav_visible(self.doc_page_count > 1)
            elif ext in (".tif", ".tiff"):
                img = Image.open(path)
                try:
                    self.doc_page_count = int(getattr(img, 'n_frames', 1))
                except Exception:
                    self.doc_page_count = 1
                img.seek(0)
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA")
                self.base_image = img
                self.mode = 'image'
                self._show_canvas_viewer()
                self._set_page_nav_visible(self.doc_page_count > 1)
                self._render_to_canvas()
            elif _is_text(path):
                self.mode = 'text'
                self._show_text_viewer()
                self._set_page_nav_visible(False)
                self._load_text_file(path)
            else:
                img = Image.open(path)
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA")
                self.base_image = img
                self.mode = 'image'
                self._show_canvas_viewer()
                self._set_page_nav_visible(False)
                self._render_to_canvas()
        except Exception as e:
            messagebox.showerror("Open error", "Could not open " + os.path.basename(path) + "" + str(e))
            self._clear_canvas()
            self._update_status()
            return

        if self.mode == 'image':
            self.fit_to_window()
        self._update_status()
        self._update_page_nav()
        self._save_session()

    # ----- text loader -----
    def _load_text_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror("Open error", "Could not read text file:" + str(e))
            content = ""
        self.text_widget.configure(state="normal")
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert("1.0", content)
        self.text_widget.configure(state="disabled")

    # ----- pdf render -----
    def _render_pdf_page(self, dpi: int = 150):
        if not self.pdf_doc:
            return
        page = self.pdf_doc.load_page(self.pdf_page_index)
        zoom = float(dpi) / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        mode = "RGB" if pix.alpha == 0 else "RGBA"
        self.base_image = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
        self._render_to_canvas()

    # ----- canvas render & zoom -----
    def _render_to_canvas(self):
        if not self.base_image:
            return
        cv_w = max(1, self.canvas.winfo_width())
        cv_h = max(1, self.canvas.winfo_height())
        img_w, img_h = self.base_image.size
        # compute scale to fit viewport
        scale = min(float(cv_w) / float(img_w), float(cv_h) / float(img_h))
        scaled = self.base_image.resize((max(1, int(img_w * scale)), max(1, int(img_h * scale))), Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(scaled)
        self.canvas.delete("all")
        x = (cv_w - scaled.width) // 2
        y = (cv_h - scaled.height) // 2
        self.image_id = self.canvas.create_image(x, y, anchor="nw", image=self.tk_image)

    def _on_canvas_resize(self, _event):
        if self.mode == 'image' and self.base_image is not None:
            self._render_to_canvas()

    def _zoom(self, factor: float):
        if self.mode != 'image' or not self.base_image:
            return
        cv_w = max(1, self.canvas.winfo_width())
        cv_h = max(1, self.canvas.winfo_height())
        img_w, img_h = self.base_image.size
        current_fit = min(float(cv_w) / float(img_w), float(cv_h) / float(img_h))
        new_scale = max(self.min_scale, min(self.max_scale, current_fit * factor))
        scaled = self.base_image.resize((max(1, int(img_w * new_scale)), max(1, int(img_h * new_scale))), Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(scaled)
        self.canvas.delete("all")
        self.image_id = self.canvas.create_image((cv_w - scaled.width) // 2, (cv_h - scaled.height) // 2, image=self.tk_image, anchor="nw")
        self.auto_fit = False
        self.scale = new_scale
        self._update_status()

    def _on_wheel(self, event):
        if self.mode != 'image' or not self.base_image:
            return
        delta = event.delta
        if sys.platform == "darwin":
            delta = -delta
        self._zoom(1.1 if delta > 0 else 1/1.1)

    def _on_wheel_linux(self, event):
        if self.mode != 'image' or not self.base_image:
            return
        self._zoom(1.1 if event.num == 4 else 1/1.1)

    def fit_to_window(self):
        if self.mode != 'image' or not self.base_image:
            return
        self.auto_fit = True
        self.scale = 1.0
        self._render_to_canvas()
        self._update_status()

    def _clear_canvas(self):
        self.canvas.delete("all")

    # ----- pager -----
    def _update_page_nav(self):
        if self.mode != 'image' or self.doc_page_count <= 1:
            self._set_page_nav_visible(False)
            return
        self._set_page_nav_visible(True)
        cur = self.pdf_page_index if self.pdf_doc else self.doc_page_index
        self.page_label.config(text="/ " + str(self.doc_page_count))
        self.page_entry_var.set(str(cur + 1))
        self.page_prev_btn.state(["!disabled"])
        self.page_next_btn.state(["!disabled"])
        if cur <= 0:
            self.page_prev_btn.state(["disabled"])
        if cur >= self.doc_page_count - 1:
            self.page_next_btn.state(["disabled"])

    def page_prev(self):
        if self.mode != 'image' or self.doc_page_count <= 1:
            return
        if self.pdf_doc:
            if self.pdf_page_index > 0:
                self.pdf_page_index -= 1
                self._render_pdf_page()
        else:
            self._goto_image_frame(self.doc_page_index - 1)
        self._update_page_nav()
        self._update_status()
        self._save_session()

    def page_next(self):
        if self.mode != 'image' or self.doc_page_count <= 1:
            return
        if self.pdf_doc:
            if self.pdf_page_index < self.doc_page_count - 1:
                self.pdf_page_index += 1
                self._render_pdf_page()
        else:
            self._goto_image_frame(self.doc_page_index + 1)
        self._update_page_nav()
        self._update_status()
        self._save_session()

    def page_go(self):
        if self.mode != 'image' or self.doc_page_count <= 1:
            return
        try:
            n = int(self.page_entry_var.get().strip())
        except Exception:
            self.root.bell()
            return
        n = max(1, min(self.doc_page_count, n))
        if self.pdf_doc:
            self.pdf_page_index = n - 1
            self._render_pdf_page()
        else:
            self._goto_image_frame(n - 1)
        self._update_page_nav()
        self._update_status()
        self._save_session()

    def _goto_image_frame(self, frame_index: int):
        if not self.current_path:
            return
        try:
            img = Image.open(self.current_path)
            total = int(getattr(img, 'n_frames', 1))
            frame_index = max(0, min(total - 1, frame_index))
            img.seek(frame_index)
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGBA")
            self.base_image = img
            self.doc_page_index = frame_index
            self.doc_page_count = total
            self._render_to_canvas()
        except Exception as e:
            messagebox.showerror("Page", "Could not change page:" + str(e))

    # ----- session -----
    def _state_path(self) -> str:
        return os.path.join(os.path.expanduser("~"), ".fileviewer_session.json")

    def _save_session(self):
        try:
            data = {
                "files": self.files,
                "current_index": self.current_index,
                "current_path": self.current_path,
                "page_index": self.pdf_page_index if self.pdf_doc else self.doc_page_index,
            }
            with open(self._state_path(), "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _load_session(self):
        path = self._state_path()
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            files = [p for p in data.get("files", []) if os.path.exists(p) and (_is_supported(p) or _is_text(p))]
            if not files:
                return
            self.files = files
            self.listbox.delete(0, tk.END)
            for p in self.files:
                self.listbox.insert(tk.END, os.path.basename(p))
            idx = data.get("current_index")
            if idx is None or not (0 <= idx < len(self.files)):
                idx = 0
            self._open_index(idx)
            # restore page if applicable
            self.doc_page_index = int(data.get("page_index") or 0)
            if self.doc_page_count > 1:
                self.page_entry_var.set(str(self.doc_page_index + 1))
                self.page_go()
        except Exception:
            pass

    def _clear_session(self):
        try:
            os.remove(self._state_path())
        except Exception:
            pass
        self.files.clear()
        self.listbox.delete(0, tk.END)
        self._clear_canvas()
        self.current_index = None
        self.current_path = None
        self._update_status()

    def _on_close(self):
        self._save_session()
        self.root.destroy()

    # ----- shortcuts dialog -----
    def show_shortcuts(self):
        shortcuts = get_shortcuts_text()
        top = tk.Toplevel(self.root)
        top.title("Keyboard Shortcuts")
        top.transient(self.root)
        top.grab_set()
        frm = ttk.Frame(top, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frm, text="Keyboard Shortcuts", font=("TkDefaultFont", 12, "bold")).pack(anchor="w", pady=(0, 6))
        txt = tk.Text(frm, width=48, height=12, wrap="word")
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert("1.0", shortcuts)
        txt.configure(state="disabled")
        ttk.Button(frm, text="Close", command=top.destroy).pack(anchor="e", pady=(8, 0))


# ---------- shortcuts text ----------
def get_shortcuts_text() -> str:
    lines = [
        "Ctrl+O — Open Folder",
        "Ctrl+Shift+O — Add Files",
        "Delete — Remove selected",
        "Ctrl+S — Save session",
        "Enter/Double-click — Open selected",
        "Ctrl+E — Open externally",
        "Ctrl+R — Show in folder",
        "+ / - — Zoom in/out",
        "F — Fit to window",
        "F1 — Keyboard Shortcuts",
    ]
    return "".join(lines)


# ---------- main ----------
def main():
    root = tk.Tk()
    FileViewerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
