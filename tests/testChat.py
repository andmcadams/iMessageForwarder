import unittest
from localCode.messageApi import api

class TestChatMethods(unittest.TestCase):

    def test_default_values(self):
        chat = api.Chat(ROWID=1)

        self.assertEqual(chat.ROWID, 1)
        self.assertIsNone(chat.chat_identifier)
        self.assertEqual(chat.display_name, '')
        self.assertEqual(chat.style, 0)
        self.assertEqual(chat.service_name, '')

        self.assertIsInstance(chat.messageList, type(api.MessageList()))
        self.assertIsInstance(chat.outgoingList, type(api.MessageList()))
        self.assertEqual(chat.lastAccessTime, 0)
        self.assertFalse(chat.localUpdate)
        self.assertEqual(chat.messagePreviewId, -1)
        self.assertFalse(chat.isTemporaryChat)
        self.assertListEqual(chat.recipientList, [])

    def test_default_properties(self):
        chat = api.Chat(ROWID=1)

        self.assertEqual(chat.chatId, chat.ROWID)
        self.assertEqual(chat.serviceName, chat.service_name)
        self.assertEqual(chat.chatIdentifier, chat.chat_identifier)
        self.assertEqual(chat.displayName, chat.display_name)
        self.assertFalse(chat.isiMessage)
        self.assertFalse(chat.isGroup)

    def test_is_imessage(self):
        chat = api.Chat(ROWID=1, service_name='iMessage')

        self.assertTrue(chat.isiMessage)

    def test_is_group(self):
        chat = api.Chat(ROWID=1, style=43)

        self.assertTrue(chat.isGroup)

    def test_missing_rowid(self):
        with self.assertRaises(api.ChatNoIdException):
            api.Chat()

    def test_add_recipient(self):
        chat = api.Chat(ROWID=1)
        recipient = '+15555555555'

        returnVal = chat.addRecipient(recipient)

        self.assertListEqual(chat.recipientList, [recipient])
        self.assertTrue(returnVal)

    def test_add_recipients(self):
        chat = api.Chat(ROWID=1)
        recipients = ['+15555555555', 'testEmail@test.com']

        returnVal = chat.addRecipients(recipients)

        for recipient in recipients:
            self.assertIn(recipient, chat.recipientList)
        self.assertTrue(returnVal)


    def test_add_recipient_blank_recipient(self):
        chat = api.Chat(ROWID=1)
        recipient = ''

        returnVal = chat.addRecipient(recipient)

        self.assertListEqual(chat.recipientList, [])
        self.assertFalse(returnVal)

    def test_add_recipients_one_bad_recipient(self):
        chat = api.Chat(ROWID=1)
        recipients = ['', '+15555555555']

        returnVal = chat.addRecipients(recipients)

        self.assertListEqual(chat.recipientList, ['+15555555555'])
        self.assertFalse(returnVal)

    def test__add_recipient(self):
        chat = api.Chat(ROWID=1)
        recipient = '+15555555555'

        returnVal = chat._addRecipient(recipient)

        self.assertListEqual(chat.recipientList, [recipient])
        self.assertTrue(returnVal)

    def test__add_recipient_blank_recipient(self):
        chat = api.Chat(ROWID=1)
        recipient = ''

        returnVal = chat._addRecipient(recipient)

        self.assertListEqual(chat.recipientList, [])
        self.assertFalse(returnVal)

    def test_add_message(self):
        chat = api.Chat(ROWID=1)
        msg = api.Message(ROWID=1)
        correctMessageDict = {
            msg.ROWID: msg
        }

        chat.addMessage(msg)

        self.assertDictEqual(chat.messageList.messages, correctMessageDict)
        self.assertEqual(chat.lastAccessTime, 0)

    def test_add_message_with_update_time(self):
        chat = api.Chat(ROWID=1)
        msg = api.Message(ROWID=1)
        lastAccessTime = 1
        correctMessageDict = {
            msg.ROWID: msg
        }

        chat.addMessage(msg, lastAccessTime)

        self.assertDictEqual(chat.messageList.messages, correctMessageDict)
        self.assertEqual(chat.lastAccessTime, lastAccessTime)

    def test_add_messages(self):
        chat = api.Chat(ROWID=1)
        msg = api.Message(ROWID=1)
        msg2 = api.Message(ROWID=2)
        correctMessageDict = {
            msg.ROWID: msg,
            msg2.ROWID: msg2
        }

        chat.addMessages([msg, msg2])

        self.assertDictEqual(chat.messageList.messages, correctMessageDict)
        self.assertListEqual(list(chat.messageList.messages), list(correctMessageDict))
        self.assertEqual(chat.lastAccessTime, 0)

    def test_add_messages_with_update_time(self):
        chat = api.Chat(ROWID=1)
        msg = api.Message(ROWID=1)
        msg2 = api.Message(ROWID=2)
        lastAccessTime = 1
        correctMessageDict = {
            msg.ROWID: msg,
            msg2.ROWID: msg2
        }

        chat.addMessages([msg, msg2], lastAccessTime)

        self.assertDictEqual(chat.messageList.messages, correctMessageDict)
        self.assertListEqual(list(chat.messageList.messages), list(correctMessageDict))
        self.assertEqual(chat.lastAccessTime, lastAccessTime)

    def test__add_message_none(self):
        chat = api.Chat(ROWID=1)

        chat._addMessage(None)

        self.assertDictEqual(chat.messageList.messages, {})

    def test__add_message_reaction(self):
        chat = api.Chat(ROWID=1)
        msg = api.Message(ROWID=2)
        reaction = api.Reaction(ROWID=1, associated_message_id=2, handle_id=1, associated_message_type=2000)
        chat.addMessage(msg)
        correctReactionDict = {
            reaction.handle_id: {
                (reaction.associated_message_type % 1000): reaction
            }
        }
        
        chat._addMessage(reaction)

        self.assertDictEqual(chat.messageList.messages[msg.ROWID].messageParts[0].reactions, correctReactionDict)

    def test__add_message_message(self):
        chat = api.Chat(ROWID=1)
        msg = api.Message(ROWID=1)
        correctMessageDict = {
            msg.ROWID: msg
        }

        chat._addMessage(msg)

        self.assertDictEqual(chat.messageList.messages, correctMessageDict)

    def test__add_message_from_me(self):
        chat = api.Chat(ROWID=1)
        msg = api.Message(ROWID=1, is_from_me=1)
        correctMessageDict = {
            msg.ROWID: msg
        }

        chat._addMessage(msg)

        self.assertDictEqual(chat.messageList.messages, correctMessageDict)
        
    def test_remove_temporary_message(self):
        chat = api.Chat(ROWID=1)
        testText = 'Test text'
        tempMsg = api.Message(ROWID=-1, text=testText, is_from_me=1)
        chat.outgoingList.append(tempMsg)
        chat.addMessage(tempMsg)
        msg = api.Message(ROWID=1, text=testText, is_from_me=1)

        chat.removeTemporaryMessage(msg)

        self.assertDictEqual(chat.outgoingList.messages, {})
        self.assertDictEqual(chat.messageList.messages, {})

    def test_remove_temporary_message_wrong_text(self):
        chat = api.Chat(ROWID=1)
        testText = 'Test text'
        incorrectText = 'Bad text'
        tempMsg = api.Message(ROWID=-1, text=testText, is_from_me=1)
        chat.outgoingList.append(tempMsg)
        chat.addMessage(tempMsg)
        msg = api.Message(ROWID=1, text=incorrectText, is_from_me=1)
        correctMessageDict = {
            tempMsg.ROWID: tempMsg
        }

        chat.removeTemporaryMessage(msg)

        self.assertDictEqual(chat.outgoingList.messages, correctMessageDict)
        self.assertDictEqual(chat.messageList.messages, correctMessageDict)

    def test_remove_temporary_message_already_removed(self):
        chat = api.Chat(ROWID=1)
        testText = 'Test text'
        tempMsg = api.Message(ROWID=-2, text=testText, is_from_me=1)
        chat.outgoingList.append(tempMsg)
        chat.addMessage(tempMsg)
        msg = api.Message(ROWID=1, text=testText, is_from_me=1)
        msg.removedTempId = -1
        correctMessageDict = {
            tempMsg.ROWID: tempMsg
        }

        chat.removeTemporaryMessage(msg)

        self.assertDictEqual(chat.outgoingList.messages, correctMessageDict)
        self.assertDictEqual(chat.messageList.messages, correctMessageDict)

    def test_remove_temporary_message_same_message(self):
        chat = api.Chat(ROWID=1)
        testText = 'Test text'
        tempMsg = api.Message(ROWID=-2, text=testText, is_from_me=1)
        chat.outgoingList.append(tempMsg)
        chat.addMessage(tempMsg)
        correctMessageDict = {
            tempMsg.ROWID: tempMsg
        }

        chat.removeTemporaryMessage(tempMsg)

        self.assertDictEqual(chat.outgoingList.messages, correctMessageDict)
        self.assertDictEqual(chat.messageList.messages, correctMessageDict)

    def test_get_name_with_display_name(self):
        displayName = 'Test name'
        chat = api.Chat(ROWID=1, display_name=displayName)

        name = chat.getName()

        self.assertEqual(name, displayName)

    def test_get_name_no_display_name(self):
        chat = api.Chat(ROWID=1)

        name = chat.getName()

        self.assertEqual(name, '')

    def test_get_name_no_display_name_with_recipient(self):
        chat = api.Chat(ROWID=1)
        recipient = 'test recipient'
        chat.addRecipient(recipient)

        name = chat.getName()

        self.assertEqual(name, recipient)

    def test_get_name_no_display_name_with_recipients(self):
        chat = api.Chat(ROWID=1)
        recipients = ['test recipient {}'.format(i) for i in range(1,4)]
        chat.addRecipients(recipients)

        name = chat.getName()

        self.assertEqual(name, ', '.join(recipients))

    def test_get_name_display_name_with_emoji(self):
        displayName = 'Recipient 🍄 emoji'
        correctName = 'Recipient  emoji'
        chat = api.Chat(ROWID=1, display_name=displayName)

        name = chat.getName()

        self.assertEqual(name, correctName)

    def test_get_messages(self):
        chat = api.Chat(ROWID=1)
        msg = api.Message(ROWID=1, text='new text')
        chat.addMessage(msg)
        correctMessageDict = {
            msg.ROWID: msg
        }

        messages = chat.getMessages()

        self.assertDictEqual(messages, correctMessageDict)
        self.assertDictEqual(messages, chat.messageList.messages)

    def test_get_most_recent_message(self):
        chat = api.Chat(ROWID=1)
        msg = api.Message(ROWID=1, text='new text')
        chat.addMessage(msg)

        recentMessage = chat.getMostRecentMessage()

        self.assertEqual(recentMessage, msg)

    class StubMessagePasser(api.MessagePasser):

        def sendMessage(self, chatId, messageText, recipientString):
            pass

        def sendReaction(self, chatId, messageId, reactionType):
            pass

    def test_send_message(self):
        chat = api.Chat(ROWID=1)
        testText = 'Test text'
        recipient = '+15555555555'

        chat.sendMessage(self.StubMessagePasser(), testText, recipient)

        self.assertEqual(chat.messagePreviewId, -2)
        self.assertIn(-1, chat.messageList.messages)
        self.assertIn(-1, chat.outgoingList.messages)
        self.assertTrue(chat.localUpdate)

    def test_send_reaction(self):
        chat = api.Chat(ROWID=1)
        testMessageId = 1
        testReactionType = 2000

        chat.sendReaction(self.StubMessagePasser(), testMessageId, testReactionType)

        self.assertDictEqual(chat.messageList.messages, {})
        self.assertDictEqual(chat.outgoingList.messages, {})
