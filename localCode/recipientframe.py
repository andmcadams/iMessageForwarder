import tkinter as tk
import threading


class RecipientFrame(tk.Frame):
    def __init__(self, parent, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)

        self.lock = threading.Lock()

        self.labelFrame = None

        self.andMore = None

        self.details = None

        self.addRecipientButton = None

        self.newWindow = None

        self.columnconfigure(0, weight=1)

    def addRecipients(self, chat):
        self.lock.acquire()
        if self.master.isCurrentChat(chat):
            if self.labelFrame:
                self.labelFrame.destroy()
            if self.andMore:
                self.andMore.destroy()
            if self.details:
                self.details.destroy()
            if self.addRecipientButton:
                self.addRecipientButton.destroy()

            if chat.isTemporaryChat is False:
                self.andMore = tk.Label(self, text='', anchor='e', justify=tk.LEFT)
                self.andMore.grid(row=0, column=1, padx=(5, 0), sticky='se')
                self.details = tk.Label(self, text='', anchor='e', justify=tk.LEFT)
                self.details.grid(row=0, column=2, sticky='se')

                self.labelFrame = RecipientLabelFrame(self, chat)
                self.labelFrame.grid(row=0, column=0, sticky='nsew')
                self.labelFrame.addRecipients(chat)
            else:
                self.labelFrame = RecipientLabelFrame(self, chat)
                self.labelFrame.grid(row=0, column=0, sticky='nsew')
                self.addRecipientButton = tk.Button(self, text='Add recipient',
                        command=lambda: self.addNewRecipient(chat))
                self.addRecipientButton.grid(row=0, column=3)
                self.andMore = tk.Label(self, text='', anchor='e', justify=tk.LEFT)
                self.andMore.grid(row=0, column=1, padx=(5, 0), sticky='se')
                self.details = tk.Label(self, text='', anchor='e', justify=tk.LEFT)
                self.details.grid(row=0, column=2, sticky='se')
        self.lock.release()

    def addNewRecipient(self, chat):
        # Create a new window with a text box and submit button
        if not self.newWindow or not self.newWindow.winfo_exists():
            self.newWindow = tk.Toplevel(self)
            t = tk.Text(self.newWindow, height=1, width=15)
            t.grid(row=0, column=0, sticky='ew')
            b = tk.Button(self.newWindow, text='Submit')
            b.grid(row=1, column=0, sticky='nsew')
            self.newWindow.columnconfigure(0, weight=1)
            self.newWindow.rowconfigure(1, weight=1)
            # On submit, add value to recipient list 
            b.configure(command=lambda: self.onSubmit(chat,
                t.get("1.0",'end-1c').lstrip().rstrip()))
        else:
            self.newWindow.lift()
            self.newWindow.focus_force()

    def onSubmit(self, chat, recipient):
        if chat.addRecipient(recipient):
            self.labelFrame.addRecipients(chat)

    def clearWindow(self):
        if self.newWindow:
            self.newWindow.destroy()

