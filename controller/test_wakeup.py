import unittest
from unittest.mock import MagicMock, patch, call
from urllib.error import HTTPError, URLError

from controller.wakeup import ensure_online


class FakeRenderer:

    def get_url(self):
        pass

    def get_mac(self):
        pass


class TestWakeup(unittest.TestCase):

    DEFAULT_MAC = "aa:bb:cc:dd:ee:ff"
    DEFAULT_URL = 'http://localhost:12345/test'
    DEFAULT_TIMEOUT = 0.2

    DEFAULT_ONLINE_ERROR = HTTPError(None, None, None, None, None)
    DEFAULT_OFFLINE_ERROR = URLError(None, None)

    DEFAULT_CHECK_CALL = call(DEFAULT_URL, timeout=DEFAULT_TIMEOUT)
    DEFAULT_WAKEUP_CALL = call(DEFAULT_MAC)

    def _testee_renderer(self):
        mock_renderer = MagicMock(spec=FakeRenderer)
        mock_renderer.get_mac.return_value = self.DEFAULT_MAC
        mock_renderer.get_url.return_value = self.DEFAULT_URL
        return mock_renderer

    @patch("controller.wakeup.urlopen")
    @patch("controller.wakeup.send_magic_packet")
    def test_online(self, wakeonlan, urlopen):

        mock_renderer = self._testee_renderer()

        self.assertTrue(ensure_online(mock_renderer))
        wakeonlan.assert_not_called()
        urlopen.assert_has_calls([self.DEFAULT_CHECK_CALL])

    @patch("controller.wakeup.urlopen")
    @patch("controller.wakeup.send_magic_packet")
    def test_online_without_mac(self, wakeonlan, urlopen):
        urlopen.side_effect = self.DEFAULT_ONLINE_ERROR

        mock_renderer = self._testee_renderer()
        mock_renderer.get_mac.return_value = None

        self.assertTrue(ensure_online(mock_renderer))
        wakeonlan.assert_not_called()
        urlopen.assert_has_calls([self.DEFAULT_CHECK_CALL])

    @patch("controller.wakeup.urlopen")
    @patch("controller.wakeup.send_magic_packet")
    def test_offline_without_mac(self, wakeonlan, urlopen):
        urlopen.side_effect = self.DEFAULT_OFFLINE_ERROR

        mock_renderer = self._testee_renderer()
        mock_renderer.get_mac.return_value = None

        self.assertFalse(ensure_online(mock_renderer))
        wakeonlan.assert_not_called()
        urlopen.assert_has_calls([self.DEFAULT_CHECK_CALL])

    @patch("controller.wakeup.urlopen")
    @patch("controller.wakeup.send_magic_packet")
    def test_with_mac_device_online(self, wakeonlan, urlopen):
        mock_renderer = self._testee_renderer()

        urlopen.side_effect = self.DEFAULT_ONLINE_ERROR

        self.assertTrue(ensure_online(mock_renderer))

        wakeonlan.assert_not_called()
        urlopen.assert_has_calls([self.DEFAULT_CHECK_CALL])

    @patch("controller.wakeup.urlopen")
    @patch("controller.wakeup.send_magic_packet")
    def test_with_mac_wake_device(self, wakeonlan, urlopen):

        mock_renderer = self._testee_renderer()

        # 3 calls, first 2 calls OFFLINE than ONLINE
        urlopen.side_effect = [self.DEFAULT_OFFLINE_ERROR, self.DEFAULT_OFFLINE_ERROR,
                               self.DEFAULT_OFFLINE_ERROR, self.DEFAULT_ONLINE_ERROR]

        self.assertTrue(ensure_online(mock_renderer))

        wakeonlan.assert_has_calls([self.DEFAULT_WAKEUP_CALL, self.DEFAULT_WAKEUP_CALL])
        urlopen.assert_has_calls([self.DEFAULT_CHECK_CALL, self.DEFAULT_CHECK_CALL, self.DEFAULT_CHECK_CALL])

    @patch("controller.wakeup.sleep")
    @patch("controller.wakeup.urlopen")
    @patch("controller.wakeup.send_magic_packet")
    def test_with_mac_wakeup_device_impossible(self, wakeonlan, urlopen, sleep):
        mock_renderer = self._testee_renderer()

        # always offline
        urlopen.side_effect = self.DEFAULT_OFFLINE_ERROR

        self.assertFalse(ensure_online(mock_renderer))

        wakeonlan.assert_has_calls([self.DEFAULT_WAKEUP_CALL, self.DEFAULT_WAKEUP_CALL, self.DEFAULT_WAKEUP_CALL,
                                    self.DEFAULT_WAKEUP_CALL, self.DEFAULT_WAKEUP_CALL, self.DEFAULT_WAKEUP_CALL,
                                    self.DEFAULT_WAKEUP_CALL, self.DEFAULT_WAKEUP_CALL, self.DEFAULT_WAKEUP_CALL,
                                    self.DEFAULT_WAKEUP_CALL])
        urlopen.assert_has_calls([self.DEFAULT_CHECK_CALL, self.DEFAULT_CHECK_CALL, self.DEFAULT_CHECK_CALL,
                                  self.DEFAULT_CHECK_CALL, self.DEFAULT_CHECK_CALL, self.DEFAULT_CHECK_CALL,
                                  self.DEFAULT_CHECK_CALL, self.DEFAULT_CHECK_CALL, self.DEFAULT_CHECK_CALL,
                                  self.DEFAULT_CHECK_CALL])
