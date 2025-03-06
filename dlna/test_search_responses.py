from dlna.search_responses import SearchResponse
import unittest


class TestSearchResponses(unittest.TestCase):

    EXAMPLE_RESPONSE = """<?xml version="1.0" encoding="utf-8"?>
        <s:Envelope xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"
        s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
        <s:Body><u:SearchResponse xmlns:u="urn:schemas-upnp-org:service:ContentDirectory:1">
        <Result>&lt;DIDL-Lite xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"
         xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" xmlns:dlna="urn:schemas-dlna-org:metadata-1-0/"&gt;
        &lt;item id="64$0$0" parentID="64$0" restricted="1"&gt;&lt;dc:title&gt;Foo 1&lt;/dc:title&gt;&lt;upnp:class&gt;object.item.videoItem&lt;/upnp:class&gt;&lt;dc:date&gt;2025-03-01T20:58:38&lt;/dc:date&gt;&lt;res size="35782106" duration="0:00:16.166" bitrate="2213417" sampleFrequency="48000" nrAudioChannels="2" resolution="1920x1080" protocolInfo="http-get:*:video/mp4:DLNA.ORG_PN=AVC_MP4_HP_HD_AAC;DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000"&gt;http://127.0.0.1/MediaItems/25091.mp4&lt;/res&gt;&lt;/item&gt;&lt;item id="64$0$1" parentID="64$0" restricted="1"&gt;&lt;dc:title&gt;Foo 1&lt;/dc:title&gt;&lt;upnp:class&gt;object.item.videoItem&lt;/upnp:class&gt;&lt;dc:date&gt;2025-03-01T20:58:38&lt;/dc:date&gt;&lt;res size="29624890" duration="0:00:13.466" bitrate="2199976" sampleFrequency="48000" nrAudioChannels="2" resolution="1920x1080" protocolInfo="http-get:*:video/mp4:DLNA.ORG_PN=AVC_MP4_HP_HD_AAC;DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000"&gt;http://127.0.0.1/MediaItems/25092.mp4&lt;/res&gt;&lt;/item&gt;&lt;item id="64$0$2" parentID="64$0" restricted="1"&gt;&lt;dc:title&gt;Foo 1&lt;/dc:title&gt;&lt;upnp:class&gt;object.item.videoItem&lt;/upnp:class&gt;&lt;dc:date&gt;2025-03-01T20:58:38&lt;/dc:date&gt;&lt;res size="7656933" duration="0:00:03.627" bitrate="2111092" sampleFrequency="48000" nrAudioChannels="2" resolution="1920x1080" protocolInfo="http-get:*:video/mp4:DLNA.ORG_PN=AVC_MP4_HP_HD_AAC;DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000"&gt;http://127.0.0.1/MediaItems/25093.mp4&lt;/res&gt;&lt;/item&gt;&lt;/DIDL-Lite&gt;
        </Result>
        <NumberReturned>3</NumberReturned>
        <TotalMatches>3</TotalMatches>
        <UpdateID>8</UpdateID></u:SearchResponse></s:Body></s:Envelope>"""

    def test_sr(self):
        res = SearchResponse(self.EXAMPLE_RESPONSE)

        self.assertEqual(3, res.get_matches())
        self.assertEqual(3, res.get_returned())

        first = res.first_item()
        self.assertEqual('Foo 1', first.get_title())

        some = res.random_item()
        self.assertEqual('Foo 1', some.get_title())
