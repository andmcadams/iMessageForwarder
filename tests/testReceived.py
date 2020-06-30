import unittest
from localCode.messageApi import api


class TestReceivedMethods(unittest.TestCase):

    # Received is an abstract class and should not be instantiated.
    def test_fail_to_construt(self):
        with self.assertRaises(TypeError):
            api.Received()
