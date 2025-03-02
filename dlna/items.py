import xml.etree.ElementTree as ET
from dlna import dlna_helper


# TODO str(item) should yield something nice
class Item():

    def __init__(self, item_element: ET.Element):
        self._element: ET.Element = item_element

    def get_title(self):
        e = self._element.find('dc:title', {'dc': dlna_helper.NAMESPACE_DC})
        if e is None:
            return None
        return e.text

    def get_actor(self):
        e = self._element.find('upnp:actor', {'upnp': dlna_helper.NAMESPACE_UPNP})
        if e is None:
            return None
        return e.text
    
    def get_artist(self):
        e = self._element.find('upnp:artist', {'upnp': dlna_helper.NAMESPACE_UPNP})
        if e is None:
            return None
        return e.text
    
    def get_author(self):
        e = self._element.find('upnp:author', {'upnp': dlna_helper.NAMESPACE_UPNP})
        if e is None:
            return None
        return e.text

    def get_creator(self):
        e = self._element.find('dc:creator', {'dc': dlna_helper.NAMESPACE_DC})
        if e is None:
            return None
        return e.text
    
    def get_class(self):
        e = self._element.find('upnp:class', {'upnp': dlna_helper.NAMESPACE_UPNP})
        if e is None:
            return None
        return e.text

    def get_url(self):
        e = self._element.find('d:res', {'d': dlna_helper.NAMESPACE_DIDL})
        if e is None:
            return None
        return e.text

    def get_res(self):
        e = self._element.find('d:res', {'d': dlna_helper.NAMESPACE_DIDL})
        if e is None:
            return None
        return e

    def get_res_as_string(self):
        res = ET.tostring(self.get_res(), encoding="utf-8", method="xml")
        # we need res to be of type str here
        if type(res) is bytes:
            res = res.decode('utf-8')
        return dlna_helper.namespace_free_res_element(res)

    def get_item(self):
        return self._element

    def get_item_as_string(self):
        return ET.tostring(self._element, encoding="utf-8", method="xml")
