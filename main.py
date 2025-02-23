import logging
import json

from controller.webserver import WebServer
from controller.appinfo import AppInfo
from controller.scheduler import Scheduler
from controller.player_dispatcher import PlayerDispatcher

from dlna.player import Player
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


def create_players(renderers_config: dict) -> list[Player]:
    res = []
    for r_config in renderers_config:
        renderer = Renderer(r_config.get('name'), r_config.get('aliases'), r_config.get('url'),
                            r_config.get('mac'), r_config.get('capabilities'), r_config.get('send_metadata'))
        res.append(Player(renderer))
    return res


def validate_players(players: list[Player]):
    names = []
    for p in players:
        p_name = p.get_name()
        if p_name in names:
            raise Exception(f"configuration contains two players with name {p_name}")
        names.append(p_name)


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
    scheduler = Scheduler()
    scheduler.start()

    players = create_players(config.get('renderers'))
    validate_players(players)

    media_servers = create_media_servers(config.get('media_servers'))

    dispatcher = PlayerDispatcher(players, media_servers[0], scheduler)  # todo for now only one
    w = WebServer(config, dispatcher, info)
    w.run()


if __name__ == "__main__":
    main()
