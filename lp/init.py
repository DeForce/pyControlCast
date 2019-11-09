import asyncio
import logging
import random
import threading

import pyautogui
from pydub import AudioSegment
from pydub.playback import play

import time

from lp import launchpad
from lp.obs_websocket import OBS

KEY_UP = 0
KEY_DOWN = 127


# ffmpeg: -loglevel panic -hide_banner -nostats
# TODO: OBS Plugin
class Launchpad(object):
    def __init__(self, config):
        self.reading_thread = None

        self.lp = launchpad.Launchpad()
        self.lp.open()

        self.obs = OBS(config)

        self.config = config
        self.buttons = {}

        self.actions = {
            'keyboard': self.keyboard_press,
            'sound': self.play_sound,
            'obs': self.obs_websocket
        }

        if self.lp.id_in:
            self.lp.reset()
        else:
            Exception('Unable to connect to MIDI controller')

        self.bind_buttons()

    @staticmethod
    def keyboard_press(keys):
        threading.Thread(target=pyautogui.hotkey, args=keys, kwargs={'interval': 0.05}).start()

    @staticmethod
    def play_sound(path=None, volume=0):
        song = AudioSegment.from_mp3(path)
        threading.Thread(target=play, args=[song + volume]).start()

    def obs_websocket(self, request, **kwargs):
        threading.Thread(target=getattr(self.obs, request), kwargs=kwargs).start()

    @staticmethod
    def get_key_info(data):
        logging.debug(data)
        y = int(data[1] / 16) + 1
        x = data[1] % 16

        if data[0] == 176:
            y = y - 1

        return {
            'is_pressed': True if data[2] == KEY_DOWN else False,
            'pos': (x, y),  # X, Y,
            'automap': True if data[0] == 176 else False
        }

    def set_key_data(self, data):
        if data['automap']:
            pass
            self.lp.led_ctrl_automap(data['pos'][1] - 8, random.randint(0, 3), random.randint(0, 3))
        else:
            key_number = (16 * data['pos'][0]) + data['pos'][1]
            self.lp.led_ctrl_raw(key_number, random.randint(0, 3), random.randint(0, 3))

    def process_key(self, data):
        if not data['is_pressed']:
            return
        action = self.buttons.get(data['pos'], {}).get('action', {})
        logging.info(f'Processing button {data["pos"]}, action:{action}')

        if action:
            self.process_action(action)

    def process_action(self, action):
        action_keys = list(action.keys())
        for action_key in action_keys:
            if action_key in self.actions:
                self.actions[action_key](**action[action_key])

    def read(self):
        while True:
            data = self.lp.midi.read_raw()
            if data:
                key_data = self.get_key_info(data[0])
                logging.debug(key_data)
                if key_data['is_pressed']:
                    self.process_key(key_data)
            else:
                time.sleep(0.001)

    def stop(self):
        self.lp.reset()

    def configure_button(self, x, y, red, green, action):
        if (x, y) not in self.buttons:
            self.buttons[(x, y)] = {'red': red, 'green': green, 'action': action}
            self.lp.led_ctrl_xy(x, y, red, green)

    def bind_buttons(self):
        for button, config in self.config['buttons'].items():
            x, y = button.split(':')
            red = config['color']['red']
            green = config['color']['green']
            action = config['action']
            self.configure_button(int(x), int(y), int(red), int(green), action)


def init_launchpad(config):
    lp = Launchpad(config)
    lp.read()
