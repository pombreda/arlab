#===============================================================================
# Copyright 2011 Jake Ross
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#   http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#===============================================================================

#============= enthought library imports =======================
from traits.api import Instance
#============= standard library imports ========================
import os
#============= local library imports  ==========================
from src.canvas.canvas2D.base_data_canvas import BaseDataCanvas
from src.canvas.canvas2D.video_underlay import VideoUnderlay
from src.canvas.canvas2D.camera import Camera
from src.helpers.paths import canvas2D_dir


class VideoCanvas(BaseDataCanvas):
    video = None
    use_camera = False
    camera = Instance(Camera)
#    use_backbuffer = True
    padding = 0
    pause = False

    def _camera_default(self):
        return Camera(parent=self)

    def __init__(self, *args, **kw):
        '''

        '''
        super(VideoCanvas, self).__init__(*args, **kw)

        self.video_underlay = VideoUnderlay(component=self, video=self.video)

        self.underlays.insert(0, self.video_underlay)


        for key, d in [('x_grid', dict(line_color=(1, 1, 0),
                                     line_width=1,
                                     line_style='dash',
                                     visible=self.show_grids)
                                     ),
                       ('y_grid', dict(line_color=(1, 1, 0),
                                      line_width=1,
                                      line_style='dash',
                                      visible=self.show_grids))]:
            o = getattr(self, key)
            o.trait_set(**d)

        self.set_camera()

        if self.video:
            self.on_trait_change(self.video.update_bounds, 'bounds')


    def set_camera(self):

        if self.use_camera:
            camera = self.camera
            camera.calibration_data.on_trait_change(self.parent.update_camera_params, 'xcoeff_str')
            camera.calibration_data.on_trait_change(self.parent.update_camera_params, 'ycoeff_str')
            camera.on_trait_change(self.parent.update_camera_params, 'focus_z')

            p = os.path.join(canvas2D_dir, 'camera.cfg')
            camera.load(p)

            camera.current_position = (0, 0)
            camera.set_limits_by_zoom(0)

            vid = self.video
            #swap red blue channels True or False
            vid.swap_rb = camera.swap_rb

            vid.vflip = camera.vflip
            vid.hflip = camera.hflip


#============= EOF ====================================
