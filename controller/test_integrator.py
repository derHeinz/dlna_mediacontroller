import unittest
from unittest.mock import patch, call, MagicMock
from dataclasses import dataclass

from controller.data.exceptions import RequestInvalidException
from controller.data.command import PlayCommand
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
    index: int = 0

    def get_matches(self):
        return len(self.items)

    def random_item(self):
        # not really random, just for testing :)
        res = self.items[self.index % len(self.items)]
        self.index += 1
        return res


class FakeServer:

    def __init__(self, name):
        self._name = name

    def search(self):
        pass


class TestIntegratorBase(unittest.TestCase):

    DEFAULT_URL = 'a-track'
    DEFAULT_PLAYER_NAME = 'TestPlayer'
    DEFAULT_PLAYER_SCHEDULER_NAME = 'Media_Observer_' + DEFAULT_PLAYER_NAME
    DEFAULT_SCHEDULER_INTERVAL = 10

    PLAYER: MagicMock
    PLAYER_DLNA: MagicMock
    FAKE_SERVER = FakeServer('F')

    DEFAULT_MEDIASERVER_URL = 'qwertz'
    DEFAULT_ITEM = MyItem('Show must go on', 'Queen', 'url-queen')
    DEFAULT_RESPONSE = MySearchResponse([DEFAULT_ITEM])

    SCHEDULER: MagicMock

    def _testee(self):
        self.PLAYER = MagicMock()
        self.PLAYER.get_name.return_value = self.DEFAULT_PLAYER_NAME
        self.PLAYER_DLNA = MagicMock()
        self.PLAYER.get_dlna_player.return_value = self.PLAYER_DLNA

        self.SCHEDULER = MagicMock()
        return Integrator(self.PLAYER, self.FAKE_SERVER, self.SCHEDULER)

    def tearDown(self):
        self.PLAYER_DLNA.reset_mock()
        self.SCHEDULER.reset_mock()

    def _assert_state(self, state: State, current_command=None, running=False, looping=False,
                      last_played_url=None, last_played_artist=None, last_played_title=None, played_count=0,
                      next_play_url=None, next_play_item=None, description="Aus", stop_reason=None):
        
        # first check internal state
        if current_command is not None:
            self.assertEqual(current_command.url, state.current_command.url)
            self.assertEqual(current_command.artist, state.current_command.artist)
            self.assertEqual(current_command.title, state.current_command.title)
            self.assertEqual(current_command.loop, state.current_command.loop)
        else:
            self.assertIsNone(state.current_command)

        self.assertEqual(running, state.running)
        self.assertEqual(last_played_url, state.last_played_url)
        self.assertEqual(played_count, state.played_count)
        self.assertEqual(description, state.description)
        self.assertEqual(stop_reason, state.stop_reason)
        self.assertEqual(next_play_url, state.next_play_url)
        self.assertEqual(next_play_item, state.next_play_item)

        # now check state's view
        view = state.view()
        self.assertEqual(looping, view.looping)
        self.assertEqual(running, view.running)
        self.assertEqual(last_played_url, view.last_played_url)
        self.assertEqual(played_count, view.played_count)
        self.assertEqual(last_played_artist, view.last_played_artist)
        self.assertEqual(last_played_title, view.last_played_title)
        self.assertEqual(description, view.description)
        self.assertEqual(stop_reason, view.stop_reason)

    def _initial_play_url(self, integrator: Integrator, loop=False):
        cmd = PlayCommand(url=self.DEFAULT_URL, artist=None, title=None, loop=loop)
        res = integrator.play(cmd)
        dsc = "Wiederholt " + self.DEFAULT_URL if loop else "Spielt " + self.DEFAULT_URL
        kwargs = {'current_command': cmd, 'last_played_url': self.DEFAULT_URL,
                  'running': True, 'played_count': 1, 'description': dsc, 'looping': loop}
        if loop:
            kwargs['next_play_url'] = self.DEFAULT_URL
        self._assert_state(integrator._state, **kwargs)
        return res

    def _initial_play_item(self, integrator: Integrator, command: PlayCommand, next_item=None):
        res = integrator.play(command)
        desc = "Spielt " + ("Lieder mit 'must go'" if command.loop else self.DEFAULT_ITEM.title + " von " + self.DEFAULT_ITEM.actor)
        kwargs = {'current_command': command, 'last_played_url': self.DEFAULT_ITEM.url,
                  'last_played_artist': self.DEFAULT_ITEM.actor, 'last_played_title': self.DEFAULT_ITEM.title,
                  'running': True, 'played_count': 1, 'description': desc, 'looping': command.loop}
        if command.loop:
            kwargs['next_play_url'] = self.DEFAULT_ITEM.url if next_item is None else next_item.url
            kwargs['next_play_item'] = self.DEFAULT_ITEM if next_item is None else next_item
        
        self._assert_state(integrator._state, **kwargs)
        self.assertEqual(res, integrator._state.view())
        return res


