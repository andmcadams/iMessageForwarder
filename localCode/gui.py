import tkinter as tk
import threading
from playsound import playsound
from responseframe import ResponseFrame
from chatframe import ChatFrame

def updateFrames(chatFrame, responseFrame, lastAccessTime):
    chatIds, newLastAccessTime = api._getChatsToUpdate(lastAccessTime)
    chatFrame.lock.acquire()
    newMessageFlag = False
    for chatId in chatIds:
        try:
            for chatButton in chatFrame.chatButtons:
                if chatId == chatButton.chat.chatId:
                    chatButton.chat._loadMostRecentMessage()
                    if chatButton.update():
                        newMessageFlag = True

            if chatId == responseFrame.currentChat.chatId:
                responseFrame.messageFrame.addMessages(responseFrame.currentChat)

            if not chatId in chatFrame.chatButtons:
                chat = api._loadChat(chatId)
                chatFrame.addChat(chat, responseFrame)
                if lastAccessTime == 0:
                    newMessageFlag = False

        except api.ChatDeletedException as e:
            # Probably want to delete the messages to avoid unnecessary computation.
            # But should deleting the chat on another device delete it from here?
            continue

    sortedChats = sorted(chatFrame.chatButtons, key=lambda chatButton: chatButton.lastMessageTimeValue, reverse=True)
    for i in range(len(sortedChats)):
        if sortedChats[i].chat.chatId != chatFrame.chatButtons[i].chat.chatId or sortedChats[i].isVisible == False:
            chatFrame.chatButtons = sortedChats
            chatFrame.packChatButtons()
            break

    if newMessageFlag:
        threading.Thread(target=lambda: playsound('bing.wav')).start()

    chatFrame.lock.release()
    
    threading.Timer(1, lambda chatFrame=chatFrame, responseFrame=responseFrame, lastAccessTime=newLastAccessTime: updateFrames(chatFrame, responseFrame, lastAccessTime)).start()

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
    root.minsize(minWidthChatFrame+minWidthResponseFrame, (minWidthChatFrame+minWidthResponseFrame)//2)
    chatFrame = ChatFrame(root, 0, minWidthChatFrame)
    chatFrame.grid(row=0, column=0, sticky='nsew')
    responseFrame = ResponseFrame(root, minWidthResponseFrame, api)
    responseFrame.grid(row=0, column=1, sticky='nsew')
    root.columnconfigure(1, weight=1)
    root.rowconfigure(0, weight=1)
    chats = api._loadChats()

    updateFrames(chatFrame, responseFrame, 0)

    while True:
        try:
            root.mainloop()
            break
        except UnicodeDecodeError:
            pass

if __name__ == '__main__':
    runGui(1)