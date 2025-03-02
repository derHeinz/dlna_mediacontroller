import unittest
import xml.etree.ElementTree as ET
from dlna.items import Item


def clean(txt):
    return txt.replace("  ", " ").replace("\t", "").replace("\n", "")


class TestItem(unittest.TestCase):

    EXAMPLE_ITEM = '''
    <ns0:item xmlns:dc="http://purl.org/dc/elements/1.1/"
     xmlns:ns0="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"
     xmlns:ns2="urn:schemas-upnp-org:metadata-1-0/upnp/"
     xmlns:ns3="urn:schemas-dlna-org:metadata-1-0/" id="64$1$1$D$4$F$E$7" parentID="64$1$1$D$4$F$E" restricted="1">
        <dc:title>I Was Born to Love You</dc:title>
        <ns2:class>object.item.audioItem.musicTrack</ns2:class>
        <dc:creator>Queen</dc:creator>
        <dc:date>1995-01-01</dc:date>
        <ns2:artist>Queen</ns2:artist>
        <ns2:album>Made in Heaven</ns2:album>
        <ns2:genre>Rock</ns2:genre>
        <ns2:originalTrackNumber>6</ns2:originalTrackNumber>
        <ns0:res size="4637479" duration="0:04:49.810" bitrate="128000"
         sampleFrequency="44100" nrAudioChannels="2"
         protocolInfo="http-get:*:audio/mpeg:DLNA.ORG_PN=MP3;DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000">http://127.0.0.1/MediaItems/20972.mp3</ns0:res>
        <ns2:albumArtURI ns3:profileID="JPEG_TN">http://127.0.0.1/AlbumArt/804-20972.jpg</ns2:albumArtURI>
    </ns0:item>
    '''

    EXAMPLE_ITEM_2 = '''
    <ns0:item xmlns:dc="http://purl.org/dc/elements/1.1/"
     xmlns:ns0="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"
     xmlns:ns2="urn:schemas-upnp-org:metadata-1-0/upnp/"
     xmlns:ns3="urn:schemas-dlna-org:metadata-1-0/" id="64$1$1$D$4$F$E$7" parentID="64$1$1$D$4$F$E" restricted="1">
        <dc:title>I Was Born to Love You</dc:title>
        <ns2:class>object.item.audioItem.musicTrack</ns2:class>
        <ns0:res size="4637479" duration="0:04:49.810" bitrate="128000"
         sampleFrequency="44100" nrAudioChannels="2"
         protocolInfo="http-get:*:audio/mpeg:DLNA.ORG_PN=MP3;DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000">http://127.0.0.1/MediaItems/20972.mp3</ns0:res>
    </ns0:item>
    '''

    def test_item_getters_example(self):
        i = Item(ET.fromstring(self.EXAMPLE_ITEM))

        self.assertEqual("I Was Born to Love You", i.get_title())
        self.assertEqual(None, i.get_actor())
        self.assertEqual("Queen", i.get_creator())
        self.assertEqual("Queen", i.get_artist())
        self.assertEqual(None, i.get_author())
        self.assertEqual("object.item.audioItem.musicTrack", i.get_class())
        self.assertEqual("http://127.0.0.1/MediaItems/20972.mp3", i.get_url())

    def test_item_getters_example_2(self):
        i = Item(ET.fromstring(self.EXAMPLE_ITEM_2))

        self.assertEqual("I Was Born to Love You", i.get_title())
        self.assertEqual("object.item.audioItem.musicTrack", i.get_class())
        self.assertEqual(None, i.get_actor())
        self.assertEqual(None, i.get_creator())
        self.assertEqual(None, i.get_artist())
        self.assertEqual(None, i.get_author())
    
        self.assertEqual("http://127.0.0.1/MediaItems/20972.mp3", i.get_url())

    def test_item_res(self):
        i = Item(ET.fromstring(self.EXAMPLE_ITEM))

        self.maxDiff = None
        res = '''<res size="4637479" duration="0:04:49.810" bitrate="128000" sampleFrequency="44100" nrAudioChannels="2" protocolInfo="http-get:*:audio/mpeg:DLNA.ORG_PN=MP3;DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000">http://192.168.0.1:8200/MediaItems/20972.mp3</res>'''
        res_as_str = ET.dump(ET.fromstring(i.get_res_as_string()))
        res_str = ET.dump(ET.fromstring(res))
        self.assertEqual(res_str, res_as_str)

    def test_item_getitem(self):
        i = Item(ET.fromstring(self.EXAMPLE_ITEM))

        val = ET.tostring(i.get_item(), encoding="utf-8", method="xml")
        self.assertEqual(val, i.get_item_as_string())
