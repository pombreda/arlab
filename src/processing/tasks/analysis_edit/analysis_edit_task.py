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
from traits.api import Instance, on_trait_change, List
from src.processing.tasks.analysis_edit.actions import DatabaseSaveAction, FindAssociatedAction
from src.processing.tasks.analysis_edit.panes import UnknownsPane, ControlsPane, \
    TablePane
from src.processing.tasks.browser.browser_task import BaseBrowserTask
from src.processing.tasks.recall.recall_editor import RecallEditor
from src.processing.tasks.search_panes import QueryPane
from src.processing.tasks.analysis_edit.adapters import UnknownsAdapter
# from pyface.tasks.task_window_layout import TaskWindowLayout
from src.database.records.isotope_record import IsotopeRecordView
from src.processing.tasks.analysis_edit.plot_editor_pane import PlotEditorPane
from src.processing.analyses.analysis import Analysis
from src.processing.selection.data_selector import DataSelector

#============= standard library imports ========================
#============= local library imports  ==========================

class AnalysisEditTask(BaseBrowserTask):
    id = 'pychron.analysis_edit'
    unknowns_pane = Instance(TablePane)
    controls_pane = Instance(ControlsPane)
    #    results_pane = Instance(ResultsPane)
    plot_editor_pane = Instance(PlotEditorPane)
    unknowns_adapter = UnknownsAdapter
    unknowns_pane_klass = UnknownsPane

    data_selector = Instance(DataSelector)
    _analysis_cache = List

    ic_factor_editor_count = 0

    tool_bars = [SToolBar(DatabaseSaveAction(),
                          FindAssociatedAction(),
                          image_size=(16, 16))]

    external_recall_window = True

    def find_associated_analyses(self):
        self.information_dialog('Find associated not yey implemented')

    def recall(self, records):
        if not hasattr(records, '__iter__'):
            records = (records, )

        ans = self.manager.make_analyses(records, calculate_age=True)

        def func(rec):
        #             rec.load_isotopes()
            rec.calculate_age()
            reditor = RecallEditor(analysis_view=rec.analysis_view)
            self.editor_area.add_editor(reditor)

        #             self.add_iso_evo(reditor.name, rec)

        if ans:
            for ri in ans:
                func(ri)
                #             self.manager._load_analyses(ans, func=func)

            ed = self.editor_area.editors[-1]
            self.editor_area.activate_editor(ed)

    def new_ic_factor(self):
        from src.processing.tasks.detector_calibration.intercalibration_factor_editor import IntercalibrationFactorEditor

        editor = IntercalibrationFactorEditor(name='ICFactor {:03n}'.format(self.ic_factor_editor_count),
                                              processor=self.manager
        )
        self._open_editor(editor)
        self.ic_factor_editor_count += 1


    def save_as(self):
        self.save()

    def save(self):
        self.warning_dialog('Please use "Data -> Database Save" to save changes to the database')

    def save_to_db(self):
        db = self.manager.db
        with db.session_ctx():
            self._save_to_db()
        self.information_dialog('Changes saved to the database')

    def set_tag(self):
        """
            set tag for either
            analyses selected in unknowns pane
            or
            analyses selected in figure e.g temp_status!=0

        """

        tag = self._get_tagname()
        if tag:
            items = self.unknowns_pane.selected
            if not items:
                items = [i for i in self.unknowns_pane.items if i.temp_status != 0]

            if items:
                db = self.manager.db
                name = tag.name
                with db.session_ctx():
                    def func(ai, x):
                        self.debug('setting {} tag= {}'.format(ai.record_id, name))
                        x.tag = name

                        ai.set_tag(tag)

                    for it in items:
                        ma = db.get_analysis_uuid(it.uuid)
                        func(it, ma)

                self.unknowns_pane.refresh_needed = True
                self.active_editor.rebuild(refresh_data=False)
            else:
                self.warning_dialog('Not analyses selected to Tag')

    def prepare_destroy(self):
        if self.unknowns_pane:
            self.unknowns_pane.dump()

            #         if self.manager:
            #             self.manager.db.close()

    def create_dock_panes(self):

        self.unknowns_pane = self._create_unknowns_pane()

        #         self.controls_pane = ControlsPane()
        self.plot_editor_pane = PlotEditorPane()
        panes = [
            self.unknowns_pane,
            #                 self.controls_pane,
            self.plot_editor_pane,
            #                self.results_pane,
            self._create_browser_pane()
        ]
        cp = self._create_control_pane()
        if cp:
            self.controls_pane = cp
            panes.append(cp)

        ps = self._create_db_panes()
        if ps:
            panes.extend(ps)

        return panes

    def _create_control_pane(self):
        return ControlsPane()

    def _create_db_panes(self):
        if self.manager.db:
            if self.manager.db.connected:
                selector = self.manager.db.selector
                #selector._search_fired()

                #             from src.processing.selection.data_selector import DataSelector
                #             from src.processing.tasks.search_panes import ResultsPane

                ds = DataSelector(database_selector=selector)
                self.data_selector = ds
                #             return (QueryPane(model=ds), ResultsPane(model=ds))
                return QueryPane(model=ds),

    def _create_unknowns_pane(self):
        up = self.unknowns_pane_klass(adapter_klass=self.unknowns_adapter)
        up.load()
        return up

    def _get_tagname(self):
        print 'asdf'
        from src.processing.tasks.analysis_edit.tags import TagTableView

        db = self.manager.db
        with db.session_ctx():
            v = TagTableView()
            v.table.db = db
            v.table.load()

        info = v.edit_traits()
        if info.result:
            tag = v.selected
            return tag

    def _open_ideogram_editor(self, ans, name, task=None):
        _id = 'pychron.processing.figures'
        task = self._open_external_task(_id)
        task.new_ideogram(ans=ans, name=name)
        return task


    def _save_to_db(self):
        if self.active_editor:
            if hasattr(self.active_editor, 'save'):
                self.active_editor.save()

    #def _record_view_factory(self, pi, **kw):
    #    db = self.manager.db
    #    iso = IsotopeRecordView(**kw)
    #    dbrecord = db.get_analysis(pi.uuid, key='uuid')
    #    if iso.create(dbrecord):
    #        return iso

    def _set_previous_selection(self, pane, new):
        if new and new.name != 'Previous Selection':
            db = self.manager.db
            with db.session_ctx():
                lns = set([si.labnumber for si in new.analysis_ids])
                ids = [si.uuid for si in new.analysis_ids]
                if ids:
                    def f(t, t2):
                        return t2.identifier.in_(lns), t.uuid.in_(ids)

                    ans = db.get_analyses(uuid=f)
                    func = self._record_view_factory
                    ans = [func(si) for si in ans]

                    for ti in new.analysis_ids:
                        a = next((ai for ai in ans if ai.uuid == ti.uuid), None)
                        if a:
                            a.trait_set(group_id=ti.group_id, graph_id=ti.graph_id)

                    pane.items = ans

    def _save_file(self, path):
        if self.active_editor:
            self.active_editor.save_file(path)
            return True

            #===============================================================================
            # handlers
            #===============================================================================

    def _active_editor_changed(self):
        if self.active_editor:
            if self.controls_pane:
                tool = None
                if hasattr(self.active_editor, 'tool'):
                    tool = self.active_editor.tool

                self.controls_pane.tool = tool

            if self.unknowns_pane:
                self.unknowns_pane.previous_selection = self.unknowns_pane.previous_selections[0]
                if hasattr(self.active_editor, 'unknowns'):
                    if self.active_editor.unknowns:
                        self.unknowns_pane.items = self.active_editor.unknowns

    @on_trait_change('active_editor:component_changed')
    def _update_component(self):
        if self.plot_editor_pane:
            self.plot_editor_pane.component = self.active_editor.component

    @on_trait_change('unknowns_pane:[items, update_needed]')
    def _update_unknowns_runs(self, obj, name, old, new):
        if not obj._no_update:
            #print 'upadte unkownasdf pane', new,
            if self.active_editor:
                self.active_editor.unknowns = self.unknowns_pane.items
            if self.plot_editor_pane:
                self.plot_editor_pane.analyses = self.unknowns_pane.items
                #                self._append_cache(self.active_editor)

    @on_trait_change('plot_editor_pane:current_editor')
    def _update_current_plot_editor(self, new):
        if new:
            self._show_pane(self.plot_editor_pane)

            #    def _append_cache(self, editor):
            #        if hasattr(editor, 'unknowns'):
            #            ans = editor.unknowns
            #            ids = [ai.uuid for ai in self._analysis_cache]
            #            c = [ai for ai in ans if ai.uuid not in ids]
            #
            #            if c:
            #                self._analysis_cache.extend(c)
            #
            #        editor.analysis_cache = self._analysis_cache

    @on_trait_change('''unknowns_pane:dclicked, data_selector:selector:dclicked''')
    def _selected_changed(self, new):
        print new
        if new:
            print new.item
            if isinstance(new.item, (IsotopeRecordView, Analysis)):
                self._recall_item(new.item)
                #                self._open_external_recall_editor(new.item)

    #@on_trait_change('controls_pane:save_button')
    #def _save_fired(self):
    #    db = self.manager.db
    #    commit = not self.controls_pane.dry_run
    #    with db.session_ctx(commit=commit):
    #        self._save_to_db()
    #
    #    if commit:
    #        self.info('committing changes')
    #    else:
    #        self.info('dry run- not committing changes')

    @on_trait_change('[analysis_table, danalysis_table]:dclicked')
    def _dclicked_analysis_changed(self, obj, name, old, new):
        sel = obj.selected
        self._recall_item(sel)

    def _recall_item(self, item):
        if not self.external_recall_window:
            self.recall(item)
        else:
            self._open_external_recall_editor(item)

    def _open_external_recall_editor(self, sel):
        tid = 'pychron.recall'
        app = self.window.application

        win, task, is_open = app.get_open_task(tid)

        if is_open:
            win.activate()
        else:
            win.open()

        task.recall(sel)

        task.load_projects()

        #print self.selected_project, 'ffff'
        task.set_projects(self.oprojects, self.selected_project)
        task.set_samples(self.osamples, self.selected_sample)

    @on_trait_change('unknowns_pane:previous_selection')
    def _update_up_previous_selection(self, obj, name, old, new):
        self._set_previous_selection(obj, new)

    def _get_selected_analyses(self, unks=None):
        s = self.analysis_table.selected
        if not s:
            if self.selected_sample:
                iv = not self.analysis_table.omit_invalid

                uuids = []
                if unks:
                    uuids = [x.uuid for x in unks]

                def test(aa):
                    return not aa.uuid in uuids

                s = [ai for si in self.selected_sample
                     for ai in self._get_sample_analyses(si, include_invalid=iv)
                     if test(ai)]

            else:
                s = self.data_selector.selector.selected

        return s

    @on_trait_change('unknowns_pane:[append_button, replace_button]')
    def _append_unknowns(self, obj, name, old, new):

        is_append = name == 'append_button'

        if self.active_editor:
            unks = None
            if is_append:
                unks = self.active_editor.unknowns

            s = self._get_selected_analyses(unks)
            if s:
                if is_append:

                    unks = self.active_editor.unknowns
                    unks.extend(s)

                    #self.active_editor.unknowns=unks
                else:
                    self.active_editor.unknowns = s

                #print 'asd', len(self.active_editor.unknowns)
                #self.unknowns_pane.items=self.active_editor.unknowns
                self._add_unknowns_hook()

    def _add_unknowns_hook(self, *args, **kw):
        pass

    @on_trait_change('active_editor:unknowns')
    def _ac_unknowns_changed(self):
        self.unknowns_pane.items = self.active_editor.unknowns

    @on_trait_change('data_selector:selector:key_pressed')
    def _key_press(self, obj, name, old, new):
        '''
            use 'u' to add selected analyses to unknowns pane
        '''

        if new:
            s = self._get_selected_analyses()
            if s:

                c = new.text
                if c == 'u':
                    self.active_editor.unknowns.extend(s)
                elif c == 'U':
                    self.active_editor.unknowns = s
                else:
                    self._handle_key_pressed(c)

    def _handle_key_pressed(self, c):
        pass




        #===============================================================================

#
#===============================================================================
#    @on_trait_change('unknowns_pane:[+button]')
#    def _update_unknowns(self, name, new):
#        print name, new
#        '''
#            get selected analyses and append/replace to unknowns_pane.items
#        '''
#        sel = None
#        if sel:
#            if name == 'replace_button':
#                self.unknowns_pane.items = sel
#            else:
#                self.unknowns_pane.items.extend(sel)

#    @on_trait_change('references_pane:[+button]')
#    def _update_items(self, name, new):
#        print name, new
#        sel = None
#        if sel:
#            if name == 'replace_button':
#                self.references_pane.items = sel
#            else:
#                self.references_pane.items.extend(sel)


#============= EOF =============================================
