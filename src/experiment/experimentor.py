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
from traits.api import Instance, List, on_trait_change, Bool, Event
# from traitsui.api import View, Item
# from src.loggable import Loggable
#============= standard library imports ========================
from itertools import groupby
#============= local library imports  ==========================
# from src.database.isotope_database_manager import IsotopeDatabaseManager
from src.experiment.queue.experiment_queue import ExperimentQueue

from src.experiment.factory import ExperimentFactory
from src.pychron_constants import ALPHAS
from src.experiment.stats import StatsGroup
from src.experiment.experiment_executor import ExperimentExecutor
# from src.experiment.executor import ExperimentExecutor
#from src.experiment.utilities.file_listener import FileListener
from src.experiment.utilities.identifier import convert_identifier, \
    ANALYSIS_MAPPING
#from src.deprecate import deprecated
from src.database.isotope_database_manager import IsotopeDatabaseManager

LAlphas = list(ALPHAS)


class Experimentor(IsotopeDatabaseManager):
    experiment_factory = Instance(ExperimentFactory)
    experiment_queue = Instance(ExperimentQueue)
    executor = Instance(ExperimentExecutor)
    experiment_queues = List
    stats = Instance(StatsGroup, ())

    mode = None
    unique_executor_db = False

    save_enabled = Bool

    #===========================================================================
    # permissions
    #===========================================================================
    #    max_allowable_runs = 10000
    #    can_edit_scripts = True
    #    _last_ver_time = None
    #    _ver_timeout = 10

    #===========================================================================
    # task events
    #===========================================================================
    execute_event = Event

    activate_editor_event = Event
    save_event = Event
    #    clear_display_event = Event
    def reset_run_generator(self):
        if self.executor.isAlive():
            self.debug('Queue modified. Reset run generator')
            #             self.executor.queue_modified = True
            self.executor.set_queue_modified()

    def refresh_executable(self, qs=None):
        if qs is None:
            qs = self.experiment_queues

        if self.executor.isAlive():
            qs = (self.executor.experiment_queue, )

        self.executor.executable = all([ei.isExecutable() for ei in qs])
        self.debug('setting executable {}'.format(self.executor.executable))

    def update_queues(self):
        self._update_queues()

    def test_connections(self):
        if not self.db:
            return

        if not self.db.connect():
            self.warning_dialog('Failed connecting to database. {}'.format(self.db.url))
            return

        return True

    def update_info(self):
        self._update()

    #===============================================================================
    # info update
    #===============================================================================
    def _get_all_runs(self, queues=None):
        if queues is None:
            queues = self.experiment_queues

        return [ai for ei in self.experiment_queues
                for ai in ei.executed_runs + ei.automated_runs
                if ai.executable]
    
    def _get_all_automated_runs(self):
        return [ai for ei in self.experiment_queues
                for ai in ei.automated_runs
                    if ai.executable]
        
    def _update(self, queues=None):
        if queues is None:
            queues = self.experiment_queues

        queues = [qi for qi in queues if qi.isUpdateable()]
        if not queues:
            return

        self.debug('update runs')
        self.debug('updating stats')
        self.stats.calculate()

        ans = self._get_all_runs(queues)
        #         print len([i for i in ans])
        exclude = ('dg', 'pa')
        #        timethis(self._modify_aliquots_steps, args=(ans,), kwargs=dict(exclude=exclude))
        self._modify_aliquots_steps(ans, exclude=exclude)

        self.debug('info updated')
        for qi in queues:
            qi.refresh_table_needed = True

    def _get_labnumber(self, ln):
        '''
            dont use cache
            cache labnumbers for quick retrieval
        '''
        db = self.db
        ln = convert_identifier(ln)
        dbln = db.get_labnumber(ln)

        return dbln

    def _group_analyses(self, ans, exclude=None):
        '''
        sort, group and filter by labnumber
        '''
        if exclude is None:
            exclude = tuple()
        key = lambda x: x.labnumber

        return ((ln, group) for ln, group in groupby(sorted(ans, key=key), key)
                if ln not in exclude)

    def _get_analysis_info(self, li):
        dbln = self.db.get_labnumber(li)
        sample, material, irradiationpos = '', '', ''
        if dbln:
            sample = dbln.sample
            if sample:
                if sample.material:
                    material = sample.material.name
                sample = sample.name

            dbpos = dbln.irradiation_position
            if dbpos:
                level = dbpos.level
                irradiationpos = '{}{}'.format(level.irradiation.name,
                                               level.name)

        dban = self.db.get_last_analysis(li)
        aliquot = 0
        step = -1
        if dban:
            aliquot = dban.aliquot
            step = dban.step

        #            self.debug('{} {} {}'.format(li, analysis, sample))
        return sample, material, irradiationpos, aliquot, step

    def _modify_aliquots_steps(self, ans, exclude=None):
        cache = dict()
        ecache = dict()
        db = self.db
        
        aruns=self._get_all_automated_runs()
        def _not_run(a):
            return a in aruns
          
        with db.session_ctx():
            for ai in ans:
                if ai.skip:
                    continue

                ln = ai.labnumber
                
                # is run in cache
                if not ln in cache:
                    sample, irrad, material, aliquot, step = self._get_analysis_info(ln)
                    cache[ln] = dict(sample=sample,
                                     material=material,
                                     irradiation=irrad,
                                     aliquot=aliquot,
                                     step=step,
                                     egrp=-1)

                last = cache[ln]
                aq = ai.aliquot
                s = -1
                #egrp = -1

                special = self._is_special(ln)
                egrp = ai.extract_group
                # is run part of aq step heat
                if egrp and not special:
                    en = '{}_{}'.format(ln, egrp)
                    if not en in ecache:
                        ecache[en] = dict(egrp=-1,
                                          step=-1,
                                          aliquot=last['aliquot'])

                    s = 0
                    elast = ecache[en]

                    aq = elast['aliquot']
                    if egrp == elast['egrp']:
                        s = elast['step'] + 1
                    else:
                        aq += 1

                        #print ai.runid, ai.state, ai.user_defined_aliquot
                        #print ai.runid, ai.user_defined_aliquot
                    if ai.user_defined_aliquot:
                        aq = ai.user_defined_aliquot
                        if ai.state not in ('success', 'failed', 'canceled'):
                            if egrp == elast['egrp']:
                                s = elast['step'] + 1
                            else:
                                dban = db.get_last_analysis(ln, aliquot=aq)
                                if dban:
                                    if dban.step:
                                        s = LAlphas.index(dban.step) + 1
                    if not _not_run(ai):
