import tkinter as tk


"""
The textbox inside of the send frame. This textbox sends out a
<<TextModified>> event whenever the user types inside of the box.
"""


class ResponsiveText(tk.Text):

    def __init__(self, parent, *args, **kw):
        tk.Text.__init__(self, parent, *args, **kw)

        self._orig = self._w + '_orig'
        self.tk.call('rename', self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

    def _proxy(self, command, *args):
        cmd = (self._orig, command) + args
        result = self.tk.call(cmd)

        if command in ('insert', 'delete', 'replace'):
            self.event_generate("<<TextModified>>")

        return result


"""
The send frame is the lower portion of the response frame. It contains a
ResponsiveText textbox for typing in a message, and a button that is active
only when there is text in the textbox and a connection to the remote machine.
"""


class SendFrame(tk.Frame):
    def __init__(self, parent, mp, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)
        self.mp = mp
        self.text = ResponsiveText(self, wrap=tk.WORD, width=1, height=1)
        self.text.grid(row=0, column=0, sticky='ew')
        self.text.bind("<<TextModified>>", self.activateButton)
        self.columnconfigure(0, weight=1)

        self.sendButton = tk.Button(self, relief=tk.FLAT,
                                    bg="gray99", fg="purple3", font="Dosis",
                                    text='Send', state='disabled')
        self.sendButton.grid(row=0, column=1)
        self.isConnected = False
        self.hasText = False
        self.consecutiveMissedPings = 0

    # Sets the status of isConnected and updates the send button accordingly.
    # consecutiveMissedPings counted may not be thread safe. This is a fairly
    # small issue that may need to be addressed in the future.
    def setIsConnected(self, isConnected):
        if isConnected:
            self.consecutiveMissedPings = 0
            self.isConnected = True
        else:
            self.consecutiveMissedPings += 1
            if self.consecutiveMissedPings > 3:
                self.isConnected = False

        if self.isConnected:
            self.sendButton.configure(text='Send')
        else:
            self.sendButton.configure(text='No connection')
        self.updateButton()

    # Sets the status of hasText and updates the send button accordingly.
    def activateButton(self, event):
        if not self.text.compare("end-1c", "==", "1.0"):
            self.hasText = True
        else:
            self.hasText = False
        self.updateButton()

    # Turns the send button "on" and "off".
    def updateButton(self):
        if self.isConnected and self.hasText and self._hasRecipients():
            self.sendButton.configure(state='normal')
        else:
            self.sendButton.configure(state='disabled')

    def _hasRecipients(self):
        return self.master.currentChat.recipientList != []

    def sendMessage(self, mp, chat):
        recipientString = (str(chat.recipientList) if chat.isTemporaryChat is
                           True else '')
        chat.sendMessage(mp, self.text.get('1.0', 'end-1c'), recipientString)
        self.text.delete('1.0', 'end')
        if chat.isTemporaryChat:
            if self.master.recipientFrame.addRecipientButton:
                self.master.recipientFrame.addRecipientButton.destroy()
            self.master.recipientFrame.clearWindow()

    # Changes the function called when clicking the send button so it is
    # passed the current chat.
    def updateSendButton(self, mp, chat):
        self.sendButton.configure(command=(lambda chat=chat, mp=mp:
                                           self.sendMessage(mp, chat)))
