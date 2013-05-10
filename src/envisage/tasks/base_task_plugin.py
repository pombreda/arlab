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
from traits.api import HasTraits, List
from envisage.plugin import Plugin
from envisage.service_offer import ServiceOffer
# from pyface.tasks.action.schema_addition import SchemaAddition
# from src.envisage.tasks.base_task import myTaskWindowLaunchGroup
# from envisage.ui.tasks.task_extension import TaskExtension
#============= standard library imports ========================
#============= local library imports  ==========================

class BaseTaskPlugin(Plugin):
    SERVICE_OFFERS = 'envisage.service_offers'
    TASK_EXTENSIONS = 'envisage.ui.tasks.task_extensions'
    TASKS = 'envisage.ui.tasks.tasks'

    tasks = List(contributes_to=TASKS)
    service_offers = List(contributes_to=SERVICE_OFFERS)
    my_task_extensions = List(contributes_to=TASK_EXTENSIONS)

    preferences = List(contributes_to='envisage.preferences')
    preferences_panes = List(
        contributes_to='envisage.ui.tasks.preferences_panes')

    managers = List(contributes_to='pychron.hardware.managers')

    def _preferences_panes_default(self):
        return []

    def _preferences_default(self):
        return []

    def service_offer_factory(self, **kw):
        '''
        
        '''
        return ServiceOffer(**kw)

    def check(self):
        return True
    
    
#============= EOF =============================================
