import unittest
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
        self.messageFrame.createTimeLabel(t.timestamp())

        children = self.messageFrame.interior.winfo_children()

        self.assertEqual(len(children), 1)
        self.assertEqual(children[0].cget('text'), correctText)

    def test_create_time_label_yesterday(self):
        t = datetime.now() - timedelta(days=1)
        correctText = mf.getTimeText(t.timestamp())
        self.messageFrame.createTimeLabel(t.timestamp())

        children = self.messageFrame.interior.winfo_children()

        self.assertEqual(len(children), 1)
        self.assertEqual(children[0].cget('text'), correctText)

    def test_create_time_label_multiple_days_back(self):
        t = datetime.now() - timedelta(days=10)
        correctText = mf.getTimeText(t.timestamp())
        self.messageFrame.createTimeLabel(t.timestamp())

        children = self.messageFrame.interior.winfo_children()

        self.assertEqual(len(children), 1)
        self.assertEqual(children[0].cget('text'), correctText)

if __name__ == '__main__':
    unittest.main()
