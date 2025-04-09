import logging
from enum import Enum
from typing import Tuple

from controller.player_wrapper import PlayerWrapper
from controller.data.state import State, StateView
from controller.data.command import PlayCommand
from controller.scheduler import Scheduler
from controller.data.exceptions import RequestInvalidException

from dlna.player import TRANSPORT_STATE
from dlna.mediaserver import MediaServer

logger = logging.getLogger(__file__)


RUNNING_STATE = Enum('RunningState', ['RUNNING_CURRENT', 'RUNNING_NEXT', 
                                      'STOPPED', 'INTERRUPTED', 'UNKNOWN'])

NEXT_MEDIA_STATE = Enum('NextMediaState', ['SET', 'UNSET'])


class Integrator():

    DEFAULT_CHECK_INTERVAL = 10

    _state: State
    _player: PlayerWrapper
    _media_server: MediaServer
    _scheduler: Scheduler

    def __init__(self, player: PlayerWrapper, media_server: MediaServer, scheduler: Scheduler) -> None:
        self._player = player
        self._media_server = media_server
        self._state: State = State()
        self._scheduler = scheduler

    def _perform_media_search(self):
        # do the searching stuff
        search_args = {}
        search_args['title'] = self._state.current_command.title
        search_args['artist'] = self._state.current_command.artist
        search_args['type'] = self._state.current_command.type

        # remove None values (and it's keys) from dictionary
        search_args_cleaned = {k: v for k, v in search_args.items() if v is not None}

        # search the media server
        logger.debug(f"searching for {search_args_cleaned}")
        search_response = self._media_server.search(**search_args_cleaned)
        logger.debug('Found {} items'.format(search_response.get_matches()))
        return search_response

    def _next_track_is_current_track(self):
        # detected that the next track is beeing played and replaces the current track
        self._state.next_track_is_playing()

    def _set_next_track(self):
        if self._state.is_url_mode():
            # this mode always plays the same url
            logger.debug('next playing without item')
            self._player.get_dlna_player().set_next(self._state.current_command.url)
            self._state.next_play(self._state.current_command.url, None)
            return

        if self._state.search_response is None:
            # this is super unlikely, as we already played one item in _play_next_track
            logger.warning("Why don't we have a search_response, when setting next track?")
            self._state.search_response = self._perform_media_search()

        if (self._state.search_response.get_matches() > 0):
            item = self._state.search_response.random_item()
            url = item.get_url()

            logger.debug(f"next with item {item}")
            self._player.get_dlna_player().set_next(url, item=item)
            self._state.next_play(url, item)
        else:
            # this is very unlikely, as we must have come across in the previous call to _play_next_track
            logger.warning("Why come here, we should have been ended privously")
            self._end("nothing found in media server")

    def _play_next_track(self):
        if self._state.is_url_mode():
            # this mode always plays the same url
            logger.debug('playing without item')
            self._player.get_dlna_player().play(self._state.current_command.url)
            self._state.now_playing(self._state.current_command.url, None)
            if self._state.looping:
                self._set_next_track()
            return  # early return since it's a simple play the URL mode.

        if self._state.search_response is None:
            self._state.search_response = self._perform_media_search()

        if (self._state.search_response.get_matches() > 0):
            item = self._state.search_response.random_item()
            url = item.get_url()

            self._player.get_dlna_player().play(url, item=item)
            self._state.now_playing(url, item)
            if self._state.looping:
                self._set_next_track()
        else:
            self._end("nothing found in media server")

    def _initiate(self, s: State) -> StateView:
        self._end("initiate new track")
        self._state = s

        self._play_next_track()

    def _loop_process(self):
        try:
            run_state, next_state = self._check_running()
            if RUNNING_STATE.INTERRUPTED == run_state:
                self._end("interrupted")
                return

            if RUNNING_STATE.RUNNING_CURRENT == run_state:
                logger.debug("running current url")
                if self._state.looping and next_state == NEXT_MEDIA_STATE.UNSET:
                    logger.debug("next media to play is unset, setting next media")
                    self._set_next_track()
                return
        
            if RUNNING_STATE.RUNNING_NEXT == run_state:
                logger.debug("running the next media")
                if self._state.looping:
                    logger.debug("next is current, find a next media and set")
                    self._next_track_is_current_track()
                    self._set_next_track()
                else:
                    raise ValueError('What the hack happened, not looping but next track detected?')

            if RUNNING_STATE.STOPPED == run_state:
                if self._state.looping:
                    self._play_next_track()
                else:
                    self._end("not looping")

            if RUNNING_STATE.UNKNOWN == run_state:
                logger.info("unable to determine running state")

        except Exception as e:
            logger.info('error in loop_process', exc_info=e)
            # reset inner state
            self._end("exception in looping: " + str(e))
            raise e

    def _end(self, reason: str):
        logger.debug(f"ending integrator due to {reason}")
        self._scheduler.stop_job(self._scheduler_name())
        self._state.stop(reason)

    def _check_running(self) -> Tuple[RUNNING_STATE, NEXT_MEDIA_STATE]:
        player_state = self._player.get_dlna_player().get_state()

        transport_state = player_state.transport_state
        currently_played_url = player_state.current_url
        next_url = player_state.next_url

        if transport_state is TRANSPORT_STATE.TRANSITIONING:
            # may be the case
            # when transition between nothing and currentURI, or
            # when transitioning between currentURI and nextURI
            # thus say NEXT_MEDIA_STATE is unkonwn
            logger.debug('reads a ressource to be presented')
            return [RUNNING_STATE.RUNNING_CURRENT, None]

        if transport_state is TRANSPORT_STATE.NO_MEDIA_PRESENT:
            logger.debug('Found shutdown of renderer')
            return [RUNNING_STATE.INTERRUPTED, None]

        # check playback uri
        is_last_played_url = self._state.last_played_url == currently_played_url
        is_next_play_url = self._state.next_play_url == currently_played_url
        if (not is_last_played_url) and (not is_next_play_url):
            logger.debug('Found renderer plays unknown track')
            return [RUNNING_STATE.INTERRUPTED, None]

        if transport_state is TRANSPORT_STATE.STOPPED:
            if player_state.progress_count == 0:
                logger.debug('Found renderer stopped naturally (played until end)')
                return [RUNNING_STATE.STOPPED, None]
            else:
                logger.debug('Found renderer stopped unnaturally (in the middle of a track)')
                return [RUNNING_STATE.INTERRUPTED, None]

        if transport_state is TRANSPORT_STATE.PLAYING:
            logger.debug('Found renderer still running a track')

            if is_last_played_url:
                return [RUNNING_STATE.RUNNING_CURRENT, NEXT_MEDIA_STATE.SET if next_url else NEXT_MEDIA_STATE.UNSET]
            if is_next_play_url:
                # next_media may be set, but not by this process, so tell him it's unset.
                return [RUNNING_STATE.RUNNING_NEXT, NEXT_MEDIA_STATE.UNSET]
            else:
                # don't know what happened / unknown url playing
                return [RUNNING_STATE.INTERRUPTED, None]

    def _validate_state(self, s: State):
        if s.current_command.title is None and s.current_command.artist is None and s.current_command.url is None:
            raise RequestInvalidException()

    def _scheduler_name(self):
        return "Media_Observer_" + self._player.get_name()

    # external methods

    def play(self, command: PlayCommand) -> StateView:
        logger.debug('play called')
        s: State = State()
        s.command(command)

        self._validate_state(s)
        try:
            self._initiate(s)
            logger.debug(f"current state {self._state.running} with count {self._state.played_count}")
            self._scheduler.start_job(self._scheduler_name(), self._loop_process, self.DEFAULT_CHECK_INTERVAL)
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
            self._player.get_dlna_player().pause()
        except Exception as e:
            # reset inner state
            self._end("exception in pause: " + str(e))
            raise e
        return self._state.view()

    def stop(self) -> StateView:
        logger.debug('stop called')
        self._end("stop invoked")
        try:
            self._player.get_dlna_player().stop()
        except Exception as e:
            # reset inner state
            self._end("exception in stop: " + str(e))
            raise e
        return self._state.view()

    def get_state(self) -> StateView:
        return self._state.view()
