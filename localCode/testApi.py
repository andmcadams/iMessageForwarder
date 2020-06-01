import unittest
import api

class TestMessageMethods(unittest.TestCase):

    def setUp(self):
        self.messageKw = {'ROWID': 581, 'guid': 'A153E7D9-8246-481C-96D4-4C15023658E1', 'text': 'This is some example text.', 'handle_id': 19, 'service': 'iMessage', 'error': 0, 'date': 1582434588, 'date_read': 0, 'date_delivered': 0, 'is_delivered': 1, 'is_finished': 1, 'is_from_me': 1, 'is_read': 0, 'is_sent': 1, 'cache_has_attachments': 0, 'cache_roomnames': None, 'item_type': 0, 'other_handle': 0, 'group_title': None, 'group_action_type': 0, 'associated_message_guid': None, 'associated_message_type': 0, 'attachment_id': None, 'message_update_date': 1584480798}
        self.reactionKw = {'ROWID': 627, 'guid': '3D8E90A2-B06A-44D1-BF62-F419320592A3', 'text': 'Loved “This is some example text.”', 'handle_id': 19, 'service': 'iMessage', 'error': 0, 'date': 1582480858, 'date_read': 978307200, 'date_delivered': 978307200, 'is_delivered': 1, 'is_finished': 1, 'is_from_me': 1, 'is_read': 0, 'is_sent': 1, 'cache_has_attachments': 0, 'cache_roomnames': None, 'item_type': 0, 'other_handle': 0, 'group_title': None, 'group_action_type': 0, 'associated_message_guid': 'p:0/495488E4-10A7-4BA2-A070-DE82AB2C2401', 'associated_message_type': 2000, 'attachment_id': None}


    # Test the creation of a message with no optional parameters.
    def test_basic_creation(self):
        msg = api.Message(**{'ROWID': 1})
        self.assertEqual(msg.attr, { 'ROWID': 1, 'text': None })
        self.assertEqual(msg.reactions, {})
        self.assertEqual(msg.attachment, None)
        self.assertEqual(msg.handleName, None)

    # Test that attempting to create a message without a 'ROWID' arg fails.
    def test_missing_rowid_creation(self):
        with self.assertRaises(api.MessageNoIdException):
            api.Message()

    # Test the creation of a message with only kw as an optional parameter (expanded).
    # The kw dictionary passed in should be the same as the message objects attr attribute.
    def test_kw_only(self):
        kw = {
            'ROWID': 1,
            'text': 'test',
            'a': 'a text',
            'b': 'b text',
            'c': 'c text'
        }
        msg = api.Message(**kw)
        self.assertEqual(msg.reactions, {})
        self.assertEqual(msg.attachment, None)
        self.assertEqual(msg.handleName, None)
        self.assertEqual(kw, msg.attr)

    # Test the creation of a message with an emoji in its text.
    # Due to tkinter issues, emojis cannot be properly displayed. Thus, they are removed from the text string.
    # They are retained in the local database.
    def test_text_with_emojis(self):
        kw = {
            'ROWID': 1,
            'text': 'This 🍄 is a mushroom'
        }
        msg = api.Message(**kw)
        self.assertEqual(msg.reactions, {})
        self.assertEqual(msg.attachment, None)
        self.assertEqual(msg.handleName, None)
        self.assertEqual('This  is a mushroom', msg.attr['text'])

    # Test the creation of a real message, similarly to how it is done in api.
    # The message is taken from a test db.
    def test_real_message(self):
        msg = api.Message(**self.messageKw)
        self.assertEqual(msg.reactions, {})
        self.assertEqual(msg.attachment, None)
        self.assertEqual(msg.handleName, None)
        self.assertEqual(self.messageKw, msg.attr)

    # Test the addition of a single reaction to a message.
    def test_add_reaction(self):
        msg = api.Message(**self.messageKw)
        reaction = api.Reaction(581, **self.reactionKw)
        msg.addReaction(reaction)

        self.assertEqual(msg.reactions, { 19: { 0: reaction }})

    # Test the addition of a reaction and its inverse reaction.
    # The reaction with the highest ROWID should be the current reaction as it (should be) the most recent.
    def test_add_multiple_reactions(self):
        reactionKw2 = {'ROWID': 628, 'guid': '3D8E90A2-B06A-44D1-BF62-F419320592A3', 'text': 'Removed a heart from “This is some example text.”', 'handle_id': 19, 'service': 'iMessage', 'error': 0, 'date': 1582480858, 'date_read': 978307200, 'date_delivered': 978307200, 'is_delivered': 1, 'is_finished': 1, 'is_from_me': 1, 'is_read': 0, 'is_sent': 1, 'cache_has_attachments': 0, 'cache_roomnames': None, 'item_type': 0, 'other_handle': 0, 'group_title': None, 'group_action_type': 0, 'associated_message_guid': 'p:0/495488E4-10A7-4BA2-A070-DE82AB2C2401', 'associated_message_type': 3000, 'attachment_id': None}
        msg = api.Message(**self.messageKw)
        reaction = api.Reaction(581, **self.reactionKw)
        reaction2 = api.Reaction(581, **reactionKw2)
        msg.addReaction(reaction)
        msg.addReaction(reaction2)

        self.assertEqual(msg.reactions, { 19: { 0: reaction2 }})

