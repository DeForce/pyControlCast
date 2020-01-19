import logging.handlers

import os
from time import sleep

import dotmap
import yaml

from gui.init import init_gui
from lp.init import init_launchpad
from settings import LOG_FOLDER


LOG_FILE = os.path.join(LOG_FOLDER, 'app.log')
LOG_FORMAT = logging.Formatter("%(asctime)s [%(threadName) s%(name)s] [%(levelname)s]  %(message)s")
LOG_FILES_COUNT = 5

VERSION = '0.0.1'


def setup_logger():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Logging level
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=1000*1024, backupCount=LOG_FILES_COUNT)
    file_handler.setFormatter(LOG_FORMAT)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(LOG_FORMAT)
    root_logger.addHandler(console_handler)
    logging.getLogger('requests').setLevel(logging.ERROR)
    # logging.getLogger('obswebsocket.core').setLevel(logging.ERROR)


def load_config():
    with open('conf/config.yaml') as conf_file:
        return yaml.safe_load(conf_file.read())


if __name__ == '__main__':
    setup_logger()

    gui_enabled = True

    log = logging.getLogger('main')

    config = dotmap.DotMap(load_config())
    lp = init_launchpad(config)
    if gui_enabled:
        gui = init_gui(config)
        lp.stop()
    else:
        try:
            while True:
                sleep(1)
        except (KeyboardInterrupt, SystemExit):
            log.info("Exiting now")
            lp.stop()
