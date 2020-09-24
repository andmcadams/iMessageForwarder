import sqlite3
import re
import os
import json
import time
import subprocess
import threading
import requests
import functools
from . import sqlcommands
from typing import List, Type, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass


def initialize(pathToDb, secretsFile):
    global dbPath, user, ip

    dbPath = pathToDb
    secrets = json.load(open(secretsFile))
    user = secrets['user']
    ip = secrets['ip']


class MessageList(dict):
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

    def __init__(self):
        self.messages = {}
        self.mostRecentMessage = None
        self.writeLock = threading.Lock()

    # Sorting on insertion is likely faster than inserting all messages with
    # one sort.
    # The assumption is that messages will be inserted near the end,
    # requiring fewer checks than looking at the entire list.
    def append(self, message: 'Received') -> None:
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

    def _insert(self,
                message: 'Received',
                messageList: Dict[int,
                                  'Received'],
                keys: List[int]) -> None:
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

    def addReaction(self, reaction: 'Reaction') -> None:

        self.writeLock.acquire()
        if reaction.associatedMessageId in self.messages.keys():
            self.messages[reaction.associatedMessageId].addReaction(reaction)

        self._updateMostRecentMessage(reaction)

        self.writeLock.release()

    def _updateMostRecentMessage(self, message: 'Received') -> None:
        if (self.mostRecentMessage is None or
                message.isNewer(self.mostRecentMessage)):
            self.mostRecentMessage = message

    def getMostRecentMessage(self) -> 'Received':
        return self.mostRecentMessage


@dataclass
class Attachment:

    ROWID: int = None
    guid: str = ''
    filename: str = ''
    uti: str = ''

    def __post_init__(self):
        if self.ROWID is None:
            raise AttachmentNoIdException

    @property
    def rowid(self) -> int:
        return self.ROWID


@dataclass
class Received(ABC):

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
    message_update_date: int = 0
    error: int = 0
    associated_message_range_location: int = 0
    associated_message_range_length: int = 0

    def __post_init__(self):

        if self.ROWID is None:
            raise ReceivedNoIdException

        # tkinter only supports some unicode characters.
        # This removes unsupported ones.
#         text = self.text
#         if self.text is not None:
#             self.text = ''.join([text[t] for t in range(
# len(text)) if ord(text[t]) in range(65536) and ord(text[t]) != 65532])
        self._handleName = 'Me' if self.is_from_me == 1 else ''
        self.removedTempId = 0

    @property
    def rowid(self) -> int:
        return self.ROWID

    @property
    def handleId(self) -> int:
        return self.handle_id

    @property
    def handleName(self) -> str:
        return self._handleName

    @handleName.setter
    def handleName(self, handleName: str) -> None:
        if handleName == '' and self.isFromMe:
            self._handleName = 'Me'
        else:
            self._handleName = handleName

    @property
    def dateRead(self) -> int:
        return self.date_read

    @property
    def isDelivered(self) -> bool:
        return self.is_delivered == 1

    @property
    def isFromMe(self) -> bool:
        return self.is_from_me == 1

    @property
    def isiMessage(self) -> bool:
        return self.service == 'iMessage'

    @property
    def isRead(self) -> bool:
        return self.is_read == 1

    @property
    def isSent(self) -> bool:
        return self.is_sent == 1

    @property
    def isTemporary(self) -> bool:
        return self.rowid < 0

    @property
    def attachment(self) -> None:
        return None

    @property
    def reactions(self) -> Dict[Any, Any]:
        return {}

    @property
    @abstractmethod
    def isReaction(self) -> bool:
        pass

    def isNewer(self, otherMessage: 'Received') -> bool:
        """Return whether or not this message is newer than otherMessage.

        Parameters:
        otherMessage : Message
            The message to compare.

        Returns:
            True if this message is newer than otherMessage.
            False if this message is older than otherMessage.
            If this message and otherMessage have the same date, age is
            determined by ROWID, with larger ROWIDs considered newer.
        """
        if self.date > otherMessage.date:
            return True
        elif self.date < otherMessage.date:
            return False
        else:
            if self.rowid > otherMessage.rowid:
                return True
            return False

    def getText(self) -> str:
        return self.text


