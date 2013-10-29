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
from traits.api import Any, List, CInt, Int, Bool
# from traitsui.api import View, Item
# from pyface.timer.do_later import do_after
#============= standard library imports ========================
import time
from threading import Event, Timer
from numpy import Inf
#============= local library imports  ==========================
from src.loggable import Loggable
# from src.ui.gui import invoke_in_main_thread
from src.globals import globalv
from src.consumer_mixin import consumable
# from src.codetools.memory_usage import mem_log

class DataCollector(Loggable):
    measurement_script = Any
    plot_panel = Any
    arar_age = Any

    detectors = List
    check_conditions = Bool(True)
    truncation_conditions = List
    terminations_conditions = List
    action_conditions = List
    ncounts = CInt
    #grpname = Str

    is_baseline = Bool(False)
    fits = List
    series_idx = Int
    #total_counts = CInt

    canceled = False

    _truncate_signal = False
    starttime = None
    _alive = False
    _evt = None

    def _detectors_changed(self):
        self._idx_func = self._get_idx_func()

    def wait(self):
        st = time.time()
        self.debug('wait started')
        while 1:
            if self._evt and self._evt.set():
                break
        self.debug('wait complete {:0.1f}s'.format(time.time() - st))

    def set_truncated(self):
        self._truncate_signal = True

    def stop(self):
        self._alive = False
        if self._evt:
            self._evt.set()

    def measure(self):
        if self.canceled:
            return

        self._truncate_signal = False

        st = time.time()
        if self.starttime is None:
            self.starttime = st

        et = self.ncounts * self.period_ms * 0.001
        evt = self._evt
        if evt:
            evt.set()
            evt.wait(0.05)
        else:
            evt = Event()

        self._evt = evt
        evt.clear()

        #         wait for graphs to be fully constructed in the MainThread
        evt.wait(0.05)

        self._alive = True

        self._measure(evt, et)

        tt = time.time() - st
        self.debug('estimated time: {:0.3f} actual time: :{:0.3f}'.format(et, tt))
        #return self.total_counts

    def _measure(self, evt, et):
        self.debug('starting measurment')
        with consumable(func=self._iter_step, main=True) as con:
            self._iter(con, evt, 1)
            evt.wait(et * 1.1)
        self.debug('measurement finished')

    def _iter(self, con, evt, i, prev=0):
        if not self._check_iteration(evt, i):
            if not self._iter_hook(con, i):
                evt.set()
                return

            ot = time.time()

            p = self.period_ms * 0.001
            p -= prev
            p = max(0, p)

            #self.debug('period {} {} {}'.format(p,prev, self.period_ms))
            t = Timer(p, self._iter, args=(con, evt, i + 1,
                                           time.time() - ot))

            t.name = 'iter_{}'.format(i + 1)
            t.start()

        else:
            #self.debug('no more iter')
            evt.set()

    def _iter_hook(self, con, i):
        return True

    def _iter_step(self, data):
        pass

    def _get_data(self, dets=None):
        data = self.data_generator.next()
        if dets:
            data = zip(*[(k, s) for k, s in zip(*data)
                         if k in dets])

        return data

    def _save_data(self, x, keys, signals):
        self.data_writer(self.detectors, x, keys, signals)

    def _get_detector(self, d):
        if isinstance(d, str):
            d = next((di for di in self.detectors
                      if di.name == d), None)
        return d

    def _plot_data(self, i, x, keys, signals):
        if globalv.experiment_debug:
            x *= (self.period_ms * 0.001) ** -1

        graph = self.plot_panel.isotope_graph

        nfs = self.get_fit_block(i)
        #if self.grpname == 'signal':
        #self.plot_panel.fits = nfs

        np = len(graph.plots)
        idx_func = self._idx_func

        for dn in keys:
            dn = self._get_detector(dn)
            if dn:
                iso = dn.isotope
                pi = idx_func(iso)
                fi = nfs[pi]

                if pi >= np:
                    graph.new_plot()
                    graph.new_series(type='scatter',
                                     marker='circle',
                                     plotid=pi)
                    dn.series_idx = 0

                series = self.series_idx
                if hasattr(dn, 'series_idx'):
                    series = dn.series_idx

                miso = self.arar_age.isotopes[iso]
                if self.is_baseline:
                    miso.baseline.fit = fi
                else:
                    miso.fit = fi

                signal = signals[keys.index(dn.name)]

                #print i, x, pi, dn
                graph.add_datum((x, signal),
                                series=series,
                                plotid=pi,
                                update_y_limits=True,
                                ypadding='0.1')
                if fi:
                    graph.set_fit(fi, plotid=pi, series=0)

        graph.refresh()

    #===============================================================================
    #
    #===============================================================================
    def get_fit_block(self, iter_cnt, fits=None):
        if fits is None:
            fits = self.fits
        return self._get_fit_block(iter_cnt, fits)

    def _get_fit_block(self, iter_cnt, fits):
        midx = None
        me = -Inf
        for i, (sli, fs) in enumerate(fits):
            if sli:
                s, e = sli
                if s is None:
                    s = 0
                if e is None:
                    e = Inf

                if iter_cnt < 0:
                    if me < e:
                        me = e
                        midx = i
                else:
                    if iter_cnt > s and iter_cnt < e:
                        break

        if midx is not None:
            fs = fits[midx]

        #        self.debug('fs {}'.format(fs))
        return fs

    #===============================================================================
    # checks
    #===============================================================================
    def _check_conditions(self, conditions, cnt):
        for ti in conditions:
            if ti.check(self.arar_age, cnt):
                return ti

    def _check_iteration(self, evt, i):

    #         if self.plot_panel is None:
    #             return 'break'
        if evt:
            if evt.isSet():
                return True

        j = i - 1
        # exit the while loop if counts greater than max of original counts and the plot_panel counts
        pc = 0
        if self.plot_panel:
            pc = self.plot_panel.ncounts

        ncounts = self.ncounts
        maxcounts = max(ncounts, pc)
        if i > maxcounts:
            return 'break'

        if self.check_conditions:
            termination_condition = self._check_conditions(self.termination_conditions, i)
            if termination_condition:
                self.info('termination condition {}. measurement iteration executed {}/{} counts'.format(
                    termination_condition.message, j, ncounts),
                          color='red'
                )
                return 'cancel'

            truncation_condition = self._check_conditions(self.truncation_conditions, i)
            if truncation_condition:
                self.info('truncation condition {}. measurement iteration executed {}/{} counts'.format(
                    truncation_condition.message, j, ncounts),
                          color='red'
                )
                self.state = 'truncated'
                self.measurement_script.abbreviated_count_ratio = truncation_condition.abbreviated_count_ratio

                #                self.condition_truncated = True
                return 'break'

            action_condition = self._check_conditions(self.action_conditions, i)
            if action_condition:
                self.info(
                    'action condition {}. measurement iteration executed {}/{} counts'.format(action_condition.message,
                                                                                              j, ncounts),
                    color='red'
                )
                action_condition.perform(self.measurement_script)
                if not action_condition.resume:
                    return 'break'

        if i > self.measurement_script.ncounts:
            self.info('script termination. measurement iteration executed {}/{} counts'.format(j,
                                                                                               self.measurement_script.ncounts))
            return 'break'

        if pc:
            if i > pc:
                self.info('user termination. measurement iteration executed {}/{} counts'.format(j, ncounts))
                self.plot_panel.total_counts -= (ncounts - i)
                return 'break'

        if self._truncate_signal:
            self.info('measurement iteration executed {}/{} counts'.format(j, ncounts))
            self._truncate_signal = False

            return 'break'

        if not self._alive:
            self.info('measurement iteration executed {}/{} counts'.format(j, ncounts))
            return 'cancel'

    def _get_idx_func(self):
        original_idx = [(di.name, di.isotope) for di in self.detectors]

        def idx_func(isot):
            return next((i for i, (n, ii) in enumerate(original_idx)
                         if ii == isot), None)

        return idx_func

        #============= EOF =============================================
