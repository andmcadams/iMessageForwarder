import tkinter as tk
import time
import api
import threading
from datetime import datetime, timedelta

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

    def _bound_to_mousewheel(self, event):
        self.canvas.bind_all('<MouseWheel>', self._on_mousewheel_windows)
        self.canvas.bind_all('<Button-4>', lambda event: self._on_mousewheel_linux(-1, event))
        self.canvas.bind_all('<Button-5>', lambda event: self._on_mousewheel_linux(1, event))

    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind_all('<MouseWheel>')
        self.canvas.unbind_all('<Button-4>')
        self.canvas.unbind_all('<Button-5>')

    def _on_mousewheel_windows(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _on_mousewheel_linux(self, direction, event):
        self.canvas.yview_scroll(direction, "units")


class ChatButton(tk.Frame):
    def __init__(self, parent, chat, responseFrame, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)

        self.chat = chat
        self.lastMessageId = chat.getMostRecentMessage().attr['ROWID']

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
        msgTime = datetime.fromtimestamp(timeStamp + 978307200, tz=datetime.now().astimezone().tzinfo)
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



class ChatFrame(VerticalScrolledFrame):
    def __init__(self, parent, minHeight, minWidth, *args, **kw):
        VerticalScrolledFrame.__init__(self, parent, minHeight, minWidth, *args, **kw)
        self.chatButtons = {}

    def addChat(self, chat, responseFrame):
        btn = ChatButton(self.interior, chat, responseFrame, bg='orange')
        btn.pack(fill=tk.X, side=tk.TOP, pady=1)
        self.chatButtons[chat.chatId] = btn
        self._configure_scrollbars()        

# The part of the right half where messages are displayed
class MessageFrame(VerticalScrolledFrame):
    def __init__(self, parent, minHeight, minWidth, *args, **kw):
        VerticalScrolledFrame.__init__(self, parent, minHeight, minWidth, *args, **kw)
        self.canvas.bind('<Configure>', self._configure_messages_canvas)
        self.messageBubbles = {}

    def changeChat(self, chat):
        for widget in self.interior.winfo_children():
            widget.destroy()
        self.messageBubbles = {}
        self.addMessages(chat)    

    def addMessages(self, chat):
        chat._loadMessages()
        messageDict = chat.getMessages()

        # For each message in messageDict
        # Update the message bubble if it exists
        # Add a new one if it does not exist
        for messageId in messageDict.keys():
            if not messageId in self.messageBubbles:
                msg = MessageBubble(self.interior, messageDict[messageId], padx=0, pady=5, width=200, fg='white', bg='blue', font="Dosis")
                if messageDict[messageId].attr['is_from_me']:
                    msg.pack(anchor=tk.E, expand=tk.FALSE)
                else:
                    msg.pack(anchor=tk.W, expand=tk.FALSE)
                self.messageBubbles[messageId] = msg
                # Maybe make it do this after all messages are added, set a flag or something
                self._configure_message_scrollbars()
            else:
                self.messageBubbles[messageId].update()

    def _configure_message_scrollbars(self):
        self.canvas.yview_moveto(0)       
        self._configure_scrollbars()
        self.interior.update()
        self.canvas.xview_moveto(0)
        self.canvas.yview_moveto(self.interior.winfo_reqheight())

    def _configure_messages_canvas(self, event):
        (_, bottom) = self.vscrollbar.get()
        self._configure_canvas(event)
        self.canvas.yview_moveto(bottom)

class MessageBubble(tk.Message):

    def __init__(self, parent, message, *args, **kw):
        tk.Message.__init__(self, parent, *args, **kw)
        
        # Store a pointer to message object, so when this object is updated
        # we can just call self.update()
        self.message = message
        self.update()

    def update(self):
        self.configure(text=self.message.attr['text'])

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

    def activateButton(self, event):
        if not self.text.compare("end-1c", "==", "1.0"):
            self.sendButton.configure(state='normal')
        else:
            self.sendButton.configure(state='disabled')

    def sendMessage(self, chat):
        chat.sendMessage(self.text.get('1.0', 'end-1c'))
        self.text.delete('1.0', 'end')

    def updateSendButton(self, chat):
        self.sendButton.configure(command= lambda chat=chat: self.sendMessage(chat))

# The entire right half of the app
class ResponseFrame(tk.Frame):
    def __init__(self, parent, minWidth, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)
        # This will eventually contain a RecipientFrame, MessageFrame, and a SendFrame
        self.messageFrame = MessageFrame(self, 0, minWidth)
        self.messageFrame.grid(row=1, column=0, sticky='nsew')

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.recipientFrame = RecipientFrame(self)
        self.recipientFrame.grid(row=0, column=0, sticky='ew')

        self.sendFrame = SendFrame(self)
        self.sendFrame.grid(row=2, column=0, sticky='ew')

        # Hold a dummy chat with an invalid id initially
        self.currentChat = api.DummyChat(-1)

    def changeChat(self, chat):
        if chat.chatId != self.currentChat.chatId:
            self.currentChat = chat
            self.currentChat.lastAccess = 0
            self.messageFrame.changeChat(chat)
            self.recipientFrame.addRecipients(chat)
            self.sendFrame.updateSendButton(chat)



def updateFrames(chatFrame, responseFrame):
    chatIds = api._getChatsToUpdate(0)
    for chatIdTuple in chatIds:
        chatId = chatIdTuple[0]
        if chatId == responseFrame.currentChat.chatId:
            responseFrame.messageFrame.addMessages(responseFrame.currentChat)
        # If there's a change in the number of messages in this chat
        # push the chat to the top
        if chatId in chatFrame.chatButtons:
            oldMessageId = chatFrame.chatButtons[chatId].lastMessageId
            chatFrame.chatButtons[chatId].chat._loadMostRecentMessage()
            mostRecent = chatFrame.chatButtons[chatId].chat.getMostRecentMessage()
            if oldMessageId != mostRecent.attr['ROWID']:
                # Push this chat to the top
                for rowid in chatFrame.chatButtons:
                    chatFrame.chatButtons[rowid].pack_forget()
                chatFrame.chatButtons[chatId].update()
                chatFrame.chatButtons[chatId].pack(fill=tk.X, side=tk.TOP, pady=1)
                for rowid in chatFrame.chatButtons:
                    if rowid != chatId:
                        chatFrame.chatButtons[rowid].pack(fill=tk.X, side=tk.TOP, pady=1)
        else:
            chat = api._loadChat(chatId)
            chatFrame.addChat(chat)


        # 
    threading.Timer(1, lambda chatFrame=chatFrame, responseFrame=responseFrame: updateFrames(chatFrame, responseFrame)).start()

root = tk.Tk()
root.title("Scrollable Frame Demo")
root.configure(background="gray99")
minWidthChatFrame = 270
minWidthResponseFrame = int(4*minWidthChatFrame/3)
root.minsize(minWidthChatFrame+minWidthResponseFrame, 100)
chatFrame = ChatFrame(root, 0, minWidthChatFrame)
chatFrame.grid(row=0, column=0, sticky='nsew')
responseFrame = ResponseFrame(root, minWidthResponseFrame)
responseFrame.grid(row=0, column=1, sticky='nsew')
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)
chats = api._loadChats()


for i, chat in enumerate(chats):
    chatFrame.addChat(chat, responseFrame)

updateFrames(chatFrame, responseFrame)


root.mainloop()