#                    if ai.state != 'not run':
                        s = LAlphas.index(ai.step)

                    elast['step'] = s
                    elast['egrp'] = ai.extract_group
                    elast['aliquot'] = aq

                    last['aliquot'] = max(aq, last['aliquot'])

                    ecache[en] = elast
                #                     last['step'] = st

                else:
                    if not ai.user_defined_aliquot:
                        aq = last['aliquot'] + 1
                        last['aliquot'] = aq

                if special:
                    s = ''
                    egrp = -1

                if _not_run(ai):
#                if ai.state == 'not run':
                    ai.trait_set(aliquot=int(aq),
                                 sample=last['sample'] or '',
                                 irradiation=last['irradiation'] or '',
                                 material=last['material'] or '',
                                 step=s)

                cache[ln] = last

    def _is_special(self, ln):
        special = False
        if '-' in ln:
            special = ln.split('-')[0] in ANALYSIS_MAPPING
        return special

    #     def execute_queues(self, queues, path, text, text_hash):
    def execute_queues(self, queues):
        self.debug('setup executor')

        self.executor.trait_set(
            experiment_queues=queues,
            experiment_queue=queues[0],
            #                                 path=path,
            stats=self.stats,
            #                                 text=text,
            #                                 text_hash=text_hash,
        )

        return self.executor.execute()

    #===============================================================================
    # handlers
    #===============================================================================
    @on_trait_change('executor:experiment_queue')
    def _activate_editor(self, eq):
        self.activate_editor_event = id(eq)

    @on_trait_change('executor:stop_button')
    def _stop(self):
        self.debug('%%%%%%%%%%%%%%%%%% Stop fired')
        if self.executor.isAlive():
            self.info('stop execution')
            '''
                if the executor is delaying then stop but dont cancel
                otherwise cancel
            '''
            self.executor.stop()

    @on_trait_change('executor:start_button')
    def _execute(self):
        '''
            trigger the experiment task to assemble current queues.
            the queues are then passed back to execute_queues()
        '''
        self.debug('%%%%%%%%%%%%%%%%%% Start fired')
        if not self.executor.isAlive():
        #             self.update_info()

            self.debug('%%%%%%%%%%%%%%%%%% Execute event true')
            self.execute_event = True

    @on_trait_change('experiment_queues[]')
    def _update_queues(self):
        qs = self.experiment_queues
        self.stats.experiment_queues = qs
        self.stats.calculate()
        self.refresh_executable(qs)

        self.debug('executor executable {}'.format(self.executor.executable))

    @on_trait_change('experiment_factory:run_factory:changed')
    def _queue_dirty(self):
        self.experiment_queue.changed = True

    #         executor = self.executor
    #         executor.executable = False

    #         if executor.isAlive():
    #             executor.prev_end_at_run_completion = executor.end_at_run_completion
    #             executor.end_at_run_completion = True
    #             executor.changed_flag = True

    @on_trait_change('experiment_queue:dclicked')
    def _dclicked_changed(self, new):
        self.experiment_factory.run_factory.edit_mode = True
        self._set_factory_runs(self.experiment_queue.selected)

    @on_trait_change('executor:non_clear_update_needed')
    def _refresh2(self):
        self.debug('non clear update needed fired')
        self.update_info()

    @on_trait_change('experiment_factory:run_factory:update_info_needed')
    def _refresh3(self):
        self.debug('update info needed fired')
        self.update_info()

    #         self.executor.clear_run_states()

    @on_trait_change('executor:queue_modified')
    def _refresh5(self, new):
        if new:
            self.debug('queue modified fired')
            self.update_info()

    @on_trait_change('experiment_factory:run_factory:refresh_table_needed')
    def _refresh4(self):
        for qi in self.experiment_queues:
            qi.refresh_table_needed = True

    @on_trait_change('experiment_factory:save_button')
    def _save_update(self):
        self.save_event = True

    def _experiment_queue_changed(self, eq):
        if eq:
            self.experiment_factory.queue = eq
            qf = self.experiment_factory.queue_factory
            for a in ('username', 'mass_spectrometer', 'extract_device',
                      'load_name',
                      'delay_before_analyses', 'delay_between_analyses'
            ):
                v = getattr(eq, a)
                if v is not None:
                    if isinstance(v, str):
                        v = v.strip()
                        if v:
                            setattr(qf, a, v)
                    else:
                        setattr(qf, a, v)

    @on_trait_change('experiment_queue:selected')
    def _selected_changed(self, new):
        ef = self.experiment_factory
        rf = ef.run_factory
        rf.edit_mode = False
        if new:

            self._set_factory_runs(new)

            a = new[-1]
            if not a.skip:
                self.stats.calculate_at(a)
                self.stats.calculate()

    def _set_factory_runs(self, new):
        ef = self.experiment_factory
        rf = ef.run_factory
        rf.special_labnumber = 'Special Labnumber'

        #rf._labnumber = NULL_STR
        #rf.labnumber = ''
        #         rf.edit_mode = True

        rf.suppress_update = True
        rf.set_selected_runs(new)

    #        rf.suppress_update = True

    #===============================================================================
    # property get/set
    #===============================================================================
    #     def _get_title(self):
    #         if self.experiment_queue:
    #             return 'Experiment {}'.format(self.experiment_queue.name)

    def _executor_factory(self):
        p1 = 'src.extraction_line.extraction_line_manager.ExtractionLineManager'
        p2 = 'src.spectrometer.spectrometer_manager.SpectrometerManager'
        p3 = 'src.spectrometer.ion_optics_manager.IonOpticsManager'
        kw = dict()
        if self.application:
            spec = self.application.get_service(p2)
            kw = dict(extraction_line_manager=self.application.get_service(p1),
                      spectrometer_manager=spec,
                      ion_optics_manager=self.application.get_service(p3), )

        if not self.unique_executor_db:
            kw['db'] = self.db
            kw['connect'] = False

        e = ExperimentExecutor(
            mode=self.mode,
            application=self.application,
            **kw
        )

        return e

    #===============================================================================
    # defaults
    #===============================================================================
    def _executor_default(self):
        return self._executor_factory()

    def _experiment_factory_default(self):
        dms = 'Spectrometer'
        if self.application:
            p2 = 'src.spectrometer.spectrometer_manager.SpectrometerManager'
            spec = self.application.get_service(p2)
            if spec:
                dms = spec.name.capitalize()

        e = ExperimentFactory(db=self.db,
                              application=self.application,
                              default_mass_spectrometer=dms
                              #                              max_allowable_runs=self.max_allowable_runs,
                              #                              can_edit_scripts=self.can_edit_scripts
        )

        #        from src.globals import globalv
        #        if globalv.experiment_debug:
        #            e.queue_factory.mass_spectrometer = 'Jan'
        #            e.queue_factory.extract_device = 'Fusions Diode'

        return e

        #============= EOF =============================================
        #     def start_file_listener(self, path):
        #         fl = FileListener(
        #                           path,
        #                           callback=self._reload_from_disk,
        #                           check=self._check_for_file_mods
        #                           )
        #         self.filelistener = fl
        #
        #     # @deprecated
        #     def stop_file_listener(self):
        #         if self.filelistener:
        #             self.filelistener.stop()
        #def _modify_aliquots_steps2(self, ans, exclude=None):
        #        '''
        #        '''
        #
        #        def get_is_special(ln):
        #            special = False
        #            if '-' in ln:
        #                special = ln.split('-')[0] in ANALYSIS_MAPPING
        #            return ln, special
        #
        #        def get_analysis_info(li):
        #            sample, irradiationpos = '', ''
        #
        #            #            analysis = db.get_last_analysis(li)
        #            #            if analysis:
        #            #                dbln = analysis.labnumber
        #            dbln = db.get_labnumber(li)
        #            if dbln:
        #                sample = dbln.sample
        #                if sample:
        #                    sample = sample.name
        #
        #                dbpos = dbln.irradiation_position
        #                if dbpos:
        #                    level = dbpos.level
        #                    irradiationpos = '{}{}'.format(level.irradiation.name,
        #                                                   level.name)
        #                    #            self.debug('{} {} {}'.format(li, analysis, sample))
        #            return sample, irradiationpos
        #
        #        db = self.db
        #        with db.session_ctx():
        #            groups = self._group_analyses(ans, exclude=exclude)
        #            for ln, analyses in groups:
        #                ln, special = get_is_special(ln)
        #                cln = convert_identifier(ln)
        #
        #                sample, irradiationpos = get_analysis_info(cln)
        #
        #                aliquot_key = lambda x: x._aliquot
        #                egroup_key = lambda x: x.extract_group
        #                if not special:
        #                    a = sorted(analyses, key=aliquot_key)
        #                    for aliquot, aa in groupby(a, key=aliquot_key):
        #                        aa = sorted(aa, key=egroup_key)
        #                        aliquot_start = None
        #
        #                        for egroup, ais in groupby(aa, key=egroup_key):
        #                            ast = self._set_aliquot_step(ais, special, cln,
        #                                                         aliquot,
        #                                                         aliquot_start,
        #                                                         egroup,
        #                                                         sample,
        #                                                         irradiationpos)
        #                            aliquot_start = ast + 1
        #
        #                else:
        #                    aliquot_start = None
        #                    egroup = 0
        #                    ans = sorted(analyses, key=aliquot_key)
        #                    for aliquot, ais in groupby(ans, key=aliquot_key):
        #                        self._set_aliquot_step(ais, special, cln, aliquot,
        #                                               aliquot_start,
        #                                               egroup,
        #                                               sample, irradiationpos)
        #
        #    def _set_aliquot_step(self, ais, special, cln,
        #                          aliquot,
        #                          aliquot_start,
        #                          egroup,
        #                          sample, irradiationpos):
        #        db = self.db
        #
        #        #         step_start = 0
        #        an = db.get_last_analysis(cln, aliquot=aliquot)
        #        if aliquot_start is None:
        #            aliquot_start = 0
        #            if an:
        #                aliquot_start = an.aliquot
        #                #                 print an.aliquot, aliquot
        #                #                 if an.step and an.aliquot == aliquot:
        #                #                     step_start = LAlphas.index(an.step) + 1
        #
        #        step_cnt = 0
        #        aliquot_cnt = 0
        #        for arun in ais:
        #        #             for arun in aruns:
        #            arun.trait_set(sample=sample or '', irradiation=irradiationpos or '')
        #            if arun.skip:
        #                arun.aliquot = 0
        #                continue
        #
        #            if arun.state in ('failed', 'canceled'):
        #                continue
        #
        #            if not arun.user_defined_aliquot:
        #                if arun.state in ('not run', 'extraction', 'measurement'):
        #                #                     print arun.runid, egroup, aliquot_start, aliquot_cnt
        #                    arun.assigned_aliquot = int(aliquot_start + aliquot_cnt + 1)
        #                    if special or not egroup:
        #                        aliquot_cnt += 1
        #
        #            if not special and egroup:
        #                step_start = 0
        #                #                 an = db.get_last_analysis(cln, aliquot=aliquot)
        #                if an and an.step and an.aliquot == arun.aliquot:
        #                    step_start = LAlphas.index(an.step) + 1
        #
        #                arun.step = int(step_start + step_cnt)
        #                #                 print arun.aliquot, arun.step, step_start, step_cnt
        #                step_cnt += 1
        #
        #        return aliquot_start