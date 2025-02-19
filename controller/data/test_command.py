from controller.data.command import PlayCommand
import unittest

class TestCommand(unittest.TestCase):

    def test_to_str(self):
        p = PlayCommand(url='a', artist='b', title='c', type='d', target='e', loop=True)
        self.assertEqual("PlayCommand(target='e', url='a', artist='b', title='c', type='d', loop=True)", str(p))
