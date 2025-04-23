import unittest

from controller.data.state import State
from controller.data.command import PlayCommand


DEFAULT_URL = 'a-track'
DEFAULT_TITLE = 'some-title'
DEFAULT_ARTIST = 'artist-to-sing-a-song'


class MyItem(object):

    title: str
    artist: str

    def __init__(self, title, artist):
        self.title = title
        self.artist = artist

    def get_title(self):
        return self.title

    def get_actor(self):
        return self.artist


class TestState(unittest.TestCase):

    def _testee(self) -> State:
        return State()

    def _url_cmd(self):
        return PlayCommand(url=DEFAULT_URL)

    def _non_url_cmd(self):
        return PlayCommand(title=DEFAULT_TITLE)

    def test_initial(self):
        t = self._testee()

        self.assertEqual(t.current_command, None)

        self.assertEqual(t.running, False)
        self.assertEqual(t.running_start_datetime, None)
        self.assertEqual(t.search_response, None)
        self.assertEqual(t.played_count, 0)
        self.assertEqual(t.description, 'Aus')
        self.assertEqual(t.stop_reason, None)

        self.assertFalse(t.is_item_mode())
        self.assertFalse(t.is_url_mode())

    def test_now_playing_url(self):
        t = self._testee()

        # always issue command before playing...
        t.command(PlayCommand(url=DEFAULT_URL))
        t.now_playing(DEFAULT_URL, None)

        self.assertEqual(t.current_command.url, DEFAULT_URL)

        self.assertEqual(t.running, True)
        self.assertNotEqual(t.running_start_datetime, None)
        self.assertEqual(t.search_response, None)
        self.assertEqual(t.played_count, 1)
        self.assertEqual(t.description, 'Spielt ' + DEFAULT_URL)
        self.assertEqual(t.stop_reason, None)

        self.assertFalse(t.is_item_mode())
        self.assertTrue(t.is_url_mode())

    def test_now_playing_item(self):
        t = self._testee()

        # always issue command before playing...
        cmd = PlayCommand(title=DEFAULT_TITLE)
        t.command(cmd)
        t.now_playing(None, MyItem(DEFAULT_TITLE, DEFAULT_ARTIST))

        self.assertEqual(t.current_command, cmd)

        self.assertEqual(t.running, True)
        self.assertNotEqual(t.running_start_datetime, None)
        self.assertEqual(t.search_response, None)
        self.assertEqual(t.played_count, 1)
        self.assertEqual(t.description, f"Spielt {DEFAULT_TITLE} von {DEFAULT_ARTIST}")
        self.assertEqual(t.stop_reason, None)

        self.assertTrue(t.is_item_mode())
        self.assertFalse(t.is_url_mode())

    def test_next_play(self):
        t = self._testee()

        # always issue command before playing...
        cmd = PlayCommand(artist=DEFAULT_ARTIST, loop=True)
        t.command(cmd)
        t.now_playing(None, MyItem(DEFAULT_TITLE, DEFAULT_ARTIST))

        self.assertEqual(t.running, True)

        t.next_play(None, MyItem('asdf', DEFAULT_ARTIST))
        t.next_track_is_playing()

        self.assertEqual(t.running, True)
        self.assertNotEqual(t.running_start_datetime, None)
        self.assertEqual(t.search_response, None)
        self.assertEqual(t.played_count, 2)
        self.assertEqual(t.description, f"Spielt Lieder von {DEFAULT_ARTIST}")
        self.assertEqual(t.stop_reason, None)

    def test_stop(self):
        t = self._testee()

        # always issue command before playing...
        t.command(PlayCommand(url=DEFAULT_URL))
        t.now_playing(DEFAULT_URL, None)

        self.assertEqual(t.current_command.url, DEFAULT_URL)

        t.stop('paused')
        self.assertEqual(t.running, False)
        self.assertEqual(t.running_start_datetime, None)
        self.assertEqual(t.search_response, None)
        self.assertEqual(t.played_count, 0)
        self.assertEqual(t.description, "Aus")
        self.assertEqual(t.stop_reason, 'paused')
