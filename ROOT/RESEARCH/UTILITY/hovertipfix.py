from tkinter import Label, Toplevel, LEFT, SOLID, N, E, S, W

class Hovertip:
    "A tooltip that pops up when a mouse hovers over an anchor widget."
    def __init__(self, anchor_widget, text, hover_delay=1000):
        """Create a text tooltip with a mouse hover delay.

        anchor_widget: the widget next to which the tooltip will be shown
        hover_delay: time to delay before showing the tooltip, in milliseconds
        """
        self.anchor_widget = anchor_widget
        self.text = text
        self.hover_delay = hover_delay
        self.tipwindow = None
        self.id = None
        self.anchor_widget.bind("<Enter>", self.enter)
        self.anchor_widget.bind("<Leave>", self.leave)

    def showcontents(self):
        "Create the tooltip window and display the text."
        if self.tipwindow or not self.text:
            return
        
        # Calculate the position of the tooltip
        x = self.anchor_widget.winfo_rootx() + 25
        y = self.anchor_widget.winfo_rooty() + self.anchor_widget.winfo_height() + 25

        self.tipwindow = Toplevel(self.anchor_widget)
        self.tipwindow.wm_overrideredirect(True)
        self.tipwindow.wm_geometry(f"+{x}+{y}")
        
        label = Label(self.tipwindow, text=self.text, justify=LEFT,
                      foreground="black", background="#ffffe0", relief=SOLID, borderwidth=1)
        label.pack()

    def enter(self, event=None):
        "Show the tooltip after a delay."
        self.id = self.anchor_widget.after(self.hover_delay, self.showcontents)

    def leave(self, event=None):
        "Hide the tooltip and cancel the show request."
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None
        if self.id:
            self.anchor_widget.after_cancel(self.id)
            self.id = None
