# A Novation Launchpad control suite for Python.
# Refactored https://github.com/dhilowitz/launchpad_rtmidi.py to support Python3 and PEP8
#
import logging
import time

import rtmidi

log = logging.getLogger()


def search_input_devices(name, quiet=True):
    midi = rtmidi.MidiIn()
    for index,  port in enumerate(midi.get_ports()):
        if not quiet:
            log.info(f'{port}, 1, 0)')
        if port.lower().find(name.lower()) >= 0:
            yield index


def search_output_devices(name, quiet=True):
    midi = rtmidi.MidiOut()
    for index,  port in enumerate(midi.get_ports()):
        if not quiet:
            log.info(f'{port}, 1, 0)')
        if port.lower().find(name.lower()) >= 0:
            yield index


class Midi(object):
    def __init__(self):
        self.dev_in = None
        self.dev_out = None

    def open_output(self, midi_id):
        if self.dev_out is None:
            try:
                self.dev_out = rtmidi.MidiOut()
                self.dev_out.open_port(midi_id)
            except:
                return False
        return True

    def close_output(self):
        if self.dev_out is not None:
            self.dev_out.close_port()
            self.dev_out = None

    def open_input(self, midi_id):
        if self.dev_in is None:
            try:
                self.dev_in = rtmidi.MidiIn()
                self.dev_in.open_port(midi_id)
            except:
                return False
        return True

    def close_input(self):
        if self.dev_in is not None:
            self.dev_in.close_port()
            self.dev_in = None

    def read_raw(self, block=False):
        if block:
            msg = self.dev_in
            while msg == (None, None):
                time.sleep(0.001)
            return msg
        else:
            msg = self.dev_in.get_message()
            if msg != (None, None):
                return msg
            else:
                return None

    def raw_write(self, stat, dat1, dat2):
        """
        Sends a single, short message
        """
        self.dev_out.send_message([stat, dat1, dat2])

    def raw_write_multi(self, messages_list):
        """
        Sends a list of messages. If timestamp is 0, it is ignored.
        Amount of <dat> bytes is arbitrary.
        [ [ [stat, <dat1>, <dat2>, <dat3>], timestamp ],  [...], ... ]
        <datN> fields are optional
        """
        self.dev_out.send_message(messages_list)

    def raw_write_system_exclusive(self, messages_list):
        """
        Sends a single system-exclusive message, given by list <lstMessage>
        The start (0xF0) and end bytes (0xF7) are added automatically.
        [ <dat1>, <dat2>, ..., <datN> ]
        """

        self.dev_out.send_message([0xf0] + messages_list + [0xf7])


class LaunchpadBase(object):

    def __init__(self):
        self.midi = Midi()  # midi interface instance (singleton)
        self.id_out = None  # midi id for output
        self.id_in = None  # midi id for input

        # scroll directions
        self.SCROLL_NONE = 0
        self.SCROLL_LEFT = -1
        self.SCROLL_RIGHT = 1

    def __delete__(self):
        self.close()

    def open(self, number=0, name="Launchpad"):
        """
        Opens one of the attached Launchpad MIDI devices
        """
        self.id_out = list(search_output_devices(name))[number]
        self.id_in = list(search_input_devices(name))[number]

        if self.id_out is None or self.id_in is None:
            raise ModuleNotFoundError(f'Unable to find launchpad by number {number}')

        outputs = (self.midi.open_output(self.id_out),
                   self.midi.open_input(self.id_in))

        return all(outputs)

    def check(self, number=0, name="Launchpad"):
        """
        Checks if a device exists, but does not open it.
        Does not check whether a device is in use or other, strange things...
        """
        self.id_out = list(search_output_devices(name))[number]
        self.id_in = list(search_input_devices(name))[number]

        if self.id_out is None or self.id_in is None:
            return False
        return True

    def close(self):
        self.midi.close_input()
        self.midi.close_output()

    @staticmethod
    def list_all():
        search_input_devices('*')
        search_output_devices('*')

    def button_flush(self):
        """
        Clears the button buffer (The Launchpads remember everything...)
        Because of empty reads (timeouts), there's nothing more we can do here, but
        repeat the polls and wait a little...
        """
        reads = 0
        while reads < 3:
            msg = self.midi.read_raw()
            if msg:
                reads = 0
            else:
                reads += 1
                time.sleep(0.001 * 5)

    def event_raw(self):
        """
        Returns a list of all MIDI events, empty list if nothing happened.
        Useful for debugging or checking new devices.
        """
        msg = self.midi.read_raw()
        if msg:
            return msg
        else:
            return []


