#===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import Any, Str, Float, Bool

#============= standard library imports ========================
#============= local library imports  ==========================
from src.graph.tools.info_inspector import InfoOverlay, InfoInspector


class ExtractionLineInfoTool(InfoInspector):
    active_item = Any
    scene = Any

    manager = Any
    name = Str
    volume = Float

    active = Bool(False)

    def assemble_lines(self):
        return [self.name, 'volume= {}'.format(self.volume)]

    def normal_mouse_move(self, event):
        if self.active:
            x, y = event.x, event.y
            item = self.scene.get_is_in(x, y)
            if not item:
                self.current_position = None
                self.metadata_changed = True
                self.active = False

    def normal_key_pressed(self, event):

        ok = event.character == 'v' and not self.active
        self.active = False

        if self.manager.use_network and ok:
            x, y = event.x, event.y
            self.current_screen = x, y
            item = self.scene.get_is_in(x, y)

            if item:
                self.current_position = x, y

                self.volume = self.manager.get_volume(item.name)
                self.name = item.name
                self.metadata_changed = True
                self.active = True
                #else:
                #    self.current_position=None


class ExtractionLineInfoOverlay(InfoOverlay):
    tool = ExtractionLineInfoTool

#============= EOF =============================================

