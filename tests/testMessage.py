import unittest
from localCode.messageApi import api

class TestMessageMethods(unittest.TestCase):

    def test_default_values(self):
        msg = api.Message(ROWID=1)

        self.assertEqual(msg.ROWID, 1)
        self.assertEqual(msg.guid, '')
        self.assertEqual(msg.text, '')
        self.assertEqual(msg.handle_id, 1)
        self.assertIsNone(msg.service)
        self.assertEqual(msg.date, 0)
        self.assertEqual(msg.date_read, 0)
        self.assertEqual(msg.date_delivered, 0)
        self.assertEqual(msg.is_delivered, 0)
        self.assertEqual(msg.is_finished, 0)
        self.assertEqual(msg.is_from_me, 0)
        self.assertEqual(msg.is_read, 0)
        self.assertEqual(msg.is_sent, 0)
        self.assertEqual(msg.cache_has_attachments, 0)
        self.assertIsNone(msg.cache_roomnames)
        self.assertEqual(msg.item_type, 0)
        self.assertEqual(msg.other_handle, 0)
        self.assertIsNone(msg.group_title)
        self.assertEqual(msg.group_action_type, 0)
        self.assertIsNone(msg.associated_message_guid)
        self.assertEqual(msg.associated_message_type, 0)
        self.assertIsNone(msg.attachment_id)
        self.assertEqual(msg.message_update_date, 0)
        self.assertEqual(msg.error, 0)

    def test_default_properties(self):
        msg = api.Message(ROWID=1)

        self.assertEqual(msg.rowid, msg.ROWID)
        self.assertEqual(msg.handleId, msg.handle_id)
        self.assertEqual(msg.handleName, '')
        self.assertEqual(msg.dateRead, msg.date_read)
        self.assertEqual(msg.isDelivered, msg.is_delivered == 1)
        self.assertEqual(msg.isFromMe, msg.is_from_me == 1)
        self.assertEqual(msg.isiMessage, msg.service == 'iMessage')
        self.assertEqual(msg.isRead, msg.is_read == 1)
        self.assertEqual(msg.isSent, msg.is_sent == 1)
        self.assertEqual(msg.isTemporary, msg.ROWID < 0)
        self.assertIsNone(msg.attachment)
        self.assertDictEqual(msg.reactions, {})
        self.assertFalse(msg.isReaction)

    def test_is_temporary(self):
        msg = api.Message(ROWID=-1)

        self.assertTrue(msg.isTemporary)

    def test_no_rowid(self):
        with self.assertRaises(api.ReceivedNoIdException):
            api.Message()

    def test_add_attachment(self):
        msg = api.Message(ROWID=1)
        attachment = api.Attachment(ROWID=1)

        msg.attachment = attachment

        self.assertEqual(msg.attachment, attachment)

    def test_add_handle_name(self):
        testHandleName = 'Handle name'
        msg = api.Message(ROWID=1)

        msg.handleName = testHandleName

        self.assertEqual(msg.handleName, testHandleName)

    def test_text_no_emoji(self):
        testText = 'Text without any emojis'

        msg = api.Message(ROWID=1, text=testText)

        self.assertEqual(msg.text, testText)

    def test_text_with_emoji(self):
        testText = 'Text with an 🍄 emoji'
        correctText = 'Text with an  emoji'

        msg = api.Message(ROWID=1, text=testText)

        self.assertNotEqual(msg.text, testText)
        self.assertEqual(msg.text, correctText)

    def test_add_first_reaction(self):
        testReaction = api.Reaction(associated_message_id=1, ROWID=1,
                handle_id=1, associated_message_type=2000)
        correctReactionDict = {
            testReaction.handleId: {
                (testReaction.associated_message_type % 1000): testReaction
            }
        }
        msg = api.Message(ROWID=1)

        msg.addReaction(testReaction)

        self.assertDictEqual(msg.reactions, correctReactionDict)

    def test_add_second_reaction_same_handle_different_reaction(self):
        testReaction = api.Reaction(associated_message_id=1, ROWID=1,
                handle_id=1, associated_message_type=2000)
        testReaction2 = api.Reaction(associated_message_id=1, ROWID=2,
                handle_id=1, associated_message_type=2001)
        correctReactionDict = {
            testReaction.handleId: {
                (testReaction.associated_message_type % 1000): testReaction,
                (testReaction2.associated_message_type % 1000): testReaction2
            }
        }
        msg = api.Message(ROWID=1)

        msg.addReaction(testReaction)
        msg.addReaction(testReaction2)

        self.assertDictEqual(msg.reactions, correctReactionDict)

    def test_add_second_reaction_same_handle_same_reaction(self):
        testReaction = api.Reaction(associated_message_id=1, ROWID=1,
                handle_id=1, associated_message_type=2000)
        testReaction2 = api.Reaction(associated_message_id=1, ROWID=2,
                handle_id=1, associated_message_type=2000)
        correctReactionDict = {
            testReaction.handleId: {
                (testReaction.associated_message_type % 1000): testReaction2
            }
        }
        msg = api.Message(ROWID=1)

        msg.addReaction(testReaction)
        msg.addReaction(testReaction2)

        self.assertDictEqual(msg.reactions, correctReactionDict)

    def test_add_second_reaction_same_handle_remove_reaction(self):
        testReaction = api.Reaction(associated_message_id=1, ROWID=1,
                handle_id=1, associated_message_type=2000)
        testReaction2 = api.Reaction(associated_message_id=1, ROWID=2,
                handle_id=1, associated_message_type=3000)
        correctReactionDict = {
            testReaction.handleId: {
                (testReaction.associated_message_type % 1000): testReaction2
            }
        }
        msg = api.Message(ROWID=1)

        msg.addReaction(testReaction)
        msg.addReaction(testReaction2)

        self.assertDictEqual(msg.reactions, correctReactionDict)

    def test_add_second_reaction_different_handle_same_reaction(self):
        testReaction = api.Reaction(associated_message_id=1, ROWID=1,
                handle_id=1, associated_message_type=2000)
        testReaction2 = api.Reaction(associated_message_id=1, ROWID=2,
                handle_id=2, associated_message_type=2000)
        correctReactionDict = {
            testReaction.handleId: {
                (testReaction.associated_message_type % 1000): testReaction
            },
            testReaction2.handleId: {
                (testReaction2.associated_message_type % 1000): testReaction2
            }
        }
        msg = api.Message(ROWID=1)

        msg.addReaction(testReaction)
        msg.addReaction(testReaction2)

        self.assertDictEqual(msg.reactions, correctReactionDict)

    def test_add_second_reaction_different_handle_different_reaction(self):
        testReaction = api.Reaction(associated_message_id=1, ROWID=1,
                handle_id=1, associated_message_type=2000)
        testReaction2 = api.Reaction(associated_message_id=1, ROWID=2,
                handle_id=2, associated_message_type=2001)
        correctReactionDict = {
            testReaction.handleId: {
                (testReaction.associated_message_type % 1000): testReaction
            },
            testReaction2.handleId: {
                (testReaction2.associated_message_type % 1000): testReaction2
            }
        }
        msg = api.Message(ROWID=1)

        msg.addReaction(testReaction)
        msg.addReaction(testReaction2)

        self.assertDictEqual(msg.reactions, correctReactionDict)

    def test_update_no_remove_temp_no_attachment(self):
        msg = api.Message(ROWID=1, date=0, date_read=0, date_delivered=0,
                is_delivered=0, is_finished=0, is_read=0, is_sent=0,
                message_update_date=0, service='iMessage')
        msg2 = api.Message(ROWID=2, date=1, date_read=1, date_delivered=1,
                is_delivered=1, is_finished=1, is_read=1, is_sent=1,
                message_update_date=1, service='SMS')

        msg.update(msg2)

        self.assertEqual(msg.date, msg2.date)
        self.assertEqual(msg.date_read, msg2.date_read)
        self.assertEqual(msg.date_delivered, msg2.date_delivered)
        self.assertEqual(msg.is_delivered, msg2.is_delivered)
        self.assertEqual(msg.is_finished, msg2.is_finished)
        self.assertEqual(msg.is_read, msg2.is_read)
        self.assertEqual(msg.is_sent, msg2.is_sent)
        self.assertEqual(msg.message_update_date, msg2.message_update_date)
        self.assertEqual(msg.service, msg2.service)

    def test_update_remove_temp(self):
        msg = api.Message(ROWID=1)
        msg2 = api.Message(ROWID=2)
        msg2.removedTempId = -1

        msg.update(msg2)

        self.assertEqual(msg.removedTempId, msg2.removedTempId)

    def test_update_do_not_update_remove_temp(self):
        msg = api.Message(ROWID=1)
        msg2 = api.Message(ROWID=2)
        msg.removedTempId = -1

        msg.update(msg2)

        self.assertEqual(msg.removedTempId, -1)

    def test_update_attachment(self):
        msg = api.Message(ROWID=1)
        msg2 = api.Message(ROWID=2)
        attachment = api.Attachment(ROWID=1)
        msg2.attachment = attachment

        msg.update(msg2)

        self.assertEqual(msg.attachment, attachment)

    def test_is_newer(self):
        msg = api.Message(ROWID=1, date=0)
        msg2 = api.Message(ROWID=2, date=1)

        self.assertFalse(msg.isNewer(msg2))
        self.assertTrue(msg2.isNewer(msg))

    def test_is_newer_same_date(self):
        msg = api.Message(ROWID=1, date=1)
        msg2 = api.Message(ROWID=2, date=1)

        self.assertFalse(msg.isNewer(msg2))
        self.assertTrue(msg2.isNewer(msg))
