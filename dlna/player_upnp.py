import uuid
import logging
from time import sleep

import upnpclient

from dlna.renderer import Renderer
from dlna.items import Item
from dlna.player import State, TRANSPORT_STATE

logger = logging.getLogger(__file__)


# a player using the upnpclient pip package
class Player():

    # http://www.upnp.org/specs/av/UPnP-av-AVTransport-v3-Service-20101231.pdf
    # http://upnp.org/specs/av/UPnP-av-ContentDirectory-v4-Service.pdf
    # http://upnp.org/specs/av/UPnP-av-AVDataStructureTemplate-v1.pdf
    # http://www.upnp.org/specs/av/UPnP-av-ContentDirectory-v1-Service.pdf
    # https://developer.sony.com/develop/audio-control-api/get-started/play-dlna-file#tutorial-step-3
    META_DATA = '''
    <DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"
    xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"
    xmlns:dc="http://purl.org/dc/elements/1.1/">
        <item id="{id}" parentID="{parentid}" restricted="1">
            {inner_info}
        </item>
    </DIDL-Lite>
    '''

    TITLE_DATA = '<dc:title>{value}</dc:title>'
    CREATOR_DATA = '<dc:creator>{value}</dc:creator>'
    AUTHOR_DATA = '<upnp:author>{value}</upnp:author>'
    ACTOR_DATA = '<upnp:actor>{value}</upnp:actor>'
    ARTIST_DATA = '<upnp:artist>{value}</upnp:artist>'
    CLASS_DATA = '<upnp:class>{value}</upnp:class>'

    GERMAN_CHAR_MAP = {ord('ä'): 'ae', ord('Ä'): 'Ae',
                       ord('ö'): 'oe', ord('Ö'): 'Oe',
                       ord('ü'): 'ue', ord('Ü'): 'Ue',
                       ord('ß'): 'ss'}

    def __init__(self, renderer: Renderer):
        self._renderer: Renderer = renderer
        self._device = upnpclient.Device(self._renderer.get_device_description_url())

    # external methods

    def get_renderer(self):
        return self._renderer

    def get_name(self):
        return self._renderer.get_name()

    def stop(self):
        self._device.AVTransport.Stop(InstanceID=0)

    def pause(self):
        self._device.AVTransport.Pause(InstanceID=0)

    def play(self, url_to_play, **kwargs):
        # TODO unclear whether this way to give the kwargs works
        encoded_meta = self._prepare_metadata(kwargs=kwargs)
        self._device.AVTransport.SetAVTransportURI(InstanceID=0, CurrentURI=url_to_play, CurrentURIMetaData=encoded_meta)

        # see spec 2.4.9.2, we must wait until one of these states
        self._wait_for_transport_state([TRANSPORT_STATE.STOPPED, TRANSPORT_STATE.PLAYING, TRANSPORT_STATE.PAUSED_PLAYBACK])

        # play message
        self._device.AVTransport.Play(InstanceID=0, Speed='1')

    def set_next(self, url_to_play, **kwargs):
        encoded_meta = self._prepare_metadata(kwargs=kwargs)
        self._device.AVTransport.SetNextAVTransportURI(InstanceID=0, NextURI=url_to_play, NextURIMetaData=encoded_meta)

    def get_state(self) -> State:

        position_info = self._device.AVTransport.GetPositionInfo(InstanceID=0)
        transport_info = self._device.AVTransport.GetTransportInfo(InstanceID=0)

        transport_state = transport_info.get('CurrentTransportState', None)
        track_URI = position_info.get('TrackURI', None)
        rel_count = int(position_info.get('RelCount', None))

        logger.debug(f"current transport_state: {transport_state} and track: {track_URI}")

        return State(TRANSPORT_STATE[transport_state], track_URI, rel_count)

    # internal methods

    def _prepare_metadata(self, **kwargs):
        if (self._renderer.include_metadata()):
            if ('item' in kwargs):
                # uses mediaserver's item
                i: Item = kwargs['item']

                inner_info = ''
                inner_info += self._add_to_content(self.TITLE_DATA, i.get_title())
                inner_info += self._add_to_content(self.CREATOR_DATA, i.get_creator())
                inner_info += self._add_to_content(self.AUTHOR_DATA, i.get_author())
                inner_info += self._add_to_content(self.ACTOR_DATA, i.get_actor())
                inner_info += self._add_to_content(self.ARTIST_DATA, i.get_artist())
                inner_info += self._add_to_content(self.CLASS_DATA, i.get_class())
                inner_info += i.get_res_as_string()

                meta = self.META_DATA.format(id=uuid.uuid4(), parentid=uuid.uuid4(), inner_info=inner_info)
                return self._escape(self._clean(meta))

            elif ('metadata_raw' in kwargs):
                return kwargs['metadata_raw']

    def _wait_for_transport_state(self, expected_transport_states: list[TRANSPORT_STATE]):
        logger.debug(f"waiting for state {','.join(map(str, expected_transport_states))}")
        for i in range(20):
            transport_info = self._device.AVTransport.GetTransportInfo(InstanceID=0)
            current_transport_state = transport_info.get('CurrentTransportState', None)
            if TRANSPORT_STATE[current_transport_state] in expected_transport_states:
                logger.debug(f"state {current_transport_state} arrived.")
                return True
            sleep(0.1)  # wait for 100ms until another try

        return False

    def _add_to_content(self, xml_tag_data: str, value: str | None):
        if value is not None:
            recoded_value = value.translate(self.GERMAN_CHAR_MAP)
            return xml_tag_data.format(value=recoded_value)
        return ''

    def _escape(self, str: str):
        str = str.replace("&", "&amp;")
        str = str.replace("<", "&lt;")
        str = str.replace(">", "&gt;")
        return str

    def _clean(self, str: str):
        result = str.strip()
        result = " ".join(result.split())
        return result
