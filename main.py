import logging
import json

from controller.integrator import Integrator
from controller.webserver import WebServer
from controller.appinfo import AppInfo

logger = logging.getLogger(__file__)


def setup_logging():
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(console_handler)


def load_config():
    # load configuration from config file
    with open('config.json') as data_file:
        return json.load(data_file)


def main():
    setup_logging()

    config = load_config()

    info = AppInfo()
    info.register('config', config)  # put full config into info

    logger.info("starting")
    integrator = Integrator(config)
    w = WebServer(config, integrator, info)
    w.run()


if __name__ == "__main__":
    main()
