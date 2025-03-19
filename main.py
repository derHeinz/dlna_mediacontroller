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
        renderer = Renderer(name=r_config.get('name'), aliases=r_config.get('aliases'), url=r_config.get('url'),
                            device_description_url=r_config.get('device_description_url'), mac=r_config.get('mac'),
                            capabilities=r_config.get('capabilities'), send_metadata=r_config.get('send_metadata'))
        res.append(Player(renderer))
    return res


def validate_players(players: list[Player]):
    if players is None or len(players) < 1:
        raise ValueError(f"Players invalid.")

    if len(players) < 2:
        return

    visited_names = []
    for p in players:
        p_names = p.get_renderer().get_known_names()
        for p_name in p_names:
            if p_name in visited_names:
                raise ValueError(f"configuration contains two players with name {p_name}")
        visited_names.extend(p_names)


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

    players = create_players(config.get('renderers'))
    validate_players(players)

    media_servers = create_media_servers(config.get('media_servers'))

    dispatcher = PlayerDispatcher(players, media_servers[0], scheduler)  # todo for now only one
    w = WebServer(config, dispatcher, info)
    w.run()


if __name__ == "__main__":
    main()
