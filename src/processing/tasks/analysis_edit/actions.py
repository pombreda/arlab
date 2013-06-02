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
from traits.api import HasTraits, Str
from traitsui.api import View, Item
from pyface.tasks.action.task_action import TaskAction
from pyface.tasks.task_window_layout import TaskWindowLayout
#============= standard library imports ========================
#============= local library imports  ==========================
class AnalysisEditAction(TaskAction):
    task_id = 'pychron.analysis_edit'
    def _create_window(self, app):
        win = None
        # search other windows
        _id = self.task_id
        for win in app.windows:
            if win.active_task.id == _id:
                win.activate()
                break
        else:
            win = app.create_window(TaskWindowLayout(_id))

        return win

    def perform(self, event):
        app = event.task.window.application
        task = self.task
        _id = self.task_id
        if not task.id == _id:
            win = self._create_window(app)
            win.open()
            task = win.active_task
        else:
            win = self._create_window(app)
            win.open()
            task = win.active_task

        self.task = task

        super(AnalysisEditAction, self).perform(event)

class FluxAction(AnalysisEditAction):
    name = 'Flux...'
    accelerator = 'Ctrl+g'
    method = 'new_flux'
    task_id = 'pychron.analysis_edit.flux'

class BlankEditAction(AnalysisEditAction):
    name = 'Blanks...'
    accelerator = 'Ctrl+B'
    method = 'new_blank'
    task_id = 'pychron.analysis_edit.blanks'


class SeriesAction(AnalysisEditAction):
    name = 'Series...'
    accelerator = 'Ctrl+L'
    method = 'new_series'
    task_id = 'pychron.analysis_edit.series'

class IsotopeEvolutionAction(AnalysisEditAction):
    name = 'Isotope Evolution...'
    accelerator = 'Ctrl+k'
    method = 'new_isotope_evolution'
    task_id = 'pychron.analysis_edit.isotope_evolution'

class RefitIsotopeEvolutionAction(AnalysisEditAction):
    name = 'Refit Isotope Evolution...'
    accelerator = 'Ctrl+Shift+f'
    method = 'refit_isotopes'
    task_id = 'pychron.analysis_edit.isotope_evolution'

class ICFactorAction(AnalysisEditAction):
    name = 'IC Factor...'
    accelerator = 'Ctrl+i'
    method = 'new_ic_factor'
    task_id = 'pychron.analysis_edit.ic_factor'

class BatchEditAction(AnalysisEditAction):
    name = 'Batch Edit...'
    accelerator = 'Ctrl+Shift+e'
    method = 'new_batch'
    task_id = 'pychron.analysis_edit.batch'

class SCLFTableAction(AnalysisEditAction):
    name = 'SCLF Table...'
    accelerator = 'Ctrl+t'
    method = 'new_sclf_table'
    task_id = 'pychron.processing.publisher'

#============= EOF =============================================
