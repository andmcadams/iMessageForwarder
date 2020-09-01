import unittest
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from localCode.messageApi import api
from localCode import messageframe as mf

class TestMessageFrameMethods(unittest.TestCase):

    def setUp(self):
        self.mp = api.SshMessagePasser(0)
        self.messageFrame = mf.MessageFrame(None, 0, 0, self.mp, api.MessageDatabase)

    def test_basic_creation(self):
        self.assertEqual(self.messageFrame.messageBubbles, {})
        self.assertEqual(self.messageFrame.messageLimit, 15)
        self.assertEqual(self.messageFrame.addedMessages, False)
        self.assertEqual(self.messageFrame.readReceiptMessageId, None)
        self.assertEqual(self.messageFrame.mp, self.mp)

    def test_check_scroll_no_load(self):
        self.messageFrame.checkScroll(0, 1)

        self.assertFalse(self.messageFrame.addedMessages)
        self.assertEqual(self.messageFrame.messageLimit, 15)
    
    # changeChat hits master in addMessages
    def test_change_chat(self):
        chat = api.Chat(ROWID=1)
        
        self.messageFrame.changeChat(chat)

        self.assertDictEqual(self.messageFrame.messageBubbles, {})
        self.assertEqual(self.messageFrame.messageLimit, 15)
        self.assertEqual(self.messageFrame.currentChat, chat)
        self.assertEqual(id(self.messageFrame.currentChat), id(chat))

    # Need slightly more complex logic for when to use sender labels
    # (label showing who the sender is)
    # addLabel is True iff
    # 1) This is a group message
    # 2) The sender of this message is not the same as the last sender
    # 3) The sender of the message is not me

    def test_need_sender_label_basic(self):
        chat = api.Chat(ROWID=1, chat_identifier='testEmail@test.com',
                        display_name=None, style=43)
        msg = api.Message(ROWID=1, is_from_me=0, service='iMessage',
                          handle_id=1)
        prevMsg = api.Message(ROWID=2, is_from_me=1, service='iMessage',
                              handle_id=0)

        result = self.messageFrame.needSenderLabel(chat, msg, prevMsg)

        self.assertTrue(result)

    def test_need_sender_label_not_group(self):
        chat = api.Chat(ROWID=1, chat_identifier='testEmail@test.com',
                        display_name=None, style=45)
        msg = api.Message(ROWID=1, is_from_me=0, service='iMessage',
                          handle_id=1)
        prevMsg = api.Message(ROWID=2, is_from_me=1, service='iMessage',
                              handle_id=0)

        result = self.messageFrame.needSenderLabel(chat, msg, prevMsg)

        self.assertFalse(result)

    def test_need_sender_label_from_me(self):
        chat = api.Chat(ROWID=1, chat_identifier='testEmail@test.com',
                        display_name=None, style=43)
        msg = api.Message(ROWID=1, is_from_me=1, service='iMessage',
                          handle_id=1)
        prevMsg = api.Message(ROWID=2, is_from_me=1, service='iMessage',
                              handle_id=0)

        result = self.messageFrame.needSenderLabel(chat, msg, prevMsg)

        self.assertFalse(result)

    def test_need_sender_label_no_previous_message(self):
        chat = api.Chat(ROWID=1, chat_identifier='testEmail@test.com',
                        display_name=None, style=43)
        msg = api.Message(ROWID=1, is_from_me=0, service='iMessage',
                          handle_id=1)
        prevMsg = None

        result = self.messageFrame.needSenderLabel(chat, msg, prevMsg)

        self.assertTrue(result)

    def test_need_sender_label_handles_equal(self):
        chat = api.Chat(ROWID=1, chat_identifier='testEmail@test.com',
                        display_name=None, style=43)
        msg = api.Message(ROWID=1, is_from_me=0, service='iMessage',
                          handle_id=1)
        prevMsg = api.Message(ROWID=2, is_from_me=1, service='iMessage',
                              handle_id=1)

        result = self.messageFrame.needSenderLabel(chat, msg, prevMsg)

        self.assertFalse(result)

    def test_need_time_label_is_temporary(self):
        msg = api.Message(ROWID=-1)
        prevMsg = api.Message(ROWID=1)

        result = self.messageFrame.needTimeLabel(msg, prevMsg)

        self.assertFalse(result)

    def test_need_time_label_no_previous_message(self):
        msg = api.Message(ROWID=1)
        prevMsg = None

        result = self.messageFrame.needTimeLabel(msg, prevMsg)

        self.assertTrue(result)

    def test_need_time_label_time_diff_lt_threshold(self):
        msg = api.Message(ROWID=2, date=20)
        prevMsg = api.Message(ROWID=1, date=18)

        result = self.messageFrame.needTimeLabel(msg, prevMsg)

        self.assertFalse(result)

    def test_need_time_label_time_diff_gt_threshold(self):
        date = 5
        thresholdTime = 60 * 15
        msg = api.Message(ROWID=2, date=(date + thresholdTime + 1))
        prevMsg = api.Message(ROWID=1, date=date)

        result = self.messageFrame.needTimeLabel(msg, prevMsg)

        self.assertTrue(result)

    def test_create_time_label_today(self):
        t = datetime.now() - timedelta(hours=2)
        correctText = mf.getTimeText(t.timestamp())

        timeLabel = self.messageFrame.createTimeLabel(t.timestamp())
        children = self.messageFrame.interior.winfo_children()

        self.assertEqual(len(children), 1)
        self.assertEqual(timeLabel.label.cget('text'), correctText)

    def test_create_time_label_yesterday(self):
        t = datetime.now() - timedelta(days=1)
        correctText = mf.getTimeText(t.timestamp())

        timeLabel = self.messageFrame.createTimeLabel(t.timestamp())
        children = self.messageFrame.interior.winfo_children()

        self.assertEqual(len(children), 1)
        self.assertEqual(timeLabel.label.cget('text'), correctText)

    def test_create_time_label_multiple_days_back(self):
        t = datetime.now() - timedelta(days=10)
        correctText = mf.getTimeText(t.timestamp())

        timeLabel = self.messageFrame.createTimeLabel(t.timestamp())
        children = self.messageFrame.interior.winfo_children()

        self.assertEqual(len(children), 1)
        self.assertEqual(timeLabel.label.cget('text'), correctText)

    def test_need_read_receipt_temporary_from_me(self):
        msg = api.Message(ROWID=-1, is_from_me=1)

        result = self.messageFrame.needReadReceipt(None, msg, None)

        self.assertTrue(result)

    def test_need_read_receipt_not_from_me(self):
        msg = api.Message(ROWID=1, is_from_me=0)
        
        result = self.messageFrame.needReadReceipt(None, msg, None)

        self.assertFalse(result)

    def test_need_read_receipt_is_group(self):
        msg = api.Message(ROWID=1, is_from_me=0)
        chat = api.Chat(ROWID=1, style=43)
        
        result = self.messageFrame.needReadReceipt(chat, msg, None)

        self.assertTrue(chat.isGroup)
        self.assertFalse(result)

    def test_need_read_receipt_not_imessage(self):
        msg = api.Message(ROWID=1, is_from_me=1, service='SMS')
        chat = api.Chat(ROWID=1)
        
        result = self.messageFrame.needReadReceipt(chat, msg, None)

        self.assertFalse(msg.isiMessage)
        self.assertFalse(result)

    def test_need_read_receipt_not_last_from_me(self):
        msg = api.Message(ROWID=1, is_from_me=1, service='iMessage')
        chat = api.Chat(ROWID=1)
        
        result = self.messageFrame.needReadReceipt(chat, msg, msg.rowid + 1)

        self.assertFalse(result)

    def test_need_read_receipt_from_me_not_group_imessage_last_from_me(self):
        msg = api.Message(ROWID=1, is_from_me=1, service='iMessage')
        chat = api.Chat(ROWID=1)
        
        result = self.messageFrame.needReadReceipt(chat, msg, msg.rowid)

        self.assertTrue(result)

    def test_remove_old_read_receipt(self):
        msg = api.Message(ROWID=1, guid='ABC', is_from_me=1, service='iMessage')
        chat = api.Chat(ROWID=1)
        chat.addMessage(msg)
        self.messageFrame.addMessage(chat, 0, msg, None, 1)
        result = self.messageFrame.needReadReceipt(chat, msg, msg.rowid)
        self.assertTrue(result)

        self.messageFrame.removeOldReadReceipt()

        self.assertIsNone(self.messageFrame.messageBubbles[msg.rowid][-1].readReceipt)

    def test_add_message(self):
        style = ttk.Style()

        borderImage = tk.PhotoImage("borderImage", file='localCode/messageBox.png')
        style.element_create("RoundedFrame",
                             "image", borderImage,
                             ("focus", borderImage),
                             border=16, sticky="nsew")
        style.layout("RoundedFrame", [("RoundedFrame", {"sticky": "nsew"})])

        chat = api.Chat(ROWID=1)
        i = 0
        message = api.Message(ROWID=1, guid='ABC-DEF-GHI-JKL', text='hi')
        chat.addMessage(message)
        prevMessage = None
        lastFromMeId = None

        self.messageFrame.addMessage(chat, i, message, prevMessage, lastFromMeId)

        self.assertIn(message.rowid, self.messageFrame.messageBubbles)
        self.assertEqual(self.messageFrame.messageBubbles[message.rowid][0].pack_info()['anchor'], 'w')

    def test_add_message_from_me(self):
        chat = api.Chat(ROWID=1)
        i = 0
        message = api.Message(ROWID=1, guid='ABC-DEF-GHI-JKL', text='hi', is_from_me=1)
        chat.addMessage(message)
        prevMessage = None
        lastFromMeId = None

        self.messageFrame.addMessage(chat, i, message, prevMessage, lastFromMeId)

        self.assertIn(message.rowid, self.messageFrame.messageBubbles)
        self.assertEqual(self.messageFrame.messageBubbles[message.rowid][0].pack_info()['anchor'], 'e')

    def test_add_message_remove_temp(self):
        chat = api.Chat(ROWID=1)
        i = 0
        tempMsg = api.Message(ROWID=-1, guid='-1', text='hi', is_from_me=1)
        message = api.Message(ROWID=1, guid='ABC-DEF-GHI-JKL', text='hi', is_from_me=1)
        chat.messageList.append(tempMsg)
        chat.outgoingList.append(tempMsg)

        prevMessage = None
        self.messageFrame.addMessage(chat, i, tempMsg, prevMessage, None)
        prevMessage = tempMsg
        lastFromMeId = -1

        self.assertIn(tempMsg.rowid, self.messageFrame.messageBubbles)

        chat.addMessage(message)
        self.messageFrame.addMessage(chat, i, message, prevMessage, lastFromMeId)

        self.assertIn(message.rowid, self.messageFrame.messageBubbles)
        self.assertNotIn(tempMsg.rowid, self.messageFrame.messageBubbles)
        self.assertEqual(self.messageFrame.messageBubbles[message.rowid][0].pack_info()['anchor'], 'e')

    def test_add_message_with_attachments(self):
        chat = api.Chat(ROWID=1)
        i = 0
        message = api.Message(ROWID=1, guid='ABC-DEF-GHI-JKL', text='hi￼', is_from_me=0)
        attachment = api.Attachment(ROWID=1, uti='public.png', filename='bogus.png')
        message.addAttachment(attachment, 0)
        chat.addMessage(message)
        prevMessage = None
        lastFromMeId = None

        self.messageFrame.addMessage(chat, i, message, prevMessage, lastFromMeId)

        self.assertIn(message.rowid, self.messageFrame.messageBubbles)
        self.assertEqual(len(self.messageFrame.messageBubbles[message.rowid]), 3)
        for bubble in self.messageFrame.messageBubbles[message.rowid]:
            self.assertEqual(bubble.pack_info()['anchor'], 'w')

    def test_add_message_with_attachments_from_me(self):
        chat = api.Chat(ROWID=1)
        i = 0
        message = api.Message(ROWID=1, guid='ABC-DEF-GHI-JKL', text='hi￼', is_from_me=1)
        attachment = api.Attachment(ROWID=1, uti='public.png', filename='bogus.png')
        message.addAttachment(attachment, 0)
        chat.addMessage(message)
        prevMessage = None
        lastFromMeId = None

        self.messageFrame.addMessage(chat, i, message, prevMessage, lastFromMeId)

        self.assertIn(message.rowid, self.messageFrame.messageBubbles)
        self.assertEqual(len(self.messageFrame.messageBubbles[message.rowid]), 3)
        for bubble in self.messageFrame.messageBubbles[message.rowid]:
            self.assertEqual(bubble.pack_info()['anchor'], 'e')

    def test_add_message_with_attachments_remove_temp(self):
        chat = api.Chat(ROWID=1)
        i = 0
        tempMsg = api.Message(ROWID=-1, guid='-1', text='hi￼', is_from_me=1)
        message = api.Message(ROWID=1, guid='ABC-DEF-GHI-JKL', text='hi￼', is_from_me=1)
        attachment = api.Attachment(ROWID=1, guid='NOT-ABC', uti='public.png', filename='bogus.png')
        tempMsg.addAttachment(attachment, 0)
        message.addAttachment(attachment, 0)

        chat.messageList.append(tempMsg)
        chat.outgoingList.append(tempMsg)

        prevMessage = None
        self.messageFrame.addMessage(chat, i, tempMsg, prevMessage, None)
        prevMessage = tempMsg
        lastFromMeId = -1

        self.assertIn(tempMsg.rowid, self.messageFrame.messageBubbles)

        chat.addMessage(message)
        self.messageFrame.addMessage(chat, i, message, prevMessage, lastFromMeId)

        self.assertIn(message.rowid, self.messageFrame.messageBubbles)
        self.assertEqual(len(self.messageFrame.messageBubbles[message.rowid]), 2)
        self.assertNotIn(tempMsg.rowid, self.messageFrame.messageBubbles)

    def test_add_messages_wrong_chat(self):
        chat = api.Chat(ROWID=1)
        wrongChat = api.Chat(ROWID=2)
        self.messageFrame.currentChat = chat

        result = self.messageFrame.addMessages(wrongChat)

        self.assertIsNone(result)
        self.assertDictEqual(self.messageFrame.messageBubbles, {})

    def test_add_messages_already_added(self):
        chat = api.Chat(ROWID=1)
        msg1 = api.Message(ROWID=1)
        msg2 = api.Message(ROWID=2, text='New text')
        chat.addMessages([msg1, msg2])
        self.messageFrame.currentChat = chat
        self.messageFrame.addMessages(chat)

        result = self.messageFrame.addMessages(chat)

        self.assertTrue(result)
        self.assertEqual(self.messageFrame.messageBubbles[msg2.rowid][0].body['text'], 'New text')

    def test_add_messages_pass_limit(self):
        chat = api.Chat(ROWID=1)
        maxId = self.messageFrame.messageLimit + 2 
        for i in range(1, maxId):
            chat.addMessage(api.Message(ROWID=i, guid=str(i)))
        self.messageFrame.currentChat = chat

        result = self.messageFrame.addMessages(chat)

        self.assertFalse(result)
        self.assertListEqual(list(self.messageFrame.messageBubbles.keys()), [i for i in range(2, maxId)])

    def test_get_messages_up_to_limit(self):
        chat = api.Chat(ROWID=1)
        maxId = self.messageFrame.messageLimit + 2 
        for i in range(1, maxId):
            chat.addMessage(api.Message(ROWID=i, guid=str(i)))
        messageDict = chat.getMessages()

        subList = self.messageFrame.getMessagesUpToLimit(messageDict, self.messageFrame.messageLimit)

        self.assertEqual(len(subList), self.messageFrame.messageLimit)

