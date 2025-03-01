import logging
from enum import Enum

from controller.data.state import State, StateView
from controller.data.command import PlayCommand
from controller.scheduler import Scheduler
from controller.data.exceptions import RequestInvalidException

from dlna.player import Player, TRANSPORT_STATE
from dlna.mediaserver import MediaServer

logger = logging.getLogger(__file__)


RUNNING_STATE = Enum('RunningState', ['RUNNING', 'STOPPED', 'INTERRUPTED', 'UNKNOWN'])


class Integrator():

    _state: State
    _player: Player
    _media_server: MediaServer
    _scheduler: Scheduler

    def __init__(self, player: Player, media_server: MediaServer, scheduler: Scheduler) -> None:
        self._player = player
        self._media_server = media_server
        self._state: State = State()
        self._scheduler = scheduler

    def _play_next_track(self):
        if self._state.url is not None:
            # this mode always plays the same url
            logger.debug('playing without item')
            self._player.play(self._state.url)
            logger.debug('setting now_playing')
            self._state.now_playing(self._state.url, None)
            return

        if self._state.search_response is None:
            # do the searching stuff
            search_args = {}
            search_args['title'] = self._state.title
            search_args['artist'] = self._state.artist
            search_args['type'] = self._state.type

            # remove None values (and it's keys) from dictionary
            search_args_cleaned = {k: v for k, v in search_args.items() if v is not None}

            # search the media server
            logger.debug(f"searching for {search_args_cleaned}")
            self._state.search_response = self._media_server.search(**search_args_cleaned)
            logger.debug('Found {} items'.format(self._state.search_response.get_matches()))

        if (self._state.search_response.get_matches() > 0):
            item = self._state.search_response.random_item()
            url = item.get_url()

            logger.debug(f"playing with item {item}")
            self._player.play(url, item=item)
            logger.debug('setting now_playing')
            self._state.now_playing(url, item)
        else:
            self._end("nothing found in media server")

    def _initiate(self, s: State) -> StateView:
        self._end("initiate new track")
        self._state = s

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
                if self._state.loop:
                    self._play_next_track()
                else:
                    self._end("not looping")
        except Exception as e:
            logger.info('error in loop_process', exc_info=e)
            # reset inner state
            self._end("exception in looping: " + str(e))
            raise e

    def _end(self, reason: str):
        logger.debug(f"ending integrator due to {reason}")
        self._scheduler.stop_job(self._scheduler_name())
        self._state.stop(reason)

    def _check_running(self) -> RUNNING_STATE:
        player_state = self._player.get_state()

        transport_state = player_state.transport_state
        track_URI = player_state.current_url

        if transport_state is TRANSPORT_STATE.NO_MEDIA_PRESENT:
            logger.debug('Found shutdown of renderer')
            return RUNNING_STATE.INTERRUPTED

        if self._state.last_played_url != track_URI:
            logger.debug('Found renderer plays different track')
            return RUNNING_STATE.INTERRUPTED

        if transport_state is TRANSPORT_STATE.STOPPED:
            if player_state.progress_count == 0:
                logger.debug('Found renderer stopped naturally (played until end)')
                return RUNNING_STATE.STOPPED
            else:
                logger.debug('Found renderer stopped unnaturally (in the middle of a track)')
                return RUNNING_STATE.INTERRUPTED
        if transport_state is TRANSPORT_STATE.PLAYING:
            logger.debug('Found renderer still running')
            return RUNNING_STATE.RUNNING

    def _validate_state(self, s: State):
        if s.title is None and s.artist is None and s.url is None:
            raise RequestInvalidException()

    def _scheduler_name(self):
        return self._player.get_name()

    # external methods

    def play(self, command: PlayCommand) -> StateView:
        logger.debug('play called')
        s: State = State()
        s.url = command.url
        s.title = command.title
        s.artist = command.artist
        s.loop = command.loop
        s.type = command.type

        self._validate_state(s)
        try:
            self._initiate(s)
            logger.debug(f"current state {self._state.running} with count {self._state.played_count}")
            self._scheduler.start_job(self._scheduler_name(), self._loop_process)
        except Exception as e:
            logger.info('error while playing', exc_info=e)
            # reset inner state
            self._end("exception in play: " + str(e))
            raise e
        return self._state.view()

    def pause(self) -> StateView:
        logger.debug('pause called')
        self._end("pause invoked")
        try:
            self._player.pause()
        except Exception as e:
            # reset inner state
            self._end("exception in pause: " + str(e))
            raise e
        return self._state.view()

    def stop(self) -> StateView:
        logger.debug('stop called')
        self._end("stop invoked")
        try:
            self._player.stop()
        except Exception as e:
            # reset inner state
            self._end("exception in stop: " + str(e))
            raise e
        return self._state.view()

    def get_state(self) -> StateView:
        return self._state.view()