class Launchpad(LaunchpadBase):
    """
    For 2-color Launchpads with 8x8 matrix and 2x8 top/right rows
    """

    # LED AND BUTTON NUMBERS IN RAW MODE (DEC):
    #
    # +---+---+---+---+---+---+---+---+
    # |200|201|202|203|204|205|206|207| < AUTOMAP BUTTON CODES;
    # +---+---+---+---+---+---+---+---+   Or use LedCtrlAutomap() for LEDs (alt. args)
    #
    # +---+---+---+---+---+---+---+---+  +---+
    # |  0|...|   |   |   |   |   |  7|  |  8|
    # +---+---+---+---+---+---+---+---+  +---+
    # | 16|...|   |   |   |   |   | 23|  | 24|
    # +---+---+---+---+---+---+---+---+  +---+
    # | 32|...|   |   |   |   |   | 39|  | 40|
    # +---+---+---+---+---+---+---+---+  +---+
    # | 48|...|   |   |   |   |   | 55|  | 56|
    # +---+---+---+---+---+---+---+---+  +---+
    # | 64|...|   |   |   |   |   | 71|  | 72|
    # +---+---+---+---+---+---+---+---+  +---+
    # | 80|...|   |   |   |   |   | 87|  | 88|
    # +---+---+---+---+---+---+---+---+  +---+
    # | 96|...|   |   |   |   |   |103|  |104|
    # +---+---+---+---+---+---+---+---+  +---+
    # |112|...|   |   |   |   |   |119|  |120|
    # +---+---+---+---+---+---+---+---+  +---+
    #
    #
    # LED AND BUTTON NUMBERS IN XY MODE (X/Y)
    #
    #   0   1   2   3   4   5   6   7      8
    # +---+---+---+---+---+---+---+---+
    # |   |1/0|   |   |   |   |   |   |         0
    # +---+---+---+---+---+---+---+---+
    #
    # +---+---+---+---+---+---+---+---+  +---+
    # |0/1|   |   |   |   |   |   |   |  |   |  1
    # +---+---+---+---+---+---+---+---+  +---+
    # |   |   |   |   |   |   |   |   |  |   |  2
    # +---+---+---+---+---+---+---+---+  +---+
    # |   |   |   |   |   |5/3|   |   |  |   |  3
    # +---+---+---+---+---+---+---+---+  +---+
    # |   |   |   |   |   |   |   |   |  |   |  4
    # +---+---+---+---+---+---+---+---+  +---+
    # |   |   |   |   |   |   |   |   |  |   |  5
    # +---+---+---+---+---+---+---+---+  +---+
    # |   |   |   |   |4/6|   |   |   |  |   |  6
    # +---+---+---+---+---+---+---+---+  +---+
    # |   |   |   |   |   |   |   |   |  |   |  7
    # +---+---+---+---+---+---+---+---+  +---+
    # |   |   |   |   |   |   |   |   |  |8/8|  8
    # +---+---+---+---+---+---+---+---+  +---+
    #

    def reset(self):
        """
        Reset the Launchpad
        Turns off all LEDs
        """
        self.midi.raw_write(176, 0, 0)

    @staticmethod
    def led_get_color(red, green):
        """
        Returns a Launchpad compatible "color code byte"
        NOTE: In here, number is 0..7 (left..right)
        """
        led = 0

        red = min(int(red), 3)  # make int and limit to <=3
        red = max(red, 0)  # no negative numbers

        green = min(int(green), 3)  # make int and limit to <=3
        green = max(green, 0)  # no negative numbers

        led |= red
        led |= green << 4

        return led

    def led_ctrl_raw(self, number, red, green):
        """
        Controls a grid LED by its raw <number>; with <green/red> brightness: 0..3
        For LED numbers, see grid description on top of class.
        """

        if number > 199:
            if number < 208:
                # 200-207
                self.led_ctrl_automap(number - 200, red, green)
        else:
            if number < 0 or number > 120:
                return
            # 0-120
            led = self.led_get_color(red, green)
            self.midi.raw_write(144, number, led)

    def led_ctrl_xy(self, x, y, red, green):
        """
        Controls a grid LED by its coordinates <x> and <y>  with <green/red> brightness 0..3
        """

        if x < 0 or x > 8 or y < 0 or y > 8:
            return

        if y == 0:
            self.led_ctrl_automap(x, red, green)

        else:
            self.led_ctrl_raw(((y - 1) << 4) | x, red, green)

    def led_ctrl_raw_rapid(self, all_leds):
        """
        Sends a list of consecutive, special color values to the Launchpad.
        Only requires (less than) half of the commands to update all buttons.
        [ LED1, LED2, LED3, ... LED80 ]
        First, the 8x8 matrix is updated, left to right, top to bottom.
        Afterwards, the algorithm continues with the rightmost buttons and the
        top "automap" buttons.
        LEDn color format: 00gg00rr <- 2 bits green, 2 bits red (0..3)
        Function LedGetColor() will do the coding for you...
        Notice that the amount of LEDs needs to be even.
        If an odd number of values is sent, the next, following LED is turned off!
        REFAC2015: Device specific.
        """

        le = len(all_leds)

        for i in range(0, le, 2):
            self.midi.raw_write(146, all_leds[i], all_leds[i + 1] if i + 1 < le else 0)

    def led_ctrl_automap(self, number, red, green):
        """
        Controls an automap LED <number>; with <green/red> brightness: 0..3
        NOTE: In here, number is 0..7 (left..right)
        """

        if number < 0 or number > 7:
            return

        # TODO: limit red/green
        led = self.led_get_color(red, green)

        self.midi.raw_write(176, 104 + number, led)

    def led_all_on(self, color_code=None):
        """
        all LEDs on
        <colorcode> is here for backwards compatibility with the newer "Mk2" and "Pro"
        classes. If it's "0", all LEDs are turned off. In all other cases turned on,
        like the function name implies :-/
        """
        if color_code == 0:
            self.reset()
        else:
            self.midi.raw_write(176, 0, 127)

    def button_state_raw(self):
        """
        Returns the raw value of the last button change as a list:
        [ <button>, <True/False> ]
        :return:
        """

        a = self.midi.read_raw()
        if a:
            return [a[0][1] if a[0][0] == 144 else a[0][1] + 96, True if a[0][2] > 0 else False]
        else:
            return []

    def button_state_xy(self):
        """
        Returns an x/y value of the last button change as a list:
        [ <x>, <y>, <True/False> ]
        """
        raw = self.midi.read_raw()
        if raw:
            if raw[0][0] == 144:
                x = raw[0][1] & 0x0f
                y = (raw[0][1] & 0xf0) >> 4

                return [x, y + 1, True if raw[0][2] > 0 else False]

            elif raw[0][0] == 176:
                return [raw[0][1] - 104, 0, True if raw[0][2] > 0 else False]
        return []


