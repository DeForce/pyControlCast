import sys

import wx


class ControlCastGui(object):
    def __init__(self):
        self.app = wx.App(False)

    def start(self):
        self.app.MainLoop()
        app = wx.App(True, filename=os.path.join(LOG_FOLDER, 'main.log'))

        w = QWidget()
        w.resize(250, 150)
        w.setWindowTitle('Simple')
        w.show()

        sys.exit(app.exec_())


def init_gui(config):
    pass
    gui = ControlCastGui()
    gui.start()
