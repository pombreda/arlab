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
from traits.api import HasTraits, Str, Instance, List, Property, \
    on_trait_change
from pyface.file_dialog import FileDialog
# from traitsui.api import View, Item
# from src.loggable import Loggable
#============= standard library imports ========================

#============= local library imports  ==========================
from src.experiment.isotope_database_manager import IsotopeDatabaseManager
from src.experiment.queue.experiment_queue import ExperimentQueue
from src.experiment.set_selector import SetSelector
from src.experiment.factory import ExperimentFactory
from src.constants import ALPHAS
from src.experiment.stats import StatsGroup
from src.experiment.executor import ExperimentExecutor
from src.paths import paths
from src.experiment.utilities.file_listener import FileListener
from src.experiment.experimentable import Experimentable


class Experimentor(Experimentable):
    experiment_factory = Instance(ExperimentFactory)
    experiment_queue = Instance(ExperimentQueue)
    executor = Instance(ExperimentExecutor)

    set_selector = Instance(SetSelector)
    stats = Instance(StatsGroup, ())



    title = Property(depends_on='experiment_queue')  # DelegatesTo('experiment_set', prefix='name')
    filelistener = None
    username = Str


    #===========================================================================
    # permissions
    #===========================================================================
    max_allowable_runs = 10000
    can_edit_scripts = True
    _last_ver_time = None
    _ver_timeout = 10

    def test_runs(self):
        for ei in self.experiment_queues:
            ei.test_runs()

    def test_connections(self):
        if not self.db:
            return

        if not self.db.connect():
            self.warning_dialog('Failed connecting to database. {}'.format(self.db.url))
            return

#        if not self.repository.connect():
#            self.warning_dialog('Failed connecting to repository {}'.format(self.repository.url))
#            return

        return True

    def load_experiment_queue(self, path=None, edit=True, saveable=False):

#        self.bind_preferences()
        # make sure we have a database connection
        if not self.test_connections():
            return

        if path is None:
            dlg = FileDialog(default_directory=paths.experiment_dir)
            if dlg.open():
                path = dlg.path
#            path = self.open_file_dialog(default_directory=paths.experiment_dir)

        if path is not None:

            self.experiment_queue = None
            self.experiment_queues = []
            # parse the file into individual experiment sets
            ts = self._parse_experiment_file(path)
            ws = []
            for text in ts:
                exp = self._experiment_queue_factory(path=path, add=False)

                exp._warned_labnumbers = ws
                if exp.load(text):
                    self.experiment_queues.append(exp)
#
#                    if edit:
#                        exp.automated_run = exp.automated_runs[-1].clone_traits()
#                        exp.set_script_names()
                ws = exp._warned_labnumbers

            self._update(all_info=True)
            self.test_runs()
            if self.experiment_queues:
                self.experiment_queue = self.experiment_queues[0]
                self.start_file_listener(self.experiment_queue.path)
#                def func():
#                self.set_selector.selected_index = -2
#                self.set_selector.selected_index = 0

#                do_later(func)
                self._load_experiment_queue_hook()
                self.save_enabled = True

                return True

    def start_file_listener(self, path):
        fl = FileListener(
                          path,
                          callback=self._reload_from_disk,
                          check=self._check_for_file_mods
                          )
        self.filelistener = fl

    def stop_file_listener(self):
        self.filelistener.stop()



#===============================================================================
# info update
#===============================================================================
    def _update(self, all_info=False):
        self.debug('update runs')

        self.stats.calculate()

        ans = self._get_all_automated_runs()
        # update the aliquots
        self._modify_aliquots(ans)

        # update the steps
        self._modify_steps(ans)

        # update run info
        if not all_info:
            ans = ans[-1:]

        self._update_info(ans)

#     def _clear_cache(self):
#         for di in dir(self):
#             if di.startswith('_cached'):
#                 setattr(self, di, None)

    def _get_labnumber(self, arun):
        '''
            cache labnumbers for quick retrieval
        '''
        ca = '_cached_{}'.format(arun.labnumber)
#         print ca, hasattr(self,ca)
        dbln = None
        if hasattr(self, ca):
            dbln = getattr(self, ca)

        if not dbln:
            db = self.db
            dbln = db.get_labnumber(arun.labnumber)
            setattr(self, ca, dbln)

        return dbln

    def _update_info(self, ans):
        self.debug('update run info')
#         db = self.db
        for ai in ans:
            if ai.labnumber and not ai.labnumber in ('dg',):
                dbln = self._get_labnumber(ai)
                sample = dbln.sample
                if sample:
                    ai.sample = sample.name

                ipos = dbln.irradiation_position
                if not ipos is None:
                    level = ipos.level
                    irrad = level.irradiation
                    ai.irradiation = '{}{}'.format(irrad.name, level.name)

    def _modify_steps(self, ans):
#        db = self.db
        idcnt_dict = dict()
        stdict = dict()
        extract_group = 1
        aoffs = dict()
        for arun in ans:
            arunid = arun.labnumber
            if arun.skip:
                continue

            if arun.extract_group:
                if not arun.extract_group == extract_group:
                    if arunid in aoffs:
                        aoffs[arunid] += 1
                    else:
                        aoffs[arunid] = 0

