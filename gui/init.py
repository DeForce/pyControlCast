import logging

import wx

from controls import ControlSound, Control

log = logging.getLogger('main')

GRID_SIZE = 8
BUTTON_SIZE = 32
AUTOMAP_ROW = -1


TYPES_MAP = {
    'sound': ControlSound
}


class LPButton:
    def __init__(self, parent, x, y, profile):
        self.x = x
        self.y = y
        self.profile = profile

        self.id = wx.NewId()

        self.parent = parent
        self.button = wx.ToggleButton(self.parent, size=wx.Size(BUTTON_SIZE, BUTTON_SIZE))

    @property
    def config(self):
        return self.parent.config.profiles[self.profile].buttons[f'{self.x}.{self.y}']

    @property
    def tooltip(self):
        button_data = self.config.toDict().get('action', {})
        return f'Button: {self.x}, {self.y}\nSettings: {button_data}'

    @property
    def color(self):
        color = self.parent.config.profiles[self.profile].buttons[f'{self.x}.{self.y}'].color

        red = color.get('red', 0) * (255 / 3)
        green = color.get('green', 0) * (255 / 3)
        return wx.Colour(red=red, green=green, blue=0)

    def reset_color(self):
        self.button.SetBackgroundColour(self.color)

    def press_color(self):
        self.button.SetBackgroundColour(wx.Colour(red=123, green=123, blue=255))

    def create(self):
        self.button.SetBackgroundColour(self.color)
        self.button.Bind(wx.EVT_TOGGLEBUTTON, self.bind)
        self.button.SetToolTip(self.tooltip)
        return self.button

    def bind(self, *args, **kwargs):
        wx.CallAfter(self.parent.button_pressed, MainFrame.get_id(self.x, self.y, self.profile))


class LPControlButton(LPButton):
    @property
    def tooltip(self):
        return f'Profile: {self.profile}'

    @property
    def color(self):
        if self.profile == self.parent.profile:
            return wx.Colour('red')
        elif self.profile is not None:
            return wx.Colour('green')
        return wx.Colour('black')


class LPItem(wx.Panel):
    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent

        main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer = wx.BoxSizer(wx.VERTICAL)

        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.add_button = wx.Button(self, label='+')
        self.add_button.Bind(wx.EVT_BUTTON, self.button_add)
        self.button_sizer.Add(self.add_button)

        self.remove_button = wx.Button(self, label='-')
        self.remove_button.Bind(wx.EVT_BUTTON, self.button_remove)
        self.button_sizer.Add(self.remove_button)

        self.controls_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.label = wx.StaticText(self, label='Not Editing any Button', style=wx.ALIGN_CENTER_VERTICAL)

        up_sizer = wx.BoxSizer(wx.HORIZONTAL)

        up_sizer.Add(self.label, 1, wx.ALIGN_CENTRE_VERTICAL)
        up_sizer.AddSpacer(10)
        up_sizer.Add(self.button_sizer)

        main_sizer.Add(up_sizer, 1, wx.ALL, border=5)
        main_sizer.Add(self.sizer, wx.ALL, border=5)
        self.main_sizer = main_sizer
        self.SetSizer(main_sizer)
        self.button_sizer.ShowItems(False)
        self.Show(True)

    def generate_settings(self, button):
        self.label.SetLabel(f'Editing Button {button.x} {button.y}')

        for action in button.config.action:
            self.create_control(action.toDict())

    def button_add(self, event):
        pass

    def button_remove(self, event):
        pass

    def create_control(self, action):
        self.button_sizer.ShowItems(True)

        for index, item in enumerate(self.sizer.GetChildren()):
            self.sizer.Remove(index)

        for name, properties in action.items():
            if name not in TYPES_MAP:
                continue

            static_box = wx.StaticBoxSizer(wx.VERTICAL, self, label=name)
            control_class: Control = TYPES_MAP.get(name)(self, static_box, properties)
            control_class.create_layout()

            self.sizer.Add(static_box)
        self.main_sizer.Fit(self)
        self.main_sizer.Layout()


class MainFrame(wx.Frame):
    def __init__(self, config, **kwargs):
        super().__init__(None, title='pyControlCast', size=wx.Size(700, 335))

        self.last_button = None
        self.buttons = {}
        self.config = config

        self.profile = self.config.get('active_profile', 'default')

        self.sizers = {
            profile: self.create_grid(profile)
            for profile in self.config.profiles
        }
        main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        side_sizer = wx.BoxSizer(wx.VERTICAL)

        self.profile_list = [None] * GRID_SIZE

        for profile_name, profile in self.config.profiles.items():
            self.profile_list[profile.order] = profile_name

        automap_sizer = wx.BoxSizer(wx.HORIZONTAL)
        for x in range(GRID_SIZE):
            button = LPControlButton(self, x, AUTOMAP_ROW, self.profile_list[x])
            self.buttons[self.get_id(x, AUTOMAP_ROW, self.profile_list[x])] = button
            automap_sizer.Add(button.create())
        side_sizer.Add(automap_sizer, flag=wx.BOTTOM, border=5)
        side_sizer.Add(self.sizers[self.profile])

        self.item_frame = LPItem(self)

        main_sizer.Add(side_sizer, flag=wx.ALL, border=5)
        main_sizer.Add(self.item_frame)
        self.sizer = side_sizer
        self.SetSizer(main_sizer)
        self.Show(True)

    @staticmethod
    def get_id(x, y, profile):
        return x, y, profile

    def create_grid(self, profile):
        buttons_sizer = wx.BoxSizer(wx.VERTICAL)

        for y in range(GRID_SIZE):
            horizontal_sizer = wx.BoxSizer(wx.HORIZONTAL)
            for x in range(GRID_SIZE + 1):
                button = LPButton(self, x, y, profile)
                self.buttons[self.get_id(x, y, profile)] = button

                last_row = 5 if x % (GRID_SIZE + 1) == GRID_SIZE else 0
                horizontal_sizer.Add(button.create(), flag=wx.LEFT, border=last_row)

            buttons_sizer.Add(horizontal_sizer)
        return buttons_sizer

    def button_pressed(self, b_id):
        if self.last_button is not None and self.last_button.id == self.buttons[b_id].id:
            return

        if self.last_button:
            self.last_button.reset_color()
        self.last_button = self.buttons[b_id]

        if self.last_button.y == AUTOMAP_ROW:
            self.replace_buttons(self.last_button)
        else:
            wx.CallAfter(self.item_frame.generate_settings, self.last_button)
        self.last_button.press_color()

    def replace_buttons(self, button):
        profile = button.profile
        log.info('replacing profile %s', profile)


class ControlCastGui(object):
    def __init__(self, config):
        # self.app = wx.App(True, filename=os.path.join(LOG_FOLDER, 'main.log'))
        self.app = wx.App(False)
        self.main = None

        self.config = config

    def start(self):
        self.main = MainFrame(self.config)
        self.app.MainLoop()


def init_gui(config):
    gui = ControlCastGui(config)
    gui.start()
