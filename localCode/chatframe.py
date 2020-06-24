import tkinter as tk
import threading
from datetime import datetime, timedelta
from verticalscrolledframe import VerticalScrolledFrame


class LeftFrame(tk.Frame):
    def __init__(
            self,
            parent,
            minHeight,
            minWidth,
            responseFrame,
            api,
            *args,
            **kw):

        tk.Frame.__init__(self, parent, *args, **kw)
        self.composeButton = tk.Button(self, relief=tk.FLAT, bg="gray99",
                                       font="Dosis", text="Compose new",
                                       command=self.openNewChat)
        self.chatFrame = ChatFrame(self, minHeight, minWidth, *args, **kw)

        self.rowconfigure(1, weight=1)
        self.composeButton.grid(row=0, column=0, sticky='se')
        self.chatFrame.grid(row=1, column=0, sticky='nsew')
        self.createNewChat = api.createNewChat
        self.newChatId = -2
        self.responseFrame = responseFrame

    def openNewChat(self):
        chat = self.createNewChat(self.newChatId)
        chat.isTemporaryChat = True
        self.responseFrame.changeChat(chat)
        self.newChatId -= 1


class ChatFrame(VerticalScrolledFrame):
    def __init__(self, parent, minHeight, minWidth, *args, **kw):
        VerticalScrolledFrame.__init__(self, parent, minHeight, minWidth,
                                       *args, **kw)
        self.chatButtons = []
        self.chats = {}
        self.lock = threading.Lock()

    def addChat(self, chat, responseFrame):
        # btn.pack(fill=tk.X, side=tk.TOP, pady=1)
        if not self.isLoaded(chat):
            btn = ChatButton(self.interior, chat, responseFrame, bg='orange')
            self.chatButtons.append(btn)
            self.chats[chat.rowid] = chat
            # self._configure_scrollbars()

    def isLoaded(self, chat):
        for chatButton in self.chatButtons:
            if chat.rowid == chatButton.chat.rowid:
                return True
        return False

    def packChatButtons(self):
        for chatButton in self.chatButtons:
            chatButton.pack_forget()
            chatButton.isVisible = False
        for chatButton in self.chatButtons:
            chatButton.pack(fill=tk.X, side=tk.TOP, pady=1)
            chatButton.isVisible = True
        self._configure_scrollbars()


class ChatButton(tk.Frame):
    def __init__(self, parent, chat, responseFrame, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)

        self.chat = chat
        self.responseFrame = responseFrame
        self.lastMessageId = chat.getMostRecentMessage().rowid
        self.lastMessageTimeValue = self.chat.getMostRecentMessage().date
        self.isVisible = False

        self.picture = tk.Label(self, height=1, width=1, text='picture')
        self.number = tk.Label(self, height=1, width=1, anchor='nw',
                               justify='left', font=("helvetica", 10),
                               wraplength=0)
        self.lastMessage = tk.Label(self, height=2, width=1, anchor='nw',
                                    justify='left', font=("helvetica", 10),
                                    wraplength=200)
        self.lastMessageTime = tk.Label(self, height=1, width=1, anchor='se',
                                        justify='right', font=("helvetica", 8))
        # Populate the above Label widgets
        self.update()

        # For debugging purposes, recolor the backgrounds of each label
        self.picture.configure(bg='red')
        self.number.configure(bg='blue')
        self.lastMessage.configure(bg='green')
        self.lastMessageTime.configure(bg='yellow')
        # This can be removed at any time.

        self.picture.grid(row=0, column=0, rowspan=2, sticky='nsew')
        self.number.grid(row=0, column=1, sticky='nsew')
        self.lastMessage.grid(row=1, column=1, columnspan=2, sticky='nsew')
        self.lastMessageTime.grid(row=0, column=2, sticky='nsew')

        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=5)
        self.columnconfigure(2, weight=2)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        # Clicking on any part of the chat button will open up the chat.
        def onClickLambda(chat):
            return lambda event, chat=chat: responseFrame.changeChat(chat)
        self.bind('<Button-1>', onClickLambda(chat))
        self.picture.bind('<Button-1>', onClickLambda(chat))
        self.number.bind('<Button-1>', onClickLambda(chat))
        self.lastMessage.bind('<Button-1>', onClickLambda(chat))
        self.lastMessageTime.bind('<Button-1>', onClickLambda(chat))

    # Use lstrip to remove any leading newlines, which could cause some issues.
    # Use rstrip to remove awkward space between text and ellipsis
    def truncate(self, string, length):
        if string:
            string = string.lstrip()
            if len(string) > length:
                return (string[:length - 3].rstrip() + '...')
            else:
                return string
        return ''

    def getTimeText(self, timeStamp):
        currentTime = datetime.now(tz=datetime.now().astimezone().tzinfo)
        msgTime = datetime.fromtimestamp(timeStamp,
                                         tz=datetime.now().astimezone().tzinfo)
        if currentTime.date() == msgTime.date():
            timeText = msgTime.strftime('%I:%M %p')
        elif currentTime.date() - timedelta(days=1) == msgTime.date():
            timeText = 'Yesterday'
        else:
            timeText = msgTime.strftime('%m/%d/%Y')
        return timeText

    def update(self):
        self.lastMessageId = self.chat.getMostRecentMessage().rowid

        name = self.truncate(self.chat.getName(), 20)
        text = self.truncate(self.chat.getMostRecentMessage().text, 50)
        # TODO 4: Need to grab the type of message and set the text to that.
        # Perhaps this should be implemented on message load.
        if text == '￼':
            text = 'Attachment: 1 Image'
        timeText = self.getTimeText(self.chat.getMostRecentMessage().date)

        self.number.configure(text=name)
        self.lastMessage.configure(text=text)
        self.lastMessageTime.configure(text=timeText)
        tempLastMessageTimeValue = self.lastMessageTimeValue
        lastMsg = self.chat.getMostRecentMessage()
        self.lastMessageTimeValue = lastMsg.date
        if (tempLastMessageTimeValue != self.lastMessageTimeValue and
                lastMsg.attr['is_from_me'] == 0 and
                self.responseFrame.isCurrentChat(self.chat) is False):
            return True
        return False
