import logging
from typing import Dict

from controller.scheduler import Scheduler
from controller.player_wrapper import PlayerWrapper, discover, configure

logger = logging.getLogger(__file__)


class PlayerManager():
    ''' PlayerManager mangages players/renderers
    * it auto-detects players and adds them to the list of known players.
    * it auto-detects capabilities for players.
    * it is capable to choose a a players per given capability.
    * it decides default player.
    * it handles online/offline states for players.
    '''

    DEFAULT_DISCOVERY_INTERVAL = 60*5

    _players: list[PlayerWrapper] = []
    _scheduler: Scheduler = None

    def __init__(self, configs: dict, scheduler: Scheduler):
        self._players = [configure(config) for config in configs]
        self._scheduler = scheduler
        self._scheduler.start_job('PLAYER_DISCOVERY', self._run_discovery, self.DEFAULT_DISCOVERY_INTERVAL)

    def get_players(self) -> list[PlayerWrapper]:
        return self._players
    
    def get_player_views(self) -> list:
        return [p.to_view() for p in self._players]

    def _run_discovery(self):
        discovered_players = discover()

        # for each newly discovered device we need to find an already existing one
        new_playerwrappers: list[PlayerWrapper] = []  # list of newly (previously unknown) devices
        updated_playerwrappers: Dict[PlayerWrapper, PlayerWrapper] = {}  # old => discovered
        # compare to already known based on the url (which is mandatory in any case)
        for dpw in discovered_players:
            existing = next(filter(lambda p: p.get_url() == dpw.get_url(), self._players), None)
            if existing is None:
                logger.debug(f"discovered an new device with url {dpw.get_url()}")
                new_playerwrappers.append(dpw)
                continue
            logger.debug(f"discovered an already known device with url {dpw.get_url()}")
            updated_playerwrappers[existing] = dpw

        # process already known devices:
        for old, new_pw in updated_playerwrappers.items():
            logger.debug(f"updateing player {old.get_url()}")
            old._detected_meta = new_pw._detected_meta  # update metadata
            old._last_seen = new_pw._last_seen  # update last seen
            if old._dlna_player is None:
                old._dlna_player = new_pw._dlna_player

        # process new devices
        for new_pw in new_playerwrappers:
            # TODO somehow create a new mapping in the player_dispatcher?!?
            logger.debug(f"adding player {new_pw.get_url()}")
            self._players.append(new_pw)