class LaunchpadPro(LaunchpadBase):
    """
    For 3-color "Pro" Launchpads with 8x8 matrix and 4x8 left/right/top/bottom rows
    """
    # LED AND BUTTON NUMBERS IN RAW MODE (DEC)
    # WITH LAUNCHPAD IN "LIVE MODE" (PRESS SETUP, top-left GREEN).
    #
    # Notice that the fine manual doesn't know that mode.
    # According to what's written there, the numbering used
    # refers to the "PROGRAMMING MODE", which actually does
    # not react to any of those notes (or numbers).
    #
    #        +---+---+---+---+---+---+---+---+
    #        | 91|   |   |   |   |   |   | 98|
    #        +---+---+---+---+---+---+---+---+
    #
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # | 80|  | 81|   |   |   |   |   |   |   |  | 89|
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # | 70|  |   |   |   |   |   |   |   |   |  | 79|
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # | 60|  |   |   |   |   |   |   | 67|   |  | 69|
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # | 50|  |   |   |   |   |   |   |   |   |  | 59|
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # | 40|  |   |   |   |   |   |   |   |   |  | 49|
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # | 30|  |   |   |   |   |   |   |   |   |  | 39|
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # | 20|  |   |   | 23|   |   |   |   |   |  | 29|
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # | 10|  |   |   |   |   |   |   |   |   |  | 19|
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    #
    #        +---+---+---+---+---+---+---+---+
    #        |  1|  2|   |   |   |   |   |  8|
    #        +---+---+---+---+---+---+---+---+
    #
    #
    # LED AND BUTTON NUMBERS IN XY CLASSIC MODE (X/Y)
    #
    #   9      0   1   2   3   4   5   6   7      8
    #        +---+---+---+---+---+---+---+---+
    #        |0/0|   |2/0|   |   |   |   |   |         0
    #        +---+---+---+---+---+---+---+---+
    #
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |0/1|   |   |   |   |   |   |   |  |   |  1
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |9/2|  |   |   |   |   |   |   |   |   |  |   |  2
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |   |   |   |   |   |5/3|   |   |  |   |  3
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |   |   |   |   |   |   |   |   |  |   |  4
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |   |   |   |   |   |   |   |   |  |   |  5
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |   |   |   |   |4/6|   |   |   |  |   |  6
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |   |   |   |   |   |   |   |   |  |   |  7
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |9/8|  |   |   |   |   |   |   |   |   |  |8/8|  8
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    #
    #        +---+---+---+---+---+---+---+---+
    #        |   |1/9|   |   |   |   |   |   |         9
    #        +---+---+---+---+---+---+---+---+
    #
    #
    # LED AND BUTTON NUMBERS IN XY PRO MODE (X/Y)
    #
    #   0      1   2   3   4   5   6   7   8      9
    #        +---+---+---+---+---+---+---+---+
    #        |1/0|   |3/0|   |   |   |   |   |         0
    #        +---+---+---+---+---+---+---+---+
    #
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |1/1|   |   |   |   |   |   |   |  |   |  1
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |0/2|  |   |   |   |   |   |   |   |   |  |   |  2
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |   |   |   |   |   |6/3|   |   |  |   |  3
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |   |   |   |   |   |   |   |   |  |   |  4
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |   |   |   |   |   |   |   |   |  |   |  5
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |   |   |   |   |5/6|   |   |   |  |   |  6
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |   |  |   |   |   |   |   |   |   |   |  |   |  7
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    # |0/8|  |   |   |   |   |   |   |   |   |  |9/8|  8
    # +---+  +---+---+---+---+---+---+---+---+  +---+
    #
    #        +---+---+---+---+---+---+---+---+
    #        |   |2/9|   |   |   |   |   |   |         9
    #        +---+---+---+---+---+---+---+---+
    #

    COLORS = {'black': 0, 'off': 0, 'white': 3, 'red': 5, 'green': 17}

    def open(self, number=0, name="Pro"):
        """
        Opens one of the attached Launchpad MIDI devices.
        Uses search string "Pro", by default.
        """

        retval = super(LaunchpadPro, self).open(number=number, name=name)
        if retval:
            # avoid sending this to an Mk2
            if name.lower() == "pro":
                self.led_set_mode(0)

        return retval

    def check(self, number=0, name="Pro"):
        """
        Checks if a device exists, but does not open it.
        # -- Does not check whether a device is in use or other, strange things...
        # -- Uses search string "Pro", by default.
        """
        return super(LaunchpadPro, self).check(number=number, name=name)

    def led_set_layout(self, mode):
        """
        Sets the button layout (and codes) to the set, specified by <mode>.
        Valid options:
         00 - Session, 01 - Drum Rack, 02 - Chromatic Note, 03 - User (Drum)
         04 - Audio, 05 -Fader, 06 - Record Arm, 07 - Track Select, 08 - Mute
         09 - Solo, 0A - Volume
        Until now, we'll need the "Session" (0x00) settings.
        """

        if mode < 0 or mode > 0x0d:
            return

        self.midi.raw_write_system_exclusive([0, 32, 41, 2, 16, 34, mode])
        time.sleep(0.001 * 10)

    def led_set_mode(self, mode):
        """
        Selects the Pro's mode.
        <mode> -> 0 -> "Ableton Live mode"  (what we need)
                  1 -> "Standalone mode"    (power up default)
        """

        if mode < 0 or mode > 1:
            return

        self.midi.raw_write_system_exclusive([0, 32, 41, 2, 16, 33, mode])
        time.sleep(0.001 * 10)

    def led_set_button_layout_session(self):
        """
        Sets the button layout to "Session" mode.
        """
        self.led_set_layout(0)

    def led_get_color_by_name(self, name):
        """
        Returns an RGB colorcode by trying to find a color of a name given by string <name>.
        If nothing was found, Code 'black' (off) is returned.
        """

        if name in LaunchpadPro.COLORS:
            return LaunchpadPro.COLORS[name]
        else:
            return LaunchpadPro.COLORS['black']

    def led_ctrl_raw(self, number, red, green, blue=None):
        """
        Controls a grid LED by its position <number> and a color, specified by
        <red>, <green> and <blue> intensities, with can each be an integer between 0..63.
        If <blue> is omitted, this methos runs in "Classic" compatibility mode and the
        intensities, which were within 0..3 in that mode, are multiplied by 21 (0..63)
        to emulate the old brightness feeling :)
        Notice that each message requires 10 bytes to be sent. For a faster, but
        unfortunately "not-RGB" method, see "LedCtrlRawByCode()"
        """

        if number < 0 or number > 99:
            return

        if blue is None:
            blue = 0
            red *= 21
            green *= 21

        limit = lambda n, mini, maxi: max(min(maxi, n), mini)

        red = limit(red, 0, 63)
        green = limit(green, 0, 63)
        blue = limit(blue, 0, 63)

        self.midi.raw_write_system_exclusive([0, 32, 41, 2, 16, 11, number, red, green, blue])

    def led_ctrl_raw_by_code(self, number, color_code=None):
        """
        Controls a grid LED by its position <number> and a color code <colorcode>
        from the Launchpad's color palette.
        If <colorcode> is omitted, 'white' is used.
        This method should be ~3 times faster that the RGB version "LedCtrlRaw()", which
        uses 10 byte, system-exclusive MIDI messages.
        """

        if number < 0 or number > 99:
            return

        # TODO: limit/check colorcode
        if color_code is None:
            color_code = LaunchpadPro.COLORS['white']

        self.midi.raw_write(144, number, color_code)

    def led_ctrl_xy(self, x, y, red, green, blue=None, mode="classic"):
        """
        Controls a grid LED by its coordinates <x>, <y> and <reg>, <green> and <blue>
        intensity values. By default, the old and compatible "Classic" mode is used
        (8x8 matrix left has x=0). If <mode> is set to "pro", x=0 will light up the round
        buttons on the left of the Launchpad Pro (not available on other models).
        This method internally uses "LedCtrlRaw()". Please also notice the comments
        in that one.
        """

        if x < 0 or x > 9 or y < 0 or y > 9:
            return

        # rotate matrix to the right, column 9 overflows from right to left, same row
        if mode != "pro":
            x = (x + 1) % 10

        # swap y
        led = 90 - (10 * y) + x

        self.led_ctrl_raw(led, red, green, blue)

    def led_ctrl_xy_by_code(self, x, y, colorcode, mode="classic"):
        """
        Controls a grid LED by its coordinates <x>, <y> and its <colorcode>.
        By default, the old and compatible "Classic" mode is used (8x8 matrix left has x=0).
        If <mode> is set to "pro", x=0 will light up the round buttons on the left of the
        Launchpad Pro (not available on other models).
        About three times faster than the SysEx RGB method LedCtrlXY().
        """

        if x < 0 or x > 9 or y < 0 or y > 9:
            return

        # rotate matrix to the right, column 9 overflows from right to left, same row
        if mode != "pro":
            x = (x + 1) % 10

        # swap y
        led = 90 - (10 * y) + x

        self.led_ctrl_raw_by_code(led, colorcode)

    def led_ctrl_xy_by_rgb(self, x, y, color_list, mode="classic"):
        """
        New approach to color arguments.
        Controls a grid LED by its coordinates <x>, <y> and a list of colors <lstColor>.
        <lstColor> is a list of length 3, with RGB color information, [<r>,<g>,<b>]
        """

        if type(color_list) is not list or len(color_list) < 3:
            return

        if x < 0 or x > 9 or y < 0 or y > 9:
            return

        # rotate matrix to the right, column 9 overflows from right to left, same row
        if mode.lower() != "pro":
            x = (x + 1) % 10

        # swap y
        led = 90 - (10 * y) + x

        self.led_ctrl_raw(led, color_list[0], color_list[1], color_list[2])

    def led_all_on(self, colorcode=None):
        """
        Quickly sets all all LEDs to the same color, given by <colorcode>.
        If <colorcode> is omitted, "white" is used.
        """
        if colorcode is None:
            colorcode = LaunchpadPro.COLORS['white']
        else:
            colorcode = min(colorcode, 127)
            colorcode = max(colorcode, 0)

        self.midi.raw_write_system_exclusive([0, 32, 41, 2, 16, 14, colorcode])

    def reset(self):
        """
        (fake to) reset the Launchpad
        Turns off all LEDs
        """
        self.led_all_on(0)

    def button_state_raw(self):
        """
        Returns the raw value of the last button change (pressed/unpressed) as a list
        [ <button>, <value> ], in which <button> is the raw number of the button and
        <value> an intensity value from 0..127.
        >0 = button pressed; 0 = button released
        A constant force ("push longer") is suppressed here... ("208" Pressure Value)
        Notice that this is not (directly) compatible with the original ButtonStateRaw()
        method in the "Classic" Launchpad, which only returned [ <button>, <True/False> ].
        Compatibility would require checking via "== True" and not "is True".
        """
        a = self.midi.read_raw()
        if a:
            # Note:
            #  Beside "144" (Note On, grid buttons), "208" (Pressure Value, grid buttons) and
            #  "176" (Control Change, outer buttons), random (broken) SysEx messages
            #  can appear here:
            #   ('###', [[[240, 0, 32, 41], 4]])
            #   ('-->', [])
            #   ('###', [[[2, 16, 45, 0], 4]])
            #   ('###', [[[247, 0, 0, 0], 4]])
            #  ---
            #   ('###', [[[240, 0, 32, 41], 4]])
            #   ('-->', [])
            #  1st one is a SysEx Message (240, 0, 32, 41, 2, 16 ), with command Mode Status (45)
            #  in "Ableton Mode" (0) [would be 1 for Standalone Mode). "247" is the SysEx termination.
            #  Additionally, it's interrupted by a read failure.
            #  The 2nd one is simply cut. Notice that that these are commands usually send TO the
            #  Launchpad...

            if a[0] is None:
                return []
            elif a[0][0] == 144 or a[0][0] == 176:
                return [a[0][1], a[0][2]]
            else:
                return []
        else:
            return []

    def ButtonStateXY(self, mode="classic"):
        """
        Returns the raw value of the last button change (pressed/unpressed) as a list
        [ <x>, <y>, <value> ], in which <x> and <y> are the buttons coordinates and
        <value> is the intensity from 0..127.
        >0 = button pressed; 0 = button released
        A constant force ("push longer") is suppressed here... (TODO)
        Notice that this is not (directly) compatible with the original ButtonStateRaw()
        method in the "Classic" Launchpad, which only returned [ <button>, <True/False> ].
        Compatibility would require checking via "== True" and not "is True".

        :param mode:
        :return:
        """
        a = self.midi.read_raw()
        if a:

            if a[0][0] == 144 or a[0][0] == 176:

                if mode.lower() != "pro":
                    x = (a[0][1] - 1) % 10
                else:
                    x = a[0][1] % 10
                y = (99 - a[0][1]) / 10

                return [x, y, a[0][2]]
            else:
                return []
        else:
            return []