#                    aoff += 1
                    idcnt_dict, stdict = dict(), dict()
                    c = 1
                else:
                    if arunid in idcnt_dict:
                        c = idcnt_dict[arunid]
                        c += 1
                    else:
                        c = 1

                ln = self._get_labnumber(arun)
#                 ln = db.get_labnumber(arunid)
                if ln is not None:
                    st = 0
                    if ln.analyses:
                        an = ln.analyses[-1]
                        if an.aliquot != arun.aliquot:
                            st = 0
                        else:
                            try:
                                st = an.step
                                st = list(ALPHAS).index(st) + 1
                            except (IndexError, ValueError):
                                st = 0
                else:
                    st = stdict[arunid] if arunid in stdict else 0

                arun._step = st + c
                idcnt_dict[arunid] = c
                stdict[arunid] = st
                extract_group = arun.extract_group


            if arunid in aoffs:
                aoff = aoffs[arunid]
            else:
                aoff = 0
#             print arun.labnumber, aoff
            arun.aliquot += aoff

    def _modify_aliquots(self, ans):
#        print ans
        offset = 0
#        if self.experiment_set and self.experiment_set.selected:
#            offset = len(self.experiment_set.selected)

#        db = self.db
        # update the aliquots
        idcnt_dict = dict()
        stdict = dict()
        fixed_dict = dict()
        for arun in ans:
            if arun.skip:
                arun.aliquot = 0
                continue

            arunid = arun.labnumber
            c = 1
            st = 0
            if arunid in fixed_dict:
                st = fixed_dict[arunid]

            if arunid in idcnt_dict:
                c = idcnt_dict[arunid]
                if not arun.extract_group:
                    c += 1
                st = stdict[arunid] if arunid in stdict else 0
            else:
                ln = self._get_labnumber(arun)
                if ln is not None:
                    try:
                        st = ln.analyses[-1].aliquot
                    except IndexError:
                        st = 0
                else:
                    st = stdict[arunid] if arunid in stdict else 0

            if not arun.user_defined_aliquot:
                arun.aliquot = int(st + c - offset)
            else:
                c = 0
                fixed_dict[arunid] = arun.aliquot

#             print '{:<20s}'.format(str(arun.labnumber)), arun.aliquot, st, c
            idcnt_dict[arunid] = c
            stdict[arunid] = st

    def _load_experiment_queue_hook(self):
        self.executor.executable = all([ei.executable for ei in self.experiment_queues])

#===============================================================================
# handlers
#===============================================================================
    @on_trait_change('executor:execute_button')
    def _execute_fired(self):
        self.stop_file_listener()

        self.executor.trait_set(experiment_queues=self.experiment_queues,
                                experiment_queue=self.experiment_queues[0],
                                _experiment_hash=self._experiment_hash,
                                _text=self._text
                                )

        self.executor._execute()

    @on_trait_change('experiment_queues[]')
    def _update_stats(self):

        self.stats.experiment_queues = self.experiment_queues
        self.stats.calculate()

    @on_trait_change('experiment_queue:selected')
    def _update_selected(self, new):
        self.experiment_factory.set_selected_runs(new)

#    @on_trait_change('can_edit_script, max_allowable_runs')
#    def _update_value(self, name, value):
#        setattr(self.experiment_factory, name, value)

    def _experiment_queue_changed(self):
        eq = self.experiment_queue
        if eq:
            self.experiment_factory.queue = self.experiment_queue
            qf = self.experiment_factory.queue_factory
            for a in ('username', 'mass_spectrometer', 'extract_device', 'username',
                      'delay_before_analyses', 'delay_between_analyses'
                      ):
                setattr(qf, a, getattr(eq, a))
#===============================================================================
# property get/set
#===============================================================================
    def _get_title(self):
        if self.experiment_queue:
            return 'Experiment {}'.format(self.experiment_queue.name)

#===============================================================================
# defaults
#===============================================================================
    def _experiment_queue_factory(self, add=True, **kw):
        exp = ExperimentQueue(
                             db=self.db,
                             application=self.application,
                             **kw)
        exp.on_trait_change(self._update, 'update_needed')
        if add:
            self.experiment_queues.append(exp)
#        exp.on_trait_change(self._update_dirty, 'dirty')
        return exp

    def _experiment_queue_default(self):
        return self._experiment_queue_factory()
#    def _set_selector_default(self):
#        s = SetSelector(experiment_manager=self,
#                        addable=True
#                        )
#        return s
    def _executor_default(self):
        e = ExperimentExecutor(db=self.db,
                               application=self.application
                               )
        return e

    def _experiment_factory_default(self):
        e = ExperimentFactory(db=self.db,
                              application=self.application,
                              queue=self.experiment_queue,
                              max_allowable_runs=self.max_allowable_runs,
                              can_edit_scripts=self.can_edit_scripts
                              )

        from globals import globalv
        if globalv.experiment_debug:
            e.queue_factory.mass_spectrometer = 'Jan'
            e.queue_factory.extract_device = 'Fusions Diode'

            e.queue_factory.delay_between_analyses = 100
            e.queue_factory.delay_before_analyses = 10312
        return e

#============= EOF =============================================