import unittest
from unittest.mock import patch, call, MagicMock
import xml.etree.ElementTree as ET
from html import unescape

from dlna.dlna_helper import XML_HEADER
from dlna.player import Player, TRANSPORT_STATE
from dlna.items import Item


class TestPlayer(unittest.TestCase):

    DEFAULT_RENDERER_NAME = 'FakeRenderer'
    DEFAULT_URL = 'url'
    DEFAULT_HEADER = 'fake-header'

    class FakeRenderer:

        def get_name(self):
            return TestPlayer.DEFAULT_RENDERER_NAME

        def get_url(self):
            return TestPlayer.DEFAULT_URL

        def include_metadata(self):
            return False

    class FakeRendererWithMetadata(FakeRenderer):

        def include_metadata(self):
            return True

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

        create_header_mock.return_value = self.DEFAULT_HEADER

        p.pause()

        create_header_mock.assert_called_with('AVTransport', 'Pause')
        send_request_mock.assert_called_with(self.DEFAULT_URL, self.DEFAULT_HEADER, Player.PAUSE_BODY)

    @patch("dlna.dlna_helper.send_request")
    @patch("dlna.dlna_helper.create_header")
    def test_get_state(self, create_header_mock, send_request_mock):
        r = TestPlayer.FakeRenderer()
        p = Player(r)

        create_header_mock.return_value = self.DEFAULT_HEADER

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
            call(self.DEFAULT_URL, self.DEFAULT_HEADER, Player.POS_INFO_BODY),
            call(self.DEFAULT_URL, self.DEFAULT_HEADER, Player.TRANS_INFO_BODY)])

    @patch("dlna.dlna_helper.send_request")
    @patch("dlna.dlna_helper.create_header")
    def test_play(self, create_header_mock, send_request_mock):
        r = TestPlayer.FakeRenderer()
        p = Player(r)

        track_uri = 'track-uri'

        create_header_mock.return_value = self.DEFAULT_HEADER

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
            call(self.DEFAULT_URL, self.DEFAULT_HEADER, Player.PREPARE_BODY.format(url=track_uri, metadata='')),
            call(self.DEFAULT_URL, self.DEFAULT_HEADER, Player.TRANS_INFO_BODY),
            call(self.DEFAULT_URL, self.DEFAULT_HEADER, Player.PLAY_BODY)])

    VALID_ITEMS = """
    <DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/" xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" \n xmlns:dlna="urn:schemas-dlna-org:metadata-1-0/">
        <item id="64$1$1$12$2E$5" parentID="64$1$1$12$2E" restricted="1">
            <dc:title>FooBar</dc:title>
            <upnp:class>object.item.audioItem.musicTrack</upnp:class>
            <dc:creator>FooBarMan</dc:creator>
            <dc:date>1999-01-01</dc:date>
            <upnp:artist>FooBarMan</upnp:artist>
            <res size="5979512" duration="0:04:09.051" bitrate="192000" sampleFrequency="44100" nrAudioChannels="2" protocolInfo="http-get:*:audio/mpeg:DLNA.ORG_PN=MP3;DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000">http://127.0.0.1/MediaItems/4711.mp3</res>
        </item>
        <item id="64$0$0" parentID="64$0" restricted="1">
            <dc:title>Foo 1</dc:title>
            <upnp:class>object.item.audioItem.musicTrack</upnp:class>
            <dc:date>2025-03-01T20:58:38</dc:date>
            <res size="35782106" duration="0:00:16.166" bitrate="2213417" sampleFrequency="48000" nrAudioChannels="2" resolution="1920x1080" protocolInfo="http-get:*:video/mp4:DLNA.ORG_PN=AVC_MP4_HP_HD_AAC;DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000">http://127.0.0.1/MediaItems/1.mp4</res>
        </item>
        <item id="64$0$1" parentID="64$0" restricted="1">
            <dc:title>Foo 2</dc:title>
            <upnp:class>object.item.videoItem</upnp:class>
            <dc:date>2025-03-01T20:58:38</dc:date>
            <res size="29624890" duration="0:00:13.466" bitrate="2199976" sampleFrequency="48000" nrAudioChannels="2" resolution="1920x1080" protocolInfo="http-get:*:video/mp4:DLNA.ORG_PN=AVC_MP4_HP_HD_AAC;DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000">http://127.0.0.1/MediaItems/2.mp4</res>
        </item>
        <item id="64$0$2" parentID="64$0" restricted="1">
            <dc:title>Foo 3</dc:title>
            <upnp:class>object.item.videoItem</upnp:class>
            <dc:date>2025-03-01T20:58:38</dc:date>
            <res size="7656933" duration="0:00:03.627" bitrate="2111092" sampleFrequency="48000" nrAudioChannels="2" resolution="1920x1080" protocolInfo="http-get:*:video/mp4:DLNA.ORG_PN=AVC_MP4_HP_HD_AAC;DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000">http://127.0.0.1:8200/MediaItems/3.mp4</res>
        </item>
    </DIDL-Lite>
    """

    @patch("dlna.dlna_helper.send_request")
    @patch("dlna.dlna_helper.create_header")
    def test_play_with_audio_item(self, create_header_mock: MagicMock, send_request_mock: MagicMock):
        p = Player(TestPlayer.FakeRendererWithMetadata())

        root_el = ET.fromstring(XML_HEADER + unescape(self.VALID_ITEMS))
        first_item = root_el.find('r:item', {'r': 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/'})
        i = Item(first_item)
        # check precondition
        self.assertEqual("FooBarMan", i.get_creator())

        create_header_mock.return_value = self.DEFAULT_HEADER

        send_request_mock.side_effect = [
            None,  # SetAVTransportURI response is not used!
            TestPlayer.FakeResponse.create_transport_info('STOPPED'),
            None  # Play response not used
        ]

        p.play(None, item=i)

        create_header_mock.assert_has_calls([
            call('AVTransport', 'SetAVTransportURI'),
            call('AVTransport', 'GetTransportInfo'),
            call('AVTransport', 'Play')])

        # prepare body
        self.assertEqual(self.DEFAULT_URL, send_request_mock.mock_calls[0].args[0])
        self.assertEqual(self.DEFAULT_HEADER, send_request_mock.mock_calls[0].args[1])
        # check third argument
        xml_content = send_request_mock.mock_calls[0].args[2]
        # make sure it is a valid XML string
        ET.fromstring(xml_content)
        self.assertTrue(i.get_class() in xml_content)
        self.assertTrue(i.get_title() in xml_content)
        self.assertTrue(i.get_creator() in xml_content)
        self.assertTrue(i.get_artist() in xml_content)
        self.assertTrue(i.get_url() in xml_content)

        send_request_mock.assert_has_calls([
            call(self.DEFAULT_URL, self.DEFAULT_HEADER, Player.TRANS_INFO_BODY),
            call(self.DEFAULT_URL, self.DEFAULT_HEADER, Player.PLAY_BODY)])

    @patch("dlna.dlna_helper.send_request")
    @patch("dlna.dlna_helper.create_header")
    def test_play_with_video_item(self, create_header_mock: MagicMock, send_request_mock: MagicMock):
        p = Player(TestPlayer.FakeRendererWithMetadata())

        root_el = ET.fromstring(XML_HEADER + unescape(self.VALID_ITEMS))
        first_item = root_el.findall('r:item', {'r': 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/'})[3]
        i = Item(first_item)
        # check precondition
        self.assertEqual("Foo 3", i.get_title())

        create_header_mock.return_value = self.DEFAULT_HEADER

        send_request_mock.side_effect = [
            None,  # SetAVTransportURI response is not used!
            TestPlayer.FakeResponse.create_transport_info('STOPPED'),
            None  # Play response not used
        ]

        p.play(None, item=i)

        create_header_mock.assert_has_calls([
            call('AVTransport', 'SetAVTransportURI'),
            call('AVTransport', 'GetTransportInfo'),
            call('AVTransport', 'Play')])

        # prepare body
        self.assertEqual(self.DEFAULT_URL, send_request_mock.mock_calls[0].args[0])
        self.assertEqual(self.DEFAULT_HEADER, send_request_mock.mock_calls[0].args[1])
        # check third argument
        xml_content = send_request_mock.mock_calls[0].args[2]
        # make sure it is a valid XML string
        ET.fromstring(xml_content)
        self.assertTrue(i.get_class() in xml_content)
        self.assertTrue(i.get_title() in xml_content)
        self.assertTrue(i.get_url() in xml_content)

        send_request_mock.assert_has_calls([
            call(self.DEFAULT_URL, self.DEFAULT_HEADER, Player.TRANS_INFO_BODY),
            call(self.DEFAULT_URL, self.DEFAULT_HEADER, Player.PLAY_BODY)])
