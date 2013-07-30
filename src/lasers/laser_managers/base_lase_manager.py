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
from traits.api import Instance, Event, Bool, Any, Property, Str, implements, \
    Float

from src.lasers.stage_managers.stage_manager import StageManager
from src.lasers.pattern.pattern_executor import PatternExecutor
from src.lasers.pattern.pattern_maker_view import PatternMakerView
from src.managers.manager import Manager
from src.lasers.laser_managers.ilaser_manager import ILaserManager
from src.ui.led_editor import LED
from src.helpers.filetools import list_directory
from src.paths import paths
#============= standard library imports ========================
#============= local library imports  ==========================

class BaseLaserManager(Manager):
    implements(ILaserManager)
    pattern_executor = Instance(PatternExecutor)
    use_video = Bool(False)

    enable = Event
    enable_label = Property(depends_on='enabled')
    enabled_led = Instance(LED, ())
    enabled = Bool(False)

    stage_manager = Instance(StageManager)

    requested_power = Any
    status_text = Str
    pulse = Any
    laser_controller = Any
    mode = 'normal'

    use_calibrated_power = Bool(True)
    requested_power = Property(Float, depends_on='_requested_power')
    units = Property(depends_on='use_calibrated_power')
    _requested_power = Float
    _calibrated_power = None

    def initialize_video(self):
        if self.use_video:
            self.stage_manager.initialize_video()
    def is_ready(self):
        return True

    def take_snapshot(self, *args, **kw):
        pass

    def end_extract(self, *args, **kw):
        pass

    def extract(self, *args, **kw):
        pass

    def prepare(self):
        pass

    def set_motor_lock(self, name, value):
        pass

    def set_motor(self, *args, **kw):
        pass

    def get_motor(self, name):
        pass

    def enable_device(self):
        return self.enable_laser()

    def disable_device(self):
        self.disable_laser()

    def enable_laser(self):
        pass

    def disable_laser(self):
        pass

    def get_pattern_names(self):
        p = paths.pattern_dir
        extension = '.lp,.txt'
        patterns = list_directory(p, extension)
        return ['', ] + patterns

#     def new_pattern_maker(self):
#         pm = PatternMakerView()
#         self.open_view(pm)
#
#     def open_pattern_maker(self):
#         pm = PatternMakerView(
#                               executor=self.pattern_executor
#                               )
#         if pm.load_pattern():
#             self.open_view(pm)

    def execute_pattern(self, name=None, block=False):
        pm = self.pattern_executor
        if pm.load_pattern(name):
            pm.execute(block)

    def stop_pattern(self):
        if self.pattern_executor:
            self.pattern_executor.stop()

    def isPatterning(self):
        if self.pattern_executor:
            return self.pattern_executor.isPatterning()

    def _pattern_executor_default(self):
        controller = None
        if hasattr(self, 'stage_manager'):
            controller = self.stage_manager.stage_controller

        pm = PatternExecutor(application=self.application, controller=controller)
        return pm

    def move_to_position(self, pos, *args, **kw):
        if not isinstance(pos, list):
            pos = [pos]

        for pi in pos:
            self._move_to_position(pi)

        return True

    def trace_path(self, *args, **kw):
        pass

    def drill_point(self, *args, **kw):
        pass

    def set_motors_for_point(self, pt):
        pass

#===============================================================================
# getter/setters
#===============================================================================
    def _get_enable_label(self):
        '''
        '''
        return 'DISABLE' if self.enabled else 'ENABLE'

    def _get_calibrated_power(self, power, use_calibration=True, verbose=True):
        if self.use_calibrated_power and use_calibration:
            power = max(0, self.laser_controller.get_calibrated_power(power))
        return power

    def _get_requested_power(self):
        return self._requested_power

    def _get_units(self):
        return '(W)' if self.use_calibrated_power else '(%)'
#===============================================================================
# handlers
#===============================================================================
    def _enabled_changed(self):
        if self.enabled:
            self.enabled_led.state = 'green'
        else:
            self.enabled_led.state = 'red'

    def _use_video_changed(self):
        if not self.use_video:
            try:
                self.stage_manager.video.close()
            except AttributeError, e:
                print 'use video 1', e

        try:
            sm = self._stage_manager_factory(self.stage_args)

            sm.stage_controller = self.stage_manager.stage_controller
            sm.stage_controller.parent = sm
            if self.plugin_id:
                sm.bind_preferences(self.plugin_id)
#             sm.visualizer = self.stage_manager.visualizer

            sm.load()

            self.stage_manager = sm
        except AttributeError, e:
            print 'use video 2', e

    def _stage_manager_factory(self, args):
        self.stage_args = args
        if self.use_video:
            from src.lasers.stage_managers.video_stage_manager import VideoStageManager
            klass = VideoStageManager
        else:
            klass = StageManager

        args['parent'] = self
        sm = klass(**args)
        return sm
#============= EOF =============================================
