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
from envisage.ui.tasks.task_extension import TaskExtension
from pyface.tasks.action.schema_addition import SchemaAddition
#============= standard library imports ========================
#============= local library imports  ==========================
from src.database.tasks.actions import UpdateDatabaseAction
from src.envisage.tasks.base_task_plugin import BaseTaskPlugin
from src.database.tasks.connection_preferences import ConnectionPreferencesPane, MassSpecConnectionPane
from src.database.isotope_database_manager import IsotopeDatabaseManager


class DatabasePlugin(BaseTaskPlugin):
    def _preferences_panes_default(self):
        return [
            ConnectionPreferencesPane,
            MassSpecConnectionPane]

    def _service_offers_default(self):
        so = self.service_offer_factory(
            protocol=IsotopeDatabaseManager,
            factory=IsotopeDatabaseManager
        )
        return [so, ]

    def _my_task_extensions_default(self):
        return [TaskExtension(actions=[SchemaAddition(id='update_database',
                                                      factory=UpdateDatabaseAction,
                                                      path='MenuBar/Tools')])]

    def start(self):
        iso = IsotopeDatabaseManager()
        iso.populate_default_tables()

#============= EOF =============================================
