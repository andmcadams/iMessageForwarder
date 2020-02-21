import tkinter as tk
from verticalscrolledframe import VerticalScrolledFrame

# The part of the right half where messages are displayed
class MessageFrame(VerticalScrolledFrame):
    def __init__(self, parent, minHeight, minWidth, *args, **kw):
        VerticalScrolledFrame.__init__(self, parent, minHeight, minWidth, *args, **kw)
        
        self.messageBubbles = {}
        self.canvas.bind('<Configure>', self._configure_messages_canvas)

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
        for widget in self.interior.winfo_children():
            widget.destroy()
        self.messageBubbles = {}
        self.addMessages(chat)    

    # Add the chat's messages to the MessageFrame as MessageBubbles
    def addMessages(self, chat):
        chat._loadMessages()
        messageDict = chat.getMessages()

        # For each message in messageDict
        # Update the message bubble if it exists
        # Add a new one if it does not exist
        for messageId in messageDict.keys():
            if not messageId in self.messageBubbles:
                msg = MessageBubble(self.interior, messageId, messageDict[messageId], padx=0, pady=5, width=200, fg='white', bg='blue', font="Dosis")
                if messageDict[messageId].attr['is_from_me']:
                    msg.pack(anchor=tk.E, expand=tk.FALSE)
                else:
                    msg.pack(anchor=tk.W, expand=tk.FALSE)
                self.messageBubbles[messageId] = msg
                # Maybe make it do this after all messages are added, set a flag or something
                self._configure_message_scrollbars()
            else:
                self.messageBubbles[messageId].update()

    # This function fixes the scrollbar for the message frame
    # VSF _configure_scrollbars just adds or removes them based on how much stuff is displayed.
    # This function first moves the scrollbars to the top, so if changing to a chat with fewer
    # messages, the messages are in view (winfo_reqheight() won't decrease without this change).
    # The interior is updated to get the new winfo_reqheight set.
    # Scrollbars are then moved to the bottom of the canvas so that the most recent messages are showing.
    def _configure_message_scrollbars(self):
        self.canvas.yview_moveto(0)       
        self._configure_scrollbars()
        self.interior.update()
        self.canvas.yview_moveto(self.interior.winfo_reqheight())

    # When the window changes size, this keeps the scrollbar's bottom location
    # locked in place so the most recent messages stay in view.
    def _configure_messages_canvas(self, event):
        (_, bottom) = self.vscrollbar.get()
        self._configure_canvas(event)
        self.canvas.yview_moveto(bottom)

class MessageMenu(tk.Menu):

    def __init__(self, parent, *args, **kw):
        tk.Menu.__init__(self, parent, tearoff=0, *args, **kw)

    def sendReaction(self, messageId, reactionValue):
        responseFrame = self.master.master.master.master.master
        #responseFrame.currentChat.sendReaction(messageId, reactionValue)

class MessageBubble(tk.Message):

    def __init__(self, parent, messageId, message, *args, **kw):
        tk.Message.__init__(self, parent, *args, **kw)
        
        # Store a pointer to message object, so when this object is updated
        # we can just call self.update()
        self.messageId = messageId
        self.message = message
        # On right click, open the menu at the location of the mouse
        self.bind("<Button-2>", lambda event: self.onRightClick(event))

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
        self.configure(text=self.message.attr['text'])