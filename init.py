import logging.handlers

import os
import sys
from time import sleep

import yaml

from gui.init import init_gui
from lp.init import init_launchpad

if hasattr(sys, 'frozen'):
    APP_FOLDER = os.path.dirname(sys.executable)
else:
    APP_FOLDER = os.path.dirname(os.path.abspath('__file__'))

LOG_FOLDER = os.path.join(APP_FOLDER, "logs")
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)
LOG_FILE = os.path.join(LOG_FOLDER, 'app.log')
LOG_FORMAT = logging.Formatter("%(asctime)s [%(threadName) s%(name)s] [%(levelname)s]  %(message)s")
LOG_FILES_COUNT = 5

VERSION = '0.0.1'


def setup_logger():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    # Logging level
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=1000*1024, backupCount=LOG_FILES_COUNT)
    file_handler.setFormatter(LOG_FORMAT)
    root_logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(LOG_FORMAT)
    root_logger.addHandler(console_handler)
    logging.getLogger('requests').setLevel(logging.ERROR)


def load_config():
    with open('conf/config.yaml') as conf_file:
        return yaml.safe_load(conf_file.read())


if __name__ == '__main__':
    setup_logger()

    log = logging.getLogger('main')

    config = load_config()
    lp = init_launchpad(config)
    gui = init_gui(config)
    try:
        while True:
            sleep(1)
    except (KeyboardInterrupt, SystemExit):
        log.info("Exiting now")
        lp.stop()
