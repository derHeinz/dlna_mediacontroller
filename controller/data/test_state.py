from controller.data.state import State
import unittest


class TestState(unittest.TestCase):

    def _testee(self) -> State:
        return State()

    def test_initial(self):
        t = self._testee()

        self.assertEqual(t.url, None)
        self.assertEqual(t.title, None)
        self.assertEqual(t.artist, None)
        self.assertEqual(t.loop, False)

        self.assertEqual(t.running, False)
        self.assertEqual(t.running_start_datetime, None)
        self.assertEqual(t.search_response, None)
        self.assertEqual(t.played_count, 0)
        self.assertEqual(t.description, 'Aus')
        self.assertEqual(t.stop_reason, None)