class TestIntegratorOtherFunctions(TestIntegratorBase):

    def test_constructor(self):
        i = self._testee()

        self._assert_state(i._state, current_command=None)

        self.assertEqual(self.PLAYER, i._player)
        self.assertEqual(self.SCHEDULER, i._scheduler)
        self.assertEqual(self.FAKE_SERVER, i._media_server)
        self.assertNotEqual(None, i._state)

    def test_get_state(self):
        i = self._testee()

        self.assertEqual(i._state.view(), i.get_state())

    def test_play_validation(self):
        i = self._testee()

        with self.assertRaises(RequestInvalidException):
            i.play(PlayCommand(url=None, artist=None, title=None, loop=False))
        self._assert_state(i._state, running=False)

    def test_pause(self):
        i = self._testee()

        self._initial_play_url(i)
        self.SCHEDULER.start_job.assert_called()
        res = i.pause()
        self.SCHEDULER.stop_job.assert_called()

        self._assert_state(i._state, last_played_url=self.DEFAULT_URL, running=False, stop_reason="pause invoked")
        self.assertEqual(res, i._state.view())

    def test_pause_error(self):
        i = self._testee()

        self.PLAYER_DLNA.pause.side_effect = OSError("test-error")
        with self.assertRaises(OSError):
            i.pause()
        self._assert_state(i._state, stop_reason="exception in pause: test-error")
        self.SCHEDULER.stop_job.assert_has_calls([call(self.DEFAULT_PLAYER_SCHEDULER_NAME)])
        self.SCHEDULER.start_job.assert_not_called()

    def test_stop(self):
        i = self._testee()

        self._initial_play_url(i)
        res = i.stop()
        self._assert_state(i._state, last_played_url=self.DEFAULT_URL, running=False, stop_reason="stop invoked")
        self.assertEqual(res, i._state.view())

    def test_stop_error(self):
        i = self._testee()

        self.PLAYER_DLNA.stop.side_effect = OSError("test-error")
        with self.assertRaises(OSError):
            i.stop()
        self._assert_state(i._state, stop_reason="exception in stop: test-error")
        self.SCHEDULER.stop_job.assert_has_calls([call(self.DEFAULT_PLAYER_SCHEDULER_NAME)])
        self.SCHEDULER.start_job.assert_not_called()