class TestReactionMethods(unittest.TestCase):

    def test_basic_creation(self):
        reaction = api.Reaction(1, **{'ROWID': 1})
        self.assertEqual(reaction.associatedMessageId, 1)
        self.assertEqual(reaction.attr, { 'ROWID': 1, 'text': None })
        self.assertEqual(reaction.handleName, None)

    def test_text_with_emojis(self):
        kw = {
            'ROWID': 1,
            'text': 'This 🍄 is a mushroom'
        }
        reaction = api.Reaction(1, **kw)
        self.assertEqual(reaction.associatedMessageId, 1)
        self.assertEqual(reaction.handleName, None)
        self.assertEqual(reaction.attr, { 'ROWID': 1, 'text': 'This  is a mushroom' })

    def test_real_reaction(self):
        kw = {'ROWID': 627, 'guid': '3D8E90A2-B06A-44D1-BF62-F419320592A3', 'text': 'Loved “Bye”', 'handle_id': 1, 'service': 'iMessage', 'error': 0, 'date': 1582480858, 'date_read': 978307200, 'date_delivered': 978307200, 'is_delivered': 1, 'is_finished': 1, 'is_from_me': 1, 'is_read': 0, 'is_sent': 1, 'cache_has_attachments': 0, 'cache_roomnames': None, 'item_type': 0, 'other_handle': 0, 'group_title': None, 'group_action_type': 0, 'associated_message_guid': 'p:0/495488E4-10A7-4BA2-A070-DE82AB2C2401', 'associated_message_type': 2000, 'attachment_id': None}
        reaction = api.Reaction(1, **kw)
        self.assertEqual(reaction.associatedMessageId, 1)
        self.assertEqual(reaction.handleName, None)
        self.assertEqual(reaction.attr, kw)

    def test_real_reaction_removal(self):
        kw = {'ROWID': 1393, 'guid': '7A291C84-F43E-4127-AC16-BD0BE4DBD7EC', 'text': 'Removed an exclamation from “..”', 'handle_id': 1, 'service': 'iMessage', 'error': 0, 'date': 1582726653, 'date_read': 1582726656, 'date_delivered': 0, 'is_delivered': 1, 'is_finished': 1, 'is_from_me': 0, 'is_read': 1, 'is_sent': 0, 'cache_has_attachments': 0, 'cache_roomnames': None, 'item_type': 0, 'other_handle': 0, 'group_title': None, 'group_action_type': 0, 'associated_message_guid': 'p:0/459BDF3C-599E-4A86-A6C5-76F6AF93BE65', 'associated_message_type': 3004, 'attachment_id': None}
        reaction = api.Reaction(1, **kw)
        self.assertEqual(reaction.associatedMessageId, 1)
        self.assertEqual(reaction.handleName, None)
        self.assertEqual(reaction.attr, kw)

class TestDummyChatMethods(unittest.TestCase):

    def test_basic_creation(self):
        dummyChat = api.DummyChat(1)
        self.assertEqual(dummyChat.chatId, 1)

