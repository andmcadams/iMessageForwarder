import sqlite3
import os
import json
import time
import subprocess
import threading

dirname = os.path.dirname(__file__)

dbPath = os.path.join(dirname, 'sms.db')

secretsFile = os.path.join(dirname, 'secrets.json')
secrets = json.load(open(secretsFile))
user = secrets['user']
ip = secrets['ip']
scriptPath = secrets['scriptPath']


"""
MessageList needs to satisfy two major criteria:
    1. Easy lookup to find a message based on messageId to update messages
    2. Ordering based on date
1 allows O(1) average time finding messages to update, which can be
  important if a user doesn't delete messages
2 allows sorting to happen at insertion in order to save time when printing
  messages and fetching older ones
Dictionary order is guaranteed (insertion order) in python 3.7+
"""


class MessageList(dict):
    def __init__(self):
        self.messages = {}
        self.mostRecentMessage = None
        self.writeLock = threading.Lock()

    # Sorting on insertion is likely faster than inserting all messages with
    # one sort.
    # The assumption is that messages will be inserted near the end,
    # requiring fewer checks than looking at the entire list.
    def append(self, message):
        self.writeLock.acquire()
        updatedMessages = self.messages

        # If the message is just being updated, no need to worry about ordering
        # (assumption that date should never change)
        if message.attr['ROWID'] in updatedMessages:
            updatedMessages[message.attr['ROWID']].update(message)
        else:
            keys = list(updatedMessages)
            # Here we need to check the dates near the end of the dictionary
            # We assume that the dictionary will be sorted at this point
            # by induction.
            # Avoid using reverse here since it has complexity O(n)
            if keys:
                i = 0
                # If i == -1, we know that this message is older than all
                # other messages in the list.
                for i in range(len(keys)-1, -2, -1):
                    #
                    if i == -1:
                        break
                    key = keys[i]
                    if message.isNewer(updatedMessages[key]):
                        break

                # Find the keys that will need to come after this new message
                keysToRemove = [k for k in keys[i+1:]]
                # Remove the keys, but save messages
                poppedMessages = []
                for key in keysToRemove:
                    poppedMessages.append(updatedMessages.pop(key))
                # Add in the new message
                updatedMessages[message.attr['ROWID']] = message
                # Add back the messages we removed from the list
                poppedMessages.reverse()
                for _ in range(len(poppedMessages)):
                    p = poppedMessages.pop()
                    updatedMessages[p.attr['ROWID']] = p
            # If the list is empty we end up here
            else:
                updatedMessages[message.attr['ROWID']] = message
        self.messages = updatedMessages

        if (self.mostRecentMessage is None or
                message.isNewer(self.mostRecentMessage)):
            self.mostRecentMessage = message
        self.writeLock.release()

    def addReaction(self, reaction):

        self.writeLock.acquire()
        if reaction.associatedMessageId in self.messages.keys():
            self.messages[reaction.associatedMessageId].addReaction(reaction)

        if (self.mostRecentMessage is None or
                reaction.isNewer(self.mostRecentMessage)):
            self.mostRecentMessage = reaction
        self.writeLock.release()

    def getMostRecentMessage(self):
        return self.mostRecentMessage


class Attachment:
    def __init__(self, **kw):
        self.attr = {}
        for key, value in kw.items():
            self.attr[key] = value


class MessageNoIdException(Exception):
    pass


class Message:

    def __init__(self, attachment=None, handleName=None, **kw):
        self.attr = {}
        self.reactions = {}
        for key, value in kw.items():
            self.attr[key] = value

        if 'ROWID' not in self.attr:
            raise MessageNoIdException

        # tkinter only supports some unicode characters.
        # This removes unsupported ones.
        self.attr['text'] = None
        if 'text' in kw and kw['text'] is not None:
            length = len(kw['text'])
            self.attr['text'] = ''.join([kw['text'][t] for t in range(length)
                                        if ord(kw['text'][t]) in range(65536)])

        self.attachment = attachment
        self.handleName = handleName

    def addReaction(self, reaction):
        # If the handle sending the reaction has not reacted to this message,
        # add it.
        if not reaction.attr['handle_id'] in self.reactions:
            self.reactions[reaction.attr['handle_id']] = {}

        # Reactions and reaction removals have the same digit in the ones place
        reactionVal = int(reaction.attr['associated_message_type']) % 1000

        # If the handle has already sent this reaction, but this one is newer,
        # replace the old reaction with this one.
        handleReactions = self.reactions[reaction.attr['handle_id']]
        if (reactionVal in handleReactions and
                reaction.isNewer(handleReactions[reactionVal])):
            self.reactions[reaction.attr['handle_id']][reactionVal] = reaction
        elif reactionVal not in handleReactions:
            self.reactions[reaction.attr['handle_id']][reactionVal] = reaction

    def isNewer(self, otherMessage):
        if self.attr['date'] > otherMessage.attr['date']:
            return True
        elif self.attr['date'] < otherMessage.attr['date']:
            return False
        else:
            if self.attr['ROWID'] > otherMessage.attr['ROWID']:
                return True
            return False

    def update(self, updatedMessage):
        for key, value in updatedMessage.attr.items():
            self.attr[key] = value


