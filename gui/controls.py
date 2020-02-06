import os

import wx


class Control:
    def __init__(self, parent, parent_sizer, properties):
        self.parent = parent
        self.parent_sizer = parent_sizer

        self.properties = properties

        self.box = wx.BoxSizer(wx.VERTICAL)

    def create_layout(self):
        self.parent_sizer.Add(self.box, 0, wx.ALL, border=5)


class ControlSound(Control):
    def __init__(self, parent, parent_sizer, properties):
        super().__init__(parent, parent_sizer, properties)

        file_sizer = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(parent, label='Path: ')
        path = os.path.abspath(properties.get('path'))
        self.file_picker = wx.FilePickerCtrl(parent)
        self.file_picker.SetPath(path)
        self.file_picker.Bind(wx.EVT_FILEPICKER_CHANGED, self.bind)
        file_sizer.Add(label, 0, wx.ALIGN_CENTRE)
        file_sizer.Add(self.file_picker)

        self.box.Add(file_sizer, 0, wx.EXPAND)

    def bind(self, event):
        pass
