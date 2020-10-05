import sqlite3
import sys
import os
import json
from dotenv import load_dotenv


if len(sys.argv) != 2:
	print('Not enough args')
	exit(1)

load_dotenv()
CHAT_DB_PATH = os.getenv('CHAT_PATH')

conn = sqlite3.connect(CHAT_DB_PATH)

conn.row_factory = sqlite3.Row

cursor = conn.cursor()

# unix time 978307200 is 0 apple time
lastTime = sys.argv[1]

cursor.execute('select * from message inner join message_update_date_join inner join chat_message_join on message_update_date >= ? and message.ROWID = message_update_date_join.message_id and chat_message_join.message_id = message.ROWID left join message_attachment_join on ROWID = message_attachment_join.message_id', (lastTime, ))
messages = []

neededColumnsMessage = ['ROWID', 'guid', 'text', 'handle_id', 'service', 'error', 'date', 'date_read', 'date_delivered', 'is_delivered', 'is_finished', 'is_from_me', 'is_read', 'is_sent', 'cache_has_attachments', 'cache_roomnames', 'item_type', 'other_handle', 'group_title', 'group_action_type', 'associated_message_guid', 'associated_message_type', 'associated_message_range_location', 'associated_message_range_length']
neededColumnsAttachment = ['ROWID', 'guid', 'filename', 'uti']
neededColumnsChat = ['ROWID', 'guid', 'style', 'state', 'account_id', 'chat_identifier', 'service_name', 'room_name', 'account_login', 'display_name', 'group_id']
neededColumnsHandle = ['ROWID', 'id', 'country', 'service', 'uncanonicalized_id']

attachments = []
message_attachment_joins = []
chats = []
handles = []
chat_handle_joins = []
chat_message_joins = []

attachmentIdSet = set()
chatIdSet = set()
handleIdSet = set()

for row in cursor:
	message = {}
	for column in neededColumnsMessage:
		message[column] = row[column]
	message['date'] = message['date']//1000000000 + 978307200 if message['date'] != 0 else 0
	message['date_read'] = message['date_read']//1000000000 + 978307200 if message['date_read'] != 0 else 0
	message['date_delivered'] = message['date_delivered']//1000000000 + 978307200 if message['date_delivered'] != 0 else 0
	chat_message_joins.append({
		'message_id': row['ROWID'],
		'chat_id': row['chat_id']
		})
	if row['attachment_id'] != None:
		attachmentIdSet.add(row['attachment_id'])
		message_attachment_joins.append({
			'message_id': row['ROWID'],
			'attachment_id': row['attachment_id']
			})
	chatIdSet.add(row['chat_id'])
	handleIdSet.add(row['handle_id'])
	handleIdSet.add(row['other_handle'])

	messages.append(message)

for attachmentId in attachmentIdSet:
	attachment = {}
	row = cursor.execute('select * from attachment where ROWID = ?', (attachmentId, )).fetchone()
	if row:
		for column in neededColumnsAttachment:
			attachment[column] = row[column]
	attachments.append(attachment)

for chatId in chatIdSet:
	chat = {}
	row = cursor.execute('select * from chat where ROWID = ?', (chatId, )).fetchone()
	if row:
		for column in neededColumnsChat:
			chat[column] = row[column]
		row2 = cursor.execute('select ROWID from handle inner join chat_handle_join where handle.ROWID = chat_handle_join.handle_id and chat_handle_join.chat_id = ?', (chatId, ))
		for r in row2.fetchall():
			handleIdSet.add(r['ROWID'])
	chats.append(chat)

for handleId in handleIdSet:
	handle = {}
	rows = cursor.execute('select * from handle inner join chat_handle_join where chat_handle_join.handle_id = handle.ROWID and ROWID = ?', (handleId, )).fetchall()
	for row in rows:
		for column in neededColumnsHandle:
			handle[column] = row[column]
		chat_handle_joins.append({
			'handle_id': row['ROWID'],
			'chat_id': row['chat_id']
			})
	handles.append(handle)

response = {
	'attachment': attachments,
	'message_attachment_join': message_attachment_joins,
	'chat': chats,
	'handle': handles,
	'message': messages,
	'chat_handle_join': chat_handle_joins,
	'chat_message_join': chat_message_joins
}

print(json.dumps(response))
sys.stdout.flush()