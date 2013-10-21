#===============================================================================
# Copyright 2012 Jake Ross
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
from src.canvas.canvas2D.base_data_canvas import BaseDataCanvas
from src.canvas.canvas2D.scene.scene import Scene
#============= standard library imports ========================
#============= local library imports  ==========================
class SceneCanvas(BaseDataCanvas):
    scene = Instance(Scene)
    _frozen = False

    def _scene_changed(self, name, old, new):

        self.scene.on_trait_change(self.request_redraw,
                                   'layout_needed')
        if old:
            old.on_trait_change(self.request_redraw,
                                'layout_needed', remove=True)

    def freeze(self):
        self._frozen = True

    def thaw(self):
        self._frozen = False

    def clear_all(self):
        if self.scene:
            self.scene.reset_layers()

    def show_all(self):
        if self.scene:
            for li in self.scene.layers:
                li.visible = True
            self.request_redraw()

    def hide_all(self):
        if self.scene:
            for li in self.scene.layers:
                li.visible = False
            self.request_redraw()

    def _draw_hook(self, gc, *args, **kw):

        if self.scene:
        #             self.scene.render_components(gc, weakref.ref(self)())
            self.scene.render_components(gc, self)

#============= EOF =============================================
