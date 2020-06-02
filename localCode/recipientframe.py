import tkinter as tk

class RecipientFrame(tk.Frame):
    def __init__(self, parent, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)

        self.labelFrame = None

        self.details = tk.Label(self, text='', anchor='e', justify=tk.LEFT)
        self.details.configure(bg='red')
        self.details.grid(row=0, column=1, sticky='se')

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, minsize=75)

    def addRecipients(self, chat):
        if self.labelFrame:
            self.labelFrame.destroy()
        self.labelFrame = RecipientLabelFrame(self)
        self.labelFrame.grid(row=0, column=0, sticky='nsew')
        self.labelFrame.update()
        self.labelFrame.addRecipients(chat)

class RecipientLabelFrame(tk.Frame):

    def __init__(self, parent, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)
        self.configure(bg='green')
        self.topFrame = RecipientLabelSubframe(self)
        self.topFrame.configure(bg='blue')
        self.topFrame.pack(expand=True, fill=tk.BOTH)
        self.topFrame.columnconfigure(0, weight=1)
        self.bottomFrame = RecipientLabelSubframe(self)
        self.bottomFrame.configure(bg='orange')
        self.bottomFrame.pack(expand=True, fill=tk.BOTH, side=tk.BOTTOM)
        self.topSize = 0
        self.bottomSize = 0


    def addRecipients(self, chat):
        # Fix resizing of label,
        # limit number of lines. Not hard to do if I hardcode the font size (17) to adjust height.
        # Seems inelegant, will return later.

        for i in range(len(chat.recipientList)):
            c = chat.recipientList[i]
            r = RecipientLabel(self)
            text = c + ',' if i != len(chat.recipientList) - 1 else c
            r.configure(padx=5, anchor='nw', justify=tk.LEFT, text=text)
            if self.topSize + r.winfo_reqwidth() < self.winfo_width():
                self.topFrame.addLabel(r)
                self.topFrame.configure(height=r.winfo_reqheight())
                self.topSize += r.winfo_reqwidth()
            else:
                self.bottomFrame.addLabel(r)
                self.bottomFrame.configure(height=r.winfo_reqheight())
                self.bottomSize += r.winfo_reqwidth()
        self.master.details.configure(text='Details')

class RecipientLabelSubframe(tk.Frame):

    def __init__(self, parent, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)
        self.configure(bg='blue')
        self.pack_propagate(0)

    def addLabel(self, recipLabel):
        recipLabel.pack(in_=self, side=tk.LEFT)

class RecipientLabel(tk.Label):
    def __init__(self, parent, *args, **kw):
        tk.Label.__init__(self, parent, *args, **kw)
