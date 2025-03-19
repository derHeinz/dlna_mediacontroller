from dlna.renderer import Renderer
import unittest


class TestRenderer(unittest.TestCase):

    def test_getters(self):
        rend = Renderer('myname', ['secondname', 'thirdname'], 'url', 'device_url', '4711', None, False)

        self.assertEqual('myname', rend.get_name())

        self.assertTrue('myname' in rend.get_known_names())
        self.assertTrue('secondname' in rend.get_known_names())
        self.assertTrue('thirdname' in rend.get_known_names())

        self.assertEqual('url', rend.get_url())
        self.assertEqual('4711', rend.get_mac())
        self.assertEqual(False, rend.include_metadata())

    def test_can_play_methods(self):
        audio_only_renderer = Renderer('bla', None, None, None, None, ['video'], None)

        self.assertTrue(audio_only_renderer.can_play_type('video'))
        self.assertFalse(audio_only_renderer.can_play_type('audio'))

    def test_known_names(self):
        testee = Renderer('a', ['foo', 'bar'], None, None, None, None, None)
        names = testee.get_known_names()
        self.assertTrue('a' in names)
        self.assertTrue('foo' in names)
        self.assertTrue('bar' in names)
