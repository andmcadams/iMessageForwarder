# The entire right half of the app
import tkinter as tk
from messageframe import MessageFrame
from recipientframe import RecipientFrame
from sendframe import SendFrame


class ResponseFrame(tk.Frame):
    def __init__(self, parent, minWidth, api, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)

        self.mp = api.HttpMessagePasser()
        self.messageFrame = MessageFrame(self, 0, minWidth,
                                         self.mp, api.MessageDatabase)
        self.messageFrame.grid(row=1, column=0, sticky='nsew', pady=(1, 0))

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.recipientFrame = RecipientFrame(self)
        self.recipientFrame.grid(row=0, column=0, sticky='ew')

        self.sendFrame = SendFrame(self, self.mp)
        self.sendFrame.grid(row=2, column=0, sticky='ew')

        # Hold a dummy chat with an invalid id initially
        self.currentChat = api.DummyChat(-1)
        self.api = api

        self.configure(bg='black')

    def changeChat(self, chat):
        if chat.chatId != self.currentChat.chatId:
            self.currentChat = chat
            self.currentChat.lastAccess = 0
            self.recipientFrame.clearWindow()
            self.recipientFrame.addRecipients(chat)
            self.messageFrame.changeChat(chat)
            self.sendFrame.updateSendButton(self.mp, chat)

    def isCurrentChat(self, chatToCompare):
        if chatToCompare.chatId == self.currentChat.chatId:
            return True
        return False
