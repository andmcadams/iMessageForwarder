import tkinter as tk

class RecipientFrame(tk.Frame):
    def __init__(self, parent, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)
        self.label = tk.Label(self, text='', anchor='nw', justify=tk.LEFT, width=1, height=1)
        self.label.grid(row=0, column=0, sticky='ew')

        self.details = tk.Label(self, text='', anchor='e', justify=tk.LEFT)
        self.details.grid(row=0, column=1, sticky='se')

        self.columnconfigure(0, weight=1)

    def addRecipients(self, chat):
        # Fix resizing of label,
        # limit number of lines. Not hard to do if I hardcode the font size (17) to adjust height.
        # Seems inelegant, will return later.
        recipString = ', '.join(chat.recipientList)
        self.label.configure(text=recipString, wraplength=int(0.66*self.winfo_width()))
        self.details.configure(text='Details')