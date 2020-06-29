import unittest
import sqlite3
import os
from localCode import api

class TestMessageDatabaseMethods(unittest.TestCase):

    def setUp(self):
        dbName = 'databases/testDb.db'
        dirname = os.path.dirname(__file__)
        self.dbPath = os.path.join(dirname, dbName)
        api._useTestDatabase(self.dbPath)

    def test_default_values(self):
        messageDb = api.MessageDatabase()

        self.assertEqual(messageDb.dbPath, self.dbPath)
        self.assertEqual(messageDb.conn.row_factory, sqlite3.Row)

    def test_get_messages_for_chat(self):
        messageDb = api.MessageDatabase()

        (msgs, lastAccessTime) = messageDb.getMessagesForChat(82, 0)

        self.assertEqual(msgs[0].ROWID, 12727)
        self.assertEqual(msgs[1].ROWID, 12732)
        self.assertEqual(lastAccessTime, 1590500766)
                                                              