class TestChatMethods(unittest.TestCase):

    def setUp(self):
        api._useTestDatabase('testDb.db')

    def test_real_chat_creation(self):
        chat = api.Chat(82, 'testEmail@test.com', None)
        self.assertEqual(chat.chatId, 82)
        self.assertEqual(chat.chatIdentifier, 'testEmail@test.com')
        self.assertEqual(chat.displayName, None)

    def test_chat_recipient_list(self):
        chat = api.Chat(82, 'testEmail@test.com', None)
        self.assertEqual(chat.recipientList, ['testEmail@test.com'])

    def test_chat_most_recent_message(self):
        chat = api.Chat(82, 'testEmail@test.com', None)
        self.assertEqual(chat.getMostRecentMessage().attr['ROWID'], 12732)

    # This chat has all messages that were received at seemingly the same time (due to rounding during conversion).
    # When there are multiple messages with the same date, they should be ordered by ROWID, with larger ROWID meaning more recent.
    def test_chat_most_recent_same_date(self):
        chat = api.Chat(85, "+15555555555", "")
        self.assertEqual(chat.getMostRecentMessage().attr['ROWID'], 13062)
        chat._loadMessages()
        self.assertEqual(chat.getMostRecentMessage().attr['ROWID'], 13062)
        # Extra checks to make sure that there haven't been any additions to the chat.
        self.assertEqual(len(list(chat.getMessages().keys())), 5)
        self.assertEqual(max(list(chat.getMessages().keys())), 13062)

    # This chat has a lot of messages received at the same time and one received slightly earlier that has the largest ROWID.
    # The most recent one should be the one with the largest datetime, and among those the one with the largest ROWID.
    # In this case, the message belonging to this chat with the largest ROWID is *not* the most recent message.
    def test_chat_most_recent_swapped_rowid(self):
        chat = api.Chat(86, "+15555555556", "")
        self.assertEqual(chat.getMostRecentMessage().attr['ROWID'], 13066)
        chat._loadMessages()
        self.assertEqual(chat.getMostRecentMessage().attr['ROWID'], 13066)
        # Extra checks to make sure that there haven't been any additions to the chat.
        self.assertEqual(len(list(chat.getMessages().keys())), 5)
        self.assertEqual(max(list(chat.getMessages().keys())), 13067)


    def test_chat_initial_message_list(self):
        chat = api.Chat(82, 'testEmail@test.com', None)
        self.assertEqual(len(chat.getMessages()), 1)
        self.assertEqual(list(chat.getMessages().keys()), [12732])

    def test_chat_after_message_load(self):
        chat = api.Chat(82, 'testEmail@test.com', None)
        self.assertEqual(len(chat.getMessages()), 1)
        self.assertEqual(list(chat.getMessages().keys()), [12732])
        chat._loadMessages()
        self.assertEqual(len(chat.getMessages()), 2)
        self.assertEqual(list(chat.getMessages().keys()), [12727, 12732])
        self.assertEqual(chat.getMostRecentMessage().attr['ROWID'], 12732)

    def test_chat_name(self):
        chat = api.Chat(82, 'testEmail@test.com', None)
        self.assertEqual(chat.getName(), 'testEmail@test.com')

    def test_chat_name_with_display_name(self):
        chat = api.Chat(82, 'testEmail@test.com', 'Group Message Name')
        self.assertEqual(chat.getName(), 'Group Message Name')
        
    def test_chat_name_with_emoji(self):
        chat = api.Chat(82, 'testEmail@test.com', 'Group Message 🍄 Name')
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
        reaction = api.Reaction(581, None, **reactionKw)
        msgList.append(msg)
        msgList.addReaction(reaction)
        self.assertEqual(msgList.getMostRecentMessage().attr['ROWID'], 628)
        self.assertEqual(len(list(msgList.messages.keys())), 1)

class TestAttachmentMethods(unittest.TestCase):

    def test_basic_creation(self):
        attachment = api.Attachment()
        self.assertEqual(attachment.attr, {})

if __name__ == '__main__':
    unittest.main()
