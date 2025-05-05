import logging
from flask.json import jsonify
import time
import os

from flask import Flask, make_response, request
from werkzeug.serving import make_server
from threading import Thread

from controller.player_dispatcher import PlayerDispatcher
from controller.appinfo import AppInfo
from controller.data.exceptions import RequestInvalidException, RequestCannotBeHandeledException
from controller.data.command import Command, PlayCommand

logger = logging.getLogger(__file__)


class WebServer():

    NAME = "DLNA Media Controller"

    def __init__(self, config, dispatcher: PlayerDispatcher, appinfo: AppInfo):
        """Create a new instance of the flask app"""
        super(WebServer, self).__init__()

        self.app = Flask(__name__)
        self.app.config['port'] = config['webserver_port']
        self.app.config['app_name'] = self.NAME
        self.app.config['webserver_cors_allow'] = config.get('webserver_cors_allow', False)
        self.app.app_context().push()

        self.dispatcher: PlayerDispatcher = dispatcher
        self.appinfo = appinfo

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

    def serve(self):
        self._server = make_server(host='0.0.0.0', port=self.app.config['port'], app=self.app, threaded=True)
        print("Starting %s on port %d" % (self.app.config['app_name'], self.app.config['port']))
        self._server.serve_forever()

    def not_found(self, error):
        return self._make_response_and_add_cors(jsonify({'error': 'Not found'}), 404)

    def index(self):
        return self.NAME

    def _exit_program(self):
        time.sleep(3)
        logger.debug("shutting down")
        self._server.shutdown()

    def exit(self):
        """exit program"""
        thread = Thread(target=self._exit_program)
        thread.start()
        return self._make_response_and_add_cors("shutdown hereafter", 200)

    def play(self):
        logger.debug("in play")
        content = request.json
        play_command = PlayCommand(url=content.get('url'),
                                   artist=content.get('artist'),
                                   title=content.get('title'),
                                   target=content.get('target'),
                                   type=content.get('type'),
                                   loop=content.get('loop', False))
        logger.debug(f"extracted information {str(play_command)}")

        try:
            state = self.dispatcher.play(play_command)
            if (state.last_played_url is None):
                return self._make_response_and_add_cors("Kein passenden Titel gefunden", 404)

            return self._make_response_and_add_cors(jsonify(state), 200)
        except RequestInvalidException as e:
            logger.exception(e)
            return self._make_response_and_add_cors("Fehleingabe", 400)
        except RequestCannotBeHandeledException as e:
            logger.exception(e)
            return self._make_response_and_add_cors(e.msg, 500)
        except Exception as e:
            logger.exception(e)
            return self._make_response_and_add_cors("Fehler", 500)  # might also be 4xx

    def _commandable_method(self, func):
        command = None
        if request.is_json:
            content = request.json
            command = Command(content.get('target'))

        try:
            res = func(command)
            return self._make_response_and_add_cors(jsonify(res), 200)
        except RequestCannotBeHandeledException as e:
            logger.error(e)
            return self._make_response_and_add_cors(e.msg, 500)
        except Exception as e:
            logger.error(e)
            return self._make_response_and_add_cors("Fehler", 500)  # might also be 4xx

    def stop(self):
        return self._commandable_method(self.dispatcher.stop)

    def pause(self):
        return self._commandable_method(self.dispatcher.pause)

    def current_state(self):
        return self._commandable_method(self.dispatcher.state)

    def info(self):
        return self.appinfo.get()
