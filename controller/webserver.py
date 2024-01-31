import logging
from flask.json import jsonify
import time
import os

from flask import Flask, make_response, request
from werkzeug.serving import make_server
from threading import Thread

from controller.integrator import Integrator
from controller.appinfo import AppInfo

logger = logging.getLogger(__file__)


class WebServer(Thread):

    NAME = "DLNA Media Controller"

    def __init__(self, config, integrator: Integrator, appinfo: AppInfo):
        """Create a new instance of the flask app"""
        super(WebServer, self).__init__()

        self.app = Flask(__name__)
        self.app.config['port'] = config['webserver_port']
        self.app.config['app_name'] = self.NAME
        self.app.config['webserver_cors_allow'] = config.get('webserver_cors_allow', False)
        self.app.app_context().push()

        self.integrator: Integrator = integrator
        self.appinfo = appinfo

        self._server = make_server(host='0.0.0.0', port=self.app.config['port'], app=self.app, threaded=True)
        print("Starting %s on port %d" % (self.app.config['app_name'], self.app.config['port']))

        # register some endpoints
        self.app.add_url_rule(rule="/", view_func=self.index, methods=['GET'])
        self.app.add_url_rule(rule="/play", view_func=self.play, methods=['POST'])
        self.app.add_url_rule(rule="/stop", view_func=self.stop, methods=['POST'])
        self.app.add_url_rule(rule="/pause", view_func=self.pause, methods=['POST'])
        self.app.add_url_rule(rule="/state", view_func=self.current_state, methods=['GET'])
        self.app.add_url_rule(rule="/exit", view_func=self.exit, methods=['GET', 'POST'])
        self.app.add_url_rule(rule="/info", view_func=self.info, methods=['GET'])

        # register default error handler
        self.app.register_error_handler(code_or_exception=404, f=self.not_found)

    def _add_cors_to_response(self, response):
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

    def _make_response_and_add_cors(self, *args):
        response = make_response(args)
        if (self.app.config['webserver_cors_allow']):
            self._add_cors_to_response(response)
        return response

    def run(self):
        self._server.serve_forever()

    def not_found(self, error):
        return self._make_response_and_add_cors(jsonify({'error': 'Not found'}), 404)

    def index(self):
        return self.NAME

    def _exit_program(self):
        time.sleep(3)
        logger.debug("shutting down")
        os._exit(0)

    def exit(self):
        """exit program"""
        thread = Thread(target=self._exit_program)
        thread.start()

        return self._make_response_and_add_cors("shutdown hereafter")

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
                return self._make_response_and_add_cors("Kein passenden Titel gefunden", 404)

            return self._make_response_and_add_cors(jsonify(state), 200)

        except Exception as e:
            logger.error(e)
            return self._make_response_and_add_cors("Fehler", 500)  # might also be 4xx

    def stop(self):
        return self._make_response_and_add_cors(jsonify(self.integrator.stop()), 200)

    def pause(self):
        return self._make_response_and_add_cors(jsonify(self.integrator.pause()), 200)

    def current_state(self):
        return self._make_response_and_add_cors(jsonify(self.integrator.state.view()), 200)

    def info(self):
        return self.appinfo.get()
