from urllib.request import urlopen, Request

XML_HEADER = '<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n'
NAMESPACE_DC = 'http://purl.org/dc/elements/1.1/'
NAMESPACE_UPNP = 'urn:schemas-upnp-org:metadata-1-0/upnp/'
NAMESPACE_DIDL = 'urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/'


def create_header(type, method):
    soapaction = '"urn:schemas-upnp-org:service:{t}:1#{m}"'.format(t=type, m=method)
    return {"Content-type": 'text/xml; charset="utf-8"',
            "Soapaction": soapaction,
            "Connection": "close",
            "Accept": "text/html, image/gif, image/jpeg, *; q=.2, */*; q=.2",
            "USER-AGENT": "Python/3.7 dlna.py/0.1 UPnP/1.0"
            }


def send_request(url, header, body):
    req = Request(url, body.encode('utf-8'), header)
    return urlopen(req)


def namespace_free_res_element(xml_str):
    ''' Workaround since python 3.6's xml.etree.ElementTree does not allow to print a string without namespace'''
    # first parse the prefix
    res_location_idx = xml_str.find('res')
    # before that there is some kind of <
    prefix_idx = xml_str.find('<', 0, res_location_idx)
    # prefix now is ns0:
    prefix = xml_str[prefix_idx+1:res_location_idx-1]

    # now cut openening and ending tag
    # heavily rely on formatting:
    # remove opening tag
    result = xml_str.replace("<" + prefix + ":res", "<res")
    # remove ending tag
    result = result.replace(prefix + ':res>', 'res>')

    # cut namespace definition
    # in '... xmlns:ns0="urn:schemas-up..." ...' we shall find the ns0 and cut something before and after
    prefix_idx = result.find(prefix)

    # now search things in front of prefix which usually is xmlns:
    namespace_begin_idx = result.rfind(' ', 0, prefix_idx)

    # find cut point the =. Therefore search first quote and following quote
    first_quote_after_prefix_idx = result.find('"', prefix_idx)
    second_quote_after_prefix_idx = result.find('"', first_quote_after_prefix_idx+1)
    # ergo cut everything 'till second_quote_after_prefix (+1 for the ")

    result = result[0:namespace_begin_idx] + result[second_quote_after_prefix_idx+1:]

    return result
