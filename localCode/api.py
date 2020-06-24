import sqlite3
import os
import json
import time
import subprocess
import threading
import sqlcommands
from dataclasses import dataclass

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
        if message.rowid in updatedMessages:
            updatedMessages[message.rowid].update(message)
        else:
            keys = list(updatedMessages)
            if keys:
                self._insert(message, updatedMessages, keys)
            # If the list is empty we end up here
            else:
                updatedMessages[message.rowid] = message
        self.messages = updatedMessages

        self._updateMostRecentMessage(message)

        self.writeLock.release()

    def _insert(self, message, messageList, keys):
        # Here we need to check the dates near the end of the dictionary
        # We assume that the dictionary will be sorted at this point
        # by induction.
        # Avoid using reverse here since it has complexity O(n)
        i = 0
        # If i == -1, we know that this message is older than all
        # other messages in the list.
        for i in range(len(keys) - 1, -2, -1):
            #
            if i == -1:
                break
            key = keys[i]
            if message.isNewer(messageList[key]):
                break

        # Find the keys that will need to come after this new message
        keysToRemove = [k for k in keys[i + 1:]]
        # Remove the keys, but save messages
        poppedMessages = []
        for key in keysToRemove:
            poppedMessages.append(messageList.pop(key))
        # Add in the new message
        messageList[message.rowid] = message
        # Add back the messages we removed from the list
        poppedMessages.reverse()
        for _ in range(len(poppedMessages)):
            p = poppedMessages.pop()
            messageList[p.rowid] = p

    def addReaction(self, reaction):

        self.writeLock.acquire()
        if reaction.associatedMessageId in self.messages.keys():
            self.messages[reaction.associatedMessageId].addReaction(reaction)

        self._updateMostRecentMessage(reaction)

        self.writeLock.release()

    def _updateMostRecentMessage(self, message):
        if (self.mostRecentMessage is None or
                message.isNewer(self.mostRecentMessage)):
            self.mostRecentMessage = message

    def getMostRecentMessage(self):
        return self.mostRecentMessage


class Attachment:
    def __init__(self, **kw):
        self.attr = {}
        for key, value in kw.items():
            self.attr[key] = value


class ReceivedNoIdException(Exception):
    pass


class ReactionNoAssociatedIdException(Exception):
    pass


@dataclass
class Received:

    ROWID: int = None
    guid: str = ''
    text: str = ''
    handle_id: int = 1
    service: str = None
    date: int = 0
    date_read: int = 0
    date_delivered: int = 0
    is_delivered: int = 0
    is_finished: int = 0
    is_from_me: int = 0
    is_read: int = 0
    is_sent: int = 0
    cache_has_attachments: int = 0
    cache_roomnames: str = None
    item_type: int = 0
    other_handle: int = 0
    group_title: str = None
    group_action_type: int = 0
    associated_message_guid: str = None
    associated_message_type: int = 0
    attachment_id: str = None
    message_update_date: int = 0
    error: int = 0

    def __post_init__(self):

        if self.ROWID is None:
            raise ReceivedNoIdException

        # tkinter only supports some unicode characters.
        # This removes unsupported ones.
        text = self.text
        if self.text is not None:
            self.text = ''.join([text[t] for t in range(
                len(text)) if ord(text[t]) in range(65536)])
        self._isTemporary = False
        self._handleName = ''

    @property
    def rowid(self):
        return self.ROWID

    @property
    def handleId(self):
        return self.handle_id

    @property
    def dateRead(self):
        return self.date_read

    @property
    def isFromMe(self):
        return self.is_from_me == 1

    @property
    def isDelivered(self):
        return self.is_delivered == 1

    @property
    def isiMessage(self):
        return self.service == 'iMessage'

    @property
    def isTemporary(self):
        return self.rowid < 0

    @property
    def isTemporary(self):
        return self._isTemporary

    @isTemporary.setter
    def isTemporary(self, val):
        self._isTemporary = val

    @property
    def handleName(self):
        return self._handleName

    @handleName.setter
    def handleName(self, handleName):
        self._handleName = handleName

    def isNewer(self, otherMessage):
        if self.date > otherMessage.date:
            return True
        elif self.date < otherMessage.date:
            return False
        else:
            if self.rowid > otherMessage.rowid:
                return True
            return False


