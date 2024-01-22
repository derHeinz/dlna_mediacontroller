import logging
from flask.json import jsonify

from flask import Flask, make_response, request
from werkzeug.serving import make_server
from threading import Thread

from controller.integrator import Integrator

logger = logging.getLogger(__file__)


class WebServer(Thread):

    def __init__(self, integrator: Integrator):
        """Create a new instance of the flask app"""
        super(WebServer, self).__init__()

        self.app = Flask(__name__)
        self.app.config['port'] = 7777
        self.app.config['app_name'] = "DLNA Media Controller"
        self.app.app_context().push()

        self.integrator: Integrator = integrator

        self._server = make_server(host='0.0.0.0', port=self.app.config['port'], app=self.app, threaded=True)
        print("Starting %s on port %d" % (self.app.config['app_name'], self.app.config['port']))

        # register some endpoints
        self.app.add_url_rule(rule="/", view_func=self.index, methods=['GET'])
        self.app.add_url_rule(rule="/play", view_func=self.play, methods=['POST'])
        self.app.add_url_rule(rule="/stop", view_func=self.stop, methods=['POST'])
        self.app.add_url_rule(rule="/pause", view_func=self.pause, methods=['POST'])
        self.app.add_url_rule(rule="/state", view_func=self.current_state, methods=['GET'])

        # register default error handler
        self.app.register_error_handler(code_or_exception=404, f=self.not_found)

    def run(self):
        self._server.serve_forever()

    def not_found(self, error):
        return make_response(jsonify({'error': 'Not found'}), 404)

    def index(self):
        return 'Hello'

    def play(self):
        json = request.json

        url = json.get('url', None)
        title = json.get('title', None)
        artist = json.get('artist', None)
        loop = json.get('loop', False)
        logger.debug(f"extracted all information url:{url}, title:{title}, artist:{artist}, loop:{loop} ")

        try:
            state = self.integrator.play(url, title, artist, loop)
            if (state.last_played_url is None):
                return make_response("Kein passenden Titel gefunden", 404)

            return make_response(jsonify(state), 200)

        except Exception as e:
            logger.error(e)
            return make_response("Fehler", 500)  # might also be 4xx

    def stop(self):
        return make_response(jsonify(self.integrator.stop()), 200)

    def pause(self):
        return make_response(jsonify(self.integrator.pause()), 200)

    def current_state(self):
        return make_response(jsonify(self.integrator.state.view()), 200)