class LaunchpadMk2(LaunchpadPro):
    """
    For 3-color "Mk2" Launchpads with 8x8 matrix and 2x8 right/top rows
    """

    # LED AND BUTTON NUMBERS IN RAW MODE (DEC)
    #
    # Notice that the fine manual doesn't know that mode.
    # According to what's written there, the numbering used
    # refers to the "PROGRAMMING MODE", which actually does
    # not react to any of those notes (or numbers).
    #
    #        +---+---+---+---+---+---+---+---+
    #        |104|   |106|   |   |   |   |111|
    #        +---+---+---+---+---+---+---+---+
    #
    #        +---+---+---+---+---+---+---+---+  +---+
    #        | 81|   |   |   |   |   |   |   |  | 89|
    #        +---+---+---+---+---+---+---+---+  +---+
    #        | 71|   |   |   |   |   |   |   |  | 79|
    #        +---+---+---+---+---+---+---+---+  +---+
    #        | 61|   |   |   |   |   | 67|   |  | 69|
    #        +---+---+---+---+---+---+---+---+  +---+
    #        | 51|   |   |   |   |   |   |   |  | 59|
    #        +---+---+---+---+---+---+---+---+  +---+
    #        | 41|   |   |   |   |   |   |   |  | 49|
    #        +---+---+---+---+---+---+---+---+  +---+
    #        | 31|   |   |   |   |   |   |   |  | 39|
    #        +---+---+---+---+---+---+---+---+  +---+
    #        | 21|   | 23|   |   |   |   |   |  | 29|
    #        +---+---+---+---+---+---+---+---+  +---+
    #        | 11|   |   |   |   |   |   |   |  | 19|
    #        +---+---+---+---+---+---+---+---+  +---+
    #
    #
    #
    # LED AND BUTTON NUMBERS IN XY MODE (X/Y)
    #
    #          0   1   2   3   4   5   6   7      8
    #        +---+---+---+---+---+---+---+---+
    #        |0/0|   |2/0|   |   |   |   |   |         0
    #        +---+---+---+---+---+---+---+---+
    #
    #        +---+---+---+---+---+---+---+---+  +---+
    #        |0/1|   |   |   |   |   |   |   |  |   |  1
    #        +---+---+---+---+---+---+---+---+  +---+
    #        |   |   |   |   |   |   |   |   |  |   |  2
    #        +---+---+---+---+---+---+---+---+  +---+
    #        |   |   |   |   |   |5/3|   |   |  |   |  3
    #        +---+---+---+---+---+---+---+---+  +---+
    #        |   |   |   |   |   |   |   |   |  |   |  4
    #        +---+---+---+---+---+---+---+---+  +---+
    #        |   |   |   |   |   |   |   |   |  |   |  5
    #        +---+---+---+---+---+---+---+---+  +---+
    #        |   |   |   |   |4/6|   |   |   |  |   |  6
    #        +---+---+---+---+---+---+---+---+  +---+
    #        |   |   |   |   |   |   |   |   |  |   |  7
    #        +---+---+---+---+---+---+---+---+  +---+
    #        |   |   |   |   |   |   |   |   |  |8/8|  8
    #        +---+---+---+---+---+---+---+---+  +---+
    #

    def open(self, number=0, name="Mk2"):
        """
        Opens one of the attached Launchpad MIDI devices.
        Uses search string "Mk2", by default.
        """
        return super(LaunchpadMk2, self).open(number=number, name=name)

    def check(self, number=0, name="Mk2"):
        """
        Checks if a device exists, but does not open it.
        Does not check whether a device is in use or other, strange things...
        Uses search string "Mk2", by default.
        """
        return super(LaunchpadMk2, self).check(number=number, name=name)

    def led_all_on(self, colorcode=None):
        """
        Quickly sets all all LEDs to the same color, given by <colorcode>.
        If <colorcode> is omitted, "white" is used.
        """
        if colorcode is None:
            colorcode = LaunchpadPro.COLORS['white']
        else:
            colorcode = min(colorcode, 127)
            colorcode = max(colorcode, 0)

        self.midi.raw_write_system_exclusive([0, 32, 41, 2, 24, 14, colorcode])

    def reset(self):
        """
        (fake to) reset the Launchpad
        Turns off all LEDs
        :return:
        """
        self.led_all_on(0)

    def ButtonStateXY(self, **kwargs):
        """
        Returns the raw value of the last button change (pressed/unpressed) as a list
        [ <x>, <y>, <value> ], in which <x> and <y> are the buttons coordinates and
        <svalue> the intensity. Because the Mk2 does not come with full analog capabilities,
        unlike the "Pro", the intensity values for the "Mk2" are either 0 or 127.
        127 = button pressed; 0 = button released
        Notice that this is not (directly) compatible with the original ButtonStateRaw()
        method in the "Classic" Launchpad, which only returned [ <button>, <True/False> ].
        Compatibility would require checking via "== True" and not "is True".
        """
        a = self.midi.read_raw()
        if a:

            if a[0][0] == 144 or a[0][0] == 176:

                if a[0][1] >= 104:
                    x = a[0][1] - 104
                    y = 0
                else:
                    x = (a[0][1] - 1) % 10
                    y = (99 - a[0][1]) / 10

                return [x, y, a[0][2]]
            else:
                return []
        else:
            return []

    def led_ctrl_raw(self, number, red, green, blue=None):
        """
        Controls a grid LED by its position <number> and a color, specified by
        <red>, <green> and <blue> intensities, with can each be an integer between 0..63.
        If <blue> is omitted, this methos runs in "Classic" compatibility mode and the
        intensities, which were within 0..3 in that mode, are multiplied by 21 (0..63)
        to emulate the old brightness feeling :)
        Notice that each message requires 10 bytes to be sent. For a faster, but
        unfortunately "not-RGB" method, see "LedCtrlRawByCode()"
        :return:
        """

        number = min(number, 111)
        number = max(number, 0)

        if 89 < number < 104:
            return

        if blue is None:
            blue = 0
            red *= 21
            green *= 21

        limit_str = lambda n, mini, maxi: max(min(maxi, n), mini)

        red = limit_str(red, 0, 63)
        green = limit_str(green, 0, 63)
        blue = limit_str(blue, 0, 63)

        self.midi.raw_write_system_exclusive([0, 32, 41, 2, 16, 11, number, red, green, blue])

    def led_ctrl_raw_by_code(self, number, color_code=None):
        """
        Controls a grid LED by its position <number> and a color code <colorcode>
        from the Launchpad's color palette.
        If <colorcode> is omitted, 'white' is used.
        This method should be ~3 times faster that the RGB version "LedCtrlRaw()", which
        uses 10 byte, system-exclusive MIDI messages.
        :param number:
        :param color_code:
        :return:
        """

        number = min(number, 111)
        number = max(number, 0)

        if 89 < number < 104:
            return

        # TODO: limit/check colorcode
        if color_code is None:
            color_code = LaunchpadPro.COLORS['white']

        if number < 104:
            self.midi.raw_write(144, number, color_code)
        else:
            self.midi.raw_write(176, number, color_code)

    def led_ctrl_xy(self, x, y, red, green, blue=None, **kwargs):
        """
        Controls a grid LED by its coordinates <x>, <y> and <reg>, <green> and <blue>
        intensity values.
        This method internally uses "LedCtrlRaw()".
        Please also notice the comments in that one.
        """

        if x < 0 or x > 8 or y < 0 or y > 8:
            return

        # top row (round buttons)
        if y == 0:
            led = 104 + x
        else:
            # swap y
            led = 91 - (10 * y) + x

        self.led_ctrl_raw(led, red, green, blue)

    def led_ctrl_xy_by_rgb(self, x, y, color_list, **kwargs):
        """
        New approach to color arguments.
        Controls a grid LED by its coordinates <x>, <y> and a list of colors <lstColor>.
        <lstColor> is a list of length 3, with RGB color information, [<r>,<g>,<b>]
        """

        if type(color_list) is not list or len(color_list) < 3:
            return

        if x < 0 or x > 8 or y < 0 or y > 8:
            return

        # top row (round buttons)
        if y == 0:
            led = 104 + x
        else:
            # swap y
            led = 91 - (10 * y) + x

        self.led_ctrl_raw(led, color_list[0], color_list[1], color_list[2])

    def led_ctrl_xy_by_code(self, x, y, colorcode, **kwargs):
        """
        Controls a grid LED by its coordinates <x>, <y> and its <colorcode>.
        About three times faster than the, indeed much more comfortable RGB version
        "LedCtrlXY()"
        """

        if x < 0 or x > 8 or y < 0 or y > 8:
            return

        # top row (round buttons)
        if y == 0:
            led = 104 + x
        else:
            # swap y
            led = 91 - (10 * y) + x

        self.led_ctrl_raw_by_code(led, colorcode)


