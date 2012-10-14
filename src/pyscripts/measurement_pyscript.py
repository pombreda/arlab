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
from traits.api import Any, on_trait_change
#============= standard library imports ========================
from pyscript import PyScript
import time
from src.pyscripts.pyscript import verbose_skip, count_verbose_skip
import os
from src.paths import paths
import random
from ConfigParser import ConfigParser
#============= local library imports  ==========================
estimated_duration_ff = 1.01

class Detector(object):
    name = None
    mass = None
    signal = None
    def __init__(self, name, mass, signal):
        self.name = name
        self.mass = mass
        self.signal = signal

from traits.api import HasTraits, Button, Dict
from traitsui.api import View
class AutomatedRun(HasTraits):
    test = Button
    traits_view = View('test')
    signals = Dict
    def _test_fired(self):
        m = MeasurementPyScript(root=os.path.join(paths.scripts_dir, 'measurement'),
                            name='measureTest.py',
                            automated_run=self
                            )
        m.bootstrap()
    #    print m._text
        m.execute()

    def do_sniff(self, ncounts, *args, **kw):
        keys = ['H2', 'H1', 'AX', 'L1', 'L2', 'CDD']
        for i in range(ncounts):
            vals = [random.random() for _ in range(len(keys))]
            self.signals = dict(zip(keys, vals))
            time.sleep(0.1)

    def set_spectrometer_parameter(self, *args, **kw):
        pass
    def set_magnet_position(self, *args, **kw):
        pass
    def activate_detectors(self, *args, **kw):
        pass
    def do_data_collection(self, *args, **kw):
        pass

class MeasurementPyScript(PyScript):
    automated_run = Any
    _time_zero = None

    _series_count = 0
    _regress_id = 0

    detector = None
    _detectors = None

    _use_abbreviated_counts = False
#    def __init__(self, *args, **kw):
#        super(MeasurementPyScript, self).__init__(*args, **kw)
#        self._detectors = dict([(k, Detector(k, m, 0)) for k, m in
#                              zip(['H2', 'H1', 'AX', 'L1', 'L2', 'CDD'],
#                                  [40, 39, 38, 37, 36, 35])
#                              ])

    def truncate(self, style=None):
        if style == 'quick':
            self._use_abbreviated_counts = True

        super(MeasurementPyScript, self).truncate(style=style)


    def _get_detectors(self):
        return self._detectors
    detector = property(fget=_get_detectors)


    def get_script_commands(self):
        cmds = ['baselines', 'position', 'set_time_zero', 'peak_center',
                 'activate_detectors', 'multicollect', 'regress', 'sniff',
                 'peak_hop',
                 'set_ysymmetry', 'set_zsymmetry', 'set_zfocus',
                 'set_extraction_lens', 'set_deflection',

                 ]
        return cmds

    def get_variables(self):
        return ['detector']

    @on_trait_change('automated_run:signals')
    def update_signals(self, obj, name, old, new):

        try:
            det = self.detector
            for k, v in new.iteritems():
                det[k].signal = v
        except AttributeError:
            pass
#===============================================================================
# commands
#===============================================================================
    @count_verbose_skip
    def sniff(self, ncounts=0, calc_time=False, integration_time=1):
        if calc_time:
            self._estimated_duration += (ncounts * integration_time * estimated_duration_ff)
            return

        if self.automated_run is None:
            return

        if not self.automated_run.do_sniff(ncounts,
                           self._time_zero,
                           series=self._series_count,

                           ):
            self.cancel()
        self._series_count += 1

    @verbose_skip
    def regress(self, *fits):
        if self.automated_run is None:
            return

        if not fits:
            fits = 'linear'

#        self.automated_run.set_regress_fits(fits, series=self._regress_id)
        self.automated_run.set_regress_fits(fits)
#        self._series_count += 3

    @verbose_skip
    def set_time_zero(self):
        self._time_zero = time.time()

    @count_verbose_skip
    def multicollect(self, ncounts=200, integration_time=1, calc_time=False):
        if calc_time:
            self._estimated_duration += (ncounts * integration_time * estimated_duration_ff)
            return

        if self.automated_run is None:
            return

#         print 'cooooll', ncounts, self._time_zero, integration_time
        if not self.automated_run.do_data_collection(ncounts, self._time_zero,
                      series=self._series_count,
                      #update_x=True
                      ):
            self.cancel()

#        self._regress_id = self._series_count
        self._series_count += 4

    @verbose_skip
    def activate_detectors(self, *dets):
        if self.automated_run is None:
            return

        if dets:
            self._detectors = dict()
            self.automated_run.activate_detectors(list(dets))
            for di in list(dets):
                self._detectors[di] = 0