#    def test_get_last_from_me_id(self):
#        chat = api.Chat(ROWID=1)
#        msg1 = api.Message(ROWID=1, guid='MSG1', is_from_me=1)
#        msg2 = api.Message(ROWID=2, guid='MSG2', is_from_me=1)
#        chat.addMessages([msg1, msg2])
#
#        result = self.messageFrame._getLastFromMeId(chat.getMessages(), list(chat.getMessages().keys()))
#
#        self.assertEqual(result, 2)

#    def test_get_last_from_me_id_last_not_from_me(self):
#        chat = api.Chat(ROWID=1)
#        msg1 = api.Message(ROWID=1, guid='MSG1', is_from_me=1)
#        msg2 = api.Message(ROWID=2, guid='MSG2', is_from_me=0)
#        chat.addMessages([msg1, msg2])
#
#        result = self.messageFrame._getLastFromMeId(chat.getMessages(), list(chat.getMessages().keys()))
#
#        self.assertEqual(result, 1)
#
#    def test_get_last_from_me_id_last_none_from_me(self):
#        chat = api.Chat(ROWID=1)
#        msg1 = api.Message(ROWID=1, guid='MSG1', is_from_me=0)
#        msg2 = api.Message(ROWID=2, guid='MSG2', is_from_me=0)
#        chat.addMessages([msg1, msg2])
#
#        result = self.messageFrame._getLastFromMeId(chat.getMessages(), list(chat.getMessages().keys()))
#
#        self.assertEqual(result, -1)

    def test_show_reaction_window(self):
        msg = api.Message(ROWID=1, guid='MSG1')
        reaction1 = api.Reaction(ROWID=2, guid='REACT1', associated_message_id=msg.rowid, associated_message_guid=msg.guid, associated_message_type=2000)
        msg.addReaction(reaction1)

        self.messageFrame._showReactionWindow(msg, msg.messageParts[0])

        self.assertTrue(self.messageFrame.reactionWindow.winfo_exists())
        
if __name__ == '__main__':
    unittest.main()
