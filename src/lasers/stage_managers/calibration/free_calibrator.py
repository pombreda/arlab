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
from traits.api import HasTraits, Float, Button, Bool, Any, String, List
from traitsui.api import View, Item, HGroup, ButtonEditor
# from src.ui.custom_label_editor import CustomLabel
# from src.geometry.geometry import calculate_reference_frame_center, calc_length
from src.lasers.stage_managers.calibration.calibrator import TrayCalibrator
from src.geometry.reference_point import ReferencePoint
from src.geometry.affine import calculate_rigid_transform
#============= standard library imports ========================
#============= local library imports  ==========================


class FreeCalibrator(TrayCalibrator):
    accept_point = Button
    finished = Button
    calibrating = Bool(False)

    manager = Any

    points = List
    append_current_calibration = Bool(False)

    def get_controls(self):
        cg = HGroup(Item('object.calibrator.accept_point',
                         enabled_when='object.calibrator.calibrating',
                       show_label=False),
                    Item('object.calibrator.append_current_calibration',
                         label='Append Points',
                         tooltip='Should points be appended to the current calibration or a new calibration started?'
                         )
                    )
        return cg

    def handle(self, step, x, y, canvas):
        if step == 'Calibrate':
            self.calibrating = True
            if self.append_current_calibration:
                if not self.points:
                    self.points = []
                    canvas.new_calibration_item()
            else:
                canvas.new_calibration_item()
                self.points = []
            return dict(calibration_step='End Calibrate')
#            return 'End Calibrate', None, None, None, None, None

        elif step == 'End Calibrate':
            self.calibrating = False
            d = dict(calibration_step='Calibrate')
            if self.points:
                refpoints, points = zip(*self.points)

                scale, theta, (tx, ty), err = calculate_rigid_transform(refpoints,
                                                                   points)

                # set canvas calibration
                ca = canvas.calibration_item
                ca.cx, ca.cy = tx, ty
                ca.rotation = theta
                ca.scale = 1 / scale
                d.update(dict(cx=tx, cy=ty, rotation=theta, scale=1 / scale, error=err
                            ))
            return d
#                return 'Calibrate', tx, ty, theta, 1 / scale, err
#            else:
#                return dict(calibration_step='Calibrate')
#                return 'Calibrate', None, None, None, None, None

    def _accept_point(self):
        sp = self.manager.get_current_position()
        npt = self._get_point(sp)
        if npt:
            self.points.append(npt)

    def _get_point(self, sp):
        rp = ReferencePoint(sp)
        info = rp.edit_traits()
        if info.result:
            refp = rp.x, rp.y
            return refp, sp

#===============================================================================
# handlers
#===============================================================================
    def _accept_point_fired(self):
        self._accept_point()



#============= EOF =============================================
