import unittest
from unittest.mock import patch, call
from dataclasses import dataclass
import random

from controller.exceptions import RequestInvalidException
from dlna.player import State as PlayerState, TRANSPORT_STATE
from controller.state import State, StateView
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


class TestIntegrator(unittest.TestCase):

    DEFAULT_URL = 'a-track'
    DEFAULT_RENDERER_URL = 'asdf'
    DEFAULT_RENDERER_NAME = 'Test'
    DEFAULT_MEDIASERVER_URL = 'qwertz'
    DEFAULT_ITEM = MyItem('Show must go on', 'Queen', 'url-queen')
    DEFAULT_RESPONSE = MySearchResponse([DEFAULT_ITEM])

    def _testee(self):
        return Integrator({'renderer_name': self.DEFAULT_RENDERER_NAME,
                           'renderer_url': self.DEFAULT_RENDERER_URL, 'server_url': self.DEFAULT_MEDIASERVER_URL})

    def _assert_state(self, state: State, url=None, artist=None, title=None, loop=False,
                      running=False, last_played_url=None, played_count=0):
        self.assertEqual(url, state.url)
        self.assertEqual(artist, state.artist)
        self.assertEqual(title, state.title)
        self.assertEqual(loop, state.loop)
        self.assertEqual(running, state.running)
        self.assertEqual(last_played_url, state.last_played_url)
        self.assertEqual(played_count, state.played_count)

    def _assert_state_view(self, view: StateView, loop=False, last_played_url=None, running=False,
                           played_count=0, last_played_artist=None, last_played_title=None):
        self.assertEqual(loop, view.loop)
        self.assertEqual(running, view.running)
        self.assertEqual(last_played_url, view.last_played_url)
        self.assertEqual(played_count, view.played_count)
        self.assertEqual(last_played_artist, view.last_played_artist)
        self.assertEqual(last_played_title, view.last_played_title)

    def _initial_play_url(self, integrator):
        res = integrator.play(self.DEFAULT_URL, None, None, False)
        self._assert_state_view(res, last_played_url=self.DEFAULT_URL, played_count=1, running=True)
        self._assert_state(integrator.state, url=self.DEFAULT_URL, last_played_url=self.DEFAULT_URL,
                           running=True, played_count=1)
        return res

    def _initial_play_item(self, integrator):
        res = integrator.play(None, 'must go', None, False)
        self._assert_state(integrator.state, title='must go', last_played_url=self.DEFAULT_ITEM.url,
                           running=True, played_count=1)
        self._assert_state_view(res, last_played_url=self.DEFAULT_ITEM.url, running=True, played_count=1,
                                last_played_artist=self.DEFAULT_ITEM.actor, last_played_title=self.DEFAULT_ITEM.title)
        return res

    @patch("controller.scheduler.Scheduler.start")
    def test_constructor(self, start_scheduler_mock):
        i = self._testee()

        self._assert_state(i.state)

        start_scheduler_mock.assert_called()
        self.assertEqual(self.DEFAULT_RENDERER_NAME, i.player_name)
        self.assertEqual(self.DEFAULT_RENDERER_URL, i.player.get_url())
        self.assertNotEqual(None, i.state)

    @patch("controller.scheduler.Scheduler.stop_job")
    def test_play_validation(self, stop_job_mock):
        i = self._testee()

        with self.assertRaises(RequestInvalidException):
            i.play(None, None, None, False)
        self._assert_state(i.state, running=False)
        stop_job_mock.assert_called_with()

    @patch("controller.integrator.Scheduler")
    @patch("controller.integrator.Player")
    def test_pause(self, player_mock, scheduler_mock):
        i = self._testee()

        self._initial_play_url(i)
        res = i.pause()
        self._assert_state(i.state, last_played_url=self.DEFAULT_URL, running=False)
        self._assert_state_view(res, last_played_url=self.DEFAULT_URL, running=False)

        player_mock.assert_called()
        scheduler_mock.assert_called()

    @patch("controller.integrator.Scheduler")
    @patch("controller.integrator.Player")
    def test_stop(self, player_mock, scheduler_mock):
        i = self._testee()

        self._initial_play_url(i)
        res = i.stop()

        self._assert_state(i.state, last_played_url=self.DEFAULT_URL, running=False)
        self._assert_state_view(res, last_played_url=self.DEFAULT_URL, running=False)

        player_mock.assert_called()
        scheduler_mock.assert_called()

    @patch("controller.scheduler.Scheduler.stop_job")
    @patch("dlna.player.Player.play")
    def test_play_url_initial(self, player_play_mock, stop_job_mock):
        i = self._testee()

        self._initial_play_url(i)

        stop_job_mock.assert_called()
        player_play_mock.assert_called_with('a-track')

    @patch("controller.integrator.Scheduler")
    @patch("dlna.player.Player.play")
    def test_play_loop_error(self, player_play_mock, scheduler_mock):
        i = self._testee()

        player_play_mock.side_effect = OSError()
        with self.assertRaises(OSError):
            i.play(self.DEFAULT_URL, None, None, True)
        self._assert_state(i.state)
        scheduler_instance_mock = scheduler_mock.return_value
        scheduler_instance_mock.stop_job.assert_has_calls([call()])
        scheduler_instance_mock.start_job.assert_not_called()

    @patch("dlna.mediaserver.MediaServer.search")
    @patch("controller.scheduler.Scheduler.stop_job")
    @patch("dlna.player.Player.play")
    def test_play_item_initial(self, player_play_mock, stop_job_mock, mediaserver_search_mock):
        i = self._testee()

        # prepare mediaserver_mock
        mediaserver_search_mock.return_value = self.DEFAULT_RESPONSE

        self._initial_play_item(i)

        mediaserver_search_mock.assert_called_with(title='must go', artist=None)
        stop_job_mock.assert_called_with()
        player_play_mock.assert_called_with(self.DEFAULT_ITEM.url, item=self.DEFAULT_ITEM)

    @patch("dlna.mediaserver.MediaServer.search")
    @patch("controller.scheduler.Scheduler.stop_job")
    @patch("dlna.player.Player.play")
    def test_play_item_not_found(self, player_play_mock, stop_job_mock, mediaserver_search_mock):
        i = self._testee()

        # prepare mediaserver_mock
        mediaserver_search_mock.return_value = MySearchResponse([])

        res = i.play(None, 'must go', None, False)
        self._assert_state(i.state)

        mediaserver_search_mock.assert_called_with(title='must go', artist=None)
        stop_job_mock.assert_called_with()
        player_play_mock.assert_not_called()

        self._assert_state_view(res)

    @patch("dlna.mediaserver.MediaServer.search")
    @patch("controller.scheduler.Scheduler.stop_job")
    @patch("dlna.player.Player.play")
    def test_play_item_second(self, player_play_mock, stop_job_mock, mediaserver_search_mock):
        i = self._testee()

        # prepare mediaserver_mock for first call
        testItem = MyItem('Show must go on', 'Queen', 'url-queen')
        mediaserver_search_mock.return_value = MySearchResponse([testItem])

        res = i.play(None, 'must go', None, False)

        self._assert_state(i.state, title='must go', last_played_url='url-queen', running=True, played_count=1)
        self._assert_state_view(res, last_played_url='url-queen', running=True, played_count=1,
                                last_played_artist='Queen', last_played_title='Show must go on')
        self.assertEqual(testItem, i.state.last_played_item)
        self.assertNotEqual(None, i.state.last_played_item)
        self.assertEqual('Queen', i.state.last_played_item.get_actor())
        self.assertEqual('Show must go on', i.state.last_played_item.get_title())
        self.assertEqual(True, i.state.running)

        mediaserver_search_mock.assert_called_with(title='must go', artist=None)
        stop_job_mock.assert_called_with()
        player_play_mock.assert_called_with('url-queen', item=testItem)

        # prepare mocks for second call
        player_play_mock.reset_mock()
        stop_job_mock.reset_mock()
        mediaserver_search_mock.reset_mock()
        testItem = MyItem('Narcotic', 'Liquido', 'url-liquido')
        mediaserver_search_mock.return_value = MySearchResponse([testItem])

        res = i.play(None, 'narco', None, False)
        self._assert_state(i.state, title='narco', last_played_url='url-liquido', running=True, played_count=1)
        self._assert_state_view(res, last_played_url='url-liquido', running=True, played_count=1,
                                last_played_artist='Liquido', last_played_title='Narcotic')
        self.assertEqual(testItem, i.state.last_played_item)
        self.assertNotEqual(None, i.state.last_played_item)
        self.assertEqual('Liquido', i.state.last_played_item.get_actor())
        self.assertEqual('Narcotic', i.state.last_played_item.get_title())
        self.assertEqual(True, i.state.running)

        mediaserver_search_mock.assert_called_with(title='narco', artist=None)
        stop_job_mock.assert_called_with()
        player_play_mock.assert_called_with('url-liquido', item=testItem)

    @patch("controller.integrator.Scheduler")
    @patch("controller.integrator.Player")
    def test_play_url_with_loops(self, player_mock, scheduler_mock):
        i = self._testee()

        i.play('a-track', None, None, True)
        self._assert_state(i.state, url='a-track', last_played_url='a-track', running=True, played_count=1, loop=True)
        self.assertEqual(1, i.state.played_count)

        scheduler_mock.assert_has_calls([call(),  # constructor call
                                         call().start(),
                                         call().stop_job(),
                                         call().start_job(i._loop_process)  # make sure loop_process has been called
                                         ])

        player_mock.assert_has_calls([  # constructor call omitted
                                      call().play('a-track')])

        # first loop, still playing
        scheduler_mock.reset_mock()
        player_mock.reset_mock()
        player_instance_mock = player_mock.return_value
        player_instance_mock.get_state.return_value = PlayerState(TRANSPORT_STATE.PLAYING, 'a-track')

        i._loop_process()
        player_instance_mock.get_state.assert_has_calls([call()])
        self._assert_state(i.state, url='a-track', last_played_url='a-track', running=True, played_count=1, loop=True)

        # second loop, playing stopped
        scheduler_mock.reset_mock()
        player_mock.reset_mock()
        player_instance_mock = player_mock.return_value
        player_instance_mock.get_state.return_value = PlayerState(TRANSPORT_STATE.STOPPED, 'a-track')

        i._loop_process()
        player_instance_mock.get_state.assert_has_calls([call()])
        player_instance_mock.play.assert_has_calls([call('a-track')])  # play track again
        self._assert_state(i.state, url='a-track', last_played_url='a-track', running=True, played_count=2, loop=True)

    @patch("dlna.mediaserver.MediaServer.search")
    @patch("controller.integrator.Scheduler")
    @patch("controller.integrator.Player")
    def test_play_item_with_loops(self, player_mock, scheduler_mock, mediaserver_search_mock):
        i = self._testee()

        # prepare mocks
        mediaserver_search_mock.return_value = self.DEFAULT_RESPONSE

        i.play(None, 'must go', None, True)
        self._assert_state(i.state, title='must go', last_played_url=self.DEFAULT_ITEM.url, running=True,
                           played_count=1, loop=True)

        # prepare a loop that plays item again
        player_mock.reset_mock()
        player_instance_mock = player_mock.return_value
        player_instance_mock.get_state.return_value = PlayerState(TRANSPORT_STATE.STOPPED, self.DEFAULT_ITEM.url)
        scheduler_mock.reset_mock()
        scheduler_instance_mock = scheduler_mock.return_value
        mediaserver_search_mock.reset_mock()

        # play item again (as it's the only one)
        i._loop_process()
        self._assert_state(i.state, title='must go', last_played_url=self.DEFAULT_ITEM.url, played_count=2,
                           running=True, loop=True)
        mediaserver_search_mock.assert_not_called()
        scheduler_instance_mock.start_job.assert_not_called()
        scheduler_instance_mock.stop_job.assert_not_called()
        player_instance_mock.get_state.assert_called_with()
        player_instance_mock.play.assert_called_with(self.DEFAULT_ITEM.url, item=self.DEFAULT_ITEM)

    @patch("controller.integrator.Scheduler")
    @patch("controller.integrator.Player")
    def test_play_url_with_loops_shutdown(self, player_mock, scheduler_mock):
        i = self._testee()

        i.play(self.DEFAULT_URL, None, None, True)
        self._assert_state(i.state, url=self.DEFAULT_URL, last_played_url=self.DEFAULT_URL, running=True,
                           played_count=1, loop=True)

        # first loop, interrupted
        scheduler_mock.reset_mock()
        scheduler_instance_mock = scheduler_mock.return_value
        player_mock.reset_mock()
        player_instance_mock = player_mock.return_value
        player_instance_mock.get_state.return_value = PlayerState(TRANSPORT_STATE.NO_MEDIA_PRESENT, None)

        i._loop_process()
        player_instance_mock.get_state.assert_has_calls([call()])
        scheduler_instance_mock.stop_job.assert_called_with()
        scheduler_instance_mock.start_job.assert_not_called()
        self._assert_state(i.state, running=False, loop=False, last_played_url=self.DEFAULT_URL)

    @patch("controller.integrator.Scheduler")
    @patch("controller.integrator.Player")
    def test_play_url_with_loops_different_media(self, player_mock, scheduler_mock):
        i = self._testee()

        i.play(self.DEFAULT_URL, None, None, True)
        self._assert_state(i.state, url=self.DEFAULT_URL, last_played_url=self.DEFAULT_URL, running=True,
                           played_count=1, loop=True)

        # first loop, interrupted
        scheduler_mock.reset_mock()
        scheduler_instance_mock = scheduler_mock.return_value
        player_mock.reset_mock()
        player_instance_mock = player_mock.return_value
        player_instance_mock.get_state.return_value = PlayerState(TRANSPORT_STATE.PLAYING, 'yet-another-track')

        i._loop_process()
        player_instance_mock.get_state.assert_has_calls([call()])
        scheduler_instance_mock.stop_job.assert_called_with()
        scheduler_instance_mock.start_job.assert_not_called()
        self._assert_state(i.state, running=False, loop=False, last_played_url=self.DEFAULT_URL)

    @patch("dlna.mediaserver.MediaServer.search")
    @patch("controller.integrator.Scheduler")
    @patch("controller.integrator.Player")
    def test_play_url_after_item(self, player_mock, scheduler_mock, mediaserver_search_mock):
        i = self._testee()

        # prepare mediaserver_mock
        mediaserver_search_mock.return_value = self.DEFAULT_RESPONSE

        self._initial_play_item(i)

        player_mock.reset_mock()
        player_instance_mock = player_mock.return_value
        scheduler_mock.reset_mock()
        scheduler_instance_mock = scheduler_mock.return_value
        mediaserver_search_mock.reset_mock()

        # play url
        res = i.play(self.DEFAULT_URL, None, None, False)
        self._assert_state(i.state, url=self.DEFAULT_URL, running=True, last_played_url=self.DEFAULT_URL,
                           played_count=1)
        self._assert_state_view(res, last_played_url=self.DEFAULT_URL, running=True, played_count=1)

        player_instance_mock.play.assert_has_calls([call(self.DEFAULT_URL)])
        scheduler_instance_mock.stop_job.assert_has_calls([call()])
        mediaserver_search_mock.assert_not_called()

    @patch("dlna.mediaserver.MediaServer.search")
    @patch("controller.integrator.Scheduler")
    @patch("controller.integrator.Player")
    def test_play_item_not_found_after_item(self, player_mock, scheduler_mock, mediaserver_search_mock):
        i = self._testee()

        # prepare mediaserver_mock
        mediaserver_search_mock.return_value = self.DEFAULT_RESPONSE
        self._initial_play_item(i)

        # prepare mocks for item not found
        player_mock.reset_mock()
        player_instance_mock = player_mock.return_value
        scheduler_mock.reset_mock()
        scheduler_instance_mock = scheduler_mock.return_value
        mediaserver_search_mock.reset_mock()
        mediaserver_search_mock.return_value = MySearchResponse([])

        res = i.play(None, 'must go', None, False)
        self._assert_state(i.state, running=False)
        self._assert_state_view(res)

        player_instance_mock.play.assert_not_called()
        scheduler_instance_mock.stop_job.assert_has_calls([call()])
        scheduler_instance_mock.start_job.assert_not_called()
        mediaserver_search_mock.assert_called_with(title='must go', artist=None)

    @patch("dlna.mediaserver.MediaServer.search")
    @patch("controller.integrator.Scheduler")
    @patch("controller.integrator.Player")
    def test_play_url_noloop_after_item_loop(self, player_mock, scheduler_mock, mediaserver_search_mock):
        i = self._testee()

        # prepare mediaserver_mock
        mediaserver_search_mock.return_value = self.DEFAULT_RESPONSE

        res = i.play(None, 'must go', None, True)
        self._assert_state(i.state, title='must go', last_played_url=self.DEFAULT_ITEM.url, running=True,
                           played_count=1, loop=True)
        self._assert_state_view(res, last_played_url=self.DEFAULT_ITEM.url, running=True, played_count=1, loop=True,
                                last_played_artist=self.DEFAULT_ITEM.actor, last_played_title=self.DEFAULT_ITEM.title)

        player_mock.reset_mock()
        player_instance_mock = player_mock.return_value
        scheduler_mock.reset_mock()
        scheduler_instance_mock = scheduler_mock.return_value
        mediaserver_search_mock.reset_mock()

        res = i.play(self.DEFAULT_URL, None, None, False)
        self._assert_state(i.state, url=self.DEFAULT_URL, last_played_url=self.DEFAULT_URL, running=True, played_count=1)
        self._assert_state_view(res, last_played_url=self.DEFAULT_URL, running=True, played_count=1)

        player_instance_mock.play.assert_called_with(self.DEFAULT_URL)
        scheduler_instance_mock.stop_job.assert_has_calls([call()])
        scheduler_instance_mock.start_job.assert_not_called()
        mediaserver_search_mock.assert_not_called()

    @patch("controller.integrator.Scheduler")
    @patch("controller.integrator.Player")
    def test_play_url_loop_error(self, player_mock, scheduler_mock):
        i = self._testee()

        i.play('a-track', None, None, True)
        self._assert_state(i.state, url='a-track', last_played_url='a-track', running=True, played_count=1, loop=True)

        # first loop, error
        scheduler_mock.reset_mock()
        scheduler_instance_mock = scheduler_mock.return_value
        player_mock.reset_mock()
        player_instance_mock = player_mock.return_value
        player_instance_mock.get_state.side_effect = OSError()

        with self.assertRaises(OSError):
            i._loop_process()
        player_instance_mock.get_state.assert_has_calls([call()])
        scheduler_instance_mock.stop_job.assert_called_with()
        self._assert_state(i.state, last_played_url='a-track', running=False, loop=False)