class Message(Received):

    def __post_init__(self):
        super().__post_init__()
        self.reactions = {}
        self.attachment = None
        self.removeTemp = 0

    def addReaction(self, reaction):
        # If the handle sending the reaction has not reacted to this message,
        # add it.
        if not reaction.handleId in self.reactions:
            self.reactions[reaction.handleId] = {}

        # Reactions and reaction removals have the same digit in the ones place
        reactionVal = reaction.associated_message_type % 1000

        # If the handle has already sent this reaction, but this one is newer,
        # replace the old reaction with this one.
        handleReactions = self.reactions[reaction.handleId]
        if (reactionVal in handleReactions and
                reaction.isNewer(handleReactions[reactionVal])):
            self.reactions[reaction.handleId][reactionVal] = reaction
        elif reactionVal not in handleReactions:
            self.reactions[reaction.handleId][reactionVal] = reaction

    def update(self, updatedMessage):
        self.date = updatedMessage.date
        self.date_read = updatedMessage.date_read
        self.date_delivered = updatedMessage.date_delivered
        self.is_delivered = updatedMessage.is_delivered
        self.is_finished = updatedMessage.is_finished
        self.is_read = updatedMessage.is_read
        self.is_sent = updatedMessage.is_sent
        self.message_update_date = updatedMessage.message_update_date
        self.service = updatedMessage.service

        if updatedMessage.attachment:
            self.attachment = updatedMessage.attachment


@dataclass
class Reaction(Received):
    associated_message_id: int = None

    def __post_init__(self):
        super().__post_init__()
        if self.associated_message_id is None:
            raise ReactionNoAssociatedIdException

    @property
    def isAddition(self):
        return self.associated_message_type < 3000

    @property
    def reactionType(self):
        return self.associated_message_type

    @property
    def associatedMessageId(self):
        return self.associated_message_id


class ChatDeletedException(Exception):
    pass


class DummyChat:
    def __init__(self, chatId):
        self.rowid = chatId


