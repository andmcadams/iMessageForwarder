import unittest
from localCode.messageApi import api

class TestReactionMethods(unittest.TestCase):

    def test_default_values(self):
        reaction = api.Reaction(ROWID=2, associated_message_id=1)

        self.assertEqual(reaction.ROWID, 2)
        self.assertEqual(reaction.associated_message_id, 1)
        self.assertEqual(reaction.guid, '')
        self.assertEqual(reaction.text, '')
        self.assertEqual(reaction.handle_id, 1)
        self.assertIsNone(reaction.service)
        self.assertEqual(reaction.date, 0)
        self.assertEqual(reaction.date_read, 0)
        self.assertEqual(reaction.date_delivered, 0)
        self.assertEqual(reaction.is_delivered, 0)
        self.assertEqual(reaction.is_finished, 0)
        self.assertEqual(reaction.is_from_me, 0)
        self.assertEqual(reaction.is_read, 0)
        self.assertEqual(reaction.is_sent, 0)
        self.assertEqual(reaction.cache_has_attachments, 0)
        self.assertIsNone(reaction.cache_roomnames)
        self.assertEqual(reaction.item_type, 0)
        self.assertEqual(reaction.other_handle, 0)
        self.assertIsNone(reaction.group_title)
        self.assertEqual(reaction.group_action_type, 0)
        self.assertIsNone(reaction.associated_message_guid)
        self.assertEqual(reaction.associated_message_type, 0)
        self.assertEqual(reaction.message_update_date, 0)
        self.assertEqual(reaction.error, 0)

    def test_default_properties(self):
        reaction = api.Reaction(ROWID=2, associated_message_id=1)

        self.assertEqual(reaction.rowid, reaction.ROWID)
        self.assertEqual(reaction.handleId, reaction.handle_id)
        self.assertEqual(reaction.handleName, '')
        self.assertEqual(reaction.dateRead, reaction.date_read)
        self.assertEqual(reaction.isDelivered, reaction.is_delivered == 1)
        self.assertEqual(reaction.isFromMe, reaction.is_from_me == 1)
        self.assertEqual(reaction.isiMessage, reaction.service == 'iMessage')
        self.assertEqual(reaction.isRead, reaction.is_read == 1)
        self.assertEqual(reaction.isSent, reaction.is_sent == 1)
        self.assertEqual(reaction.isTemporary, reaction.ROWID < 0)
        self.assertIsNone(reaction.attachment)
        self.assertDictEqual(reaction.reactions, {})
        self.assertTrue(reaction.isAddition)
        self.assertEqual(reaction.reactionType,
                reaction.associated_message_type)
        self.assertEqual(reaction.associatedMessageId,
                reaction.associated_message_id)
        self.assertTrue(reaction.isReaction)

    def test_is_temporary(self):
        reaction = api.Reaction(ROWID=-1, associated_message_id=1)

        self.assertTrue(reaction.isTemporary)

    def test_no_rowid(self):
        with self.assertRaises(api.ReceivedNoIdException):
            api.Reaction()

    def test_no_associated_message_id(self):
        with self.assertRaises(api.ReactionNoAssociatedIdException):
            api.Reaction(ROWID=1)

    def test_text_no_emoji(self):
        testText = 'Text without any emojis'

        reaction = api.Reaction(ROWID=2, associated_message_id=1,
                                text=testText)

        self.assertEqual(reaction.text, testText)

    def test_text_with_emoji(self):
        testText = 'Text with an 🍄 emoji'
        correctText = 'Text with an  emoji'

        reaction = api.Reaction(ROWID=2, associated_message_id=1,
                                text=testText)

        self.assertNotEqual(reaction.text, testText)
        self.assertEqual(reaction.text, correctText)

    def test_is_newer(self):
        reaction = api.Reaction(ROWID=2, associated_message_id=1, date=0)
        reaction2 = api.Reaction(ROWID=4, associated_message_id=3, date=1)

        self.assertFalse(reaction.isNewer(reaction2))

    def test_is_newer_same_date(self):
        reaction = api.Reaction(ROWID=2, associated_message_id=1, date=1)
        reaction2 = api.Reaction(ROWID=4, associated_message_id=3, date=1)

        self.assertFalse(reaction.isNewer(reaction2))