class LaunchControlXL(LaunchpadBase):
    """
    For 2-color Launch Control XL
    """

    # LED, BUTTON AND POTENTIOMETER NUMBERS IN RAW MODE (DEC)
    #
    #     +---+---+---+---+---+---+---+---+  +---++---+
    #     | 13| 29| 45| 61| 77| 93|109|125|  |NOP||NOP|
    #     +---+---+---+---+---+---+---+---+  +---++---+
    #     | 14| 30| 46| 62| 78| 94|110|126|  |104||105|
    #     +---+---+---+---+---+---+---+---+  +---++---+
    #     | 15| 31| 47| 63| 79| 95|111|127|  |106||107|
    #     +---+---+---+---+---+---+---+---+  +---++---+
    #
    #     +---+---+---+---+---+---+---+---+     +---+
    #     |   |   |   |   |   |   |   |   |     |105|
    #     |   |   |   |   |   |   |   |   |     +---+
    #     |   |   |   |   |   |   |   |   |     |106|
    #     | 77| 78| 79| 80| 81| 82| 83| 84|     +---+
    #     |   |   |   |   |   |   |   |   |     |107|
    #     |   |   |   |   |   |   |   |   |     +---+
    #     |   |   |   |   |   |   |   |   |     |108|
    #     +---+---+---+---+---+---+---+---+     +---+
    #
    #     +---+---+---+---+---+---+---+---+
    #     | 41| 42| 43| 44| 57| 58| 59| 60|
    #     +---+---+---+---+---+---+---+---+
    #     | 73| 74| 75| 76| 89| 90| 91| 92|
    #     +---+---+---+---+---+---+---+---+
    #
    #
    # LED NUMBERS IN X/Y MODE (DEC)
    #
    #       0   1   2   3   4   5   6   7      8    9
    #
    #     +---+---+---+---+---+---+---+---+  +---++---+
    #  0  |0/1|   |   |   |   |   |   |   |  |NOP||NOP|  0
    #     +---+---+---+---+---+---+---+---+  +---++---+
    #  1  |   |   |   |   |   |   |   |   |  |   ||   |  1
    #     +---+---+---+---+---+---+---+---+  +---++---+
    #  2  |   |   |   |   |   |5/2|   |   |  |   ||   |  2
    #     +---+---+---+---+---+---+---+---+  +---++---+
    #                                            8/9
    #     +---+---+---+---+---+---+---+---+     +---+
    #     |   |   |   |   |   |   |   |   |     |   |    3(!)
    #     |   |   |   |   |   |   |   |   |     +---+
    #     |   |   |   |   |   |   |   |   |     |   |    4(!)
    #  3  |   |   |2/3|   |   |   |   |   |     +---+
    #     |   |   |   |   |   |   |   |   |     |   |    5(!)
    #     |   |   |   |   |   |   |   |   |     +---+
    #     |   |   |   |   |   |   |   |   |     |   |    6
    #     +---+---+---+---+---+---+---+---+     +---+
    #
    #     +---+---+---+---+---+---+---+---+
    #  4  |   |   |   |   |   |   |   |   |              4(!)
    #     +---+---+---+---+---+---+---+---+
    #  5  |   |   |   |3/4|   |   |   |   |              5(!)
    #     +---+---+---+---+---+---+---+---+
    #
    #

    def open(self, number=0, name="Control XL", template=0):
        """
        Opens one of the attached Control XL MIDI devices.
        Uses search string "Control XL", by default.
        """

        # The user template number adds to the MIDI commands.
        # Make sure that the Control XL is set to the corresponding mode by
        # holding down one of the template buttons and selecting the template
        # with the lowest button row 1..8 (variable here stores that as 0..7 for
        # user or 8..15 for the factory templates).
        # By default, user template 0 is enabled
        self.user_template = template

        retval = super(LaunchControlXL, self).open(number=number, name=name)
        if retval:
            self.template_set(self.user_template)

        return retval

    def check(self, number=0, name="Control XL"):
        """
        Checks if a device exists, but does not open it.
        Does not check whether a device is in use or other, strange things...
        Uses search string "Pro", by default.
        """
        return super(LaunchControlXL, self).check(number=number, name=name)

    def template_set(self, template_num):
        """
        Sets the layout template.
        1..8 selects the user and 9..16 the factory setups.
        """
        if template_num < 1 or template_num > 16:
            return
        else:
            self.midi.raw_write_system_exclusive([0, 32, 41, 2, 17, 119, template_num - 1])

    def reset(self):
        """
        reset the Launchpad
        Turns off all LEDs
        :return:
        """
        self.midi.raw_write(176, 0, 0)

    def led_all_on(self, color_code=None):
        """
        all LEDs on
        # -- <colorcode> is here for backwards compatibility with the newer "Mk2" and "Pro"
        # -- classes. If it's "0", all LEDs are turned off. In all other cases turned on,
        # -- like the function name implies :-/
        """
        if color_code is None or color_code == 0:
            self.reset()
        else:
            self.midi.raw_write(176, 0, 127)

    def led_get_color(self, red, green):
        """
        Returns a Launchpad compatible "color code byte"
        NOTE: In here, number is 0..7 (left..right)
        :param red:
        :param green:
        :return:
        """
        # TODO: copy and clear bits
        led = 0

        red = min(int(red), 3)  # make int and limit to <=3
        red = max(red, 0)  # no negative numbers

        green = min(int(green), 3)  # make int and limit to <=3
        green = max(green, 0)  # no negative numbers

        led |= red
        led |= green << 4

        return led

    def led_ctrl_raw(self, number, red, green):
        """
        Controls a grid LED by its raw <number>; with <green/red> brightness: 0..3
        For LED numbers, see grid description on top of class.
        """
        # the order of the LEDs is really a mess
        led = self.led_get_color(red, green)
        self.midi.raw_write(144, number, led)

    def led_ctrl_xy(self, x, y, red, green):
        """
        Controls a grid LED by its coordinates <x> and <y>  with <green/red> brightness 0..3
        """
        # TODO: Note about the y coords
        if x < 0 or x > 9 or y < 0 or y > 6:
            return

        if x < 8:
            color = self.led_get_color(red, green)
        else:
            # the "special buttons" only have one color
            color = self.led_get_color(3, 3)

        # TODO: double code ahead ("37 + y"); query "y>2" first, then x...

        if x < 8:
            if y < 3:
                index = y * 8 + x
            elif 3 < y < 6:
                # skip row 3 and continue with 4 and 5
                index = (y - 1) * 8 + x
            else:
                return
        elif x == 8:
            # device, mute, solo, record
            if y > 2:
                index = 37 + y
            # up
            elif y == 1:
                index = 44
            # left
            elif y == 2:
                index = 46
            else:
                return
        elif x == 9:
            # device, mute, solo, record
            if y > 2:
                index = 37 + y
            # down
            elif y == 1:
                index = 45
            # right
            elif y == 2:
                index = 47
            else:
                return

        self.midi.raw_write_system_exclusive([0, 32, 41, 2, 17, 120, 0, index, color])

    def input_flush(self):
        """
        Clears the input buffer (The Launchpads remember everything...)
        """
        return self.button_flush()

    def input_state_raw(self):
        """
        Returns the raw value of the last button or potentiometer change as a list:
        potentiometers/sliders:  <pot.number>, <value>     , 0 ]
        buttons:                 <pot.number>, <True/False>, 0 ]
        """
        a = self.midi.read_raw()
        if a:

            # pressed
            if a[0][0] == 144:
                return [a[0][1], True, 127]
            # released
            elif a[0][0] == 128:
                return [a[0][1], False, 0]
            # potentiometers and the four cursor buttons
            elif a[0][0] == 176:
                # cursor buttons
                if 104 <= a[0][1] <= 107:
                    if a[0][2] > 0:
                        return [a[0][1], True, a[0][2]]
                    else:
                        return [a[0][1], False, 0]
                # potentiometers
                else:
                    return [a[0][1], a[0][2], 0]
            else:
                return []
        else:
            return []


