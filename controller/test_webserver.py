import unittest
from unittest.mock import patch, MagicMock

from controller.webserver import WebServer
from controller.appinfo import AppInfo
from controller.data.exceptions import RequestCannotBeHandeledException, RequestInvalidException


class TestWebServer(unittest.TestCase):

    class MyState(dict):  # inherit from dict to make JSON serializable class

        def __init__(self, l_p_u):
            self.last_played_url = l_p_u

    DEFAULT_DISPATCHER: MagicMock = MagicMock()
    APPINFO: MagicMock = MagicMock(spec=AppInfo)

    DEFAULT_TARGET_JSON = {'target': 'a'}
    DEFAULT_JSON = {'target': 'a', 'url': 'url'}

    def _create_webserver(self, additional_config: dict = None) -> WebServer:
        config = {'webserver_port': 8080}
        if additional_config is not None:
            config = {**config, **additional_config}
        return WebServer(config, self.DEFAULT_DISPATCHER, self.APPINFO)

    def client(self, webserver=None):
        self._webserver = webserver
        if (not webserver):
            self._webserver = self._create_webserver()
        self._webserver.app.testing = True
        return self._webserver.app.test_client()

    def test_not_found(self):
        with self.client() as client:
            response = client.get("/foo-bar-not-found")
            self.assertEqual(404, response.status_code)
            self.assertTrue(b"error" in response.data)

    def test_index(self):
        with self.client() as client:
            response = client.get("/")
            self.assertEqual(200, response.status_code)
            self.assertEqual(b"DLNA Media Controller", response.data)

    def test_info(self):
        client = self.client()

        self.APPINFO.get.assert_not_called()
        response = client.get("/info")
        self.assertEqual(200, response.status_code)
        self.APPINFO.get.assert_called()

    def test_state(self):
        client = self.client()

        self.DEFAULT_DISPATCHER.state.return_value = {'foo': 'bar'}
        response = client.get("/state")
        self.assertEqual(200, response.status_code)
        self.DEFAULT_DISPATCHER.state.assert_called()

    def test_state_with_json(self):
        client = self.client()

        self.DEFAULT_DISPATCHER.state.return_value = {'foo': 'bar'}
        response = client.get("/state", json=self.DEFAULT_TARGET_JSON)
        self.assertEqual(200, response.status_code)
        self.DEFAULT_DISPATCHER.state.assert_called()

    def test_stop(self):
        client = self.client()

        self.DEFAULT_DISPATCHER.stop.return_value = {'foo': 'bar'}
        response = client.post("/stop", json=self.DEFAULT_TARGET_JSON)
        self.assertEqual(200, response.status_code)
        self.DEFAULT_DISPATCHER.stop.assert_called()

    def test_pause(self):
        client = self.client()

        self.DEFAULT_DISPATCHER.pause.return_value = {'foo': 'bar'}
        response = client.post("/pause", json=self.DEFAULT_TARGET_JSON)
        self.assertEqual(200, response.status_code)
        self.DEFAULT_DISPATCHER.pause.assert_called()

    def test_play_404(self):
        client = self.client()

        self.DEFAULT_DISPATCHER.play.return_value = TestWebServer.MyState(None)

        response = client.post("/play", json=self.DEFAULT_JSON)
        self.assertEqual(404, response.status_code)
        self.DEFAULT_DISPATCHER.play.assert_called()

    def test_play_200(self):
        client = self.client()

        self.DEFAULT_DISPATCHER.play.return_value = TestWebServer.MyState('foo')

        response = client.post("/play", json=self.DEFAULT_JSON)
        self.assertEqual(200, response.status_code)
        self.DEFAULT_DISPATCHER.play.assert_called()

    def test_play_request_invalid(self):
        client = self.client()

        self.DEFAULT_DISPATCHER.play.side_effect = RequestInvalidException()

        response = client.post("/play", json=self.DEFAULT_JSON)
        self.assertEqual(400, response.status_code)
        self.DEFAULT_DISPATCHER.play.assert_called()

    def test_play_request_cannot_handeled(self):
        client = self.client()

        self.DEFAULT_DISPATCHER.play.side_effect = RequestCannotBeHandeledException("foo")

        response = client.post("/play", json=self.DEFAULT_JSON)
        self.assertEqual(500, response.status_code)
        self.DEFAULT_DISPATCHER.play.assert_called()

    def test_play_error(self):
        client = self.client()

        self.DEFAULT_DISPATCHER.play.side_effect = KeyError()

        response = client.post("/play", json=self.DEFAULT_JSON)
        self.assertEqual(500, response.status_code)
        self.DEFAULT_DISPATCHER.play.assert_called()

    def test_pause_error(self):
        client = self.client()

        self.DEFAULT_DISPATCHER.pause.side_effect = KeyError()

        response = client.post("/pause", json=self.DEFAULT_TARGET_JSON)
        self.assertEqual(500, response.status_code)
        self.DEFAULT_DISPATCHER.pause.assert_called()

    def test_pause_request_cannot_handeled(self):
        client = self.client()

        self.DEFAULT_DISPATCHER.pause.side_effect = RequestCannotBeHandeledException("foo")

        response = client.post("/pause", json=self.DEFAULT_TARGET_JSON)
        self.assertEqual(500, response.status_code)
        self.DEFAULT_DISPATCHER.pause.assert_called()

    def test_pause_cors(self):
        config = {'webserver_port': 17, 'webserver_cors_allow': True}
        webserver = self._create_webserver(config)
        client = self.client(webserver)

        self.DEFAULT_DISPATCHER.pause.return_value = {'foo': 'bar'}
        response = client.post("/pause", json=self.DEFAULT_TARGET_JSON)
        self.assertEqual(200, response.status_code)
        self.assertTrue('Access-Control-Allow-Origin' in response.headers)
        self.assertEqual('*', response.headers.get('Access-Control-Allow-Origin'))
        self.DEFAULT_DISPATCHER.pause.assert_called()

    def test_exit(self):
        webserver = self._create_webserver()

        with patch.object(webserver, '_exit_program', wraps=webserver._exit_program) as wrapped_exit:
            wrapped_exit.return_value = None  # make it not a spy, thus method not called
            client = self.client(webserver)
            response = client.post("/exit")
            self.assertEqual(200, response.status_code)
            wrapped_exit.assert_called()
