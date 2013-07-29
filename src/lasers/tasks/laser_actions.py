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
# from traits.api import HasTraits
# from traitsui.api import View, Item
from pyface.action.action import Action
from src.lasers.laser_managers.ilaser_manager import ILaserManager
from src.lasers.laser_managers.pychron_laser_manager import PychronLaserManager
from pyface.tasks.action.task_action import TaskAction
from pyface.tasks.task_layout import TaskLayout
from pyface.tasks.task_window_layout import TaskWindowLayout
#============= standard library imports ========================
#============= local library imports  ==========================

class BaseLaserAction(Action):
    manager_name = None
    manager = None
    def _get_manager(self, event, app=None):
        if self.manager is not None:
            manager = self.manager
        else:
            if app is None:
                app = event.task.window.application

            manager = app.get_service(ILaserManager,
                                      'name=="{}"'.format(self.manager_name),
                                      )
        return manager

class LocalLaserAction(BaseLaserAction):
    client_action = False
    def __init__(self, manager, *args, **kw):
        super(LocalLaserAction, self).__init__(*args, **kw)

#        man = self._get_manager(None, app=self.window.application)
        if isinstance(manager, PychronLaserManager) and not self.client_action:
            self.enabled = False

        self.manager = manager

class OpenScannerAction(LocalLaserAction):
    name = 'Open Scanner...'
    accelerator = 'Ctrl+T'
    def perform(self, event):
        manager = self._get_manager(event)
        if manager is not None:
            manager.open_scanner()


class OpenAutoTunerAction(LocalLaserAction):
    name = 'Open AutoTuner...'
    # accelerator = 'Ctrl+T'
    def perform(self, event):
        manager = self._get_manager(event)
        if manager is not None:
            manager.open_autotuner()

class LaserTaskAction(TaskAction):
    _enabled = None
    def _task_changed(self):
        if self.task:
            if self.task.id in ('pychron.fusions.co2',
                                'pychron.fusions.diode'):
                enabled = True
                if self.enabled_name:
                    if self.object:
                        enabled = bool(self._get_attr(self.object,
                                                   self.enabled_name, False))
                if enabled:
                    self._enabled = True
            else:
                self._enabled = False

    def _enabled_update(self):
        '''
             reimplement ListeningAction's _enabled_update
        '''
        if self.enabled_name:
            if self.object:
                self.enabled = bool(self._get_attr(self.object,
                                                   self.enabled_name, False))
            else:
                self.enabled = False
        elif self._enabled is not None:
            self.enabled = self._enabled
        else:
            self.enabled = bool(self.object)

class TestDegasAction(LaserTaskAction):
    name = 'Test Degas...'
    method = 'test_degas'

class OpenPatternAction(LaserTaskAction):
    name = 'Open Pattern...'
    method = 'open_pattern'


class NewPatternAction(LaserTaskAction):
    name = 'New Pattern...'
    method = 'new_pattern'

class LaserCalibrationAction(Action):
    def _get_task(self, event):
        app = event.task.window.application
        task_id = 'pychron.laser.calibration'
        task = app.open_task(task_id)
        return task

class PowerMapAction(LaserCalibrationAction):
    name = 'Power Map...'
    def perform(self, event):
        task = self._get_task(event)
        task.new_power_map()

class OpenPowerMapAction(LaserCalibrationAction):
    name = 'Power Map'
    accelerator = 'Ctrl+3'
    def perform(self, event):
        task = self._get_task(event)
        task.open_power_map()

class PowerCalibrationAction(LaserCalibrationAction):
    name = 'Power Calibration...'
    def perform(self, event):
        task = self._get_task(event)
        task.new_power_calibration()


#============= EOF =============================================
