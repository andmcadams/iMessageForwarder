import unittest
import sqlite3
import os
from localCode.messageApi import api

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
        self.assertEqual(lastAccessTime, 1596330123)
        self.assertEqual(len(msgs[1].messageParts), 2)
        self.assertIsNotNone(msgs[1].messageParts[1].attachment)
        self.assertEqual(msgs[0].handleName, 'testEmail@test.com')

    def test_get_messages_for_chat_reaction(self):
        messageDb = api.MessageDatabase()

        (msgs, lastAccessTime) = messageDb.getMessagesForChat(87, 0)

        self.assertEqual(msgs[0].ROWID, 13068)
        self.assertTrue(msgs[0].isReaction)
        self.assertEqual(lastAccessTime, 1593473316)

    def test_get_most_recent_message(self):
        messageDb = api.MessageDatabase()

        msg = messageDb.getMostRecentMessage(82)

        self.assertEqual(msg.ROWID, 12732) 
        self.assertEqual(msg.handleName, 'testEmail@test.com')

    def test_get_most_recent_message_reaction(self):
        messageDb = api.MessageDatabase()

        msg = messageDb.getMostRecentMessage(87)

        self.assertEqual(msg.ROWID, 13068) 

    def test_get_most_recent_message_bad_chat(self):
        messageDb = api.MessageDatabase()

        msg = messageDb.getMostRecentMessage(1)

        self.assertIsNone(msg) 

    def test_get_attachment_index_p_str(self):
        associatedMessageGuid = 'p:1/B7E83654-FE3F-4D60-AA56-0D7E3704D5FF'
        messageDb = api.MessageDatabase()

        ind = messageDb._getAttachmentIndex(associatedMessageGuid)

        self.assertEqual(ind, 1)

    def test_get_attachment_index_bp_str(self):
        associatedMessageGuid = 'bp:D5A96C8F-D001-4BD4-A0D1-2539635BC92E'
        messageDb = api.MessageDatabase()

        ind = messageDb._getAttachmentIndex(associatedMessageGuid)

        self.assertEqual(ind, 0)

    def test_get_handle_name(self):
        messageDb = api.MessageDatabase()

        handle = messageDb._getHandleName(86)

        self.assertEqual(handle, 'testEmail@test.com')

    def test_get_handle_name_bad_handle(self):
        messageDb = api.MessageDatabase()

        handle = messageDb._getHandleName(1)

        self.assertEqual(handle, '')

    def test_get_formatted_columns(self):
        messageDb = api.MessageDatabase()
        correctColumns = ('ROWID, guid, text, handle_id, service, error, date,'
                          ' date_read, date_delivered, is_delivered,'
                          ' is_finished, is_from_me, is_read, is_sent,'
                          ' cache_has_attachments, cache_roomnames, item_type,'
                          ' other_handle, group_title, group_action_type,'
                          ' associated_message_guid, associated_message_type,'
                          ' message_update_date')

        cols = messageDb._getFormattedColumns()

        self.assertEqual(cols, correctColumns)

    def test_get_recipients(self):
        messageDb = api.MessageDatabase()

        recipients = messageDb.getRecipients(82)

        self.assertEqual(recipients, ['testEmail@test.com'])

    def test_get_chat(self):
        messageDb = api.MessageDatabase()
        correctChatDict = {
            'ROWID': 82,
            'chat_identifier': 'testEmail@test.com',
            'display_name': '',
            'service_name': 'iMessage',
            'style': 45
        }

        chatDict = messageDb.getChat(82)

        self.assertDictEqual(chatDict, correctChatDict)

    def test_get_chat_bad_rowid(self):
        messageDb = api.MessageDatabase()

        with self.assertRaises(api.ChatDeletedException):
            messageDb.getChat(1)

    def test_get_chats_to_update(self):
        messageDb = api.MessageDatabase()

        (chats, maxUpdate) = messageDb.getChatsToUpdate(0)

        self.assertEqual(maxUpdate, 1596330123)
        self.assertListEqual(chats, [82, 85, 86, 87])

    def test_get_chats_to_update_with_local_updates(self):
        messageDb = api.MessageDatabase()
        chat = api.Chat(ROWID=1)
        chat.localUpdate = True

        (chats, maxUpdate) = messageDb.getChatsToUpdate(0, {chat.ROWID: chat})

        self.assertEqual(maxUpdate, 1596330123)
        self.assertListEqual(chats, [82, 85, 86, 87, 1])
        self.assertFalse(chat.localUpdate)
