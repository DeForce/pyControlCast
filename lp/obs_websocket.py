import time

import pyobs
import pyobs.requests as req


class OBS(object):
    def __init__(self, config):
        self.host = config.obs.url
        self.port = config.obs.port
        self.password = config.obs.get('password')

        self.client = pyobs.Client(self.host, self.port, self.password)
        self.client.connect()

    def toggle_mute(self, source=None):
        return self.client.call(req.ToggleMute(source))

    def switch_scene(self, scene=None):
        return self.client.call(req.SetCurrentScene(scene))

    def show_and_hide_scene_item(self, source, timeout, delay=0):
        current_scene = self.client.call(req.GetCurrentScene()).name
        if delay:
            time.sleep(delay)
        self.client.call(req.SetSceneItemProperties(source, visible=True, scene_name=current_scene))
        time.sleep(timeout)
        self.client.call(req.SetSceneItemProperties(source, visible=False, scene_name=current_scene))

    def scale_up(self, source):
        current_scene = self.client.call(req.GetCurrentScene()).name
        current_item = self.client.call(req.GetSceneItemProperties(source))
        scale_x = current_item._returns['scale']['x'] + 0.2
        scale_y = current_item._returns['scale']['y'] + 0.2
        self.client.call(req.SetSceneItemProperties(source, x_scale=scale_x, y_scale=scale_y, scene_name=current_scene,
                                                   rotation=None))

    def scale_down(self, source):
        pass