class RecipientLabelFrame(tk.Frame):

    def __init__(self, parent, chat, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)
        self.topFrame = RecipientLabelSubframe(self)
        self.topFrame.pack(expand=True, fill=tk.BOTH)
        self.topFrame.columnconfigure(0, weight=1)
        self.bottomFrame = RecipientLabelSubframe(self)
        self.bottomFrame.pack(expand=True, fill=tk.BOTH, side=tk.BOTTOM)
        self.topSize = 0
        self.bottomSize = 0
        self.hiddenLabels = []

    def onClick(self, event, chat):
        menu = tk.Menu(self, tearoff=0)
        # Apple's version adds one to the number of members to
        # include yourself.
        # This seems a bit counterintuitive honestly, so I don't do that here.
        if chat.isGroup():
            if chat.isiMessage():
                displayName = chat.attr['display_name']
                menu.add_command(label='Name: {}'.format(displayName if
                                 displayName else 'Add group name...'))
            menu.add_command(label='{} members'
                             .format(len(chat.recipientList)))
        # Single chats lack the message about the number of members.
        else:
            pass
        for r in chat.recipientList:
            menu.add_command(label=r)
        if chat.isGroup() and chat.isiMessage():
            menu.add_command(label='Add Member')
        menu.add_checkbutton(label='Do Not Disturb')
        if chat.isGroup() and chat.isiMessage():
            menu.add_command(label='Leave this Conversation')
        elif not chat.isGroup() and chat.isiMessage():
            menu.add_checkbutton(label='Send Read Receipts')
        menu.tk_popup(event.x_root, event.y_root)

    def addRecipients(self, chat):
        if self.topFrame:
            self.topFrame.destroy()
        if self.bottomFrame:
            self.bottomFrame.destroy()
        self.topFrame = RecipientLabelSubframe(self)
        self.topFrame.pack(expand=True, fill=tk.BOTH)
        self.topFrame.columnconfigure(0, weight=1)
        self.bottomFrame = RecipientLabelSubframe(self)
        self.bottomFrame.pack(expand=True, fill=tk.BOTH, side=tk.BOTTOM)
        self.topSize = 0
        self.bottomSize = 0
        self.hiddenLabels = []

        self.bind('<Configure>',
                  lambda event: self.resizeRecipients(event, chat))

        # These should do different things, but just let them do
        # the same thing for now.
        self.master.andMore.bind("<Button-1>",
                                 lambda event: self.onClick(event, chat))
        self.master.details.bind("<Button-1>",
                                 lambda event: self.onClick(event, chat))

        recipLabels = {
                'top': [],
                'bottom': []
        }

        self.master.details.configure(text='Details')
        # self.master.details.update()
        if chat.attr['display_name']:
            r = RecipientLabel(self, chat.attr['display_name'])
            r.configure(padx=5, anchor='nw', justify=tk.LEFT, text=r.fullText)
            r.resizeLabel(True, self.winfo_reqwidth())
            self.topFrame.addLabel(r)
            self.topFrame.configure(height=r.winfo_reqheight())
            return
        andMoreFlag = False
        for i in range(len(chat.recipientList)):
            c = chat.recipientList[i]
            isLast = i == len(chat.recipientList) - 1
            text = c + ',' if i != len(chat.recipientList) - 1 else c + ' '
            r = RecipientLabel(self, c)
            r.configure(padx=5, anchor='nw', justify=tk.LEFT, text=text)
            w = r.winfo_reqwidth()
            if self.topSize + w <= self.winfo_reqwidth():
                self.topSize += w
                recipLabels['top'].append(r)
            elif self.topSize == 0:
                r.resizeLabel(isLast, self.winfo_reqwidth())
                self.topSize += w
                recipLabels['top'].append(r)
            elif self.bottomSize + w <= self.winfo_reqwidth():
                self.bottomSize += w
                recipLabels['bottom'].append(r)
            elif self.bottomSize == 0:
                r.resizeLabel(isLast, self.winfo_reqwidth())
                self.bottomSize += w
                recipLabels['bottom'].append(r)
            else:
                # This is going to mess up the previously calculated values,
                # resulting in another run.
                self.hiddenLabels.append(r)
                andMoreFlag = True

        if andMoreFlag:
            andMoreText = 'and {} more...'.format(len(chat.recipientList)-i)
            self.master.andMore.configure(text=andMoreText)
            # self.master.andMore.update()

        for r in recipLabels['top']:
            self.topFrame.addLabel(r)
            self.topFrame.configure(height=r.winfo_reqheight())
        for r in recipLabels['bottom']:
            self.bottomFrame.addLabel(r)
            self.bottomFrame.configure(height=r.winfo_reqheight())

    def moveFromBottomToTop(self, width):
        bottomChildren = self.bottomFrame.labels
        for b in bottomChildren:
            # If the top frame can hold b, move it up there.
            if self.topSize + b.winfo_reqwidth() <= width:
                self.topSize += b.winfo_reqwidth()
                self.bottomSize -= b.winfo_reqwidth()
                self.bottomFrame.removeLabel(b)
                self.topFrame.addLabel(b)
            # If we can't move the next one up, don't move any
            # following ones up.
            else:
                break

    def moveFromMissingToBottom(self, chat, width):
        for i in range(len(self.hiddenLabels)):
            c = self.hiddenLabels[i]
            w = c.winfo_reqwidth()
            if self.bottomSize + w <= width:
                self.bottomSize += w
                self.bottomFrame.addLabel(c)
            else:
                self.hiddenLabels = self.hiddenLabels[i:]
                return
        self.hiddenLabels = []

    def canAllFit(self, width):
        topSize = self.topSize
        bottomSize = self.bottomSize
        for label in self.bottomFrame.labels:
            if topSize + label.winfo_reqwidth() <= width:
                topSize += label.winfo_reqwidth()
                bottomSize -= label.winfo_reqwidth()
        for label in self.hiddenLabels:
            if bottomSize + label.winfo_reqwidth() <= width:
                bottomSize += label.winfo_reqwidth()
            else:
                return False
        return True

    # Move around recipient labels in order to meet sizing requirements.
    # Keep in mind that both the "and more" and "Details" labels should be
    # updated at this point.
    def resizeRecipients(self, event, chat):
        self.master.lock.acquire()

        if chat.attr['display_name']:
            if self.topFrame.labels:
                self.topFrame.labels[0].resizeLabel(True, event.width)
            self.master.lock.release()
            return

        if self.topSize == 0 and self.bottomSize == 0:
            self.master.lock.release()
            return

        if len(self.topFrame.labels) == 1:
            isLast = not (self.bottomFrame.labels or self.hiddenLabels)
            self.topFrame.labels[0].resizeLabel(isLast, event.width)
        if len(self.bottomFrame.labels) == 1:
            isLast = not self.hiddenLabels
            self.bottomFrame.labels[0].resizeLabel(isLast, event.width)
        # Try to add labels to the bottom frame, then the top frame
        self.moveFromBottomToTop(event.width)
        self.moveFromMissingToBottom(chat, event.width)

        # Try to remove labels from the top frame, then the bottom frame
        topChildren = reversed(self.topFrame.labels)
        if len(self.topFrame.labels) != 1 and event.width < self.topSize:
            for t in topChildren:
                # If the top frame can no longer hold t, push it down.
                self.topSize -= t.winfo_reqwidth()
                self.bottomSize += t.winfo_reqwidth()
                self.topFrame.removeLabel(t)
                self.bottomFrame.addLabel(t, lift=True)
                if event.width >= self.topSize:
                    break
        bottomChildren = reversed(self.bottomFrame.labels)

        if len(self.bottomFrame.labels) != 1 and event.width < self.bottomSize:
            for b in bottomChildren:
                self.bottomSize -= b.winfo_reqwidth()
                self.hiddenLabels = [b] + self.hiddenLabels
                self.bottomFrame.removeLabel(b)
                if event.width >= self.bottomSize:
                    break

        # Should not be "Are all children displayed", but rather, "can all
        # children be displayed without the tag?"
        # Might want to do this by creating all the labels initially,
        # and just packing them as required.
        reqwidth = self.master.andMore.winfo_reqwidth()
        if not self.hiddenLabels or self.canAllFit(event.width + reqwidth):
            self.master.andMore.configure(text='')
            self.moveFromBottomToTop(event.width + reqwidth)
            self.moveFromMissingToBottom(chat, event.width + reqwidth)
        else:
            self.master.andMore.configure(text='and {} more...'
                                          .format(len(self.hiddenLabels)))

        if self.bottomSize == 0:
            self.bottomFrame.configure(height=1)
        elif self.bottomFrame.labels:
            self.bottomFrame.configure(height=self.bottomFrame
                                       .labels[0].winfo_reqheight())
        self.master.lock.release()


