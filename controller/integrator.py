import logging
from enum import Enum

from controller.state import State, StateView
from controller.scheduler import Scheduler
from controller.exceptions import RequestInvalidException

from dlna.player import Player, TRANSPORT_STATE
from dlna.renderer import Renderer
from dlna.mediaserver import MediaServer

logger = logging.getLogger(__file__)


RUNNING_STATE = Enum('RunningState', ['RUNNING', 'STOPPED', 'INTERRUPTED', 'UNKNOWN'])


class Integrator():

    state: State
    player: Player
    player_name: str
    media_server: MediaServer
    scheduler: Scheduler

    def __init__(self, config) -> None:
        self.player = Player(Renderer(config.get('renderer_name'), config.get('renderer_url'), True))
        self.player_name = config.get('renderer_name')
        self.media_server = MediaServer(config.get('mediaserver_url'))

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
            self.player.play(self.state.url)
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
            self.player.play(url, item=item)
            logger.debug('setting now_playing')
            self.state.now_playing(url, item)
        else:
            self._end()

    def _initiate(self, s: State) -> StateView:
        assert s.last_played_url is None

        self._end()
        self.state = s

        self._play_next_track()

    def _loop_process(self):
        try:
            run_state = self._check_running()
            if RUNNING_STATE.INTERRUPTED == run_state:
                self._end()
                return

            if RUNNING_STATE.RUNNING == run_state:
                return

            if RUNNING_STATE.STOPPED == run_state:
                if self.state.loop:
                    self._play_next_track()
                else:
                    self._end()
        except Exception as e:
            logger.info('error in loop_process', exc_info=e)
            # reset inner state
            self._end()
            raise e

    def _end(self):
        logger.debug('ending integrator')
        self.scheduler.stop_job()
        self.state.stop()

    def _check_running(self) -> RUNNING_STATE:
        player_state = self.player.get_state()

        transport_state = player_state.transport_state
        track_URI = player_state.current_url

        if transport_state is TRANSPORT_STATE.NO_MEDIA_PRESENT:
            logger.info('Found shutdown of renderer')
            return RUNNING_STATE.INTERRUPTED

        if self.state.last_played_url != track_URI:
            logger.info('Found renderer plays different track')
            return RUNNING_STATE.INTERRUPTED

        # we know it's our track
        if transport_state is TRANSPORT_STATE.STOPPED:
            return RUNNING_STATE.STOPPED
        if transport_state is TRANSPORT_STATE.PLAYING:
            return RUNNING_STATE.RUNNING

    def _validate_state(self, s: State):
        if s.title is None and s.artist is None and s.url is None:
            raise RequestInvalidException()

    # external methods

    def play(self, url, title, artist, loop: bool) -> StateView:
        logger.debug('play called')
        s: State = State()
        s.url = url
        s.title = title
        s.artist = artist
        s.loop = loop

        try:
            self._validate_state(s)
            self._initiate(s)
            logger.debug(f"current state {self.state.running} with count {self.state.played_count}")
            self.scheduler.start_job(self._loop_process)
        except Exception as e:
            logger.info('error while playing', exc_info=e)
            # reset inner state
            self._end()
            raise e
        return self.state.view()

    def pause(self) -> StateView:
        logger.debug('pause called')
        self._end()
        try:
            self.player.pause()
        except Exception as e:
            # reset inner state
            self._end()
            raise e
        return self.state.view()

    def stop(self) -> StateView:
        logger.debug('stop called')
        self._end()
        try:
            self.player.stop()
        except Exception as e:
            # reset inner state
            self._end()
            raise e
        return self.state.view()

    def get_state(self) -> StateView:
        return self.state.view()
