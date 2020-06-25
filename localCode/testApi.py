import unittest
from testHelperFunctions import MessageFactory
import api

class TestMessageMethods(unittest.TestCase):

    def setUp(self):
        self.messageKw = {'ROWID': 581, 'guid': 'A153E7D9-8246-481C-96D4-4C15023658E1', 'text': 'This is some example text.', 'handle_id': 19, 'service': 'iMessage', 'error': 0, 'date': 1582434588, 'date_read': 0, 'date_delivered': 0, 'is_delivered': 1, 'is_finished': 1, 'is_from_me': 1, 'is_read': 0, 'is_sent': 1, 'cache_has_attachments': 0, 'cache_roomnames': None, 'item_type': 0, 'other_handle': 0, 'group_title': None, 'group_action_type': 0, 'associated_message_guid': None, 'associated_message_type': 0, 'attachment_id': None, 'message_update_date': 1584480798}
        self.reactionKw = {'ROWID': 627, 'guid': '3D8E90A2-B06A-44D1-BF62-F419320592A3', 'text': 'Loved “This is some example text.”', 'handle_id': 19, 'service': 'iMessage', 'error': 0, 'date': 1582480858, 'date_read': 978307200, 'date_delivered': 978307200, 'is_delivered': 1, 'is_finished': 1, 'is_from_me': 1, 'is_read': 0, 'is_sent': 1, 'cache_has_attachments': 0, 'cache_roomnames': None, 'item_type': 0, 'other_handle': 0, 'group_title': None, 'group_action_type': 0, 'associated_message_guid': 'p:0/495488E4-10A7-4BA2-A070-DE82AB2C2401', 'associated_message_type': 2000, 'attachment_id': None}

    # Test that attempting to create a message without a 'ROWID' arg fails.
    def test_missing_rowid_creation(self):
        with self.assertRaises(api.ReceivedNoIdException):
            api.Message()

    # Test that attempting to create a message without a 'ROWID' arg fails.
    def test_missing_rowid_creation_with_other_info(self):
        with self.assertRaises(api.ReceivedNoIdException):
            api.Message(handle_id=5)

    # Test the creation of a message with no optional parameters.
    def test_basic_creation(self):
        msg = api.Message(ROWID=1)
        self.assertEqual(msg.rowid, 1)
        self.assertEqual(msg.reactions, {})
        self.assertEqual(msg.attachment, None)
        self.assertEqual(msg.isTemporary, False)
        self.assertEqual(msg.handleName, '')

    # Test the creation of a message with an emoji in its text.
    # Due to tkinter issues, emojis cannot be properly displayed. Thus, they are removed from the text string.
    # They are retained in the local database.
    def test_text_with_emojis(self):
        msg = api.Message(ROWID=1, text='This 🍄 is a mushroom')
        self.assertEqual('This  is a mushroom', msg.text)

    # Test the creation of a real message, similarly to how it is done in api.
    # The message is taken from a test db.
    def test_real_message(self):
        msg = api.Message(**self.messageKw)
        self.assertEqual(msg.reactions, {})
        self.assertEqual(msg.attachment, None)
        self.assertEqual(msg.isTemporary, False)
        self.assertEqual(msg.handleName, '')
        self.assertEqual(msg.dateRead, self.messageKw['date_read'])
        self.assertEqual(msg.isFromMe, True)
        self.assertEqual(msg.isDelivered, True)
        self.assertEqual(msg.isiMessage, True)
        self.assertEqual(msg.isTemporary, False)

        for k in self.messageKw.keys():
            self.assertEqual(msg.__dict__[k], self.messageKw[k])

    def test_temporary_message(self):
        msg = api.Message(ROWID=-1)
        self.assertEqual(msg.isTemporary, True)

    # Test the addition of a single reaction to a message.
    def test_add_reaction(self):
        msg = api.Message(ROWID=5)
        reaction = api.Reaction(associated_message_id=msg.rowid,
                                **self.reactionKw)
        msg.addReaction(reaction)
        self.assertEqual(reaction.associatedMessageId, msg.rowid)
        self.assertEqual(msg.reactions, { 19: { 0: reaction }})

    # Test the addition of a reaction and its inverse reaction.
    # The reaction with the highest ROWID should be the current reaction as it (should be) the most recent.
    def test_add_multiple_reactions(self):
        reactionKw2 = {'ROWID': 628, 'text': 'Removed a heart from “This is some example text.”', 'handle_id':
                self.reactionKw['handle_id'], 'date': 1582480858, 'date_read': 978307200, 'date_delivered': 978307200, 'is_from_me': 1, 'associated_message_guid': 'p:0/495488E4-10A7-4BA2-A070-DE82AB2C2401', 'associated_message_type': 3000}
        msg = api.Message(**self.messageKw)
        reaction = api.Reaction(associated_message_id=msg.rowid, **self.reactionKw)
        reaction2 = api.Reaction(associated_message_id=msg.rowid, **reactionKw2)
        msg.addReaction(reaction)
        msg.addReaction(reaction2)

        self.assertEqual(msg.reactions, { 19: { 0: reaction2 }})

