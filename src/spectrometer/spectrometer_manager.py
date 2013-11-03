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
from traits.api import Instance, Any, Property
#============= standard library imports ========================
import os
#============= local library imports  ==========================
from src.database.isotope_database_manager import IsotopeDatabaseManager
from src.managers.manager import Manager
from src.spectrometer.spectrometer import Spectrometer
from src.paths import paths
from src.spectrometer.jobs.relative_detector_positions import RelativeDetectorPositions
from src.spectrometer.jobs.coincidence_scan import CoincidenceScan
from src.spectrometer.jobs.cdd_operating_voltage_scan import CDDOperatingVoltageScan
from apptools.preferences.preference_binding import bind_preference
from src.spectrometer.spectrometer_parameters import SpectrometerParameters, \
    SpectrometerParametersView


class SpectrometerManager(Manager):
    spectrometer = Instance(Spectrometer)
    spectrometer_microcontroller = Any
    name = Property(depends_on='spectrometer_microcontroller')

    def _spectrometer_default(self):
        return Spectrometer(application=self.application)

    def open_parameters(self):
        p = SpectrometerParameters(spectrometer=self.spectrometer)
        p.load()

        v = SpectrometerParametersView(model=p)
        v.edit_traits()

    def make_parameters_dict(self):
        spec = self.spectrometer
        d = dict()
        for attr, cmd in [('extraction_lens', 'ExtractionLens'), ('ysymmetry', 'YSymmetry'),
                          ('zsymmetry', 'ZSymmetry'), ('zfocus', 'ZFocus')
        ]:
            v = spec.get_parameter('Get{}'.format(cmd))
            if v is not None:
                d[attr] = v

        return d

    def make_deflections_dict(self):
        spec = self.spectrometer
        d = dict()
        for di in spec.detectors:
            d[di.name] = di.read_deflection()
        return d

    def load(self, db_mol_weights=True):
        self.debug('******************************* LOAD Spec')
        if db_mol_weights:
            # get the molecular weights from the database
            dbm = IsotopeDatabaseManager(application=self.application,
                                         warn=False)
            self.db = dbm
            if dbm.isConnected():
                self.info('loading molecular_weights from database')
                mws = dbm.db.get_molecular_weights()
                # convert to a dictionary
                m = dict([(mi.name, mi.mass) for mi in mws])
                self.spectrometer.molecular_weights = m

        if not self.spectrometer.molecular_weights:
            import csv
            # load the molecular weights dictionary
            p = os.path.join(paths.spectrometer_dir, 'molecular_weights.csv')
            if os.path.isfile(p):
                self.info('loading "molecular_weights.csv" file')
                with open(p, 'U') as f:
                    reader = csv.reader(f, delimiter='\t')
                    args = [[l[0], float(l[1])] for l in reader]
                    self.spectrometer.molecular_weights = dict(args)
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
                self.spectrometer.molecular_weights = mw

        #config = self.get_configuration(path=os.path.join(paths.spectrometer_dir, 'detectors.cfg'))
        #for name in config.sections():
        #    relative_position = self.config_get(config, name, 'relative_position', cast='float')
        #    color = self.config_get(config, name, 'color', default='black')
        #    default_state = self.config_get(config, name, 'default_state', default=True, cast='boolean')
        #    isotope = self.config_get(config, name, 'isotope')
        #    kind = self.config_get(config, name, 'kind', default='Faraday', optional=True)
        #    self.spectrometer.add_detector(name=name,
        #                                   relative_position=relative_position,
        #                                   color=color,
        #                                   active=default_state,
        #                                   isotope=isotope,
        #                                   kind=kind)
        self.spectrometer.load()

        return True

    def finish_loading(self):
        integration_time = 1.048576

        # set device microcontrollers
        self.spectrometer.set_microcontroller(self.spectrometer_microcontroller)

        # update the current hv
        self.spectrometer.source.sync_parameters()

        # set integration time
        self.integration_time = integration_time
        # self.integration_time = 0.065536

        self.spectrometer.load_configurations()

        bind_preference(self.spectrometer, 'send_config_on_startup',
                        'pychron.spectrometer.send_config_on_startup')
        self.spectrometer.finish_loading()

    def relative_detector_positions_task_factory(self):
        return self._factory(RelativeDetectorPositions)

    def do_coincidence_scan(self):
        obj = self._factory(CoincidenceScan)
        obj.inform = False
        self.open_view(obj.graph)
        t = obj.execute()
        return obj, t

    def coincidence_scan_task_factory(self):
        obj = self._factory(CoincidenceScan)
        info = obj.edit_traits(view='edit_view',
                               kind='livemodal')
        if info.result:
            self.open_view(obj.graph)
            obj.execute()

    def cdd_operate_voltage_scan_task_factory(self):
        obj = CDDOperatingVoltageScan(spectrometer=self.spectrometer)
        info = obj.edit_traits(kind='livemodal')
        if info.result:
            self.open_view(obj.graph)
            obj.execute()

    def _factory(self, klass):
        ion = self.application.get_service('src.spectrometer.ion_optics_manager.IonOpticsManager')
        return klass(spectrometer=self.spectrometer, ion_optics_manager=ion)

    def _get_name(self):
        r = ''
        if self.spectrometer_microcontroller:
            r = self.spectrometer_microcontroller.name
        return r

        #    def _spectrometer_microcontroller_default(self):

#        return ArgusController()

if __name__ == '__main__':
    from src.helpers.logger_setup import logging_setup

    logging_setup('spectrometer')
# #    s = SpectrometerManager()
#    ini = Initializer()
#    ini.add_initialization(dict(name='spectrometer_manager',
#                                manager=s
#                                ))
#    ini.run()
# #    s.magnet_field_calibration()
#    s.configure_traits()#kind = 'live')
#============= EOF =============================================
#    def _update_hover(self, obj, name, old, new):
#        if new is not None:
#            g = Graph(container_dict=dict(padding=[30, 0, 0, 30]))
#            g.new_plot(padding=5)
#            g.new_series()
# #            root = os.path.join(data_dir, 'magfield', 'def_calibration001')
#            try:
#                p = os.path.join(self.results_root, self.center_paths[new])
#            except IndexError:
#                return
#            g.read_xy(p, header=True)
#
#            xs, ys, mx, my = self.spectrometer.calculate_peak_center(g.get_data(), g.get_data(axis=1))
#            g.new_series(x=xs, y=ys, type='scatter')
#            g.new_series(x=mx, y=my, type='scatter')
#
#            g.window_width = 250
#            g.window_height = 250
#            g.width = 200
#            g.height = 200
#            x, y = self.results_graph.current_pos
#
#            g.window_x = x + 75
#
#            g.window_y = 400 - y
#
#            g.edit_traits(kind='popover')
#
