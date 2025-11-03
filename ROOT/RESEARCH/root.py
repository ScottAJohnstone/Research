
#. Research V2:	ROOT 
#. Handle the organization and implementation of Title/Land Record documents and files.
#. Runs Rename.py, Research.py, FileView.py in tabular model.


import datetime
import os
import sys
import json
import re
import subprocess
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from PIL.Image import Resampling
import utility.helper as hlp
import webbrowser


try:
    import fitz  # PyMuPDF for PDF rendering
except Exception:
    fitz = None
    


#/                                                                                                               #/
#/                                                                                                               #/

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
        self.root.title("RESEARCH LOGGER")
        self.root.geometry("1480x940")
        self.root.minsize(1200, 780)
        self.root.configure()

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
        self.mode = None               # 'image' or 'text' for previewer

        # image/pdf render state
        self.base_image = None         # type: Image.Image | None
        self.tk_image = None           # type: ImageTk.PhotoImage | None
        self.scale = 1.0
        self.min_scale = 0.1
        self.max_scale = 8.0
        self.auto_fit = True
        self._center_next_render = True

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

            "default_open_dir": "/Users/sjohnstone/Python/RESEARCHV2/TEST",
            "default_session_path": "/Users/sjohnstone/Python/RESEARCHV2/usr",
            "presets": {},
            "prev_job_id": "",
        }

        # ensure recent lists exist in config
        self.config.setdefault("recent_job_ids", [])
        self.config.setdefault("recent_clients", [])
        self.config.setdefault("recent_cities", [])
        self.config.setdefault("recent_addr1", [])


        # rename preview state
        self.rename_preview = {}

        # UI
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

        # set initial sashes
        self.root.after(60, self._init_panes)

    # ----- UI -----
    def _build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label="Open Folder…", command=self.open_folder, accelerator="Ctrl+O")
        file_menu.add_command(label="Add Files…", command=self.add_files, accelerator="Ctrl+Shift+O")
        file_menu.add_command(label="Remove Selected Files", command=self.remove_selected, accelerator="Del")
        file_menu.add_separator()
        file_menu.add_command(label="Save Research Session", command=self.save_session, accelerator="Ctrl+S")
        file_menu.add_command(label="Save Research Session As…", command=self.save_session_as)
        file_menu.add_command(label="Load Research Session", command=self.load_session_from_file)
        file_menu.add_separator()
        file_menu.add_command(label="Clear Research Session", command=self.clear_session_ui)
        file_menu.add_separator()
        file_menu.add_command(label="Exit Program", command=self.root.quit, accelerator="Ctrl+Q")
        menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=False)
        view_menu.add_command(label="Fit to Window", command=self.fit_to_window, accelerator="F")
        view_menu.add_command(label="Fit Width", command=self.fit_width)
        view_menu.add_command(label="Fit Height", command=self.fit_height)
        view_menu.add_command(label="Zoom In", command=lambda: self._zoom(1.1), accelerator="+")
        view_menu.add_command(label="Zoom Out", command=lambda: self._zoom(1/1.1), accelerator="-")
        menubar.add_cascade(label="View", menu=view_menu)

        # NEW JOB MENU
        job_menu = tk.Menu(menubar, tearoff=False)
        job_menu.add_command(
            label="New Job Data…",
            command=self.start_prelim_job
        )
        menubar.add_cascade(label="Job", menu=job_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label="Keyboard Shortcuts", command=self.show_shortcuts, accelerator="F1")
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)


    def _build_layout(self):
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        # Outer frame that provides window padding
        outer = ttk.Frame(self.root, padding=12)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.rowconfigure(0, weight=1)
        outer.columnconfigure(0, weight=1)

        # OUTER LEFT | RIGHT (bold sash)
        self.pw = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        self.pw.grid(row=0, column=0, sticky="nsew", padx=12, pady=12)

        # LEFT
        self.left_frame = ttk.Frame(self.pw, padding=(8, 8, 6, 8))
        self.left_frame.columnconfigure(0, weight=1, minsize=560)
        self.left_frame.rowconfigure(1, weight=1)
        self.pw.add(self.left_frame, minsize=560, stretch="always")

        # Treeview
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

        for i in range(1, 9):
            self.research.insert("", "end", values=("UUID-" + str(i), "Document " + str(i), "Example note"))

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

        actions = ttk.Frame(self.left_frame)
        actions.grid(row=3, column=0, columnspan=2, sticky="ew")
        for i in range(1, 6):
            actions.columnconfigure(i, weight=1)
        ttk.Button(actions, text="Enter Record").grid(row=0, column=0, sticky="ew")
        ttk.Button(actions, text="Edit Record").grid(row=0, column=1, sticky="ew")
        ttk.Button(actions, text="Delete Record").grid(row=0, column=2, sticky="ew")
        ttk.Button(actions, text="Log to Files").grid(row=0, column=3, sticky="ew")
        ttk.Checkbutton(actions, text="Abutter").grid(row=0, column=4, sticky="e")

        # RIGHT
        self.right = ttk.Frame(self.pw, padding=(8, 8, 6, 8))
        self.right.columnconfigure(0, weight=1, minsize=560)
        self.right.rowconfigure(0, weight=1)
        self.pw.add(self.right, minsize=560, stretch="always")

        # INNER TOP | BOTTOM (bold sash)
        self.right_pw = tk.PanedWindow(self.right, orient=tk.VERTICAL, sashrelief=tk.RAISED)
        self.right_pw.grid(row=0, column=0, sticky="nsew")

        # Top pane
        self.right_top = ttk.Frame(self.right_pw)
        self.right_top.columnconfigure(0, weight=1)
        self.right_top.rowconfigure(1, weight=1)  # preview expands

        # Bottom pane
        self.right_bottom = ttk.Frame(self.right_pw)
        self.right_bottom.columnconfigure(0, weight=1)
        self.right_bottom.rowconfigure(0, weight=1)

        self.right_pw.add(self.right_top, minsize=200, stretch="always")
        self.right_pw.add(self.right_bottom, minsize=120, stretch="always")

        # ---- Top controls live in self.right_top ----
        topbar = ttk.Frame(self.right_top, padding=(0, 0))
        topbar.grid(row=0, column=0, sticky="ew", pady=(0, 2))
        for i in range(4):
            topbar.columnconfigure(i, weight=1)
        # reduce vertical padding on the buttons via padding=(hor, vert)
        ttk.Button(topbar, text="Open Folder", command=self.open_folder, padding=(6, 2)).grid(row=0, column=0, sticky="ew")
        ttk.Button(topbar, text="Add File", command=self.add_files, padding=(6, 2)).grid(row=0, column=1, sticky="ew")
        ttk.Button(topbar, text="Remove File", command=self.remove_selected, padding=(6, 2)).grid(row=0, column=2, sticky="ew")
        ttk.Button(topbar, text="Pop Out", command=self.pop_out, padding=(6, 2)).grid(row=0, column=3, sticky="ew")

        # Preview window (Canvas/Text)
        self.preview_border = ttk.Frame(self.right_top, relief="solid", borderwidth=1, height=60)
        self.preview_border.grid(row=1, column=0, sticky="nsew")
        self.preview_border.rowconfigure(0, weight=1)
        self.preview_border.columnconfigure(0, weight=1)

        self.canvas = tk.Canvas(self.preview_border, height=200)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.image_id = self.canvas.create_image(0, 0, anchor="nw")

        self.text_frame = ttk.Frame(self.preview_border, height=200)
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

        tool_frame = ttk.Frame(self.right_top, padding=(0, 0))
        tool_frame.grid(row=2, column=0, sticky="ew", pady=(6, 0), ipady=6)

        # prepare columns (4 to accommodate nav / zoom / help rows)
        for i in range(4):
            tool_frame.columnconfigure(i, weight=1)

        # Row 0: navigation (no vertical padding, fill horizontally)
        ttk.Button(tool_frame, text="Previous File", command=self.prev_file, padding=(6, 0))\
            .grid(row=0, column=0, sticky="nsew", padx=(0, 0), pady=0, columnspan=2)
        ttk.Button(tool_frame, text="Next File", command=self.next_file, padding=(6, 0))\
            .grid(row=0, column=2, sticky="nsew", padx=(0, 0), pady=0, columnspan=2)

        # Row 1: zoom / fit / help (no vertical padding, fill horizontally)
        ttk.Button(tool_frame, text="Fit W", command=self.fit_width, padding=(6, 0))\
            .grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        ttk.Button(tool_frame, text="Fit H", command=self.fit_height, padding=(6, 0))\
            .grid(row=1, column=1, sticky="nsew", padx=0, pady=0)
        ttk.Button(tool_frame, text="Zoom +", command=lambda: self._zoom(1.1), padding=(6, 0))\
            .grid(row=1, column=2, sticky="nsew", padx=0, pady=0)
        ttk.Button(tool_frame, text="Help", command=self.show_shortcuts, padding=(6, 0))\
            .grid(row=1, column=3, sticky="nsew", padx=0, pady=0)

        # Row 2: bulk rename tools (fill full width)
        row2 = ttk.Frame(tool_frame)
        row2.grid(row=2, column=0, columnspan=4, sticky="nsew", padx=0, pady=0)
        for i in range(3):
            row2.columnconfigure(i, weight=1)
        ttk.Button(row2, text="Scan", command=self.scan_bulk_renames, padding=(6, 0))\
            .grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        ttk.Button(row2, text="Clear", command=self.clear_bulk_rename_preview, padding=(6, 0))\
            .grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        ttk.Button(row2, text="Apply", command=self.apply_bulk_renames, padding=(6, 0))\
            .grid(row=0, column=2, sticky="nsew", padx=0, pady=0)

        # --- Floating pager overlay (rounded chip) ---
        self._build_pager_overlay()
        # Reposition overlay when preview resizes
        self.preview_border.bind("<Configure>", lambda e: self._position_pager())

        # ---- Bottom files list in RIGHT BOTTOM ----
        files_box = ttk.LabelFrame(self.right_bottom, text="List of files", height=5)
        files_box.grid(row=0, column=0, sticky="nsew",pady=(6,0))
        files_box.rowconfigure(0, weight=1)
        files_box.columnconfigure(0, weight=1)

        self.listbox = tk.Listbox(files_box, activestyle="dotbox")
        self.listbox.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        sb = ttk.Scrollbar(files_box, orient="vertical", command=self.listbox.yview,style="")
        sb.grid(row=0, column=1, sticky="ns", pady=6)
        self.listbox.configure(yscrollcommand=sb.set)


        # Status bar (left bar per your layout)
        self.status = ttk.Label(self.left_frame, text="Ready", anchor="w", padding=(8, 4))
        self.status.grid(row=10, column=0, sticky="ew")

    # ----- pager chip helpers -----
    def _build_pager_overlay(self):
        # Canvas that draws rounded bg + shadow, with a ttk frame on top
        self.page_overlay = tk.Canvas(self.preview_border, highlightthickness=0, bd=0)
        self.page_overlay_visible = False  # track visibility

        # Inner frame that holds the actual controls
        self.page_bar = ttk.Frame(self.page_overlay)

        # Controls
        self.page_prev_btn = ttk.Button(self.page_bar, text="◀ Prev", command=self.page_prev, width=8)
        self.page_entry_var = tk.StringVar(value="1")
        self.page_entry = ttk.Entry(self.page_bar, width=6, textvariable=self.page_entry_var)
        self.page_go_btn = ttk.Button(self.page_bar, text="Go", command=self.page_go, width=4)
        self.page_label = ttk.Label(self.page_bar, text="/ 1")
        self.page_next_btn = ttk.Button(self.page_bar, text="Next ▶", command=self.page_next, width=8)

        # Layout inside the chip
        self.page_prev_btn.grid(row=0, column=0, padx=(6, 4))
        ttk.Label(self.page_bar, text="Page").grid(row=0, column=1, padx=(0, 4))
        self.page_entry.grid(row=0, column=2, padx=(0, 4))
        self.page_label.grid(row=0, column=3, padx=(4, 8))
        self.page_go_btn.grid(row=0, column=4, padx=(0, 8))
        self.page_next_btn.grid(row=0, column=5, padx=(0, 6))

        # Put the frame onto the canvas
        self._pager_window_id = self.page_overlay.create_window(0, 0, window=self.page_bar, anchor="nw")
        #self.page_overlay.configure(bg=self._chip_bg_color())
        # Raise the widget (Canvas) itself using Tk call (avoids Canvas tag_raise signature)
        self.page_overlay.tk.call('raise', self.page_overlay._w)

    def _chip_bg_color(self):
        return "#303030"
        #return "#f5f6f8"

    def _chip_border_color(self):
        return "#303030"

    def _position_pager(self):
        """Size the chip to its contents, draw rounded bg + shadow, and place at bottom-center."""
        if not hasattr(self, "page_overlay"):
            return

        # Measure contents
        self.page_bar.update_idletasks()
        inner_w = self.page_bar.winfo_reqwidth()
        inner_h = self.page_bar.winfo_reqheight()

        pad_x = 12  # horizontal padding inside rounded bg
        pad_y = 6   # vertical padding inside rounded bg
        radius = 10 # corner radius

        w = inner_w + pad_x * 2
        h = inner_h + pad_y * 2

        # Resize canvas to fit rounded rect + content
        self.page_overlay.configure(width=w, height=h)
        self.page_overlay.delete("chip")

        # Subtle shadow
        # shadow_offset = 2
        # self._draw_rounded_rect(self.page_overlay, 1 + shadow_offset, 1 + shadow_offset,
        #                         w - 1 + shadow_offset, h - 1 + shadow_offset, radius,
        #                         fill="#e2e3e7", outline="", tags=("chip",))

        # Main rounded rectangle
        self._draw_rounded_rect(self.page_overlay, 1, 1, w - 1, h - 1, radius,
                                fill=self._chip_bg_color(), outline=self._chip_border_color(), tags=("chip",))

        # Center the inner frame within the canvas
        self.page_overlay.coords(self._pager_window_id, pad_x, pad_y)

        # Place at bottom-center of the preview, above content
        self.page_overlay.place(relx=0.5, rely=1.0, anchor="s", y=-10)
        # Raise the widget via Tk call
        self.page_overlay.tk.call('raise', self.page_overlay._w)

    def _draw_rounded_rect(self, cvs, x1, y1, x2, y2, r, **kwargs):
        """Draw a rounded rectangle on a Canvas."""
        r = max(0, min(r, int(min((x2 - x1), (y2 - y1)) / 2)))
        cvs.create_arc(x1, y1, x1 + 2 * r, y1 + 2 * r, start=90, extent=90, style="pieslice", **kwargs)
        cvs.create_arc(x2 - 2 * r, y1, x2, y1 + 2 * r, start=0, extent=90, style="pieslice", **kwargs)
        cvs.create_arc(x1, y2 - 2 * r, x1 + 2 * r, y2, start=180, extent=90, style="pieslice", **kwargs)
        cvs.create_arc(x2 - 2 * r, y2 - 2 * r, x2, y2, start=270, extent=90, style="pieslice", **kwargs)
        cvs.create_rectangle(x1 + r, y1, x2 - r, y2, **kwargs)
        cvs.create_rectangle(x1, y1 + r, x2, y2 - r, **kwargs)

    def _init_panes(self):
        # outer left|right split
        try:
            total = self.pw.winfo_width() or self.root.winfo_width() or 1
            self.pw.sash_place(0, int(total * 0.45), 1)  # ~45% left / 55% right
        except Exception:
            pass

        # inner top|bottom split
        try:
            rh = self.right_pw.winfo_height() or self.right.winfo_height() or 1
            self.right_pw.sash_place(0, 1, int(rh * 0.70))  # ~70% top / 30% bottom
        except Exception:
            pass

    # ----- events -----
    def _bind_events(self):
        self.root.bind_all("<Control-o>", lambda e: self.open_folder())
        self.root.bind_all("<Control-Shift-o>", lambda e: self.add_files())
        self.root.bind_all("<Delete>", lambda e: self.remove_selected())
        self.root.bind_all("<Control-s>", lambda e: self.save_session())
        self.root.bind_all("<Up>", lambda e: self.prev_file())
        self.root.bind_all("<Down>", lambda e: self.next_file())
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
        # Control the floating pager chip visibility
        if visible:
            if not self.page_overlay_visible:
                self.page_overlay_visible = True
                self._position_pager()
                self.page_overlay.place(relx=0.5, rely=1.0, anchor="s", y=-10)
                # Raise widget via direct Tk call (avoid Canvas tag_raise)
                self.page_overlay.tk.call('raise', self.page_overlay._w)
            else:
                self._position_pager()
        else:
            if self.page_overlay_visible:
                self.page_overlay_visible = False
                try:
                    self.page_overlay.place_forget()
                except Exception:
                    pass

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

        # reflect selection in the files list
        try:
            self.listbox.selection_clear(0, tk.END)
            self.listbox.selection_set(idx)
            self.listbox.activate(idx)
            self.listbox.see(idx)  # ensure it's visible
        except Exception:
            pass

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
        I = 0  # dummy local to avoid accidental f-strings; keeps style consistent
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
            # default zoom to Fit Width
            self.fit_width()
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
        self._render_to_canvas()
        if self.pop_canvas is not None and self.base_image is not None:
            img = self.base_image
            w = max(1, int(img.width * self.scale))
            h = max(1, int(img.height * self.scale))
            scaled = img.resize((w, h), Resampling.LANCZOS)
            self.pop_tk_image = ImageTk.PhotoImage(scaled)
            self.pop_canvas.delete("all")
            self.pop_canvas.create_image(0, 0, anchor="nw", image=self.pop_tk_image)
            self.pop_canvas.config(scrollregion=(0, 0, scaled.width, scaled.height))
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
                self.listbox.itemconfig(i, fg="white")
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
                    self.listbox.itemconfig(i, fg="white")
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
        folder = self.config.get("default_session_path")
        if folder:
            # make sure the folder exists
            try:
                os.makedirs(folder, exist_ok=True)
            except Exception:
                pass
            return os.path.join(folder,"autosave.rdata")                    #- Add Date?

        # fallback if not configured
        return os.path.join(os.path.expanduser("~"), ".fileviewer_session.research")


    def _config_path(self) -> str:
        return os.path.join(os.path.expanduser("~"), ".fileviewer_config.rdata")

    def save_session(self):
        # Save to the default session path if we have one,
        # otherwise ask user where to save
        path = self._state_path() if self.config.get("default_session_path") else None
        if not path:
            self.save_session_as()
            return
        self._write_session(path)

    def save_session_as(self):
        path = filedialog.asksaveasfilename(
            title="Save Research Session As…",
            defaultextension=".rdata",
            filetypes=[("RESEARCH", "*.rddata")]
        )
        if not path:
            return

        # remember this location for future quick-saves
        self.config["default_session_path"] = os.path.dirname(path)
        # if you have a helper like _save_config() already, call it:
        if hasattr(self, "_save_config"):
            self._save_config()

        self._write_session(path)


    def _write_session(self, path: str):
        try:
            data_file_viewer = {
                "files": self.files,
                "current_index": self.current_index,
                "current_path": self.current_path,
                "page_index": self.pdf_page_index if getattr(self, "pdf_doc", None) else self.doc_page_index,
                "current_dir": self.current_dir,
            }

            data_research = {
                "test": None
            }

            job_data = {
                "info": {
                    "job_number": "",
                    "pid": "",
                    "address": "",
                    "client": ""
                },
                "_meta": {
                    "modified": datetime.datetime.now().isoformat(timespec="seconds"),
                    "creator": "Scott"
                }
            }

            full_payload = {
                "job_data": job_data,
                "data_file_viewer": data_file_viewer,
                "data_research": data_research,
                "_meta": {
                    "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
                    "version": 1,
                }
            }

            with open(path, "w", encoding="utf-8") as f:
                json.dump(full_payload, f, indent=2)

        except Exception as e:
            messagebox.showerror("Save Session", "Could not save session:\n" + str(e))


    def load_session_from_file(self):
        # Prefer whatever is in config, but fall back to hardcoded usr folder
        start_dir = self.config.get("default_session_path")
        if not start_dir:
            start_dir = "/Users/sjohnstone/Python/RESEARCHV2/usr"

        # Make sure the directory actually exists, or ignore it
        if not os.path.isdir(start_dir):
            start_dir = os.path.expanduser("~")

        path = filedialog.askopenfilename(
            title="Load Session…",
            initialdir=start_dir,
            filetypes=[("RESEARCH", "*.rdata"), ("All Files", "*.*")],
        )
        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)  # <- now valid because we fixed the trailing comma

            # --- pull the viewer block ---
            viewer = data.get("data_file_viewer", {})

            # restore file list
            files = [
                p for p in viewer.get("files", [])
                if os.path.exists(p) and (_is_supported(p) or _is_text(p))
            ]
            self.files = files

            # repopulate the listbox
            self.listbox.delete(0, tk.END)
            for p in self.files:
                self.listbox.insert(tk.END, os.path.basename(p))

            # restore directory info
            self.current_dir = viewer.get("current_dir")

            # figure out which index to open
            idx = viewer.get("current_index")
            if idx is None or not (0 <= idx < len(self.files)):
                idx = 0 if self.files else None
            if idx is not None:
                self._open_index(idx)

            # restore page index
            self.doc_page_index = int(viewer.get("page_index") or 0)
            if self.doc_page_count > 1:
                self.page_entry_var.set(str(self.doc_page_index + 1))
                self.page_go()

            # --- pull any future sections safely ---
            # e.g. your "data_research" block
            self.research_data = data.get("data_research", {})

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
                # only overwrite keys with truthy values
                for k, v in data.items():
                    if v not in (None, "", []):
                        self.config[k] = v
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



    def start_prelim_job(self):
        """
        Launch the Preliminary Job Intake dialog.
        """
        PreliminaryJobDialog(self)


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
        # Register proper close handler for the popout window
        try:
            self.popwin.protocol("WM_DELETE_WINDOW", self._on_popwin_close)
        except Exception:
            pass
        wrap = ttk.Frame(self.popwin, padding=6)
        wrap.pack(fill=tk.BOTH, expand=True)
        self.pop_canvas = tk.Canvas(wrap, bg="#303030", highlightthickness=0)
        self.pop_canvas.pack(fill=tk.BOTH, expand=True)
        self.pop_canvas.bind("<MouseWheel>", self._on_wheel)
    def _on_popwin_close(self):
        """Handle the pop-out window closing: destroy and clear references, then re-render main preview."""
        try:
            if self.popwin is not None:
                self.popwin.destroy()
        except Exception:
            pass
        self.popwin = None
        self.pop_canvas = None
        self.pop_tk_image = None

        try:
            self._render_all()
        except Exception:
            pass
        # If the user clicks 'No', the window remains open


        self.popwin.protocol("WM_DELETE_WINDOW", on_close(self))
        self._render_all()


