#===============================================================================
# Copyright 2011 Jake Ross
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
from traits.api import  Instance, Int, Property, List, \
    Any, Enum, Str, DelegatesTo, Event, Bool

#============= standard library imports ========================
from ConfigParser import ConfigParser
import os
#============= local library imports  ==========================
from src.spectrometer.source import Source
from src.spectrometer.magnet import Magnet
from src.spectrometer.detector import Detector
from src.spectrometer.spectrometer_device import SpectrometerDevice
from src.constants import NULL_STR
from src.database.isotope_database_manager import IsotopeDatabaseManager
from src.paths import paths

DETECTOR_ORDER = ['H2', 'H1', 'AX', 'L1', 'L2', 'CDD']
debug = False


class Spectrometer(SpectrometerDevice):
    magnet = Instance(Magnet)
    source = Instance(Source)

    detectors = List(Detector)

    microcontroller = Any
    integration_time = Enum(0.065536, 0.131072, 0.262144, 0.524288,
                            1.048576, 2.097152, 4.194304, 8.388608,
                            16.777216, 33.554432, 67.108864)

    reference_detector = Str('H1')

    magnet_dac = DelegatesTo('magnet', prefix='dac')

    magnet_dacmin = DelegatesTo('magnet', prefix='dacmin')
    magnet_dacmax = DelegatesTo('magnet', prefix='dacmin')

    current_hv = DelegatesTo('source')
    scan_timer = None


    molecular_weight = Str('Ar40')
    molecular_weights = None
    sub_cup_configurations = List

    sub_cup_configuration = Property(depends_on='_sub_cup_configuration')
    _sub_cup_configuration = Str

    dc_start = Int(0)
    dc_stop = Int(500)
    dc_step = Int(50)
    dc_stepmin = Int(1)
    dc_stepmax = Int(1000)
    dc_threshold = Int(3)
    dc_npeak_centers = Int(3)

    _alive = False
    intensity_dirty = Event

    testcnt = 0
    send_config_on_startup = Bool

    def send_configuration(self):
        '''
            send the configuration values to the device
        '''
        self._send_configuration()

    def set_parameter(self, name, v):
        cmd = '{} {}'.format(name, v)
        self.ask(cmd)

    def get_parameter(self, cmd):
        return self.ask(cmd)

    def set_microcontroller(self, m):
        self.debug('set microcontroller {}'.format(m))
        self.magnet.microcontroller = m
        self.source.microcontroller = m
        self.microcontroller = m
        for d in self.detectors:
            d.microcontroller = m
            d.load()

    def get_detector(self, name):
        if not isinstance(name, str):
            name = str(name)

        return next((det for det in self.detectors if det.name == name), None)
#    def get_hv_correction(self, current=False):
#        cur = self.source.current_hv
#        if current:
#            cur = self.source.read_hv()
#
#        if cur is None:
#            cor = 1
#        else:
#            cor = self.source.nominal_hv / cur
#        return cor

#    def get_relative_detector_position(self, det):
#        '''
#            return position relative to ref detector in dac space
#        '''
#        if det is None:
#            return 0
#        else:
#            return 0

#    def set_magnet_position(self, pos, detector=None):
#        #calculate the dac value for pos is on the reference detector
#        #the mftable should be set to the ref detector
#        dac = self.magnet.calculate_dac(pos)
#
#        #correct for detector
#        #calculate the dac so that this position is shifted onto the given
#        #detector.
# #        dac += self.get_detector_position(detector)
#
#        #correct for deflection
#        self.magnet.dac = dac
#
#        #correct for hv
#        dac *= self.get_hv_correction(current=True)

#===============================================================================
# change handlers
#===============================================================================
#    def _molecular_weight_changed(self):
#        self.set_magnet_position(MOLECULAR_WEIGHTS[self.molecular_weight])

#    def _integration_time_changed(self):
#        if self.microcontroller:
#            self.microcontroller.ask('SetIntegrationTime {}'.format(self.integration_time))
#            self.reset_scan_timer()

#===============================================================================
# timers
#===============================================================================

#    def reset_scan_timer(self):
#        if self.scan_timer is not None:
#            self.scan_timer.Stop()
#        self._timer_factory()
#
#    def stop(self):
#        if self._alive == True:
#            self.info('Calibration canceled by user')
#            self._alive = False
#            return False
#        else:
#            self._alive = False
#            return True
#        if self.centering_timer and self.centering_timer.IsRunning():
#            self.centering_timer.Stop()
#            self.info('Peak centering stopped by user')
#            self._timer_factory()
#        else:
#            return True
#===============================================================================
# peak centering
#===============================================================================
    def isAlive(self):
        return self._alive


    def update_isotopes(self, isotope, detector):

        if isotope != NULL_STR:
            det = self.get_detector(detector)
            det.isotope = isotope
            index = self.detectors.index(det)

            nmass = int(isotope[2:])
            for i, di in enumerate(self.detectors):
                mass = nmass - (i - index)
                di.isotope = 'Ar{}'.format(mass)