class Reaction:

    def __init__(self, associatedMessageId, handleName=None, **kw):
        self.attr = {}
        self.associatedMessageId = associatedMessageId
        self.handleName = handleName
        for key, value in kw.items():
            self.attr[key] = value

        # This has to be done since tkinter only supports some unicode characters
        self.attr['text'] = None
        if 'text' in kw and kw['text'] is not None:
            self.attr['text'] = ''.join([kw['text'][t] for t in range(len(kw['text'])) if ord(kw['text'][t]) in range(65536)])

    def isNewer(self, otherMessage):
        if self.attr['date'] > otherMessage.attr['date']:
            return True
        elif self.attr['date'] < otherMessage.attr['date']:
            return False
        else:
            if self.attr['ROWID'] > otherMessage.attr['ROWID']:
                return True
            return False


class ChatDeletedException(Exception):
    pass


class DummyChat:
    def __init__(self, chatId):
        self.chatId = chatId


class Chat:

    def __init__(self, chatId, chatIdentifier, displayName, **kw):
        self.chatId = chatId
        self.chatIdentifier = chatIdentifier
        self.displayName = displayName
        self.messageList = MessageList()
        self.outgoingList = MessageList()
        self.recipientList = self._loadRecipients()
        self._loadMostRecentMessage()
        self.lastAccessTime = 0
        self.localUpdate = False
        self.messagePreviewId = -1

        self.attr = {}
        for key, value in kw.items():
            self.attr[key] = value

    def isiMessage(self):
        if 'service_name' in self.attr and self.attr['service_name'] == 'iMessage':
            return True
        return False

    def isGroup(self):
        if 'style' in self.attr and self.attr['style'] == 43:
            return True
        return False

    def _loadRecipients(self):
        conn = sqlite3.connect(dbPath)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('select id from handle inner join chat_handle_join on handle.ROWID = chat_handle_join.handle_id and chat_handle_join.chat_id = ?', (self.chatId, ))
        recipients = []
        for recipient in cursor.fetchall():
            recipients.append(recipient[0])
        conn.close()
        return recipients

    def getName(self):
        if self.displayName:
            return ''.join([self.displayName[t] for t in range(len(self.displayName)) if ord(self.displayName[t]) in range(65536)])
        else:
            return ', '.join(self.recipientList)

    def getMessages(self):
        return self.messageList.messages

    def _loadMessages(self):
        # if self.messages is not none, we should just query for messages received after last message
        conn = sqlite3.connect(dbPath)
        conn.row_factory = sqlite3.Row
        tempLastAccess = self.lastAccessTime
        neededColumnsMessage = ['ROWID', 'guid', 'text', 'handle_id', 'service', 'error', 'date', 'date_read', 'date_delivered', 'is_delivered', 'is_finished', 'is_from_me', 'is_read', 'is_sent', 'cache_has_attachments', 'cache_roomnames', 'item_type', 'other_handle', 'group_title', 'group_action_type', 'associated_message_guid', 'associated_message_type', 'attachment_id']
        columns = ', '.join(neededColumnsMessage)
        sql = 'SELECT {}, message_update_date FROM message inner join chat_message_join on message.ROWID = chat_message_join.message_id and chat_message_join.chat_id = ? inner join message_update_date_join on message.ROWID = message_update_date_join.message_id and message_update_date_join.message_update_date > ? left join message_attachment_join on message.ROWID = message_attachment_join.message_id'.format(columns)
        cursor = conn.execute(sql, (self.chatId, tempLastAccess))

        for row in cursor:
            handleSql = 'SELECT id from handle where ROWID = ?'
            handleName = conn.execute(handleSql, (row['handle_id'], )).fetchone()
            if handleName:
                handleName = handleName[0]
            else:
                handleName = ''

            if row['message_update_date'] > tempLastAccess:
                tempLastAccess = row['message_update_date']
            if not row['associated_message_guid']:
                attachment = None
                if row['attachment_id'] is not None:
                    a = conn.execute('SELECT filename, uti from attachment where ROWID = ?', (row['attachment_id'], )).fetchone()
                    attachment = Attachment(**a)
                message = Message(attachment, handleName, **row)
                self.messageList.append(message)
                if message.attr['is_from_me'] == 1:
                    self.isTemporary(self.messageList.messages[message.attr['ROWID']])
            else:
                associatedMessageId = conn.execute('SELECT ROWID FROM message where guid = ?', (row['associated_message_guid'][-36:], )).fetchone()
                if associatedMessageId:
                    associatedMessageId = associatedMessageId[0]
                    reaction = Reaction(associatedMessageId, handleName, **row)
                    self.messageList.addReaction(reaction)

        conn.close()

        self.lastAccessTime = max(self.lastAccessTime, tempLastAccess)

    def isTemporary(self, message):
        self.messageList.writeLock.acquire()
        self.outgoingList.writeLock.acquire()
        idToDelete = 0
        for tempMsgId in self.outgoingList.messages:
            tempMsg = self.outgoingList.messages[tempMsgId]
            if (tempMsg.attr['text'] == message.attr['text'] and
                    'removeTemp' not in message.attr):
                message.attr['removeTemp'] = tempMsgId
                del self.messageList.messages[tempMsgId]
                idToDelete = tempMsgId
                break
        if idToDelete != 0:
            del self.outgoingList.messages[idToDelete]
        self.messageList.writeLock.release()
        self.outgoingList.writeLock.release()

    def sendMessage(self, messageText):
        messageText = messageText.replace('\'', '\\\'')
        subprocess.run(["ssh", "{}@{}".format(user, ip), "python {} $\'{}\' {} {}".format(scriptPath, messageText, self.chatId, 0)])
        msg = Message(None, None, **{'ROWID': self.messagePreviewId, 'text': messageText, 'date': int(time.time()), 'date_read': 0, 'is_delivered': 0, 'is_from_me': 1, 'service': 'iMessage', 'temporary': 1})
        self.messagePreviewId -= 1
        self.messageList.append(msg)
        self.outgoingList.append(msg)
        self.localUpdate = True

    def sendReaction(self, messageId, assocType):
        subprocess.run(["ssh", "{}@{}".format(user, ip), "python {} \'{}\' {} {} \'{}\' {}".format(scriptPath, '', self.chatId, 1, messageId, assocType)])

    def getMostRecentMessage(self):
        return self.messageList.getMostRecentMessage()

    def _loadMostRecentMessage(self):
        conn = sqlite3.connect(dbPath)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute('select ROWID, handle_id, text, date, is_from_me, associated_message_guid, associated_message_type, is_delivered, is_from_me from message inner join chat_message_join on message.ROWID = chat_message_join.message_id and chat_message_join.chat_id = ? order by date desc, ROWID desc', (self.chatId, ))
        for row in cursor.fetchall():
            if not row['associated_message_guid']:
                message = Message(**row)
                self.messageList.append(message)
                break
            else:
                associatedMessageId = conn.execute('SELECT ROWID FROM message where guid = ?', (row['associated_message_guid'][-36:], )).fetchone()
                if associatedMessageId:
                    associatedMessageId = associatedMessageId[0]
                    reaction = Reaction(associatedMessageId, **row)
                    self.messageList.addReaction(reaction)
                    break
        conn.close()


