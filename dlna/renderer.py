from enum import Enum

CAPABILITIES = Enum('Capabilities', ['audio', 'video', 'image'])


class Renderer():
    '''Holder for meta-information about a device capable of playing DLNA/UPNP'''

    def __init__(self, name, aliases, url, mac, capabilities, send_metadata):
        self._name = name
        self._aliases = aliases
        self._control_url = url
        self._mac = mac
        self._capabilities = capabilities
        self._send_metadata = send_metadata

    def get_name(self):
        return self._name

    def get_mac(self):
        return self._mac

    def include_metadata(self):
        return self._send_metadata

    def get_url(self):
        return self._control_url

    def get_known_names(self):
        res = []
        res.append(self._name)
        if self._aliases and len(self._aliases):
            for a in self._aliases:
                res.append(a)
        return res

    def can_play_type(self, type: str):
        if self._capabilities and type in self._capabilities:
            return True
        return False
