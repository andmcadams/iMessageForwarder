import sqlite3

conn = sqlite3.connect('../messages/SMS/sms.db')


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
		if message.messageId in updatedMessages:
			updatedMessages[message.messageId] = message
		else:
			keys = list(updatedMessages)
			# Here we need to check the dates near the end of the dictionary
			# We assume that the dictionary will be sorted at this point by induction
			# Avoid using reverse here since it has complexity O(n)
			if keys:
				# Find first message older than the new message
				i = -1
				for i in range(-1, -len(keys)):
					if message.date > updatedMessages[key].date:
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
					updatedMessages[message.messageId] = message
					# Add back the messages we removed from the list
					for poppedMessage in poppedMessages:
						p = poppedMessages.pop()
						updatedMessages[p.messageId] = p
				else:
					updatedMessages[message.messageId] = message
			# If the list is empty we end up here
			else:
				updatedMessages[message.messageId] = message
		self.messages = updatedMessages

class Message:

	def __init__(self, messageId, handleId, text, date, isFromMe):
		self.messageId = messageId
		self.handleId = handleId

		self.date = date
		self.isFromMe = isFromMe

		# This has to be done since tkinter only supports some unicode characters
		self.text = None
		if text != None:
			self.text = ''.join([text[t] for t in range(len(text)) if ord(text[t]) in range(65536)])


class Chat:

	def __init__(self, chatId, chatIdentifier, displayName):
		self.chatId = chatId
		self.chatIdentifier = chatIdentifier
		self.displayName = displayName
		# This should probably eventually be a list where the messages are in order
		self.messageList = MessageList()
		self.mostRecentMessage = self._getMostRecentMessage()

	def _getMostRecentMessage(self):
		cursor = conn.execute('select ROWID, handle_id, text, max(message.date), is_from_me from message inner join chat_message_join on message.ROWID = chat_message_join.message_id and chat_message_join.chat_id = ?', (self.chatId, ))
		m = cursor.fetchone()
		message = Message(*m)

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
		cursor = conn.execute('select ROWID, handle_id, text, date, is_from_me from message inner join chat_message_join on message.ROWID = chat_message_join.message_id and chat_message_join.chat_id = ?', (self.chatId, ))
		for row in cursor:
			message = Message(*row)
			self.messageList.append(message)

def _loadChats():
	cursor = conn.execute('select ROWID, chat_identifier, display_name from chat')
	chats = []
	for row in cursor.fetchall():
		chat = Chat(row[0], row[1], row[2])
		if chat.mostRecentMessage.messageId != None:
			chats.append(chat)
	return chats