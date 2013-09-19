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
from traits.api import Instance, HasTraits, Any, Enum
from pyface.tasks.action.schema import SToolBar, SGroup
# from pyface.action.action import Action
# from pyface.tasks.action.task_action import TaskAction
# from pyface.tasks.task_layout import TaskLayout, PaneItem
# from pyface.timer.do_later import do_later
import time
import subprocess
# from pyface.tasks.action.schema import SToolBar
#============= standard library imports ========================
#============= local library imports  ==========================
from src.processing.tasks.tables.table_actions import  ToggleStatusAction, \
    SummaryTableAction, AppendSummaryTableAction, MakeTableAction, \
    AppendLaserTableAction
# from src.processing.tasks.analysis_edit.analysis_edit_task import AnalysisEditTask
from src.processing.tasks.browser.panes import BrowserPane
from src.processing.tasks.tables.panes import TableEditorPane
from src.processing.tasks.browser.browser_task import BrowserTask
from src.processing.tasks.tables.editors.laser_table_editor import LaserTableEditor
from src.processing.tasks.tables.table_task_editor import TableTaskEditor
from src.processing.tasks.tables.editors.adapters import TableBlank, \
    TableSeparator
from src.processing.tasks.tables.editors.summary_table_editor import SummaryTableEditor


from traits.api import Str, Float, List
from pyface.timer.do_later import do_later
from src.processing.analysis_means import Mean
from traits.has_traits import on_trait_change
from envisage.ui.action.group import Group

class Summary(Mean):
    sample = Str
    material = Str
#     age = Float
#     age_error = Float
    irradiation = Str
    age_type = Str

class StepHeatingSummary(Summary):
    age_type = Str('Plateau')
    age_types = List(['Plateau', 'Isochron', 'Integrated'])

class FusionSummary(Summary):
    age_type = Str('Weighted Mean')
    age_types = List(['Weighted Mean', ])


class TableTask(BrowserTask):
    name = 'Tables'

    tool_bars = [
                 SToolBar(
                          MakeTableAction(),
                          SGroup(
                                ToggleStatusAction(),
                                SummaryTableAction(),
                                AppendSummaryTableAction()
                                ),
                          SGroup(
                                AppendLaserTableAction()
                                ),


                          image_size=(16, 16)
                          ),
                 ]

    editor = Instance(TableTaskEditor, ())

    def activated(self):
        editor = LaserTableEditor()
        self._open_editor(editor)
        self.load_projects()

        self.selected_project = self.projects[1]
#         self._dclicked_sample_changed('')

#         super(TableTask, self).activated()
#         self.make_laser_table()
    def _dclicked_sample_changed(self, new):
        self._append_laser_table()
#         man = self.manager
#         ans = [ai for ai in self.analyses
# #                 if not ai.step
#                 ]  # [:5]
# #         self.manager.make
#         ans = man.make_analyses(ans)
#         aa = [r for ai in ans
#                 for r in (ai, TableBlank(analysis=(ai)))]
#
#         self.active_editor.oitems = aa
#         self.active_editor.items = aa
#         self.active_editor.refresh_blanks()

        self.active_editor.name = self.selected_sample[0].name

#===============================================================================
# task actions
#===============================================================================

    def make_table(self):
        ae = self.active_editor
        ae.use_alternating_background = self.editor.use_alternating_background
        ae.notes_template = self.editor.notes_template

        title = self.editor.make_title()

        p = ae.make_table(title)
        self.view_pdf(p)

    def toggle_status(self):
        ae = self.active_editor
        if ae and ae.selected:
            for s in ae.selected:
                s.temp_status = int(not s.temp_status)

    def append_summary_table(self):
        if isinstance(self.active_editor, SummaryTableEditor):
#             do_later(self._append_summary_table)
            self._append_summary_table()

    def append_laser_table(self):
        if isinstance(self.active_editor, LaserTableEditor):
#             do_later(self._append_summary_table)
            self._append_laser_table()

    def open_summary_table(self):
        do_later(self._open_summary_table)

    def _append_laser_table(self):

        for sa in self.selected_sample:
            sam = next((si
                        for si in self.active_editor.items
                            if si.sample == sa.name), None)
            if sam is None:
                man = self.manager
                ans = self._get_sample_analyses(sa)
                ans = man.make_analyses(ans)

                aa = ans
#                 aa = [r for ai in ans
#                         for r in (ai, TableBlank(analysis=(ai)))]

                if self.active_editor.oitems:
                    aa.insert(0, TableSeparator())

                self.active_editor.oitems.extend(aa)
                self.active_editor.items.extend(aa)

#         self.active_editor.refresh_blanks()

    def _append_summary_table(self):
        ss = self.active_editor.items
        items = self._make_summary_table(ss)
        self.active_editor.items.extend(items)


    def _open_summary_table(self):
        items = self._make_summary_table()
        uab = self.editor.use_alternating_background
        editor = SummaryTableEditor(items=items,
                                    name='Summary',
                                    use_alternating_background=uab
                                    )
        self._open_editor(editor)

    def _make_summary_table(self, pitems=None):
        def factory(s):
            sam = s.name
            mat = ''
            if s.material:
                mat = s.material

            ans = self._get_sample_analyses(s)
#             ans = [ai for ai in ans if ai.step == ''][:5]
#             ans = [ai for ai in ans][:5]
#            ans = self.manager.make_analyses(ans[:4])
            ans = self.manager.make_analyses(ans)

            ref = ans[0]
            irrad_str = ref.irradiation_str

            klass = StepHeatingSummary if ref.step else FusionSummary
            ss = klass(
                       sample=sam,
                       material=mat,
                       irradiation=irrad_str,
                       analyses=ans
                       )
            return ss

        if pitems is None:
            pitems = []

        def test(si):
            return next((ss for ss in pitems if ss.sample == si.name), None)

        items = [factory(si)
                    for si in self.selected_sample
                        if not test(si)]

#         ans = [ai for si in items
#                     for ai in si.analyses]

#         self.manager.load_analyses(ans)
        return items


    def create_dock_panes(self):
        return [
                BrowserPane(model=self),
                TableEditorPane(model=self.editor)
                ]



#===============================================================================
# handlers
#===============================================================================
    @on_trait_change('editor:age_type')
    def _edit_handler(self, obj, name, old, new):
        ae = self.active_editor
        if isinstance(ae, SummaryTableEditor):
            if ae.selected:
                for si in ae.selected:
                    si.age_type = new

                ae.refresh_needed = True

    @on_trait_change('active_editor:selected')
    def _update_selected(self, new):
        if new:
            ref = new[0]
            if hasattr(ref, 'age_types'):
                self.editor.age_types = ref.age_types


#============= EOF =============================================