class Message(Received):

    def __post_init__(self):
        super().__post_init__()
        messageRegex = '[^￼]+|￼'
        self._reactions = {}
        self._messageParts = []
        self._imageCount = 0

        if self.text is not None:
            self.text = self.text.replace(' ', '\n')
        text = self.text or ''
        messageParts = re.findall(messageRegex, text)

        currentLocation = 0
        hadText = False
        for part in messageParts:
            if part == '￼':
                # this is an attachment message part
                i = ImagePart(startLocation=currentLocation)
                self._messageParts.append(i)
                currentLocation += 2 if hadText else 1
                self._imageCount += 1
            else:
                # this is a text message part
                t = TextPart(startLocation=currentLocation, text=part)
                self._messageParts.append(t)
                currentLocation += len(part)
                hadText = True

        if len(messageParts) == 0:
            self._messageParts.append(TextPart(text=''))

        if self.item_type == 2:
            self._messageParts = []

        if self.text is not None:
            self.text = ''.join([text[t] for t in range(len(text))
                                 if (ord(text[t]) in range(65536)
                                     and ord(text[t]) != 65532)])

    @property
    def reactions(self) -> Dict[int, Dict[int, 'Reaction']]:
        return self._reactions

    def addAttachment(self, attachment: 'Attachment', ind: int) -> None:
        if attachment is not None:
            for i in range(len(self._messageParts)):
                if self._messageParts[i].kind == 'image':
                    if ind == 0:
                        self._messageParts[i].attachment = attachment
                    else:
                        ind -= 1

    @property
    def isReaction(self) -> bool:
        return False

    def getText(self) -> str:
        if self.item_type == 2:
            handleName = self.handleName if self.handle_id != 0 else "You"
            newName = self.group_title
            return '{} named the conversation "{}".'.format(handleName,
                                                            newName)
        if self._imageCount >= 1:
            return '{} attachments'.format(len(self.messageParts))
        elif self.text != '':
            return self.text
        else:
            return ''

    @property
    def messageParts(self) -> List['MessagePart']:
        return self._messageParts

    def addReaction(self, reaction: 'Reaction') -> None:

        ind = reaction.associated_message_range_location
        for part in self.messageParts:
            if part.startLocation == ind:
                part.addReaction(reaction)
                break

    def update(self, updatedMessage: 'Message') -> None:
        self.date = updatedMessage.date
        self.date_read = updatedMessage.date_read
        self.date_delivered = updatedMessage.date_delivered
        self.is_delivered = updatedMessage.is_delivered
        self.is_finished = updatedMessage.is_finished
        self.is_read = updatedMessage.is_read
        self.is_sent = updatedMessage.is_sent
        self.message_update_date = updatedMessage.message_update_date
        self.service = updatedMessage.service
        self.removedTempId = (updatedMessage.removedTempId if
                              self.removedTempId == 0 else self.removedTempId)


@dataclass
class MessagePart(ABC):
    _kind: str = None
    startLocation: int = 0

    def __post_init__(self):
        self._reactions = {}

    @property
    def kind(self):
        return self._kind

    @kind.setter
    def kind(self, _):
        raise CannotChangeKindException

    @property
    def reactions(self) -> Dict[int, Dict[int, 'Reaction']]:
        return self._reactions

    def addReaction(self, reaction: 'Reaction') -> None:
        # If the handle sending the reaction has not reacted to this message,
        # add it.
        if reaction.handleId not in self.reactions:
            self.reactions[reaction.handleId] = {}

        # Reactions and reaction removals have the same digit in the ones place
        reactionVal = reaction.reactionType % 1000

        # If the handle has already sent this reaction, but this one is newer,
        # replace the old reaction with this one.
        handleReactions = self.reactions[reaction.handleId]
        if (reactionVal in handleReactions and
                reaction.isNewer(handleReactions[reactionVal])):
            self.reactions[reaction.handleId][reactionVal] = reaction
        elif reactionVal not in handleReactions:
            self.reactions[reaction.handleId][reactionVal] = reaction


@dataclass
class TextPart(MessagePart):
    text: str = ''

    def __post_init__(self):
        super().__post_init__()
        self._kind = 'text'
        text = self.text
        if self.text is not None:
            self.text = ''.join([text[t] for t in range(len(text))
                                 if (ord(text[t]) in range(65536)
                                     and ord(text[t]) != 65532)])

    def getText(self) -> str:
        return self.text


