import unittest
from unittest.mock import patch, call, MagicMock
import xml.etree.ElementTree as ET
from html import unescape

from dlna.dlna_helper import XML_HEADER
from dlna.player import Player, TRANSPORT_STATE
from dlna.items import Item


class TestPlayer(unittest.TestCase):

    DEFAULT_WITH_METADATA = True

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

    @patch("upnpclient.Device")
    def test_stop(self, device):
        p = Player(device, self.DEFAULT_WITH_METADATA)

        p.stop()
        device.assert_has_calls([
            call.AVTransport.Stop(InstanceID=0)
        ])

    @patch("upnpclient.Device")
    def test_pause(self, device):
        p = Player(device, self.DEFAULT_WITH_METADATA)

        p.pause()

        device.assert_has_calls([
            call.AVTransport.Pause(InstanceID=0)
        ])

    @patch("upnpclient.Device")
    def test_get_state(self, device):
        p = Player(device, self.DEFAULT_WITH_METADATA)

        device.AVTransport.GetTransportInfo.return_value = {'CurrentTransportState': 'NO_MEDIA_PRESENT'}
        device.AVTransport.GetPositionInfo.return_value = {'RelCount': '0'}
        device.AVTransport.GetMediaInfo.return_value = {'CurrentURI': 'a-track', 'NextURI': 'b-track'}

        res = p.get_state()
        self.assertEqual(TRANSPORT_STATE.NO_MEDIA_PRESENT, res.transport_state)
        self.assertEqual('a-track', res.current_url)
        self.assertEqual(0, res.progress_count)
        self.assertEqual('b-track', res.next_url)

        device.assert_has_calls([
            call.AVTransport.GetTransportInfo(InstanceID=0),
            call.AVTransport.GetPositionInfo(InstanceID=0),
            call.AVTransport.GetMediaInfo(InstanceID=0)
        ])

    @patch("upnpclient.Device")
    def test_play(self, device):
        p = Player(device, self.DEFAULT_WITH_METADATA)

        device.AVTransport.GetTransportInfo.return_value = {'CurrentTransportState': 'STOPPED'}

        track_uri = 'track-uri'

        p.play(track_uri)

        device.assert_has_calls([
            call.AVTransport.SetAVTransportURI(InstanceID=0, CurrentURI=track_uri, CurrentURIMetaData=None),
            call.AVTransport.GetTransportInfo(InstanceID=0),
        ])

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

    @patch("upnpclient.Device")
    def test_set_next(self, device):
        p = Player(device, self.DEFAULT_WITH_METADATA)

        track_uri = 'track-uri'
        root_el = ET.fromstring(XML_HEADER + unescape(self.VALID_ITEMS))
        first_item = root_el.find('r:item', {'r': 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/'})
        i = Item(first_item)
        p.set_next(track_uri, item=i)

        set_next_av = device.mock_calls[0]
        self.assertEqual('AVTransport.SetNextAVTransportURI', set_next_av[0])
        self.assertEqual(0, set_next_av[2]['InstanceID'])
        self.assertEqual(track_uri, set_next_av[2]['NextURI'])

        # check third argument
        xml_content = set_next_av[2].get('NextURIMetaData')
        # make sure it is a valid XML string
        ET.fromstring(unescape(xml_content))
        self.assertTrue(i.get_class() in xml_content)
        self.assertTrue(i.get_title() in xml_content)
        self.assertTrue(i.get_creator() in xml_content)
        self.assertTrue(i.get_artist() in xml_content)
        self.assertTrue(i.get_url() in xml_content)

    @patch("upnpclient.Device")
    def test_play_with_audio_item(self, device: MagicMock):
        p = Player(device, self.DEFAULT_WITH_METADATA)

        root_el = ET.fromstring(XML_HEADER + unescape(self.VALID_ITEMS))
        first_item = root_el.find('r:item', {'r': 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/'})
        i = Item(first_item)
        # check precondition
        self.assertEqual("FooBarMan", i.get_creator())

        device.AVTransport.GetTransportInfo.return_value = {'CurrentTransportState': 'STOPPED'}

        p.play(None, item=i)

        device.assert_has_calls([
            call.AVTransport.GetTransportInfo(InstanceID=0),
            call.AVTransport.Play(InstanceID=0, Speed='1'),
        ], any_order=True)
        set_av_transport_info_call_args = device.mock_calls[0][2]

        # check third argument
        xml_content = set_av_transport_info_call_args.get('CurrentURIMetaData')
        # make sure it is a valid XML string
        ET.fromstring(unescape(xml_content))
        self.assertTrue(i.get_class() in xml_content)
        self.assertTrue(i.get_title() in xml_content)
        self.assertTrue(i.get_creator() in xml_content)
        self.assertTrue(i.get_artist() in xml_content)
        self.assertTrue(i.get_url() in xml_content)

    @patch("upnpclient.Device")
    def test_play_with_video_item(self, device: MagicMock):
        p = Player(device, self.DEFAULT_WITH_METADATA)

        root_el = ET.fromstring(XML_HEADER + unescape(self.VALID_ITEMS))
        first_item = root_el.findall('r:item', {'r': 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/'})[3]
        i = Item(first_item)
        # check precondition
        self.assertEqual("Foo 3", i.get_title())
        device.AVTransport.GetTransportInfo.return_value = {'CurrentTransportState': 'STOPPED'}

        p.play(None, item=i)

        device.assert_has_calls([
            call.AVTransport.GetTransportInfo(InstanceID=0),
            call.AVTransport.Play(InstanceID=0, Speed='1'),
        ], any_order=True)
        set_av_transport_info_call_args = device.mock_calls[0][2]

        # check third argument
        xml_content = set_av_transport_info_call_args.get('CurrentURIMetaData')
        # make sure it is a valid XML string
        ET.fromstring(unescape(xml_content))
        self.assertTrue(i.get_class() in xml_content)
        self.assertTrue(i.get_title() in xml_content)
        self.assertTrue(i.get_url() in xml_content)
