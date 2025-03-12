import logging
from dlna import dlna_helper
from dlna.search_responses import SearchResponse

logger = logging.getLogger(__file__)


class MediaServer():

    QUERY = '''<?xml version="1.0"?>
    <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
     SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
        <SOAP-ENV:Body>
            <m:Search xmlns:m="urn:schemas-upnp-org:service:ContentDirectory:1">
                <ContainerID xmlns:dt="urn:schemas-microsoft-com:datatypes" dt:dt="string">0</ContainerID>
                <SearchCriteria xmlns:dt="urn:schemas-microsoft-com:datatypes" dt:dt="string">{type} and @refID exists false {criteria}</SearchCriteria>
                <Filter xmlns:dt="urn:schemas-microsoft-com:datatypes" dt:dt="string">*</Filter>
                <StartingIndex xmlns:dt="urn:schemas-microsoft-com:datatypes" dt:dt="ui4">0</StartingIndex>
                <RequestedCount xmlns:dt="urn:schemas-microsoft-com:datatypes" dt:dt="ui4">{max_size}</RequestedCount>
                <SortCriteria xmlns:dt="urn:schemas-microsoft-com:datatypes" dt:dt="string">
                 +upnp:artist,+upnp:album,+upnp:originalTrackNumber,+dc:title</SortCriteria>
            </m:Search>
        </SOAP-ENV:Body>
    </SOAP-ENV:Envelope>
    '''
    TITLE_PATTERN = ' and dc:title contains "{q}"'
    ARTIST_PATTERN = ' and upnp:artist contains "{q}"'

    AUDIO = 'upnp:class derivedfrom "object.item.audioItem"'
    VIDEO = 'upnp:class derivedfrom "object.item.videoItem"'
    IMAGE = 'upnp:class derivedfrom "object.item.imageItem"'

    def __init__(self, url):
        self._url = url

    def _type_str_to_type_criteria(self, type_str):
        if 'image' == type_str:
            return self.IMAGE
        elif 'video' == type_str:
            return self.VIDEO
        elif 'audio' == type_str:
            return self.AUDIO
        else:
            raise ValueError(f"cannot work with type {type_str}")

    def _size_to_size_criteria(self, max_size):
        size_int: int = None
        if isinstance(max_size, str):
            # try to parse int - if it works ok - otherwise raise excpetion
            size_int = int(max_size)
        elif isinstance(max_size, int):
            size_int = max_size
        else:
            raise ValueError(f"Cannot work with size: {str(max_size)}")

        # now check whether the value is valid
        if size_int < 1:
            raise ValueError(f"Invalid size {str(size_int)}")
        return str(size_int)

    def search(self, title=None, artist=None, type='audio', max_size=200):

        # size
        size_criteria = self._size_to_size_criteria(max_size)
        # type criteria
        type_criteria = self._type_str_to_type_criteria(type)
        # additional query options
        search_query_criteria = ''
        if (not self._is_blank(title)):
            search_query_criteria += (self.TITLE_PATTERN.format(q=title))
        if (not self._is_blank(artist)):
            search_query_criteria += (self.ARTIST_PATTERN.format(q=artist))
        query = self.QUERY.format(criteria=search_query_criteria, type=type_criteria, max_size=size_criteria)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"query string: {query}")
        response = self._send_request(self._create_header(), query)
        return SearchResponse(response.read().decode("utf-8"))

    def _is_blank(self, str):
        return not (str and str.strip())

    def _send_request(self, header, body):
        return dlna_helper.send_request(self._url, header, body)

    def _create_header(self):
        return dlna_helper.create_header('ContentDirectory', 'Search')
