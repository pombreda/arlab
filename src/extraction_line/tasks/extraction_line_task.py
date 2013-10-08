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
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.task_layout import TaskLayout, PaneItem
from traits.api import Bool
# from pyface.tasks.action.schema import SMenu
# from src.extraction_line.tasks.extraction_line_actions import RefreshCanvasAction
#============= standard library imports ========================
#============= local library imports  ==========================
from src.extraction_line.tasks.extraction_line_actions import FinishChamberChangeAction, \
    EvacuateChamberAction, IsolateChamberAction
from src.extraction_line.tasks.extraction_line_pane import CanvasPane, GaugePane, \
    ExplanationPane
from src.envisage.tasks.base_task import BaseHardwareTask


class ExtractionLineTask(BaseHardwareTask):
    id = 'pychron.extraction_line'
    name = 'Extraction Line'

    def _tool_bars_default(self):
        tb = SToolBar(
            IsolateChamberAction(),
            EvacuateChamberAction(),
            FinishChamberChangeAction(),
            image_size=(16, 16)
        )
        return [tb, ]

    def _default_layout_default(self):
        return TaskLayout(
            top=PaneItem('pychron.extraction_line.gauges'),
            left=PaneItem('pychron.extraction_line.explanation')
        )

    def activated(self):
        self.manager.activate()

    def prepare_destroy(self):
        self.manager.deactivate()
        #         self.manager.closed(True)

    def create_central_pane(self):
        g = CanvasPane(model=self.manager)
        return g

    def create_dock_panes(self):
        panes = [GaugePane(model=self.manager),
                 ExplanationPane(model=self.manager)
        ]
        return panes

    #=======================================================================
    # toolbar actions
    #=======================================================================
    def isolate_chamber(self):
        self.manager.isolate_chamber()

    def evacuate_chamber(self):
        self.manager.evacuate_chamber()

    def finish_chamber_change(self):
        self.manager.finish_chamber_change()

#============= EOF =============================================
