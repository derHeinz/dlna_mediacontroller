import unittest

from main import  setup_logging, create_media_servers


class TestMain(unittest.TestCase):

    RENDERER_CFG = [
        {"name": "Ex 1", "aliases": ["Radio"], "url": "http://x.y.z.1:12345/AVTransport/control",
         "capabilities": ["audio"], "send_metadata": True},
        {"name": "Ex 2", "aliases": ["TV"], "url": "http://x.y.z.2:12345/AVTransport/",
         "mac": "ab:cd:ef:12:34:56", "capabilities": ["audio", "video"], "send_metadata": True}
    ]

    def test_run_setup_logging(self):
        setup_logging()

    def test_create_mediaplayers(self):
        media_players_cfg = [
            {"name": "MS-A", "url": "http://x.y.z.3:12345/ContentDir"},
            {"name": "MS-B", "url": "http://x.y.z.4:12345/MediaServer/ContentDirectory/Control"}
        ]
        res = create_media_servers(media_servers_config=media_players_cfg)
        self.assertEqual(2, len(res))
        self.assertEqual("http://x.y.z.3:12345/ContentDir", res[0]._url)
        self.assertEqual("http://x.y.z.4:12345/MediaServer/ContentDirectory/Control", res[1]._url)
