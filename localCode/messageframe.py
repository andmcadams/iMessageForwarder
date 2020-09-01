import tkinter as tk
from tkinter import ttk
import os
import threading
import json
from datetime import datetime, timedelta

from PIL import Image, ImageTk
from verticalscrolledframe import VerticalScrolledFrame
from constants import LINUX, MACOS

dirname = os.path.dirname(__file__)


def getTimeText(timeStamp):
    currentTime = datetime.now(tz=datetime.now().astimezone().tzinfo)
    msgTime = datetime.fromtimestamp(timeStamp,
                                     tz=datetime.now().astimezone().tzinfo)
    if currentTime.date() == msgTime.date():
        timeText = msgTime.strftime('%-I:%M %p')
    elif currentTime.date() - timedelta(days=1) == msgTime.date():
        timeText = 'Yesterday, ' + msgTime.strftime('%-I:%M %p')
    else:
        timeText = msgTime.strftime('%-m/%-d/%Y at %-I:%M %p')
    return timeText


# The part of the right half where messages are displayed
class MessageFrame(VerticalScrolledFrame):

    def __init__(self, parent, minHeight, minWidth, mp, messageDatabase):
        VerticalScrolledFrame.__init__(self, parent, minHeight, minWidth)
        self.messageBubbles = {}
        self.canvas.bind('<Configure>', self._configure_messages_canvas)
        self.lock = threading.Lock()
        self.canvas.configure(yscrollcommand=self.checkScroll)
        # Arbitrary initial limit
        self.messageLimit = 15
        # This almost certainly introduces more race conditions
        self.addedMessages = False
        self.scrollLock = threading.Lock()

        self.readReceiptMessageId = None
        self.mp = mp
        self.messageDatabase = messageDatabase
        self.reactionWindow = None
        self._currentChat = None

    @property
    def currentChat(self):
        return self._currentChat

    @currentChat.setter
    def currentChat(self, chat: 'api.Chat'):
        self._currentChat = chat

    # This probably has some nasty race conditions.
    # This also has unfortunate recursion issues that should be fixed
    def checkScroll(self, x, y):
        self.vscrollbar.set(x, y)
        (top, bottom) = self.vscrollbar.get()
        if top < 0.05 and self.addedMessages is True:
            self.addedMessages = False
            self.messageLimit += 20
            oldHeight = self.interior.winfo_height()
            for widget in self.interior.winfo_children():
                widget.destroy()
            self.messageBubbles = {}
            hitLimit = self.addMessages(self.currentChat)
            self._configure_message_scrollbars()
            self.addedMessages = not hitLimit
            newHeight = self.interior.winfo_reqheight()

            newY = (top * oldHeight + (newHeight - oldHeight)) / newHeight
            self.canvas.yview_moveto(newY)

    # To change chats (ie display messages of a new chat)
    # we need to delete all the MessageBubbles of the old chat
    # and then add the messages of the new chat.
    #
    # This could probably be changed so that there are frames for each chat
    # and when a chat is opened, that frame is lifted. That should help
    # avoid stutter by buffering.
    # However, this probably needs to follow restricting chats to their first x
    # messages without scrolling up to avoid consuming too much memory.
    def changeChat(self, chat):
        self.currentChat = chat
        self.addedMessages = False
        for widget in self.interior.winfo_children():
            widget.destroy()
        self.messageBubbles = {}
        # Reset the message limit before opening a new chat
        self.messageLimit = 15
        hitLimit = self.addMessages(chat)

        # Pack a temp frame if there are no children.
        # Otherwise, the scrollbars will not disappear as there is no
        # geometry manager in control.
        if not self.interior.winfo_children():
            tempFrame = tk.Frame(self.interior)
            tempFrame.pack()
        self._configure_message_scrollbars()
        self.addedMessages = not hitLimit
        (top, bottom) = self.vscrollbar.get()
        self.checkScroll(top, bottom)
        self.canvas.yview_moveto(self.interior.winfo_reqheight())

        self._destroyReactionWindow()

    def needSenderLabel(self, chat, message, prevMessage):
        """Return whether or not a sender label needs to be added.

        Parameters:
        chat : Chat
            The open chat.
        message : Message
            The message that the sender label would appear before.
        prevMessage : Message
            The message that the sender label would appear after.

        Returns:
            True if a sender label needs to be appended.
            False if a sender label does not need to be appended.
        """

        if chat.isGroup:
            if not message.isFromMe:
                if (prevMessage is None or
                        prevMessage.handleId != message.handleId):
                    return True
        return False

    def needTimeLabel(self, message, previousMessage):
        """Return whether or not a time label needs to be added.

        Parameters:
        message : Message
            The message that the time label would appear before.
        prevMessage : Message
            The message that the time label would appear after.

        Returns:
            True if a time label needs to be appended.
            False if a sender label does not need to be appended.
        """
        if message.isTemporary:
            return False
        if previousMessage is None:
            return True

        tz = datetime.now().astimezone().tzinfo
        timeDiff = (datetime.fromtimestamp(message.date, tz=tz)
                    - datetime.fromtimestamp(previousMessage.date, tz=tz))
        if timeDiff > timedelta(minutes=15):
            return True

        return False

    def createTimeLabel(self, messageDate):
        timeLabel = MessageHeader(self.interior,
                                  getTimeText(messageDate))
        timeLabel.pack(fill=tk.X)
        return timeLabel

    def needReadReceipt(self, chat, message, lastFromMeId):
        """Return whether or not a read receipt needs to be added to the
        message.

        Parameters:
        chat : Chat
            The open chat.
        message : Message
            The message that the read receipt would be added to.
        lastFromMeId : int
            The rowid of the last message sent from the user in the chat.

        Returns:
            True if a read receipt needs to be added to the message.
            False if a read receipt does not need to be added to the message.
        """
        # Need to add a read receipt iff
        # 1) The message is from me.
        # AND one of the two following:
        #   a) The message is currently being sent (rowid < 0)
        #   b) All of the following:
        #       1) The chat is not a group chat
        #       2) The message is an iMessage
        #       3) There is no later message than this one sent by me

        if message.isFromMe and message.rowid < 0:
            return True

        if (message.isFromMe and not chat.isGroup and message.isiMessage
                and message.rowid == lastFromMeId):
            return True
        return False

    def removeOldReadReceipt(self):
        readReceiptId = self.readReceiptMessageId
        if (readReceiptId is not None and
                readReceiptId in self.messageBubbles):
            self.messageBubbles[readReceiptId][-1].removeReadReceipt()

    def addMessage(self, chat, i, message, prevMessage, lastFromMeId):

        addLabel = self.needSenderLabel(chat, message, prevMessage)

        messageParts = []
        if (self.needTimeLabel(message, prevMessage)):
            timeLabel = self.createTimeLabel(message.date)
            messageParts.append(timeLabel)

        addReceipt = self.needReadReceipt(chat, message, lastFromMeId)
        if addReceipt:
            self.removeOldReadReceipt()
            self.readReceiptMessageId = message.rowid

        allowedTypes = ['public.jpeg', 'public.png', 'public.gif',
                        'com.compuserve.gif']
        # If the message is for a group rename
        if message.item_type == 2:
            newName = message.group_title
            text = '{} named the conversation "{}".'.format(message.handleName,
                                                            newName)
            nameChange = MessageHeader(self.interior, text)
            nameChange.pack(fill=tk.X)
            messageParts.append(nameChange)

        for i in range(len(message.messageParts)):
            messagePart = message.messageParts[i]
            lastPart = (i == len(message.messageParts) - 1)
            firstPart = i == 0
            if messagePart.kind == 'image':
                if messagePart.attachment.uti in allowedTypes:
                    bubble = ImageMessageBubble(self.interior, message.rowid,
                                                chat, i,
                                                addLabel and firstPart,
                                                addReceipt and lastPart,
                                                messagePart)
                    messageParts.append(bubble)
            else:
                bubble = TextMessageBubble(self.interior, message.rowid, chat,
                                           i, addLabel and firstPart,
                                           addReceipt and lastPart,
                                           messagePart)
                messageParts.append(bubble)

        for msg in messageParts:
            if message.isFromMe:
                msg.pack(anchor=tk.E, expand=tk.FALSE)
            else:
                msg.pack(anchor=tk.W, expand=tk.FALSE)
        # If this message is replacing a temporary message,
        # get rid of that old message.
        if (message.removedTempId < 0 and message.removedTempId in
                self.messageBubbles):
            for bubble in self.messageBubbles[message.removedTempId]:
                bubble.destroy()
            del self.messageBubbles[message.removedTempId]
        self.messageBubbles[message.rowid] = messageParts

    # Add the chat's messages to the MessageFrame as MessageBubbles
    # A lock is required here since both changing the chat and the constant
    # frame updates can add messages.
    # This can result in two copies of certain messages appearing.
    def addMessages(self, chat):
        self.lock.acquire()
        if chat.chatId != self.currentChat.chatId:
            self.lock.release()
            return None

        db = self.messageDatabase()
        messageList, lastAccessTime = db.getMessagesForChat(
            chat.chatId, chat.lastAccessTime)
        chat.addMessages(messageList, lastAccessTime)

        messageDict = chat.getMessages()

        # For each message in messageDict
        # Update the message bubble if it exists
        # Add a new one if it does not exist
        subList = self.getMessagesUpToLimit(messageDict, self.messageLimit)

        lastFromMeId = -1
        for i in reversed(subList):
            if messageDict[i].isFromMe:
                lastFromMeId = messageDict[i].rowid
                break

        # val is grabbed and then assigned to top/bottom since this gives a
        # 4-tuple in testing.
        val = self.vscrollbar.get()
        (top, bottom) = (val[0], val[1])

        for i in range(len(subList)):
            messageId = subList[i]
            if messageId not in self.messageBubbles:
                prevMessage = (messageDict[subList[i - 1]] if (i - 1) in
                               range(len(subList)) else None)
                self.addMessage(chat, i, messageDict[messageId], prevMessage,
                                lastFromMeId)
            else:
                for bubble in self.messageBubbles[messageId]:
                    bubble.update()
        self.lock.release()
        if bottom >= 0.99:
            self.canvas.update()
            self.canvas.yview_moveto(self.interior.winfo_reqheight())
        if self.messageLimit > len(list(messageDict.keys())):
            return True
        return False

    # Iterate backwards through the list and chop off when there are more
    # message parts than messageLimit.
    def getMessagesUpToLimit(self, messageDict, messageLimit):
        subList = list(messageDict.keys())[-self.messageLimit:]
        messagePartCount = 0
        for i in range(len(subList) - 1, -1, -1):
            messagePartCount += len(messageDict[subList[i]].messageParts)
            if messagePartCount > messageLimit:
                return subList[min(len(subList), (i + 1)):]
        return subList

    # This function fixes the scrollbar for the message frame
    # VSF _configure_scrollbars just adds or removes them based on how
    # much stuff is displayed.
    # This function first moves the scrollbars to the top, so if changing to a
    # chat with fewer messages, the messages are in view (winfo_reqheight()
    # won't decrease without this change).
    # The interior is updated to get the new winfo_reqheight set.
    # Scrollbars are then moved to the bottom of the canvas so that the
    # most recent messages are showing.

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
            for bubble in self.messageBubbles[messageBubble]:
                bubble.resize(event)
        self._configure_canvas(event)
        if bottom == 1.0:
            self.canvas.yview_moveto(bottom)
        else:
            self.vscrollbar.set(top, bottom)

    def _showReactionWindow(self, message, messagePart):
        # Create a new window with a text box and submit button
        if messagePart.reactions == {}:
            return

        # In order to guarantee uniqueness of the bubble, I either need to make
        # reactionWindow store the startLocation of message parts or give each
        # bubble its own unique id. Note that message ids/guids can't be used
        # since message parts of the same message all share these.
        if (self.reactionWindow is not None
                and (self.reactionWindow.messageId != message.rowid
                     or (self.reactionWindow.startLocation !=
                         messagePart.startLocation))):
            self._destroyReactionWindow()

        if not self.reactionWindow or not self.reactionWindow.winfo_exists():
            self.reactionWindow = tk.Toplevel(self, bg='black')
            self.reactionWindow.messageId = message.rowid
            self.reactionWindow.startLocation = messagePart.startLocation
            self.reactionWindow.grid_propagate(True)
            reactionsByType = self._reactionsByTypeDict(messagePart.reactions)
            i = 0
            for reactionType in reactionsByType:
                if reactionsByType[reactionType] != []:
                    reactionLabel = tk.Label(self.reactionWindow)
                    reactionLabel.configure(text=reactionType)
                    handleLabel = tk.Label(self.reactionWindow)
                    handleText = ', '.join(reactionsByType[reactionType])
                    handleLabel.configure(text=handleText)
                    reactionLabel.grid(
                        row=0, column=i, pady=(
                            1, 1), padx=(
                            1, 1), sticky='ew')
                    handleLabel.grid(row=1, column=i, padx=(1, 1), sticky='ew')
                    self.reactionWindow.columnconfigure(index=i, weight=1)
                    i += 1
        else:
            self.reactionWindow.lift()
            self.reactionWindow.focus_force()

    def _destroyReactionWindow(self):
        if self.reactionWindow is not None:
            self.reactionWindow.destroy()
            self.reactionWindow.messageId = 0

    def _reactionsByTypeDict(self, reactionsDict):
        reactionsBySender = {0: [], 1: [], 2: [], 3: [], 4: [], 5: []}
        for handle in reactionsDict:
            for reactionType in reactionsDict[handle]:
                reactionsBySender[reactionType].append(
                    reactionsDict[handle][reactionType].handleName)

        reactionsBySender['Loved'] = reactionsBySender.pop(0)
        reactionsBySender['Liked'] = reactionsBySender.pop(1)
        reactionsBySender['Disliked'] = reactionsBySender.pop(2)
        reactionsBySender['Laughed'] = reactionsBySender.pop(3)
        reactionsBySender['Emphasized'] = reactionsBySender.pop(4)
        reactionsBySender['Questioned'] = reactionsBySender.pop(5)
        return reactionsBySender


