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
from traits.api import HasTraits
from traitsui.api import View, Item
from src.processing.tasks.analysis_edit.analysis_edit_task import AnalysisEditTask
from src.processing.tasks.figures.figure_editor import FigureEditor
from pyface.tasks.task_layout import TaskLayout, Splitter, PaneItem
#============= standard library imports ========================
#============= local library imports  ==========================

class FigureTask(AnalysisEditTask):
    id = 'pychron.processing.figures'
    def _default_layout_default(self):
        return TaskLayout(
                          id='pychron.analysis_edit',
                          left=Splitter(
                                     PaneItem('pychron.analysis_edit.unknowns'),
                                     PaneItem('pychron.analysis_edit.controls'),
                                     orientation='vertical'
                                     ),
                          right=Splitter(
                                         PaneItem('pychron.search.query'),
                                         PaneItem('pychron.search.results'),
                                         orientation='vertical'
                                         )
                          )

    def new_ideogram(self, ans, name='Ideo'):
        self.unknowns_pane.items = ans
        comp = self.manager.new_ideogram(ans=ans)
        editor = FigureEditor(component=comp,
                              name=name)
        self._open_editor(editor)

#============= EOF =============================================
