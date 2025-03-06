import logging

from time import sleep
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

from wakeonlan import send_magic_packet

logger = logging.getLogger(__file__)

MAX_RETRIES = 10


def _check_online(url) -> bool:
    try:
        urlopen(url, timeout=0.2)
        return True
    except HTTPError:
        logger.debug(f"checked url {url} and got response.")
        # error indicating we received a respones -> there is someone
        return True
    except URLError:
        logger.debug(f"checked url {url} and got no response.")
        return False


def _try_wakeup(mac):
    send_magic_packet(mac)


def ensure_online(renderer) -> bool:
    url = renderer.get_url()

    online = _check_online(url)
    if online:
        return True
    if not renderer.get_mac():
        logger.debug("Cannot wakeup because device has no mac.")
        return False

    # try a wakeup
    mac = renderer.get_mac()
    for i in range(MAX_RETRIES):
        online = _check_online(url)
        if not online:
            _try_wakeup(mac)
            sleep(2)
        else:
            logger.debug(f"device online after {i} wakeup(s).")
            return True

    logger.debug(f"could not wake up device after {MAX_RETRIES}.")
    return False
