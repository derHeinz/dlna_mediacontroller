import logging
import json

from controller.integrator import Integrator
from controller.webserver import WebServer
from controller.appinfo import AppInfo

from dlna.renderer import Renderer
from dlna.mediaserver import MediaServer

logger = logging.getLogger(__file__)


def setup_logging():
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)


def load_config():
    # load configuration from config file
    with open('config.json') as data_file:
        return json.load(data_file)


def create_renderers(renderers_config: dict):
    res = []
    for r_config in renderers_config:
        renderer = Renderer(r_config.get('name'), r_config.get('aliases'), r_config.get('url'),
                            r_config.get('mac'), r_config.get('capabilities'), r_config.get('send_metadata'))
        res.append(renderer)
    return res


def create_media_servers(media_servers_config: dict):
    res = []
    for m_config in media_servers_config:
        server = MediaServer(m_config.get('url'))
        res.append(server)
    return res


def main():
    setup_logging()

    config = load_config()

    info = AppInfo()
    info.register('config', config)  # put full config into info

    logger.info("starting")
    renderers = create_renderers(config.get('renderers'))
    media_servers = create_media_servers(config.get('media_servers'))
    integrator = Integrator(renderers, media_servers[0])  # ONLY the first server!
    w = WebServer(config, integrator, info)
    w.run()


if __name__ == "__main__":
    main()
