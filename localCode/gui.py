import tkinter as tk
from tkinter import ttk
import threading
import os
import simpleaudio as sa
from responseframe import ResponseFrame
from chatframe import LeftFrame
import messageApi.api as api


def updateFrames(chatFrame, responseFrame, lastAccessTime,
                 lastSoundTime, currentThread):
    if currentThread._stopevent.isSet():
        chatFrame.master.quit()
        # chatFrame.master.destroy()
        return

    db = api.MessageDatabase()
    chatIds, newLastAccessTime = db.getChatsToUpdate(lastAccessTime,
                                                     chatFrame.chats)
    chatFrame.lock.acquire()
    newMessageFlag = False
    for chatId in chatIds:
        try:
            for chatButton in chatFrame.chatButtons:
                if chatId == chatButton.chat.chatId:
                    recentMessage = db.getMostRecentMessage(
                        chatButton.chat.chatId)
                    chatButton.chat.addMessage(recentMessage)
                    if chatButton.update():
                        newMessageFlag = True

            if chatId == responseFrame.currentChat.chatId:
                (responseFrame.messageFrame
                 .addMessages(responseFrame.currentChat))

            if chatId not in chatFrame.chatButtons:
                row = db.getChat(chatId)
                chat = api.Chat(**row)
                chat.addRecipients(db.getRecipients(chat.chatId))
                recentMessage = db.getMostRecentMessage(chat.chatId)
                chat.addMessage(recentMessage)
                chatFrame.addChat(chat, responseFrame)
                if lastAccessTime == 0:
                    newMessageFlag = False

        except api.ChatDeletedException as e:
            continue

    sortedChats = sorted(chatFrame.chatButtons, key=lambda chatButton:
                         chatButton.lastMessageTimeValue, reverse=True)
    for i in range(len(sortedChats)):
        if (sortedChats[i].chat.chatId != chatFrame.chatButtons[i].chat.chatId
                or sortedChats[i].isVisible is False):
            chatFrame.chatButtons = sortedChats
            chatFrame.packChatButtons()
            break

    if newMessageFlag and lastSoundTime == 0:
        lastSoundTime = 5
        threading.Thread(target=lambda: soundObject.play().wait_done()).start()

    chatFrame.lock.release()

    threading.Thread(target=lambda sendFrame=responseFrame.sendFrame:
                     sendFrame.setIsConnected(sendFrame.mp.ping())).start()
    lastSoundTime = 0 if lastSoundTime == 0 else lastSoundTime - 1
    threading.Timer(1, lambda chatFrame=chatFrame, responseFrame=responseFrame,
                    lastAccessTime=newLastAccessTime,
                    lastSoundTime=lastSoundTime, currentThread=currentThread:
                        updateFrames(chatFrame, responseFrame, lastAccessTime,
                                     lastSoundTime, currentThread)).start()


def runGui(debug, currentThread):
    root = tk.Tk()
    root.title("Messages")
    root.configure(background="gray99")

    style = ttk.Style()

    borderImage = tk.PhotoImage("borderImage", file='messageBox.png')
    style.element_create("RoundedFrame",
                         "image", borderImage,
                         ("focus", borderImage),
                         border=16, sticky="nsew")
    style.layout("RoundedFrame", [("RoundedFrame", {"sticky": "nsew"})])

    minWidthChatFrame = 270
    minWidthResponseFrame = int(4 * minWidthChatFrame / 3)
    root.minsize(minWidthChatFrame + minWidthResponseFrame,
                 (minWidthChatFrame + minWidthResponseFrame) // 2)
    responseFrame = ResponseFrame(root, minWidthResponseFrame, api)
    responseFrame.grid(row=0, column=1, sticky='nsew')
    leftFrame = LeftFrame(root, 0, minWidthChatFrame, responseFrame, api)
    chatFrame = leftFrame.chatFrame
    chatFrame.setDebug(debug)
    leftFrame.grid(row=0, column=0, sticky='nsew')
    root.columnconfigure(1, weight=1)
    root.rowconfigure(0, weight=1)

    global soundObject
    soundObject = sa.WaveObject.from_wave_file('bing.wav')
    updateFrames(chatFrame, responseFrame, 0, 0, currentThread)

    while True:
        try:
            root.mainloop()
            break
        except UnicodeDecodeError:
            pass


class GuiThread(threading.Thread):

    def __init__(self, debug=False, name='GuiThread'):
        self._stopevent = threading.Event()
        threading.Thread.__init__(self, name=name)

        dirname = os.path.dirname(__file__)

        self.debug = debug
        secretsPath = os.path.join(dirname, 'secrets.json')
        dbPath = os.path.join(dirname, 'sms.db')
        api.initialize(dbPath, secretsPath)

    def run(self):
        runGui(self.debug, self)

    def stopThread(self):
        self._stopevent.set()


if __name__ == '__main__':
    runGui(1)