class TestReactionMethods(unittest.TestCase):

    def test_missing_rowid(self):
        with self.assertRaises(api.ReceivedNoIdException):
            api.Reaction()

    def test_missing_associated_message_id(self):
        with self.assertRaises(api.ReactionNoAssociatedIdException):
            api.Reaction(ROWID=1)

    def test_basic_creation(self):
        reaction = api.Reaction(ROWID=1, associated_message_id=1)
        self.assertEqual(reaction.associatedMessageId, 1)
        self.assertEqual(reaction.rowid, 1)

    def test_text_with_emojis(self):
        reaction = api.Reaction(ROWID=1, text='This 🍄 is a mushroom',
                                associated_message_id=1)
        self.assertEqual(reaction.associatedMessageId, 1)
        self.assertEqual(reaction.rowid, 1)
        self.assertEqual(reaction.text, 'This  is a mushroom')

    def test_real_reaction(self):
        kw = {'ROWID': 627, 'guid': '3D8E90A2-B06A-44D1-BF62-F419320592A3', 'text': 'Loved “Bye”', 'handle_id': 1, 'service': 'iMessage', 'error': 0, 'date': 1582480858, 'date_read': 978307200, 'date_delivered': 978307200, 'is_delivered': 1, 'is_finished': 1, 'is_from_me': 1, 'is_read': 0, 'is_sent': 1, 'cache_has_attachments': 0, 'cache_roomnames': None, 'item_type': 0, 'other_handle': 0, 'group_title': None, 'group_action_type': 0, 'associated_message_guid': 'p:0/495488E4-10A7-4BA2-A070-DE82AB2C2401', 'associated_message_type': 2000, 'attachment_id': None}
        reaction = api.Reaction(associated_message_id=1, **kw)
        self.assertEqual(reaction.associatedMessageId, 1)
        self.assertEqual(reaction.rowid, 627)
        self.assertEqual(reaction.isAddition, True)
        self.assertEqual(reaction.isiMessage, True)
        self.assertEqual(reaction.reactionType, 2000)

    def test_real_reaction_removal(self):
        kw = {'ROWID': 1393, 'guid': '7A291C84-F43E-4127-AC16-BD0BE4DBD7EC', 'text': 'Removed an exclamation from “..”', 'handle_id': 1, 'service': 'iMessage', 'error': 0, 'date': 1582726653, 'date_read': 1582726656, 'date_delivered': 0, 'is_delivered': 1, 'is_finished': 1, 'is_from_me': 0, 'is_read': 1, 'is_sent': 0, 'cache_has_attachments': 0, 'cache_roomnames': None, 'item_type': 0, 'other_handle': 0, 'group_title': None, 'group_action_type': 0, 'associated_message_guid': 'p:0/459BDF3C-599E-4A86-A6C5-76F6AF93BE65', 'associated_message_type': 3004, 'attachment_id': None}
        reaction = api.Reaction(associated_message_id=1, **kw)
        self.assertEqual(reaction.associatedMessageId, 1)
        self.assertEqual(reaction.isAddition, False)
        self.assertEqual(reaction.reactionType, 3004)

