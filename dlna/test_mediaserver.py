import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

from dlna.mediaserver import MediaServer
from dlna.search_responses import SearchResponse

class TestMediaserver(unittest.TestCase):

    EXAMPLE_ITEM = '''
    <reponse><Result>&lt;c&gt;d&lt;/c&gt;</Result><TotalMatches>42</TotalMatches><NumberReturned>42</NumberReturned></reponse>
    '''

    class FakeResponse:

        class Decodeable:
            text: str

            def __init__(self, txt):
                self.text = txt

            def decode(self, encoding):
                assert encoding == 'utf-8'
                return self.text

        def __init__(self, txt):
            self.text = txt
            self.read_result = TestMediaserver.FakeResponse.Decodeable(txt)

        def read(self):
            return self.read_result


    @patch("dlna.dlna_helper.send_request")
    @patch("dlna.dlna_helper.create_header")
    def test_search_basic(self, create_header_mock, send_request_mock):
        create_header_mock.return_value = 'bla'
        send_request_mock.return_value = TestMediaserver.FakeResponse(self.EXAMPLE_ITEM)
        
        ms = MediaServer('some-url')
        res = ms.search(title='foo')
        self.assertTrue(isinstance(res, SearchResponse))

        create_header_mock.assert_called_with('ContentDirectory', 'Search')

        send_request_mock.assert_called()
        self.assertTrue(send_request_mock.call_args.args[0], 'some-url')
        self.assertTrue(send_request_mock.call_args.args[1], 'bla')

        body = ET.fromstring(send_request_mock.call_args.args[2])
        # default size
        self.assertEqual(body.find('.//RequestedCount').text, str(200))
        # default type
        self.assertTrue(MediaServer.AUDIO in body.find('.//SearchCriteria').text)
        # default search title
        self.assertTrue('dc:title contains "foo"' in body.find('.//SearchCriteria').text)

    @patch("dlna.dlna_helper.send_request")
    @patch("dlna.dlna_helper.create_header")
    def test_search_artist(self, create_header_mock, send_request_mock):
        create_header_mock.return_value = 'bla'
        send_request_mock.return_value = TestMediaserver.FakeResponse(self.EXAMPLE_ITEM)
        
        ms = MediaServer('some-url')
        res = ms.search(artist='bar')
        self.assertTrue(isinstance(res, SearchResponse))

        send_request_mock.assert_called()
        body = ET.fromstring(send_request_mock.call_args.args[2])
        self.assertTrue('upnp:artist contains "bar"' in body.find('.//SearchCriteria').text)

    @patch("dlna.dlna_helper.send_request")
    @patch("dlna.dlna_helper.create_header")
    def test_search_sizes(self, create_header_mock, send_request_mock):
        create_header_mock.return_value = 'bla'
        send_request_mock.return_value = TestMediaserver.FakeResponse(self.EXAMPLE_ITEM)
        
        ms = MediaServer('asdf')
        with self.assertRaises(ValueError):
            ms.search(title='foo', max_size=47.11)

        with self.assertRaises(ValueError):
            ms.search(title='foo', max_size=-1)

        # as int
        ms.search(title='foo', max_size=300)
        body = ET.fromstring(send_request_mock.call_args.args[2])
        self.assertEqual(body.find('.//RequestedCount').text, str(300))
        send_request_mock.reset_mock()

        # as str
        ms.search(title='foo', max_size='42')
        body = ET.fromstring(send_request_mock.call_args.args[2])
        self.assertEqual(body.find('.//RequestedCount').text, str(42))
        send_request_mock.reset_mock()

    @patch("dlna.dlna_helper.send_request")
    @patch("dlna.dlna_helper.create_header")
    def test_search_types(self, create_header_mock, send_request_mock):
        create_header_mock.return_value = 'bla'
        send_request_mock.return_value = TestMediaserver.FakeResponse(self.EXAMPLE_ITEM)
        
        ms = MediaServer('asdf')
       
        # audio
        ms.search(title='foo', type='audio')
        body = ET.fromstring(send_request_mock.call_args.args[2])
        self.assertTrue(MediaServer.AUDIO in body.find('.//SearchCriteria').text)
        send_request_mock.reset_mock()

        # video
        ms.search(title='foo', type='video')
        body = ET.fromstring(send_request_mock.call_args.args[2])
        self.assertTrue(MediaServer.VIDEO in body.find('.//SearchCriteria').text)
        send_request_mock.reset_mock()

        # image
        ms.search(title='foo', type='image')
        body = ET.fromstring(send_request_mock.call_args.args[2])
        self.assertTrue(MediaServer.IMAGE in body.find('.//SearchCriteria').text)
        send_request_mock.reset_mock()

        # default
        ms.search(title='foo')
        body = ET.fromstring(send_request_mock.call_args.args[2])
        self.assertTrue(MediaServer.AUDIO in body.find('.//SearchCriteria').text)
        send_request_mock.reset_mock()

        with self.assertRaises(ValueError):
            ms.search(title='foo', type='somethingelse')
