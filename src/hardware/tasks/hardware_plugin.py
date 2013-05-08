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
from traits.api import HasTraits, Bool, Instance, List, Dict
# from traitsui.api import View, Item
from src.envisage.tasks.base_task_plugin import BaseTaskPlugin
from envisage.extension_point import ExtensionPoint
from src.managers.hardware_manager import HardwareManager
# from src.remote_hardware.remote_hardware_manager import RemoteHardwareManager
from src.hardware.flag_manager import FlagManager
# from apptools.preferences.preference_binding import bind_preference
from src.hardware.core.i_core_device import ICoreDevice
from envisage.ui.tasks.task_factory import TaskFactory
from src.hardware.tasks.hardware_task import HardwareTask
from envisage.ui.tasks.task_extension import TaskExtension
from pyface.tasks.action.task_action import TaskAction
from pyface.action.action import Action
from pyface.tasks.action.schema_addition import SchemaAddition
#============= standard library imports ========================
#============= local library imports  ==========================
class Preference(HasTraits):
    pass

class SerialPreference(Preference):
    auto_find_handle = Bool
    auto_write_handle = Bool

class DevicePreferences(HasTraits):
    serial_preference = Instance(SerialPreference)
    def _serial_preference_default(self):
        return SerialPreference()

class OpenFlagManagerAction(Action):
    name = 'Flag Manager'
    def perform(self, event):
        app = event.task.window.application
        man = app.get_service('src.hardware.flag_manager.FlagManager')

        app.open_view(man)


class HardwarePlugin(BaseTaskPlugin):
    '''
        
    '''
    id = 'pychron.hardware.plugin'
    managers = ExtensionPoint(List(Dict),
                              id='pychron.hardware.managers')

    my_managers = List(contributes_to='pychron.hardware.managers')

    def _my_task_extensions_default(self):
        return [TaskExtension(actions=[SchemaAddition(id='Flag Manager',
                                                      factory=OpenFlagManagerAction,
                                                      path='MenuBar/Tools'), ])]

    def _tasks_default(self):
        return [TaskFactory(id='tasks.hardware',
                            name='Hardware',
                            factory=self._factory
                            )
                ]

    def _factory(self):
        man = self.application.get_service(HardwareManager)
        task = HardwareTask(manager=man)
        return task

    def _service_offers_default(self):
        '''
        '''

        so = self.service_offer_factory(
                          protocol=HardwareManager,
                          factory=self._hardware_manager_factory)

#        so1 = self.service_offer_factory(
#                          protocol=RemoteHardwareManager,
#                          factory=self._remote_hardware_manager_factory)

        so2 = self.service_offer_factory(
                          protocol=FlagManager,
                          factory=self._flag_manager_factory
                          )
#        return [so, so1, so2]
        return [so, so2]

    def _flag_manager_factory(self):
        return FlagManager(application=self.application)

    def _hardware_manager_factory(self):
        return HardwareManager(application=self.application)

#    def _remote_hardware_manager_factory(self):
#        return RemoteHardwareManager(application=self.application)

    def _my_managers_default(self):
        return [dict(name='hardware', manager=self._hardware_manager_factory())]
#    def _system_lock_manager_factory(self):
#        return SystemLockManager(application=self.application)

    def start(self):
        '''
        '''
        # if self.managers:
        from src.initializer import Initializer

        dp = DevicePreferences()
        afh = self.application.preferences.get('pychron.hardware.auto_find_handle')
        awh = self.application.preferences.get('pychron.hardware.auto_write_handle')
        if afh is not None:
            toBool = lambda x: True if x == 'True' else False
            dp.serial_preference.auto_find_handle = toBool(afh)
            dp.serial_preference.auto_write_handle = toBool(awh)

        ini = Initializer(device_prefs=dp)

        for m in self.managers:
            ini.add_initialization(m)

        # any loaded managers will be registered as services
        if not ini.run(application=self.application):
            self.application.exit()
            return

        # create the hardware server
#        rhm = self.application.get_service(RemoteHardwareManager)
#        bind_preference(rhm, 'enable_hardware_server', 'pychron.hardware.enable_hardware_server')
#        bind_preference(rhm, 'enable_directory_server', 'pychron.hardware.enable_directory_server')
#        rhm.bootstrap()

    def stop(self):

#        rhm = self.application.get_service(RemoteHardwareManager)
#        rhm.stop()

        if self.managers:
            for m in self.managers:
                man = m['manager']
                if man:
                    man.kill()
                    man.close_ui()

        for s in self.application.get_services(ICoreDevice):
            if s.is_scanable:
                if s._scanning and not s._auto_started:
                    s.stop_scan()
#                s.save_to_db()
#============= EOF =============================================
