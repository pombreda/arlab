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
from traits.api import Any, Str, String, Int, List, Enum, Property, \
     Event, Float, Instance, Bool, cached_property, Dict, on_trait_change
from traitsui.api import View, Item, VGroup, EnumEditor, HGroup, Group
from traitsui.tabular_adapter import TabularAdapter
from pyface.timer.do_later import do_later
#============= standard library imports ========================
import os
import time
import random
#============= local library imports  ==========================
from src.loggable import Loggable
from src.experiment.heat_schedule import HeatStep
from src.graph.stacked_graph import StackedGraph
from src.data_processing.regression.regressor import Regressor
from src.scripts.extraction_line_script import ExtractionLineScript
from src.pyscripts.measurement_pyscript import MeasurementPyScript
from src.pyscripts.extraction_line_pyscript import ExtractionLinePyScript
from src.database.adapters.isotope_adapter import IsotopeAdapter
from src.paths import paths
from src.data_processing.mass_spec_database_importer import MassSpecDatabaseImporter

class AutomatedRunAdapter(TabularAdapter):

    state_image = Property
    state_text = Property
    extraction_script_text = Property
    measurement_script_text = Property

    def _columns_default(self):
        hp = ('Temp', 'temp_or_power')
        power = True
        if power:
            hp = ('Power', 'temp_or_power')

        return  [('', 'state'), ('id', 'identifier'), ('sample', 'sample'),
               hp, ('Duration', 'duration'),
               ('Extraction', 'extraction_script'),
               ('Measurement', 'measurement_script'),
               ]
    def _get_extraction_script_text(self, trait, item):
        return self.item.extraction_script.name

    def _get_measurement_script_text(self, trait, item):
        return self.item.measurement_script.name

    def _get_state_text(self):
        return ''

    def _get_state_image(self):
        if self.item:
            im = 'gray'
            if self.item.state == 'extraction':
                im = 'yellow'
            elif self.item.state == 'measurement':
                im = 'orange'
            elif self.item.state == 'success':
                im = 'green'
            elif self.item.state == 'fail':
                im = 'red'

            #get the source path
            root = os.path.split(__file__)[0]
            while not root.endswith('src'):
                root = os.path.split(root)[0]
            root = os.path.split(root)[0]
            root = os.path.join(root, 'resources')
            return os.path.join(root, '{}_ball.png'.format(im))


class AutomatedRun(Loggable):
    spectrometer_manager = Any
    extraction_line_manager = Any
    experiment_manager = Any
    ion_optics_manager = Any
    data_manager = Any

    db = Any
    massspec_importer = Any
    runner = Any
    graph = Any

    sample = Str

    identifier = String(enter_set=True, auto_set=False)
    state = Enum('not run', 'extraction', 'measurement', 'success', 'fail')
    runtype = Enum('Blank', 'Air')
    irrad_level = Str

    heat_step = Instance(HeatStep)
    duration = Property(depends_on='heat_step,_duration')
    temp_or_power = Property(depends_on='heat_step,_temp_or_power')
    _duration = Float
    _temp_or_power = Float

    position = Int
    endposition = Int
    multiposition = Bool

    weight = Float
    comment = Str

    scripts = Dict
    signals = Dict
    sample_data_record = Any

    update = Event

    measurement_script = Property
    _measurement_script = Any


    extraction_script = Property
    _extraction_script = Any

    _active_detectors = List
    _debug = False
    _loaded = False
    configuration = None

    def get_estimated_duration(self):
        '''
            use the pyscripts to calculate etd
        '''
        s = self.duration
        ms = self.measurement_script
        if ms is not None:
            s += ms.get_estimated_duration()

        es = self.extraction_script
        if es is not None:
            s += es.get_estimated_duration()

        return s

    def get_measurement_parameter(self, key, default=None):
        ms = self.measurement_script
        import ast
        import yaml
        m = ast.parse(ms._text)
        docstr = ast.get_docstring(m)
        if docstr is not None:
            params = yaml.load(ast.get_docstring(m))
            try:
                return params[key]
            except KeyError:
                pass
            except TypeError:
                self.warning('Invalid yaml docstring in {}. Could not retrieve {}'.format(ms.name, key))

        return default

    def measurement_script_factory(self, ec):
        ec = self.configuration
        mname = os.path.basename(ec['measurement_script'])

        ms = MeasurementPyScript(root=os.path.dirname(ec['measurement_script']),
            name=mname,
            automated_run=self
            )
        return ms
