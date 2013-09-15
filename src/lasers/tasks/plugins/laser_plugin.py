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
from traits.api import List, Str
from src.envisage.tasks.base_task_plugin import BaseTaskPlugin
from envisage.ui.tasks.task_factory import TaskFactory
from src.lasers.tasks.laser_task import FusionsDiodeTask, FusionsCO2Task
from src.lasers.laser_managers.ilaser_manager import ILaserManager
from src.helpers.parsers.initialization_parser import InitializationParser
import os
from src.paths import paths
from src.lasers.tasks.laser_preferences import FusionsDiodePreferencesPane, \
    FusionsCO2PreferencesPane
from pyface.tasks.action.schema_addition import SchemaAddition
from envisage.ui.tasks.task_extension import TaskExtension
from src.lasers.tasks.laser_actions import OpenScannerAction, \
    OpenAutoTunerAction, PowerMapAction, PowerCalibrationAction, \
    OpenPowerMapAction, TestDegasAction
from pyface.tasks.action.schema import SMenu, GroupSchema, MenuSchema
from pyface.action.group import Group
from src.lasers.tasks.laser_calibration_task import LaserCalibrationTask
#============= standard library imports ========================
#============= local library imports  ==========================

class CoreLaserPlugin(BaseTaskPlugin):
    def _my_task_extensions_default(self):
        actions = [
                   SchemaAddition(factory=OpenPowerMapAction,
                                  path='MenuBar/File/Open'
                                ),
#                    SchemaAddition(id='calibration',
#                                   factory=lambda: Group(
#                                                          PowerMapAction(),
#                                                          PowerCalibrationAction(),
#                                                          ),
#                                    path='MenuBar/Extraction'
#                                    ),
#                     SchemaAddition(
#                                    factory=TestDegasAction,
#                                    path='MenuBar/Extraction'
#                                    )
                   ]
        return [TaskExtension(actions=actions),

                ]


class BaseLaserPlugin(BaseTaskPlugin):
    MANAGERS = 'pychron.hardware.managers'

    klass = None
    name = None

    def _service_offers_default(self):
        '''
        '''
        if self.klass is None:
            raise NotImplementedError

        so = self.service_offer_factory(
                          protocol=ILaserManager,
                          factory=self._manager_factory)
        return [so]

    def _manager_factory(self):
        '''
        '''

        ip = InitializationParser()
        plugin = ip.get_plugin(self.klass[1].replace('Manager', ''), category='hardware')
        mode = ip.get_parameter(plugin, 'mode')

        if mode == 'client':
            klass = ip.get_parameter(plugin, 'klass')
            if klass is None:
                klass = 'PychronLaserManager'

            pkg = 'src.lasers.laser_managers.pychron_laser_manager'
            try:
                tag = ip.get_parameter(plugin, 'communications', element=True)
#                tag = plugin.find('communications')
                params = dict()
                for attr in ['host', 'port', 'kind']:
                    try:
                        params[attr] = tag.find(attr).text.strip()
                    except Exception, e:
                        print 'client comms fail', attr, e
            except Exception, e:
                print 'client comms fail', e

            params['name'] = self.name
            factory = __import__(pkg, fromlist=[klass])
            m = getattr(factory, klass)(**params)
        else:
            factory = __import__(self.klass[0], fromlist=[self.klass[1]])
            m = getattr(factory, self.klass[1])()

        m.bootstrap()
        m.plugin_id = self.id
        m.bind_preferences(self.id)

        return m

    managers = List(contributes_to=MANAGERS)
    def _managers_default(self):
        '''
        '''
        d = []

        if self.klass is not None:
            d = [dict(name=self.name,
                     manager=self._get_manager())]

        return d

    def _get_manager(self):

        return self.application.get_service(ILaserManager, 'name=="{}"'.format(self.name))

    def _preferences_default(self):
        root = paths.preferences_dir
        path = os.path.join(root, 'preferences.ini')
        if not os.path.isfile(path):
            with open(path, 'w'):
                pass
        return ['file://{}'.format(path)]

class FusionsPlugin(BaseLaserPlugin):
    task_name = Str

    def _tasks_default(self):
        return [TaskFactory(id=self.id,
                            task_group='hardware',
                            factory=self._task_factory,
                            name=self.task_name,
#                             accelerator='Ctrl+l'
                            accelerator=self.accelerator
                            ),
                TaskFactory(id='pychron.laser.calibration',
                            task_group='hardware',
                            factory=self._calibration_task_factory,
                            name='Laser Calibration',
                            accelerator='Ctrl+2'
                            ),
                ]

    def _calibration_task_factory(self):
        t = LaserCalibrationTask(manager=self._get_manager())
        return t

    sources = List(contributes_to='pychron.video.sources')
    def _sources_default(self):
        ip = InitializationParser()
        plugin = ip.get_plugin(self.task_name.replace(' ', ''),
                               category='hardware')
        source = ip.get_parameter(plugin, 'video_source')
        rs = []
        if source:
            rs = [(source, self.task_name)]
        return rs

    def _my_task_extensions_default(self):
#     def _get_task_extensions(self):
        def efactory():
            return SMenu(id='Laser', name='Laser')
        return [TaskExtension(actions=[
                   SchemaAddition(id='Laser',
                                  factory=efactory,
                                  path='MenuBar',
                                  before='Tools',
                                  after='View'
                                  ),
#                    SchemaAddition(id='fusions_laser_group',
#                                  factory=lambda: GroupSchema(id='FusionsLaserGroup'
#                                                        ),
#                                  path='MenuBar/Extraction'
#                                  ),
#                    SchemaAddition(id='pattern',
#                                   factory=lambda:Group(
#                                                        OpenPatternAction(),
#                                                        NewPatternAction(),
#                                                        ),
#                                   path='MenuBar/Extraction'
#                                   ),
#                     SchemaAddition(id='calibration',
#                                    factory=lambda: Group(
#                                                          PowerMapAction(),
#                                                          PowerCalibrationAction(),
#                                                          ),
#                                    path='MenuBar/Extraction'
#                                    ),
#                     SchemaAddition(
#                                    factory=OpenPowerMapAction,
#                                    path='MenuBar/File/Open'
#                                    ),
#                     SchemaAddition(
#                                    factory=TestDegasAction,
#                                    path='MenuBar/Extraction'
#                                    ),
                              ]
                            )
                       ]





#============= EOF =============================================
