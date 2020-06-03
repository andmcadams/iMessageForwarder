import tkinter as tk

class RecipientFrame(tk.Frame):
    def __init__(self, parent, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)

        self.labelFrame = None

        self.andMore = tk.Label(self, text='', anchor='e', justify=tk.LEFT)
        self.andMore.configure(bg='gray')
        self.andMore.grid(row=0, column=1, padx=(5, 0), sticky='se')

        self.details = tk.Label(self, text='', anchor='e', justify=tk.LEFT)
        self.details.configure(bg='red')
        self.details.grid(row=0, column=2, sticky='se')

        self.columnconfigure(0, weight=1)


    def addRecipients(self, chat):
        if self.labelFrame:
            self.labelFrame.destroy()
        self.andMore.configure(text='')
        self.details.configure(text='')
        self.labelFrame = RecipientLabelFrame(self, chat)
        self.labelFrame.grid(row=0, column=0, sticky='nsew')
        self.labelFrame.update()
        self.labelFrame.addRecipients(chat)

class RecipientLabelFrame(tk.Frame):

    def __init__(self, parent, chat, *args, **kw):
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
        self.bind('<Configure>', lambda event, chat=chat: self.resizeRecipients(chat))


    def addRecipients(self, chat):
        # Fix resizing of label,
        # limit number of lines. Not hard to do if I hardcode the font size (17) to adjust height.
        # Seems inelegant, will return later.

        recipLabels = {
                'top': [],
                'bottom': []
        }

        self.master.details.configure(text='Details')
        self.master.details.update()
        for i in range(len(chat.recipientList)):
            c = chat.recipientList[i]
            r = RecipientLabel(self)
            isLast = i == len(chat.recipientList) - 1
            text = c + ',' if i != len(chat.recipientList) - 1 else c
            r.configure(padx=5, anchor='nw', justify=tk.LEFT, text=text)
            w = r.winfo_reqwidth()
            if self.topSize + w < self.winfo_width():
                self.topSize += w
                recipLabels['top'].append(r)
            elif self.topSize == 0:
                r.resizeLabel(c, isLast, self.winfo_width())
                self.topSize += w
                recipLabels['top'].append(r)
            elif self.bottomSize + w < self.winfo_width():
                self.bottomSize += w
                recipLabels['bottom'].append(r)
            elif self.bottomSize == 0:
                r.resizeLabel(c, isLast, self.winfo_width())
                self.bottomSize += w
                recipLabels['bottom'].append(r)
            else:
                # This is going to mess up the previously calculated values, resulting in another run
                self.master.andMore.configure(text='and {} more...'.format(len(chat.recipientList)-i))
                self.master.andMore.update()
                return
        for r in recipLabels['top']:
            self.topFrame.addLabel(r.cget('text'))
            self.topFrame.configure(height=r.winfo_reqheight())
        for r in recipLabels['bottom']:
            self.bottomFrame.addLabel(r.cget('text'))
            self.bottomFrame.configure(height=r.winfo_reqheight())

    # Move around recipient labels in order to meet sizing requirements.
    # Keep in mind that both the "and more" and "Details" labels should be updated at this point.
    def resizeRecipients(self, chat):
        if self.topSize == 0 and self.bottomSize == 0:
            return
        self.topSize = 0
        self.bottomSize = 0
        for child in self.topFrame.winfo_children():
            child.destroy()
        for child in self.bottomFrame.winfo_children():
            child.destroy()
        for i in range(len(chat.recipientList)):
            c = chat.recipientList[i]
            r = RecipientLabel(self)
            isLast = i == len(chat.recipientList) - 1
            text = c + ',' if i != len(chat.recipientList) - 1 else c
            r.configure(padx=5, anchor='nw', justify=tk.LEFT, text=text)
            w = r.winfo_reqwidth()
            totalWidth = self.winfo_width()
            if self.topSize + w <= totalWidth:
                self.topFrame.addLabel(text)
                self.topFrame.configure(height=r.winfo_reqheight())
                self.topSize += w
            elif self.topSize == 0:
                r.resizeLabel(c, isLast, self.winfo_width())
                self.topFrame.addLabel(text)
                self.topFrame.configure(height=r.winfo_reqheight())
                self.topSize += w
            elif self.bottomSize + w <= totalWidth:
                self.bottomFrame.addLabel(text)
                self.bottomFrame.configure(height=r.winfo_reqheight())
                self.bottomSize += w
            elif self.bottomSize == 0:
                r.resizeLabel(c, isLast, self.winfo_width())
                self.bottomFrame.addLabel(text)
                self.bottomFrame.configure(height=r.winfo_reqheight())
                self.bottomSize += w
            else:
                # This is going to mess up the previously calculated values, resulting in another run
                self.master.andMore.configure(text='and {} more...'.format(len(chat.recipientList)-i))
                break
        if self.bottomSize == 0:
            self.bottomFrame.configure(height=1)

class RecipientLabelSubframe(tk.Frame):

    def __init__(self, parent, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)
        self.configure(bg='blue')
        self.pack_propagate(0)

    def addLabel(self, text):
        r = RecipientLabel(self)
        r.configure(padx=5, anchor='nw', justify=tk.LEFT, text=text)
        r.pack(in_=self, side=tk.LEFT)

class RecipientLabel(tk.Label):
    def __init__(self, parent, *args, **kw):
        tk.Label.__init__(self, parent, *args, **kw)

    def resizeLabel(self, text, isLast, maxSize):
        self.configure(text=text[0:len(text)//2])