class MessageMenu(tk.Menu):

    def __init__(self, parent, *args, **kw):
        tk.Menu.__init__(self, parent, tearoff=0, *args, **kw)

    def sendReaction(self, messageId, reactionValue):
        respFrame = self.master.master.master.master.master
        respFrame.currentChat.sendReaction(respFrame.mp, messageId,
                                           reactionValue)


class MessageHeader(tk.Frame):

    def __init__(self, parent, text, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)

        # Store a pointer to message object, so when this object is updated
        # we can just call self.update()
        self.label = tk.Message(self, width=parent.winfo_width(), text=text,
                                justify=tk.CENTER, font=('helvetica', 8))

        self.label.pack(fill=tk.X, expand=tk.TRUE)

    def update(self):
        pass

    def resize(self, event):
        self.label.configure(width=event.width)


class MessageBubble(tk.Frame):

    def __init__(self, parent, messageId, chat, addLabel, addReadReceipt,
                 messagePart, *args, **kw):
        tk.Frame.__init__(self, parent, padx=4, pady=4, *args, **kw)

        self.senderLabel = None
        if addLabel is True:
            senderName = chat.getMessages()[messageId].handleName
            self.senderLabel = tk.Label(self, height=1, text=senderName,
                                        font=('helvetica', 8))
        self.messageInterior = ttk.Frame(self, padding=6)
        self.reactions = {}
        # Store a pointer to message object, so when this object is updated
        # we can just call self.update()
        self.messageId = messageId
        self.chat = chat
        self.reactionCount = 0
        self.messagePart = messagePart

        self.readReceipt = None
        if addReadReceipt:
            self.readReceipt = tk.Label(self, text='')

    # self.body MUST be assigned before calling this method
    def initBody(self):
        # On right click, open the menu at the location of the mouse
        if LINUX:
            self.messageInterior.bind("<Button-3>", self.onRightClick)
            self.body.bind("<Button-3>", self.onRightClick)
        elif MACOS:
            self.messageInterior.bind("<Button-2>", self.onRightClick)
            self.body.bind("<Button-2>", self.onRightClick)
        self.body.grid(row=1)

        stickyValue = ('e' if self.chat.getMessages()[self.messageId].isFromMe
                       else 'w')
        self.messageInterior.grid(row=2, sticky=stickyValue)
        if self.senderLabel:
            self.senderLabel.grid(row=0, sticky='w')

        if self.readReceipt:
            self.readReceipt.grid(row=3, sticky='e')
        self.update()

    def onRightClick(self, event):

        def sendReaction(mesMenu, mesId):
            return lambda rValue: lambda: mesMenu.sendReaction(mesId,
                                                               rValue)
        messageMenu = MessageMenu(self)
        message = self.chat.getMessages()[self.messageId]

        react = sendReaction(messageMenu, self.messageId)

        messageMenu.add_command(label=self.messageId)
        if self.reactions != {} and self.chat.isGroup:
            messageMenu.add_command(
                label='Reactions',
                command=lambda: (self.master
                                 .master.master
                                 ._showReactionWindow(message,
                                                      self.messagePart)))
        messageMenu.add_command(label=getTimeText(message.date))
        messageMenu.add_command(label=message.guid)
        messageMenu.add_command(label="Love", command=react(2000))
        messageMenu.add_command(label="Like", command=react(2001))
        messageMenu.add_command(label="Dislike", command=react(2002))
        messageMenu.add_command(label="Laugh", command=react(2003))
        messageMenu.add_command(label="Emphasize", command=react(2004))
        messageMenu.add_command(label="Question", command=react(2005))
        messageMenu.tk_popup(event.x_root, event.y_root)

    def updateReaction(self, message, reaction, reactionBubble):
        if reaction.isAddition:
            if reactionBubble is None:
                reactionBubble = ReactionBubble(self, reaction.reactionType)
                if message.isFromMe:
                    reactionBubble.grid(row=1, padx=5 * self.reactionCount,
                                        sticky='w')
                else:
                    reactionBubble.grid(row=1, padx=5 * self.reactionCount,
                                        sticky='e')
                self.reactionCount += 1 if self.reactionCount < 10 else 0
                # self.body.configure(bg='red')
        elif not reaction.isAddition:
            if reactionBubble is not None:
                reactionBubble.destroy()
                del reactionBubble
                # self.body.configure(bg='green')

    def update(self):
        # Text probably won't change but this is nice for initially populating.
        message = self.chat.getMessages()[self.messageId]
        if message.text is not None:
            self.body.configure(text=self.messagePart.getText())

        if self.readReceipt:
            if message.dateRead != 0:
                timeText = getTimeText(message.dateRead)
                self.readReceipt.configure(text='Read at {}'.format(timeText))
            elif message.isDelivered:
                self.readReceipt.configure(text='Delivered')
            else:
                self.readReceipt.configure(text='Sending...')
        # Handle reactions
        self.reactionCount = 0
        for handle in self.messagePart.reactions:
            if handle not in self.reactions:
                self.reactions[handle] = {}
            for reactionId in self.messagePart.reactions[handle]:
                reaction = self.messagePart.reactions[handle][reactionId]
                reactionBubble = (self.reactions[handle][reactionId] if
                                  reactionId in self.reactions[handle] else
                                  None)
                self.updateReaction(message, reaction, reactionBubble)

    def removeReadReceipt(self):
        # Don't delete read receipts off of temporary messages
        if self.readReceipt is not None and self.messageId >= 0:
            self.readReceipt.grid_forget()
            self.readReceipt = None

    def resize(self, event):
        pass