#
    def extraction_script_factory(self, ec):
        #get the klass

        key = 'extraction_script'
        path = os.path

        source_dir = path.dirname(ec[key])
        file_name = path.basename(ec[key])

        if file_name.endswith('.py'):
            klass = ExtractionLinePyScript
            params = dict(root=source_dir,
                    name=file_name,)
        elif file_name.endswith('.rs'):
            klass = ExtractionLineScript
            params = dict(source_dir=source_dir,
                    file_name=file_name,)

        if klass:
            return klass(
                    hole=self.position,
                    heat_duration=self.duration,
                    temp_or_power=self.temp_or_power,
                    manager=self.extraction_line_manager,
                    runner=self.runner,
                    **params
                    )

#===============================================================================
# doers
#===============================================================================
    def do_extraction(self):
        self.info('extraction')
        self.state = 'extraction'

        self.extraction_script.execute()
        self.info('extraction finished')

    def do_measurement(self):
        #use a measurement_script to explicitly define 
        #measurement sequence

        self._pre_analysis_save()
        if self.measurement_script.execute():
            self._post_analysis_save()

        self.info('measurement finished')

    def do_data_collection(self, ncounts, starttime, series=0):

        gn = 'signals'
        self._build_tables(gn)
        self._measure_iteration(gn,
                                self._get_data_writer(gn),
                                ncounts, starttime, series)

    def do_sniff(self, ncounts, starttime, series=0):
        gn = 'sniffs'
        self._build_tables(gn)

        self._measure_iteration(gn,
                                self._get_data_writer(gn),
                                ncounts, starttime, series)

    def do_baselines(self, ncounts, starttime, detector=None,
                     position=None, series=0):
        sm = self.spectrometer_manager
        if sm:
            if position is not None:
                sm.spectrometer.set_magnet_position(position)

        gn = 'baselines'
        self._build_tables(gn)
        if detector is None:
            self._measure_iteration(gn,
                                self._get_data_writer(gn),
                                ncounts, starttime, series)
        else:
            masses = [1, 2]
            self._peak_hop(gn, detector, masses, ncounts, starttime, series)

    def do_peak_center(self, **kw):
        ion = self.ion_optics_manager
        if ion is not None:

            t = ion.do_peak_center(**kw)

            #block until finished
            t.join()

#        sm = self.spectrometer_manager
#        if sm is not None:
##            sm.spectrometer._alive = True
#            sm.peak_center(**kw)
##            sm.spectrometer._alive = False

    def set_spectrometer_parameter(self, name, v):
        self.info('setting spectrometer parameter {} {}'.format(name, v))
        sm = self.spectrometer_manager
        if sm is not None:
            sm.spectrometer.set_parameter(name, v)

    def set_position(self, pos, detector, dac=False):
        ion = self.ion_optics_manager
        if ion is not None:
            ion.position(pos, detector, dac)

#    def set_magnet_position(self, v, **kw):
#        sm = self.spectrometer_manager
#        if sm is not None:
#            sm.spectrometer.set_magnet_position(v, **kw)

    def activate_detectors(self, dets):
        g = self.graph
        if g is None:
            g = StackedGraph(
                             container_dict=dict(padding=5, bgcolor='gray',
                                                 ),
                             window_width=500,
                             window_height=700,
                             window_y=0.05 + 0.01 * self.index,
                             window_x=0.6 + 0.01 * self.index,
                             window_title='Plot Panel {}'.format(self.identifier)
                             )
            self.graph = g


            self.experiment_manager.open_view(self.graph)
#            do_later(self.graph.edit_traits)

#        dets.reverse()
        for i, l in enumerate(dets):

            l = dets[-(i + 1)]

            if not l in self._active_detectors:
                g.new_plot(ytitle='{} Signal (fA)'.format(l))
                g.new_series(type='scatter',
                             marker='circle',
                             marker_size=1.25,
                             label=l)
        g.set_x_limits(min=0, max=100)
#        dets.reverse()

#            g.new_series(type='scatter',
#                         marker='circle',
#                         marker_size=1.25,
#                         label=l, plotid=i)


        self._active_detectors = dets
#        do_later(self.experiment_manager.ui.control.Raise)

