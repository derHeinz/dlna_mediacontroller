from datetime import datetime
import logging
from dataclasses import dataclass, field, asdict

import upnpclient

from dlna.player import Player

logger = logging.getLogger(__file__)


@dataclass
class PlayerMetadata():
    ''' A meta-object containing information about a player
    '''
    name: str = None
    id: str = None
    aliases: list[str] = field(default_factory=list)
    url: str = None
    mac: str = None
    capabilities: list[str] = field(default_factory=list)
    send_metadata: bool = True


class PlayerWrapper():
    ''' An object wrapping a player including it's discovered metadata,
    in case it's configured also it's configured metadata.
    And direct access to the player object to do sth. with the player like
    playing a music peace.
    '''

    _configured_meta: PlayerMetadata = None
    _detected_meta: PlayerMetadata = None

    _last_seen: datetime = None
    _dlna_player: Player = None

    _upnp_device: upnpclient.Device = None

    def _get_attr_preferred(self, attr):
        if self._configured_meta is not None and getattr(self._configured_meta, attr) is not None:
            return getattr(self._configured_meta, attr)
        elif self._detected_meta is not None and getattr(self._detected_meta, attr) is not None:
            return getattr(self._detected_meta, attr)
        return None

    def is_configured(self):
        return self._configured_meta is not None

    def is_detected(self):
        return self._detected_meta is not None

    def get_known_names(self) -> list[str]:
        res = []
        if self.is_configured():
            if self._configured_meta.name is not None:
                res.append(self._configured_meta.name)
            if self._configured_meta.aliases is not None:
                res.extend(self._configured_meta.aliases)
        if self.is_detected():
            if self._detected_meta.name is not None:
                res.append(self._detected_meta.name)
            if self._detected_meta.aliases is not None:
                res.extend(self._detected_meta.aliases)
        return res

    def can_play_type(self, type: str) -> bool:
        # create types list
        caps = []
        if self.is_configured():
            if self._configured_meta.capabilities is not None:
                caps.extend(self._configured_meta.capabilities)
        if self.is_detected():
            if self._detected_meta.capabilities is not None:
                caps.extend(self._detected_meta.capabilities)

        if type in caps:
            return True
        return False

    def get_name(self) -> str:
        return self._get_attr_preferred('name')

    def get_mac(self) -> str:
        return self._get_attr_preferred('mac')

    def include_metadata(self) -> bool:
        return self._get_attr_preferred('send_metadata')

    def get_url(self) -> str:
        return self._get_attr_preferred('url')

    def get_id(self) -> str:
        return self._get_attr_preferred('id')

    def get_dlna_player(self) -> Player:
        if self._dlna_player is None:
            # ensure device
            if self._upnp_device is None:
                self._upnp_device = upnpclient.Device(self.get_url())
            self._dlna_player = Player(self._upnp_device, self.include_metadata())
        return self._dlna_player
    
    def to_view(self):
        return {
            'configured_meta': asdict(self._configured_meta) if self._configured_meta is not None else None,
            'detected_meta': asdict(self._detected_meta) if self._detected_meta is not None else None,
            'last_seen': self._last_seen.isoformat() if self._last_seen is not None else None
        }


def _discover_players() -> list[upnpclient.Device]:
    all_devices = upnpclient.discover()

    for d in all_devices:
        logger.debug(f"discovered device {d}")

    def has_av_transport_service(d):
        for s in d.services:
            if 'AVTransport' == s.name:
                return True
        return False
    return list(filter(has_av_transport_service, all_devices))


def _detect_capabilities(device: upnpclient.Device):
    detected_capabilities = []
    for a in device.actions:
        if 'GetProtocolInfo' in str(a):
            logger.debug('can query for capabilities')
            res = device.ConnectionManager.GetProtocolInfo()
            if 'audio' in res['Sink']:
                detected_capabilities.append('audio')
            if 'video' in res['Sink']:
                detected_capabilities.append('video')
            if 'image' in res['Sink']:
                detected_capabilities.append('image')
    return detected_capabilities


def _create_configured(config: dict) -> 'PlayerWrapper':
    configured_meta = PlayerMetadata(**config)
    pw = PlayerWrapper()
    pw._last_seen = None
    pw._configured_meta = configured_meta
    pw._detected_meta = None
    pw._upnp_device = None
    pw._dlna_player = None
    return pw


def _create_discovered(device: upnpclient.Device) -> 'PlayerWrapper':
    discovered_meta = PlayerMetadata(name=device.friendly_name, url=device.location, id=device.udn,
                                     capabilities=_detect_capabilities(device))
    pw = PlayerWrapper()
    pw._last_seen = datetime.now()
    pw._configured_meta = None
    pw._detected_meta = discovered_meta
    pw._upnp_device = device
    pw._dlna_player = None
    return pw


def discover() -> list[PlayerWrapper]:
    devices = _discover_players()
    res = []
    for d in devices:
        res.append(_create_discovered(d))
    return res


def configure(config) -> PlayerWrapper:
    return _create_configured(config)
