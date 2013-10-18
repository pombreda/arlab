#===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Any, Float, DelegatesTo, Int, List, Bool
from traitsui.api import View, Item, EnumEditor, Group, HGroup, spring, ButtonEditor
from pyface.timer.do_later import do_after
#============= standard library imports ========================
from numpy import linspace, exp, hstack, array
import random
import time
from threading import Event
#============= local library imports  ==========================
from spectrometer_task import SpectrometerTask
from src.globals import globalv
from src.ui.gui import invoke_in_main_thread


def multi_peak_generator(values):
    for v in values:
        m = 0.1
        if 4.8 <= v <= 5.2:
            m = 3
        elif 5.5 <= v <= 5.8:
            m = 9
        elif 6.1 <= v <= 7:
            m = 6

        yield m + random.random() / 5.0


def psuedo_peak(center, start, stop, step, magnitude=500, peak_width=0.008):
    x = linspace(start, stop, step)
    gaussian = lambda x: magnitude * exp(-((center - x) / peak_width) ** 2)

    for i, d in enumerate(gaussian(x)):
        if abs(center - x[i]) < peak_width:
        #            d = magnitude
            d = magnitude + magnitude / 50.0 * random.random()
        yield d


class MagnetScan(SpectrometerTask):
#    graph = Any
    detectors = DelegatesTo('spectrometer')
    reference_detector = Any
    additional_detectors = List
    #    execute = Event
    #    execute_label = Property(depends_on='_alive')
    #    _alive = Bool

    start_mass = Float(36)
    stop_mass = Float(40)
    step_mass = Float(1)
    period = Int(900)
    normalize = Bool(True)

    verbose = False

    def _scan_dac(self, values, det=None):
        if det is None:
            det = self.reference_detector

        if self.spectrometer.simulation:
            self._peak_generator = psuedo_peak(values[len(values) / 2] + 0.001, values[0], values[-1], len(values))
            #self._peak_generator= multi_peak_generator(values)

        gen = (vi for vi in values)
        evt = Event()
        intensities = []
        mag = self.spectrometer.magnet

        invoke_in_main_thread(self._iter_dac, mag, gen.next(),
                              gen, evt, intensities)

        while not evt.isSet():
            time.sleep(0.01)

        return True

    def _iter_dac(self, mag, di, gen, evt, intensities):

        mag.set_dac(di, verbose=self.verbose)

        d = self._magnet_step_hook()

        self._graph_hook(di, d)

        intensities.append(d)

        try:
            di = gen.next()
        except StopIteration:
            di = None

        if di is not None and self.isAlive():
            p = self.period
            do_after(p, self._iter_dac, mag, di, gen, evt, intensities)
        else:
            evt.set()

    def _update_graph_data(self, plot, di, intensity, **kw):
        """
            add and scale scans
        """

        def set_data(k, v):
            plot.data.set_data(k, v)

        def get_data(k):
            return plot.data.get_data(k)

        R = None
        r = None

        for i, v in enumerate(intensity):
            oys = None
            k = 'odata{}'.format(i)
            if hasattr(plot, k):
                oys = getattr(plot, k)

            oys = array([v]) if oys is None else hstack((oys, v))
            setattr(plot, k, oys)

            if i == 0:
                # calculate ref range
                miR = min(oys)
                maR = max(oys)
                R = maR - miR
            else:
                mir = min(oys)
                mar = max(oys)
                r = mar - mir

            if r and R and self.normalize:
                oys = (oys - mir) * R / r + miR

            xs = get_data('x{}'.format(i))
            xs = hstack((xs, di))
            set_data('x{}'.format(i), xs)
            set_data('y{}'.format(i), oys)

    def _graph_hook(self, di, intensity, **kw):
        graph = self.graph
        if graph:
            plot = graph.plots[0]
            self._update_graph_data(plot, di, intensity)

    def _magnet_step_hook(self):
        spec = self.spectrometer
        #if detector:
        #    ds = [str(detector)]
        #else:
        ds = [str(self.reference_detector)] + self.additional_detectors
        #        spec.magnet.set_dac(di, verbose=False)
        #        if delay:
        #            time.sleep(delay)
        intensity = spec.get_intensity(ds)

        #            debug
        if globalv.experiment_debug:
            from numpy import array, random, ones

            v = self._peak_generator.next()
            v = array([v])

            r = ones(len(ds))
            #             r = random.random(len(ds))
            r = r * v
            if len(r) > 1:
                r[1] *= 0.5
                if len(r) > 2:
                    r[2] *= 0.1

            intensity = r
            #             intensity = (intensity,) * len(ds)

        return intensity

    def _execute(self):
        sm = self.start_mass
        em = self.stop_mass
        stm = self.step_mass

        self.verbose = True
        if abs(sm - em) > stm:
            self._do_scan(sm, em, stm)
            self._alive = False
            self._post_execute()

        self.verbose = False

    def _do_scan(self, sm, em, stm, directions=None, map_mass=True):
        self.debug('_do_scan')
        # default to forward scan
        if directions is None:
            directions = [1]
        elif isinstance(directions, str):
            if directions == 'Decrease':
                directions = [-1]
            elif directions == 'Oscillate':
                def oscillate():
                    i = 0
                    while 1:
                        if i % 2 == 0:
                            yield 1
                        else:
                            yield -1
                        i += 1

                directions = oscillate()
            else:
                directions = [1]

        spec = self.spectrometer
        mag = spec.magnet
        if map_mass:
            ds = spec.correct_dac(self.reference_detector,
                                  mag.map_mass_to_dac(sm))
            de = spec.correct_dac(self.reference_detector,
                                  mag.map_mass_to_dac(em))


            #        de = mag.calculate_dac(em)
            massdev = abs(sm - em)
            dacdev = abs(ds - de)

            stm = stm / float(massdev) * dacdev
            sm, em = ds, de

        for di in directions:
            if not self._alive:
                return

            if di == -1:
                sm, em = em, sm
            values = self._calc_step_values(sm, em, stm)

            if not self._scan_dac(values):
                return

        return True

    def _post_execute(self):
        self.debug('scan finished')

    def _reference_detector_default(self):
        return self.detectors[0]

    def edit_view(self):
        v = self.traits_view()
        v.title = self.title
        v.buttons = ['OK', 'Cancel']
        return v

    def traits_view(self):
        v = View(
            Group(
                Item('reference_detector', editor=EnumEditor(name='detectors')),
                Item('start_mass', label='Start'),
                Item('stop_mass', label='Stop'),
                Item('step_mass', label='Step'),
                Item('period', label='Scan Period (ms)'),
                HGroup(spring, Item('execute_button', editor=ButtonEditor(label_value='execute_label'),
                                    show_label=False)),
                label='Magnet Scan',
                show_border=True
            )
            #                 buttons=['OK', 'Cancel'],
            #                 title=self.title
            #                  HGroup(spring, Item('execute', editor=ButtonEditor(label_value='execute_label'),
            #                        show_label=False))

        )
        return v

