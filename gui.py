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
        interior_id = self.canvas.create_window(0, 0, window=self.interior,
                                           anchor=tk.NW)



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

        def _configure_canvas(event):
            if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
                # update the inner frame's width to fill the canvas
                self.canvas.itemconfigure(interior_id, width=self.canvas.winfo_width())
            # Remove or add scrollbars depending on whether or not they're necessary
            self._configure_scrollbars()
        self.canvas.bind('<Configure>', _configure_canvas)

    # If the scrollable area is smaller than the window size, get rid of the
    # scroll bars. Keep space while the scrollbars are gone though.
    def _configure_scrollbars(self):
        if self.canvas.winfo_height() > self.interior.winfo_reqheight():
            self.scrollbarwidth = self.vscrollbar.winfo_width()
            self.vscrollbar.grid_forget()
            self.canvas.grid_configure(padx=(0,self.scrollbarwidth))
        else:
            self.vscrollbar.grid(row=0, column=1, sticky='ns')
            self.canvas.grid_configure(padx=(0,0))


class ChatFrame(VerticalScrolledFrame):
    def __init__(self, parent, minHeight, minWidth, *args, **kw):
        VerticalScrolledFrame.__init__(self, parent, minHeight, minWidth, *args, **kw)

    def addChat(self, chat, messageFrame):
        btn = tk.Button(self.interior, height=1, width=20, relief=tk.FLAT, 
            bg="gray99", fg="purple3",
            font="Dosis", text=chat.getName(),
            command=lambda chat=chat: messageFrame.addMessages(chat))
        btn.pack(padx=0, pady=0, side=tk.TOP)

        self._configure_scrollbars()

class MessageFrame(VerticalScrolledFrame):
    def __init__(self, parent, minHeight, minWidth, *args, **kw):
        VerticalScrolledFrame.__init__(self, parent, minHeight, minWidth, *args, **kw)

    def addMessages(self, chat):
        for widget in self.interior.winfo_children():
            widget.destroy()
        chat._loadMessages()
        messageDict = chat.getMessages()
        for message in messageDict.values():
            msg = MessageBubble(self.interior, message.messageId, padx=0, pady=5, width=200, bg='blue', text=message.text, font="Dosis")
            if message.isFromMe:
                msg.pack(anchor=tk.E, expand=tk.FALSE)
            else:
                msg.pack(anchor=tk.W, expand=tk.FALSE)
        self._configure_scrollbars()

class MessageBubble(tk.Message):

    def __init__(self, parent, messageId, *args, **kw):
        tk.Message.__init__(self, parent, *args, **kw)
        self.messageId = messageId


root = tk.Tk()
root.title("Scrollable Frame Demo")
root.configure(background="gray99")
root.minsize(500, 100)
chatFrame = ChatFrame(root, 0, 100)
chatFrame.grid(row=0, column=0, sticky='nsew')
messageFrame = MessageFrame(root, 0, 400)
messageFrame.grid(row=0, column=1, sticky='nsew')
root.columnconfigure(1, weight=1)
root.rowconfigure(0, weight=1)
chats = api._loadChats()


for i, chat in enumerate(chats):
    chatFrame.addChat(chat, messageFrame)

def openlink(i):
    print(lis[i])

root.mainloop()