def _loadChat(chatId):
    conn = sqlite3.connect(dbPath)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute('select ROWID, chat_identifier, display_name, style, service_name from chat where ROWID = ?', (chatId, ))
    row = cursor.fetchone()
    if row is None:
        raise ChatDeletedException
    chat = Chat(row[0], row[1], row[2], **row)
    conn.close()
    if chat is None:
        return None
    if chat.getMostRecentMessage().attr['ROWID'] is not None:
        return chat

    return None


def _loadChats():
    conn = sqlite3.connect(dbPath)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute('select ROWID, chat_identifier, display_name, style from chat')
    chats = []
    for row in cursor.fetchall():
        chat = Chat(row[0], row[1], row[2], **row)
        if chat.getMostRecentMessage().attr['ROWID'] is not None:
            chats.append(chat)
    conn.close()
    chats = sorted(chats, key=lambda chat: chat.getMostRecentMessage().attr['date'], reverse=True)
    return chats


def _getChatsToUpdate(lastAccessTime, chats):
    conn = sqlite3.connect(dbPath)
    conn.row_factory = sqlite3.Row
    sql = 'SELECT chat_id, max(message_update_date), text FROM message inner join chat_message_join on message.ROWID = chat_message_join.message_id inner join message_update_date_join on message.ROWID = message_update_date_join.message_id and message_update_date_join.message_update_date > ? group by chat_id'
    cursor = conn.execute(sql, (lastAccessTime, ))
    chatIds = []
    maxUpdate = lastAccessTime
    for row in cursor.fetchall():
        chatIds.append(row['chat_id'])
        if row['max(message_update_date)'] > maxUpdate:
            maxUpdate = row['max(message_update_date)']
    for idx in chats:
        chat = chats[idx]
        if chat.localUpdate:
            chat.localUpdate = False
            if chat.chatId not in chatIds:
                chatIds.append(chat.chatId)
    conn.close()
    return chatIds, maxUpdate


def _ping():
    try:
        output = subprocess.run(['nc', '-vz', '-w 1', ip, '22'], stderr=subprocess.DEVNULL, check=True)
        return True
    except subprocess.CalledProcessError as e:
        return False


def _useTestDatabase(dbName):
    global dbPath
    dbPath = os.path.join(dirname, dbName)
