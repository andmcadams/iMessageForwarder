import unittest
from localCode import api

class TestDummyChatMethods(unittest.TestCase):

    def test_basic_creation(self):
        dummyChat = api.DummyChat(1)

        self.assertEqual(dummyChat.chatId, 1)

    def test_missing_chat_id(self):
        with self.assertRaises(api.ChatNoIdException):
            api.DummyChat(None)
