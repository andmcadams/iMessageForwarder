import sqlite3
import sys

if len(sys.argv) < 4:
	exit(1)

text, chatId, messageCode = sys.argv[1:4]
assocGUID = None
assocType = None
if len(sys.argv) > 4:
	assocGUID, assocType = sys.argv[4:]

conn = sqlite3.connect('/Users/andmcadams/Library/Messages/msgqueue.db')

conn.execute('insert into outgoing (text, chatId, assocGUID, assocType, messageCode) values ( ?, ?, ?, ?, ? )', (text, chatId, assocGUID, assocType, messageCode))
conn.commit()