class TestDummyChatMethods(unittest.TestCase):

    def test_basic_creation(self):
        dummyChat = api.DummyChat(1)
        self.assertEqual(dummyChat.chatId, 1)

class TestChatMethods(unittest.TestCase):

    def setUp(self):
        api._useTestDatabase('testing/databases/testDb.db')

    def test_real_chat_creation(self):
        chat = api.Chat(**{'ROWID': 82, 'chat_identifier': 'testEmail@test.com', 'display_name': None, 'style': 43})
        self.assertEqual(chat.chatId, 82)
        self.assertEqual(chat.chatIdentifier, 'testEmail@test.com')
        self.assertEqual(chat.displayName, None)

    def test_chat_recipient_list(self):
        chat = api.Chat(**{'ROWID': 82, 'chat_identifier': 'testEmail@test.com', 'display_name': None, 'style': 43})
        self.assertEqual(chat.recipientList, ['testEmail@test.com'])

    def test_chat_most_recent_message(self):
        chat = api.Chat(**{'ROWID': 82, 'chat_identifier': 'testEmail@test.com', 'display_name': None, 'style': 43})
        self.assertEqual(chat.getMostRecentMessage().rowid, 12732)

    # This chat has all messages that were received at seemingly the same time (due to rounding during conversion).
    # When there are multiple messages with the same date, they should be ordered by ROWID, with larger ROWID meaning more recent.
    def test_chat_most_recent_same_date(self):
        chat = api.Chat(**{'ROWID': 85, 'chat_identifier': "+15555555555",
            'display_name': None, 'style': 43})
        self.assertEqual(chat.getMostRecentMessage().rowid, 13062)
        db = api.MessageDatabase()
        messageList, lastAccessTime = db.getMessagesForChat(chat.chatId, chat.lastAccessTime)
        chat.addMessages(messageList, lastAccessTime)
        self.assertEqual(chat.getMostRecentMessage().rowid, 13062)
        # Extra checks to make sure that there haven't been any additions to the chat.
        self.assertEqual(len(list(chat.getMessages().keys())), 5)
        self.assertEqual(max(list(chat.getMessages().keys())), 13062)

    # This chat has a lot of messages received at the same time and one received slightly earlier that has the largest ROWID.
    # The most recent one should be the one with the largest datetime, and among those the one with the largest ROWID.
    # In this case, the message belonging to this chat with the largest ROWID is *not* the most recent message.
    def test_chat_most_recent_swapped_rowid(self):
        chat = api.Chat(**{'ROWID': 86, 'chat_identifier': "+15555555556",
            'display_name': None, 'style': 43})
        self.assertEqual(chat.getMostRecentMessage().rowid, 13066)
        db = api.MessageDatabase()
        messageList, lastAccessTime = db.getMessagesForChat(chat.chatId, chat.lastAccessTime)
        chat.addMessages(messageList, lastAccessTime)
        self.assertEqual(chat.getMostRecentMessage().rowid, 13066)
        # Extra checks to make sure that there haven't been any additions to the chat.
        self.assertEqual(len(list(chat.getMessages().keys())), 5)
        self.assertEqual(max(list(chat.getMessages().keys())), 13067)


    def test_chat_initial_message_list(self):
        chat = api.Chat(**{'ROWID': 82, 'chat_identifier': 'testEmail@test.com', 'display_name': None, 'style': 43})
        self.assertEqual(len(chat.getMessages()), 1)
        self.assertEqual(list(chat.getMessages().keys()), [12732])

    def test_chat_after_message_load(self):
        chat = api.Chat(**{'ROWID': 82, 'chat_identifier': 'testEmail@test.com', 'display_name': None, 'style': 43})
        self.assertEqual(len(chat.getMessages()), 1)
        self.assertEqual(list(chat.getMessages().keys()), [12732])
        db = api.MessageDatabase()
        messageList, lastAccessTime = db.getMessagesForChat(chat.chatId, chat.lastAccessTime)
        chat.addMessages(messageList, lastAccessTime)
        self.assertEqual(len(chat.getMessages()), 2)
        self.assertEqual(list(chat.getMessages().keys()), [12727, 12732])
        self.assertEqual(chat.getMostRecentMessage().rowid, 12732)

    def test_chat_name(self):
        chat = api.Chat(**{'ROWID': 82, 'chat_identifier': 'testEmail@test.com', 'display_name': None, 'style': 43})
        self.assertEqual(chat.getName(), 'testEmail@test.com')

    def test_chat_name_with_display_name(self):
        chat = api.Chat(**{'ROWID': 82, 'chat_identifier':
            'testEmail@test.com', 'display_name': 'Group Message Name', 'style': 43})
        self.assertEqual(chat.getName(), 'Group Message Name')
        
    def test_chat_add_recipient(self):
        chat = api.Chat(**{'ROWID': 82, 'chat_identifier': 'testEmail@test.com', 'display_name': None, 'style': 43})
        returnVal = chat.addRecipient('testEmail2@test.com')
        self.assertTrue(returnVal)
        self.assertTrue('testEmail2@test.com' in chat.recipientList)
        self.assertEqual('testEmail@test.com, testEmail2@test.com',
                chat.getName())

    def test_chat_add_recipient(self):
        chat = api.Chat(**{'ROWID': 82, 'chat_identifier': 'testEmail@test.com', 'display_name': None, 'style': 43})
        for name in ['testEmail2@test.com', 'testEmail3@test.com']:
            returnVal = chat.addRecipient(name)
            self.assertTrue(returnVal)
            self.assertTrue(name in chat.recipientList)
        self.assertEqual('testEmail@test.com, testEmail2@test.com, testEmail3@test.com', chat.getName())

    def test_chat_add_blank_recipient(self):
        chat = api.Chat(**{'ROWID': 82, 'chat_identifier': 'testEmail@test.com', 'display_name': None, 'style': 43})
        returnVal = chat.addRecipient('')
        self.assertFalse(returnVal)
        self.assertEqual('testEmail@test.com', chat.getName())

    def test_chat_name_with_emoji(self):
        chat = api.Chat(**{'ROWID': 82, 'chat_identifier':
            'testEmail@test.com', 'display_name': 'Group Message 🍄 Name', 'style': 43})
        self.assertEqual(chat.getName(), 'Group Message  Name')
        
