import tkinter as tk

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

class SendFrame(tk.Frame):
    def __init__(self, parent, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)
        self.text = ResponsiveText(self, wrap=tk.WORD, width=1, height=1)
        self.text.grid(row=0, column=0, sticky='ew')
        self.text.bind("<<TextModified>>", self.activateButton)
        self.columnconfigure(0, weight=1)

        self.sendButton = tk.Button(self, relief=tk.FLAT, 
            bg="gray99", fg="purple3",
            font="Dosis", text='Send', state='disabled')
        self.sendButton.grid(row=0, column=1)
        self.isConnected = False
        self.hasText = False

    def setIsConnected(self, isConnected):
        self.isConnected = isConnected
        if self.isConnected == True:
            self.sendButton.configure(text='Send')
        else:
            self.sendButton.configure(text='No connection')
        self.updateButton()

    def activateButton(self, event):
        if not self.text.compare("end-1c", "==", "1.0"):
            self.hasText = True
        else:
            self.hasText = False
        self.updateButton()

    def updateButton(self):
        if self.isConnected and self.hasText:
            self.sendButton.configure(state='normal')
        else:
            self.sendButton.configure(state='disabled')

    def sendMessage(self, chat):
        chat.sendMessage(self.text.get('1.0', 'end-1c'))
        self.text.delete('1.0', 'end')

    def updateSendButton(self, chat):
        self.sendButton.configure(command= lambda chat=chat: self.sendMessage(chat))