class LaunchKeyMini(LaunchpadBase):
    """
    For 2-color LaunchKey Keyboards
    """

    # LED, BUTTON, KEY AND POTENTIOMETER NUMBERS IN RAW MODE (DEC)
    # NOTICE THAT THE OCTAVE BUTTONS SHIFT THE KEYS UP OR DOWN BY 12.
    #
    # LAUNCHKEY MINI:
    #
    #                   +---+---+---+---+---+---+---+---+
    #                   | 21| 22|...|   |   |   |   | 28|
    #     +---+---+---+ +---+---+---+---+---+---+---+---+ +---+  +---+
    #     |106|107|NOP| | 40| 41| 42| 43| 48| 49| 50| 51| |108|  |104|
    #     +---+---+---+ +---+---+---+---+---+---+---+---+ +---+  +---+
    #     |NOP|NOP|     | 36| 37| 38| 39| 44| 45| 46| 47| |109|  |105|
    #     +---+---+     +---+---+---+---+---+---+---+---+ +---+  +---+
    #
    #     +--+-+-+-+--+--+-+-+-+-+-+--+--+-+-+-+--+--+-+-+-+-+-+--+---+
    #     |  | | | |  |  | | | | | |  |  | | | |  |  | | | | | |  |   |
    #     |  |4| |5|  |  | | | | | |  |  |6| | |  |  | | | | |7|  |   |
    #     |  |9| |1|  |  | | | | | |  |  |1| | |  |  | | | | |0|  |   |
    #     |  +-+ +-+  |  +-+ +-+ +-+  |  +-+ +-+  |  +-+ +-+ +-+  |   |
    #     | 48| 50| 52|   |   |   |   | 60|   |   |   |   |   | 71| 72|
    #     |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
    #     | C | D | E |...|   |   |   | C2| D2|...|   |   |   |   | C3|
    #     +---+---+---+---+---+---+---+---+---+---+---+---+---+---+---+
    #
    #
    # LAUNCHKEY 25/49/61:
    #
    #    SLIDERS:           41..48
    #    SLIDER (MASTER):   7
    #

    def open(self, number=0, name="LaunchKey"):
        """
        Opens one of the attached LaunchKey devices.
        Uses search string "LaunchKey", by default.
        """
        retval = super(LaunchKeyMini, self).open(number=number, name=name)
        return retval

    def check(self, number=0, name="LaunchKey"):
        """
        Checks if a device exists, but does not open it.
        Does not check whether a device is in use or other, strange things...
        Uses search string "LaunchKey", by default.
        """
        return super(LaunchKeyMini, self).check(number=number, name=name)

    def input_state_raw(self):
        """
        Returns the raw value of the last button, key or potentiometer change as a list:
        potentiometers:   <pot.number>, <value>     , 0          ]
        buttons:          <but.number>, <True/False>, <velocity> ]
        keys:             <but.number>, <True/False>, <velocity> ]
        If a button does not provide an analog value, 0 or 127 are returned as velocity values.
        Because of the octave settings cover the complete note range, the button and potentiometer
        numbers collide with the note numbers in the lower octaves.
        """
        a = self.midi.read_raw()
        if a:

            # pressed key
            if a[0][0] == 144:
                return [a[0][1], True, a[0][2]]
            # released key
            elif a[0][0] == 128:
                return [a[0][1], False, 0]
            # pressed button
            elif a[0][0] == 153:
                return [a[0][1], True, a[0][2]]
            # released button
            elif a[0][0] == 137:
                return [a[0][1], False, 0]
            # potentiometers and the four cursor buttons
            elif a[0][0] == 176:
                # cursor, track and scene buttons
                if 104 <= a[0][1] <= 109:
                    if a[0][2] > 0:
                        return [a[0][1], True, 127]
                    else:
                        return [a[0][1], False, 0]
                # potentiometers
                else:
                    return [a[0][1], a[0][2], 0]
            else:
                return []
        else:
            return []

    def input_flush(self):
        """
        Clears the input buffer (The Launchpads remember everything...)
        :return:
        """
        return self.button_flush()


