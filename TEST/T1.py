import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from PIL.Image import Resampling

"""
T1.py — Image/PDF/Text File Viewer

- Starts every visual file at **Fit to Window** (keeps auto-fit until you manually zoom)
- Sidebar file list, toolbar buttons (Open Folder, Add Files, Open Externally, Show in Folder, Prev/Next, Fit, Zoom +, Zoom −, Shortcuts)
- Text viewer for .txt/.md/.csv/.log
- Multi-page docs (PDF, multi-frame TIFF): **pager below the preview, bottom-left**, with **direct page jump** entry
- Keyboard shortcuts dialog (F1)

Run: python T1.py
Run tests: python T1.py --test
"""

try:
    import fitz  # PyMuPDF for PDF rendering
except Exception:
    fitz = None

SUPPORTED_EXTS = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp", ".gif", ".pdf")
TEXT_EXTS = (".txt", ".md", ".csv", ".log")


def _is_supported(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in SUPPORTED_EXTS


def _is_text(path: str) -> bool:
    return os.path.splitext(path)[1].lower() in TEXT_EXTS


def _system_open(path: str):
    """Open a file with the OS default app."""
    try:
        if sys.platform.startswith("win"):
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        messagebox.showerror("Open externally", f"""Could not open with system app:
{e}""")


def _reveal_in_file_manager(path: str):
    """Reveal file in Explorer/Finder (or open containing folder on Linux)."""
    try:
        if sys.platform.startswith("win"):
            subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", path])
        else:
            folder = os.path.dirname(path)
            subprocess.Popen(["xdg-open", folder])
    except Exception as e:
        messagebox.showerror("Show in folder", f"""Could not reveal file:
{e}""")


class FileViewerApp:
    def __init__(self, root, start_dir: str | None = None):
        self.root = root
        self.root.title("Multi-file Viewer")
        self.root.geometry("1200x800")

        # --- state ---
        self.current_dir: str | None = start_dir
        self.files: list[str] = []  # absolute paths
        self.current_index: int | None = None
        self.current_path: str | None = None
        self.scale: float = 1.0
        self.min_scale: float = 0.1
        self.max_scale: float = 8.0
        self.base_image: Image.Image | None = None
        self.tk_image: ImageTk.PhotoImage | None = None
        self.pdf_doc = None
        self.pdf_page_index = 0
        self.doc_page_index = 0
        self.doc_page_count = 1
        self.auto_fit: bool = True
        self.mode: str | None = None  # 'image' or 'text'

        # --- UI ---
        self._build_menu()
        self._build_layout()
        self._bind_events()

        if self.current_dir and os.path.isdir(self.current_dir):
            self.load_directory(self.current_dir)

    # ===== UI =====
    def _build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Open Folder…", command=self.open_folder, accelerator="Ctrl+O")
        file_menu.add_command(label="Add Files…", command=self.add_files, accelerator="Ctrl+Shift+O")
        file_menu.add_separator()
        file_menu.add_command(label="Open Externally", command=self.open_external, accelerator="Ctrl+E")
        file_menu.add_command(label="Show in Folder", command=self.reveal_selected, accelerator="Ctrl+R")
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.root.quit, accelerator="Ctrl+Q")
        menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=False)
        view_menu.add_command(label="Fit to Window", command=self.fit_to_window, accelerator="F")
        view_menu.add_separator()
        view_menu.add_command(label="Zoom In", command=lambda: self._zoom(1.1), accelerator="+")
        view_menu.add_command(label="Zoom Out", command=lambda: self._zoom(1/1.1), accelerator="-")
        menubar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts, accelerator="F1")
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

        # Keyboard shortcuts
        self.root.bind_all("<Control-o>", lambda e: self.open_folder())
        self.root.bind_all("<Control-O>", lambda e: self.open_folder())  # sometimes Shifted
        self.root.bind_all("<Control-Shift-o>", lambda e: self.add_files())
        self.root.bind_all("<Return>", lambda e: self.open_selected())
        self.root.bind_all("<Control-e>", lambda e: self.open_external())
        self.root.bind_all("<Control-r>", lambda e: self.reveal_selected())
        self.root.bind_all("<Control-q>", lambda e: self.root.quit())
        self.root.bind_all("<Key-f>", lambda e: self.fit_to_window())
        self.root.bind_all("<Key-plus>", lambda e: self._zoom(1.1))
        self.root.bind_all("<Key-equal>", lambda e: self._zoom(1.1))
        self.root.bind_all("<Key-minus>", lambda e: self._zoom(1/1.1))
        self.root.bind_all("<Left>", lambda e: self.prev_file())
        self.root.bind_all("<Right>", lambda e: self.next_file())
        self.root.bind_all("<F1>", lambda e: self.show_shortcuts())

    def _build_layout(self):
        # Grid: toolbar (row 0), main (row 1), status (row 3)
        self.root.rowconfigure(1, weight=1)
        self.root.columnconfigure(1, weight=1)

        # Toolbar
        tb = ttk.Frame(self.root, padding=(8, 6))
        tb.grid(row=0, column=0, columnspan=2, sticky="ew")

        def B(text, cmd):
            b = ttk.Button(tb, text=text, command=cmd)
            b.pack(side=tk.LEFT, padx=4)
            return b

        B("Open Folder", self.open_folder)
        B("Add Files", self.add_files)
        ttk.Separator(tb, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=6)
        B("Open Externally", self.open_external)
        B("Show in Folder", self.reveal_selected)
        ttk.Separator(tb, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=6)
        B("Prev ←", self.prev_file)
        B("Next →", self.next_file)
        ttk.Separator(tb, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=6)
        B("Fit", self.fit_to_window)
        B("Zoom +", lambda: self._zoom(1.1))
        B("Zoom -", lambda: self._zoom(1/1.1))
        ttk.Separator(tb, orient="vertical").pack(side=tk.LEFT, fill=tk.Y, padx=6)
        B("Shortcuts", self.show_shortcuts)

        # Sidebar (files list)
        sidebar_frame = ttk.Frame(self.root)
        sidebar_frame.grid(row=1, column=0, sticky="nsw")
        sidebar_frame.rowconfigure(1, weight=1)
        sidebar_frame.columnconfigure(0, weight=1)

        ttk.Label(sidebar_frame, text="Files", padding=(8, 6)).grid(row=0, column=0, sticky="w")

        self.listbox = tk.Listbox(sidebar_frame, width=42, activestyle="dotbox")
        self.listbox.grid(row=1, column=0, sticky="nsew")
        sb_scroll = ttk.Scrollbar(sidebar_frame, orient="vertical", command=self.listbox.yview)
        sb_scroll.grid(row=1, column=1, sticky="ns")
        self.listbox.configure(yscrollcommand=sb_scroll.set)

        # Main frame holds viewer and pager bar
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.grid(row=1, column=1, sticky="nsew")
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.rowconfigure(1, weight=0)
        self.main_frame.columnconfigure(0, weight=1)

        # Canvas viewer (+ scrollbars)
        self.canvas_frame = ttk.Frame(self.main_frame)
        self.canvas_frame.grid(row=0, column=0, sticky="nsew")
        self.canvas_frame.rowconfigure(0, weight=1)
        self.canvas_frame.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.canvas_frame, bg="#303030", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.hbar = ttk.Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.hbar.grid(row=1, column=0, sticky="ew")
        self.vbar = ttk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.vbar.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(xscrollcommand=self.hbar.set, yscrollcommand=self.vbar.set)
        self.image_id = self.canvas.create_image(0, 0, anchor="nw")

        # Pager bar (bottom-left, off the image)
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
        self.page_label.pack(side=tk.LEFT, padx=(6,6))
        self.page_go_btn.pack(side=tk.LEFT)
        self.page_next_btn.pack(side=tk.LEFT, padx=(8,0))
        self._set_page_nav_visible(False)

        # Text viewer
        self.text_frame = ttk.Frame(self.main_frame)
        self.text_frame.rowconfigure(0, weight=1)
        self.text_frame.columnconfigure(0, weight=1)
        self.text_widget = tk.Text(self.text_frame, wrap="none", font=("Consolas", 11))
        self.text_widget.configure(state="disabled")
        self.text_widget.grid(row=0, column=0, sticky="nsew")
        self.text_vbar = ttk.Scrollbar(self.text_frame, orient="vertical", command=self.text_widget.yview)
        self.text_vbar.grid(row=0, column=1, sticky="ns")
        self.text_hbar = ttk.Scrollbar(self.text_frame, orient="horizontal", command=self.text_widget.xview)
        self.text_hbar.grid(row=1, column=0, sticky="ew")
        self.text_widget.configure(yscrollcommand=self.text_vbar.set, xscrollcommand=self.text_hbar.set)

        # Status bar
        self.status = ttk.Label(self.root, text="Ready", anchor="w", padding=(8, 3))
        self.status.grid(row=2, column=0, columnspan=2, sticky="ew")

    def _set_page_nav_visible(self, visible: bool):
        if visible:
            self.page_bar.grid()
        else:
            self.page_bar.grid_remove()

    def _bind_events(self):
        self.listbox.bind("<<ListboxSelect>>", self._on_select)
        self.listbox.bind("<Double-1>", lambda e: self.open_selected())
        self.listbox.bind("<Return>", lambda e: self.open_selected())

        # Context menu for list
        self._ctx = tk.Menu(self.root, tearoff=False)
        self._ctx.add_command(label="Open", command=self.open_selected)
        self._ctx.add_command(label="Open Externally", command=self.open_external)
        self._ctx.add_command(label="Show in Folder", command=self.reveal_selected)
        self.listbox.bind("<Button-3>", self._show_ctx)  # Windows/Linux
        self.listbox.bind("<Control-Button-1>", self._show_ctx)  # mac alt binding

        # Panning & Zoom (canvas)
        self.canvas.bind("<ButtonPress-1>", self._start_pan)
        self.canvas.bind("<B1-Motion>", self._do_pan)
        self.canvas.bind("<MouseWheel>", self._on_wheel)      # Win/mac
        self.canvas.bind("<Button-4>", self._on_wheel_linux)  # Linux up
        self.canvas.bind("<Button-5>", self._on_wheel_linux)  # Linux down

        # Resize
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        # PageUp/PageDown for page nav
        self.root.bind_all("<Prior>", lambda e: self.page_prev())  # PageUp
        self.root.bind_all("<Next>", lambda e: self.page_next())   # PageDown
        self.page_entry.bind("<Return>", lambda e: self.page_go())

    # ===== Convenience =====
    def _update_status(self):
        name = os.path.basename(self.current_path) if self.current_path else "—"
        zoom = f"{int(self.scale*100)}%" if (self.base_image and self.mode == 'image') else ""
        self.status.config(text=f"{name}    {zoom}")

    def _show_ctx(self, event):
        try:
            self._ctx.tk_popup(event.x_root, event.y_root)
        finally:
            self._ctx.grab_release()

    # ===== Folder & file loading =====
    def open_folder(self, initial_dir: str | None = None):
        dirpath = filedialog.askdirectory(initialdir=initial_dir or os.getcwd(), title="Select folder to view")
        if not dirpath:
            return
        self.load_directory(dirpath)

    def add_files(self):
        paths = filedialog.askopenfilenames(title="Add files to view", filetypes=[
            ("Supported", " ".join("*"+ext for ext in SUPPORTED_EXTS)),
            ("Text files", " ".join("*"+ext for ext in TEXT_EXTS)),
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

    def load_directory(self, dirpath: str):
        self.current_dir = dirpath
        entries: list[str] = []
        try:
            for f in os.listdir(dirpath):
                if f.lower().endswith(SUPPORTED_EXTS):  # keep tests stable
                    entries.append(os.path.join(dirpath, f))
        except Exception as e:
            messagebox.showerror("Error", f"""Could not list directory:
{e}""")
            return

        entries.sort(key=lambda p: os.path.basename(p).lower())
        self.files = entries
        self.listbox.delete(0, tk.END)
        for path in self.files:
            self.listbox.insert(tk.END, os.path.basename(path))
        self.current_index = 0 if self.files else None

        if self.files:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(0)
            self.listbox.activate(0)
            self._open_index(0)
        else:
            self._clear_canvas()
            self._update_status()

    def _on_select(self, _event=None):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = int(sel[0])
        self._open_index(idx)

    def _open_index(self, idx: int):
        if idx < 0 or idx >= len(self.files):
            return
        self.current_index = idx
        path = self.files[idx]
        self.open_path(path)

    def open_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        self._open_index(int(sel[0]))

    def open_external(self):
        if self.current_path:
            _system_open(self.current_path)

    def reveal_selected(self):
        if self.current_path:
            _reveal_in_file_manager(self.current_path)

    # ===== Display logic =====
    def _show_canvas_viewer(self):
        self.text_frame.grid_forget()
        self.canvas_frame.grid(row=0, column=0, sticky="nsew")

    def _show_text_viewer(self):
        self.canvas_frame.grid_forget()
        self.text_frame.grid(row=0, column=0, sticky="nsew")

    def open_path(self, path: str):
        self.current_path = path
        self.scale = 1.0
        self.auto_fit = True
        self.pdf_doc = None
        self.pdf_page_index = 0
        self.doc_page_index = 0
        self.doc_page_count = 1
        self.base_image = None

        ext = os.path.splitext(path)[1].lower()
        try:
            if ext == ".pdf":
                if fitz is None:
                    raise RuntimeError("PyMuPDF (fitz) is not installed.")
                self.pdf_doc = fitz.open(path)
                self.doc_page_count = int(self.pdf_doc.page_count)
                self.pdf_page_index = 0
                self.doc_page_index = 0
                self._render_pdf_base()
                self.mode = 'image'
                self._show_canvas_viewer()
                self._set_page_nav_visible(self.doc_page_count > 1)
            elif ext in (".tif", ".tiff"):
                img = Image.open(path)
                try:
                    self.doc_page_count = getattr(img, 'n_frames', 1)
                except Exception:
                    self.doc_page_count = 1
                img.seek(0)
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA")
                self.base_image = img
                self.mode = 'image'
                self._show_canvas_viewer()
                self._set_page_nav_visible(self.doc_page_count > 1)
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
        except Exception as e:
            messagebox.showerror("Open error", f"""Could not open {os.path.basename(path)}
{e}""")
            self._clear_canvas()
            self._update_status()
            return

        if self.mode == 'image':
            # Start at Fit zoom
            self.fit_to_window()
        self._update_status()
        self._update_page_nav()

    def _load_text_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror("Open error", f"""Could not read text file:
{e}""")
            content = ""
        self.text_widget.configure(state="normal")
        self.text_widget.delete("1.0", tk.END)
        self.text_widget.insert("1.0", content)
        self.text_widget.configure(state="disabled")

    def _render_pdf_base(self, dpi: int = 150):
        if not self.pdf_doc:
            return
        page = self.pdf_doc.load_page(self.pdf_page_index)
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        mode = "RGB" if pix.alpha == 0 else "RGBA"
        self.base_image = Image.frombytes(mode, (pix.width, pix.height), pix.samples)

    def _maybe_rerender_pdf_for_scale(self):
        if not self.pdf_doc:
            return
        if self.scale <= 1.5:
            return
        target_dpi = int(150 * min(self.scale, 4.0))
        self._render_pdf_base(dpi=target_dpi)

    def _render_to_canvas(self):
        if not self.base_image:
            return
        self._maybe_rerender_pdf_for_scale()

        img = self.base_image
        if self.scale != 1.0:
            w = max(1, int(img.width * self.scale))
            h = max(1, int(img.height * self.scale))
            img = img.resize((w, h), Resampling.LANCZOS)

        self.tk_image = ImageTk.PhotoImage(img)
        self.canvas.itemconfigure(self.image_id, image=self.tk_image)
        self.canvas.config(scrollregion=(0, 0, img.width, img.height))

    def _center_image(self):
        bbox = self.canvas.bbox(self.image_id)
        if not bbox:
            return
        img_w = bbox[2] - bbox[0]
        img_h = bbox[3] - bbox[1]
        cv_w = self.canvas.winfo_width()
        cv_h = self.canvas.winfo_height()
        x = max(0, (cv_w - img_w) // 2)
        y = max(0, (cv_h - img_h) // 2)
        self.canvas.coords(self.image_id, x, y)

    def _clear_canvas(self):
        self.canvas.itemconfigure(self.image_id, image="")
        self.canvas.config(scrollregion=(0, 0, 0, 0))
        self.base_image = None
        self.tk_image = None

    # ===== Multi-page nav =====
    def _update_page_nav(self):
        if self.mode != 'image' or self.doc_page_count <= 1:
            self._set_page_nav_visible(False)
            return
        self._set_page_nav_visible(True)
        # Update label and entry to reflect 1-based index
        self.page_label.config(text=f"/ {self.doc_page_count}")
        self.page_entry_var.set(str(self.doc_page_index + 1))
        # enable/disable
        self.page_prev_btn.state(["!disabled"])
        self.page_next_btn.state(["!disabled"])
        if self.doc_page_index <= 0:
            self.page_prev_btn.state(["disabled"])
        if self.doc_page_index >= self.doc_page_count - 1:
            self.page_next_btn.state(["disabled"])

    def _clamp_page(self, idx_0_based: int) -> int:
        """Clamp a 0-based page index to valid range."""
        if self.doc_page_count <= 0:
            return 0
        return max(0, min(self.doc_page_count - 1, idx_0_based))

    def page_go(self):
        """Jump to page from entry (1-based)."""
        try:
            entered = int(self.page_entry_var.get().strip())
        except Exception:
            self.root.bell()
            return
        target_0 = self._clamp_page(entered - 1)
        self._goto_page(target_0)

    def _goto_page(self, target_0: int):
        if self.mode != 'image' or self.doc_page_count <= 1:
            return
        target_0 = self._clamp_page(target_0)
        if target_0 == self.doc_page_index:
            return
        self.doc_page_index = target_0
        if self.pdf_doc:
            self.pdf_page_index = self.doc_page_index
            self._render_pdf_base()
        else:
            try:
                img = Image.open(self.current_path)
                img.seek(self.doc_page_index)
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA")
                self.base_image = img
            except Exception as e:
                messagebox.showerror("Page error", f"""Could not go to page {self.doc_page_index+1}:
{e}""")
                return
        self._render_to_canvas()
        self._center_image()
        self._update_page_nav()
        self._update_status()

    def page_prev(self):
        self._goto_page(self.doc_page_index - 1)

    def page_next(self):
        self._goto_page(self.doc_page_index + 1)

    # ===== File list navigation =====
    def prev_file(self):
        if self.current_index is None or not self.files:
            return
        self._open_index((self.current_index - 1) % len(self.files))

    def next_file(self):
        if self.current_index is None or not self.files:
            return
        self._open_index((self.current_index + 1) % len(self.files))

    # ===== Zoom & pan =====
    def _start_pan(self, event):
        if self.mode != 'image':
            return
        self.canvas.scan_mark(event.x, event.y)

    def _do_pan(self, event):
        if self.mode != 'image':
            return
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def _zoom(self, factor: float, focus_x: int | None = None, focus_y: int | None = None):
        if self.mode != 'image':
            return
        new_scale = max(self.min_scale, min(self.max_scale, self.scale * factor))
        if abs(new_scale - self.scale) < 1e-4:
            return
        if focus_x is not None and focus_y is not None:
            self._zoom_to_point(new_scale, focus_x, focus_y)
        else:
            self.scale = new_scale
            self._render_to_canvas()
        self.auto_fit = False
        self._update_status()

    def _zoom_to_point(self, new_scale: float, x: int, y: int):
        vx0 = self.canvas.canvasx(0)
        vy0 = self.canvas.canvasy(0)
        cx = self.canvas.canvasx(x)
        cy = self.canvas.canvasy(y)
        img_x = cx - vx0
        img_y = cy - vy0
        self.scale = new_scale
        self._render_to_canvas()
        img_bbox = self.canvas.bbox(self.image_id)
        if img_bbox:
            self.canvas.xview_moveto(max(0.0, (cx - img_x) / max(1, img_bbox[2])))
            self.canvas.yview_moveto(max(0.0, (cy - img_y) / max(1, img_bbox[3])))

    def _on_wheel(self, event):
        if self.mode != 'image':
            return
        delta = event.delta
        if sys.platform == "darwin":
            delta = -delta
        factor = 1.1 if delta > 0 else 1/1.1
        self._zoom(factor, event.x, event.y)

    def _on_wheel_linux(self, event):
        if self.mode != 'image':
            return
        factor = 1.1 if event.num == 4 else 1/1.1
        self._zoom(factor, event.x, event.y)

    def fit_to_window(self):
        if self.mode != 'image' or not self.base_image:
            return
        cv_w = max(1, self.canvas.winfo_width())
        cv_h = max(1, self.canvas.winfo_height())
        img_w, img_h = self.base_image.size
        scale_w = cv_w / img_w
        scale_h = cv_h / img_h
        new_scale = min(scale_w, scale_h)
        new_scale = max(self.min_scale, min(self.max_scale, new_scale))
        self.scale = new_scale
        self._render_to_canvas()
        self._center_image()
        self.auto_fit = True
        self._update_status()

    def actual_size(self):
        if self.mode != 'image' or not self.base_image:
            return
        self.scale = 1.0
        self._render_to_canvas()
        self._center_image()
        self.auto_fit = False
        self._update_status()

    def _on_canvas_resize(self, _event):
        if self.mode != 'image':
            return
        if self.auto_fit:
            self.fit_to_window()
        else:
            if self.base_image:
                w = int(self.base_image.width * self.scale)
                h = int(self.base_image.height * self.scale)
                self.canvas.config(scrollregion=(0, 0, w, h))

    # ===== Shortcuts dialog =====
    def show_shortcuts(self):
        shortcuts = get_shortcuts_text()
        top = tk.Toplevel(self.root)
        top.title("Keyboard Shortcuts")
        top.transient(self.root)
        top.grab_set()
        frm = ttk.Frame(top, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frm, text="Keyboard Shortcuts", font=("TkDefaultFont", 12, "bold")).pack(anchor="w", pady=(0,6))
        txt = tk.Text(frm, width=48, height=12, wrap="word")
        txt.pack(fill=tk.BOTH, expand=True)
        txt.insert("1.0", shortcuts)
        txt.configure(state="disabled")
        ttk.Button(frm, text="Close", command=top.destroy).pack(anchor="e", pady=(8,0))


def get_shortcuts_text() -> str:
    """Builds and returns the keyboard shortcuts list as a single string."""
    lines = [
        "Ctrl+O — Open Folder",
        "Ctrl+Shift+O — Add Files",
        "Enter/Double-click — Open selected",
        "Ctrl+E — Open externally",
        "Ctrl+R — Show in folder",
        "←/→ — Previous/Next",
        "+ / - — Zoom in/out",
        "1 — Actual size",
        "F — Fit to window",
        "F1 — Keyboard shortcuts",
    ]
    return "\n".join(lines)


def main():
    root = tk.Tk()
    app = FileViewerApp(root)
    root.mainloop()


if __name__ == "__main__":
    if "--test" in sys.argv:
        import unittest

        class UtilsTests(unittest.TestCase):
            def test_is_supported(self):
                self.assertTrue(_is_supported("a.png"))
                self.assertTrue(_is_supported("b.PDF"))
                self.assertFalse(_is_supported("c.txt"))

            def test_paths_added_unique(self):
                s = set()
                files = ["/tmp/x.png", "/tmp/x.png", "/tmp/y.jpg"]
                for p in files:
                    if _is_supported(p) and p not in s:
                        s.add(p)
                self.assertEqual(len(s), 2)

            def test_shortcuts_text_has_lines(self):
                text = get_shortcuts_text()
                self.assertIn("Ctrl+O — Open Folder", text)
                self.assertIn("F1 — Keyboard shortcuts", text)
                self.assertEqual(len([ln for ln in text.split("\n") if ln.strip() != ""]), 10)

            def test_supported_exts_case_insensitive(self):
                self.assertTrue(_is_supported("PIC.JpEg"))
                self.assertTrue(_is_supported("scan.TIFF"))
                self.assertTrue(_is_supported("doc.PdF"))

            def test_is_text_helper(self):
                self.assertTrue(_is_text("notes.txt"))
                self.assertTrue(_is_text("README.MD"))
                self.assertTrue(_is_text("data.csv"))
                self.assertFalse(_is_text("image.png"))

            def test_clamp_page(self):
                class D:
                    doc_page_count = 10
                d = D()
                # Directly call the instance method with a dummy object
                self.assertEqual(FileViewerApp._clamp_page(d, -5), 0)
                self.assertEqual(FileViewerApp._clamp_page(d, 0), 0)
                self.assertEqual(FileViewerApp._clamp_page(d, 9), 9)
                self.assertEqual(FileViewerApp._clamp_page(d, 99), 9)

        unittest.main(argv=[arg for arg in sys.argv if arg != "--test"])  # run tests
    else:
        main()
