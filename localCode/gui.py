import tkinter as tk
import threading
from responseframe import ResponseFrame
from chatframe import ChatFrame

def updateFrames(chatFrame, responseFrame):
    chatIds = api._getChatsToUpdate(0)
    for chatIdTuple in chatIds:
        try:
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
                for rowid in chatFrame.chatButtons:
                    chatFrame.chatButtons[rowid].pack_forget()
                chatFrame.addChat(chat, responseFrame)
                for rowid in chatFrame.chatButtons:
                    if rowid != chatId:            
                        chatFrame.chatButtons[rowid].pack(fill=tk.X, side=tk.TOP, pady=1)
                #need to reconfigure scrollbars again
        except api.ChatDeletedException as e:
            # Probably want to delete the messages to avoid unnecessary computation.
            # But should deleting the chat on another device delete it from here?
            continue
            
        # 
    threading.Timer(1, lambda chatFrame=chatFrame, responseFrame=responseFrame: updateFrames(chatFrame, responseFrame)).start()

def runGui(DEBUG):
    if DEBUG == 1:
        globals()["api"] = __import__('dummyApi')
    else:
        globals()["api"] = __import__('api')
    root = tk.Tk()
    root.title("Scrollable Frame Demo")
    root.configure(background="gray99")
    minWidthChatFrame = 270
    minWidthResponseFrame = int(4*minWidthChatFrame/3)
    root.minsize(minWidthChatFrame+minWidthResponseFrame, 100)
    chatFrame = ChatFrame(root, 0, minWidthChatFrame)
    chatFrame.grid(row=0, column=0, sticky='nsew')
    responseFrame = ResponseFrame(root, minWidthResponseFrame, api)
    responseFrame.grid(row=0, column=1, sticky='nsew')
    root.columnconfigure(1, weight=1)
    root.rowconfigure(0, weight=1)
    chats = api._loadChats()

    for i, chat in enumerate(chats):
        chatFrame.addChat(chat, responseFrame)

    updateFrames(chatFrame, responseFrame)

    while True:
        try:
            root.mainloop()
            break
        except UnicodeDecodeError:
            pass

if __name__ == '__main__':
    runGui(1)