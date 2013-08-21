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
from traits.api import Str
from pyface.action.action import Action
from pyface.tasks.task_window_layout import TaskWindowLayout
from pyface.tasks.action.task_action import TaskAction

#============= standard library imports ========================
#============= local library imports  ==========================
# class ProcessorAction(Action):
#     def _get_processor(self, event):
#         app = event.task.window.application
#         processor = app.get_service('src.processing.processor.Processor')
#         return processor


#===============================================================================
# grouping
#===============================================================================
class GroupAction(TaskAction):

    def _task_changed(self):
        if self.task:
            if self.task.id in ('pychron.processing.figures',):
                enabled = True
                if self.enabled_name:
                    if self.object:
                        enabled = bool(self._get_attr(self.object,
                                                   self.enabled_name, False))
                if enabled:
                    self._enabled = True
            else:
                self._enabled = False

    def _enabled_update(self):
        '''
             reimplement ListeningAction's _enabled_update
        '''
        if self.enabled_name:
            if self.object:
                self.enabled = bool(self._get_attr(self.object,
                                                   self.enabled_name, False))
            else:
                self.enabled = False
        elif self._enabled is not None:
            self.enabled = self._enabled
        else:
            self.enabled = bool(self.object)

class GroupSelectedAction(GroupAction):
    name = 'Group Selected'
    method = 'group_selected'
#     def perform(self, event):
#         task = event.task
#         if task.id == 'pychron.processing.figures':
#             task.group_selected()

class GroupbySampleAction(GroupAction):
    name = 'Group by Sample'
    method = 'group_by_sample'

class GroupbyLabnumberAction(GroupAction):
    name = 'Group by Labnumber'
    method = 'group_by_labnumber'

class GroupbyAliquotAction(GroupAction):
    name = 'Group by Aliquot'
    method = 'group_by_aliquot'

class ClearGroupAction(GroupAction):
    name = 'Clear Grouping'
    method = 'clear_grouping'


#===============================================================================
#
#===============================================================================
class EquilibrationInspectorAction(Action):
    name = 'Equilibration Inspector...'
    def perform(self, event):
        from src.processing.utils.equil import EquilibrationInspector

        eq = EquilibrationInspector()
        eq.refresh()
        app = event.task.window.application
        app.open_view(eq)


#===============================================================================
# figures
#===============================================================================
class FigureAction(Action):
    method = Str
    def perform(self, event):
        app = event.task.window.application
        task = app.get_task('pychron.processing.figures')
#         task = event.task
#         if not task.id == 'pychron.processing.figures':
#             app = task.window.application
#             win = app.create_window(TaskWindowLayout(
#                                                'pychron.processing.figures'
#                                                )
#                               )
#             win.open()
#             task = win.active_task

        if hasattr(task, self.method):
            getattr(task, self.method)()
#         task.new_ideogram()

class IdeogramAction(FigureAction):
    name = 'Ideogram'
    accelerator = 'Ctrl+J'
    method = 'new_ideogram'

class SpectrumAction(FigureAction):
    name = 'Spectrum'
    accelerator = 'Ctrl+D'
    method = 'new_spectrum'
#     def perform(self, event):
#
#         task = event.task
#         if not task.id == 'pychron.processing.figures':
#             app = task.window.application
#             win = app.create_window(TaskWindowLayout(
#                                                'pychron.processing.figures'
#                                                )
#                               )
#             win.open()
#             task = win.active_task
#
#         task.new_spectrum()


class InverseIsochronAction(FigureAction):
    name = 'Inverse Isochron'
    method = 'new_inverse_isochron'
    accelerator = 'Ctrl+i'
#===============================================================================
#
#===============================================================================
class RecallAction(Action):
    name = 'Recall'
    accelerator = 'Ctrl+R'
    def perform(self, event):
        app = event.task.window.application
        app.get_task('pychron.recall')
#         task = event.task
#         if not task.id == 'pychron.recall':
#             app = task.window.application
#             win = app.create_window(TaskWindowLayout(
#                                                'pychron.recall'
#                                                )
#                               )
#             win.open()
#             task = win.active_task
#         else:
#             task.window.activate()


class LabnumberEntryAction(Action):
    name = 'Labnumber Entry'
    accelerator = 'Ctrl+Shift+l'

    task_id = 'pychron.labnumber_entry'

    def perform(self, event):
        pid = 'pychron.entry'
        app = event.task.window.application
        app.get_task(pid)

#         task = event.task
#         if not task.id == 'pychron.entry':
#             app = task.window.application
#             win = app.create_window(TaskWindowLayout(
#                                                'pychron.entry'
#                                                )
#                               )
#             win.open()
#         else:
#             task.window.activate()


class SmartProjectAction(Action):
    name = 'Smart Project'
    accelerator = 'Ctrl+P'
    def perform(self, event):
        app = event.task.window.application
        app.get_task('pychron.processing.smart_project')

#============= EOF =============================================
