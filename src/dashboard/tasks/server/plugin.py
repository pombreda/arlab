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
from envisage.ui.tasks.task_factory import TaskFactory
from traits.api import Instance

#============= standard library imports ========================
#============= local library imports  ==========================
from src.dashboard.tasks.server.server import DashboardServer
from src.dashboard.tasks.server.task import DashboardServerTask
from src.envisage.tasks.base_task_plugin import BaseTaskPlugin


class DashboardServerPlugin(BaseTaskPlugin):
    dashboard_server = Instance(DashboardServer)

    def _tasks_default(self):
        return [TaskFactory(id='pychron.dashboard.server',
                            name='Dashboard Server',
                            accelerator='Ctrl+4',
                            factory=self._factory)]

    def _factory(self):
        f = DashboardServerTask(server=self.dashboard_server)
        return f

    def start(self):
        self.dashboard_server = DashboardServer(application=self.application)
        s = self.dashboard_server
        s.activate()

#============= EOF =============================================