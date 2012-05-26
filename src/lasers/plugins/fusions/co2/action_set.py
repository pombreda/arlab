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
from envisage.ui.action.api import Action#, Group, Menu, ToolBar
from envisage.ui.workbench.api import WorkbenchActionSet

#============= standard library imports ========================

#============= local library imports  ==========================


class FusionsCo2ActionSet(WorkbenchActionSet):
    '''
    '''
    id = 'pychron.fusions.co2.action_set'
#    menus = [
#           Menu(name = '&File', path = 'MenuBar')
#           ]
    name = 'CO2'
    action_path = 'src.lasers.plugins.fusions.co2.actions:'

    def _actions_default(self):
        laser_path = 'MenuBar/Lasers/{}'.format(self.name)
        results_path = 'MenuBar/Results/{}'.format(self.name)
        return [
                Action(name='Laser Manager',
                       path=laser_path,
                       class_name='{}OpenLaserManagerAction'.format(self.action_path)
                       ),
                Action(name='Configure Brightness Meter',
                       path=laser_path,
                       class_name='{}ConfigureBrightnessMeterAction'.format(self.action_path)
                       ),
                Action(name='Power Map',
                       path=laser_path,
                       class_name='{}PowerMapAction'.format(self.action_path)
                       ),
                Action(name='Power Calibration',
                       path=laser_path,
                       class_name='{}PowerCalibrationAction'.format(self.action_path)
                       ),
                Action(name='Beam',
                       path='{}/Initialize'.format(laser_path),
                       class_name='{}InitializeBeamAction'.format(self.action_path)
                       ),
                Action(name='Zoom',
                       path='{}/Initialize'.format(laser_path),
                       class_name='{}InitializeZoomAction'.format(self.action_path)
                       ),


                Action(name='Power Recording',
                       path=results_path,
                       class_name='{}OpenPowerRecordGraphAction'.format(self.action_path)
                       ),
                Action(name='Power Map',
                       path=results_path,
                       class_name='{}OpenPowerMapAction'.format(self.action_path)
                       ),
                Action(name='Video',
                       path=results_path,
                       class_name='{}OpenVideoAction'.format(self.action_path)
                       ),
                Action(name='Power Calibration',
                       path=results_path,
                       class_name='{}OpenPowerCalibrationAction'.format(self.action_path)
                       ),



##                Action(name='Configure Motion Controller',
##                       path='MenuBar/Lasers/{}'.format(self.name),
##                       class_name='src.lasers.plugins.laser_actions:OpenMotionControllerManagerAction'
##                       ),
#
#
#                Action(name='Pattern Manager',
#                       path='MenuBar/Lasers/{}/Pattern'.format(self.name),
#                       class_name='src.lasers.plugins.laser_actions:OpenPatternManagerAction'),
#                Action(name='Execute Pattern',
#                       path='MenuBar/Lasers/{}/Pattern'.format(self.name),
#                       class_name='src.lasers.plugins.laser_actions:ExecutePatternAction'
#                       ),
#
#                Action(name='Power Map',
#                       path='MenuBar/Lasers/{}/Scans'.format(self.name),
#                       class_name='src.lasers.plugins.laser_actions:PowerMapAction'
#                       ),
##                Action(name='Pulse',
##                       path='MenuBar/Lasers/Scans',
##                       class_name='src.lasers.plugins.laser_actions:PulseAction'
##                       ),
##                Action(name='Step Heat',
##                       path='MenuBar/Lasers/Scans',
##                       class_name='src.lasers.plugins.laser_actions:StepHeatAction'
##                       ),
#                Action(name='Power Scan',
#                       path='MenuBar/Lasers/Scans',
#                       class_name='src.lasers.plugins.laser_actions:PowerScanAction'
#                       ),
##                Action(name='Loading Position',
##                       path='MenuBar/Lasers/{}'.format(self.name),
##                       class_name='src.lasers.plugins.laser_actions:MoveLoadPositionAction'
##                       ),
#                Action(name='Open Power Scan',
#                       path='MenuBar/Lasers/{}/Results'.format(self.name),
#                       class_name='src.lasers.plugins.laser_actions:OpenPowerScanGraphAction'
#                       ),




             ]
#============= EOF ====================================
