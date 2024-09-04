import xml.etree.ElementTree as ET
import random

from dlna.dlna_helper import XML_HEADER, NAMESPACE_DIDL, NAMESPACE_DC, NAMESPACE_UPNP, create_header, send_request, namespace_free_res_element


class Item():

    def __init__(self, item_element):
        self._element = item_element

    def get_title(self):
        e = self._element.find('dc:title', {'dc': NAMESPACE_DC})
        if e is None:
            return None
        return e.text

    def get_actor(self):
        e = self._element.find('upnp:actor', {'upnp': NAMESPACE_UPNP})
        if e is None:
            return None
        return e.text

    def get_creator(self):
        e = self._element.find('dc:creator', {'dc': NAMESPACE_DC})
        if e is None:
            return None
        return e.text

    def get_url(self):
        e = self._element.find('d:res', {'d': NAMESPACE_DIDL})
        if e is None:
            return None
        return e.text

    def get_res(self):
        e = self._element.find('d:res', {'d': NAMESPACE_DIDL})
        if e is None:
            return None
        return e

    def get_res_as_string(self):
        res = ET.tostring(self.get_res(), encoding="utf-8", method="xml")
        # we need res to be of type str here
        if type(res) is bytes:
            # print("res is of type bytes, reformatting")
            res = res.decode('utf-8')
        return namespace_free_res_element(res)

    def get_item(self):
        return self._element

    def get_item_as_string(self):
        return ET.tostring(self._element, encoding="utf-8", method="xml")


class SearchResponse():

    def __init__(self, result_text):
        self._root_element = ET.fromstring(result_text)
        self._matches = self._root_element.find('.//TotalMatches').text
        self._returned = self._root_element.find('.//NumberReturned').text
        result = self._root_element.find('.//Result').text

        # create valid XML from result. This field containing escaped XML without header.
        result_unescaped = XML_HEADER + result
        self._result_root = ET.fromstring(result_unescaped)

    def get_matches(self):
        return int(self._matches)

    def get_returned(self):
        return int(self._returned)

    def first_item(self):
        first_item = self._result_root.find('r:item', {'r': 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/'})
        if (first_item is not None):
            return Item(first_item)
        return None

    def random_item(self):
        all_item = self._result_root.findall('r:item', {'r': 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/'})
        if all_item is None or len(all_item) == 0:
            return None
        return Item(random.choice(all_item))


class MediaServer():

    QUERY = '''
    <?xml version="1.0"?>
    <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
        <SOAP-ENV:Body>
            <m:Search xmlns:m="urn:schemas-upnp-org:service:ContentDirectory:1">
                <ContainerID xmlns:dt="urn:schemas-microsoft-com:datatypes" dt:dt="string">0</ContainerID>
                <SearchCriteria xmlns:dt="urn:schemas-microsoft-com:datatypes" dt:dt="string">upnp:class derivedfrom "object.item.audioItem" and @refID exists false {criteria}</SearchCriteria>
                <Filter xmlns:dt="urn:schemas-microsoft-com:datatypes" dt:dt="string">*</Filter>
                <StartingIndex xmlns:dt="urn:schemas-microsoft-com:datatypes" dt:dt="ui4">0</StartingIndex>
                <RequestedCount xmlns:dt="urn:schemas-microsoft-com:datatypes" dt:dt="ui4">200</RequestedCount>
                <SortCriteria xmlns:dt="urn:schemas-microsoft-com:datatypes" dt:dt="string">+upnp:artist,+upnp:album,+upnp:originalTrackNumber,+dc:title</SortCriteria>
            </m:Search>
        </SOAP-ENV:Body>
    </SOAP-ENV:Envelope>
    '''
    TITLE_PATTERN = ' and dc:title contains "{q}"'
    ARTIST_PATTERN = ' and upnp:artist contains "{q}"'

    def __init__(self, url):
        self._url = url

    def search(self, title=None, artist=None):
        search_query_additionals = ''
        if (not self._is_blank(title)):
            search_query_additionals += (self.TITLE_PATTERN.format(q=title))
        if (not self._is_blank(artist)):
            search_query_additionals += (self.ARTIST_PATTERN.format(q=artist))
        query = self.QUERY.format(criteria=search_query_additionals)
        response = self._send_request(self._create_header(), query)
        return SearchResponse(response.read().decode("utf-8"))

    def _is_blank(self, str):
        return not (str and str.strip())

    def _send_request(self, header, body):
        return send_request(self._url, header, body)

    def _create_header(self):
        return create_header('ContentDirectory', 'Search')
