import tkinter as tk

class VerticalScrolledFrame(tk.Frame):
    """A pure Tkinter scrollable frame that actually works!

    * Use the 'interior' attribute to place widgets inside the scrollable frame
    * Construct and pack/place/grid normally
    * This frame only allows vertical scrolling
    """
    def __init__(self, parent, minHeight, minWidth, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)            
        # create a canvas object and a vertical scrollbar for scrolling it
        self.vscrollbar = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.vscrollbar.grid(row=0, column=1, sticky='ns')
        self.canvas = tk.Canvas(self, bd=0, highlightthickness=0,
                        yscrollcommand=self.vscrollbar.set)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.vscrollbar.config(command=self.canvas.yview)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # reset the view
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(0)

        # create a frame inside the canvas which will be scrolled with it
        self.interior = interior = tk.Frame(self.canvas)
        self.interior_id = self.canvas.create_window(0, 0, window=self.interior,
                                           anchor=tk.NW)

        self.bind('<Enter>', self._bound_to_mousewheel)
        self.bind('<Leave>', self._unbound_to_mousewheel)

        # track changes to the canvas and frame width and sync them,
        # also updating the scrollbar
        def _configure_interior(event):
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

            # update the scrollbars to match the size of the inner frame
            size = (max(minWidth, self.interior.winfo_reqwidth()), max(minHeight, self.interior.winfo_reqheight()))
            self.canvas.config(scrollregion="0 0 %s %s" % size)
            if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                self.canvas.config(width=max(minWidth, self.interior.winfo_reqwidth()))

        interior.bind('<Configure>', _configure_interior)


        self.canvas.bind('<Configure>', self._configure_canvas)

    def _configure_canvas(self, event):
        if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
            # update the inner frame's width to fill the canvas
            self.canvas.itemconfigure(self.interior_id, width=self.canvas.winfo_width())
        # Remove or add scrollbars depending on whether or not they're necessary
        self._configure_scrollbars()

    # If the scrollable area is smaller than the window size, get rid of the
    # scroll bars. Keep space while the scrollbars are gone though.
    def _configure_scrollbars(self):
        self.interior.update()
        if self.canvas.winfo_height() > self.interior.winfo_reqheight():
            self.scrollbarwidth = self.vscrollbar.winfo_width()
            self.vscrollbar.grid_forget()
            self.canvas.grid_configure(padx=(0,self.scrollbarwidth))
        else:
            self.vscrollbar.grid(row=0, column=1, sticky='ns')
            self.canvas.grid_configure(padx=(0,0))
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


    def _bound_to_mousewheel(self, event):
        self.canvas.bind_all('<MouseWheel>', self._on_mousewheel_windows)
        self.canvas.bind_all('<Button-4>', lambda event: self._on_mousewheel_linux(-1, event))
        self.canvas.bind_all('<Button-5>', lambda event: self._on_mousewheel_linux(1, event))

    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind_all('<MouseWheel>')
        self.canvas.unbind_all('<Button-4>')
        self.canvas.unbind_all('<Button-5>')

    def _on_mousewheel_windows(self, event):
        if self.canvas.winfo_height() < self.interior.winfo_reqheight():
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_mousewheel_linux(self, direction, event):
        if self.canvas.winfo_height() < self.interior.winfo_reqheight():
            self.canvas.yview_scroll(direction, "units")
