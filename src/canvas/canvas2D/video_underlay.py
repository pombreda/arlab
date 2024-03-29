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
from traits.api import Instance, Any
from chaco.api import AbstractOverlay
#============= standard library imports ========================

#============= local library imports  ==========================
# from src.image.video import Video

class VideoUnderlay(AbstractOverlay):
    '''
    '''
    video = Any
#    video = Instance(Video)
#    use_backbuffer = True
#    use_backbuffer = False
#    swap_rb = True
#    mirror = False
#    flip = False
#    pause = False
    _cached_image = None
    def overlay(self, component, gc, *args, **kw):
        '''

        '''
        with gc:
            gc.clip_to_rect(component.x, component.y,
                        component.width, component.height)

            if self.video:
                img = self.video.get_image_data()
            else:
                img = self._cached_image
#            if not self.pause:
#            else:
#                img = self._cached_image

            if img is not None:
                gc.draw_image(img)
                self._cached_image = img


#============= EOF ====================================
