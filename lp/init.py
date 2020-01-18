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
class Launchpad(object):
    def __init__(self, config):
        self.reading_thread = None

        self.lp = launchpad.Launchpad()
        self.lp.open()

        self.obs = None

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
        threading.Thread(target=self.setup_obs, daemon=True).start()

    @staticmethod
    def keyboard_press(keys):
        threading.Thread(target=pyautogui.hotkey, args=keys, kwargs={'interval': 0.05}).start()

    def play_sound(self, path=None, volume=0, delay=0):
        if isinstance(path, str):
            path = [path]
        if isinstance(volume, int):
            volume = [volume]
        threading.Thread(target=self.play_sounds_thread, args=[path, volume, delay]).start()

    @staticmethod
    def play_sounds_thread(paths, volumes, delay):
        if delay:
            time.sleep(delay)
        for path, volume in zip(paths, volumes):
            song = AudioSegment.from_mp3(path)
            play(song + volume)

    def obs_websocket(self, request, **kwargs):
        if self.obs:
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

    def process_action(self, actions):
        for action_key in actions:
            action, config = list(action_key.items())[0]
            if action in self.actions:
                self.actions[action](**config)

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

    def setup_obs(self):
        while True:
            try:
                self.obs = OBS(self.config)
                break
            except:
                logging.info('Unable to connect to OBS, check your settings')
                time.sleep(5)


def init_launchpad(config):
    lp = Launchpad(config)
    threading.Thread(target=lp.read, daemon=True).start()
    return lp
