import unittest
from unittest.mock import patch, call

from dlna.player import Player, TRANSPORT_STATE


class TestPlayer(unittest.TestCase):

    DEFAULT_RENDERER_NAME = 'FakeRenderer'
    DEFAULT_URL = 'url'

    class FakeRenderer:

        def get_name(self):
            return TestPlayer.DEFAULT_RENDERER_NAME

        def get_url(self):
            return TestPlayer.DEFAULT_URL

        def include_metadata(self):
            return False

    class FakeResponse:

        FAKE_POSITION_INFO = '''<?xml version="1.0" encoding="utf-8"?>
        <s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"
         xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
            <s:Body>
                <u:GetPositionInfoResponse xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
                    <Track>0</Track>
                    <TrackDuration>00:04:37</TrackDuration>
                    <TrackMetaData></TrackMetaData>
                    <TrackURI>{uri}</TrackURI>
                    <RelTime>00:00:00</RelTime>
                    <AbsTime>NOT_IMPLEMENTED</AbsTime>
                    <RelCount>{cnt}</RelCount>
                    <AbsCount>2147483647</AbsCount>
                </u:GetPositionInfoResponse>
            </s:Body>
        </s:Envelope>
        '''

        FAKE_TRANSPORT_INFO = '''<?xml version="1.0" encoding="utf-8"?>
        <s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"
         xmlns:s="http://schemas.xmlsoap.org/soap/envelope/">
            <s:Body>
                <u:GetTransportInfoResponse xmlns:u="urn:schemas-upnp-org:service:AVTransport:1">
                    <CurrentTransportState>{transport_state}</CurrentTransportState>
                    <CurrentTransportStatus>OK</CurrentTransportStatus>
                    <CurrentSpeed>1</CurrentSpeed>
                </u:GetTransportInfoResponse>
            </s:Body>
        </s:Envelope>
        '''

        class Decodeable:
            text: str

            def __init__(self, txt):
                self.text = txt

            def decode(self, encoding):
                assert encoding == 'utf-8'
                return self.text

        def __init__(self, txt):
            self.text = txt
            self.read_result = TestPlayer.FakeResponse.Decodeable(txt)

        def read(self):
            return self.read_result

        def create_position_info(uri, rel_count):
            txt = TestPlayer.FakeResponse.FAKE_POSITION_INFO.format(uri=uri, cnt=rel_count)
            return TestPlayer.FakeResponse(txt)

        def create_transport_info(transport_state):
            txt = TestPlayer.FakeResponse.FAKE_TRANSPORT_INFO.format(transport_state=transport_state)
            return TestPlayer.FakeResponse(txt)

    def test_getter(self):
        r = TestPlayer.FakeRenderer()
        p = Player(r)

        self.assertEqual('FakeRenderer', p.get_name())
        self.assertEqual(r, p.get_renderer())

    @patch("dlna.dlna_helper.send_request")
    @patch("dlna.dlna_helper.create_header")
    def test_stop(self, create_header_mock, send_request_mock):
        r = TestPlayer.FakeRenderer()
        p = Player(r)

        create_header_mock.return_value = 'bla'

        p.stop()

        create_header_mock.assert_called_with('AVTransport', 'Stop')
        send_request_mock.assert_called_with('url', 'bla', Player.STOP_BODY)

    @patch("dlna.dlna_helper.send_request")
    @patch("dlna.dlna_helper.create_header")
    def test_pause(self, create_header_mock, send_request_mock):
        r = TestPlayer.FakeRenderer()
        p = Player(r)

        create_header_mock.return_value = 'bla'

        p.pause()

        create_header_mock.assert_called_with('AVTransport', 'Pause')
        send_request_mock.assert_called_with('url', 'bla', Player.PAUSE_BODY)

    @patch("dlna.dlna_helper.send_request")
    @patch("dlna.dlna_helper.create_header")
    def test_play(self, create_header_mock, send_request_mock):
        r = TestPlayer.FakeRenderer()
        p = Player(r)

        track_uri = 'track-uri'

        fake_header = 'bla-header'
        create_header_mock.return_value = fake_header

        send_request_mock.side_effect = [
            None,  # SetAVTransportURI response is not used!
            TestPlayer.FakeResponse.create_transport_info('STOPPED'),
            None  # Play response not used
        ]

        p.play(track_uri)

        create_header_mock.assert_has_calls([
            call('AVTransport', 'SetAVTransportURI'),
            call('AVTransport', 'GetTransportInfo'),
            call('AVTransport', 'Play')])

        send_request_mock.assert_has_calls([
            call(self.DEFAULT_URL, fake_header, Player.PREPARE_BODY.format(url=track_uri, metadata='')),
            call(self.DEFAULT_URL, fake_header, Player.TRANS_INFO_BODY),
            call(self.DEFAULT_URL, fake_header, Player.PLAY_BODY)])

    @patch("dlna.dlna_helper.send_request")
    @patch("dlna.dlna_helper.create_header")
    def test_get_state(self, create_header_mock, send_request_mock):
        r = TestPlayer.FakeRenderer()
        p = Player(r)

        fake_header = 'bla-header'
        create_header_mock.return_value = fake_header

        fake_pos_info = TestPlayer.FakeResponse.create_position_info('a-track', 0)
        fake_transport_info = TestPlayer.FakeResponse.create_transport_info('NO_MEDIA_PRESENT')
        send_request_mock.side_effect = [fake_pos_info, fake_transport_info]

        res = p.get_state()
        self.assertEqual(TRANSPORT_STATE.NO_MEDIA_PRESENT, res.transport_state)
        self.assertEqual('a-track', res.current_url)
        self.assertEqual(0, res.progress_count)

        create_header_mock.assert_has_calls([
            call('AVTransport', 'GetPositionInfo'),
            call('AVTransport', 'GetTransportInfo')])

        send_request_mock.assert_has_calls([
            call(self.DEFAULT_URL, fake_header, Player.POS_INFO_BODY),
            call(self.DEFAULT_URL, fake_header, Player.TRANS_INFO_BODY)])
