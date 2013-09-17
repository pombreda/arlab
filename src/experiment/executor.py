# #===============================================================================
# # Copyright 2012 Jake Ross
# #
# # Licensed under the Apache License, Version 2.0 (the "License");
# # you may not use this file except in compliance with the License.
# # You may obtain a copy of the License at
# #
# #   http://www.apache.org/licenses/LICENSE-2.0
# #
# # Unless required by applicable law or agreed to in writing, software
# # distributed under the License is distributed on an "AS IS" BASIS,
# # WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# # See the License for the specific language governing permissions and
# # limitations under the License.
# #===============================================================================
#
# #============= enthought library imports =======================
# from traits.api import Button, Event, Enum, Property, Bool, Float, Dict, \
#     Instance, Str, String, List, Color, Int
# from apptools.preferences.preference_binding import bind_preference
# #============= standard library imports ========================
# from threading import Event as Flag
# from threading import Thread
# import time
# import os
# import weakref
# #============= local library imports  ==========================
# from src.ui.thread import Thread as uThread
# from src.globals import globalv
# from src.managers.manager import Manager
# from src.pyscripts.pyscript_runner import PyScriptRunner, RemotePyScriptRunner
# from src.managers.data_managers.h5_data_manager import H5DataManager
# from src.experiment.utilities.mass_spec_database_importer import MassSpecDatabaseImporter
# from src.paths import paths
# from src.helpers.parsers.initialization_parser import InitializationParser
# from src.experiment.stats import StatsGroup
# from src.pyscripts.extraction_line_pyscript import ExtractionPyScript
# from src.lasers.laser_managers.ilaser_manager import ILaserManager
# from src.database.orms.isotope_orm import meas_AnalysisTable, gen_AnalysisTypeTable, \
#     meas_MeasurementTable, gen_MassSpectrometerTable, meas_ExtractionTable, \
#     gen_ExtractionDeviceTable
# from src.constants import NULL_STR
# from src.monitors.automated_run_monitor import AutomatedRunMonitor, \
#     RemoteAutomatedRunMonitor
# from src.displays.display import DisplayController
# from src.experiment.experimentable import Experimentable
# # from src.ui.thread import Thread
# from src.pyscripts.wait_dialog import WaitDialog
# from src.experiment.automated_run.automated_run import AutomatedRun
# from pyface.constant import CANCEL, NO, YES
# # from src.helpers.ctx_managers import no_update
# from sqlalchemy.orm.exc import NoResultFound
# from src.consumer_mixin import ConsumerMixin, consumable
# from src.codetools.memory_usage import mem_log, mem_break, \
#     mem_available, mem_log_func, count_instances
# from src.ui.gui import invoke_in_main_thread
# from pyface.timer.do_later import do_later
# from memory_profiler import profile
# import gc
#
#
# BLANK_MESSAGE = '''First "{}" not preceeded by a blank.
# If "Yes" use last "blank_{}"
# Last Run= {}
#
# If "No" select from database
# '''
#
# class ExperimentExecutor(Experimentable):
#     spectrometer_manager = Instance(Manager)
#     extraction_line_manager = Instance(Manager)
#     ion_optics_manager = Instance(Manager)
#     massspec_importer = Instance(MassSpecDatabaseImporter)
#     info_display = Instance(DisplayController)
#     pyscript_runner = Instance(PyScriptRunner)
#     monitor = Instance(AutomatedRunMonitor)
#     data_manager = Instance(H5DataManager, ())
#
#     wait_dialog = Instance(WaitDialog, ())
#
#     current_run = Instance(AutomatedRun)
#     executed_runs = List
#
#     end_at_run_completion = Bool(False)
#     delay_between_runs_readback = Float
#     delaying_between_runs = Bool(False)
#     resume_runs = Bool(False)
# #     changed_flag = Bool(False)
#
#     show_sample_map = Button
#     execute_button = Event
#     resume_button = Button('Resume')
#     cancel_run_button = Button('Cancel Run')
#     refresh_button = Event
#     non_clear_update_needed = Event
#     run_completed = Event
#     auto_save_event = Event
#
#     can_cancel = Property(depends_on='_alive, delaying_between_runs')
# #     refresh_label = Property(depends_on='_was_executed')
#     execute_label = Property(depends_on='_alive')
#
#     truncate_button = Button('Truncate Run')
#     truncate_style = Enum('Normal', 'Quick')
#     '''
#         immediate 0= measure_iteration stopped at current step, script continues
#         quick     1= measure_iteration stopped at current step, script continues using 0.25*counts
#
#         old-style
#             immediate 0= is the standard truncation, measure_iteration stopped at current step and measurement_script truncated
#             quick     1= the current measure_iteration is truncated and a quick baseline is collected, peak center?
#             next_int. 2= same as setting ncounts to < current step. measure_iteration is truncated but script continues
#     '''
#
#     extraction_state_label = String
#     extraction_state_color = Color
#     extraction_state = None
#
#     _alive = Bool(False)
# #     _last_ran = None
#     _prev_baselines = Dict
#     _prev_blanks = Dict
# #     _was_executed = Bool(False)
#     err_message = None
#
#     db_kind = Str
#     username = Str
#
#     mode = 'normal'
#
#     measuring = Bool(False)
#     extracting = Bool(False)
#
#     stats = Instance(StatsGroup)
#
#     new_run_gen_needed = False
#
#     statusbar = String
#
#     executable = Bool
#
#     _state_thread = None
#     _end_flag = None
#     _canceled = False
#
#     _abort_overlap_signal = None
# #     _triggered_run = False
#
#     queue_modified = False
# #     _queue_dirty = False
#
#     auto_save_delay = Int(30)
#     use_auto_save = Bool(True)
#
#     def set_queue_modified(self):
#         self.queue_modified = True
#
#     def isAlive(self):
#         return self._alive
#
#     def info(self, msg, log=True, color=None, *args, **kw):
#         if self.info_display:
#             if color is None:
#                 color = 'green'
#
#             self.info_display.add_text(msg, color=color)
#
#         if log:
#             super(ExperimentExecutor, self).info(msg, *args, **kw)
#
#     def bind_preferences(self):
#         super(ExperimentExecutor, self).bind_preferences()
#
#         prefid = 'pychron.experiment'
#
#         bind_preference(self.massspec_importer.db, 'name', '{}.massspec_dbname'.format(prefid))
#         bind_preference(self.massspec_importer.db, 'host', '{}.massspec_host'.format(prefid))
#         bind_preference(self.massspec_importer.db, 'username', '{}.massspec_username'.format(prefid))
#         bind_preference(self.massspec_importer.db, 'password', '{}.massspec_password'.format(prefid))
#
#     def experiment_blob(self):
#         path = self.experiment_queue.path
#         if os.path.isfile(path):
#             with open(self.experiment_queue.path) as fp:
#                 text = fp.read()
#                 return '{}\n{}'.format(self.experiment_queue.path, text)
#
#     def add_backup(self, uuid_str):
#         with open(paths.backup_recovery_file, 'a') as fp:
#             fp.write('{}\n'.format(uuid_str))
#
#     def remove_backup(self, uuid_str):
#         with open(paths.backup_recovery_file, 'r') as fp:
#             r = fp.read()
#
#         r = r.replace('{}\n'.format(uuid_str), '')
#         with open(paths.backup_recovery_file, 'w') as fp:
#             fp.write(r)
#
#     def execute_procedure(self, name=None):
#         if name is None:
#             name = self.open_file_dialog(default_directory=paths.procedures_dir)
#             if not name:
#                 return
#             name = os.path.basename(name)
#
#         self._execute_procedure(name)
#
#     def reset(self):
# #         self._was_executed = False
#         self.experiment_queue = None
#         self.experiment_queues = []
#
#     def stop(self):
#         if self.delaying_between_runs:
#             self._alive = False
#             self.stats.stop_timer()
#         else:
#             self.cancel()
#
#     def cancel(self, style='queue', cancel_run=False, msg=None, confirm=True):
#         arun = self.current_run
# #        arun = self.experiment_queue.current_run
#         if style == 'queue':
#             name = os.path.basename(self.experiment_queue.path)
#             name, _ = os.path.splitext(name)
#         else:
#             name = arun.runid
#
#         if name:
#             ret = YES
#             if confirm:
#                 m = 'Cancel {} in Progress'.format(name)
#                 if msg:
#                     m = '{}\n{}'.format(m, msg)
#
#                 ret = self.confirmation_dialog(m,
#                                          title='Confirm Cancel',
#                                          return_retval=True
#                                          )
#
#             if ret == YES:
#                 # stop queue
#                 if style == 'queue':
#                     self._alive = False
#                     self.stats.stop_timer()
#                 self.set_extract_state(False)
#                 self.wait_dialog.stop()
#                 self._canceled = True
#                 if arun:
#                     if style == 'queue':
#                         state = None
#                         if cancel_run:
#                             state = 'canceled'
#                     else:
#                         state = 'canceled'
#                         arun.aliquot = 0
#
#                     arun.cancel_run(state=state)
#                     self.non_clear_update_needed = True
#                     self.current_run = None
#
#     def set_extract_state(self, state, flash=0.75, color='green'):
#
#         def loop(end_flag, label, color):
#             '''
#                 freq== percent label is shown e.g 0.75 means display label 75% of the iterations
#                 iperiod== iterations per second (inverse period == rate)
#
#             '''
#             freq = flash
#             if freq:
#                 iperiod = 20
#                 period = 1 / float(iperiod)
#
#                 threshold = freq ** 2 * iperiod  # mod * freq
#
#                 i = 0
#                 kw = dict(extraction_state_label=label,
#                         extraction_state_color=color)
#                 while not end_flag.is_set():
#                     if i % iperiod < threshold:
#                         invoke_in_main_thread(self.trait_set, **kw)
#                     else:
#                         invoke_in_main_thread(self.trait_set,
#                                               extraction_state_label='')
#
#                     time.sleep(period)
#                     i += 1
#                     if i > 1000:
#                         i = 0
#             else:
#                 invoke_in_main_thread(self.trait_set,
#                                       extraction_state_label=label,
#                                       extraction_state_color=color)
#
#         if state:
#             if self._state_thread:
#                 self._end_flag.set()
#
#             time.sleep(0.1)
#             self._end_flag = Flag()
#             t = uThread(target=loop,
#                        args=(self._end_flag,
#                              '*** {} ***'.format(state.upper()),
#                              color,
#                              )
#                        )
#             t.start()
#             self._state_thread = t
#         else:
#             if self._end_flag:
#                 self._end_flag.set()
#             invoke_in_main_thread(self.trait_set, extraction_state_label='')
#
#     def clear_run_states(self):
#         for exp in self.experiment_queues:
#             if exp.selected:
#                 runs = exp.selected
#             else:
#                 runs = exp.automated_runs
#             for ei in runs:
#                 ei.state = 'not run'
#
#     def check_alive(self):
#         if not self.isAlive():
#             self.err_message = 'User quit'
#             return False
#         else:
#             return True
#
#     def execute(self):
#
#         self.debug('%%%%%%%%%%%%%%%%%%% Starting Execution')
#         mem_log('exp start')
#                     # check for blank before starting the thread
#         if self._pre_execute_check():
#             self.stats.reset()
#             self.stats.start_timer()
#
#             self._canceled = False
#             self._abort_overlap_signal = Flag()
#             self.extraction_state_label = ''
#
#             self.debug('execution started')
#
#             t = Thread(target=self._execute)
#             t.start()
#
#             return True
#
# #===============================================================================
# # stats
# #===============================================================================
#     def _increment_nruns_finished(self):
#         self.stats.nruns_finished += 1
#
# #    def reset_stats(self):
# # #        self._alive = True
# #        self.stats.start_timer()
# #
# #    def stop_stats_timer(self):
# # #        self._alive = False
# #        self.stats.stop_timer()
#
# #===============================================================================
# # handlers
# #===============================================================================
#
# #===============================================================================
# # private
# #===============================================================================
# #===============================================================================
# # pre execute checking
# #===============================================================================
#     def _pre_execute_check(self, inform=True):
#         self.debug('********************** NOT DOING PRE EXECUTE CHECK ')
#         return True
#
#         if self._check_memory():
#             return
#
#         dbr = self._get_preceeding_blank_or_background(inform=inform)
#         if not dbr is True:
#             if dbr is None:
#                 return
#             else:
#                 self.info('using {} as the previous blank'.format(dbr.record_id))
#                 dbr.load_isotopes()
#                 self._prev_blanks = dbr.get_baseline_corrected_signal_dict()
#
#         if not self.massspec_importer.connect():
#             if not self.confirmation_dialog('Not connected to a Mass Spec database. Do you want to continue with pychron only?'):
#                 return
#
#         if not self._check_managers(inform=inform):
#             return
#
# #         if self.monitor is None:
# #             self.warning('No automated run monitor')
# #             self.warning_dialog('Canceled! Error in the AutomatedRunMonitor configuration file')
# #             self.info('experiment canceled because automated_run_monitor is not setup properly')
# #             return
#
#         return True
#
#     def _get_blank(self, kind, ms, ed, last=False):
#         db = self.db
#         sel = db.selector_factory(style='single')
#         sess = db.get_session()
#         q = sess.query(meas_AnalysisTable)
#         q = q.join(meas_MeasurementTable)
#         q = q.join(meas_ExtractionTable)
#         q = q.join(gen_AnalysisTypeTable)
#         q = q.join(gen_MassSpectrometerTable)
#         q = q.join(gen_ExtractionDeviceTable)
#
#         q = q.filter(gen_AnalysisTypeTable.name == 'blank_{}'.format(kind))
#         q = q.filter(gen_MassSpectrometerTable.name == ms)
#         q = q.filter(gen_ExtractionDeviceTable.name == ed)
#
#         dbr = None
#         if last:
#             q = q.order_by(meas_AnalysisTable.analysis_timestamp.desc())
#             q = q.limit(1)
#             try:
#                 dbr = q.one()
#             except NoResultFound:
#                 pass
#
#         else:
#             dbs = q.all()
#             sel.load_records(dbs, load=False)
#             sel.selected = sel.records[-1]
#             info = sel.edit_traits(kind='livemodal')
#             if info.result:
#                 dbr = sel.selected
#
#         if dbr:
#             dbr = sel._record_factory(dbr)
#             return dbr
#
#     def _get_preceeding_blank_or_background(self, inform=True):
#         exp = self.experiment_queue
#
#         types = ['air', 'unknown', 'cocktail']
#         # get first air, unknown or cocktail
#         aruns = exp.cleaned_automated_runs
#         an = next((a for a in aruns
#                                     if not a.skip and \
#                                         a.analysis_type in types and \
#                                             a.state == 'not run'), None)
#
#         if an:
#             if aruns.index(an) == 0:
#                 pdbr = self._get_blank(an.analysis_type, exp.mass_spectrometer,
#                                        exp.extract_device,
#                                        last=True)
#                 if pdbr:
#                     msg = BLANK_MESSAGE.format(an.analysis_type,
#                                                an.analysis_type,
#                                                pdbr.record_id)
#
#                     retval = NO
#                     if inform:
#                         retval = self.confirmation_dialog(msg,
#                                                       cancel=True,
#                                                       return_retval=True)
#
#                     if retval == CANCEL:
#                         return
#                     elif retval == YES:
#                         return pdbr
#                     else:
#                         return self._get_blank(an.analysis_type, exp.mass_spectrometer,
#                                                exp.extract_device)
#                 else:
#                     self.warning_dialog('No blank for {} is in the database. Run a blank!!'.format(an.analysis_type))
#                     return
#
#         return True
#
#     def _check_managers(self, inform=True):
#         exp = self.experiment_queue
#         nonfound = self._check_for_managers(exp)
#         if nonfound:
#             if inform:
#                 self.warning_dialog('Canceled! Could not find managers {}'.format(','.join(nonfound)))
#             self.info('experiment canceled because could not find managers {}'.format(nonfound))
#             return
#
#         return True
#
#     def _check_for_managers(self, exp):
#         if globalv.experiment_debug:
#             self.debug('not checking for managers')
#             return []
#
#         nonfound = []
#         if self.extraction_line_manager is None:
#             if not globalv.experiment_debug:
#                 nonfound.append('extraction_line')
#
#         if exp.extract_device != NULL_STR:
#             extract_device = exp.extract_device.replace(' ', '_').lower()
#             man = None
#             if self.application:
#                 man = self.application.get_service(ILaserManager, 'name=="{}"'.format(extract_device))
#
#             if not man:
#                 nonfound.append(extract_device)
#             elif man.mode == 'client':
#                 if not man.test_connection():
#                     nonfound.append(extract_device)
#
#         needs_spec_man = any([ai.measurement_script
#                               for ai in self._get_all_automated_runs()
#                                     if ai.state == 'not run'])
#
#         if self.spectrometer_manager is None and needs_spec_man:
#             nonfound.append('spectrometer')
#
#         return nonfound
#
# #===============================================================================
# # execution
# #===============================================================================
#     def _execute(self):
#         self.db.reset()
#         self._execute_experiment_queues()
#         self.err_message = False
# #         self._was_executed = True
#
#     def _execute_experiment_queues(self):
#
#         self.pyscript_runner.connect()
#         self._alive = True
#
#         exp = self.experiment_queue
# #         do_later(exp.trait_set, executed=True)
# #         invoke_in_main_thread(exp.trait_set, executed=True)
#         exp.executed = True
#
#         # check the first aliquot before delaying
#         arv = exp.cleaned_automated_runs[0]
#         self._check_run_aliquot(arv)
#
#         # delay before starting
#         delay = exp.delay_before_analyses
#         self._delay(delay, message='before')
#
#         rc = 0
#         ec = 0
#         for i, exp in enumerate(self.experiment_queues):
#             if self.isAlive():
#                 self.experiment_queue = exp
#
#                 exp.executed = True
#
#                 # scroll to the first run
#                 exp.automated_runs_scroll_to_row = 0
#
#                 t = self._execute_automated_runs(i + 1, exp)
#                 if t:
#                     rc += t
#                     ec += 1
#
#             if self.end_at_run_completion:
#                 break
#
#         self.info('Executed {:n} queues. total runs={:n}'.format(ec, rc))
#         self._alive = False
#
#     def _check_memory(self, threshold=50):
#         '''
#             if avaliable memory is less than threshold  (MB)
#             stop the experiment
#             issue a warning
#
#             return True if out of memory
#             otherwise None
#         '''
#         # return amem in MB
#         amem = mem_available()
#         self.debug('Available memory {}. mem-threshold= {}'.format(amem, threshold))
#         if amem < threshold:
#             msg = 'Memory limit exceeded. Only {} MB available. Stopping Experiment'.format(amem)
#             invoke_in_main_thread(self.warning_dialog, msg)
#             return True
#
#     def _wait_for_save(self):
#         '''
#             wait for experiment queue to be saved.
#
#             actually wait until time out or self.executable==True
#             executable set higher up by the Experimentor
#
#             if timed out auto save or cancel
#
#         '''
#         st = time.time()
#         delay = self.auto_save_delay
#         auto_save = self.use_auto_save
#
#         if not self.executable:
#             self.info('Waiting for save')
#             cnt = 0
#
#             while not self.executable:
#                 time.sleep(1)
#                 if time.time() - st < delay:
#                     self.set_extract_state('Waiting for save. Autosave in {} s'.format(delay - cnt),
#                                            flash=False
#                                            )
#                     cnt += 1
#                 else:
#                     break
#
#             if not self.executable:
#                 self.info('Timed out waiting for user input')
#                 if auto_save:
#                     self.info('autosaving experiment queues')
#                     self.set_extract_state('')
#                     self.auto_save_event = True
#                 else:
#                     self.info('canceling experiment queues')
#                     self.cancel(confirm=False)
#
#     def _delay(self, delay, message='between'):
#         self.delay_between_runs_readback = delay
#         self.info('Delay {} runs {}'.format(message, delay))
#
#         time.sleep(1)
#         self.delaying_between_runs = True
#         self.resume_runs = False
#         st = time.time()
#         while time.time() - st < delay - 1:
#             if not self.isAlive():
#                 break
#             if self.resume_runs:
#                 break
#
#             time.sleep(0.5)
#             self.delay_between_runs_readback -= 0.5
#         self.delaying_between_runs = False
#         self.delay_between_runs_readback = 0
#
#     def _execute_procedure(self, name):
#         self.pyscript_runner.connect()
#
#         root = paths.procedures_dir
#         self.info('executing procedure {}'.format(os.path.join(root, name)))
#
#         els = ExtractionPyScript(root=root,
#                                      name=name,
#                                      runner=self.pyscript_runner
#                                      )
#         if els.bootstrap():
#             try:
#                 els._test()
#                 els.execute(new_thread=True, bootstrap=False)
#             except Exception, e:
#                 self.warning(e)
#                 self.warning_dialog('Invalid Script {}'.format(name))
#
#     def _execute_automated_runs(self, iexp, exp):
#
#         self.info('Starting automated runs set= Set{}'.format(iexp))
#
#         # save experiment to database
#         self.info('saving experiment "{}" to database'.format(exp.name))
#         dbexp = self.db.add_experiment(exp.path)
#         self.db.commit()
#         exp.database_identifier = int(dbexp.id)
#
#         # get a run generator
#         rgen, nruns = exp.new_runs_generator()
#         cnt = 0
#         totalcnt = 0
#
#         # setup consumer for overlapping runs
# #         consumer = ConsumerMixin()
# #         consumer.setup_consumer(func=self._overlapped_run)
#
#         delay = exp.delay_between_analyses
#         force_delay = False
#         last_runid = None
#
# #         sbefore = measure_type(group='src')
# #         qbefore = measure_type(group='sqlalchemy')
#         with consumable(func=self._overlapped_run) as con:
#             while self.isAlive():
#                 mem_log('run start')
#
#                 if self._check_memory():
#                     break
#
#                 # if the experiment queue has been modified wait until saved or
#                 # timed out. if timed out autosave.
#                 # @todo: add preferences for timeout and whether to autosave or stop
#                 self._wait_for_save()
#
#                 if self.queue_modified:
#                     self.debug('Queue modified. making new run generator')
#                     rgen, nruns = exp.new_runs_generator()
#                     cnt = 0
#                     self.queue_modified = False
#                     force_delay = True
#
#                 if force_delay or \
#                     (self.isAlive() and cnt < nruns and not cnt == 0):
#                     # delay between runs
#                     self._delay(delay)
#                     force_delay = False
#
# #                 if self.current_run is not None:
# #                     self.current_run.plot_panel.reset()
# #                     self.current_run.plot_panel = None
#
#                 self.current_run = None
#                 self.db.reset()
#                 mem_log('post reset')
#
#                 runargs = None
#                 try:
#                     runspec = rgen.next()
#                     # wait until only one previous run if overlapping
#                     while not con.is_empty() and con.queue_size() > 1:
#                         time.sleep(0.05)
#
#                     if not runspec.skip:
#                         runargs = self._launch_run(runspec, cnt)
#                         mem_log('post launch run')
#
#                 except StopIteration:
#                     break
#
#                 cnt += 1
#                 if runargs:
#                     t, run = runargs
#                     '''
#                         ?? overlay not fully implemented ??
#                     '''
#                     if runspec.analysis_type == 'unknown' and runspec.overlap:
#                         self.info('overlaping')
#                         run.wait_for_overlap()
#                         self.debug('overlap finished. starting next run')
#
#                         con.add_consumable((t, run))
# #                         self._executing_queue.put((t, run))
#                         totalcnt += 1
#
#                     else:
#                         t.join()
#
#                         self.debug('{} finished'.format(run.runid))
#                         if self.isAlive():
#                             totalcnt += 1
#                             if runspec.analysis_type.startswith('blank'):
#                                 pb = run.get_baseline_corrected_signals()
#                                 if pb is not None:
#                                     self._prev_blanks = pb
#
#                         self._report_execution_state(run)
#                         last_runid = run.runid
#                         run.teardown()
#
#                         mem_log('{} post teardown'.format(last_runid))
#
#                 if self.end_at_run_completion:
#                     break
#
# #                 from PySide import QtCore
# #                 gc.collect()
# #                 count_instances()
# #                 roots = objgraph.get_leaking_objects()
# #                 objgraph.show_most_common_types(objects=roots)
# #                 objgraph.show_refs()
#             if self.err_message:
#                 self.warning('automated runs did not complete successfully')
#                 self.warning('error: {}'.format(self.err_message))
#
#             self._end_runs()
#             if last_runid:
#                 self.info('Queue {:02n}. Automated runs ended at {}, runs executed={}'.format(iexp, last_runid, totalcnt))
#
#         return totalcnt
#
#     def _overlapped_run(self, v):
#         t, run = v
# #         while t.is_alive():
# #             time.sleep(1)
#         t.join()
#
#         self.debug('{} finished'.format(run.runid))
#         if run.analysis_type.startswith('blank'):
#             pb = run.get_baseline_corrected_signals()
#             if pb is not None:
#                 self._prev_blanks = pb
#         self._report_execution_state(run)
#         run.teardown()
#
#     def _report_execution_state(self, run):
#         if self.err_message:
#             msg = self.err_message
#         else:
#             msg = 'Success'
#
#         man = self.application.get_service('src.social.twitter_manager.TwitterManager')
#         if man is not None:
#             man.post('{} {}'.format(msg, run.runid))
#
#         man = self.application.get_service('src.social.email_manager.EmailManager')
#         if man is not None:
#             if msg == 'Success':
#                 msg = '{}\n{}'.format(msg, run.assemble_report())
# #                man.broadcast(msg)
#
#     def _launch_run(self, run, cnt):
#         arun = self._setup_automated_run(cnt, run)
#         self.info('========== {} =========='.format(arun.runid))
#
#         ta = Thread(name=arun.runid,
# #                     target=lambda x: x,
#                    target=self._do_automated_run,
#                    args=(arun,)
#                    )
#         ta.start()
#         return ta, arun
#
#     def _check_run_aliquot(self, arv):
#         '''
#             check the secondary database for this labnumber
#             get last aliquot
#         '''
#         if self.massspec_importer:
#             db = self.massspec_importer.db
#             if db.connected:
#                 try:
#                     _ = int(arv.labnumber)
#                     al = db.get_lastest_analysis_aliquot(arv.labnumber)
#                     if al is not None:
#                         if al > arv.aliquot:
#                             old = arv.aliquot
#                             arv.aliquot = al + 1
#                             self.message('{}-{:02n} exists in secondary database. Modifying aliquot to {:02n}'.format(arv.labnumber,
#                                                                                                                       old,
#                                                                                                            arv.aliquot))
#                 except ValueError:
#                     pass
#
# #    def _setup_automated_run(self, i, arun, repo, dm, runner):
#     def _setup_automated_run(self, i, arv):
#         '''
#             convert the an AutomatedRunSpec an AutomatedRun
#         '''
#         exp = self.experiment_queue
#         self.debug('setup run {} of {}'.format(i, exp.name))
#
#         # the first run was checked before delay before runs
#         if i > 1:
#             # test manager connections
#             if not self._check_managers():
#                 return
#
#             self._check_run_aliquot(arv)
#
#         if arv.end_after:
#             self.end_at_run_completion = True
#
#         arun = arv.make_run(run=self.current_run)
#         '''
#             save this runs uuid to a hidden file
#             used for analysis recovery
#         '''
#         self.add_backup(arun.uuid)
#         arun.experiment_identifier = exp.database_identifier
#         arun.load_name = exp.load_name
#         arun.integration_time = 1.04
#
#         if self.current_run is None:
#             arun.experiment_manager = weakref.ref(self)()
#
#             arun.spectrometer_manager = self.spectrometer_manager
#             arun.extraction_line_manager = self.extraction_line_manager
#             arun.ion_optics_manager = self.ion_optics_manager
#             arun.data_manager = self.data_manager
#             arun.db = self.db
#             arun.massspec_importer = self.massspec_importer
#             arun.runner = self.pyscript_runner
#
#         mon = self.monitor
#         if mon is not None:
#             mon.automated_run = weakref.ref(arun)()
#             arun.monitor = mon
#
#         self.current_run = arun
#         return arun
#
#     def _do_automated_run(self, arun):
#
#         mem_log('{} started'.format(arun.runid))
#         st = time.time()
#         for step in (
#                      '_start_run',
#                     '_extraction',
#                     '_measurement',
#                     '_post_measurement'
#                      ):
#
#             if not self.check_alive():
#                 break
#
#             f = getattr(self, step)
#             if not f(arun):
#                 break
#         else:
#
#             self.debug('$$$$$$$$$$$$$$$$$$$$ state at run end {}'.format(arun.state))
#             if not arun.state in ('truncated', 'canceled', 'failed'):
#                 arun.state = 'success'
#
#         self._increment_nruns_finished()
#
#         if arun.state in ('success', 'truncated'):
#             self.run_completed = arun
#
#         # check to see if action should be taken
#         self._check_run_at_end(arun)
#
#         t = time.time() - st
#         self.info('Automated run {} {} duration: {:0.3f} s'.format(arun.runid, arun.state, t))
#
#         arun.finish()
#         mem_log('{} post finish'.format(arun.runid))
#
#     def _start_run(self, ai):
#         ret = True
#
#         if not ai.start():
#             self.err_message = 'Monitor failed to start'
#             self._alive = False
#             ret = False
#         else:
#             self.experiment_queue.set_run_inprogress(ai.runid)
#
#         return ret
#
#     def _extraction(self, ai):
#         ret = True
# #         invoke_in_main_thread(self.trait_set, extracting=True)
#         self.extracting = True
#         if not ai.do_extraction():
#             ret = self._failed_execution_step('Extraction Failed')
#
# #         invoke_in_main_thread(self.trait_set, extraction_state_label='', extraction=False)
#         self.trait_set(extraction_state_label='', extraction=False)
#         return ret
#
#     def _measurement(self, ai):
#         ret = True
#
#         self.measuring = True
#
# #         invoke_in_main_thread(self.trait_set, measuring=True)
#         if not ai.do_measurement():
#             ret = self._failed_execution_step('Measurement Failed')
# #         else:
# #             mem_log('{} post measurement'.format(ai.runid))
# #             ai.post_measurement_save()
# #             mem_log('post save {}'.format(ai.runid))
#
#         self.measuring = False
# #         invoke_in_main_thread(self.trait_set, measuring=False)
#         return ret
#
#     def _post_measurement(self, ai):
#         if not ai.do_post_measurement():
#             self._failed_execution_step('Post Measurement Failed')
#         else:
#             return True
#
#     def _failed_execution_step(self, msg):
#         if not self._canceled:
#             self.err_message = msg
#             self._alive = False
#         return False
# #===============================================================================
# #
# #===============================================================================
#     def _check_run_at_end(self, run):
#         '''
#             check to see if an action should be taken
#
#             if runs  are overlapping this will be a problem.
#
#             dont overlay onto blanks
#
#             execute the action and continue the queue
#         '''
#
#         for action in self.experiment_queue.queue_actions:
#             if action.check_run(run):
#                 self._do_action(action)
#                 break
#
#     def _do_action(self, action):
#         self.info('Do queue action {}'.format(action.action))
#         if action.action == 'repeat':
#             if action.count < action.nrepeat:
#                 self.debug('repeating last run')
#                 action.count += 1
#                 exp = self.experiment_queue
#
#                 run = exp.executed_runs[0]
#                 exp.automated_runs.insert(0, run)
#
#                 # experimentor handles the queue modified
#                 # resets the database and updates info
#                 self.queue_modified = True
#
#             else:
#                 self.info('executed N {} {}s'.format(action.count + 1,
#                                                      action.action))
#                 self.cancel(confirm=False)
#
#         elif action.action == 'cancel':
#             self.cancel(confirm=False)
#
# #===============================================================================
# #
# #===============================================================================
#
#     def _end_runs(self):
# #         self._last_ran = None
#         self.stats.stop_timer()
#
#         self.db.reset()
#
#         def _set_extraction_state():
#             self.extraction_state = False
#             self.extraction_state_color = 'green'
#             self.extraction_state_label = '{} Finished'.format(self.experiment_queue.name)
#         invoke_in_main_thread(_set_extraction_state)
#
# #     def _get_all_automated_runs(self):
# #         ans = super(ExperimentExecutor, self)._get_all_automated_runs()
# #
# #         startid = 0
# #         exp = self.experiment_queue
# #         if exp and exp._cached_runs:
# #             try:
# #                 startid = exp._cached_runs.index(self._last_ran) + 1
# #             except ValueError:
# #                 pass
# #
# #         if startid:
# #             return [ai for ai in ans][startid:]
# #         else:
# #             return ans
#
# #===============================================================================
# # handlers
# #===============================================================================
#     def _resume_button_fired(self):
#         self.resume_runs = True
#
#     def _cancel_run_button_fired(self):
#         self.debug('cancel run {}'.format(self.isAlive()))
#         if self.isAlive():
#             crun = self.current_run
#             self.debug('cancel run {}'.format(crun))
#             if crun:
#                 t = Thread(target=self.cancel, kwargs={'style':'run'})
#                 t.start()
# #                 self._cancel_thread = t
#
#     def _truncate_button_fired(self):
#         if self.current_run:
#             self.current_run.truncate_run(self.truncate_style)
#
# #    def _show_sample_map_fired(self):
# #
# #        lm = self.experiment_queue.sample_map
# #        if lm is None:
# #            self.warning_dialog('No Tray map is set. Add "tray: <name_of_tray>" to ExperimentSet file')
# #        elif lm.ui:
# #            lm.ui.control.Raise()
# #        else:
# #            self.open_view(lm)
#
# #===============================================================================
# # property get/set
# #===============================================================================
#     def _get_execute_label(self):
#         return 'Start Queue' if not self._alive else 'Stop Queue'
#
# #     def _get_refresh_label(self):
# #         return 'Reset Queue' if self._was_executed else 'Refresh Queue'
# #    def _get_edit_enabled(self):
# #        if self.selected:
# #            states = [ri.state == 'not run' for ri in self.selected]
# #            return all(states)
# #
# #    def _get_recall_enabled(self):
# #        if self.selected:
# #            if len(self.selected) == 1:
# #                return self.selected[0].state == 'success'
#
#     def _get_can_cancel(self):
#         return self.isAlive() and not self.delaying_between_runs
# #===============================================================================
# # defaults
# #===============================================================================
#     def _massspec_importer_default(self):
#         msdb = MassSpecDatabaseImporter()
#         return msdb
#
#     def _info_display_default(self):
#
#         return DisplayController(
#                                  bg_color='black',
#                                  default_color='limegreen',
#                                  max_blocks=100
#                                  )
#
#     def _monitor_default(self):
#         mon = None
#         isok = True
#         self.debug('mode={}'.format(self.mode))
#         if self.mode == 'client':
#             ip = InitializationParser()
#             exp = ip.get_plugin('Experiment', category='general')
#             monitor = exp.find('monitor')
#             host, port, kind = None, None, None
#
#             if monitor is not None:
#                 comms = monitor.find('communications')
#                 host = comms.find('host')
#                 port = comms.find('port')
#                 kind = comms.find('kind')
#
#                 if host is not None:
#                     host = host.text  # if host else 'localhost'
#                 if port is not None:
#                     port = int(port.text)  # if port else 1061
#                 if kind is not None:
#                     kind = kind.text
#
#                 mon = RemoteAutomatedRunMonitor(host, port, kind, name=monitor.text.strip())
#         else:
#             mon = AutomatedRunMonitor()
#
#         if mon is not None:
# #        mon.configuration_dir_name = paths.monitors_dir
#             isok = mon.load()
#             if isok:
#                 return mon
#             else:
#                 self.warning('no automated run monitor avaliable. Make sure config file is located at setupfiles/monitors/automated_run_monitor.cfg')
#
#     def _pyscript_runner_default(self):
#         if self.mode == 'client':
# #            em = self.extraction_line_manager
#             ip = InitializationParser()
#             elm = ip.get_plugin('Experiment', category='general')
#             runner = elm.find('runner')
#             host, port, kind = None, None, None
#
#             if runner is not None:
#                 comms = runner.find('communications')
#                 host = comms.find('host')
#                 port = comms.find('port')
#                 kind = comms.find('kind')
#
#             if host is not None:
#                 host = host.text  # if host else 'localhost'
#             if port is not None:
#                 port = int(port.text)  # if port else 1061
#             if kind is not None:
#                 kind = kind.text  # if kind else 'udp'
#
#             runner = RemotePyScriptRunner(host, port, kind)
#         else:
#             runner = PyScriptRunner()
#
#         return runner
# #============= EOF =============================================

