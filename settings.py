import os
import sys


if hasattr(sys, 'frozen'):
    APP_FOLDER = os.path.dirname(sys.executable)
else:
    APP_FOLDER = os.path.dirname(os.path.abspath('__file__'))

LOG_FOLDER = os.path.join(APP_FOLDER, "logs")
if not os.path.exists(LOG_FOLDER):
    os.makedirs(LOG_FOLDER)