class PreliminaryJobDialog:
    """
    Compact and aligned job intake dialog.
    - Smaller window (~450x420)
    - Tight grid alignment for labels, boxes, and buttons
    - Keyboard shortcuts (Ctrl+S, Ctrl+M, Esc)
    - Autofocus on Job ID
    """

    def __init__(self, parent_app: FileViewerApp):
        import webbrowser

        self.parent = parent_app
        self.top = tk.Toplevel(parent_app.root)
        self.top.title("New Job Intake")
        self.top.transient(parent_app.root)
        self.top.grab_set()
        self.top.geometry("450x420")  # smaller window size
        self.top.resizable(False, False)

        # keyboard shortcuts
        self.top.bind("<Escape>", lambda e: self._cancel())
        self.top.bind("<Control-s>", lambda e: self._save_job_safe())
        self.top.bind("<Command-s>", lambda e: self._save_job_safe())
        self.top.bind("<Control-m>", lambda e: self._open_in_maps_safe())
        self.top.bind("<Command-m>", lambda e: self._open_in_maps_safe())

        # ensure recents exist
        for key in ("recent_job_ids", "recent_addr1", "recent_cities", "recent_clients"):
            self.parent.config.setdefault(key, [])

        # variables
        self.job_id_var = tk.StringVar()
        self.addr1_var = tk.StringVar()
        self.city_var = tk.StringVar()
        self.state_var = tk.StringVar()
        self.zip_var = tk.StringVar()
        self.client_var = tk.StringVar()

        # recents
        recent_job_ids = self.parent.config["recent_job_ids"]
        recent_addr1 = self.parent.config["recent_addr1"]
        recent_cities = self.parent.config["recent_cities"]
        recent_clients = self.parent.config["recent_clients"]

        # root frame
        main = ttk.Frame(self.top, padding=10)
        main.pack(fill="both", expand=True)
        main.columnconfigure(1, weight=1)

        row = 0

        # --- Job ID ---------------------------------------------------------
        ttk.Label(main, text="Job ID / Number:").grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
        self.job_id_cb = ttk.Combobox(main, textvariable=self.job_id_var, values=recent_job_ids, state="normal", width=32)
        self.job_id_cb.grid(row=row, column=1, sticky="ew", pady=3)
        row += 1

        # --- Client ---------------------------------------------------------
        ttk.Label(main, text="Client / Requester:").grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
        self.client_cb = ttk.Combobox(main, textvariable=self.client_var, values=recent_clients, state="normal", width=32)
        self.client_cb.grid(row=row, column=1, sticky="ew", pady=3)
        row += 1

        # --- Address --------------------------------------------------------
        ttk.Label(main, text="Address:").grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
        self.addr1_cb = ttk.Combobox(main, textvariable=self.addr1_var, values=recent_addr1, state="normal", width=32)
        self.addr1_cb.grid(row=row, column=1, sticky="ew", pady=3)
        row += 1

        # --- City -----------------------------------------------------------
        ttk.Label(main, text="City / Town:").grid(row=row, column=0, sticky="w", padx=(0, 8), pady=3)
        self.city_cb = ttk.Combobox(main, textvariable=self.city_var, values=recent_cities, state="normal", width=32)
        self.city_cb.grid(row=row, column=1, sticky="ew", pady=3)
        row += 1

        # --- State and ZIP (on same line) -----------------------------------
        subframe = ttk.Frame(main)
        subframe.grid(row=row, column=0, columnspan=2, sticky="ew", pady=3)
        subframe.columnconfigure(1, weight=1)

        ttk.Label(subframe, text="State:").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.state_cb = ttk.Combobox(subframe, width=6, textvariable=self.state_var,
                                     values=getattr(hlp, "US_STATES", []), state="readonly")
        self.state_cb.grid(row=0, column=1, sticky="w")

        ttk.Label(subframe, text="ZIP:").grid(row=0, column=2, sticky="w", padx=(16, 6))
        ttk.Entry(subframe, width=10, textvariable=self.zip_var).grid(row=0, column=3, sticky="w")
        row += 1

        # --- Notes ----------------------------------------------------------
        ttk.Label(main, text="Notes / Instructions:").grid(row=row, column=0, sticky="nw", padx=(0, 8), pady=(6, 2))
        self.notes_widget = tk.Text(main, height=4, wrap="word", width=34)
        self.notes_widget.grid(row=row, column=1, sticky="ew", pady=(6, 2))
        row += 1

        # --- Action Buttons (maps + history) --------------------------------
        action_row = ttk.Frame(main)
        action_row.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(8, 0))
        action_row.columnconfigure((0, 1, 2), weight=1)

        ttk.Button(action_row, text="Open in Maps", command=self._open_in_maps_safe).grid(row=0, column=0, padx=3)
        ttk.Button(action_row, text="Clear History", command=self._clear_recent_safe).grid(row=0, column=1, padx=3)
        row += 1

        # --- Footer (Save + Cancel) ----------------------------------------
        footer = ttk.Frame(main)
        footer.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        footer.columnconfigure((0, 1), weight=1)

        ttk.Button(footer, text="Cancel (Esc)", command=self._cancel).grid(row=0, column=0, sticky="e", padx=6)
        ttk.Button(footer, text="Save Job (Ctrl+S)", command=self._save_job_safe).grid(row=0, column=1, sticky="w", padx=6)

        # autofocus first field
        self.job_id_cb.focus_set()
        self.top.bind("<Return>", self._enter_key_handler)

    # --------------------- Behavior ---------------------------------------
    def _enter_key_handler(self, e):
        if self.top.focus_get() is self.notes_widget:
            return
        self._save_job_safe()

    def _cancel(self):
        self.top.destroy()

    # --------------------- Maps -------------------------------------------
    def _open_in_maps_safe(self):
        try:
            import webbrowser
            url = hlp.build_maps_query(
                self.addr1_var.get(), self.city_var.get(),
                self.state_var.get(), self.zip_var.get()
            )
            webbrowser.open(url)
        except Exception as e:
            messagebox.showerror("Maps Error", str(e))

    # --------------------- Clear History ----------------------------------
    def _clear_recent_safe(self):
        if not messagebox.askyesno("Clear History", "Clear all saved dropdown histories?"):
            return
        for key in ("recent_job_ids", "recent_addr1", "recent_cities", "recent_clients"):
            self.parent.config[key] = []
        try:
            self.parent._save_config()
        except Exception:
            pass
        for cb in (self.job_id_cb, self.addr1_cb, self.city_cb, self.client_cb):
            cb["values"] = []
        messagebox.showinfo("Cleared", "History cleared.")

    # --------------------- Save Logic -------------------------------------
    def _save_job_safe(self):
        try:
            self._save_job()
        except Exception as e:
            messagebox.showerror("Save Error", str(e))

    def _save_job(self):
        job_id = hlp.clean_job_id(self.job_id_var.get())
        if not job_id:
            messagebox.showerror("Missing Job ID", "Please enter a Job ID.")
            self.job_id_cb.focus_set()
            return

        record = hlp.build_job_record(
            job_id=job_id,
            addr_line1=self.addr1_var.get(),
            city=self.city_var.get(),
            state=self.state_var.get(),
            zipcode=self.zip_var.get(),
            client_name=self.client_var.get(),
            notes=self.notes_widget.get("1.0", "end").strip(),
        )
        base_dir = self.parent.config.get("default_session_path") or os.getcwd()
        path = hlp.save_job_record(record, base_dir)

        # update MRU
        self.parent.config["recent_job_ids"] = hlp.push_recent_value(self.parent.config["recent_job_ids"], job_id)
        self.parent.config["recent_addr1"] = hlp.push_recent_value(self.parent.config["recent_addr1"], self.addr1_var.get())
        self.parent.config["recent_cities"] = hlp.push_recent_value(self.parent.config["recent_cities"], self.city_var.get())
        self.parent.config["recent_clients"] = hlp.push_recent_value(self.parent.config["recent_clients"], self.client_var.get())

        try:
            self.parent._save_config()
        except Exception:
            pass

        messagebox.showinfo("Job Saved", f'Job "{job_id}" saved to:\n{path}')
        self._cancel()





# ---------- main ----------
def main():
    root = tk.Tk()
    FileViewerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
