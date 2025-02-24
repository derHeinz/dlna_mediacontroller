from dlna import dlna_helper
from dlna.search_responses import SearchResponse


class MediaServer():

    QUERY = '''
    <?xml version="1.0"?>
    <SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/"
     SOAP-ENV:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/">
        <SOAP-ENV:Body>
            <m:Search xmlns:m="urn:schemas-upnp-org:service:ContentDirectory:1">
                <ContainerID xmlns:dt="urn:schemas-microsoft-com:datatypes" dt:dt="string">0</ContainerID>
                <SearchCriteria xmlns:dt="urn:schemas-microsoft-com:datatypes" dt:dt="string">
                 upnp:class derivedfrom "object.item.audioItem" and @refID exists false {criteria}</SearchCriteria>
                <Filter xmlns:dt="urn:schemas-microsoft-com:datatypes" dt:dt="string">*</Filter>
                <StartingIndex xmlns:dt="urn:schemas-microsoft-com:datatypes" dt:dt="ui4">0</StartingIndex>
                <RequestedCount xmlns:dt="urn:schemas-microsoft-com:datatypes" dt:dt="ui4">200</RequestedCount>
                <SortCriteria xmlns:dt="urn:schemas-microsoft-com:datatypes" dt:dt="string">
                 +upnp:artist,+upnp:album,+upnp:originalTrackNumber,+dc:title</SortCriteria>
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
        return dlna_helper.send_request(self._url, header, body)

    def _create_header(self):
        return dlna_helper.create_header('ContentDirectory', 'Search')
