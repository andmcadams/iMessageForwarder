import tkinter as tk
from tkinter import ttk
import os
import threading

from PIL import Image, ImageTk
from verticalscrolledframe import VerticalScrolledFrame
from constants import LINUX, MACOS

# The part of the right half where messages are displayed
class MessageFrame(VerticalScrolledFrame):
    def __init__(self, parent, minHeight, minWidth, *args, **kw):
        VerticalScrolledFrame.__init__(self, parent, minHeight, minWidth, *args, **kw)
        
        self.messageBubbles = {}
        self.canvas.bind('<Configure>', self._configure_messages_canvas)
        self.lock = threading.Lock()
        self.canvas.configure(yscrollcommand=self.checkScroll)
        # Arbitrary initial limit
        self.messageLimit = 20
        # This almost certainly introduces more race conditions
        self.addedMessages = False
        self.scrollLock = threading.Lock()


    # This probably has some nasty race conditions.
    # This also has unfortunate recursion issues that should be fixed
    def checkScroll(self, x, y):
        self.vscrollbar.set(x, y)
        (top, bottom) = self.vscrollbar.get()
        if top < 0.05 and self.addedMessages == True:
            self.addedMessages = False
            self.messageLimit += 20
            oldHeight = self.interior.winfo_height()
            for widget in self.interior.winfo_children():
                widget.destroy()
            self.messageBubbles = {}
            hitLimit = self.addMessages(self.master.currentChat)
            self._configure_message_scrollbars()
            self.addedMessages = not hitLimit
            newHeight = self.interior.winfo_reqheight()

            self.canvas.yview_moveto((top*oldHeight+(newHeight-oldHeight))/newHeight)


    # To change chats (ie display messages of a new chat)
    # we need to delete all the MessageBubbles of the old chat
    # and then add the messages of the new chat.
    #
    # This could probably be changed so that there are frames for each chat
    # and when a chat is opened, that frame is lifted. That should help
    # avoid stutter by buffering.
    # However, this probably needs to follow restricting chats to their first x messages
    # without scrolling up to avoid consuming too much memory.
    def changeChat(self, chat):
        self.addedMessages = False
        for widget in self.interior.winfo_children():
            widget.destroy()
        self.messageBubbles = {}
        # Reset the message limit before opening a new chat
        self.messageLimit = 15
        hitLimit = self.addMessages(chat)
        self._configure_message_scrollbars()
        self.addedMessages = not hitLimit
        (top, bottom) = self.vscrollbar.get()
        self.checkScroll(top, bottom)
        self.canvas.yview_moveto(self.interior.winfo_reqheight())
   

    # Add the chat's messages to the MessageFrame as MessageBubbles
    # A lock is required here since both changing the chat and the constant frame updates can add messages
    # This can result in two copies of certain messages appearing.

    def addMessages(self, chat):
        self.lock.acquire()
        if chat.chatId == self.master.currentChat.chatId:
            chat._loadMessages()
            messageDict = chat.getMessages()

            # For each message in messageDict
            # Update the message bubble if it exists
            # Add a new one if it does not exist
            subList = list(messageDict.keys())[-self.messageLimit:]
            for i in range(len(subList)):
                messageId = subList[i]
                if not messageId in self.messageBubbles:
                    allowedTypes = ['public.jpeg', 'public.png', 'public.gif', 'com.compuserve.gif']
                    if messageDict[messageId].attachment != None and messageDict[messageId].attachment.attr['uti'] in allowedTypes:
                        msg = ImageMessageBubble(self.interior, messageId, messageDict[messageId])
                    else:
                        msg = TextMessageBubble(self.interior, messageId, messageDict[messageId], i)
                    if messageDict[messageId].attr['is_from_me']:
                        msg.pack(anchor=tk.E, expand=tk.FALSE)
                    else:
                        msg.pack(anchor=tk.W, expand=tk.FALSE)
                    self.messageBubbles[messageId] = msg
                else:
                    self.messageBubbles[messageId].update()
            self.lock.release()
            if self.messageLimit > len(list(messageDict.keys())):
                return True
            return False
        else:
            self.lock.release()
            return None


    # This function fixes the scrollbar for the message frame
    # VSF _configure_scrollbars just adds or removes them based on how much stuff is displayed.
    # This function first moves the scrollbars to the top, so if changing to a chat with fewer
    # messages, the messages are in view (winfo_reqheight() won't decrease without this change).
    # The interior is updated to get the new winfo_reqheight set.
    # Scrollbars are then moved to the bottom of the canvas so that the most recent messages are showing.
    def _configure_message_scrollbars(self):
        # self.canvas.yview_moveto(0)       
        self._configure_scrollbars()
        self.interior.update()
        # self.canvas.yview_moveto(self.interior.winfo_reqheight())

    # When the window changes size, this keeps the scrollbar's bottom location
    # locked in place so the most recent messages stay in view.
    def _configure_messages_canvas(self, event):
        (top, bottom) = self.vscrollbar.get()
        for messageBubble in self.messageBubbles:
            self.messageBubbles[messageBubble].resize(event)
        self._configure_canvas(event)
        if bottom == 1.0:
            self.canvas.yview_moveto(bottom)
        else:
            self.vscrollbar.set(top, bottom)

