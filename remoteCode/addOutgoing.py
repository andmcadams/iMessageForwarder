import sqlite3

conn = sqlite3.connect('msgQueue.db')

conn.execute('insert into outgoing (text, chatId) values ( ?, ? )', text, chatId)