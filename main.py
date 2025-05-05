import logging
import json

from controller.webserver import WebServer
from controller.appinfo import AppInfo
from controller.scheduler import Scheduler
from controller.player_dispatcher import PlayerDispatcher
from controller.player_manager import PlayerManager

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


def create_media_servers(media_servers_config: dict) -> list[MediaServer]:
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
    scheduler = Scheduler()
    scheduler.start()

    manager = PlayerManager(config.get('players'), scheduler)
    info.register('players', manager.get_player_views)
    media_servers = create_media_servers(config.get('media_servers'))

    dispatcher = PlayerDispatcher(manager, media_servers[0], scheduler)  # todo for now only one
    w = WebServer(config, dispatcher, info)
    w.serve()


if __name__ == "__main__":
    main()