#===============================================================================
# 
#===============================================================================

    def regress(self, kind, series=0):
        r = Regressor()
        g = self.graph

        time_zero_offset = 0#int(self.experiment_manager.equilibration_time * 2 / 3.)
        n = len(self._active_detectors)

        for i, dn in enumerate(self._active_detectors):
#        for pi in range(len(g.plots)):
            pi = n - (i + 1)
            x = g.get_data(plotid=pi, series=series)[time_zero_offset:]
            y = g.get_data(plotid=pi, series=series, axis=1)[time_zero_offset:]
            x, y = zip(*zip(x, y))
            rdict = r._regress_(x, y, kind)
            self.info('{} intercept {}+/-{}'.format(dn,
                                                    rdict['coefficients'][-1],
                                                 rdict['coeff_errors'][-1]
                                                 ))
            g.new_series(rdict['x'],
                         rdict['y'],
                         plotid=pi, color='black')
            kw = dict(color='red',
                         line_style='dash',
                         plotid=pi)

            g.new_series(rdict['upper_x'],
                         rdict['upper_y'],
                         **kw
                         )
            g.new_series(rdict['lower_x'],
                         rdict['lower_y'],
                         **kw
                         )
            g.redraw()

    def _state_changed(self):
        #update the analysis table
        self.update = True

    def _build_tables(self, gn):
        dm = self.data_manager
        #build tables
        for di in self._active_detectors:
            dm.new_table('/{}'.format(gn), di)

    def _peak_hop(self, name, detector, masses, ncounts, starttime, series):
        self.info('peak hopping {} detector={}'.format(name, detector))
        spec = None
        sm = self.spectrometer_manager
        if sm:
            spec = sm.spectrometer

        for i in xrange(0, ncounts, 1):
            for mi, mass in enumerate(masses):
                ti = self.integration_time * 0.99 if not self._debug else 0.01
                time.sleep(ti)
                if spec is not None:
                    #position mass m onto detector
                    spec.set_magnet_position()

                x = time.time() - starttime
#                if i % 100 == 0 or x > self.graph.get_x_limits()[1]:
                print x, self.graph.get_x_limits()[1]
                if x > self.graph.get_x_limits()[1]:
                    self.graph.set_x_limits(0, x + 10)

                signals = [1200 * (1 + random.random()),
                        3.5 * (1 + random.random())]

                v = signals[mi]

                kw = dict(series=series, do_after=1,)
#                print len(self.graph.series[mi])
                if len(self.graph.series[mi]) < series + 1:
                    kw['marker'] = 'circle'
                    kw['type'] = 'scatter'
                    kw['marker_size'] = 1.25
                    self.graph.new_series(x=[x], y=[v], plotid=mi, **kw)
                else:
                    self.graph.add_datum((x, v), plotid=mi, ** kw)

    def _measure_iteration(self, grpname, data_write_hook,
                           ncounts, starttime, series):

        self.info('measuring {}'.format(grpname))

        spec = self.spectrometer_manager.spectrometer

        for i in xrange(0, ncounts, 1):
            if i % 50 == 0:
                self.info('collecting point {}'.format(i + 1))

            m = self.integration_time * 0.99 if not self._debug else 0.01
            time.sleep(m)

            if not self._debug:
                data = spec.get_intensities(tagged=True)
                if data is not None:
                    keys, signals = data
