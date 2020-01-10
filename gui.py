import tkinter as tk
import time
import api
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

class ChatFrame(VerticalScrolledFrame):
    def __init__(self, parent, minHeight, minWidth, *args, **kw):
        VerticalScrolledFrame.__init__(self, parent, minHeight, minWidth, *args, **kw)

    def addChat(self, chat, responseFrame):
        btn = tk.Button(self.interior, height=1, width=20, relief=tk.FLAT, 
            bg="gray99", fg="purple3",
            font="Dosis", text=chat.getName(),
            command=lambda chat=chat: responseFrame.changeChat(chat))
        btn.pack(padx=0, pady=0, side=tk.TOP)
        self._configure_scrollbars()

# The part of the right half where messages are displayed
class MessageFrame(VerticalScrolledFrame):
    def __init__(self, parent, minHeight, minWidth, *args, **kw):
        VerticalScrolledFrame.__init__(self, parent, minHeight, minWidth, *args, **kw)
        self.canvas.bind('<Configure>', self._configure_messages_canvas)

    def addMessages(self, chat):
        for widget in self.interior.winfo_children():
            widget.destroy()
        chat._loadMessages()
        messageDict = chat.getMessages()
        for message in messageDict.values():
            msg = MessageBubble(self.interior, message.messageId, padx=0, pady=5, width=200, fg='white', bg='blue', text=message.text, font="Dosis")
            if message.isFromMe:
                msg.pack(anchor=tk.E, expand=tk.FALSE)
            else:
                msg.pack(anchor=tk.W, expand=tk.FALSE)

        self._configure_message_scrollbars()

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

    def __init__(self, parent, messageId, *args, **kw):
        tk.Message.__init__(self, parent, *args, **kw)
        self.messageId = messageId

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

class SendFrame(tk.Frame):
    def __init__(self, parent, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)
        self.text = tk.Text(self, wrap=tk.WORD, width=1, height=1)
        self.text.grid(row=0, column=0, sticky='ew')

        self.columnconfigure(0, weight=1)

        self.sendButton = tk.Button(self, relief=tk.FLAT, 
            bg="gray99", fg="purple3",
            font="Dosis", text='Send')
        self.sendButton.grid(row=0, column=1)

# The entire right half of the app
class ResponseFrame(tk.Frame):
    def __init__(self, parent, *args, **kw):
        tk.Frame.__init__(self, parent, *args, **kw)
        # This will eventually contain a RecipientFrame, MessageFrame, and a SendFrame
        self.messageFrame = MessageFrame(self, 0, 400)
        self.messageFrame.grid(row=1, column=0, sticky='nsew')

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self.recipientFrame = RecipientFrame(self)
        self.recipientFrame.grid(row=0, column=0, sticky='ew')

        self.sendFrame = SendFrame(self)
        self.sendFrame.grid(row=2, column=0, sticky='ew')

    def changeChat(self, chat):
        self.messageFrame.addMessages(chat)
        self.recipientFrame.addRecipients(chat)




root = tk.Tk()
root.title("Scrollable Frame Demo")
root.configure(background="gray99")
root.minsize(500, 100)
chatFrame = ChatFrame(root, 0, 100)
chatFrame.grid(row=0, column=0, sticky='nsew')
responseFrame = ResponseFrame(root)
responseFrame.grid(row=0, column=1, sticky='nsew')
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)
chats = api._loadChats()


for i, chat in enumerate(chats):
    chatFrame.addChat(chat, responseFrame)

def openlink(i):
    print(lis[i])

root.mainloop()