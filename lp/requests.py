from pyobs.base_classes import BaseRequest


class SetSceneItemProperties(BaseRequest):
    def __init__(self, item,
                 scene_name=None, rotation=None, visible=None, locked=None,
                 position_x=None, position_y=None, scale_x=None, scale_y=None):
        BaseRequest.__init__(self)
        self._name = 'SetSceneItemProperties'
        self._params['item'] = item
        self._params['scene-name'] = scene_name
        self._params['rotation'] = rotation
        self._params['visible'] = visible
        self._params['locked'] = locked
        self._params['position.x'] = position_x
        self._params['position.y'] = position_y
        self._params['scale'] = {
            'x': scale_x,
            'y': scale_y
        }
