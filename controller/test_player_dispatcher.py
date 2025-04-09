import unittest
from unittest.mock import MagicMock, patch, call

from controller.player_dispatcher import PlayerDispatcher
from controller.player_manager import PlayerManager
from controller.player_wrapper import PlayerWrapper
from controller.data.command import Command, PlayCommand
from controller.data.exceptions import RequestCannotBeHandeledException


class FakeServer:

    def __init__(self, name):
        self._name = name

    def search(self):
        pass


class TestPlayerDispatcher(unittest.TestCase):

    FAKE_MANAGER: MagicMock = MagicMock(spec=PlayerManager)
    FAKE_PLAYER_A: MagicMock = MagicMock(spec=PlayerWrapper)
    FAKE_PLAYER_B: MagicMock = MagicMock(spec=PlayerWrapper)
    FAKE_SCHEDULER: MagicMock = MagicMock()

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

        self.FAKE_PLAYER_A.get_known_names.return_value = ['A']
        self.FAKE_PLAYER_A.get_name.return_value = 'A'
        self.FAKE_PLAYER_A.can_play_type.side_effect = true_on_audio

        self.FAKE_PLAYER_B.get_known_names.return_value = ['B']
        self.FAKE_PLAYER_B.get_name.return_value = 'B'
        self.FAKE_PLAYER_B.can_play_type.side_effect = true_on_audio_and_video

        # preset
        self.FAKE_PLAYER_A.reset_mock()
        self.FAKE_PLAYER_B.reset_mock()

        self.FAKE_MANAGER.get_players.return_value = [self.FAKE_PLAYER_A, self.FAKE_PLAYER_B]

        return PlayerDispatcher(self.FAKE_MANAGER, self.FAKE_SERVER, self.FAKE_SCHEDULER)

    @patch("controller.player_dispatcher.Integrator")
    @patch("controller.player_dispatcher.ensure_online")
    def test_pause_default(self, ensure_online, integrator_constructor):
        ensure_online.return_value = True

        i = integrator_constructor.return_value
        self._testee().pause(None)

        integrator_constructor.assert_called_with(self.FAKE_PLAYER_A, self.FAKE_SERVER, self.FAKE_SCHEDULER)
        i.pause.assert_called_with()
        ensure_online.assert_called_with(self.FAKE_PLAYER_A)

    @patch("controller.player_dispatcher.Integrator")
    @patch("controller.player_dispatcher.ensure_online")
    def test_pause_target(self, ensure_online, integrator_constructor):
        ensure_online.return_value = True
        i = integrator_constructor.return_value

        self._testee().pause(Command('B'))

        integrator_constructor.assert_called_with(self.FAKE_PLAYER_B, self.FAKE_SERVER, self.FAKE_SCHEDULER)
        i.pause.assert_called_with()
        ensure_online.assert_called_with(self.FAKE_PLAYER_B)

    @patch("controller.player_dispatcher.Integrator")
    @patch("controller.player_dispatcher.ensure_online")
    def test_stop_target(self, ensure_online, integrator_constructor):
        ensure_online.return_value = True
        i = integrator_constructor.return_value

        self._testee().stop(Command('B'))

        integrator_constructor.assert_called_with(self.FAKE_PLAYER_B, self.FAKE_SERVER, self.FAKE_SCHEDULER)
        i.stop.assert_called_with()
        ensure_online.assert_called_with(self.FAKE_PLAYER_B)

    def test_state(self):
        self._testee().state(None)

    @patch("controller.player_dispatcher.Integrator")
    @patch("controller.player_dispatcher.ensure_online")
    def test_play_target(self, ensure_online, integrator_constructor):
        ensure_online.return_value = True
        i = integrator_constructor.return_value

        c = PlayCommand(target='B', url=self.DEFAULT_URL)
        self._testee().play(c)

        integrator_constructor.assert_called_with(self.FAKE_PLAYER_B, self.FAKE_SERVER, self.FAKE_SCHEDULER)
        i.play.assert_called_with(c)
        ensure_online.assert_called_with(self.FAKE_PLAYER_B)

    @patch("controller.player_dispatcher.Integrator")
    @patch("controller.player_dispatcher.ensure_online")
    def test_play_target_but_offline(self, ensure_online, integrator_constructor):
        ensure_online.return_value = False
        i = integrator_constructor.return_value

        c = PlayCommand(target='B', url=self.DEFAULT_URL)
        with self.assertRaises(RequestCannotBeHandeledException):
            self._testee().play(c)

        integrator_constructor.assert_not_called()
        i.play.assert_not_called()
        ensure_online.assert_called_with(self.FAKE_PLAYER_B)

    @patch("controller.player_dispatcher.Integrator")
    @patch("controller.player_dispatcher.ensure_online")
    def test_play_type_audio(self, ensure_online, integrator_constructor):
        ensure_online.return_value = True
        i = integrator_constructor.return_value

        c = PlayCommand(url=self.DEFAULT_URL, type='audio')
        self._testee().play(c)

        integrator_constructor.assert_called_with(self.FAKE_PLAYER_A, self.FAKE_SERVER, self.FAKE_SCHEDULER)
        i.play.assert_called_with(c)
        ensure_online.assert_called_with(self.FAKE_PLAYER_A)

    @patch("controller.player_dispatcher.Integrator")
    @patch("controller.player_dispatcher.ensure_online")
    def test_play_type_asdf_noone(self, ensure_online, integrator_constructor):
        ensure_online.return_value = True
        i = integrator_constructor.return_value

        with self.assertRaises(RequestCannotBeHandeledException):
            self._testee().play(PlayCommand(url=self.DEFAULT_URL, type='asfd'))

        integrator_constructor.assert_not_called()
        i.play.assert_not_called()
        ensure_online.assert_not_called()

    @patch("controller.player_dispatcher.Integrator")
    @patch("controller.player_dispatcher.ensure_online")
    def test_play_type_video(self, ensure_online, integrator_constructor):
        ensure_online.return_value = True
        i = integrator_constructor.return_value

        c = PlayCommand(url=self.DEFAULT_URL, type='video')
        self._testee().play(c)

        integrator_constructor.assert_called_with(self.FAKE_PLAYER_B, self.FAKE_SERVER, self.FAKE_SCHEDULER)
        i.play.assert_called_with(c)
        ensure_online.assert_called_with(self.FAKE_PLAYER_B)

    @patch("controller.player_dispatcher.Integrator")
    @patch("controller.player_dispatcher.ensure_online")
    def test_play_default_not_available(self, ensure_online, integrator_constructor):
        ensure_online.return_value = False
        i = integrator_constructor.return_value

        with self.assertRaises(RequestCannotBeHandeledException):
            self._testee().play(PlayCommand(url=self.DEFAULT_URL))

        integrator_constructor.assert_not_called()
        i.play.assert_not_called()
        ensure_online.has_calls(call(self.FAKE_PLAYER_A), call(self.FAKE_PLAYER_B))