class MessageMenu(tk.Menu):

    def __init__(self, parent, *args, **kw):
        tk.Menu.__init__(self, parent, tearoff=0, *args, **kw)

    def sendReaction(self, messageId, reactionValue):
        responseFrame = self.master.master.master.master.master
        #responseFrame.currentChat.sendReaction(messageId, reactionValue)

class MessageBubble(tk.Frame):

    def __init__(self, parent, messageId, message, *args, **kw):
        tk.Frame.__init__(self, parent, padx=4, pady=4, *args, **kw)

        self.messageInterior = ttk.Frame(self, padding=6)
        self.reactions = {}
        # Store a pointer to message object, so when this object is updated
        # we can just call self.update()
        self.messageId = messageId
        self.message = message

    # self.body MUST be assigned before calling this method
    def initBody(self):
        # On right click, open the menu at the location of the mouse
        if LINUX:
            self.messageInterior.bind("<Button-3>", lambda event: self.onRightClick(event))
            self.body.bind("<Button-3>", lambda event: self.onRightClick(event))
        elif MACOS:
            self.messageInterior.bind("<Button-2>", lambda event: self.onRightClick(event))
            self.body.bind("<Button-2>", lambda event: self.onRightClick(event))
        self.body.grid(row=1)
        self.messageInterior.grid(row=1)
        self.update()

    def onRightClick(self, event):
        messageMenu = MessageMenu(self)
        react = lambda reactionValue: lambda messageId=self.messageId: messageMenu.sendReaction(messageId, reactionValue)
        messageMenu.add_command(label="Love", command=react(2000))
        messageMenu.add_command(label="Like", command=react(2001))
        messageMenu.add_command(label="Dislike", command=react(2002))
        messageMenu.add_command(label="Laugh", command=react(2003))
        messageMenu.add_command(label="Emphasize", command=react(2004))
        messageMenu.add_command(label="Question", command=react(2005))
        messageMenu.tk_popup(event.x_root, event.y_root)

    def update(self):
        if self.message.attr['text'] != None:
            self.body.configure(text=self.message.attr['text'])
        for r in self.message.reactions:
            if self.message.reactions[r].attr['associated_message_type'] == 2000:
                if not r in self.reactions:
                    self.reactions[r] = ReactionBubble(self)
                    self.reactions[r].grid(row=0)
                    self.body.configure(bg='red')
            elif self.message.reactions[r].attr['associated_message_type'] == 3000:
                self.body.configure(bg='purple')

    def resize(self, event):
        pass
        #print("resizing text message bubble")

class ReactionBubble(tk.Label):
    def __init__(self, parent, *args, **kw):
        tk.Label.__init__(self, parent, *args, **kw)
        self.original = Image.open('loveReact.png')
        self.original.image = ImageTk.PhotoImage(self.original)
        self.configure(image=self.original.image)

class TextMessageBubble(MessageBubble):
    def __init__(self, parent, messageId, message, index, *args, **kw):
        MessageBubble.__init__(self, parent, messageId, message, *args, **kw)
        maxWidth = 3*self.master.master.winfo_width()//5
        # Could make color a gradient depending on index later but it will add a lot of
        # dumb code.
        self.messageInterior.configure(style="RoundedFrame")
        self.body = tk.Message(self.messageInterior, padx=0, pady=3, bg='#01cdfe', width=maxWidth, font="Dosis")
        self.initBody()

    def resize(self, event):
        self.body.configure(width=3*event.width//5)

class ImageMessageBubble(MessageBubble):
    def __init__(self, parent, messageId, message, *args, **kw):
        MessageBubble.__init__(self, parent, messageId, message, *args, **kw)
        self.messageInterior.columnconfigure(0,weight=1)
        self.messageInterior.rowconfigure(0,weight=1)
        self.display = tk.Canvas(self.messageInterior, bd=0, highlightthickness=0, bg='green')
        self.display.grid(row=0, sticky='nsew')
        self.body = tk.Label(self.display)
        self.body.original = Image.open(os.path.expanduser(message.attachment.attr['filename']))
        newSize = self.getNewSize(self.body.original, self.master.master.winfo_width(), self.master.master.winfo_height())
        self.body.image = ImageTk.PhotoImage(self.body.original.resize(newSize, Image.ANTIALIAS))
        self.body.configure(image=self.body.image)
        self.body.grid(row=0, sticky='nsew')
        self.display.configure(width=newSize[0], height=newSize[1])
        self.initBody()


    def getNewSize(self, im, winWidth, winHeight):
        maxWidth = 3*winWidth//4
        maxHeight = 4*winHeight//5

        resized = im
        size = (im.width, im.height)

        if im.height > maxHeight or im.width > maxWidth:
            h = int(im.height*(maxWidth/im.width))
            if h > maxHeight:
                w = int(im.width*(maxHeight/im.height))
                size = (w, maxHeight)
            else:
                size = (maxWidth, h)
        return size


    def resize(self, event):
        newSize = self.getNewSize(self.body.original, event.width, event.height)
        resized = self.body.original.resize(newSize, Image.ANTIALIAS)

        self.body.image = ImageTk.PhotoImage(resized)
        self.body.configure(image=self.body.image)
        self.display.configure(width=newSize[0], height=newSize[1])