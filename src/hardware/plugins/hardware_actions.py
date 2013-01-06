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
from pyface.action.api import Action

#============= standard library imports ========================
#============= local library imports  ==========================
from src.envisage.core.action_helper import open_protocol, open_manager
from src.database.adapters.hardware_adapter import HardwareAdapter
from src.hardware.plugins.register_manager import RegisterManager


class OpenHardwareManagerAction(Action):
    '''
    '''
    description = 'Open the hardware manager'
    name = 'Hardware Manager'
    def perform(self, event):
        '''
        '''
        p = 'src.managers.hardware_manager.HardwareManager'
        from src.managers.hardware_manager import HardwareManager

        open_protocol(self.window, HardwareManager)

class OpenRemoteHardwareServerAction(Action):
    '''
    '''
    description = 'Open the remote hardware server'
    name = 'Remote Hardware Server'

    def __init__(self, *args, **kw):
        from globals import globalv
        self.enabled = not globalv.use_ipc
        super(OpenRemoteHardwareServerAction, self).__init__(*args, **kw)

    def perform(self, event):
        '''
        '''
        p = 'src.remote_hardware.remote_hardware_manager.RemoteHardwareManager'
        open_protocol(self.window, p)


class OpenDeviceScansAction(Action):
    '''
    '''
    description = 'Open device scans selector'
    name = 'Open Device Scans'

    def perform(self, event):
        '''
        '''
        from src.paths import paths

#        p = 'src.remote_hardware.remote_hardware_manager.RemoteHardwareManager'
#        open_protocol(self.window, p)
        db = HardwareAdapter(name=paths.device_scan_db,
                               kind='sqlite',
                               application=self.window.application)
#        open_selector(db, self.window.application)
        db.connect(test=False)
        man = db.selector
        open_manager(self.window.application, man)


class RegisterDeviceAction(Action):
    def perform(self, event):
        rdm = RegisterManager(application=self.window.application)
        rdm.load()
        open_manager(self.window.application,
                     rdm
                     )


class OpenFlagManagerAction(Action):
    def __init__(self, *args, **kw):
        super(OpenFlagManagerAction, self).__init__(*args, **kw)
        fm = self.window.application.get_service('src.extraction_line.flag_manager.FlagManager')
        self.enabled = False
        if fm and (fm.flags or fm.timed_flags):
            self.enabled = True
#        self.enabled = fm and (bool(len(fm.flags)) or bool(len(fm.timed_flags)))

    def perform(self, event):
        fm = event.window.application.get_service('src.extraction_line.flag_manager.FlagManager')
        open_manager(self.window.application,
                     fm
                     )



#============= EOF ====================================
