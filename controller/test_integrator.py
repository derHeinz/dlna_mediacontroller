import unittest
from unittest.mock import patch, call
from dataclasses import dataclass
import random

from controller.data.exceptions import RequestInvalidException
from controller.scheduler import Scheduler
from dlna.player import State as PlayerState, TRANSPORT_STATE
from controller.data.state import State
from controller.integrator import Integrator


@dataclass
class MyItem():

    title: str
    actor: str
    url: str

    def get_title(self):
        return self.title

    def get_actor(self):
        return self.actor

    def get_url(self):
        return self.url


@dataclass
class MySearchResponse():
    items: list[MyItem]

    def get_matches(self):
        return len(self.items)

    def random_item(self):
        return random.choice(self.items)


class FakePlayer:

    def __init__(self, name):
        self._name = name

    def get_name(self):
        return self._name

    def stop(self):
        pass

    def pause(self):
        pass

    def play(self, url):
        pass

    def get_state(self):
        pass


class FakeServer:

    def __init__(self, name):
        self._name = name

    def search(self):
        pass


class TestIntegrator(unittest.TestCase):

    DEFAULT_URL = 'a-track'
    DEFAULT_PLAYER_NAME = 'TestPlayer'

    FAKE_PLAYER = FakePlayer(DEFAULT_PLAYER_NAME)
    FAKE_SERVER = FakeServer('F')

    DEFAULT_MEDIASERVER_URL = 'qwertz'
    DEFAULT_ITEM = MyItem('Show must go on', 'Queen', 'url-queen')
    DEFAULT_RESPONSE = MySearchResponse([DEFAULT_ITEM])

    SCHEDULER = Scheduler()

    def _testee(self):
        self.SCHEDULER.start()
        return Integrator(self.FAKE_PLAYER, self.FAKE_SERVER, self.SCHEDULER)

    def _assert_state(self, state: State, url=None, artist=None, title=None, loop=False, running=False,
                      last_played_url=None, last_played_artist=None, last_played_title=None, played_count=0,
                      description="Aus", stop_reason=None):
        # first check internal state
        self.assertEqual(url, state.url)
        self.assertEqual(artist, state.artist)
        self.assertEqual(title, state.title)
        self.assertEqual(loop, state.loop)
        self.assertEqual(running, state.running)
        self.assertEqual(last_played_url, state.last_played_url)
        self.assertEqual(played_count, state.played_count)
        self.assertEqual(description, state.description)
        self.assertEqual(stop_reason, state.stop_reason)

        # now check state's view
        view = state.view()
        self.assertEqual(loop, view.loop)
        self.assertEqual(running, view.running)
        self.assertEqual(last_played_url, view.last_played_url)
        self.assertEqual(played_count, view.played_count)
        self.assertEqual(last_played_artist, view.last_played_artist)
        self.assertEqual(last_played_title, view.last_played_title)
        self.assertEqual(description, view.description)
        self.assertEqual(stop_reason, view.stop_reason)

    def _initial_play_url(self, integrator: Integrator, loop=False):
        res = integrator.play(self.DEFAULT_URL, None, None, loop)
        dsc = "Wiederholt " + self.DEFAULT_URL if loop else "Spielt " + self.DEFAULT_URL
        self._assert_state(integrator._state, url=self.DEFAULT_URL, last_played_url=self.DEFAULT_URL,
                           running=True, played_count=1, description=dsc, loop=loop)
        return res

    def _initial_play_item(self, integrator: Integrator, loop=False):  # TOOD add parameter loop!
        res = integrator.play(None, 'must go', None, loop)
        desc = "Spielt " + ("Lieder mit 'must go'" if loop else self.DEFAULT_ITEM.title + " von " + self.DEFAULT_ITEM.actor)
        self._assert_state(integrator._state, title='must go', last_played_url=self.DEFAULT_ITEM.url, loop=loop,
                           last_played_artist=self.DEFAULT_ITEM.actor, last_played_title=self.DEFAULT_ITEM.title,
                           running=True, played_count=1, description=desc)
        self.assertEqual(res, integrator._state.view())
        return res

    @patch("controller.scheduler.Scheduler.start")
    def test_constructor(self, start_scheduler_mock):
        i = self._testee()

        self._assert_state(i._state)

        start_scheduler_mock.assert_called()
        self.assertEqual(self.FAKE_PLAYER, i._player)
        self.assertEqual(self.FAKE_SERVER, i._media_server)
        self.assertNotEqual(None, i._state)

    def test_get_state(self):
        i = self._testee()

        self.assertEqual(i._state.view(), i.get_state())

    def test_play_validation(self):
        i = self._testee()

        with self.assertRaises(RequestInvalidException):
            i.play(None, None, None, False)
        self._assert_state(i._state, running=False)

    def test_pause(self):
        i = self._testee()

        self._initial_play_url(i)
        res = i.pause()
        self._assert_state(i._state, last_played_url=self.DEFAULT_URL, running=False, stop_reason="pause invoked")
        self.assertEqual(res, i._state.view())

    @patch("controller.integrator.Scheduler.stop_job")
    @patch("controller.integrator.Scheduler.start_job")
    @patch("controller.test_integrator.FakePlayer.pause")
    def test_pause_error(self, player_pause_mock, scheduler_start_mock, scheduler_stop_mock):
        i = self._testee()

        player_pause_mock.side_effect = OSError("test-error")
        with self.assertRaises(OSError):
            i.pause()
        self._assert_state(i._state, stop_reason="exception in pause: test-error")
        scheduler_stop_mock.assert_has_calls([call(self.DEFAULT_PLAYER_NAME)])
        scheduler_start_mock.assert_not_called()

    def test_stop(self):
        i = self._testee()

        self._initial_play_url(i)
        res = i.stop()
        self._assert_state(i._state, last_played_url=self.DEFAULT_URL, running=False, stop_reason="stop invoked")
        self.assertEqual(res, i._state.view())

    @patch("controller.integrator.Scheduler.stop_job")
    @patch("controller.integrator.Scheduler.start_job")
    @patch("controller.test_integrator.FakePlayer.stop")
    def test_stop_error(self, player_stop_mock, scheduler_start_mock, scheduler_stop_mock):
        i = self._testee()

        player_stop_mock.side_effect = OSError("test-error")
        with self.assertRaises(OSError):
            i.stop()
        self._assert_state(i._state, stop_reason="exception in stop: test-error")
        scheduler_stop_mock.assert_has_calls([call(self.DEFAULT_PLAYER_NAME)])
        scheduler_start_mock.assert_not_called()

    @patch("controller.scheduler.Scheduler.stop_job")
    @patch("controller.test_integrator.FakePlayer.play")
    def test_play_url_initial(self, player_play_mock, stop_job_mock):
        i = self._testee()

        self._initial_play_url(i)

        stop_job_mock.assert_called()
        player_play_mock.assert_called_with('a-track')

    @patch("controller.integrator.Scheduler.stop_job")
    @patch("controller.integrator.Scheduler.start_job")
    @patch("controller.test_integrator.FakePlayer.play")
    def test_play_loop_error(self, player_play_mock, scheduler_start_mock, scheduler_stop_mock):
        i = self._testee()

        player_play_mock.side_effect = OSError("test-error")
        with self.assertRaises(OSError):
            i.play(self.DEFAULT_URL, None, None, True)
        self._assert_state(i._state, stop_reason="exception in play: test-error")
        scheduler_stop_mock.assert_has_calls([call(self.DEFAULT_PLAYER_NAME)])
        scheduler_start_mock.assert_not_called()

    @patch("controller.test_integrator.FakeServer.search")
    @patch("controller.scheduler.Scheduler.stop_job")
    @patch("controller.test_integrator.FakePlayer.play")
    def test_play_item_initial(self, player_play_mock, stop_job_mock, mediaserver_search_mock):
        i = self._testee()

        # prepare mediaserver_mock
        mediaserver_search_mock.return_value = self.DEFAULT_RESPONSE

        self._initial_play_item(i)

        mediaserver_search_mock.assert_called_with(title='must go', artist=None)
        stop_job_mock.assert_called_with(self.DEFAULT_PLAYER_NAME)
        player_play_mock.assert_called_with(self.DEFAULT_ITEM.url, item=self.DEFAULT_ITEM)

    @patch("controller.test_integrator.FakeServer.search")
    @patch("controller.scheduler.Scheduler.stop_job")
    @patch("controller.test_integrator.FakePlayer.play")
    def test_play_item_not_found(self, player_play_mock, stop_job_mock, mediaserver_search_mock):
        i = self._testee()

        # prepare mediaserver_mock
        mediaserver_search_mock.return_value = MySearchResponse([])

        res = i.play(None, 'must go', None, False)
        self._assert_state(i._state, stop_reason="nothing found in media server")
        self.assertEqual(res, i._state.view())

        mediaserver_search_mock.assert_called_with(title='must go', artist=None)
        stop_job_mock.assert_called_with(self.DEFAULT_PLAYER_NAME)
        player_play_mock.assert_not_called()

        self._assert_state(i._state, stop_reason="nothing found in media server")

    @patch("controller.test_integrator.FakeServer.search")
    @patch("controller.integrator.Scheduler.stop_job")
    @patch("controller.integrator.Scheduler.start_job")
    @patch("controller.test_integrator.FakePlayer.play")
    def test_play_item_second(self, player_play_mock, scheduler_start_mock, scheduler_stop_mock, mediaserver_search_mock):
        i = self._testee()

        # prepare mediaserver_mock for first call
        testItem = MyItem('Show must go on', 'Queen', 'url-queen')
        mediaserver_search_mock.return_value = MySearchResponse([testItem])

        res = i.play(None, 'must go', None, False)
        self.assertEqual(res, i._state.view())
        self._assert_state(i._state, title='must go', last_played_url='url-queen',
                           last_played_artist='Queen', last_played_title='Show must go on',
                           running=True, played_count=1,
                           description="Spielt Show must go on von Queen")
        self.assertEqual(testItem, i._state.last_played_item)

        mediaserver_search_mock.assert_called_with(title='must go', artist=None)
        scheduler_stop_mock.assert_called()
        scheduler_start_mock.assert_called()
        player_play_mock.assert_called_with('url-queen', item=testItem)

        # prepare mocks for second call
        player_play_mock.reset_mock()
        scheduler_start_mock.reset_mock()
        scheduler_stop_mock.reset_mock()
        mediaserver_search_mock.reset_mock()
        testItem = MyItem('Narcotic', 'Liquido', 'url-liquido')
        mediaserver_search_mock.return_value = MySearchResponse([testItem])

        res = i.play(None, 'narco', None, False)
        self._assert_state(i._state, title='narco', last_played_url='url-liquido', running=True, played_count=1,
                           description="Spielt Narcotic von Liquido", last_played_artist='Liquido',
                           last_played_title='Narcotic')
        self.assertEqual(testItem, i._state.last_played_item)
        self.assertNotEqual(None, i._state.last_played_item)

        mediaserver_search_mock.assert_called_with(title='narco', artist=None)
        scheduler_stop_mock.assert_called()
        scheduler_start_mock.assert_called()
        player_play_mock.assert_called_with('url-liquido', item=testItem)

    @patch("controller.integrator.Scheduler.stop_job")
    @patch("controller.integrator.Scheduler.start_job")
    @patch("controller.test_integrator.FakePlayer.get_state")
    @patch("controller.test_integrator.FakePlayer.play")
    def test_play_url_with_loops_not_looping(self, player_play_mock, player_get_state_mock, start_job_mock, stop_job_mock):
        i = self._testee()

        self._initial_play_url(i)
        start_job_mock.assert_has_calls([call(self.DEFAULT_PLAYER_NAME, i._loop_process)])
        stop_job_mock.assert_has_calls([call(self.DEFAULT_PLAYER_NAME)])
        player_play_mock.assert_has_calls([call('a-track')])

        # first loop, stop playing
        player_get_state_mock.return_value = PlayerState(TRANSPORT_STATE.STOPPED, 'a-track', 0)

        i._loop_process()
        player_get_state_mock.assert_has_calls([call()])
        self._assert_state(i._state, last_played_url='a-track', running=False, description="Aus", stop_reason="not looping")

    @patch("controller.integrator.Scheduler.stop_job")
    @patch("controller.integrator.Scheduler.start_job")
    @patch("controller.test_integrator.FakePlayer.get_state")
    @patch("controller.test_integrator.FakePlayer.play")
    def test_play_url_with_loops(self, player_play_mock, player_get_state_mock, start_job_mock, stop_job_mock):
        i = self._testee()

        self._initial_play_url(i, True)
        start_job_mock.assert_has_calls([call(self.DEFAULT_PLAYER_NAME, i._loop_process)])
        stop_job_mock.assert_has_calls([call(self.DEFAULT_PLAYER_NAME)])
        player_play_mock.assert_has_calls([call('a-track')])

        # first loop, still playing
        player_get_state_mock.return_value = PlayerState(TRANSPORT_STATE.PLAYING, 'a-track', 42)

        i._loop_process()
        player_get_state_mock.assert_has_calls([call()])
        self._assert_state(i._state, url='a-track', last_played_url='a-track', running=True, played_count=1, loop=True,
                           description="Wiederholt a-track")

        # second loop, playing stopped
        player_play_mock.reset_mock()
        player_get_state_mock.reset_mock()
        player_get_state_mock.return_value = PlayerState(TRANSPORT_STATE.STOPPED, 'a-track', 0)

        i._loop_process()
        player_get_state_mock.assert_has_calls([call()])
        player_play_mock.assert_has_calls([call('a-track')])  # play track again
        self._assert_state(i._state, url='a-track', last_played_url='a-track', running=True, played_count=2, loop=True,
                           description="Wiederholt a-track")

    @patch("controller.test_integrator.FakeServer.search")
    @patch("controller.integrator.Scheduler")
    @patch("controller.test_integrator.FakePlayer.get_state")
    @patch("controller.test_integrator.FakePlayer.play")
    def test_play_item_with_loops(self, player_play_mock, player_get_state_mock, scheduler_mock, mediaserver_search_mock):
        i = self._testee()

        # prepare mocks
        mediaserver_search_mock.return_value = self.DEFAULT_RESPONSE

        self._initial_play_item(i, True)

        # prepare a loop that plays item again
        player_get_state_mock.reset_mock()
        player_play_mock.reset_mock()
        player_get_state_mock.return_value = PlayerState(TRANSPORT_STATE.STOPPED, self.DEFAULT_ITEM.url, 0)
        scheduler_mock.reset_mock()
        scheduler_instance_mock = scheduler_mock.return_value
        mediaserver_search_mock.reset_mock()

        # play item again (as it's the only one)
        i._loop_process()
        self._assert_state(i._state, title='must go', last_played_url=self.DEFAULT_ITEM.url, played_count=2,
                           last_played_artist="Queen", last_played_title="Show must go on",
                           running=True, loop=True, description="Spielt Lieder mit 'must go'")
        mediaserver_search_mock.assert_not_called()
        scheduler_instance_mock.start_job.assert_not_called()
        scheduler_instance_mock.stop_job.assert_not_called()
        player_get_state_mock.assert_called_with()
        player_play_mock.assert_called_with(self.DEFAULT_ITEM.url, item=self.DEFAULT_ITEM)

    @patch("controller.integrator.Scheduler.stop_job")
    @patch("controller.integrator.Scheduler.start_job")
    @patch("controller.test_integrator.FakePlayer.get_state")
    def test_play_url_with_loops_shutdown(self, player_get_state_mock, start_job_mock, stop_job_mock):
        i = self._testee()

        self._initial_play_url(i, True)

        # first loop, interrupted
        start_job_mock.reset_mock()
        stop_job_mock.reset_mock()
        player_get_state_mock.reset_mock()
        player_get_state_mock.return_value = PlayerState(TRANSPORT_STATE.NO_MEDIA_PRESENT, None, 0)

        i._loop_process()
        player_get_state_mock.assert_has_calls([call()])
        stop_job_mock.assert_called_with(self.DEFAULT_PLAYER_NAME)
        start_job_mock.assert_not_called()
        self._assert_state(i._state, running=False, loop=False, last_played_url=self.DEFAULT_URL, stop_reason="interrupted")

    @patch("controller.integrator.Scheduler.stop_job")
    @patch("controller.integrator.Scheduler.start_job")
    @patch("controller.test_integrator.FakePlayer.get_state")
    def test_play_url_with_loops_different_media(self, player_get_state_mock, start_job_mock, stop_job_mock):
        i = self._testee()

        self._initial_play_url(i, True)

        # first loop, interrupted with another title 'yet-another-track'
        start_job_mock.reset_mock()
        stop_job_mock.reset_mock()
        player_get_state_mock.reset_mock()
        player_get_state_mock.return_value = PlayerState(TRANSPORT_STATE.PLAYING, 'yet-another-track', 42)

        i._loop_process()
        player_get_state_mock.assert_has_calls([call()])
        stop_job_mock.assert_called_with(self.DEFAULT_PLAYER_NAME)
        start_job_mock.assert_not_called()
        self._assert_state(i._state, running=False, loop=False, last_played_url=self.DEFAULT_URL, description="Aus",
                           stop_reason="interrupted")
        
    @patch("controller.integrator.Scheduler.stop_job")
    @patch("controller.integrator.Scheduler.start_job")
    @patch("controller.test_integrator.FakePlayer.get_state")
    def test_play_url_with_loops_stopped_unnaturally(self, player_get_state_mock, start_job_mock, stop_job_mock):
        i = self._testee()

        self._initial_play_url(i, True)

        # first loop, interrupted due to unnaturally stoppage
        start_job_mock.reset_mock()
        stop_job_mock.reset_mock()
        player_get_state_mock.reset_mock()
        player_get_state_mock.return_value = PlayerState(TRANSPORT_STATE.STOPPED, self.DEFAULT_URL, 47)

        i._loop_process()
        player_get_state_mock.assert_has_calls([call()])
        stop_job_mock.assert_called_with(self.DEFAULT_PLAYER_NAME)
        start_job_mock.assert_not_called()
        self._assert_state(i._state, running=False, loop=False, last_played_url=self.DEFAULT_URL, description="Aus",
                           stop_reason="interrupted")

    @patch("controller.test_integrator.FakeServer.search")
    @patch("controller.integrator.Scheduler.stop_job")
    @patch("controller.integrator.Scheduler.start_job")
    @patch("controller.test_integrator.FakePlayer.play")
    def test_play_url_after_item(self, player_play_mock, start_job_mock, stop_job_mock, mediaserver_search_mock):
        i = self._testee()

        # prepare mediaserver_mock
        mediaserver_search_mock.return_value = self.DEFAULT_RESPONSE

        self._initial_play_item(i)

        start_job_mock.reset_mock()
        stop_job_mock.reset_mock()
        mediaserver_search_mock.reset_mock()

        # play url
        res = i.play(self.DEFAULT_URL, None, None, False)
        self._assert_state(i._state, url=self.DEFAULT_URL, running=True, last_played_url=self.DEFAULT_URL,
                           played_count=1, description="Spielt a-track")
        self.assertEqual(res, i._state.view())

        player_play_mock.assert_has_calls([call(self.DEFAULT_URL)])
        stop_job_mock.assert_has_calls([call(self.DEFAULT_PLAYER_NAME)])
        start_job_mock.assert_called_once()
        mediaserver_search_mock.assert_not_called()

    @patch("controller.test_integrator.FakeServer.search")
    @patch("controller.integrator.Scheduler.stop_job")
    @patch("controller.integrator.Scheduler.start_job")
    @patch("controller.test_integrator.FakePlayer.play")
    def test_play_item_not_found_after_item(self, player_play_mock, start_job_mock, stop_job_mock, mediaserver_search_mock):
        i = self._testee()

        # prepare mediaserver_mock
        mediaserver_search_mock.return_value = self.DEFAULT_RESPONSE
        self._initial_play_item(i)

        # prepare mocks for item not found
        start_job_mock.reset_mock()
        stop_job_mock.reset_mock()
        player_play_mock.reset_mock()
        mediaserver_search_mock.reset_mock()
        mediaserver_search_mock.return_value = MySearchResponse([])

        res = i.play(None, 'must go', None, False)
        self._assert_state(i._state, running=False, stop_reason="nothing found in media server")
        self.assertEqual(res, i._state.view())

        player_play_mock.assert_not_called()
        stop_job_mock.assert_called()
        start_job_mock.assert_called()
        mediaserver_search_mock.assert_called_with(title='must go', artist=None)

    @patch("controller.test_integrator.FakeServer.search")
    @patch("controller.integrator.Scheduler.stop_job")
    @patch("controller.integrator.Scheduler.start_job")
    @patch("controller.test_integrator.FakePlayer.play")
    def test_play_url_noloop_after_item_loop(self, player_play_mock, start_job_mock, stop_job_mock, mediaserver_search_mock):
        i = self._testee()

        # prepare mediaserver_mock
        mediaserver_search_mock.return_value = self.DEFAULT_RESPONSE

        self._initial_play_item(i, True)

        start_job_mock.reset_mock()
        stop_job_mock.reset_mock()
        mediaserver_search_mock.reset_mock()

        res = i.play(self.DEFAULT_URL, None, None, False)
        self._assert_state(i._state, url=self.DEFAULT_URL, last_played_url=self.DEFAULT_URL, running=True, played_count=1,
                           description="Spielt a-track")
        self.assertEqual(res, i._state.view())

        player_play_mock.assert_called_with(self.DEFAULT_URL)
        stop_job_mock.assert_called()
        start_job_mock.assert_called()
        mediaserver_search_mock.assert_not_called()

    @patch("controller.integrator.Scheduler.stop_job")
    @patch("controller.test_integrator.FakePlayer.get_state")
    def test_play_url_loop_error(self, player_get_state_mock, stop_job_mock):
        i = self._testee()

        self._initial_play_url(i, True)

        # first loop, error
        stop_job_mock.reset_mock()
        player_get_state_mock.side_effect = OSError("test-error")

        with self.assertRaises(OSError):
            i._loop_process()
        player_get_state_mock.assert_has_calls([call()])
        stop_job_mock.assert_called_with(self.DEFAULT_PLAYER_NAME)
        self._assert_state(i._state, last_played_url='a-track', running=False, loop=False, description='Aus',
                           stop_reason="exception in looping: test-error")
