import sqlite3
import os
import json
import time


dbPath = 'sms.db'
conn = sqlite3.connect(dbPath)
conn.row_factory = sqlite3.Row

secrets = json.load(open('secrets.json'))
ip = secrets['ip']
scriptPath = secrets['scriptPath']
"""
MessageList needs to satisfy two major criteria:
	1. Easy lookup to find a message based on messageId (in order to update messages)
	2. Ordering based on date
1 allows O(1) time finding messages to update, which can be important if a user doesn't delete messages
2 allows sorting to happen at insertion in order to save time when printing messages and fetching older ones
Dictionary order is guaranteed in python 3.7+, so we will take advantage of that here
"""
class MessageList(dict):
	def __init__(self):
		self.messages = {}

	# Is this going to be faster than just sorting the entire thing every append?
	# Probably
	# The assumption is that messages probably will not need to be inserted back very far
	# requiring a much lower check than all n entries
	def append(self, message):
		updatedMessages = self.messages

		# If the message is just being updated, no need to worry about ordering
		# (assumption that date should never change)
		if message.attr['ROWID'] in updatedMessages:
			updatedMessages[message.attr['ROWID']] = message
		else:
			keys = list(updatedMessages)
			# Here we need to check the dates near the end of the dictionary
			# We assume that the dictionary will be sorted at this point by induction
			# Avoid using reverse here since it has complexity O(n)
			if keys:
				# Find first message older than the new message
				i = -1
				for i in range(-1, -len(keys)):
					if message.attr['date'] > updatedMessages[key].attr['date']:
						break
				# i contains the index that message should be inserted after
				# Note that if i == -1, we don't need to remove anything since -1 is the last index
				if i != -1:
					# Find the keys that will need to come after this new message
					keysToRemove = [k for k in keys[i+1:]]
					# Remove the keys, but save messages
					poppedMessages = []
					for key in keysToRemove:
						poppedMessages.append(updatedMessages.pop(key))
					# Add in the new message
					updatedMessages[message.attr['ROWID']] = message
					# Add back the messages we removed from the list
					for poppedMessage in poppedMessages:
						p = poppedMessages.pop()
						updatedMessages[p.attr['ROWID']] = p
				else:
					updatedMessages[message.attr['ROWID']] = message
			# If the list is empty we end up here
			else:
				updatedMessages[message.attr['ROWID']] = message
		self.messages = updatedMessages

class Message:

	def __init__(self, **kw):
		self.attr = {}
		for key, value in kw.items():
			self.attr[key] = value

		# This has to be done since tkinter only supports some unicode characters
		self.attr['text'] = None
		if kw['text'] != None:
			self.attr['text'] = ''.join([kw['text'][t] for t in range(len(kw['text'])) if ord(kw['text'][t]) in range(65536)])

		print('Created message with text "{}"'.format(self.attr['text']))

class DummyChat:
	def __init__(self, chatId):
		self.chatId = chatId

class Chat:

	def __init__(self, chatId, chatIdentifier, displayName):
		self.chatId = chatId
		self.chatIdentifier = chatIdentifier
		self.displayName = displayName
		# This should probably eventually be a list where the messages are in order
		self.messageList = MessageList()
		self.mostRecentMessage = self._getMostRecentMessage()
		self.recipientList = self._loadRecipients()
		self.lastAccess = 0

	def _loadRecipients(self):
		cursor = conn.execute('select id from handle inner join chat_handle_join on handle.ROWID = chat_handle_join.handle_id and chat_handle_join.chat_id = ?', (self.chatId, ))
		recipients = []
		for recipient in cursor.fetchall():
			recipients.append(recipient[0])
		return recipients

	def _getMostRecentMessage(self):
		cursor = conn.execute('select ROWID, handle_id, text, max(message.date), is_from_me from message inner join chat_message_join on message.ROWID = chat_message_join.message_id and chat_message_join.chat_id = ?', (self.chatId, ))
		m = cursor.fetchone()
		message = Message(**m)

		# If I can guarantee that self.messages[-1] is the most recent message, this can be a lot simpler
		return message
	
	def getName(self):
		if self.displayName:
			return self.displayName
		else:
			return self.chatIdentifier

	def getMessages(self):
		return self.messageList.messages

	def _loadMessages(self):
		# if self.messages is not none, we should just query for messages received after last message
		conn = sqlite3.connect(dbPath)
		conn.row_factory = sqlite3.Row
		tempLastAccess = self.lastAccess
		self.setAccessTime(int(time.time()))
		neededColumnsMessage = ['ROWID', 'guid', 'text', 'handle_id', 'service', 'error', 'date', 'date_read', 'date_delivered', 'is_delivered', 'is_finished', 'is_from_me', 'is_read', 'is_sent', 'cache_has_attachments', 'cache_roomnames', 'item_type', 'other_handle', 'group_title', 'group_action_type', 'associated_message_guid', 'associated_message_type']

		columns = ', '.join(neededColumnsMessage)
		sql = 'SELECT {} FROM message inner join chat_message_join on message.ROWID = chat_message_join.message_id and (date > ? or date_read > ? or date_delivered > ?) and chat_message_join.chat_id = ? '.format(columns)
		cursor = conn.execute(sql, (tempLastAccess,tempLastAccess, tempLastAccess, self.chatId))

		for row in cursor:
			message = Message(**row)
			self.messageList.append(message)

		conn.close()

	def sendMessage(self, messageText):
		messageText = messageText.replace('\"', '\\\"')
		cmd = "ssh root@{} \"python {} \\\"{}\\\" {}\"".format(ip, scriptPath, messageText, self.chatId)
		os.system(cmd)

	def setAccessTime(self, t):
		self.lastAccess = t - 978307400


def _loadChats():
	cursor = conn.execute('select ROWID, chat_identifier, display_name from chat')
	chats = []
	for row in cursor.fetchall():
		chat = Chat(row[0], row[1], row[2])
		if chat.mostRecentMessage.attr['ROWID'] != None:
			chats.append(chat)
	return chats

def _getChatsToUpdate(lastAccessTime):
	conn = sqlite3.connect(dbPath)
	conn.row_factory = sqlite3.Row
	sql = 'SELECT chat_id FROM message inner join chat_message_join on message.ROWID = chat_message_join.message_id and (date > ? or date_read > ? or date_delivered > ?)'
	cursor = conn.execute(sql, (lastAccessTime, lastAccessTime, lastAccessTime))
	chatIds = set()
	for row in cursor.fetchall():
		chatIds.add(row['chat_id'])
	conn.close()
	return chatIds
