import unittest
import threading
from localCode.messageApi import api

class TestMessageListMethods(unittest.TestCase):

    def test_default_values(self):
        msgList = api.MessageList()

        self.assertDictEqual(msgList.messages, {})
        self.assertIsNone(msgList.mostRecentMessage)
        self.assertIsInstance(msgList.writeLock, type(threading.Lock()))

    def test_append_first_message(self):
        msgList = api.MessageList()
        message = api.Message(ROWID=1)
        correctMessagesDict = {
            message.ROWID: message
        }

        msgList.append(message)

        self.assertDictEqual(msgList.messages, correctMessagesDict)

    def test_append_same_message(self):
        msgList = api.MessageList()
        message = api.Message(ROWID=1)
        correctMessagesDict = {
            message.ROWID: message
        }

        msgList.append(message)
        msgList.append(message)

        self.assertDictEqual(msgList.messages, correctMessagesDict)

    def test_append_subsequent_message(self):
        msgList = api.MessageList()
        msg = api.Message(ROWID=1, date=10)
        msg2 = api.Message(ROWID=2, date=11)
        correctMessagesDict = {
            msg.ROWID: msg,
            msg2.ROWID: msg2
        }

        msgList.append(msg)
        msgList.append(msg2)

        self.assertDictEqual(msgList.messages, correctMessagesDict)
        self.assertListEqual(list(msgList.messages.keys()),
                             list(correctMessagesDict.keys()))
        self.assertEqual(msgList.mostRecentMessage, msg2)

    def test_append_prior_message(self):
        msgList = api.MessageList()
        msg = api.Message(ROWID=1, date=10)
        msg2 = api.Message(ROWID=2, date=11)
        correctMessagesDict = {
            msg.ROWID: msg,
            msg2.ROWID: msg2
        }

        msgList.append(msg2)
        msgList.append(msg)

        self.assertDictEqual(msgList.messages, correctMessagesDict)
        self.assertListEqual(list(msgList.messages.keys()),
                             list(correctMessagesDict.keys()))
        self.assertEqual(msgList.mostRecentMessage, msg2)

    def test_insert_subsequent_message(self):
        msgList = api.MessageList()
        msg = api.Message(ROWID=1, date=10)
        msg2 = api.Message(ROWID=2, date=11)
        correctMessagesDict = {
            msg.ROWID: msg,
            msg2.ROWID: msg2
        }
        msgList.append(msg)

        msgList._insert(msg2, msgList.messages, list(msgList))

        self.assertDictEqual(msgList.messages, correctMessagesDict)
        self.assertListEqual(list(msgList.messages.keys()),
                             list(correctMessagesDict.keys()))

    def test_insert_prior_message(self):
        msgList = api.MessageList()
        msg = api.Message(ROWID=1, date=10)
        msg2 = api.Message(ROWID=2, date=11)
        correctMessagesDict = {
            msg.ROWID: msg,
            msg2.ROWID: msg2
        }
        msgList.append(msg2)

        msgList._insert(msg, msgList.messages, list(msgList.messages))

        self.assertDictEqual(msgList.messages, correctMessagesDict)
        self.assertListEqual(list(msgList.messages.keys()),
                             list(correctMessagesDict.keys()))

    def test_add_reaction_with_message_in_list(self):
        msgList = api.MessageList()
        msg = api.Message(ROWID=1)
        reaction = api.Reaction(ROWID=2, associated_message_id=1, handle_id=1,
                associated_message_type=2000)
        msgList.append(msg)
        correctReactionDict = {
            reaction.handle_id: {
                (reaction.associated_message_type % 1000): reaction
            }
        }

        msgList.addReaction(reaction)

        self.assertEqual(msgList.messages[msg.ROWID].reactions,
                         correctReactionDict)

    def test_add_reaction_no_message_in_list(self):
        msgList = api.MessageList()
        reaction = api.Reaction(ROWID=2, associated_message_id=1, handle_id=1,
                associated_message_type=2000)

        msgList.addReaction(reaction)

        self.assertDictEqual(msgList.messages, {})

    def test_update_most_recent_message_first_message(self):
        msgList = api.MessageList()
        msg = api.Message(ROWID=1)

        msgList._updateMostRecentMessage(msg)

        self.assertEqual(msgList.mostRecentMessage, msg)

    def test_update_most_recent_message_new_message_replace(self):
        msgList = api.MessageList()
        msg = api.Message(ROWID=1, date=1)
        msg2 = api.Message(ROWID=1, date=2)
        msgList._updateMostRecentMessage(msg)

        msgList._updateMostRecentMessage(msg2)

        self.assertEqual(msgList.mostRecentMessage, msg2)

    def test_update_most_recent_message_new_message_no_replace(self):
        msgList = api.MessageList()
        msg = api.Message(ROWID=1, date=2)
        msg2 = api.Message(ROWID=1, date=1)
        msgList._updateMostRecentMessage(msg)

        msgList._updateMostRecentMessage(msg2)

        self.assertEqual(msgList.mostRecentMessage, msg)

    def test_get_most_recent_message(self):
        msgList = api.MessageList()
        msg = api.Message(ROWID=1)
        msgList.append(msg)

        mostRecent = msgList.getMostRecentMessage()

        self.assertEqual(mostRecent, msg)
