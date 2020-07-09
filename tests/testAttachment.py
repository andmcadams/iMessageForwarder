import unittest
from localCode.messageApi import api

class TestAttachmentMethods(unittest.TestCase):

    def test_default_values(self):
        attachment = api.Attachment(ROWID=1)

        self.assertEqual(attachment.ROWID, 1)
        self.assertEqual(attachment.guid, '')
        self.assertEqual(attachment.filename, '')
        self.assertEqual(attachment.uti, '')

    def test_default_properties(self):
        attachment = api.Attachment(ROWID=1)

        self.assertEqual(attachment.rowid, 1)
        self.assertDictEqual(attachment.reactions, {})

    def test_missing_rowid(self):
        with self.assertRaises(api.AttachmentNoIdException):
            api.Attachment()

    def test_default_properties(self):
        attachment = api.Attachment(ROWID=1)

        self.assertEqual(attachment.rowid, attachment.ROWID)

    def test_add_first_reaction(self):
        testReaction = api.Reaction(associated_message_id=1, ROWID=1,
                handle_id=1, associated_message_type=2000)
        correctReactionDict = {
            testReaction.handleId: {
                (testReaction.associated_message_type % 1000): testReaction
            }
        }
        attachment = api.Attachment(ROWID=1)

        attachment.addReaction(testReaction)

        self.assertDictEqual(attachment.reactions, correctReactionDict)

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
        attachment = api.Attachment(ROWID=1)

        attachment.addReaction(testReaction)
        attachment.addReaction(testReaction2)

        self.assertDictEqual(attachment.reactions, correctReactionDict)

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
        attachment = api.Attachment(ROWID=1)

        attachment.addReaction(testReaction)
        attachment.addReaction(testReaction2)

        self.assertDictEqual(attachment.reactions, correctReactionDict)

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
        attachment = api.Attachment(ROWID=1)

        attachment.addReaction(testReaction)
        attachment.addReaction(testReaction2)

        self.assertDictEqual(attachment.reactions, correctReactionDict)

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
        attachment = api.Attachment(ROWID=1)

        attachment.addReaction(testReaction)
        attachment.addReaction(testReaction2)

        self.assertDictEqual(attachment.reactions, correctReactionDict)

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
        attachment = api.Attachment(ROWID=1)

        attachment.addReaction(testReaction)
        attachment.addReaction(testReaction2)

        self.assertDictEqual(attachment.reactions, correctReactionDict)