@dataclass
class ImagePart(MessagePart):

    def __post_init__(self):
        super().__post_init__()
        self._kind = 'image'

    @property
    def attachment(self) -> 'Attachment':
        return self._attachment

    @attachment.setter
    def attachment(self, attachment: 'Attachment') -> None:
        self._attachment = attachment

    def getText(self) -> None:
        return None


@dataclass
class Reaction(Received):
    associated_message_id: int = None
    attachmentIndex: int = 0

    def __post_init__(self):
        super().__post_init__()
        if self.associated_message_id is None:
            raise ReactionNoAssociatedIdException
        if self.attachmentIndex is None:
            raise ReactionNoAttachmentIndexException

        text = self.text
        if self.text is not None:
            self.text = ''.join([text[t] for t in range(len(text))
                                 if (ord(text[t]) in range(65536)
                                     and ord(text[t]) != 65532)])

    @property
    def isAddition(self) -> bool:
        return self.associated_message_type < 3000

    @property
    def reactionType(self) -> int:
        return self.associated_message_type

    @property
    def associatedMessageId(self) -> int:
        return self.associated_message_id

    @property
    def isReaction(self) -> bool:
        return True

    def getText(self):
        return super().getText()


class DummyChat:
    def __init__(self, chatId: int) -> None:
        if chatId is None:
            raise ChatNoIdException
        self.chatId = chatId


@dataclass
class Chat:

    ROWID: int = None
    chat_identifier: str = None
    display_name: str = ''
    style: int = 0
    service_name: str = ''

    def __post_init__(self):

        if self.ROWID is None:
            raise ChatNoIdException

        self.messageList = MessageList()
        self.outgoingList = MessageList()
        self.lastAccessTime = 0
        self.localUpdate = False
        self.messagePreviewId = -1
        self.isTemporaryChat = False
        self.recipientList = []

    @property
    def chatId(self) -> int:
        return self.ROWID

    @property
    def serviceName(self) -> str:
        return self.service_name

    @property
    def chatIdentifier(self) -> str:
        return self.chat_identifier

    @property
    def displayName(self) -> str:
        return self.display_name

    @property
    def isiMessage(self) -> bool:
        if (self.serviceName == 'iMessage'):
            return True
        return False

    @property
    def isGroup(self) -> bool:
        if self.style == 43:
            return True
        return False

    def addRecipient(self, recipient: str) -> bool:
        return self.addRecipients([recipient])

    def addRecipients(self, recipients: List[str]) -> bool:
        allTrue = True
        if recipients:
            for recipient in recipients:
                allTrue = self._addRecipient(recipient) and allTrue
        return allTrue

    def _addRecipient(self, recipient: str) -> bool:
        if recipient:
            self.recipientList.append(recipient)
            return True
        return False

    def addMessage(
            self,
            message: 'Received',
            lastAccessTime: int = 0) -> None:
        self.addMessages([message], lastAccessTime)

    def addMessages(
            self,
            messageList: List['Received'],
            lastAccessTime: int = 0) -> None:
        for m in messageList:
            self._addMessage(m)
        if lastAccessTime > self.lastAccessTime:
            self.lastAccessTime = lastAccessTime

    def _addMessage(
            self,
            message: Optional['Received']) -> None:
        if message is None:
            pass
        elif message.isReaction:
            self.messageList.addReaction(message)
        else:
            self.messageList.append(message)
            if self.messageList.messages[message.rowid].isFromMe:
                self.removeTemporaryMessage(
                    self.messageList.messages[message.rowid])

    def removeTemporaryMessage(self, message: 'Received') -> None:
        self.messageList.writeLock.acquire()
        self.outgoingList.writeLock.acquire()
        idToDelete = 0
        for tempMsgId in self.outgoingList.messages:
            tempMsg = self.outgoingList.messages[tempMsgId]
            if (tempMsg.text == message.text and
                    message.removedTempId == 0 and
                    tempMsg.rowid != message.rowid):
                message.removedTempId = tempMsg.rowid
                del self.messageList.messages[tempMsgId]
                idToDelete = tempMsgId
                break
        if idToDelete != 0:
            del self.outgoingList.messages[idToDelete]
        self.messageList.writeLock.release()
        self.outgoingList.writeLock.release()

    def getName(self) -> str:
        if self.displayName:
            return ''.join([self.displayName[t] for t in
                            range(len(self.displayName)) if
                            ord(self.displayName[t]) in range(65536)])
        else:
            return ', '.join(self.recipientList)

    def getMessages(self) -> Dict[int, 'Received']:
        return self.messageList.messages

    def getMostRecentMessage(self) -> 'Received':
        return self.messageList.getMostRecentMessage()

    def sendMessage(
            self,
            mp: 'MessagePasser',
            messageText: str,
            recipientString: str) -> None:
        if recipientString == '' or recipientString is None:
            mp.sendMessage(self.chatId, messageText)
        else:
            mp.sendChat(recipientString, messageText)
        msg = Message(**{'ROWID': self.messagePreviewId,
                         'text': messageText, 'date':
                         int(time.time()), 'date_read': 0,
                         'is_delivered': 0, 'is_from_me': 1,
                         'service': 'iMessage'})
        self.messagePreviewId -= 1
        self.messageList.append(msg)
        self.outgoingList.append(msg)
        self.localUpdate = True

    def sendReaction(
            self,
            mp: 'MessagePasser',
            messageId: int,
            reactionType: int) -> None:
        mp.sendReaction(self.chatId, messageId, reactionType)


