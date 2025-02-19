import unittest
from unittest.mock import MagicMock, patch

from controller.player_dispatcher import PlayerDispatcher
from controller.data.command import Command, PlayCommand
from controller.data.exceptions import RequestCannotBeHandeledException

from dlna.player import Player


class FakeServer:

    def __init__(self, name):
        self._name = name

    def search(self):
        pass


class TestPlayerDispatcher(unittest.TestCase):

    FAKE_PLAYER_A = MagicMock(spec=Player)
    FAKE_PLAYER_B = MagicMock(spec=Player)

    FAKE_SERVER = FakeServer('F')

    DEFAULT_URL = 'http://bla'

    
    def _testee(self):

        def true_on_audio(type: str):
            if "audio" == type:
                return True
            return False
        
        def true_on_audio_and_video(type: str):
            if type in ["audio", "video"]:
                return True
            return False
        
        fake_renderer_A_mock = self.FAKE_PLAYER_A.get_renderer.return_value
        fake_renderer_A_mock.get_known_names.return_value = ['A']
        fake_renderer_A_mock.get_name.return_value = 'A'
        fake_renderer_A_mock.can_play_type.side_effect = true_on_audio
        
        fake_renderer_B_mock = self.FAKE_PLAYER_B.get_renderer.return_value
        fake_renderer_B_mock.get_known_names.return_value = ['B']
        fake_renderer_B_mock.get_name.return_value = 'B'
        fake_renderer_B_mock.can_play_type.side_effect = true_on_audio_and_video

        # preset
        self.FAKE_PLAYER_A.reset_mock()
        self.FAKE_PLAYER_B.reset_mock()

        return PlayerDispatcher([self.FAKE_PLAYER_A, self.FAKE_PLAYER_B], self.FAKE_SERVER, MagicMock())

    @patch("controller.player_dispatcher.ensure_online")
    def test_pause_default(self, ensure_online):
        ensure_online.return_value = True

        self._testee().pause(None)
        self.FAKE_PLAYER_A.pause.assert_called_with()  # first one is default
        self.FAKE_PLAYER_B.pause.assert_not_called()
        ensure_online.assert_called_with(self.FAKE_PLAYER_A.get_renderer())

    @patch("controller.player_dispatcher.ensure_online")
    def test_pause_target(self, ensure_online):
        ensure_online.return_value = True

        self._testee().pause(Command('B'))
        self.FAKE_PLAYER_A.pause.assert_not_called()
        self.FAKE_PLAYER_B.pause.assert_called_with()  # i needed to call B
        ensure_online.assert_called_with(self.FAKE_PLAYER_B.get_renderer())

    @patch("controller.player_dispatcher.ensure_online")
    def test_stop_target(self, ensure_online):
        ensure_online.return_value = True

        self._testee().stop(Command('B'))
        self.FAKE_PLAYER_A.stop.assert_not_called()
        self.FAKE_PLAYER_B.stop.assert_called_with()  # i needed to call B
        ensure_online.assert_called_with(self.FAKE_PLAYER_B.get_renderer())

    def test_state(self):
        self._testee().state(None)

    @patch("controller.player_dispatcher.ensure_online")
    def test_play_target(self, ensure_online):
        ensure_online.return_value = True

        self._testee().play(PlayCommand(target='B', url=self.DEFAULT_URL))
        self.FAKE_PLAYER_A.play.assert_not_called()
        self.FAKE_PLAYER_B.play.assert_called_with(self.DEFAULT_URL)  # i needed to call B
        ensure_online.assert_called_with(self.FAKE_PLAYER_B.get_renderer())

    @patch("controller.player_dispatcher.ensure_online")
    def test_play_target_but_offline(self, ensure_online):
        ensure_online.return_value = False

        with self.assertRaises(RequestCannotBeHandeledException):
            self._testee().play(PlayCommand(target='B', url=self.DEFAULT_URL))
        self.FAKE_PLAYER_A.play.assert_not_called()
        self.FAKE_PLAYER_B.play.assert_not_called()
        ensure_online.assert_called_with(self.FAKE_PLAYER_B.get_renderer())

    @patch("controller.player_dispatcher.ensure_online")
    def test_play_type_audio(self, ensure_online):
        ensure_online.return_value = True

        self._testee().play(PlayCommand(url=self.DEFAULT_URL, type='audio'))
        self.FAKE_PLAYER_A.play.assert_called_with(self.DEFAULT_URL)
        self.FAKE_PLAYER_B.play.assert_not_called()
        ensure_online.assert_called_with(self.FAKE_PLAYER_A.get_renderer())

    @patch("controller.player_dispatcher.ensure_online")
    def test_play_type_asdf_noone(self, ensure_online):
        ensure_online.return_value = True

        with self.assertRaises(RequestCannotBeHandeledException):
            self._testee().play(PlayCommand(url=self.DEFAULT_URL, type='asfd'))
        self.FAKE_PLAYER_A.play.assert_not_called()
        self.FAKE_PLAYER_B.play.assert_not_called()
        ensure_online.assert_not_called()

    @patch("controller.player_dispatcher.ensure_online")
    def test_play_type_video(self, ensure_online):
        ensure_online.return_value = True

        self._testee().play(PlayCommand(url=self.DEFAULT_URL, type='video'))
        self.FAKE_PLAYER_A.play.assert_not_called()
        self.FAKE_PLAYER_B.play.assert_called_with(self.DEFAULT_URL)
        ensure_online.assert_called_with(self.FAKE_PLAYER_B.get_renderer())

    @patch("controller.player_dispatcher.ensure_online")
    def test_play_default_not_available(self, ensure_online):
        ensure_online.return_value = False

        with self.assertRaises(RequestCannotBeHandeledException):
            self._testee().play(PlayCommand(url=self.DEFAULT_URL))
        self.FAKE_PLAYER_A.play.assert_not_called()
        self.FAKE_PLAYER_B.play.assert_not_called()
        ensure_online.assert_called_with(self.FAKE_PLAYER_A.get_renderer())
