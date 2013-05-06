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
# from envisage.ui.workbench.workbench_plugin import WorkbenchPlugin
from envisage.core_plugin import CorePlugin
from envisage.ui.tasks.tasks_plugin import TasksPlugin
#============= standard library imports ========================
import os
#============= local library imports  ==========================
# from src.bakeout.plugins.bakedpy_plugin import BakedpyPlugin
# from src.bakeout.plugins.bakedpy_ui_plugin import BakedpyUIPlugin
# from src.envisage.bakedpy_application import Bakedpy
from src.bakeout.tasks.bakeout_plugin import BakeoutPlugin

from src.helpers.logger_setup import new_logger
from src.bakeout.bakedpy_application import Bakedpy

def launch():
    logger = new_logger('launcher')
    plugins = [
               CorePlugin(),
#               WorkbenchPlugin(),
               TasksPlugin(),
               BakeoutPlugin(),
#               BakedpyUIPlugin()
               ]
    app = Bakedpy(plugins=plugins)

    app.run()

    logger.info('Quitting Bakedpy')
    app.exit()

    # force a clean exit
    os._exit(0)


#============= EOF =============================================
