import unittest
from localCode.messageApi import api
from localCode import messageframe as mf

class TestReactionBubbleMethods(unittest.TestCase):

    def test_basic_creation(self):
        reactionBubble = mf.ReactionBubble(None, 2000)

        self.assertIsNotNone(reactionBubble.original)

    def test_bad_associated_message_type(self):
        with self.assertRaises(mf.ReactionBubbleBadMessageTypeException):
            mf.ReactionBubble(None, 1)

