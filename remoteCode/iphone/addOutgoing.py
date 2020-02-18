import sqlite3
import sys

if len(sys.argv) != 3:
	exit(1)

# Obviously not safe.
text = sys.argv[1]
chatId = sys.argv[2]

conn = sqlite3.connect('msgQueue.db')

conn.execute('insert into outgoing (text, chatId) values ( ?, ? )', text, chatId)