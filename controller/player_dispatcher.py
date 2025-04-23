from dataclasses import dataclass
import logging

from controller.player_wrapper import PlayerWrapper
from controller.player_manager import PlayerManager
from controller.scheduler import Scheduler
from dlna.mediaserver import MediaServer
from controller.integrator import Integrator
from controller.data.command import PlayCommand, Command
from controller.data.exceptions import RequestCannotBeHandeledException
from controller.data.state import StateView
from controller.wakeup import ensure_online


logger = logging.getLogger(__file__)


@dataclass
class Mapping():
    player: PlayerWrapper
    integrator: Integrator


@dataclass
class StatePerPlayer():
    player_name: str
    state: StateView


class PlayerDispatcher:
    '''Player dispatcher dispatches calls to players
    based on:
    * does the command mention the player's name
    * is the player known to be online.
    * is the player capable of handling the format (audio/video)

    as a default the first player is chosen.
    '''

    _players_to_integrators: list[Mapping]
    _player_manager: PlayerManager
    _media_server: MediaServer
    _scheduler: Scheduler

    def __init__(self, player_manager, media_server, scheduler) -> None:
        self._players_to_integrators = []
        self._player_manager = player_manager
        self._media_server = media_server
        self._scheduler = scheduler

    def _player_from_target(self, target: str) -> PlayerWrapper | None:
        if target:
            for p in self._player_manager.get_players():
                if target in p.get_known_names():
                    return p
        return None

    def _get_or_create_integrator(self, player) -> Integrator:
        for m in self._players_to_integrators:
            if m.player == player:
                return m.integrator

        i = Integrator(player, self._media_server, self._scheduler)
        mapping = Mapping(player, i)
        self._players_to_integrators.append(mapping)
        return i

    def _player_available(self, player: PlayerWrapper) -> bool:
        if not player:
            return False
        if not ensure_online(player):
            logger.debug(f"Player {player.get_name()} not online")
            return False
        return True

    def _decide_integrator_by_target(self, command: Command) -> Integrator | None:
        if hasattr(command, 'target'):
            player = self._player_from_target(command.target)
            if player:
                logger.debug(f"Found player {player.get_name()} from target")
                if (self._player_available(player)):
                    return self._get_or_create_integrator(player)
                else:
                    msg = f"The requested player {command.target} is not available"
                    logger.error(msg)
                    raise RequestCannotBeHandeledException(msg)
        return None

    def _decide_integrator(self, command: Command) -> Integrator:
        # FIRST if it's explicitely mentioned: player from command's target
        by_target = self._decide_integrator_by_target(command)
        if (by_target):
            return by_target

        # SECOND, beginning from the first player,
        # check through the list of players if one is available to play
        for p in self._player_manager.get_players():
            if hasattr(command, 'type') and command.type:
                if not p.can_play_type(command.type):
                    logger.debug(f"Cannot play on {p.get_name()} due to type restriction")
                    continue
            if (self._player_available(p)):
                logger.debug(f"Using default player {p.get_name()}")
                return self._get_or_create_integrator(p)
            logger.debug(f"Cannot play on {p.get_name()} due to offline state")

        msg = "No player available to play the media"
        logger.error(msg)
        raise RequestCannotBeHandeledException(msg)

    def play(self, command: PlayCommand):
        i = self._decide_integrator(command)
        return i.play(command)

    def pause(self, command: Command):
        i = self._decide_integrator(command)
        return i.pause()

    def stop(self, command: Command):
        i = self._decide_integrator(command)
        return i.stop()

    def state(self, command: Command = None):

        # single result
        by_target = self._decide_integrator_by_target(command)
        if (by_target):
            for m in self._players_to_integrators:
                if by_target == m.integrator:
                    return [StatePerPlayer(m.player.get_name(), m.integrator.get_state())]

        # state over all players used
        res = []
        for m in self._players_to_integrators:
            s = StatePerPlayer(m.player.get_name(), m.integrator.get_state())
            res.append(s)

        return res
