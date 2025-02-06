from dlna.renderer import Renderer
import unittest


class TestRenderer(unittest.TestCase):

    def test_can_play_methods(self):
        audio_only_renderer = Renderer('bla', None, None, None, ['audio'], None)

        self.assertTrue(audio_only_renderer.can_play_audio())
        self.assertFalse(audio_only_renderer.can_play_video())
