import xml.etree.ElementTree as ET
import random
import logging

from dlna import dlna_helper
from dlna.items import Item

logger = logging.getLogger(__file__)


class SearchResponse():

    def __init__(self, result_text):
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"constructing search response from content {result_text}")
        self._root_element = ET.fromstring(result_text)
        self._matches = self._root_element.find('.//TotalMatches').text
        self._returned = self._root_element.find('.//NumberReturned').text
        result = self._root_element.find('.//Result').text

        # create valid XML from result. This field containing escaped XML without xml-header.
        result_unescaped = dlna_helper.XML_HEADER + result
        self._result_root = ET.fromstring(result_unescaped)
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"result content as xml {ET.tostring(self._result_root, encoding='utf-8', method='xml')}")

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