class Dicer(LaunchpadBase):
    """
    For that Dicer thingy...
    """

    # LED, BUTTON, KEY AND POTENTIOMETER NUMBERS IN RAW MODE (DEC)
    # NOTICE THAT THE OCTAVE BUTTONS SHIFT THE KEYS UP OR DOWN BY 10.
    #
    # FOR SHIFT MODE (HOLD ONE OF THE 3 MODE BUTTONS): ADD "5".
    #     +-----+  +-----+  +-----+             +-----+  +-----+  +-----+
    #     |#    |  |#    |  |     |             |#   #|  |#   #|  |    #|
    #     |  #  |  |     |  |  #  |             |  #  |  |     |  |  #  |
    #     |    #|  |    #|  |     |             |#   #|  |#   #|  |#    |
    #     +-----+  +-----+  +-----+             +-----+  +-----+  +-----+
    #
    #     +-----+            +---+               +----+           +-----+
    #     |#   #|            | +0|               |+120|           |    #|
    #     |     |            +---+               +----+           |     |
    #     |#   #|       +---+                         +----+      |#    |
    #     +-----+       |+10|                         |+110|      +-----+
    #                   +---+                         +----+
    #     +-----+  +---+                                  +----+  +-----+
    #     |#   #|  |+20|                                  |+100|  |     |
    #     |  #  |  +---+                                  +----+  |  #  |
    #     |#   #|                                                 |     |
    #     +-----+                                                 +-----+
    #
    #

    def open(self, number=0, name="Dicer"):
        """
        Opens one of the attached Dicer devices.
        Uses search string "dicer", by default.
        """
        retval = super(Dicer, self).open(number=number, name=name)
        return retval

    def check(self, number=0, name="Dicer"):
        """
        Checks if a device exists, but does not open it.
        Does not check whether a device is in use or other, strange things...
        Uses search string "dicer", by default.
        """
        return super(Dicer, self).check(number=number, name=name)

    def reset(self):
        """
        reset the Dicer
        Turns off all LEDs, restores power-on state, but does not disable an active light show.
        :return:
        """
        self.midi.raw_write(186, 0, 0)

    def led_all_off(self):
        """
        All LEDs off
        Turns off all LEDs, does not change or touch any other settings.
        """
        self.midi.raw_write(186, 0, 112)

    def button_state_raw(self):
        """
        Returns (an already nicely mapped and not raw :) value of the last button change as a list:
        buttons: <number>, <True/False>, <velocity> ]
        If a button does not provide an analog value, 0 or 127 are returned as velocity values.
        Small buttons select either 154, 155, 156 cmd for master or 157, 158, 159 for slave.
        Button numbers (1 to 5): 60, 61 .. 64; always
        Guess it's best to return: 1..5, 11..15, 21..25 for Master and 101..105, ... etc for slave
        Actually, as you can see, it's not "raw", but I guess those decade modifiers really
        make sense here (less brain calculations for you :)
        :return:
        """
        a = self.midi.read_raw()
        if a:

            if 154 <= a[0][0] <= 156:
                but_num = a[0][1]
                if 60 <= but_num <= 69:
                    but_num -= 59
                    but_num += 10 * (a[0][0] - 154)
                    if a[0][2] == 127:
                        return [but_num, True, 127]
                    else:
                        return [but_num, False, 0]
                else:
                    return []
            elif 157 <= a[0][0] <= 159:
                but_num = a[0][1]
                if 60 <= but_num <= 69:
                    but_num -= 59
                    but_num += 100 + 10 * (a[0][0] - 157)
                    if a[0][2] == 127:
                        return [but_num, True, 127]
                    else:
                        return [but_num, False, 0]
                else:
                    return []
        else:
            return []

    def led_set_lightshow(self, device, enable):
        """
        Enables or diabled the Dicer's built-in light show.
        Device: 0 = Master, 1 = Slave; enable = True/False
        """
        # Who needs error checks anyway?
        self.midi.raw_write(186 if device == 0 else 189, 0, 40 if enable else 41)

    def led_ctrl_raw(self, number, hue, intensity):
        """
        Controls an LED by its raw <number>; with <hue> brightness: 0..7 (red to green)
        and <intensity> 0..15
        For LED numbers, see grid description on top of class.
        :param number:
        :param hue:
        :param intensity:
        :return:
        """

        if number < 0 or number > 130:
            return

        # check if that is a slave device number (>100)
        if number > 100:
            number -= 100
            cmd = 157
        else:
            cmd = 154

        # determine the "page", "hot cue", "loop" or "auto loop"
        page = number / 10
        if page > 2:
            return

        # correct the "page shifted" LED number
        number = number - (page * 10)
        if number > 10:
            return

        # limit the hue range
        hue = min(int(hue), 7)  # make int and limit to <=7
        hue = max(hue, 0)  # no negative numbers

        # limit the intensity
        intensity = min(int(intensity), 15)  # make int and limit to <=15
        intensity = max(intensity, 0)  # no negative numbers

        self.midi.raw_write(cmd + page, number + 59, (hue << 4) | intensity)

    def mode_set(self, device, mode):
        """
        Sets the Dicer <device> (0=master, 1=slave) to one of its six modes,
        as specified by <mode>:
         0 - "cue"
         1 - "cue, shift lock"
         2 - "loop"
         3 - "loop, shift lock"
         4 - "auto loop"
         5 - "auto loop, shift lock"
         6 - "one page"
        :param device:
        :param mode:
        :return:
        """

        if device < 0 or device > 1:
            return

        if mode < 0 or mode > 6:
            return

        self.midi.raw_write(186 if device == 0 else 189, 17, mode)
