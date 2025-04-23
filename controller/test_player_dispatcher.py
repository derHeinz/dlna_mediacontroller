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

    @patch("controller.player_dispatcher.Integrator")
    @patch("controller.player_dispatcher.ensure_online")
    def test_state(self, ensure_online, integrator_constructor):
        ensure_online.return_value = True
        integrator_constructor.side_effect = [MagicMock(), MagicMock()]  # return 2 differnt integrators (one per player)

        stateful_dispatcher = self._testee()
        res_none = stateful_dispatcher.state(None)
        self.assertEqual([], res_none)

        # play one item
        cmd_a = PlayCommand(target='A', url=self.DEFAULT_URL)
        stateful_dispatcher.play(cmd_a)
        res_a_none = stateful_dispatcher.state(None)
        res_a_cmd = stateful_dispatcher.state(cmd_a)
        self.assertEqual(res_a_none, res_a_cmd)

        # play to another player
        cmd_b = PlayCommand(target='B', url=self.DEFAULT_URL)
        stateful_dispatcher.play(cmd_b)
        res_b_none = stateful_dispatcher.state(None)
        res_b_cmd = stateful_dispatcher.state(cmd_b)
        self.assertNotEqual(res_b_none, res_b_cmd)  # because of player 'A' now in res_b_none
        self.assertEqual(res_b_none[0], res_a_cmd[0])
        self.assertEqual(res_b_none[1], res_b_cmd[0])

        self.assertNotEqual(res_a_cmd, res_b_cmd)  # because different players
        self.assertNotEqual(res_a_none, res_b_none)  # because different times

    @patch("controller.player_dispatcher.Integrator")
    @patch("controller.player_dispatcher.ensure_online")
    def test_play_target(self, ensure_online, integrator_constructor):
        ensure_online.return_value = True
        i = integrator_constructor.return_value

        c = PlayCommand(target='B', url=self.DEFAULT_URL)
        t = self._testee()
        t.play(c)

        integrator_constructor.assert_called_with(self.FAKE_PLAYER_B, self.FAKE_SERVER, self.FAKE_SCHEDULER)
        i.play.assert_called_with(c)
        ensure_online.assert_called_with(self.FAKE_PLAYER_B)

        # check state method aswell
        state_res = t.state(c)
        i.get_state.assert_called()
        self.FAKE_PLAYER_B.get_name.assert_called()
        self.assertTrue(state_res[0].player_name, 'B')

    @patch("controller.player_dispatcher.Integrator")
    @patch("controller.player_dispatcher.ensure_online")
    def test_play_target_again(self, ensure_online, integrator_constructor):
        ensure_online.return_value = True
        i = integrator_constructor.return_value

        stateful_dispatcher = self._testee()
        c = PlayCommand(target='B', url=self.DEFAULT_URL)
        stateful_dispatcher.play(c)
        stateful_dispatcher.play(c)

        integrator_constructor.assert_called_with(self.FAKE_PLAYER_B, self.FAKE_SERVER, self.FAKE_SCHEDULER)
        i.play.assert_called_with(c)
        ensure_online.assert_called_with(self.FAKE_PLAYER_B)

        # check state method aswell
        state_res = stateful_dispatcher.state(None)
        i.get_state.assert_called()
        self.FAKE_PLAYER_B.get_name.assert_called()
        self.assertTrue(state_res[0].player_name, 'B')

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