class TestIntegratorPlayFunctions(TestIntegratorBase):

    def test_play_url_initial(self):
        i = self._testee()

        self._initial_play_url(i)

        self.SCHEDULER.stop_job.assert_called()
        self.PLAYER_DLNA.play.assert_called_with('a-track')

    def test_play_loop_error(self):
        i = self._testee()

        self.PLAYER_DLNA.play.side_effect = OSError("test-error")
        with self.assertRaises(OSError):
            i.play(PlayCommand(url=self.DEFAULT_URL, artist=None, title=None, loop=True))
        self._assert_state(i._state, stop_reason="exception in play: test-error")
        self.SCHEDULER.stop_job.assert_has_calls([call(self.DEFAULT_PLAYER_SCHEDULER_NAME)])
        self.SCHEDULER.start_job.assert_not_called()

    @patch("controller.test_integrator.FakeServer.search")
    def test_play_item_initial(self, mediaserver_search_mock):
        i = self._testee()

        # prepare mediaserver_mock
        mediaserver_search_mock.return_value = self.DEFAULT_RESPONSE

        self._initial_play_item(i, PlayCommand(title='must go'))

        mediaserver_search_mock.assert_called_with(title='must go')
        self.SCHEDULER.stop_job.assert_called_with(self.DEFAULT_PLAYER_SCHEDULER_NAME)
        self.PLAYER_DLNA.play.assert_called_with(self.DEFAULT_ITEM.url, item=self.DEFAULT_ITEM)

    @patch("controller.test_integrator.FakeServer.search")
    def test_play_item_not_found(self, mediaserver_search_mock):
        i = self._testee()

        # prepare mediaserver_mock
        mediaserver_search_mock.return_value = MySearchResponse([])

        res = i.play(PlayCommand(url=None, artist=None, title='must go', loop=False))
        self._assert_state(i._state, stop_reason="nothing found in media server")
        self.assertEqual(res, i._state.view())

        mediaserver_search_mock.assert_called_with(title='must go')
        self.SCHEDULER.stop_job.assert_called_with(self.DEFAULT_PLAYER_SCHEDULER_NAME)
        self.PLAYER_DLNA.play.assert_not_called()

        self._assert_state(i._state, stop_reason="nothing found in media server")

    @patch("controller.test_integrator.FakeServer.search")
    def test_play_item_second(self, mediaserver_search_mock):
        i = self._testee()

        # prepare mediaserver_mock for first call
        testItem = MyItem('Show must go on', 'Queen', 'url-queen')
        mediaserver_search_mock.return_value = MySearchResponse([testItem])

        cmd_1 = PlayCommand(title='must go')
        res = i.play(cmd_1)
        self.assertEqual(res, i._state.view())
        self._assert_state(i._state, current_command=cmd_1, last_played_url='url-queen',
                           last_played_artist='Queen', last_played_title='Show must go on',
                           running=True, played_count=1,
                           description="Spielt Show must go on von Queen")
        self.assertEqual(testItem, i._state.last_played_item)

        mediaserver_search_mock.assert_called_with(title='must go')
        self.SCHEDULER.stop_job.assert_called()
        self.SCHEDULER.start_job.assert_called()
        self.PLAYER_DLNA.play.assert_called_with('url-queen', item=testItem)

        # prepare mocks for second call
        self.PLAYER_DLNA.play.reset_mock()
        self.SCHEDULER.reset_mock()
        mediaserver_search_mock.reset_mock()
        testItem = MyItem('Narcotic', 'Liquido', 'url-liquido')
        mediaserver_search_mock.return_value = MySearchResponse([testItem])

        cmd_2 = PlayCommand(title='narco')
        res = i.play(cmd_2)
        self._assert_state(i._state, current_command=cmd_2, last_played_url='url-liquido', running=True, played_count=1,
                           description="Spielt Narcotic von Liquido", last_played_artist='Liquido',
                           last_played_title='Narcotic')
        self.assertEqual(testItem, i._state.last_played_item)
        self.assertNotEqual(None, i._state.last_played_item)

        mediaserver_search_mock.assert_called_with(title='narco')
        self.SCHEDULER.stop_job.assert_called()
        self.SCHEDULER.start_job.assert_called()
        self.PLAYER_DLNA.play.assert_called_with('url-liquido', item=testItem)

    def test_play_url_with_loops_not_looping(self):
        i = self._testee()

        self._initial_play_url(i)
        self.SCHEDULER.start_job.assert_has_calls([call(self.DEFAULT_PLAYER_SCHEDULER_NAME, i._loop_process, self.DEFAULT_SCHEDULER_INTERVAL)])
        self.SCHEDULER.stop_job.assert_has_calls([call(self.DEFAULT_PLAYER_SCHEDULER_NAME)])
        self.PLAYER_DLNA.play.assert_has_calls([call('a-track')])

        # first loop, stop playing
        self.PLAYER_DLNA.get_state.return_value = PlayerState(transport_state=TRANSPORT_STATE.STOPPED,
                                                         current_url='a-track', progress_count=0,
                                                         next_url=None)

        i._loop_process()
        self.PLAYER_DLNA.get_state.assert_has_calls([call()])
        self._assert_state(i._state, last_played_url='a-track', running=False, description="Aus",
                           stop_reason="not looping")

    def test_play_url_with_loops(self):
        i = self._testee()

        cmd = PlayCommand(url=self.DEFAULT_URL, loop=True)
        self._initial_play_url(i, True)
        self.SCHEDULER.start_job.assert_has_calls([call(self.DEFAULT_PLAYER_SCHEDULER_NAME, i._loop_process, self.DEFAULT_SCHEDULER_INTERVAL)])
        self.SCHEDULER.stop_job.assert_has_calls([call(self.DEFAULT_PLAYER_SCHEDULER_NAME)])
        self.PLAYER_DLNA.play.assert_has_calls([call('a-track')])

        # first loop, still playing
        self.PLAYER_DLNA.get_state.return_value = PlayerState(transport_state=TRANSPORT_STATE.PLAYING,
                                                         current_url='a-track', progress_count=42,
                                                         next_url=None)

        i._loop_process()
        self.PLAYER_DLNA.get_state.assert_has_calls([call()])
        self._assert_state(i._state, current_command=cmd,
                           last_played_url='a-track', next_play_url='a-track',
                           running=True, played_count=1, looping=True,
                           description="Wiederholt a-track")

        # second loop, playing stopped
        self.PLAYER_DLNA.reset_mock()
        self.PLAYER_DLNA.get_state.return_value = PlayerState(TRANSPORT_STATE.STOPPED, 'a-track', None, 0)

        i._loop_process()
        self.PLAYER_DLNA.get_state.assert_has_calls([call()])
        self.PLAYER_DLNA.play.assert_has_calls([call('a-track')])  # play track again
        self._assert_state(i._state, current_command=cmd, 
                           last_played_url='a-track', next_play_url='a-track',
                           running=True, played_count=2, looping=True,
                           description="Wiederholt a-track")

    @patch("controller.test_integrator.FakeServer.search")
    def test_play_item_with_loops(self, mediaserver_search_mock):
        i = self._testee()

        # prepare mocks
        mediaserver_search_mock.return_value = self.DEFAULT_RESPONSE

        cmd = PlayCommand(title='must go', loop=True)
        self._initial_play_item(i, cmd)

        # prepare a loop that plays item again
        self.PLAYER_DLNA.reset_mock()
        self.PLAYER_DLNA.get_state.return_value = PlayerState(TRANSPORT_STATE.STOPPED, self.DEFAULT_ITEM.url, None, 0)
        mediaserver_search_mock.reset_mock()
        self.SCHEDULER.reset_mock()

        # play item again (as it's the only one)
        i._loop_process()
        self._assert_state(i._state, current_command=cmd, last_played_url=self.DEFAULT_ITEM.url, played_count=2,
                           last_played_artist="Queen", last_played_title="Show must go on",
                           running=True, looping=True, description="Spielt Lieder mit 'must go'",
                           next_play_url=self.DEFAULT_ITEM.url, next_play_item=self.DEFAULT_ITEM)
        mediaserver_search_mock.assert_not_called()
        self.SCHEDULER.start_job.assert_not_called()
        self.SCHEDULER.stop_job.assert_not_called()
        self.PLAYER_DLNA.get_state.assert_called_with()
        self.PLAYER_DLNA.play.assert_called_with(self.DEFAULT_ITEM.url, item=self.DEFAULT_ITEM)

    def test_play_url_with_loops_shutdown(self):
        i = self._testee()

        self._initial_play_url(i, True)

        # first loop, interrupted
        self.SCHEDULER.reset_mock()
        self.PLAYER_DLNA.get_state.reset_mock()
        self.PLAYER_DLNA.get_state.return_value = PlayerState(TRANSPORT_STATE.NO_MEDIA_PRESENT, None, None, 0)

        i._loop_process()
        self.PLAYER_DLNA.get_state.assert_has_calls([call()])
        self.SCHEDULER.stop_job.assert_called_with(self.DEFAULT_PLAYER_SCHEDULER_NAME)
        self.SCHEDULER.start_job.assert_not_called()
        self._assert_state(i._state, running=False, looping=False, last_played_url=self.DEFAULT_URL, stop_reason="interrupted")

    def test_play_url_with_loops_different_media(self):
        i = self._testee()

        self._initial_play_url(i, True)

        # first loop, interrupted with another title 'yet-another-track'
        self.SCHEDULER.reset_mock()
        self.PLAYER_DLNA.get_state.reset_mock()
        self.PLAYER_DLNA.get_state.return_value = PlayerState(TRANSPORT_STATE.PLAYING, 'yet-another-track', None, 42)

        i._loop_process()
        self.PLAYER_DLNA.get_state.assert_has_calls([call()])
        self.SCHEDULER.stop_job.assert_called_with(self.DEFAULT_PLAYER_SCHEDULER_NAME)
        self.SCHEDULER.start_job.assert_not_called()
        self._assert_state(i._state, running=False, last_played_url=self.DEFAULT_URL, description="Aus",
                           stop_reason="interrupted")

    def test_play_url_with_loops_stopped_unnaturally(self):
        i = self._testee()

        self._initial_play_url(i, True)

        # first loop, interrupted due to unnaturally stoppage
        self.SCHEDULER.reset_mock()
        self.PLAYER_DLNA.get_state.reset_mock()
        self.PLAYER_DLNA.get_state.return_value = PlayerState(TRANSPORT_STATE.STOPPED, self.DEFAULT_URL, None, 47)

        i._loop_process()
        self.PLAYER_DLNA.get_state.assert_has_calls([call()])
        self.SCHEDULER.stop_job.assert_called_with(self.DEFAULT_PLAYER_SCHEDULER_NAME)
        self.SCHEDULER.start_job.assert_not_called()
        self._assert_state(i._state, running=False, looping=False, last_played_url=self.DEFAULT_URL, description="Aus",
                           stop_reason="interrupted")

    @patch("controller.test_integrator.FakeServer.search")
    def test_play_url_after_item(self, mediaserver_search_mock):
        i = self._testee()

        # prepare mediaserver_mock
        mediaserver_search_mock.return_value = self.DEFAULT_RESPONSE

        cmd = PlayCommand(title='must go')
        self._initial_play_item(i, cmd)

        self.SCHEDULER.reset_mock()
        mediaserver_search_mock.reset_mock()

        # play url
        cmd_2 = PlayCommand(url=self.DEFAULT_URL, artist=None, title=None, loop=False)
        res = i.play(cmd_2)
        self._assert_state(i._state, current_command=cmd_2, running=True, last_played_url=self.DEFAULT_URL,
                           played_count=1, description="Spielt a-track")
        self.assertEqual(res, i._state.view())

        self.PLAYER_DLNA.play.assert_has_calls([call(self.DEFAULT_URL)])
        self.SCHEDULER.stop_job.assert_has_calls([call(self.DEFAULT_PLAYER_SCHEDULER_NAME)])
        self.SCHEDULER.start_job.assert_called_once()
        mediaserver_search_mock.assert_not_called()

    @patch("controller.test_integrator.FakeServer.search")
    def test_play_item_not_found_after_item(self, mediaserver_search_mock):
        i = self._testee()

        # prepare mediaserver_mock
        mediaserver_search_mock.return_value = self.DEFAULT_RESPONSE
        cmd_1 = PlayCommand(title='must go')
        self._initial_play_item(i, cmd_1)

        # prepare mocks for item not found
        self.SCHEDULER.reset_mock()
        self.PLAYER_DLNA.play.reset_mock()
        mediaserver_search_mock.reset_mock()
        mediaserver_search_mock.return_value = MySearchResponse([])

        cmd_2 = PlayCommand(url=None, artist=None, title='must go', loop=False)
        res = i.play(cmd_2)
        self._assert_state(i._state, running=False, stop_reason="nothing found in media server")
        self.assertEqual(res, i._state.view())

        self.PLAYER_DLNA.play.assert_not_called()
        self.SCHEDULER.stop_job.assert_called()
        self.SCHEDULER.start_job.assert_called()
        mediaserver_search_mock.assert_called_with(title='must go')

    @patch("controller.test_integrator.FakeServer.search")
    def test_play_url_noloop_after_item_loop(self, mediaserver_search_mock):
        i = self._testee()

        # prepare mediaserver_mock
        mediaserver_search_mock.return_value = self.DEFAULT_RESPONSE

        cmd_1 = PlayCommand(title='must go', loop=True)
        self._initial_play_item(i, cmd_1)

        self.SCHEDULER.reset_mock()
        mediaserver_search_mock.reset_mock()

        cmd_2 = PlayCommand(url=self.DEFAULT_URL)
        res = i.play(cmd_2)
        self._assert_state(i._state, current_command=cmd_2, last_played_url=self.DEFAULT_URL, running=True, played_count=1,
                           description="Spielt a-track")
        self.assertEqual(res, i._state.view())

        self.PLAYER_DLNA.play.assert_called_with(self.DEFAULT_URL)
        self.SCHEDULER.stop_job.assert_called()
        self.SCHEDULER.start_job.assert_called()
        mediaserver_search_mock.assert_not_called()

    def test_play_url_loop_error(self):
        i = self._testee()

        cmd_1 = PlayCommand(title='must go', loop=True)
        self._initial_play_url(i, cmd_1)

        # first loop, error
        self.SCHEDULER.stop_job.reset_mock()
        self.PLAYER_DLNA.get_state.side_effect = OSError("test-error")

        with self.assertRaises(OSError):
            i._loop_process()
        self.PLAYER_DLNA.get_state.assert_has_calls([call()])
        self.SCHEDULER.stop_job.assert_called_with(self.DEFAULT_PLAYER_SCHEDULER_NAME)
        self._assert_state(i._state, last_played_url='a-track', running=False, description='Aus',
                           stop_reason="exception in looping: test-error")

    @patch("controller.test_integrator.FakeServer.search")
    def test_play_loop_scenario_1(self, mediaserver_search_mock):
        """Scenario description:
        1) command: play songs from one artist in a loop
        2) loop1: initial item playing, next item already set! check not set again
        3) loop2: next item is playing, check next-next item is beeing set
        """
        i = self._testee()

        # prepare mock
        item_1 = self.DEFAULT_ITEM
        item_2 = MyItem('must go forward', 'foo', 'bar')
        item_3 = MyItem('Fred must gobble things', 'fuu', 'baz')
        mediaserver_search_mock.return_value = MySearchResponse([item_1, item_2, item_3])

        cmd = PlayCommand(title='must go', loop=True)
        self._initial_play_item(i, cmd, next_item=item_2)
        self.SCHEDULER.reset_mock()

        # loop1
        self.PLAYER_DLNA.reset_mock()
        self.PLAYER_DLNA.get_state.return_value = PlayerState(TRANSPORT_STATE.PLAYING, item_1.url, item_2.url, 0)
        i._loop_process()
        self.PLAYER_DLNA.set_next.assert_not_called()
        self.PLAYER_DLNA.reset_mock()
        self._assert_state(i._state, current_command=cmd, last_played_url=item_1.url, played_count=1,
                           last_played_artist=item_1.actor, last_played_title=item_1.title,
                           next_play_url=item_2.url, next_play_item=item_2,
                           running=True, looping=True, description="Spielt Lieder mit 'must go'")

        # loop2
        self.PLAYER_DLNA.reset_mock()
        self.PLAYER_DLNA.get_state.return_value = PlayerState(TRANSPORT_STATE.PLAYING, item_2.url, None, 0)
        i._loop_process()
        self.PLAYER_DLNA.set_next.assert_called_with(item_3.url, item=item_3)
        self.PLAYER_DLNA.reset_mock()
        self._assert_state(i._state, current_command=cmd, last_played_url=item_2.url, played_count=2,
                           last_played_artist=item_2.actor, last_played_title=item_2.title,
                           next_play_url=item_3.url, next_play_item=item_3,
                           running=True, looping=True, description="Spielt Lieder mit 'must go'")

    @patch("controller.test_integrator.FakeServer.search")
    def test_play_loop_scenario_2(self, mediaserver_search_mock):
        """Scenario where some weired stuff happens:
        1) command: play songs from one artist in a loop
        2) loop1: renderer in TRANSITIONING, check nothing done
        2) loop2: renderer in STOPPED, check next is played immediately
        3) loop3: renderer plays random track, check playback cancelled
        """
        i = self._testee()

        # prepare mock
        item_1 = self.DEFAULT_ITEM
        item_2 = MyItem('must go forward', 'foo', 'bar')
        item_3 = MyItem('Fred must gobble things', 'fuu', 'baz')
        mediaserver_search_mock.return_value = MySearchResponse([item_1, item_2, item_3])

        cmd = PlayCommand(title='must go', loop=True)
        self._initial_play_item(i, cmd, next_item=item_2)
        self.SCHEDULER.reset_mock()

        # loop1
        self.PLAYER_DLNA.reset_mock()
        self.PLAYER_DLNA.get_state.return_value = PlayerState(TRANSPORT_STATE.TRANSITIONING, None, None, 0)
        i._loop_process()
        self.PLAYER_DLNA.set_next.assert_not_called()
        self.PLAYER_DLNA.play.assert_not_called()
        self.PLAYER_DLNA.reset_mock()
        self._assert_state(i._state, current_command=cmd, last_played_url=item_1.url, played_count=1,
                           last_played_artist=item_1.actor, last_played_title=item_1.title,
                           running=True, looping=True, description="Spielt Lieder mit 'must go'",
                           next_play_url=item_2.url, next_play_item=item_2)

        # loop2
        self.PLAYER_DLNA.reset_mock()
        self.PLAYER_DLNA.get_state.return_value = PlayerState(TRANSPORT_STATE.STOPPED, item_1.url, None, 0)
        i._loop_process()
        self.PLAYER_DLNA.play.assert_called_with(item_3.url, item=item_3)
        self.PLAYER_DLNA.set_next.assert_called_with(item_1.url, item=item_1)
        self.PLAYER_DLNA.reset_mock()
        self._assert_state(i._state, current_command=cmd, last_played_url=item_3.url, played_count=2,
                           last_played_artist=item_3.actor, last_played_title=item_3.title,
                           running=True, looping=True, description="Spielt Lieder mit 'must go'",
                           next_play_url=item_1.url, next_play_item=item_1)

        # loop3
        self.PLAYER_DLNA.reset_mock()
        self.PLAYER_DLNA.get_state.return_value = PlayerState(TRANSPORT_STATE.PLAYING, "random-other", None, 0)
        i._loop_process()
        self.PLAYER_DLNA.set_next.assert_not_called()
        self.PLAYER_DLNA.play.assert_not_called()
        self.PLAYER_DLNA.reset_mock()
        self._assert_state(i._state, current_command=None, last_played_url=item_3.url, played_count=0,
                           last_played_artist=item_3.actor, last_played_title=item_3.title,
                           running=False, looping=False, description="Aus", stop_reason='interrupted')
