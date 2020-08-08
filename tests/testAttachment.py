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
