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
from traits.api import HasTraits, Str, Float, Event, String
from traitsui.api import View, Item, ButtonEditor
from src.loggable import Loggable
import math
import apptools.sweet_pickle as pickle
import os
from src.paths import paths
from src.traits_editors.custom_label_editor import CustomLabel
#============= standard library imports ========================
#============= local library imports  ==========================
SIMPLE_HELP = '''1. Locate center hole
2. Locate right hole
'''


class TrayCalibrator(Loggable):
    name = Str

    def get_controls(self):
        pass

    def handle(self, step, x, y, canvas):
        if step == 'Calibrate':
            canvas.new_calibration_item()
            return 'Locate Center', None, None, None
        elif step == 'Locate Center':
            canvas.calibration_item.set_center(x, y)
            return 'Locate Right', x, y, None
        elif step == 'Locate Right':
            canvas.calibration_item.set_right(x, y)
            self.save(canvas.calibration_item)
            return 'Calibrate', None, None, canvas.calibration_item.rotation

    def save(self, obj):
        p = self._get_path(self.name)
        with open(p, 'wb') as f:
            pickle.dump(obj, f)

    @classmethod
    def load(cls, name):
        path = cls._get_path(name)
        print os.path.isfile(path), path
        if os.path.isfile(path):
            with open(path, 'rb') as f:
                try:
                    obj = pickle.load(f)
                    return obj
                except pickle.PickleError, e:
                    print e

    @classmethod
    def _get_path(cls, name):
        return os.path.join(paths.hidden_dir, '{}_stage_calibration'.format(name))

#============= EOF =============================================
