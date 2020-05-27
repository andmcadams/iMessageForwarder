import unittest
import api

class TestMessageMethods(unittest.TestCase):

    # Test the creation of a message with no optional parameters.
    def test_basic_creation(self):
        msg = api.Message()
        self.assertEqual(msg.attr, { 'text': None })
        self.assertEqual(msg.reactions, {})
        self.assertEqual(msg.attachment, None)
        self.assertEqual(msg.handleName, None)

    # Test the creation of a message with only kw as an optional parameter (expanded).
    # The kw dictionary passed in should be the same as the message objects attr attribute.
    def test_kw_only(self):
        kw = {
            'text': 'test',
            'a': 'a text',
            'b': 'b text',
            'c': 'c text'
        }
        msg = api.Message(**kw)
        self.assertEqual(kw, msg.attr)

    # Test the creation of a message with an emoji in its text.
    # Due to tkinter issues, emojis cannot be properly displayed. Thus, they are removed from the text string.
    # They are retained in the local database.
    def test_text_with_emojis(self):
        kw = {
            'text': 'This 🍄 is a mushroom'
        }
        msg = api.Message(**kw)
        self.assertEquals('This  is a mushroom', msg.attr['text'])

    # Test the creation of a real message, similarly to how it is done in api.
    # The message is taken from a test db.
    def test_real_message(self):
        kw = {'ROWID': 581, 'guid': 'A153E7D9-8246-481C-96D4-4C15023658E1', 'text': 'This is some example text.', 'handle_id': 19, 'service': 'iMessage', 'error': 0, 'date': 1582434588, 'date_read': 0, 'date_delivered': 0, 'is_delivered': 1, 'is_finished': 1, 'is_from_me': 1, 'is_read': 0, 'is_sent': 1, 'cache_has_attachments': 0, 'cache_roomnames': None, 'item_type': 0, 'other_handle': 0, 'group_title': None, 'group_action_type': 0, 'associated_message_guid': None, 'associated_message_type': 0, 'attachment_id': None, 'message_update_date': 1584480798}   
        msg = api.Message(**kw)
        self.assertEquals(kw, msg.attr)

if __name__ == '__main__':
    unittest.main()