#============= EOF =============================================
        #    title = 'Magnet Scan'
        #    def _scan_dac(self, values, det, delay=850):
        #
        #        graph = self.graph
        #        spec = self.spectrometer
        #
        #        mag = spec.magnet
        #        mag.settling_time = 0.5
        #        if globalv.experiment_debug:
        #            delay = 1
        #            mag.settling_time = 0.001
        #
        #        peak_generator = psuedo_peak(values[len(values) / 2] + 0.001, values[0], values[-1], len(values))
        #
        #        do = values[0]
        #        mag.set_dac(do, verbose=False)
        #        time.sleep(delay / 1000.)
        #
        #        intensity = spec.get_intensity(det)
        #        if globalv.experiment_debug:
        #            intensity = peak_generator.next()
        #        intensities = [intensity]
        #
        # #        if graph:
        # #            graph.add_datum(
        # #                            (do, intensity),
        # ##                            update_y_limits=True,
        # #                            do_after=1)
        #
        #        for di in values[1:]:
        #            if not self.isAlive():
        #                break
        #
        #            mag.set_dac(di, verbose=False)
        #
        #            intensity = spec.get_intensity(det)
        #
        # #            debug
        #            if globalv.experiment_debug:
        #                intensity = peak_generator.next()
        #
        #            intensities.append(intensity)
        #            if graph:
        #                graph.add_datum(
        #                                (di, intensity),
        #                                update_y_limits=True,
        #                                do_after=1)
        #
        #            time.sleep(delay / 1000.)
        #
        #        return intensities

        #     def _scan_dac(self, values, det, start_delay=3):
        #         '''
        #             period: ms between steps
        #             start_delay: wait start_delay s after first step before first measurement.
        #
        #
        #         '''
        #
        #         spec = self.spectrometer
        #
        #         mag = spec.magnet
        #         mag.settling_time = 0.25
        #
        #         period = self.period
        #         if globalv.experiment_debug:
        #             period = 50
        # #             mag.settling_time = 0.5
        #
        #         peak_generator = psuedo_peak(values[len(values) / 2] + 0.001, values[0], values[-1], len(values))
        #
        #         do = values[0]
        #         mag.set_dac(do, verbose=False)
        #         intensities = self._magnet_step_hook(
        # #                                             do,
        # #                                             period=start_delay,
        #                                              detector=det,
        #                                              peak_generator=peak_generator)
        #
        #         invoke_in_main_thread(self._graph_hook, do, intensities)
        #         rintensities = [intensities]
        #
        #         period = period / 1000.
        #         for di in values[1:]:
        #             if not self.isAlive():
        #                 break
        #
        #             mag.set_dac(di, verbose=False)
        #             if period:
        #                 time.sleep(period)
        #
        #             intensities = self._magnet_step_hook(detector=det,
        #                                                  peak_generator=peak_generator)
        #             rintensities.append(intensities)
        #
        #             invoke_in_main_thread(self._graph_hook, di, intensities,
        #                                   update_y_limits=True)
        # #             self._graph_hook(di, intensities, update_y_limits=True)
        #
        #
        #         return rintensities