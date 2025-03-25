from enum import Enum

CAPABILITIES = Enum('Capabilities', ['audio', 'video', 'image'])


class Renderer():
    '''Holder for meta-information about a device capable of playing DLNA/UPNP'''

    def __init__(self, name: str, aliases: list[str], url: str, mac: str, capabilities: list[str], send_metadata: bool):
        self._name: str = name
        self._aliases: list[str] = aliases
        self._url: str = url
        self._mac: str = mac
        self._capabilities: list[str] = capabilities
        self._send_metadata: bool = send_metadata

    def get_name(self) -> str:
        return self._name

    def get_mac(self) -> str:
        return self._mac

    def include_metadata(self) -> bool:
        return self._send_metadata

    def get_url(self) -> str:
        return self._url

    def get_known_names(self) -> list[str]:
        res = []
        res.append(self._name)
        if self._aliases and len(self._aliases):
            for a in self._aliases:
                res.append(a)
        return res

    def can_play_type(self, type: str) -> bool:
        if self._capabilities and type in self._capabilities:
            return True
        return False