#===============================================================================
# property get/set
#===============================================================================

    def _get_detectors(self):
        ds = []
        for di in DETECTOR_ORDER:
            ds.append(self._detectors[di])
        return ds

    def _get_sub_cup_configuration(self):
        return self._sub_cup_configuration

    def _set_sub_cup_configuration(self, v):
        self._sub_cup_configuration = v
        self.microcontroller.ask('SetSubCupConfiguration {}'.format(v))


#===============================================================================
# load
#===============================================================================
    def load_configurations(self):
        self.sub_cup_configurations = ['A', 'B', 'C']
        self._sub_cup_configuration = 'B'
        if self.microcontroller is not None:

            scc = self.microcontroller.ask('GetSubCupConfigurationList Argon', verbose=False)
            if scc:
                if 'ERROR' not in scc:
                    self.sub_cup_configurations = scc.split('\r')

            n = self.microcontroller.ask('GetActiveSubCupConfiguration')
            if n:
                if 'ERROR' not in n:
                    self._sub_cup_configuration = n

        self.molecular_weight = 'Ar40'

    def load(self):

        # get the molecular weights from the database
        dbm = IsotopeDatabaseManager(application=self.application,
                                     warn=False)

        if dbm.isConnected():
            self.info('loading molecular_weights from database')
            mws = dbm.db.get_molecular_weights()
            # convert to a dictionary
            m = dict([(mi.name, mi.mass) for mi in mws])
            self.molecular_weights = m

        else:
            import csv
            # load the molecular weights dictionary
            p = os.path.join(paths.spectrometer_dir, 'molecular_weights.csv')
            if os.path.isfile(p):
                self.info('loading "molecular_weights.csv" file')
                with open(p, 'U') as f:
                    reader = csv.reader(f, delimiter='\t')
                    args = [[l[0], float(l[1])] for l in reader]
                    self.molecular_weights = dict(args)
            else:
                self.info('writing a default "molecular_weights.csv" file')
                # make a default molecular_weights.csv file
                from src.spectrometer.molecular_weights import MOLECULAR_WEIGHTS as mw
                with open(p, 'U') as f:
                    writer = csv.writer(f, delimiter='\t')
                    data = [a for a in mw.itervalues()]
                    data = sorted(data, key=lambda x: x[1])
                    for row in data:
                        writer.writerow(row)
                self.molecular_weights = mw

        self.magnet.load()

    def finish_loading(self):
        self.magnet.finish_loading()

        if self.send_config_on_startup:
            # write configuration to spectrometer
            self._send_configuration()


    def add_detector(self, **kw):
        d = Detector(spectrometer=self,
                     **kw)
        self.detectors.append(d)

#===============================================================================
# signals
#===============================================================================
    def get_intensities(self, record=True, tagged=True):
        keys, signals = None, None
        if self.microcontroller:
            datastr = self.microcontroller.ask('GetData', verbose=False)
            keys = []
            signals = []
            if datastr:
                if not 'ERROR' in datastr:
                    try:
                        data = [float(d) for d in datastr.split(',')]
                    except:

                        if tagged:
                            data = [d for d in datastr.split(',')]

                            keys = [data[i] for i in range(0, len(data), 2)]
                            signals = map(float, [data[i + 1] for i in range(0, len(data), 2)])

        if not keys:
#             signals = [(ns + self.testcnt * 0.1) + random.random()
#                         for ns in [1, 100, 3, 1, 1, 0]]
            signals = [1, 100, 3, 0, 0, 0.01]


#             signals = [(i * 2 + self.testcnt * 0.1) + random.random() for i in range(6)]
            self.testcnt += 1
            if tagged:
                keys = ['H2', 'H1', 'AX', 'L1', 'L2', 'CDD']

        self.intensity_dirty = dict(zip(keys, signals))
        return keys, signals

    def get_intensity(self, dkeys):
        '''
            dkeys: str or tuple of strs
            
        '''
