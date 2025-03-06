import unittest
from dlna import dlna_helper


class TestDLNAHelper(unittest.TestCase):

    def test_namespace_free_res_element(self):

        # no content in res
        before = '''<bla:res xmlns:bla="blubb"></bla:res>'''
        after = '''<res></res>'''
        self.assertEqual(after, dlna_helper.namespace_free_res_element(before))

        # content in res
        before = '''<bla:res xmlns:bla="blubb">asdf</bla:res>'''
        after = '''<res>asdf</res>'''
        self.assertEqual(after, dlna_helper.namespace_free_res_element(before))

        # real life example
        before = '''<ns0:res xmlns:ns0="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/" size="3094117" duration="0:03:13.366" bitrate="128000" sampleFrequency="44100" nrAudioChannels="2" protocolInfo="http-get:*:audio/mpeg:DLNA.ORG_PN=MP3;DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000">http://192.168.0.9:8200/MediaItems/20971.mp3</ns0:res>'''
        after = '''<res size="3094117" duration="0:03:13.366" bitrate="128000" sampleFrequency="44100" nrAudioChannels="2" protocolInfo="http-get:*:audio/mpeg:DLNA.ORG_PN=MP3;DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000">http://192.168.0.9:8200/MediaItems/20971.mp3</res>'''
        self.assertEqual(after, dlna_helper.namespace_free_res_element(before))