class Chat:

    def __init__(self, chatId, chatIdentifier, displayName, **kw):

        self.attr = {}
        for key, value in kw.items():
            self.attr[key] = value
        if 'display_name' not in self.attr:
            self.attr['display_name'] = ''
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
        self.isTemporaryChat = False

    @property
    def rowid(self):
        return self.attr['ROWID']

    def isiMessage(self):
        if ('service_name' in self.attr and
                self.attr['service_name'] == 'iMessage'):
            return True
        return False

    def isGroup(self):
        if 'style' in self.attr and self.attr['style'] == 43:
            return True
        return False

    def addRecipient(self, recipient):
        if recipient:
            self.recipientList.append(recipient)
            return True
        return False

    def _loadRecipients(self):
        conn = sqlite3.connect(dbPath)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(sqlcommands.LOAD_RECIPIENTS_SQL, (self.rowid, ))
        recipients = []
        for recipient in cursor.fetchall():
            recipients.append(recipient[0])
        conn.close()
        return recipients

    def getName(self):
        if self.displayName:
            return ''.join([self.displayName[t] for t in
                            range(len(self.displayName)) if
                            ord(self.displayName[t]) in range(65536)])
        else:
            return ', '.join(self.recipientList)

    def getMessages(self):
        return self.messageList.messages

    def _loadMessages(self):
        # If self.messages is not none, we should just query for messages
        # received after last message.
        conn = sqlite3.connect(dbPath)
        conn.row_factory = sqlite3.Row
        tempLastAccess = self.lastAccessTime
        neededColumnsMessage = ['ROWID', 'guid', 'text', 'handle_id',
                                'service', 'error', 'date', 'date_read',
                                'date_delivered', 'is_delivered',
                                'is_finished', 'is_from_me', 'is_read',
                                'is_sent', 'cache_has_attachments',
                                'cache_roomnames', 'item_type',
                                'other_handle', 'group_title',
                                'group_action_type', 'associated_message_guid',
                                'associated_message_type', 'attachment_id',
                                'message_update_date']
        columns = ', '.join(neededColumnsMessage)
        sql = sqlcommands.LOAD_MESSAGES_SQL.format(columns)
        cursor = conn.execute(sql, (self.rowid, tempLastAccess))

        for row in cursor:
            handleName = conn.execute(sqlcommands.HANDLE_SQL,
                                      (row['handle_id'], )).fetchone()
            if handleName:
                handleName = handleName[0]
            else:
                handleName = ''

            if row['message_update_date'] > tempLastAccess:
                tempLastAccess = row['message_update_date']

            # If there are no associated messages
            if not row['associated_message_guid']:
                attachment = None
                if row['attachment_id'] is not None:
                    a = conn.execute(sqlcommands.ATTACHMENT_SQL,
                                     (row['attachment_id'], )).fetchone()
                    attachment = Attachment(**a)
                message = Message(**row)
                message.handleName = handleName
                self.messageList.append(message)

                if message.isFromMe == 1:
                    self.removeTemporaryMessage(self.messageList.
                                                messages[message.rowid])
            else:
                assocMessageId = conn.execute(sqlcommands.ASSOC_MESSAGE_SQL,
                                              (row['associated_message_guid']
                                                  [-36:], )).fetchone()
                if assocMessageId:
                    assocMessageId = assocMessageId[0]
                    reaction = Reaction(associated_message_id=assocMessageId, **row)
                    reaction.handleName = handleName
                    self.messageList.addReaction(reaction)

        conn.close()

        self.lastAccessTime = max(self.lastAccessTime, tempLastAccess)

    def removeTemporaryMessage(self, message):
        self.messageList.writeLock.acquire()
        self.outgoingList.writeLock.acquire()
        idToDelete = 0
        for tempMsgId in self.outgoingList.messages:
            tempMsg = self.outgoingList.messages[tempMsgId]
            if (tempMsg.text == message.text and
                    message.removeTemp is 0):
                message.removeTemp = tempMsg.rowid
                del self.messageList.messages[tempMsgId]
                idToDelete = tempMsgId
                break
        if idToDelete != 0:
            del self.outgoingList.messages[idToDelete]
        self.messageList.writeLock.release()
        self.outgoingList.writeLock.release()

    def sendMessage(self, messageText, recipientString):
        messageTextC = messageText.replace("'", "\\'")
        recipientString = recipientString.replace('\'', '\\\'')
        self.sendData(messageTextC, messageId=None, assocType=None,
                      messageCode=0, recipientString=recipientString)
        msg = Message(**{'ROWID': self.messagePreviewId,
                                     'text': messageText, 'date':
                                     int(time.time()), 'date_read': 0,
                                     'is_delivered': 0, 'is_from_me': 1,
                                     'service': 'iMessage'})
        msg.isTemporary = True
        self.messagePreviewId -= 1
        self.messageList.append(msg)
        self.outgoingList.append(msg)
        self.localUpdate = True

    def sendReaction(self, messageId, assocType):
        self.sendData(messageText='', messageId=messageId, assocType=assocType,
                      messageCode=1, recipientString='')

    def sendData(self, messageText='', messageId=None, assocType=None,
                 messageCode=None, recipientString=''):
        cmd = [
            "ssh",
            "{}@{}".format(
                user,
                ip),
            "python {} $\'{}\' \'{}\' \'{}\' \'{}\' \'{}\' $\'{}\'".format(
                scriptPath,
                messageText,
                self.rowid,
                messageCode,
                messageId,
                assocType,
                recipientString)]
        subprocess.run(cmd)

    def getMostRecentMessage(self):
        return self.messageList.getMostRecentMessage()

    def _loadMostRecentMessage(self):
        conn = sqlite3.connect(dbPath)
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(sqlcommands.RECENT_MESSAGE_SQL, (self.rowid, ))
        for row in cursor.fetchall():
            if not row['associated_message_guid']:
                message = Message(**row)
                self.messageList.append(message)
                break
            else:
                assocMessageId = conn.execute(sqlcommands.ASSOC_MESSAGE_SQL,
                                              (row['associated_message_guid']
                                               [-36:], )).fetchone()
                if assocMessageId:
                    assocMessageId = assocMessageId[0]
                    reaction = Reaction(associated_message_id=assocMessageId, **row)
                    self.messageList.addReaction(reaction)
                    break
        conn.close()


def createNewChat(chatId):
    chat = Chat(chatId, '', None, **{'ROWID': chatId})
    return chat


def _loadChat(chatId):
    conn = sqlite3.connect(dbPath)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(sqlcommands.LOAD_CHAT_SQL,
                          (chatId, ))
    row = cursor.fetchone()
    if row is None:
        raise ChatDeletedException
    chat = Chat(row[0], row[1], row[2], **row)
    conn.close()
    if chat is None:
        return None
    if chat.getMostRecentMessage().rowid is not None:
        return chat

    return None


def _getChatsToUpdate(lastAccessTime, chats):
    conn = sqlite3.connect(dbPath)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(sqlcommands.CHATS_TO_UPDATE_SQL, (lastAccessTime, ))
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
                chatIds.append(chat.rowid)
    conn.close()
    return chatIds, maxUpdate


def _ping():
    try:
        output = subprocess.run(['nc', '-vz', '-w 1', ip, '22'],
                                stderr=subprocess.DEVNULL, check=True)
        return True
    except subprocess.CalledProcessError as e:
        return False


def _useTestDatabase(dbName):
    global dbPath
    dbPath = os.path.join(dirname, dbName)