#    @verbose_skip
#    def set_isotopes(self, *isotopes):
#        if self.automated_run is None:
#            return
#        if isotopes:
#            self.automated_run.set_isotopes(list(isotopes))

    @count_verbose_skip
    def baselines(self, counts=1, cycles=5, mass=None, detector='', calc_time=False):
        '''
            if detector is not none then it is peak hopped
        '''
        if calc_time:
            if not detector:
                ns = counts
            else:
                ns = counts * cycles

            self._estimated_duration += ns * estimated_duration_ff
            return

        if self.automated_run is None:
            return

        if self._use_abbreviated_counts:
            counts *= 0.25

        if not self.automated_run.do_baselines(counts, self._time_zero,
                               mass,
                               detector,
                               series=self._series_count,
                               nintegrations=cycles

                              ):
            self.cancel()
        self._series_count += 1

    @count_verbose_skip
    def peak_hop(self, detector=None, isotopes=None, cycles=5, integrations=5, calc_time=False):
        if calc_time:
            self._estimated_duration += (cycles * integrations * estimated_duration_ff)
            return

        if self.automated_run is None:
            return
#        isotopes = sorted(isotopes, key=lambda k:int(k[2:4]))
        self.automated_run.do_peak_hop(detector, isotopes,
                                    cycles,
                                    integrations,
                                    self._time_zero,
                                    self._series_count
                                    )
        self._series_count += 3

    @count_verbose_skip
    def peak_center(self, detector='AX', isotope='Ar40', calc_time=False):
        if calc_time:
            self._estimated_duration += 45
            return

        if self.automated_run is None:
            return

        self.automated_run.do_peak_center(detector=detector, isotope=isotope)

    @verbose_skip
    def position(self, pos, detector='AX', dac=False):
        '''
            position(4.54312, dac=True) # detector is not relevant
            position(39.962, detector='AX')
            position('Ar40', detector='AX') #Ar40 will be converted to 39.962 use mole weight dict
            
        '''

        if self.automated_run is None:
            return
        self.automated_run.set_position(pos, detector, dac=dac)

    @verbose_skip
    def set_ysymmetry(self, v):
        if self.automated_run is None:
            return

        self.automated_run.set_spectrometer_parameter('SetYSymmetry', v)

    @verbose_skip
    def set_zsymmetry(self, v):
        if self.automated_run is None:
            return

        self.automated_run.set_spectrometer_parameter('SetZSymmetry', v)

    @verbose_skip
    def set_zfocus(self, v):
        if self.automated_run is None:
            return

        self.automated_run.set_spectrometer_parameter('SetZFocus', v)

    @verbose_skip
    def set_extraction_lens(self, v):
        if self.automated_run is None:
            return

        self.automated_run.set_spectrometer_parameter('SetExtractionLens', v)

    @verbose_skip
    def set_deflection(self, detname, v):
        if self.automated_run is None:
            return

        v = '{},{}'.format(detname, v)
        self.automated_run.set_spectrometer_parameter('SetDeflection', v)

    @verbose_skip
    def set_source_optics_from_file(self):
        ''' 
        '''
        attrs = ['YSymmetry', 'ZSymmetry', 'ZFocus', 'ExtractionLens']
        self._set_from_file(attrs, 'SourceOptics')

    @verbose_skip
    def set_cdd_operating_voltage_from_file(self):
        config = self._get_config()

        v = config.getfloat('CDDParameters', 'OperatingVoltage')
        if v is not None:
            func = self.automated_run.set_spectrometer_parameter
            func('SetOperatingVoltage', '{},{}'.format('CDD', v))

    @verbose_skip
    def set_source_parameters_from_file(self):
        '''            
        '''
        attrs = ['IonRepeller', 'ElectronVolts']
        self._set_from_file(attrs, 'SourceParameters')

    @verbose_skip
    def set_deflections_from_file(self):
        func = self.automated_run.set_spectrometer_parameter

        config = self._get_config()
        section = 'Deflections'
        dets = config.options(section)
        for dn in dets:
            v = config.getfloat(section, dn)
            if v is not None:
                func('SetDeflection', '{},{}'.format(dn, v))

    def _set_from_file(self, attrs, section):
        func = self.automated_run.set_spectrometer_parameter
        config = self._get_config()
        for attr in attrs:
            v = config.getfloat(section, attr)
            if v is not None:
                func('Set{}'.format(attr), v)

    def _get_config(self):
        config = ConfigParser()
        p = os.path.join(paths.spectrometer_dir, 'config.cfg')
        config.read(p)

        return config
if __name__ == '__main__':
    from src.helpers.logger_setup import logging_setup
    paths.build('_test')
    logging_setup('m_pyscript')

    d = AutomatedRun()
    d.configure_traits()

#============= EOF =============================================