class MessageDatabase:

    def __init__(self):
        self.dbPath = dbPath
        self.conn = sqlite3.connect(self.dbPath)
        self.conn.row_factory = sqlite3.Row

    def getMessagesForChat(
            self,
            chatId: int,
            lastAccessTime: int = 0) -> Tuple[List['Received'], int]:
        messages = []
        tempLastAccess = lastAccessTime
        columns = self._getFormattedColumns()
        sql = sqlcommands.LOAD_MESSAGES_SQL.format(columns)
        cursor = self.conn.execute(sql, (chatId, tempLastAccess))

        for row in cursor:
            if row['message_update_date'] > tempLastAccess:
                tempLastAccess = row['message_update_date']

            message = self._parseMessage(row)

            handleName = self._getHandleName(row['handle_id'])
            if message is not None:
                message.handleName = handleName
                messages.append(message)

        lastAccessTime = max(lastAccessTime, tempLastAccess)
        return (messages, lastAccessTime)

    def getMostRecentMessage(self, chatId: int) -> Optional['Received']:
        cursor = self.conn.execute(sqlcommands.RECENT_MESSAGE_SQL, (chatId, ))
        for row in cursor:
            message = self._parseMessage(row)
            handleName = self._getHandleName(row['handle_id'])
            if message is not None:
                message.handleName = handleName
                return message
        return None

    def _parseMessage(self, row: sqlite3.Row) -> 'Message':

        message = None
        # If there are no associated messages
        if not row['associated_message_guid']:
            message = Message(**row)
            self._getAttachments(message)

        else:
            assocMessageId = (self.conn
                              .execute(sqlcommands.ASSOC_MESSAGE_SQL,
                                       (row['associated_message_guid']
                                           [-36:], )).fetchone())
            if assocMessageId:
                assocMessageId = assocMessageId[0]
                ind = self._getAttachmentIndex(row['associated_message_guid'])

                message = Reaction(associated_message_id=assocMessageId,
                                   attachmentIndex=ind, **row)

        return message

    def _getAttachmentIndex(self, associatedMessageGuid: str) -> int:
        match = re.match(r'[\w]+:((\d+)/)?.*', associatedMessageGuid)
        ind = int(match.group(2)) if match.group(2) is not None else None
        if ind is None:
            ind = 0
        return ind

    def _getAttachments(self, message: 'Received') -> None:
        cursor = self.conn.execute(
            sqlcommands.ATTACHMENTS_SQL, (message.rowid, ))
        count = 0
        for row in cursor:
            attachment = Attachment(**row)
            if attachment is not None:
                message.addAttachment(attachment, count)
                count += 1

    def _getHandleName(self, handleId: int) -> str:
        handleName = self.conn.execute(sqlcommands.HANDLE_SQL,
                                       (handleId, )).fetchone()
        if handleName:
            handleName = handleName[0]
        else:
            handleName = ''

        return handleName

    def _getFormattedColumns(self) -> str:
        neededColumnsMessage = ['ROWID', 'guid', 'text', 'handle_id',
                                'service', 'error', 'date', 'date_read',
                                'date_delivered', 'is_delivered',
                                'is_finished', 'is_from_me', 'is_read',
                                'is_sent', 'cache_has_attachments',
                                'cache_roomnames', 'item_type',
                                'other_handle', 'group_title',
                                'group_action_type', 'associated_message_guid',
                                'associated_message_type',
                                'message_update_date',
                                'associated_message_range_location',
                                'associated_message_range_length']
        columns = ', '.join(neededColumnsMessage)
        return columns

    def getRecipients(self, chatId: int) -> List[str]:
        cursor = self.conn.execute(sqlcommands.LOAD_RECIPIENTS_SQL, (chatId, ))
        recipients = []
        for recipient in cursor.fetchall():
            recipients.append(recipient[0])
        return recipients

    def getChat(self, chatId: int) -> Dict[str, Any]:
        cursor = self.conn.execute(sqlcommands.LOAD_CHAT_SQL,
                                   (chatId, ))
        row = cursor.fetchone()
        if row is None:
            raise ChatDeletedException

        return dict(row)

    def getChatsToUpdate(self,
                         lastAccessTime: int,
                         chats: Dict[int,
                                     'Chat'] = None) -> Tuple[List[int],
                                                              int]:
        if chats is None:
            chats = {}

        cursor = self.conn.execute(
            sqlcommands.CHATS_TO_UPDATE_SQL, (lastAccessTime, ))
        chatIds = []
        maxUpdate = lastAccessTime
        for row in cursor.fetchall():
            chatIds.append(row['chat_id'])
            if row['max(message_update_date)'] > maxUpdate:
                maxUpdate = row['max(message_update_date)']
        for _, chat in chats.items():
            if chat.localUpdate:
                chat.localUpdate = False
                if chat.chatId not in chatIds:
                    chatIds.append(chat.chatId)
        return chatIds, maxUpdate