#        index = DETECTOR_ORDER.index(key)
        data = self.get_intensities()
        if data is not None:
            keys, signals = data

            if isinstance(dkeys, (tuple, list)):
                return [signals[keys.index(key)] for key in dkeys]
            else:
                return signals[keys.index(dkeys)]

    def get_hv_correction(self, current=False):
        source = self.source
        cur = source.current_hv
        if current:
            cur = source.read_hv()

        if cur is None:
            cor = 1
        else:
            cor = source.nominal_hv / cur
        return cor

    def correct_dac(self, det, dac):
#        dac is in axial units

#        convert to detector
        dac *= det.relative_position

        '''
        convert to axial detector 
        dac_a=  dac_d / relpos
        
        relpos==dac_detA/dac_axial 
        
        '''
        # correct for deflection
        dev = det.get_deflection_correction()

        dac += dev

#        #correct for hv
        dac *= self.get_hv_correction(current=True)
        return dac

    def uncorrect_dac(self, det, dac):
        dac /= self.get_hv_correction()
        dev = det.get_deflection_correction()
        dac -= dev
        dac /= det.relative_position
        return dac

#===============================================================================
# private
#===============================================================================

    def _send_configuration(self):
        COMMAND_MAP = dict(ionrepeller='IonRepeller',
                         electronenergy='ElectronEnergy',
                         ysymmetry='YSymmetry',
                         zsymmetry='ZSymmetry',
                         zfocus='ZFocus',
                         extractionlens='ExtractionLens',
                         ioncountervoltage='IonCounterVoltage'
                         )

        self.debug('Sending configuration to spectrometer')
        if self.microcontroller:

            p = os.path.join(paths.spectrometer_dir, 'config.cfg')
            config = ConfigParser()
            config.read(p)

            for section in config.sections():
                for attr in config.options(section):
                    v = config.getfloat(section, attr)
                    if v is not None:

                        if section == 'Deflections':
                            cmd = 'SetDeflection'
                            v='{},{}'.format(attr.upper(), v)
                        else:
                            cmd = 'Set{}'.format(COMMAND_MAP[attr])

                        self.set_parameter(cmd, v)

#===============================================================================
# defaults
#===============================================================================
    def _magnet_default(self):
        return Magnet(spectrometer=self)

    def _source_default(self):
        return Source(spectrometer=self)

#============= EOF =============================================
#    def _peak_center_scan_step(self, di, graph, plotid, cond):
# #       3print cond
#        if self.first:
#            self.first = False
#            x = di
#            cond.acquire()
#        else:
#            x = self.x
#        data = self.get_intensities()
#        if data is not None:
#            if self.simulation:
#                intensity = self.peak_generator.next()
#            else:
#                intensity = data[DETECTOR_ORDER.index(self.reference_detector)]
#
#            self.intensities.append(intensity)
#            graph.add_datum((x, intensity), plotid = plotid, update_y_limits = True)
#
#        try:
#            x = self.gen.next()
#        except StopIteration:
#            try:
#                cond.notify()
#                cond.release()
#            finally:
#                raise StopIteration
#
#        self.x = x
#        self.magnet.set_dac(x)
#    def _peak_center(self, graph, update_mftable, update_pos, center_pos):

#    def _peak_center_scan(self, start, end, step_len, graph, ppc = 40, plotid = 0):
#
#        #stop the scan timer and use peak scan timer
#        self.intensities = []
#        sign = 1 if start < end else - 1
#        nsteps = abs(end - start + step_len * sign) / step_len
#        dac_values = np.linspace(start, end, nsteps)
#        self.peak_generator = psuedo_peak(ppc, start, end, nsteps)
#
#        self.first = True
#        self.x = 0
#        self.gen = (i for i in dac_values)
#        period = self.integration_time * 1000
#        if self.simulation:
#            period = 150
#
#        #do first dac move
# #        di = self.gen.next()
# #        self.magnet.set_dac(di)
# #        time.sleep(2)
#
#        if self.scan_timer.IsRunning():
#            self.scan_timer.Stop()

#        t = Thread(target = self.scan, args = (dac_values, graph))
#        t.start()
#        t.join()
#===============================================================================
# old
#===============================================================================
#        if self.condition is None:
#            cond = Condition()
#        with cond:
#            if self.centering_timer is not None:
#                self.centering_timer.Stop()
#
#            self.centering_timer = Timer(period, self._peak_center_scan_step, di, graph, plotid, cond)
#            self.centering_timer.Start()
#
#            cond.wait()
#===============================================================================
# old end
#===============================================================================

        # restart the scan timer
#        self._timer_factory()
#
#        return self.finish_peak_center(graph, dac_values, self.intensities)
