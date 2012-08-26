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
from traits.api import Float, Any, Button, Bool
from traitsui.api import View, Item, spring, ButtonEditor, HGroup
#============= standard library imports ========================
#============= local library imports  ==========================
from spectrometer_task import SpectrometerTask
import time

class RiseRate(SpectrometerTask):
    result = Float
    graph = Any
    clear_button = Button('Clear')
    calculated = Bool

    def _clear_button_fired(self):
        self.calculated = False

        self.graph.plots[0].overlays.pop()
        self.graph.plots[0].overlays.pop()
        self.graph.redraw()

    def _execute(self):
        self.result = 0
        self._starttime = self.graph.get_data()[-1]
        self._start_intensity = self._get_intensity()
        self._start_intensity = 0

        self.graph.add_vertical_rule(self._starttime, color=self.reference_detector.color.Get())
        self.graph.redraw()

    def _calculate_rise_rate(self):
        rise = self._get_intensity() - self._start_intensity

        ts = self.graph.get_data()[-1]
        run = (ts - self._starttime) / 60.
        self.graph.add_vertical_rule(ts)
        self.graph.redraw()
        self.calculated = True
        return rise / run

    def _get_intensity(self):
        return self.spectrometer.get_intensity(self.reference_detector.name)

    def _end(self):
        self.result = self._calculate_rise_rate()

    def traits_view(self):
        v = View(
                 Item('result', style='readonly',
                      format_str='%0.3f',
                      label='Rise Rate (fA/min)'),
                  HGroup(spring,
                         Item('clear_button', show_label=False, enabled_when='calculated'),
                         Item('execute',
                              enabled_when='not calculated',
                              editor=ButtonEditor(label_value='execute_label'),
                        show_label=False))

                  )
        return v
#============= EOF =============================================
