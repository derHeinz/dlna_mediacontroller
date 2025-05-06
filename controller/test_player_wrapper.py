import unittest
from unittest.mock import patch, MagicMock
import json

from controller.player_wrapper import configure, discover, _create_discovered


class TestPlayerWrapper(unittest.TestCase):

    DEFAULT_URL = 'a-track'
    DEFAULT_CONFIG = {
        'name': 'test',
        'aliases': ['foo', 'bar'],
        'url': 'http://test.com',
        'mac': '4711',
        'capabilities': ['audio'],
        'send_metadata': True
    }

    DEFAULT_FRIENDLY_NAME = 'Chekov'
    DEFAULT_LOCATION = 'http://bla.foo'
    DEFAULT_UDN = '123456789'

    def _create_discoverable_player(self):
        disc_player = MagicMock()
        disc_player.friendly_name = self.DEFAULT_FRIENDLY_NAME
        disc_player.location = self.DEFAULT_LOCATION
        disc_player.udn = self.DEFAULT_UDN

        av_service = MagicMock()
        av_service.name = 'AVTransport'
        disc_player.services = [av_service]

        get_protocol_action = 'GetProtocolInfo'
        disc_player.actions = [get_protocol_action]

        protocol = {'Sink': 'only-audio-and-image'}
        disc_player.ConnectionManager.GetProtocolInfo.return_value = protocol

        return disc_player

    def create_discovered_player(self):
        device = MagicMock()
        device.friendly_name = 'foo'
        device.location = 'http://url.test'
        device.udn = 'id-0815'

        return _create_discovered(device)

    def test_simple_configured_device(self):
        p = configure(self.DEFAULT_CONFIG)

        self.assertEqual('test', p.get_name())
        self.assertEqual('http://test.com', p.get_url())
        self.assertIsNone(p.get_id())
        self.assertEqual('4711', p.get_mac())
        self.assertEqual(True, p.include_metadata())

        self.assertTrue(p.is_configured())
        self.assertFalse(p.is_detected())

        self.assertTrue(p.can_play_type('audio'))
        self.assertFalse(p.can_play_type('video'))
        self.assertFalse(p.can_play_type('image'))

        self.assertTrue('foo' in p.get_known_names())
        self.assertTrue('bar' in p.get_known_names())

        # check json dumpable
        json.dumps(p.to_view())

    @patch('upnpclient.discover')
    def test_simple_discovered(self, upnp_discover):
        discoverable_player = self._create_discoverable_player()
        upnp_discover.return_value = [discoverable_player]

        players = discover()
        self.assertEqual(1, len(players))
        p = players[0]

        self.assertEqual(self.DEFAULT_FRIENDLY_NAME, p.get_name())
        self.assertEqual(self.DEFAULT_LOCATION, p.get_url())
        self.assertEqual(self.DEFAULT_UDN, p.get_id())
        self.assertIsNone(p.get_mac())
        self.assertEqual(True, p.include_metadata())

        self.assertFalse(p.is_configured())
        self.assertTrue(p.is_detected())

        self.assertTrue(p.can_play_type('audio'))
        self.assertFalse(p.can_play_type('video'))
        self.assertTrue(p.can_play_type('image'))

        self.assertTrue(self.DEFAULT_FRIENDLY_NAME in p.get_known_names())

        # check json dumpable
        json.dumps(p.to_view())

    @patch('upnpclient.discover')
    def test_non_discoverable(self, upnp_discover):
        discoverable_player = self._create_discoverable_player()

        non_av_service = MagicMock()
        non_av_service.name = 'No-real-service'
        discoverable_player.services = [non_av_service]

        upnp_discover.return_value = [discoverable_player]

        players = discover()
        self.assertEqual(0, len(players))

    @patch('upnpclient.discover')
    def test_non_capability_detectable(self, upnp_discover):
        # test1: sink without any format -> no capabilities
        discoverable_player = self._create_discoverable_player()
        upnp_discover.return_value = [discoverable_player]
        protocol = {'Sink': 'only-5d-cinema'}
        discoverable_player.ConnectionManager.GetProtocolInfo.return_value = protocol

        players = discover()
        self.assertEqual(1, len(players))
        p = players[0]

        self.assertFalse(p.can_play_type('audio'))
        self.assertFalse(p.can_play_type('video'))
        self.assertFalse(p.can_play_type('image'))

        # tes2: no action defined -> no capabilities
        discoverable_player = self._create_discoverable_player()
        upnp_discover.return_value = [discoverable_player]
        discoverable_player.actions = []
        players = discover()
        self.assertEqual(1, len(players))
        p = players[0]

        self.assertFalse(p.can_play_type('audio'))
        self.assertFalse(p.can_play_type('video'))
        self.assertFalse(p.can_play_type('image'))

    @patch('upnpclient.discover')
    def test_all_capabilities(self, upnp_discover):

        discoverable_player = self._create_discoverable_player()
        upnp_discover.return_value = [discoverable_player]
        protocol = {'Sink': 'audio-video-and-image'}
        discoverable_player.ConnectionManager.GetProtocolInfo.return_value = protocol

        players = discover()
        self.assertEqual(1, len(players))
        p = players[0]

        self.assertTrue(p.can_play_type('audio'))
        self.assertTrue(p.can_play_type('video'))
        self.assertTrue(p.can_play_type('image'))

    @patch('upnpclient.Device')
    def test_configured(self, device_constructor: MagicMock):

        p = configure(self.DEFAULT_CONFIG)
        p.get_dlna_player()
        device_constructor.assert_called_with(self.DEFAULT_CONFIG['url'])

        device_constructor.reset_mock()
        p.get_dlna_player()
        device_constructor.assert_not_called()

    def test_configured_and_discovered(self):
        p = configure(self.DEFAULT_CONFIG)
        pd = self.create_discovered_player()

        # this is how they are merged together
        p._detected_meta = pd._detected_meta

        self.assertEqual('test', p.get_name())
        self.assertEqual('http://test.com', p.get_url())
        self.assertEqual('id-0815', p.get_id())
        self.assertEqual('4711', p.get_mac())
        self.assertEqual(True, p.include_metadata())

        self.assertTrue(p.is_configured())
        self.assertTrue(p.is_detected())

        self.assertTrue(p.can_play_type('audio'))
        self.assertFalse(p.can_play_type('video'))
        self.assertFalse(p.can_play_type('image'))

        self.assertTrue('foo' in p.get_known_names())
        self.assertTrue('bar' in p.get_known_names())

        # check json dumpable
        json.dumps(p.to_view())
