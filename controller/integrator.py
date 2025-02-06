import logging
from enum import Enum

from controller.state import State, StateView
from controller.scheduler import Scheduler
from controller.exceptions import RequestInvalidException

from dlna.player import Player, TRANSPORT_STATE
from dlna.mediaserver import MediaServer

logger = logging.getLogger(__file__)


RUNNING_STATE = Enum('RunningState', ['RUNNING', 'STOPPED', 'INTERRUPTED', 'UNKNOWN'])


class Integrator():

    state: State
    _players: list[Player]
    media_server: MediaServer
    scheduler: Scheduler

    def __init__(self, renderers, media_server) -> None:
        self._players = []
        for r in renderers:
            self._players.append(Player(r))

        self.media_server = media_server

        self.state = State()
        self.scheduler = Scheduler()
        self.scheduler.start()

    def _search(self, title, artist):
        logger.debug('searching for title="{t}" of artist="{a}"'.format(t=title, a=artist))
        search_res = self.media_server.search(title=title, artist=artist)
        logger.debug('Found {} items'.format(search_res.get_matches()))
        return search_res

    def _play_next_track(self):
        if self.state.url is not None:
            # this mode always plays the same url
            logger.debug('playing without item')
            self._default_player().play(self.state.url)
            logger.debug('setting now_playing')
            self.state.now_playing(self.state.url, None)
            return

        if self.state.search_response is None:
            search_response = self._search(self.state.title, self.state.artist)
            self.state.search_response = search_response

        if (self.state.search_response.get_matches() > 0):
            item = self.state.search_response.random_item()
            url = item.get_url()

            logger.debug('playing with item')
            self._default_player().play(url, item=item)
            logger.debug('setting now_playing')
            self.state.now_playing(url, item)
        else:
            self._end("nothing found in media server")

    def _initiate(self, s: State) -> StateView:
        self._end("initiate new track")
        self.state = s

        self._play_next_track()

    def _loop_process(self):
        try:
            run_state = self._check_running()
            if RUNNING_STATE.INTERRUPTED == run_state:
                self._end("interrupted")
                return

            if RUNNING_STATE.RUNNING == run_state:
                return

            if RUNNING_STATE.STOPPED == run_state:
                if self.state.loop:
                    self._play_next_track()
                else:
                    self._end("not looping")
        except Exception as e:
            logger.info('error in loop_process', exc_info=e)
            # reset inner state
            self._end("exception in looping: " + str(e))
            raise e

    def _end(self, reason: str):
        logger.debug('ending integrator')
        print(f"ending due to {reason}")
        self.scheduler.stop_job()
        self.state.stop(reason)

    def _check_running(self) -> RUNNING_STATE:
        player_state = self._default_player().get_state()

        transport_state = player_state.transport_state
        track_URI = player_state.current_url

        if transport_state is TRANSPORT_STATE.NO_MEDIA_PRESENT:
            logger.debug('Found shutdown of renderer')
            return RUNNING_STATE.INTERRUPTED

        if self.state.last_played_url != track_URI:
            logger.debug('Found renderer plays different track')
            return RUNNING_STATE.INTERRUPTED

        # we know it's our track
        if transport_state is TRANSPORT_STATE.STOPPED:
            logger.debug('Found renderer stopped')
            return RUNNING_STATE.STOPPED
        if transport_state is TRANSPORT_STATE.PLAYING:
            logger.debug('Found renderer still running')
            return RUNNING_STATE.RUNNING

    def _validate_state(self, s: State):
        if s.title is None and s.artist is None and s.url is None:
            raise RequestInvalidException()

    def _default_player(self) -> Player:
        return self._players[0]

    # external methods

    def play(self, url, title, artist, loop: bool) -> StateView:
        logger.debug('play called')
        s: State = State()
        s.url = url
        s.title = title
        s.artist = artist
        s.loop = loop

        self._validate_state(s)
        try:
            self._initiate(s)
            logger.debug(f"current state {self.state.running} with count {self.state.played_count}")
            self.scheduler.start_job(self._loop_process)
        except Exception as e:
            logger.info('error while playing', exc_info=e)
            # reset inner state
            self._end("exception in play: " + str(e))
            raise e
        return self.state.view()

    def pause(self) -> StateView:
        logger.debug('pause called')
        self._end("pause invoked")
        try:
            self._default_player().pause()
        except Exception as e:
            # reset inner state
            self._end("exception in pause: " + str(e))
            raise e
        return self.state.view()

    def stop(self) -> StateView:
        logger.debug('stop called')
        self._end("stop invoked")
        try:
            self._default_player().stop()
        except Exception as e:
            # reset inner state
            self._end("exception in stop: " + str(e))
            raise e
        return self.state.view()

    def get_state(self) -> StateView:
        return self.state.view()
