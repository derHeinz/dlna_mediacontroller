import unittest
from unittest.mock import MagicMock, patch

from controller.player_manager import PlayerManager


class TestPlayerManager(unittest.TestCase):

    SCHEDULER: MagicMock = MagicMock()
    PLAYER_A: MagicMock = MagicMock()
    PLAYER_B: MagicMock = MagicMock()

    def _testee(self):
        self.SCHEDULER = MagicMock()
        m = PlayerManager([None], self.SCHEDULER)
        # mock the configured players
        m._players = [self.PLAYER_A, self.PLAYER_B]
        return m

    @patch("controller.player_manager.configure")
    def test_constructor(self, configure):

        m = self._testee()
        configure.assert_called()
        self.SCHEDULER.start_job.assert_called_with('PLAYER_DISCOVERY', m._run_discovery, m.DEFAULT_DISCOVERY_INTERVAL)

        self.assertEqual(self.PLAYER_A, m.get_players()[0])
        self.assertEqual(self.PLAYER_B, m.get_players()[1])

    @patch("controller.player_manager.configure")
    def test_getters(self, configure):
        m = self._testee()
        configure.assert_called()

        p = m.get_players()
        v = m.get_player_views()

    @patch("controller.player_manager.discover")
    @patch("controller.player_manager.configure")
    def test_discover_new_device(self, configure, discover):
        m = self._testee()
        configure.assert_called()

        new_discoverable_player = MagicMock()
        new_discoverable_player.get_url.return_value = 'URL'
        discover.return_value = [new_discoverable_player]

        self.assertEqual(2, len(m.get_players()))
        m._run_discovery()
        self.assertEqual(3, len(m.get_players()))
        self.assertEqual(new_discoverable_player, m.get_players()[2])

    @patch("controller.player_manager.discover")
    @patch("controller.player_manager.configure")
    def test_discover_new_devices(self, configure, discover):
        m = self._testee()
        configure.assert_called()

        new_discoverable_player_A = MagicMock()
        new_discoverable_player_A.get_url.return_value = 'URL'
        new_discoverable_player_B = MagicMock()
        new_discoverable_player_B.get_url.return_value = 'URL2'
        discover.return_value = [new_discoverable_player_A, new_discoverable_player_B]

        self.assertEqual(2, len(m.get_players()))
        m._run_discovery()
        self.assertEqual(4, len(m.get_players()))
        self.assertEqual(new_discoverable_player_A, m.get_players()[2])
        self.assertEqual(new_discoverable_player_B, m.get_players()[3])

    @patch("controller.player_manager.discover")
    @patch("controller.player_manager.configure")
    def test_discover_updated_devices(self, configure, discover):
        m = self._testee()
        configure.assert_called()

        # define stuff for "old" player
        self.PLAYER_B.get_url.return_value = 'URL'  # same as the discovered!
        self.PLAYER_A.get_url.return_value = 'URL2'  # same as the discovered!

        # define stuff for "discovered" player
        new_discoverable_player_A = MagicMock()
        new_discoverable_player_A.get_url.return_value = 'URL'
        new_discoverable_player_B = MagicMock()
        new_discoverable_player_B.get_url.return_value = 'URL2'
        discover.return_value = [new_discoverable_player_A, new_discoverable_player_B]

        self.assertEqual(2, len(m.get_players()))
        m._run_discovery()
        self.assertEqual(2, len(m.get_players()))

    @patch("controller.player_manager.discover")
    @patch("controller.player_manager.configure")
    def test_discover_updated_device(self, configure, discover):
        m = self._testee()
        configure.assert_called()

        # define stuff for "old" player
        self.PLAYER_B.get_url.return_value = 'URL'  # same as the discovered!
        self.PLAYER_B._detected_meta = 4711
        self.PLAYER_B._last_seen = 1234
        self.PLAYER_B._dlna_player = None

        # define stuff for "discovered" player
        new_discoverable_player = MagicMock()
        new_discoverable_player.get_url.return_value = 'URL'
        new_discoverable_player._detected_meta = 'something-else'
        new_discoverable_player._last_seen = 'yet-another-value'
        new_discoverable_player._dlna_player = 99665

        # define discovered device
        discover.return_value = [new_discoverable_player]

        self.assertEqual(2, len(m.get_players()))
        m._run_discovery()
        self.assertEqual(2, len(m.get_players()))

        p2 = m.get_players()[1]
        self.assertEqual(new_discoverable_player._detected_meta, p2._detected_meta)
        self.assertEqual(new_discoverable_player._last_seen, p2._last_seen)
        self.assertEqual(new_discoverable_player._dlna_player, p2._dlna_player)
