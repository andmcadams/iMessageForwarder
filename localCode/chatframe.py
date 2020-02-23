import tkinter as tk
import threading
from datetime import datetime, timedelta
from verticalscrolledframe import VerticalScrolledFrame

class ChatFrame(VerticalScrolledFrame):
    def __init__(self, parent, minHeight, minWidth, *args, **kw):
        VerticalScrolledFrame.__init__(self, parent, minHeight, minWidth, *args, **kw)
        self.chatButtons = []
        self.lock = threading.Lock()

    def addChat(self, chat, responseFrame):
        # btn.pack(fill=tk.X, side=tk.TOP, pady=1)
        if not self.isLoaded(chat):
            btn = ChatButton(self.interior, chat, responseFrame, bg='orange')
            self.chatButtons.append(btn)
            # self._configure_scrollbars()

    def isLoaded(self, chat):
        for chatButton in self.chatButtons:
            if chat.chatId == chatButton.chat.chatId:
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
        self.lastMessageId = chat.getMostRecentMessage().attr['ROWID']
        self.isVisible = False

        self.picture = tk.Label(self, height=1, width=1, text='picture')
        self.number = tk.Label(self, height=1, width=1, anchor='nw', justify='left', font=("helvetica", 10), wraplength=0)
        self.lastMessage = tk.Label(self, height=2, width=1, anchor='nw', justify='left', font=("helvetica", 10), wraplength=200)
        self.lastMessageTime = tk.Label(self, height=1, width=1, anchor='se', justify='right', font=("helvetica", 8))
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

        # Set up bindings so that clicking on any part of the chat button will open up the chat.
        onClick = lambda event, chat=chat: responseFrame.changeChat(chat)
        self.bind('<Button-1>', onClick)
        self.picture.bind('<Button-1>', onClick)
        self.number.bind('<Button-1>', onClick)
        self.lastMessage.bind('<Button-1>', onClick)
        self.lastMessageTime.bind('<Button-1>', onClick)

    def truncate(self, string, length):
        # Use lstrip to remove any leading newlines, which could cause some issues.
        # Note that using lstrip here ONLY affects what the text looks like in the chat button.
        # Use rstrip to remove awkward space between text and ellipsis in case last char is a space
        if string:
            string = string.lstrip()
            return (string[:length-3].rstrip() + '...') if len(string) > length else string
        return ''

    def getTimeText(self, timeStamp):
        currentTime = datetime.now(tz=datetime.now().astimezone().tzinfo)
        msgTime = datetime.fromtimestamp(timeStamp, tz=datetime.now().astimezone().tzinfo)
        if currentTime.date() == msgTime.date():
            timeText = msgTime.strftime('%I:%M %p')
        elif currentTime.date() - timedelta(days=1) == msgTime.date():
            timeText = 'Yesterday'
        else:
            timeText = msgTime.strftime('%m/%d/%Y')  
        return timeText  

    def update(self):
        self.lastMessageId = self.chat.getMostRecentMessage().attr['ROWID']

        name = self.truncate(self.chat.getName(), 20)
        text = self.truncate(self.chat.getMostRecentMessage().attr['text'], 50)
        timeText = self.getTimeText(self.chat.getMostRecentMessage().attr['date'])

        self.number.configure(text=name)
        self.lastMessage.configure(text=text)
        self.lastMessageTime.configure(text=timeText)
        self.lastMessageTimeValue = self.chat.getMostRecentMessage().attr['date']
