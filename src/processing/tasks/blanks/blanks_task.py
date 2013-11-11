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
# from traits.api import HasTraits
from pyface.tasks.task_layout import TaskLayout, PaneItem, HSplitter, Tabbed

from src.processing.tasks.analysis_edit.interpolation_task import InterpolationTask
#============= standard library imports ========================
#============= local library imports  ==========================


class BlanksTask(InterpolationTask):
    id = 'pychron.analysis_edit.blanks'
    blank_editor_count = 1
    name = 'Blanks'
    default_reference_analysis_type = 'blank_unknown'

    def _default_layout_default(self):
        return TaskLayout(
            id='pychron.analysis_edit.blanks',
            left=HSplitter(
                Tabbed(
                    PaneItem('pychron.browser'),
                    PaneItem('pychron.search.query'),
                ),
                Tabbed(
                    PaneItem('pychron.analysis_edit.unknowns'),
                    PaneItem('pychron.analysis_edit.references'),
                    PaneItem('pychron.analysis_edit.controls')
                ),
            ),
        )

    def new_blank(self):
        from src.processing.tasks.blanks.blanks_editor import BlanksEditor

        editor = BlanksEditor(name='Blanks {:03n}'.format(self.blank_editor_count),
                              processor=self.manager,
                              task=self,
                              default_reference_analysis_type=self.default_reference_analysis_type)

        self._open_editor(editor)
        self.blank_editor_count += 1

    def _set_selected_analysis(self, new):
        if not new:
            return
        self._load_references(new)

    def do_easy_blanks(self):
        self._do_easy(self._easy_blanks)

    def _easy_blanks(self, db, ep):
        doc = ep.doc('blanks')
        fits = doc['blank_fit_isotopes']
        projects = doc['projects']

        ans = [ai for proj in projects
               for si in db.get_samples(project=proj)
               for ln in si.labnumbers
               for ai in ln.analyses]

        prog = self.manager.open_progress(len(ans) + 1)
        #bin analyses
        for ais in self._bin_analyses(ans):
            for ai in ais:
                l, a, s = ai.labnumber.identifier, ai.aliquot, ai.step
                prog.change_message('Save preceeding blank for {}-{:02n}{}'.format(l, a, s))
                hist = db.add_history(ai, 'blanks')

                ai.selected_histories.selected_blanks = hist

                for fi in fits:
                    if fi['fit'] == 'preceeding':
                        self._preceeding_correct(db, fi, ai, hist)
                    else:
                        pass

        prog.increment()

    def _preceeding_correct(self, db, fi, ai, hist):
        pa = db.get_preceeding(ai.analysis_timestamp,
                               ai.measurement.mass_spectrometer.name)
        if pa:
            an_pa = self.manager.make_analysis(pa)
            iso = fi['name']
            if iso in an_pa.isotopes:
                blank = an_pa.isotopes[iso].get_corrected_value()
                dbblank = db.add_blanks(hist,
                                        isotope=iso,
                                        user_value=float(blank.nominal_value),
                                        user_error=float(blank.std_dev),
                                        fit='preceeding')

                db.add_blanks_set(dbblank, pa)

            else:
                self.warning('{} does not have iso {}'.format(an_pa.record_id, iso))

        else:
            self.warning('No preceeding analyses for {}-{:02n}{}'.format(ai.labnumber.identifier,
                                                                         ai.aliquot, ai.step))

    def _bin_analyses(self, ans):
        ans = iter(sorted(ans, key=lambda x: x.analysis_timestamp))

        def _bin():
            ai = ans.next()
            pt = ai.analysis_timestamp
            g = [ai]
            tol = 60 * 60
            cnt = 0
            while 1:
                try:
                    ai = ans.next()
                    dev = ai.analysis_timestamp - pt
                    pt = ai.analysis_timestamp
                    if dev.total_seconds() > tol:
                        yield g
                        g = [ai]
                    else:
                        g.append(ai)

                except StopIteration:
                    break

            yield g

        return _bin()


#============= EOF =============================================
