from dataclasses import dataclass
import logging

from dlna.player import Player
from dlna.renderer import Renderer
from controller.integrator import Integrator
from controller.data.command import PlayCommand, Command
from controller.data.exceptions import RequestCannotBeHandeledException
from controller.data.state import StateView
from controller.wakeup import ensure_online


logger = logging.getLogger(__file__)

@dataclass
class Mapping():
    renderer: Renderer
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

    _renderers_to_integrators: list[Mapping]

    def __init__(self, players: list[Player], media_server, scheduler) -> None:
        self._renderers_to_integrators = []
        for p in players:
            i = Integrator(p, media_server, scheduler)
            self._renderers_to_integrators.append(Mapping(renderer=p.get_renderer(), integrator=i))

    def _renderer_from_target(self, target: str) -> Renderer:
        if target:
            for m in self._renderers_to_integrators:
                if target in m.renderer.get_known_names():
                    return m.renderer
        return None
    
    def _renderer_for_type(self, type: str) -> Renderer:
        if (type):
            for m in self._renderers_to_integrators:
                if m.renderer.can_play_type(type):
                    return m.renderer
        return None
    
    def _find_integrator_from_renderer(self, renderer) -> Integrator:
        for m in self._renderers_to_integrators:
            if m.renderer == renderer:
                
                return m.integrator
            
    def _renderer_available(self, renderer) -> bool:
        if not renderer:
            return False
        if not ensure_online(renderer):
            logger.debug(f"Renderer {renderer.get_name()} not online")
            return False
        return True

    def _decide_integrator(self, command: Command) -> Integrator:

        # renderer from command's target
        if hasattr(command, 'target'):
            renderer = self._renderer_from_target(command.target)
            if renderer:
                logger.debug(f"Found renderer {renderer.get_name()} from target")
                if (self._renderer_available(renderer)):
                    return self._find_integrator_from_renderer(renderer)
                else:
                    msg = f"The requested renderer {command.target} is not available"
                    logger.error(msg)
                    raise RequestCannotBeHandeledException(msg) 
           
        # renderer from command's type
        if hasattr(command, 'type') and command.type:
            renderer = self._renderer_for_type(command.type)
            if renderer:
                logger.debug(f"Found renderer {renderer.get_name()} by type {command.type}")
                if (self._renderer_available(renderer)):
                    return self._find_integrator_from_renderer(renderer)

        # default renderer, check type if available
        renderer = self._renderers_to_integrators[0].renderer
        if hasattr(command, 'type') and command.type:
            if not renderer.can_play_type(command.type):
                msg = f"No renderer for type {command.type} available, default renderer cannot play this type"
                logger.error(msg)
                raise RequestCannotBeHandeledException(msg)
        logger.debug(f"Using default renderer {renderer.get_name()}")
        if (self._renderer_available(renderer)):
            return self._renderers_to_integrators[0].integrator
        msg = "No renderer available, default renderer unavailable"
        logger.error(msg)
        raise RequestCannotBeHandeledException(msg)

    def play(self, command: PlayCommand):
        i = self._decide_integrator(command)
        return i.play(url=command.url, title=command.title, artist=command.artist, loop=command.loop)

    def pause(self, command: Command):
        i = self._decide_integrator(command)
        return i.pause()

    def stop(self, command: Command):
        i = self._decide_integrator(command)
        return i.stop()

    def state(self, command: Command = None):
        res = []
        # todo we probably need a way to get the state of a particular player?!?

        # integrated state over all players
        for m in self._renderers_to_integrators:
            s = StatePerPlayer(m.renderer.get_name(), m.integrator.get_state())
            res.append(s)

        return res