class RecipientLabelSubframe(tk.Frame):

    def __init__(self, parent, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)
        self.pack_propagate(0)
        self.labels = []

    def addLabel(self, label, lift=False):
        if lift:
            for c in self.labels:
                c.pack_forget()
        label.pack(in_=self, side=tk.LEFT)
        if lift:
            self.labels = [label] + self.labels
            for c in self.labels:
                c.pack(in_=self, side=tk.LEFT)
        else:
            self.labels.append(label)

    def removeLabel(self, label):
        label.pack_forget()
        self.labels.remove(label)


class RecipientLabel(tk.Label):
    def __init__(self, parent, text, *args, **kw):
        tk.Label.__init__(self, parent, *args, **kw)
        self.fullText = text

    def resizeLabel(self, isLast, maxSize):
        self.configure(text=self.fullText + (',' if isLast is False else ' '))
        if self.winfo_reqwidth() <= maxSize:
            return
        div = 2
        currentLen = len(self.fullText)//2
        while len(self.fullText)//div != 0:
            self.configure(text=self.fullText[0:currentLen] + '...'
                           + (',' if isLast is False else ' '))
            div *= 2
            if self.winfo_reqwidth() > maxSize:
                currentLen -= len(self.fullText)//div
            elif self.winfo_reqwidth() < maxSize:
                currentLen += len(self.fullText)//div
            else:
                break
