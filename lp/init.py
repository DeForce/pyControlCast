import logging
import random
import threading

import pyautogui
from pydub import AudioSegment
from pydub.playback import play

import controller as launchpad
import time

KEY_UP = 0
KEY_DOWN = 127


# ffmpeg: -loglevel panic -hide_banner -nostats
# TODO: OBS Plugin
class Launchpad(object):
    def __init__(self, config):
        self.reading_thread = None

        self.lp = launchpad.Launchpad()
        self.lp.open()

        self.config = config
        self.buttons = {}

        self.actions = {
            'keyboard': self.keyboard_press,
            'sound': self.play_sound
        }

        if self.lp.id_in:
            self.lp.reset()
        else:
            Exception('Unable to connect to MIDI controller')

        self.bind_buttons()

    def keyboard_press(self, keys):
        key_list = keys.split('+')
        thread = threading.Thread(target=pyautogui.hotkey, args=key_list, kwargs={'interval': 0.05})
        thread.start()
        # for key in keys.split(','):
        #     key_list = list(map(str.lower, key.split('+')))

    def play_sound(self, path=None, volume=0):
        song = AudioSegment.from_mp3(path)
        thread = threading.Thread(target=play, args=[song + volume])
        thread.start()

    def get_key_info(self, data):
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
        action_key = list(action.keys())[0]
        if action_key in self.actions:
            self.actions[action_key](**action[action_key])

    def reading(self):
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

    def read_thread(self):
        self.reading_thread = threading.Thread(target=self.reading, daemon=True)
        self.reading_thread.start()

    def bind_buttons(self):
        for button, config in self.config['buttons'].items():
            x, y = button.split(':')
            red = config['color']['red']
            green = config['color']['green']
            action = config['action']
            self.configure_button(int(x), int(y), int(red), int(green), action)


def init_launchpad(config):
    lp = Launchpad(config)
    lp.read_thread()
    return lp
