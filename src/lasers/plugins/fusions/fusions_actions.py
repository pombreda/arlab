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
from pyface.action.api import Action
from src.envisage.core.action_helper import open_manager, open_selector
from src.lasers.laser_managers.laser_manager import ILaserManager
from src.lasers.laser_managers.pychron_laser_manager import PychronLaserManager

#from guppy import hpy
#hp = hpy()

#============= standard library imports ========================
#============= local library imports  ==========================
class LaserAction(Action):
    client_action = False
    def __init__(self, window=None, *args, **kw):
        super(LaserAction, self).__init__(window=window, *args, **kw)
        man = window.workbench.application.get_service(ILaserManager)
        if isinstance(man, PychronLaserManager) and not self.client_action:
            self.enabled = False

class FOpenLaserManagerAction(LaserAction):
    accelerator = 'Ctrl+L'
    def perform(self, event):
        manager = self.get_manager(event)
        if manager is not None:
            app = self.window.application
            open_manager(app, manager)


class FOpenMotionControllerManagerAction(LaserAction):

    def perform(self, event):
        man = self.get_manager(event)
        if man is not None:
            m = man.stage_manager.motion_configure_factory(view_style='full_view')
            app = self.window.application
            open_manager(app, m)


class FPowerMapAction(LaserAction):
    name = 'Power Map'

    def perform(self, event):
        manager = self.get_manager(event)
        if manager is not None:
            man = manager.get_power_map_manager()
            app = self.window.application
            open_manager(app, man)

class FPowerCalibrationAction(LaserAction):
    def perform(self, event):
        manager = self.get_manager(event)
        if manager is not None:
            app = self.window.application
            open_manager(app, manager.power_calibration_manager)


class FOpenStageVisualizerAction(LaserAction):
#    def __init__(self, *args, **kw):
#        print 'sffsadf', args, kw
#        super(FStageVisualizerAction, self).__init__(*args, **kw)
#
#        man = self.get_manager(None, window=kw['window'])
##        print man.use_video?
#        self.enabled_when = 'enabled'
#        self.enabled = man.use_video
#        man.on_trait_change(self.update_enabled, 'use_video')

#    def update_enabled(self, obj, name, new):
#        if name == 'use_video':
#            self.enabled = new
#        print self.enabled

    def perform(self, event):
        manager = self.get_manager(event)
        if manager is not None:
            app = self.window.application
            open_manager(app, manager.stage_manager.visualizer)

class FLoadStageVisualizerAction(LaserAction):
    def perform(self, event):
        manager = self.get_manager(event)
        if manager is not None:
            app = self.window.application
            visualizer = manager.stage_manager.visualizer
            visualizer.load_visualization()
            open_manager(app, visualizer)


#===============================================================================
# database selectors
#===============================================================================
class FOpenPowerCalibrationAction(LaserAction):
    def perform(self, event):
        manager = self.get_manager(event)
        if manager is not None:
            db = manager.get_power_calibration_database()
            open_selector(db, self.window.application)

class FOpenPowerMapAction(LaserAction):
    name = 'Open Map Result'

    def perform(self, event):
        manager = self.get_manager(event)
        if manager is not None:
            db = manager.get_power_map_manager().database
            open_selector(db, self.window.application)


class FOpenPowerRecordGraphAction(LaserAction):
    name = 'Open Power Scan Result'

    def perform(self, event):
        manager = self.get_manager(event)
        if manager is not None:
            db = manager.get_power_database()
            open_selector(db, self.window.application)


class FOpenVideoAction(LaserAction):
    name = 'Open Video Result'

    def perform(self, event):
        manager = self.get_manager(event)
        if manager is not None:
            db = manager.stage_manager.get_video_database()
            open_selector(db, self.window.application)


class FMotorConfigureAction(LaserAction):
    def perform(self, event):
        manager = self.get_manager(event)
        if manager is not None:
            manager.open_motor_configure()

class FConfigureBrightnessMeterAction(LaserAction):
    def __init__(self, *args, **kw):
        super(FConfigureBrightnessMeterAction, self).__init__(*args, **kw)
        man = self.get_manager(None, app=self.window.application)
        man.on_trait_change(self._update_enable, 'use_video')
        if man.use_video:
            self.enabled = False

    def _update_enable(self, new):
        self.enabled = new

    def perform(self, event):
        manager = self.get_manager(event)
        if manager is not None:
            app = self.window.application
            open_manager(app, manager.brightness_meter)
#===============================================================================
# initializations
#===============================================================================
#class FInitializeBeamAction(LaserAction):
#    def perform(self, event):
#        manager = self.get_manager(event)
#        if manager is not None:
#            manager.do_motor_initialization('beam')
#
#
#class FInitializeZoomAction(LaserAction):
#    def perform(self, event):
#        manager = self.get_manager(event)
#        if manager is not None:
#            manager.do_motor_initialization('zoom')

#===============================================================================
# patterning
#===============================================================================
class FOpenPatternAction(Action):
    def perform(self, event):
        manager = self.get_manager(event)
        if manager is not None:
            manager.open_pattern_maker()

class FNewPatternAction(Action):
    def perform(self, event):
        manager = self.get_manager(event)
        if manager is not None:
            manager.new_pattern_maker()

class FExecutePatternAction(Action):
    def perform(self, event):
        manager = self.get_manager(event)
        if manager is not None:
            manager.execute_pattern()

#============= EOF =============================================
