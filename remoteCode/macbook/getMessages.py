import sqlite3
import sys
import os
import simplejson as json


if len(sys.argv) != 2:
	print('Not enough args')
	exit(1)

dirname = os.path.dirname(__file__)
configFile = os.path.join(dirname, 'config.json')
config = json.load(open(configFile))
CHAT_DB_PATH = config['chatLocation']

lastTime = (int(sys.argv[1]) - 978307200)*1000000000

conn = sqlite3.connect(CHAT_DB_PATH)

conn.row_factory = sqlite3.Row

cursor = conn.cursor()

# unix time 978307200 is 0 apple time

cursor.execute('select * from message inner join chat_message_join where (date > ? or date_read > ? or date_delivered > ?) and message.ROWID = chat_message_join.message_id', (lastTime, lastTime, lastTime))
messages = []

neededColumnsMessage = ['ROWID', 'guid', 'text', 'handle_id', 'service', 'error', 'date', 'date_read', 'date_delivered', 'is_delivered', 'is_finished', 'is_from_me', 'is_read', 'is_sent', 'cache_has_attachments', 'cache_roomnames', 'item_type', 'other_handle', 'group_title', 'group_action_type', 'associated_message_guid', 'associated_message_type']
neededColumnsChat = ['ROWID', 'guid', 'style', 'state', 'account_id', 'chat_identifier', 'service_name', 'room_name', 'account_login', 'display_name', 'group_id']
neededColumnsHandle = ['ROWID', 'id', 'country', 'service', 'uncanonicalized_id']

chats = []
handles = []
chat_handle_joins = []
chat_message_joins = []

chatIdSet = set()
handleIdSet = set()

for row in cursor:
	message = {}
	for column in neededColumnsMessage:
		message[column] = row[column]
	message['date'] = message['date']//1000000000 + 978307200
	message['date_read'] = message['date_read']//1000000000 + 978307200
	message['date_delivered'] = message['date_delivered']//1000000000 + 978307200
	chat_message_joins.append({
		'message_id': row['ROWID'],
		'chat_id': row['chat_id']
		})
	chatIdSet.add(row['chat_id'])
	handleIdSet.add(row['handle_id'])
	handleIdSet.add(row['other_handle'])

	messages.append(message)

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
	'chat': chats,
	'handle': handles,
	'message': messages,
	'chat_handle_join': chat_handle_joins,
	'chat_message_join': chat_message_joins
}

print(json.dumps(response))
