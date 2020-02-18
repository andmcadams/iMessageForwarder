import sqlite3
import sys
import os

dirname = os.path.dirname(__file__)
configFile = os.path.join(dirname, 'config.json')
config = json.load(open(configFile))
QUEUE_DB_PATH = config['queueLocation']

if len(sys.argv) < 4:
	exit(1)

text, chatId, messageCode = sys.argv[1:4]
assocGUID = None
assocType = None
if len(sys.argv) > 4:
	assocGUID, assocType = sys.argv[4:]

conn = sqlite3.connect(QUEUE_DB_PATH)

conn.execute('insert into outgoing (text, chatId, assocGUID, assocType, messageCode) values ( ?, ?, ?, ?, ? )', (text, chatId, assocGUID, assocType, messageCode))
conn.commit()