#                keys, signals = zip(*data)
            else:
                keys = ['H2', 'H1', 'AX', 'L1', 'L2', 'CDD']

                if series == 0:
                    signals = [10, 1000, 8, 8, 8, 3]
                elif series == 1:
                    r = random.randint(0, 75)
                    signals = [0.1, (0.015 * (i - 2800 + r)) ** 2,
                               0.1, 1, 0.1, (0.001 * (i - 2000 + r)) ** 2
                               ]
                else:
                    signals = [1, 2, 3, 4, 5, 6]

            x = time.time() - starttime# if not self._debug else i + starttime
            data_write_hook(x, keys, signals)

            self.signals = dict(zip(keys, signals))

            kw = dict(series=series, do_after=1, update_y_limits=True)
            if len(self.graph.series[0]) < series + 1:
                kw['marker'] = 'circle'
                kw['type'] = 'scatter'
                kw['marker_size'] = 1.25
                func = lambda x, signal, kw: self.graph.new_series(x=[x],
                                                                 y=[signal],
                                                                 **kw
                                                                 )
            else:
                func = lambda x, signal, kw: self.graph.add_datum((x, signal), **kw)
            dets = self._active_detectors
            n = len(dets)
            for pi, dn in enumerate(dets):
                signal = signals[keys.index(dn)]
                kw['plotid'] = n - (pi + 1)
                func(x, signal, kw)


            if (i and i % 100 == 0) or x > self.graph.get_x_limits()[1]:
                self.graph.set_x_limits(0, x + 10)

    def _load_script(self, name):

        ec = self.configuration
        fname = os.path.basename(ec['{}_script'.format(name)])
        if fname in self.scripts:
            self.info('script "{}" already loaded... cloning'.format(fname))
            s = self.scripts[fname].clone_traits()
            s.automated_run = self
            return s
        else:
            self.info('loading script "{}"'.format(fname))
            func = getattr(self, '{}_script_factory'.format(name))
            s = func(ec)
            if s.bootstrap():
                try:
                    s._test()
                    setattr(self, '_{}_script'.format(name), s)
                    return s
                except Exception, e:
                    self.warning(e)

    def _pre_analysis_save(self):
        self.info('pre analysis save')
        dm = self.data_manager
        #make a new frame for saving data
        dm.new_frame(directory='automated_runs',
                     base_frame_name='{}-intensity'.format(self.identifier))


        #create initial structure
        dm.new_group('baselines')
        dm.new_group('sniffs')
        dm.new_group('signals')

    def _post_analysis_save(self):
        self.info('post analysis save')
        db = self.db

        if db:
        #save to a database
            self.labnumber = 1
            a = db.add_analysis(self.labnumber)
            p = self.data_manager.get_current_path()
            db.add_analysis_path(p, analysis=a)
            db.commit()

#        #save to mass spec database
#        self.massspec_importer.add_analysis(self.identifier,
#                                            self.irrad_level,
#                                            self.sample,
#                                            self.runtype
#                                            )
#===============================================================================
# property get/set
#===============================================================================
    def _get_data_writer(self, grpname):
        dm = self.data_manager
        def write_data(x, keys, signals):
#            print x, keys, signals
#            print grpname
            for k in self._active_detectors:
                t = dm.get_table(k, '/{}'.format(grpname))
                nrow = t.row
                nrow['time'] = x
                nrow['value'] = signals[keys.index(k)]
                nrow.append()
                t.flush()

        return write_data

    @cached_property
    def _get_measurement_script(self):
        self._measurement_script = self._load_script('measurement')
        return self._measurement_script

    @cached_property
    def _get_extraction_script(self):
        self._extraction_script = self._load_script('extraction')
        return self._extraction_script

    @property
    def index(self):
        return self._index

    @index.setter
    def index(self, v):
        self._index = v

    def _get_duration(self):
        if self.heat_step:
            d = self.heat_step.duration
        else:
            d = self._duration
        return d

    def _get_temp_or_power(self):
        if self.heat_step:

            t = self.heat_step.temp_or_power
        else:
            t = self._temp_or_power
        return t

    def _validate_duration(self, d):
        return self._validate_float(d)

    def _validate_temp_or_power(self, d):
        return self._validate_float(d)

    def _validate_float(self, d):
        try:
            return float(d)
        except ValueError:
            pass

    def _set_duration(self, d):
        if d is not None:
            if self.heat_step:
                self.heat_step.duration = d
            else:
                self._duration = d

    def _set_temp_or_power(self, t):
        if t is not None:
            if self.heat_step:
                self.heat_step.temp_or_power = t
            else:
                self._temp_or_power = t

#===============================================================================
# views
#===============================================================================
    def traits_view(self):

#        scripts = VGroup(
#                       Item('extraction_line_script_name',
#                        editor=EnumEditor(name='extraction_line_scripts'),
#                        label='Extraction'
#                        ),
#                       Item('measurement_script_name',
#                            editor=EnumEditor(name='measurement_scripts'),
#                            label='Measurement'
#                            ),
#                       label='Scripts',
#                       show_border=True
#                       )
        v = View(
                 VGroup(
                     Group(
                     Item('identifier'),
                     Item('irrad_level', label='Irradiation'),
                     Item('sample', style='readonly'),
                     Item('weight'),
                     Item('comment'),
                     show_border=True,
                     label='Info'
                     ),
                     Group(
                         Item('position'),
                         Item('multiposition', label='Multi. position run'),
                         Item('endposition'),
                         show_border=True,
                         label='Position'
                     ),
#                     scripts,
                     )
                 )
        return v
#============= EOF =============================================