class TestMessageListMethods(unittest.TestCase):

    def test_basic_creation(self):
        msgList = api.MessageList()
        self.assertEqual(msgList.messages, {})
        self.assertEqual(msgList.getMostRecentMessage(), None)

    def test_addition(self):
        messageKw = {'ROWID': 581, 'guid': 'A153E7D9-8246-481C-96D4-4C15023658E1', 'text': 'This is some example text.', 'handle_id': 19, 'service': 'iMessage', 'error': 0, 'date': 1582434588, 'date_read': 0, 'date_delivered': 0, 'is_delivered': 1, 'is_finished': 1, 'is_from_me': 1, 'is_read': 0, 'is_sent': 1, 'cache_has_attachments': 0, 'cache_roomnames': None, 'item_type': 0, 'other_handle': 0, 'group_title': None, 'group_action_type': 0, 'associated_message_guid': None, 'associated_message_type': 0, 'attachment_id': None, 'message_update_date': 1584480798}
        messageKw2 = {'ROWID': 582, 'guid': 'B153E7D9-8246-481C-96D4-4C15023658E1', 'text': 'This is some more example text.', 'handle_id': 19, 'service': 'iMessage', 'error': 0, 'date': 1582434598, 'date_read': 0, 'date_delivered': 0, 'is_delivered': 1, 'is_finished': 1, 'is_from_me': 1, 'is_read': 0, 'is_sent': 1, 'cache_has_attachments': 0, 'cache_roomnames': None, 'item_type': 0, 'other_handle': 0, 'group_title': None, 'group_action_type': 0, 'associated_message_guid': None, 'associated_message_type': 0, 'attachment_id': None, 'message_update_date': 1584480798}
        msgList = api.MessageList()
        msg = api.Message(**messageKw)
        msg2 = api.Message(**messageKw2)
        msgList.append(msg)
        msgList.append(msg2)
        self.assertEqual(list(msgList.messages.keys()), [581, 582])
        self.assertEqual(msgList.getMostRecentMessage(), msg2)
        
    def test_reaction_addition(self):
        messageKw = {'ROWID': 581, 'guid': 'A153E7D9-8246-481C-96D4-4C15023658E1', 'text': 'This is some example text.', 'handle_id': 19, 'service': 'iMessage', 'error': 0, 'date': 1582434588, 'date_read': 0, 'date_delivered': 0, 'is_delivered': 1, 'is_finished': 1, 'is_from_me': 1, 'is_read': 0, 'is_sent': 1, 'cache_has_attachments': 0, 'cache_roomnames': None, 'item_type': 0, 'other_handle': 0, 'group_title': None, 'group_action_type': 0, 'associated_message_guid': None, 'associated_message_type': 0, 'attachment_id': None, 'message_update_date': 1584480798}
        reactionKw = {'ROWID': 628, 'guid': '3D8E90A2-B06A-44D1-BF62-F419320592A3', 'text': 'Loved “This is some example text.”', 'handle_id': 19, 'service': 'iMessage', 'error': 0, 'date': 1582480858, 'date_read': 978307200, 'date_delivered': 978307200, 'is_delivered': 1, 'is_finished': 1, 'is_from_me': 1, 'is_read': 0, 'is_sent': 1, 'cache_has_attachments': 0, 'cache_roomnames': None, 'item_type': 0, 'other_handle': 0, 'group_title': None, 'group_action_type': 0, 'associated_message_guid': 'p:0/4A153E7D9-8246-481C-96D4-4C15023658E1', 'associated_message_type': 2000, 'attachment_id': None}
        msgList = api.MessageList()
        msg = api.Message(**messageKw)
        reaction = api.Reaction(associated_message_id=581, **reactionKw)
        msgList.append(msg)
        msgList.addReaction(reaction)
        self.assertEqual(msgList.getMostRecentMessage().rowid, 628)
        self.assertEqual(len(list(msgList.messages.keys())), 1)

class TestAttachmentMethods(unittest.TestCase):

    def test_basic_creation(self):
        attachment = api.Attachment(ROWID=1)
        self.assertEqual(attachment.rowid, 1)

    def test_missing_rowid(self):
        with self.assertRaises(api.AttachmentNoIdException):
            api.Attachment()

class TestMessageDatabaseMethods(unittest.TestCase):

    def test_get_messages_for_chat(self):
        api._useTestDatabase('testing/databases/testDb.db')
        chat = api.Chat(**{'ROWID': 82, 'chat_identifier': 'testEmail@test.com', 'display_name': None, 'style': 43})
        db = api.MessageDatabase()
        messages, lastAccessTime = db.getMessagesForChat(chat.chatId, chat.lastAccessTime)
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].rowid, 12727)
        self.assertEqual(messages[1].rowid, 12732)
        self.assertEqual(lastAccessTime, 1590500766)


if __name__ == '__main__':
    unittest.main()
