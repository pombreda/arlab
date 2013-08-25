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
from traits.api import HasTraits, List, Str, Property, Any, cached_property
from traitsui.api import View, Item
from src.envisage.tasks.editor_task import EditorTask, BaseEditorTask
from src.processing.tasks.browser.panes import BrowserPane
from pyface.tasks.task_layout import TaskLayout, PaneItem
from src.processing.tasks.recall.recall_editor import RecallEditor
from src.experiment.utilities.identifier import make_runid, strip_runid
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.action.task_action import TaskAction
from src.paths import paths
from pyface.image_resource import ImageResource
#============= standard library imports ========================
#============= local library imports  ==========================
'''
add toolbar action to open another editor tab


'''
class NewBrowserEditorAction(TaskAction):
    method = 'new_editor'
    image = ImageResource(name='add.png',
                         search_path=[paths.resources,
                                      paths.app_resources
                                      ]
                         )

class BrowserTask(BaseEditorTask):
    projects = List
    oprojects = List

    samples = List  # Property(depends_on='selected_project')
    osamples = List

    analyses = List  # Property(depends_on='selected_sample')
    oanalyses = List

    project_filter = Str
    sample_filter = Str
    analysis_filter = Str

    selected_project = Any
    selected_sample = Any
    selected_analysis = Any


    tool_bars = [SToolBar(NewBrowserEditorAction(),
                          image_size=(16, 16)
                          )]

    def activated(self):
        editor = RecallEditor()
        self._open_editor(editor)

        ps = self.manager.db.get_projects()
        self.projects = [p.name for p in ps]
        self.oprojects = [p.name for p in ps]

    def new_editor(self):
        editor = RecallEditor()
        self._open_editor(editor)

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem('pychron.browswer'))

    def _selected_analysis_changed(self):
        if self.selected_analysis:
            s = self.selected_analysis
            l, a, s = strip_runid(s)
            an = self.manager.db.get_unique_analysis(l, a, s)
            an = self.manager.make_analyses([an])[0]
            an.load_isotopes(refit=False)
            self.active_editor.analysis_summary = an.analysis_summary

#     @cached_property
#     def _get_samples(self):
#         samples = []
#         if self.selected_project:
#             samples = self.manager.db.get_samples(project=self.selected_project)
#         return [s.name for s in samples]

#     @cached_property
#     def _get_analyses(self):
#         ans = []
#         if self.selected_sample:
#             sample = self.manager.db.get_sample(self.selected_sample,
#                                                 project=self.selected_project
#                                                 )
#             ans = [make_runid(ln.identifier,
#                               a.aliquot, a.step) for ln in sample.labnumbers
#                             for a in ln.analyses]
# #             ans = self.manager.db.get_analyses(sample=self.s)
#         return ans

    def create_dock_panes(self):
        return [BrowserPane(model=self)]

#===============================================================================
# handlers
#===============================================================================
    def _selected_project_changed(self, new):
        if new:
            samples = self.manager.db.get_samples(project=new)
            ss = [s.name for s in samples]
            self.samples = ss
            self.osamples = ss
#             self.analyses = []
#             self.onalyses = []
            if ss:
                self.selected_sample = ss[0]

    def _selected_sample_changed(self, new):
        if new:
            sample = self.manager.db.get_sample(self.selected_sample,
                                                project=self.selected_project
                                                )
            ans = [make_runid(ln.identifier,
                              a.aliquot, a.step) for ln in sample.labnumbers
                            for a in ln.analyses]
            self.analyses = ans
            self.oanalyses = ans
            if ans:
                self.selected_analysis = ans[0]

    def _filter_func(self, new):
        def func(x):
            return x.lower().startswith(new.lower())
        return func

    def _project_filter_changed(self, new):
        self.projects = filter(self._filter_func(new), self.oprojects)

    def _sample_filter_changed(self, new):
        self.samples = filter(self._filter_func(new), self.osamples)

    def _analysis_filter_changed(self, new):
        self.analyses = filter(self._filter_func(new), self.oanalyses)

#============= EOF =============================================