class ReactionBubbleBadMessageTypeException(Exception):
    pass


class ReactionBubble(tk.Label):
    def __init__(self, parent, associatedMessageType, *args, **kw):
        tk.Label.__init__(self, parent, *args, **kw)

        imageDictionary = {
            2000: 'loveReact.png',
            2001: 'thumbsupReact.png',
            2002: 'thumbsdownReact.png',
            2003: 'hahaReact.png',
            2004: 'emphasizeReact.png',
            2005: 'questionReact.png'
        }
        if associatedMessageType not in imageDictionary:
            raise ReactionBubbleBadMessageTypeException

        # This is very silly and could probably be done using a Flyweight
        # pattern. Should look into how much memory this would save.
        self.original = Image.open(
            '{}/{}'.format(dirname, imageDictionary[associatedMessageType]))
        self.original.image = ImageTk.PhotoImage(self.original)
        self.configure(image=self.original.image)


class TextMessageBubble(MessageBubble):
    def __init__(self, parent, messageId, chat, index, addLabel,
                 addReadReceipt, messagePart, *args, **kw):
        MessageBubble.__init__(self, parent, messageId, chat, addLabel,
                               addReadReceipt, messagePart, *args, **kw)
        maxWidth = 3 * self.master.master.winfo_width() // 5
        # Could make color a gradient depending on index later but it will
        # add a lot of dumb code.
        self.messageInterior.configure(style="RoundedFrame")
        if messageId >= 0:
            self.body = tk.Message(self.messageInterior, padx=0, pady=3,
                                   bg='#01cdfe', width=maxWidth, font="helvetica")
        else:
            self.body = tk.Message(self.messageInterior, padx=0, pady=3,
                                   bg='#01ffff', width=maxWidth, font="helvetica")
        self.initBody()

    def resize(self, event):
        self.body.configure(width=3 * event.width // 5)


class ImageMessageBubble(MessageBubble):
    def __init__(self, parent, messageId, chat, index, addLabel,
                 addReadReceipt, messagePart, *args, **kw):
        MessageBubble.__init__(self, parent, messageId, chat,
                               addLabel, addReadReceipt, messagePart,
                               *args, **kw)
        self.messageInterior.columnconfigure(0, weight=1)
        self.messageInterior.rowconfigure(0, weight=1)
        self.display = tk.Canvas(self.messageInterior, bd=0,
                                 highlightthickness=0)
        self.display.grid(row=0, sticky='nsew')
        self.body = tk.Label(self.display)
        try:
            self.body.original = Image.open(os.path
                                            .expanduser(messagePart
                                                        .attachment.filename))
            newSize = self.getNewSize(self.body.original,
                                      self.master.master.winfo_width(),
                                      self.master.master.winfo_height())
            self.body.image = ImageTk.PhotoImage(self.body.original
                                                 .resize(newSize,
                                                         Image.ANTIALIAS))
            self.body.configure(image=self.body.image)
            self.display.configure(width=newSize[0], height=newSize[1])

            self.body.grid(row=0, sticky='nsew')
            self.initBody()

        except FileNotFoundError as e:
            print(e)
            self.body.original = None
            self.body.configure(text='Image not found')

    def getNewSize(self, im, winWidth, winHeight):
        maxWidth = 3 * winWidth // 4
        maxHeight = 4 * winHeight // 5

        resized = im
        size = (im.width, im.height)

        if im.height > maxHeight or im.width > maxWidth:
            h = int(im.height * (maxWidth / im.width))
            if h > maxHeight:
                w = int(im.width * (maxHeight / im.height))
                size = (w, maxHeight)
            else:
                size = (maxWidth, h)
        return size

    def resize(self, event):
        if self.body.original:
            newSize = self.getNewSize(self.body.original,
                                      event.width, event.height)
            resized = self.body.original.resize(newSize, Image.ANTIALIAS)

            self.body.image = ImageTk.PhotoImage(resized)
            self.body.configure(image=self.body.image)
            self.display.configure(width=newSize[0], height=newSize[1])
        else:
            self.body.configure(width=3 * event.width // 5)