class MessagePasser(ABC):

    @abstractmethod
    def sendMessage(self, chatId: int, messageText: str) -> None:
        pass

    @abstractmethod
    def sendChat(self, recipient_string: str, text: str) -> None:
        pass

    @abstractmethod
    def sendReaction(self, chatId: int, associated_guid: str,
                     associated_type: int) -> None:
        pass

    @abstractmethod
    def sendRename(self, chatId: int, group_title: str) -> None:
        pass


class HttpMessagePasser():

    class __HttpMessagePasser(MessagePasser):

        def connectionErrorDecorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.ConnectionError as e:
                    return False
            return wrapper

        @connectionErrorDecorator
        def sendMessage(self, chatId: int, messageText: str):
            data = {
                'chat_id': chatId,
                'text': messageText
            }
            r = requests.post('http://{}:3000/message'.format(ip), json=data)
            return r

        @connectionErrorDecorator
        def sendChat(self, recipient_string: str, text: str):
            data = {
                'recipient_string': recipient_string,
                'text': text
            }
            r = requests.post('http://{}:3000/chat'.format(ip), json=data)
            return r

        @connectionErrorDecorator
        def sendReaction(self, chatId: int, associated_guid: str,
                         associated_type: int):
            data = {
                'chat_id': chatId,
                'associated_guid': associated_guid,
                'associated_type': associated_type
            }
            r = requests.post('http://{}:3000/reaction'.format(ip), json=data)
            return r

        @connectionErrorDecorator
        def sendRename(self, chatId: int, group_title: str):
            data = {
                'chat_id': chatId,
                'group_title': group_title
            }
            r = requests.post('http://{}:3000/rename'.format(ip), json=data)
            return r

        @connectionErrorDecorator
        def ping(self) -> bool:
            r = requests.get('http://{}:3000/ping'.format(ip))
            return r.status_code == 200

    instance = None

    def __init__(self):
        if HttpMessagePasser.instance is None:
            HttpMessagePasser.instance = (HttpMessagePasser
                                          .__HttpMessagePasser())

    def __getattr__(self, name):
        return getattr(self.instance, name)


def createNewChat(chatId: int) -> 'Chat':
    chat = Chat(**{'ROWID': chatId})
    return chat


class ReceivedNoIdException(Exception):
    pass


class ReactionNoAssociatedIdException(Exception):
    pass


class AttachmentNoIdException(Exception):
    pass


class ChatDeletedException(Exception):
    pass


class ChatNoIdException(Exception):
    pass


class ReactionNoAttachmentIndexException(Exception):
    pass


class CannotChangeKindException(Exception):
    pass


def _useTestDatabase(dbName: str) -> None:
    global dbPath
    dbPath = dbName
