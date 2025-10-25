import os
import sys
import json
import re
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from PIL.Image import Resampling

"""
Image/PDF/Text File Viewer (stable, with pop-out mirror and placeholders)

- No f-strings (uses concatenation) to avoid parser issues you saw earlier
- Fit-to-Window, pan (mouse drag), zoom (+/- or wheel)
- Sessions are MANUAL ONLY (Save/Load via menu). Config (preferences/presets) persists
- Presets menu (save/load the current file list)
- Multi-page pager (PDF & multi-frame TIFF)
- Text viewer for .txt/.md/.csv/.log/.res
- Pop Out window mirrors the main preview; shortcuts act on both, panning is kept in sync
- Left inputs use ghost placeholders that disappear on focus and return if empty
- Resizable layout; right preview area a bit larger by default; min-widths to keep things visible
- Bulk Rename (preview + apply) following your rules
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
        messagebox.showerror("Open Externally", "Could not open with system app:\n" + str(e))


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
        messagebox.showerror("Show in Folder", "Could not reveal file:\n" + str(e))


# ---------- app ----------
class FileViewerApp:
    def __init__(self, root, start_dir: str | None = None):
        self.root = root
        self.root.title("File Viewer")
        self.root.geometry("1480x940")   # a bit larger to comfortably fit everything
        self.root.minsize(1200, 780)

        # ttk padding tweaks (keep system colors)
        try:
            style = ttk.Style()
            style.configure("TButton", padding=(6, 4))
            style.configure("TLabel", padding=(2, 2))
            style.configure("TEntry", padding=(2, 2))
        except Exception:
            pass

        # state
        self.current_dir = start_dir
        self.files = []                # type: list[str]
        self.current_index = None      # type: int | None
        self.current_path = None       # type: str | None
        self.mode = None               # 'image' or 'text'

        # image/pdf render state
        self.base_image = None         # type: Image.Image | None
        self.tk_image = None           # type: ImageTk.PhotoImage | None
        self.scale = 1.0               # current scale applied to base_image
        self.min_scale = 0.1
        self.max_scale = 8.0
        self.auto_fit = True           # if True, resize triggers re-fit
        self._center_next_render = True  # center view on next render

        # pop-out window mirror
        self.popwin = None
        self.pop_canvas = None
        self.pop_tk_image = None

        # multi-page
        self.pdf_doc = None
        self.pdf_page_index = 0
        self.doc_page_index = 0
        self.doc_page_count = 1

        # config (preferences + presets)
        self.config = {
            "default_open_dir": None,          # str | None
            "default_session_path": None,      # str | None
            "presets": {}                      # name -> list[str]
        }

        # rename preview state
        self.rename_preview = {}   # index -> new_basename (with extension preserved)

        # ui
        self._build_menu()
        self._build_layout()
        self._bind_events()

        # load config only (sessions are manual)
        self._load_config()
        if self.current_dir is None and self.config.get("default_open_dir"):
            self.current_dir = self.config.get("default_open_dir")
        if self.current_dir and os.path.isdir(self.current_dir) and not self.files:
            self.load_directory(self.current_dir)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # set initial sash (~45% left, 55% right — larger preview)
        self.root.after(60, self._init_panes)

    # ----- UI -----
    def _build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Open Folder…", command=self.open_folder, accelerator="Ctrl+O")
        file_menu.add_command(label="Add Files…", command=self.add_files, accelerator="Ctrl+Shift+O")
        file_menu.add_command(label="Remove Selected", command=self.remove_selected, accelerator="Del")
        file_menu.add_separator()
        file_menu.add_command(label="Save Session", command=self.save_session, accelerator="Ctrl+S")
        file_menu.add_command(label="Save Session As…", command=self.save_session_as)
        file_menu.add_command(label="Load Session…", command=self.load_session_from_file)
        file_menu.add_command(label="Clear Session", command=self.clear_session_ui)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.root.quit, accelerator="Ctrl+Q")
        menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=False)
        view_menu.add_command(label="Fit to Window", command=self.fit_to_window, accelerator="F")
        view_menu.add_command(label="Fit Width", command=self.fit_width)
        view_menu.add_command(label="Fit Height", command=self.fit_height)
        view_menu.add_command(label="Zoom In", command=lambda: self._zoom(1.1), accelerator="+")
        view_menu.add_command(label="Zoom Out", command=lambda: self._zoom(1/1.1), accelerator="-")
        menubar.add_cascade(label="View", menu=view_menu)

        presets_menu = tk.Menu(menubar, tearoff=False)
        presets_menu.add_command(label="Save Current as Preset…", command=self.save_preset)
        presets_menu.add_command(label="Load Preset…", command=self.load_preset)
        menubar.add_cascade(label="Presets", menu=presets_menu)

        tools_menu = tk.Menu(menubar, tearoff=False)
        tools_menu.add_command(label="Scan Renames", command=self.scan_bulk_renames)
        tools_menu.add_command(label="Clear Rename Preview", command=self.clear_bulk_rename_preview)
        tools_menu.add_command(label="Apply Renames…", command=self.apply_bulk_renames)
        menubar.add_cascade(label="Tools", menu=tools_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts, accelerator="F1")
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def _build_layout(self):
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Paned window: LEFT (tree + inputs) | RIGHT (preview + controls)
        self.pw = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        self.pw.grid(row=0, column=0, sticky="nsew")

        # =============== LEFT =================
        self.left_frame = ttk.Frame(self.pw, padding=(8, 8, 6, 8))
        self.left_frame.columnconfigure(0, weight=1, minsize=560)
        self.left_frame.rowconfigure(1, weight=1)
        self.pw.add(self.left_frame, weight=3)

        # Treeview (no top label per request)
        self.research = ttk.Treeview(
            self.left_frame,
            columns=("uuid", "name", "comments"),
            show="headings",
            selectmode="browse"
        )
        self.research.heading("uuid", text="UUID")
        self.research.heading("name", text="Document Name")
        self.research.heading("comments", text="Comments")
        self.research.column("uuid", width=160, minwidth=140, anchor="w", stretch=False)
        self.research.column("name", width=360, minwidth=320, anchor="w", stretch=True)
        self.research.column("comments", width=220, minwidth=160, anchor="w", stretch=True)
        self.research.grid(row=1, column=0, sticky="nsew", pady=(0, 8))
        r_sb = ttk.Scrollbar(self.left_frame, orient="vertical", command=self.research.yview)
        r_sb.grid(row=1, column=1, sticky="ns", pady=(0, 8))
        self.research.configure(yscrollcommand=r_sb.set)

        # demo rows
        for i in range(1, 9):
            self.research.insert("", "end", values=("UUID-" + str(i), "Document " + str(i), "Example note"))

        # Two labeled text boxes with ghost placeholders
        sub = ttk.Frame(self.left_frame)
        sub.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        sub.columnconfigure(0, weight=1, minsize=260)
        sub.columnconfigure(1, weight=1, minsize=260)

        doc_group = ttk.LabelFrame(sub, text="Documents")
        com_group = ttk.LabelFrame(sub, text="Comments")
        doc_group.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        com_group.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        self.doc_var = tk.StringVar()
        self.com_var = tk.StringVar()
        self.doc_entry = ttk.Entry(doc_group, textvariable=self.doc_var)
        self.com_entry = ttk.Entry(com_group, textvariable=self.com_var)
        self.doc_entry.pack(fill=tk.X, padx=8, pady=8)
        self.com_entry.pack(fill=tk.X, padx=8, pady=8)
        self._add_placeholder(self.doc_entry, "Documents")
        self._add_placeholder(self.com_entry, "Comments")

        # Bottom row of buttons + checkbox (placeholders)
        actions = ttk.Frame(self.left_frame)
        actions.grid(row=3, column=0, columnspan=2, sticky="ew")
        for i in range(1, 6):
            actions.columnconfigure(i, weight=1)
        ttk.Button(actions, text="Enter Record").grid(row=0, column=0, padx=4, pady=6, sticky="ew")
        ttk.Button(actions, text="Edit Record").grid(row=0, column=1, padx=4, pady=6, sticky="ew")
        ttk.Button(actions, text="Delete Record").grid(row=0, column=2, padx=4, pady=6, sticky="ew")
        ttk.Button(actions, text="Log to Files").grid(row=0, column=3, padx=4, pady=6, sticky="ew")
        ttk.Checkbutton(actions, text="A Butter").grid(row=0, column=4, padx=4, pady=6, sticky="e")

        # =============== RIGHT =================
        self.right = ttk.Frame(self.pw, padding=(6, 8, 8, 8))
        self.right.columnconfigure(0, weight=1, minsize=560)
        self.right.rowconfigure(1, weight=1)
        self.right.rowconfigure(5, weight=1)
        self.pw.add(self.right, weight=4)

        # Top buttons row
        topbar = ttk.Frame(self.right)
        topbar.grid(row=0, column=0, sticky="ew")
        for i in range(4):
            topbar.columnconfigure(i, weight=1)
        ttk.Button(topbar, text="Open Folder", command=self.open_folder).grid(row=0, column=0, padx=4, pady=(0, 6), sticky="ew")
        ttk.Button(topbar, text="Add File", command=self.add_files).grid(row=0, column=1, padx=4, pady=(0, 6), sticky="ew")
        ttk.Button(topbar, text="Remove File", command=self.remove_selected).grid(row=0, column=2, padx=4, pady=(0, 6), sticky="ew")
        ttk.Button(topbar, text="Pop Out", command=self.pop_out).grid(row=0, column=3, padx=4, pady=(0, 6), sticky="ew")

        # Preview window (Canvas/Text) — larger area
        preview_border = ttk.Frame(self.right, relief="groove", borderwidth=2)
        preview_border.grid(row=1, column=0, sticky="nsew")
        preview_border.rowconfigure(0, weight=1)
        preview_border.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(preview_border, bg="#303030", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.image_id = self.canvas.create_image(0, 0, anchor="nw")

        # Text viewer
        self.text_frame = ttk.Frame(preview_border)
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

        # Row: Prev/Next (full width)
        nav_row = ttk.Frame(self.right)
        nav_row.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        nav_row.columnconfigure(0, weight=1)
        nav_row.columnconfigure(1, weight=1)
        ttk.Button(nav_row, text="Previous File", command=self.prev_file).grid(row=0, column=0, padx=4, sticky="ew")
        ttk.Button(nav_row, text="Next File", command=self.next_file).grid(row=0, column=1, padx=4, sticky="ew")

        # Row: Fit W | Fit H | Zoom + | Help
        zoom_row = ttk.Frame(self.right)
        zoom_row.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        for i in range(4):
            zoom_row.columnconfigure(i, weight=1)
        ttk.Button(zoom_row, text="Fit W", command=self.fit_width).grid(row=0, column=0, padx=4, sticky="ew")
        ttk.Button(zoom_row, text="Fit H", command=self.fit_height).grid(row=0, column=1, padx=4, sticky="ew")
        ttk.Button(zoom_row, text="Zoom +", command=lambda: self._zoom(1.1)).grid(row=0, column=2, padx=4, sticky="ew")
        ttk.Button(zoom_row, text="Help", command=self.show_shortcuts).grid(row=0, column=3, padx=4, sticky="ew")

        # Row: Scan | Clear | Apply
        tools_row = ttk.Frame(self.right)
        tools_row.grid(row=4, column=0, sticky="ew", pady=(6, 0))
        for i in range(3):
            tools_row.columnconfigure(i, weight=1)
        ttk.Button(tools_row, text="Scan", command=self.scan_bulk_renames).grid(row=0, column=0, padx=4, sticky="ew")
        ttk.Button(tools_row, text="Clear", command=self.clear_bulk_rename_preview).grid(row=0, column=1, padx=4, sticky="ew")
        ttk.Button(tools_row, text="Apply", command=self.apply_bulk_renames).grid(row=0, column=2, padx=4, sticky="ew")

        # List of files
        files_box = ttk.LabelFrame(self.right, text="List of files")
        files_box.grid(row=5, column=0, sticky="nsew", pady=(8, 0))
        files_box.rowconfigure(0, weight=1)
        files_box.columnconfigure(0, weight=1)

        self.listbox = tk.Listbox(files_box, activestyle="dotbox")
        self.listbox.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        sb = ttk.Scrollbar(files_box, orient="vertical", command=self.listbox.yview)
        sb.grid(row=0, column=1, sticky="ns", pady=6)
        self.listbox.configure(yscrollcommand=sb.set)

        # Pager (hidden until needed)
        self.page_bar = ttk.Frame(self.right)
        self.page_bar.grid_forget()
        self.page_prev_btn = ttk.Button(self.page_bar, text="◀ Prev", command=self.page_prev, width=8)
        self.page_entry_var = tk.StringVar(value="1")
        self.page_entry = ttk.Entry(self.page_bar, width=6, textvariable=self.page_entry_var)
        self.page_go_btn = ttk.Button(self.page_bar, text="Go", command=self.page_go, width=4)
        self.page_label = ttk.Label(self.page_bar, text="/ 1")
        self.page_next_btn = ttk.Button(self.page_bar, text="Next ▶", command=self.page_next, width=8)
        self.page_prev_btn.pack(side=tk.LEFT)
        ttk.Label(self.page_bar, text=" Page ").pack(side=tk.LEFT)
        self.page_entry.pack(side=tk.LEFT)
        self.page_label.pack(side=tk.LEFT, padx=(6, 6))
        self.page_go_btn.pack(side=tk.LEFT)
        self.page_next_btn.pack(side=tk.LEFT, padx=(8, 0))

        # Status bar
        self.status = ttk.Label(self.root, text="Ready", anchor="w", padding=(8, 4))
        self.status.grid(row=1, column=0, sticky="ew")

    def _init_panes(self):
        try:
            self.pw.pane(self.left_frame, minsize=560)
            self.pw.pane(self.right, minsize=560)
        except Exception:
            pass
        try:
            total = self.pw.winfo_width() or self.root.winfo_width()
            self.pw.sashpos(0, int(total * 0.45))  # bigger preview (right ~55%)
        except Exception:
            pass

    # ----- events -----
    def _bind_events(self):
        self.root.bind_all("<Control-o>", lambda e: self.open_folder())
        self.root.bind_all("<Control-Shift-o>", lambda e: self.add_files())
        self.root.bind_all("<Delete>", lambda e: self.remove_selected())
        self.root.bind_all("<Control-s>", lambda e: self.save_session())
        self.root.bind_all("<Left>", lambda e: self.prev_file())
        self.root.bind_all("<Right>", lambda e: self.next_file())
        self.root.bind_all("<Key-plus>", lambda e: self._zoom(1.1))
        self.root.bind_all("<Key-equal>", lambda e: self._zoom(1.1))
        self.root.bind_all("<Key-minus>", lambda e: self._zoom(1/1.1))
        self.root.bind_all("<Key-f>", lambda e: self.fit_to_window())
        self.root.bind_all("<F1>", lambda e: self.show_shortcuts())

        self.listbox.bind("<<ListboxSelect>>", self._on_select)
        self.listbox.bind("<Double-1>", lambda e: self.open_selected())
        self.listbox.bind("<Return>", lambda e: self.open_selected())
        self._ctx = tk.Menu(self.root, tearoff=False)
        self._ctx.add_command(label="Open", command=self.open_selected)
        self._ctx.add_command(label="Open Externally", command=self.open_external)
        self._ctx.add_command(label="Show in Folder", command=self.reveal_selected)
        self._ctx.add_separator()
        self._ctx.add_command(label="Remove", command=self.remove_selected)
        self.listbox.bind("<Button-3>", self._show_ctx)
        self.listbox.bind("<Control-Button-1>", self._show_ctx)

        # main canvas
        self.canvas.bind("<Configure>", self._on_canvas_resize)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Button-4>", self._on_wheel_linux)
        self.canvas.bind("<Button-5>", self._on_wheel_linux)
        self.canvas.bind("<ButtonPress-1>", lambda e: self._start_pan(self.canvas, e))
        self.canvas.bind("<B1-Motion>", lambda e: self._do_pan(self.canvas, e))

        self.page_entry.bind("<Return>", lambda e: self.page_go())

    # ----- placeholders -----
    def _add_placeholder(self, entry: ttk.Entry, text: str):
        normal_fg = entry.cget("foreground") or "black"
        ph_fg = "#888"
        entry._placeholder = text  # type: ignore[attr-defined]
        entry._is_placeholder = True  # type: ignore[attr-defined]
        entry.configure(foreground=ph_fg)
        entry.insert(0, text)

        def on_focus_in(_e):
            if getattr(entry, "_is_placeholder", False):
                entry.delete(0, tk.END)
                entry.configure(foreground=normal_fg)
                entry._is_placeholder = False  # type: ignore[attr-defined]

        def on_focus_out(_e):
            if entry.get().strip() == "":
                entry.configure(foreground=ph_fg)
                entry.delete(0, tk.END)
                entry.insert(0, text)
                entry._is_placeholder = True  # type: ignore[attr-defined]

        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    # ----- utils -----
    def _show_ctx(self, event):
        try:
            self._ctx.tk_popup(event.x_root, event.y_root)
        finally:
            self._ctx.grab_release()

    def _set_page_nav_visible(self, visible: bool):
        if visible:
            self.page_bar.grid(row=2, column=0, sticky="w", padx=8, pady=(6, 0))
        else:
            self.page_bar.grid_forget()

    def _update_status(self):
        name = os.path.basename(self.current_path) if self.current_path else "—"
        zoom = (" " + str(int(self.scale * 100)) + "%") if (self.mode == 'image' and self.base_image) else ""
        self.status.config(text=name + zoom)

    # ----- open / list ops -----
    def open_folder(self, initial_dir: str | None = None):
        start_dir = initial_dir or self.config.get("default_open_dir") or os.getcwd()
        dirpath = filedialog.askdirectory(initialdir=start_dir, title="Select folder to view")
        if not dirpath:
            return
        self.load_directory(dirpath)

    def add_files(self):
        start_dir = self.config.get("default_open_dir") or os.getcwd()
        paths = filedialog.askopenfilenames(title="Add files to view", initialdir=start_dir, filetypes=[
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

    def remove_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        idx = int(sel[0])
        if 0 <= idx < len(self.files):
            self.files.pop(idx)
            self.listbox.delete(idx)
            if idx in self.rename_preview:
                self.rename_preview.pop(idx, None)
            new_preview = {}
            for k, v in self.rename_preview.items():
                new_preview[k - 1 if k > idx else k] = v
            self.rename_preview = {k: v for k, v in new_preview.items() if k >= 0}
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

    def load_directory(self, dirpath: str):
        self.current_dir = dirpath
        self.rename_preview.clear()
        entries = []
        try:
            for f in os.listdir(dirpath):
                if f.lower().endswith(SUPPORTED_EXTS):
                    entries.append(os.path.join(dirpath, f))
        except Exception as e:
            messagebox.showerror("Error", "Could not list directory:\n" + str(e))
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
        self.canvas.grid(row=0, column=0, sticky="nsew")

    def _show_text_viewer(self):
        self.canvas.grid_forget()
        self.text_frame.grid(row=0, column=0, sticky="nsew")

    # ----- open path -----
    def open_path(self, path: str):
        self.current_path = path
        self.base_image = None
        self.tk_image = None
        self.scale = 1.0
        self.auto_fit = True
        self._center_next_render = True
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
            messagebox.showerror("Open Error", "Could not open " + os.path.basename(path) + "\n" + str(e))
            self._clear_canvas()
            self._update_status()
            return

        if self.mode == 'image':
            self.fit_to_window()
        self._update_status()
        self._update_page_nav()

    # ----- text loader -----
    def _load_text_file(self, path: str):
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            messagebox.showerror("Open Error", "Could not read text file:\n" + str(e))
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

    # ----- scale helpers -----
    def _fit_scale(self) -> float:
        if not self.base_image:
            return 1.0
        cv_w = max(1, self.canvas.winfo_width())
        cv_h = max(1, self.canvas.winfo_height())
        img_w, img_h = self.base_image.size
        return min(float(cv_w) / float(img_w), float(cv_h) / float(img_h))

    def fit_width(self):
        if self.mode != 'image' or not self.base_image:
            return
        cv_w = max(1, self.canvas.winfo_width())
        img_w = self.base_image.size[0]
        self.scale = max(self.min_scale, min(self.max_scale, float(cv_w) / float(img_w)))
        self.auto_fit = False
        self._center_next_render = True
        self._render_all()
        self._update_status()

    def fit_height(self):
        if self.mode != 'image' or not self.base_image:
            return
        cv_h = max(1, self.canvas.winfo_height())
        img_h = self.base_image.size[1]
        self.scale = max(self.min_scale, min(self.max_scale, float(cv_h) / float(img_h)))
        self.auto_fit = False
        self._center_next_render = True
        self._render_all()
        self._update_status()

    # ----- canvas render & zoom & pan -----
    def _render_all(self):
        # render main
        self._render_to_canvas()
        # render popup mirror if present
        if self.pop_canvas is not None and self.base_image is not None:
            img = self.base_image
            w = max(1, int(img.width * self.scale))
            h = max(1, int(img.height * self.scale))
            scaled = img.resize((w, h), Resampling.LANCZOS)
            self.pop_tk_image = ImageTk.PhotoImage(scaled)
            self.pop_canvas.delete("all")
            self.pop_canvas.create_image(0, 0, anchor="nw", image=self.pop_tk_image)
            self.pop_canvas.config(scrollregion=(0, 0, scaled.width, scaled.height))
            # center once when opening
            try:
                cv_w = max(1, self.pop_canvas.winfo_width())
                cv_h = max(1, self.pop_canvas.winfo_height())
                x0 = max(0, (scaled.width - cv_w) / 2.0)
                y0 = max(0, (scaled.height - cv_h) / 2.0)
                if scaled.width > 0:
                    self.pop_canvas.xview_moveto(x0 / float(scaled.width))
                if scaled.height > 0:
                    self.pop_canvas.yview_moveto(y0 / float(scaled.height))
            except Exception:
                pass

    def _render_to_canvas(self):
        if not self.base_image:
            return
        img = self.base_image
        w = max(1, int(img.width * self.scale))
        h = max(1, int(img.height * self.scale))
        scaled = img.resize((w, h), Resampling.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(scaled)
        self.canvas.delete("all")
        self.image_id = self.canvas.create_image(0, 0, anchor="nw", image=self.tk_image)
        self.canvas.config(scrollregion=(0, 0, scaled.width, scaled.height))
        if self._center_next_render:
            cv_w = max(1, self.canvas.winfo_width())
            cv_h = max(1, self.canvas.winfo_height())
            x0 = max(0, (scaled.width - cv_w) / 2.0)
            y0 = max(0, (scaled.height - cv_h) / 2.0)
            if scaled.width > 0:
                self.canvas.xview_moveto(x0 / float(scaled.width))
            if scaled.height > 0:
                self.canvas.yview_moveto(y0 / float(scaled.height))
            self._center_next_render = False

    def _on_canvas_resize(self, _event):
        if self.mode != 'image' or not self.base_image:
            return
        if self.auto_fit:
            self.scale = self._fit_scale()
            self._center_next_render = True
        self._render_all()
        self._update_status()

    def _zoom(self, factor: float):
        if self.mode != 'image' or not self.base_image:
            return
        new_scale = max(self.min_scale, min(self.max_scale, self.scale * factor))
        if abs(new_scale - self.scale) < 1e-4:
            return
        self.scale = new_scale
        self.auto_fit = False
        self._center_next_render = False
        self._render_all()
        self._update_status()

    # --- panning (sync both canvases) ---
    def _start_pan(self, canvas: tk.Canvas, event):
        if self.mode != 'image' or not self.base_image:
            return
        canvas.scan_mark(event.x, event.y)

    def _do_pan(self, canvas: tk.Canvas, event):
        if self.mode != 'image' or not self.base_image:
            return
        canvas.scan_dragto(event.x, event.y, gain=1)
        # mirror pan positions
        try:
            if canvas is self.canvas and self.pop_canvas is not None:
                self.pop_canvas.xview_moveto(self.canvas.xview()[0])
                self.pop_canvas.yview_moveto(self.canvas.yview()[0])
            elif canvas is self.pop_canvas:
                self.canvas.xview_moveto(self.pop_canvas.xview()[0])
                self.canvas.yview_moveto(self.pop_canvas.yview()[0])
        except Exception:
            pass

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
        self.scale = self._fit_scale()
        self.auto_fit = True
        self._center_next_render = True
        self._render_all()
        self._update_status()

    def _clear_canvas(self):
        self.canvas.delete("all")
        self.canvas.config(scrollregion=(0, 0, 0, 0))
        if self.pop_canvas is not None:
            try:
                self.pop_canvas.delete("all")
                self.pop_canvas.config(scrollregion=(0, 0, 0, 0))
            except Exception:
                pass

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
        if self.auto_fit:
            self.scale = self._fit_scale()
            self._center_next_render = True
        self._render_all()
        self._update_page_nav()
        self._update_status()

    def page_next(self):
        if self.mode != 'image' or self.doc_page_count <= 1:
            return
        if self.pdf_doc:
            if self.pdf_page_index < self.doc_page_count - 1:
                self.pdf_page_index += 1
                self._render_pdf_page()
        else:
            self._goto_image_frame(self.doc_page_index + 1)
        if self.auto_fit:
            self.scale = self._fit_scale()
            self._center_next_render = True
        self._render_all()
        self._update_page_nav()
        self._update_status()

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
        if self.auto_fit:
            self.scale = self._fit_scale()
            self._center_next_render = True
        self._render_all()
        self._update_page_nav()
        self._update_status()

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
        except Exception as e:
            messagebox.showerror("Page", "Could not change page:\n" + str(e))

    # ----- Bulk rename helpers -----
    def _suggest_rename_for_base(self, base_without_ext: str, ext: str) -> str | None:
        paren_pat = re.compile(r"\(([^)]*)\)")
        notes = paren_pat.findall(base_without_ext)
        remainder = paren_pat.sub("", base_without_ext).strip()
        if re.fullmatch(r"\d+", remainder):
            new_base = "Map#" + remainder
        else:
            m = re.fullmatch(r"(\d+)-(\d+)", remainder)
            if not m:
                return None
            a = m.group(1)
            b = m.group(2)
            new_base = "Vol." + a + "-Pg." + b
        if notes:
            note = " " + "(" + " ".join([n.strip() for n in notes if n.strip() != ""]) + ")"
            new_base = new_base + note
        return new_base + ext

    def scan_bulk_renames(self):
        self.rename_preview.clear()
        for i, p in enumerate(self.files):
            base = os.path.basename(p)
            root, ext = os.path.splitext(base)
            suggestion = self._suggest_rename_for_base(root, ext)
            self.listbox.delete(i)
            self.listbox.insert(i, suggestion if suggestion else base)
            try:
                self.listbox.itemconfig(i, fg=("blue" if suggestion else "black"))
            except Exception:
                pass
            if suggestion:
                self.rename_preview[i] = suggestion
        if self.current_index is not None and self.current_index < self.listbox.size():
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.current_index)
            self.listbox.activate(self.current_index)

    def _unique_name_in_folder(self, folder: str, desired_name: str) -> str:
        name_root, ext = os.path.splitext(desired_name)
        candidate = desired_name
        n = 2
        while os.path.exists(os.path.join(folder, candidate)):
            candidate = name_root + " (" + str(n) + ")" + ext
            n += 1
        return candidate

    def apply_bulk_renames(self):
        if not self.rename_preview:
            messagebox.showinfo("Apply Renames", "Nothing to rename. Use Scan Renames first.")
            return
        proceed = messagebox.askyesno("Apply Renames", "Rename " + str(len(self.rename_preview)) + " file(s) now?")
        if not proceed:
            return
        new_files = list(self.files)
        for i, new_display in list(self.rename_preview.items()):
            if i < 0 or i >= len(self.files):
                continue
            old_full = self.files[i]
            folder = os.path.dirname(old_full)
            old_base = os.path.basename(old_full)
            root_disk, ext_disk = os.path.splitext(old_base)
            root_new, _ = os.path.splitext(new_display)
            dest_name = root_new + ext_disk
            if os.path.exists(os.path.join(folder, dest_name)):
                dest_name = self._unique_name_in_folder(folder, dest_name)
            src = old_full
            dst = os.path.join(folder, dest_name)
            try:
                os.rename(src, dst)
            except Exception as e:
                messagebox.showerror("Rename", "Could not rename:\n" + src + "\n→ " + dst + "\n" + str(e))
                continue
            new_files[i] = dst
            self.listbox.delete(i)
            self.listbox.insert(i, dest_name)
            try:
                self.listbox.itemconfig(i, fg="black")
            except Exception:
                pass
            if self.current_index == i:
                self.current_path = dst
        self.files = new_files
        self.rename_preview.clear()
        if self.current_index is not None and self.current_index < len(self.files):
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.current_index)
            self.listbox.activate(self.current_index)
        messagebox.showinfo("Apply Renames", "Renaming complete.")

    def clear_bulk_rename_preview(self):
        for i, p in enumerate(self.files):
            base = os.path.basename(p)
            try:
                self.listbox.delete(i)
                self.listbox.insert(i, base)
                try:
                    self.listbox.itemconfig(i, fg="black")
                except Exception:
                    pass
            except Exception:
                pass
        self.rename_preview.clear()
        if self.current_index is not None and self.current_index < self.listbox.size():
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(self.current_index)
            self.listbox.activate(self.current_index)

    # ----- session & config (manual sessions) -----
    def _state_path(self) -> str:
        cfg_path = self.config.get("default_session_path")
        if cfg_path:
            return cfg_path
        return os.path.join(os.path.expanduser("~"), ".fileviewer_session.json")

    def _config_path(self) -> str:
        return os.path.join(os.path.expanduser("~"), ".fileviewer_config.json")

    def save_session(self):
        path = self._state_path() if self.config.get("default_session_path") else None
        if not path:
            self.save_session_as()
            return
        self._write_session(path)

    def save_session_as(self):
        path = filedialog.asksaveasfilename(title="Save Session As…", defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return
        self._write_session(path)

    def _write_session(self, path: str):
        try:
            data = {
                "files": self.files,
                "current_index": self.current_index,
                "current_path": self.current_path,
                "page_index": self.pdf_page_index if self.pdf_doc else self.doc_page_index,
                "current_dir": self.current_dir,
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            messagebox.showerror("Save Session", "Could not save session:\n" + str(e))

    def load_session_from_file(self):
        path = filedialog.askopenfilename(title="Load Session…", filetypes=[("JSON", "*.json"), ("All files", "*.*")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            files = [p for p in data.get("files", []) if os.path.exists(p) and (_is_supported(p) or _is_text(p))]
            self.files = files
            self.listbox.delete(0, tk.END)
            for p in self.files:
                self.listbox.insert(tk.END, os.path.basename(p))
            self.current_dir = data.get("current_dir")
            idx = data.get("current_index")
            if idx is None or not (0 <= idx < len(self.files)):
                idx = 0 if self.files else None
            if idx is not None:
                self._open_index(idx)
            self.doc_page_index = int(data.get("page_index") or 0)
            if self.doc_page_count > 1:
                self.page_entry_var.set(str(self.doc_page_index + 1))
                self.page_go()
        except Exception as e:
            messagebox.showerror("Load Session", "Could not load session:\n" + str(e))

    def _load_config(self):
        path = self._config_path()
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self.config.update(data)
        except Exception:
            pass

    def _save_config(self):
        try:
            with open(self._config_path(), "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2)
        except Exception:
            pass

    def clear_session_ui(self):
        self.files.clear()
        self.rename_preview.clear()
        self.listbox.delete(0, tk.END)
        self._clear_canvas()
        self.current_index = None
        self.current_path = None
        self._update_status()

    def _on_close(self):
        self._save_config()
        try:
            if self.popwin is not None:
                self.popwin.destroy()
        except Exception:
            pass
        self.root.destroy()

    # ----- presets -----
    def save_preset(self):
        top = tk.Toplevel(self.root)
        top.title("Save Preset")
        ttk.Label(top, text="Preset name:").pack(padx=12, pady=(12, 6), anchor="w")
        name_var = tk.StringVar()
        e = ttk.Entry(top, textvariable=name_var, width=32)
        e.pack(padx=12, pady=(0, 12), fill=tk.X)
        e.focus_set()

        def do_save():
            name = name_var.get().strip()
            if not name:
                self.root.bell()
                return
            self.config.setdefault("presets", {})[name] = list(self.files)
            self._save_config()
            top.destroy()

        ttk.Button(top, text="Save", command=do_save).pack(padx=12, pady=(0, 12))

    def load_preset(self):
        presets = self.config.get("presets") or {}
        if not presets:
            messagebox.showinfo("Presets", "No presets saved yet.")
            return
        top = tk.Toplevel(self.root)
        top.title("Load Preset")
        ttk.Label(top, text="Choose a preset:").pack(padx=12, pady=(12, 6), anchor="w")
        lb = tk.Listbox(top, width=30, height=8)
        for k in sorted(presets.keys()):
            lb.insert(tk.END, k)
        lb.pack(padx=12, pady=(0, 12), fill=tk.BOTH, expand=True)

        def do_load():
            sel = lb.curselection()
            if not sel:
                self.root.bell()
                return
            name = lb.get(sel[0])
            files = [p for p in presets.get(name, []) if os.path.exists(p) and (_is_supported(p) or _is_text(p))]
            self.files = files
            self.listbox.delete(0, tk.END)
            for p in self.files:
                self.listbox.insert(tk.END, os.path.basename(p))
            if self.files:
                self._open_index(0)
            else:
                self._clear_canvas()
                self._update_status()
            top.destroy()

        ttk.Button(top, text="Load", command=do_load).pack(padx=12, pady=(0, 12))

    # ----- shortcuts -----
    def show_shortcuts(self):
        lines = [
            "Ctrl+O — Open Folder",
            "Ctrl+Shift+O — Add Files",
            "Delete — Remove selected",
            "Ctrl+S — Save session",
            "Enter/Double-click — Open selected",
            "Ctrl+E — Open externally",
            "Ctrl+R — Show in folder",
            "Mouse drag — Pan image",
            "+ / - — Zoom in/out",
            "F — Fit to window",
            "F1 — Keyboard Shortcuts",
        ]
        txt = "\n".join(lines)
        top = tk.Toplevel(self.root)
        top.title("Keyboard Shortcuts")
        frm = ttk.Frame(top, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)
        t = tk.Text(frm, width=56, height=14, wrap="word")
        t.pack(fill=tk.BOTH, expand=True)
        t.insert("1.0", txt)
        t.configure(state="disabled")
        ttk.Button(frm, text="Close", command=top.destroy).pack(anchor="e", pady=(8, 0))

    # ----- pop-out mirror -----
    def pop_out(self):
        if self.popwin is not None:
            try:
                self.popwin.lift()
                return
            except Exception:
                self.popwin = None
                self.pop_canvas = None
        self.popwin = tk.Toplevel(self.root)
        self.popwin.title("Preview — Pop Out")
        self.popwin.geometry("960x720")
        self.popwin.minsize(640, 480)
        wrap = ttk.Frame(self.popwin, padding=6)
        wrap.pack(fill=tk.BOTH, expand=True)
        self.pop_canvas = tk.Canvas(wrap, bg="#303030", highlightthickness=0)
        self.pop_canvas.pack(fill=tk.BOTH, expand=True)
        # Bind same mouse gestures for panning/zoom
        self.pop_canvas.bind("<MouseWheel>", self._on_wheel)
        self.pop_canvas.bind("<Button-4>", self._on_wheel_linux)
        self.pop_canvas.bind("<ButtonPress-1>", lambda e: self._start_pan(self.pop_canvas, e))
        self.pop_canvas.bind("<B1-Motion>", lambda e: self._do_pan(self.pop_canvas, e))

        def on_close():
            self.popwin.destroy()
            self.popwin = None
            self.pop_canvas = None
            self.pop_tk_image = None
        self.popwin.protocol("WM_DELETE_WINDOW", on_close)

        # initial draw
        self._render_all()


# ---------- main ----------
def main():
    root = tk.Tk()
    FileViewerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
