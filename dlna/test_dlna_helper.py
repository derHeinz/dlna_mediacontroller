import unittest
from dlna import dlna_helper
from unittest.mock import patch


class TestDLNAHelper(unittest.TestCase):

    @patch("dlna.dlna_helper.urlopen")
    @patch("dlna.dlna_helper.Request")
    def test_send_request(self, request_constructor, urlopen):
        dlna_helper.send_request('foo', 'bar', 'faz')

        request_constructor.assert_called_with('foo', 'faz'.encode('utf-8'), 'bar')
        urlopen.assert_called()

    def test_create_header(self):
        res = dlna_helper.create_header('foo', 'bar')
        self.assertTrue('foo' in res['Soapaction'])
        self.assertTrue('bar' in res['Soapaction'])

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
