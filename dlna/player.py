import uuid
import logging
import xml.etree.ElementTree as ET
from enum import Enum
from dataclasses import dataclass
from time import sleep

from dlna.renderer import Renderer
from dlna.items import Item
from dlna import dlna_helper

TRANSPORT_STATE = Enum('TransportState', ['STOPPED', 'PLAYING', 'TRANSITIONING', 'PAUSED_PLAYBACK',
                                          'RECORDING', 'PAUSED_RECORDING', 'NO_MEDIA_PRESENT'])

logger = logging.getLogger(__file__)


@dataclass
class State():
    transport_state: TRANSPORT_STATE
    current_url: str
    progress_count: int


class Player():

    # http://www.upnp.org/specs/av/UPnP-av-AVTransport-v3-Service-20101231.pdf
    # http://upnp.org/specs/av/UPnP-av-ContentDirectory-v4-Service.pdf
    # http://upnp.org/specs/av/UPnP-av-AVDataStructureTemplate-v1.pdf
    # http://www.upnp.org/specs/av/UPnP-av-ContentDirectory-v1-Service.pdf
    # https://developer.sony.com/develop/audio-control-api/get-started/play-dlna-file#tutorial-step-3
    META_DATA = '''
    <DIDL-Lite xmlns="urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/"
    xmlns:upnp="urn:schemas-upnp-org:metadata-1-0/upnp/"
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:dlna="urn:schemas-dlna-org:metadata-1-0/"
    xmlns:sec="http://www.sec.co.kr/"
    xmlns:pv="http://www.pv.com/pvns/">
        <item id="{id}" parentID="{parentid}" restricted="1">
            <dc:title>{title}</dc:title>

            <dc:creator>{artist}</dc:creator>
            <upnp:artist>{artist}</upnp:artist>
            <upnp:actor>{artist}</upnp:actor>
            <upnp:author>{artist}</upnp:author>

            <upnp:class>{class_or_type}</upnp:class>
            {res}
        </item>
    </DIDL-Lite>
    '''

    # play should get the variable: speed
    PLAY_BODY = dlna_helper.XML_HEADER + '<s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><u:Play xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID><Speed>1</Speed></u:Play></s:Body></s:Envelope>'
    PAUSE_BODY = dlna_helper.XML_HEADER + '<s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><u:Pause xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID></u:Pause></s:Body></s:Envelope>'
    STOP_BODY = dlna_helper.XML_HEADER + '<s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><u:Stop xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID></u:Stop></s:Body></s:Envelope>'
    POS_INFO_BODY = dlna_helper.XML_HEADER + '<s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><u:GetPositionInfo xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID></u:GetPositionInfo></s:Body></s:Envelope>'
    TRANS_INFO_BODY = dlna_helper.XML_HEADER + '<s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><u:GetTransportInfo xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID></u:GetTransportInfo></s:Body></s:Envelope>'
    MEDIA_INFO_BODY = dlna_helper.XML_HEADER + '<s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><u:GetMediaInfo xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID></u:GetMediaInfo></s:Body></s:Envelope>'
    # should get the variabl: url and metadata
    PREPARE_BODY = dlna_helper.XML_HEADER + '<s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><u:SetAVTransportURI xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID><CurrentURI>{url}</CurrentURI><CurrentURIMetaData>{metadata}</CurrentURIMetaData></u:SetAVTransportURI></s:Body></s:Envelope>'
    PREPARE_BODY_2 = dlna_helper.XML_HEADER + '<s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><u:SetAVTransportURI xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID><CurrentURI>{url}</CurrentURI></u:SetAVTransportURI></s:Body></s:Envelope>'

    # should get the variabl: url and metadata
    PREPARE_NEXT_BODY = '<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n<s:Envelope s:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/" xmlns:s="http://schemas.xmlsoap.org/soap/envelope/"><s:Body><u:SetAVTransportURI xmlns:u="urn:schemas-upnp-org:service:AVTransport:1"><InstanceID>0</InstanceID><NextURI>{url}</NextURI><NextURIMetaData>{metadata}</NextURIMetaData></u:SetAVTransportURI></s:Body></s:Envelope>'

    def __init__(self, renderer: Renderer):
        self._renderer: Renderer = renderer

    # external methods

    def get_renderer(self):
        return self._renderer

    def get_name(self):
        return self._renderer.get_name()

    def stop(self):
        return self._send_request('Stop', self.STOP_BODY)

    def pause(self):
        return self._send_request('Pause', self.PAUSE_BODY)

    def play(self, url_to_play, **kwargs):
        # prepare metadata
        encoded_meta = ''
        if (self._renderer.include_metadata()):
            if ('item' in kwargs):
                # uses mediaserver's item
                item: Item = kwargs['item']
                meta = self.META_DATA.format(id=uuid.uuid4(), parentid=uuid.uuid4(), title=item.get_title(),
                                             artist=item.get_actor(), class_or_type=item.get_class(),
                                             res=item.get_res_as_string())
                encoded_meta = self._escape(self._clean(meta))
                if logger.isEnabledFor(logging.DEBUG):
                    metadata_xml = ET.fromstring(dlna_helper.XML_HEADER + meta)
                    logger.debug(f"metadata as xml {ET.tostring(metadata_xml, encoding='utf-8', method='xml')}")

            elif ('metadata_raw' in kwargs):
                encoded_meta = kwargs['metadata_raw']

        prepare_body = self.PREPARE_BODY.format(url=url_to_play, metadata=encoded_meta)
        self._send_request('SetAVTransportURI', prepare_body)

        # see spec 2.4.9.2, we must wait until one of these states
        self._wait_for_transport_state([TRANSPORT_STATE.STOPPED, TRANSPORT_STATE.PLAYING, TRANSPORT_STATE.PAUSED_PLAYBACK])

        # play SOAP message
        return self._send_request('Play', self.PLAY_BODY)

    def get_state(self) -> State:
        position_info = self._position_info()
        transport_info = self._transport_info()

        transport_state = transport_info.get('CurrentTransportState', None)
        track_URI = position_info.get('TrackURI', None)
        rel_count = int(position_info.get('RelCount', None))

        logger.debug(f"current transport_state: {transport_state} and track: {track_URI}")

        return State(TRANSPORT_STATE[transport_state], track_URI, rel_count)

    # internal methods

    def _escape(self, str):
        str = str.replace("&", "&amp;")
        str = str.replace("<", "&lt;")
        str = str.replace(">", "&gt;")
        return str

    def _clean(self, str):
        result = str.strip()
        result = " ".join(result.split())
        return result

    def _position_info(self):
        response = self._send_request('GetPositionInfo', self.POS_INFO_BODY)
        response_as_text = response.read().decode('utf-8')
        logger.debug(f"position info response: {response_as_text}")
        xml_content = ET.fromstring(response_as_text)

        getPositionInfoResponse = xml_content.find(".//{urn:schemas-upnp-org:service:AVTransport:1}GetPositionInfoResponse")
        result = {}

        for child in getPositionInfoResponse:
            result[child.tag] = child.text

        return result

    def _transport_info(self):
        response = self._send_request('GetTransportInfo', self.TRANS_INFO_BODY)
        response_as_text = response.read().decode('utf-8')
        logger.debug(f"transport info response: {response_as_text}")
        xml_content = ET.fromstring(response_as_text)

        getPositionInfoResponse = xml_content.find(".//{urn:schemas-upnp-org:service:AVTransport:1}GetTransportInfoResponse")
        result = {}

        for child in getPositionInfoResponse:
            result[child.tag] = child.text

        return result

    def _wait_for_transport_state(self, expected_transport_states: list[TRANSPORT_STATE]):
        logger.debug(f"waiting for state {','.join(map(str, expected_transport_states))}")
        for i in range(20):
            transport_info = self._transport_info()
            current_transport_state = transport_info.get('CurrentTransportState', None)
            if TRANSPORT_STATE[current_transport_state] in expected_transport_states:
                logger.debug(f"state {current_transport_state} arrived.")
                return True
            sleep(0.1)  # wait for 100ms until another try

        return False

    def _send_request(self, header_keyword, body):
        device_url = self._renderer.get_url()
        headers = dlna_helper.create_header('AVTransport', header_keyword)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Sending player request: ")
            logger.debug(f"body: {body}")
            logger.debug(f"headers: {headers}")
        return dlna_helper.send_request(device_url, headers, body)
