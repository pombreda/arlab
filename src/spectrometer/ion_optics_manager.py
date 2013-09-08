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
from traits.api import Range, Instance, Bool, \
     Button, Any, Str, Float, Enum, HasTraits, List
from traitsui.api import View, Item, EnumEditor, Handler
import apptools.sweet_pickle as pickle
#============= standard library imports ========================
#============= local library imports  ==========================
from src.managers.manager import Manager
from src.graph.graph import Graph
from src.spectrometer.jobs.peak_center import PeakCenter
# from threading import Thread
from src.spectrometer.detector import Detector
from src.constants import NULL_STR
from src.ui.thread import Thread
from src.paths import paths
import os
from src.helpers.isotope_utils import sort_isotopes
# from src.ui.gui import invoke_in_main_thread
from memory_profiler import profile

class PeakCenterConfigHandler(Handler):
    def closed(self, info, isok):
        if isok:
            info.object.dump()
        return isok

class PeakCenterConfig(HasTraits):
    detectors = List(transient=True)
    detector = Instance(Detector, transient=True)
    detector_name = Str
    isotope = Str('Ar40')
    isotopes = List(transient=True)
    dac = Float

    directions = Enum('Increase', 'Decrease', 'Oscillate')
    def dump(self):
        p = os.path.join(paths.hidden_dir, 'peak_center_config')
        with open(p, 'wb') as fp:
            pickle.dump(self, fp)

    def _detector_changed(self):
        if self.detector:
            self.detector_name = self.detector.name

    def traits_view(self):
        v = View(Item('detector', editor=EnumEditor(name='detectors')),
               Item('isotope', editor=EnumEditor(name='isotopes')),
               Item('dac'),
               Item('directions'),
               buttons=['OK', 'Cancel'],
               kind='livemodal',
               title='Peak Center',
               handler=PeakCenterConfigHandler
               )
        return v


class IonOpticsManager(Manager):
    magnet_dac = Range(0.0, 6.0)
    graph = Instance(Graph)
    peak_center_button = Button('Peak Center')
    stop_button = Button('Stop')

    alive = Bool(False)
    spectrometer = Any

    peak_center = Instance(PeakCenter)
    peak_center_config = Instance(PeakCenterConfig)
    canceled = False

    peak_center_result = None

    def get_mass(self, isotope_key):
        spec = self.spectrometer
        molweights = spec.molecular_weights
        return molweights[isotope_key]

    def position(self, pos, detector, use_dac=False):
        if pos == NULL_STR:
            return

        spec = self.spectrometer
        mag = spec.magnet

        if use_dac:
            dac = pos
        else:
            if isinstance(pos, str):

                # if the pos is an isotope then update the detectors
                spec.update_isotopes(pos, detector)

                # pos is isotope
                pos = self.get_mass(pos)
                mag._mass = pos

            # pos is mass i.e 39.962
            dac = mag.map_mass_to_dac(pos)

        det = spec.get_detector(detector)
        self.debug('detector {}'.format(det))
        if det:
            dac = spec.correct_dac(det, dac)

            self.info('positioning {} ({}) on {}'.format(pos, dac, detector))
            mag.set_dac(dac)

    def get_center_dac(self, det, iso):
        spec = self.spectrometer
        det = spec.get_detector(det)

        molweights = spec.molecular_weights
        mass = molweights[iso]
        dac = spec.magnet.map_mass_to_dac(mass)

        # correct for deflection
        return spec.correct_dac(det, dac)

    def do_peak_center(self, detector=None, isotope=None,
                       period=900,
                       center_dac=None,
                       save=True,
                       confirm_save=False,
                       warn=False,
                       new_thread=True,
                       plot_panel=None,
                       ):
        directions = 'Increase'
#        spec = self.spectrometer
        if detector is None or isotope is None:
            pcc = self.peak_center_config
            info = pcc.edit_traits()
#             info = self.edit_traits(view='peak_center_config_view')
            if not info.result:
                return
            else:

                detector = pcc.detector.name
                isotope = pcc.isotope
                dac = pcc.dac
                directions = pcc.directions

                if dac > 0:
                    center_dac = dac

        if isinstance(detector, (tuple, list)):
            ref = detector[0]
            detectors = detector
        else:
            ref = detector
            detectors = (ref,)

        if center_dac is None:
            center_dac = self.get_center_dac(ref, isotope)

        self.canceled = False
        self.alive = True

        self._setup_peak_center(detectors, isotope, period,
                                      center_dac, directions, plot_panel)

        args = (save, confirm_save, warn)
        if new_thread:
            t = Thread(name='ion_optics.peak_center', target=self._peak_center,
                       args=args)
            t.start()
            self._thread = t
            return t
        else:
            self._peak_center(*args)

    def _setup_peak_center(self, detectors, isotope, period,
                           center_dac, directions, plot_panel):
        self.debug('doing pc')

        spec = self.spectrometer

        ref = detectors[0]
        self.reference_detector = ref
        self.reference_isotope = isotope

        if len(detectors) > 1:
            ad = detectors[1:]
        else:
            ad = []

        pc = self.peak_center
        if not pc:
            pc = PeakCenter()

        pc.trait_set(center_dac=center_dac,
                   period=period,
                   directions=directions,
                   reference_detector=ref,
                   additional_detectors=ad,
                   reference_isotope=isotope,
                   spectrometer=spec)

        self.peak_center = pc
        if plot_panel:
            graph = pc.graph
#             plot_panel.peak_center_graph = graph
            plot_panel.set_peak_center_graph(graph)
        else:
            # bind to the graphs close_func
            # self.close is called when graph window is closed
            # use so we can stop the timer
            graph.close_func = self.close
            # set graph window attributes
            graph.window_title = 'Peak Center {}({}) @ {:0.3f}'.format(ref, isotope, center_dac)
            graph.window_width = 300
            graph.window_height = 250
            self.open_view(graph)

    def _peak_center(self, save, confirm_save, warn):

        pc = self.peak_center
        spec = self.spectrometer
        ref = self.reference_detector
        isotope = self.reference_isotope

        dac_d = pc.get_peak_center()
        self.peak_center_result = dac_d
        if dac_d:
            args = ref, isotope, dac_d
            self.info('new center pos {} ({}) @ {}'.format(*args))

            det = spec.get_detector(ref)

            # correct for hv
            dac_d /= spec.get_hv_correction(current=True)

            # correct for deflection
            dac_d = dac_d - det.get_deflection_correction()

            # convert dac to axial units
            dac_a = dac_d / det.relative_position

            self.info('converted to axial units {}'.format(dac_a))
#             args = ref, isotope, dac_a

            if save:
                save = True
                if confirm_save:
                    msg = 'Update Magnet Field Table with new peak center- {} ({}) @ RefDetUnits= {}'.format(*args)
                    save = self.confirmation_dialog(msg)
                if save:
                    spec.magnet.update_field_table(isotope, dac_a)
                    spec.magnet.set_dac(self.peak_center_result)

        elif not self.canceled:
            msg = 'centering failed'
            if warn:
                self.warning_dialog(msg)
            self.warning(msg)

        # needs to be called on the main thread to properly update
        # the menubar actions. alive=False enables IonOptics>Peak Center
#        d = lambda:self.trait_set(alive=False)
        # still necessary with qt? and tasks

        self.trait_set(alive=False)

    def close(self):
        self.cancel_peak_center()

    def cancel_peak_center(self):
        self.alive = False
        self.canceled = True
        self.peak_center.canceled = True
        self.peak_center.stop()

#===============================================================================
# handler
#===============================================================================
    def _peak_center_config_default(self):
        config = None
        p = os.path.join(paths.hidden_dir, 'peak_center_config')
        if os.path.isfile(p):
            try:
                with open(p) as fp:
                    config = pickle.load(fp)
                    config.detectors = dets = self.spectrometer.detectors
                    config.detector = next((di for di in dets if di.name == config.detector_name), None)

            except Exception, e:
                print 'peak center config', e

        if config is None:
            config = PeakCenterConfig()
            config.detectors = self.spectrometer.detectors
            config.detector = config.detectors[0]

        keys = self.spectrometer.molecular_weights.keys()
        config.isotopes = sort_isotopes(keys)


        return config

if __name__ == '__main__':
    io = IonOpticsManager()
    io.configure_traits()

#============= EOF =============================================
#    def _graph_factory(self):
#        g = Graph(
#                  container_dict=dict(padding=5, bgcolor='gray'))
#        g.new_plot()
#        return g
#
#    def _graph_default(self):
#        return self._graph_factory()

#     def _detector_default(self):
#         return self.detectors[0]
#     def peak_center_config_view(self):
#         v = View(Item('detector', editor=EnumEditor(name='detectors')),
#                Item('isotope'),
#                Item('dac'),
#                Item('directions'),
#                buttons=['OK', 'Cancel'],
#                kind='livemodal',
#                title='Peak Center'
#                )
#         return v
#    def graph_view(self):
#        v = View(Item('graph', show_label=False, style='custom'),
#                 width=300,
#                 height=500
#                 )
#        return v
#    def peak_center_view(self):
#        v = View(Item('graph', show_label=False, style='custom'),
#                 width=300,
#                 height=500,
#                 handler=self.handler_klass
#                 )
#        return v

#    def traits_view(self):
#        v = View(Item('magnet_dac'),
#                 Item('peak_center_button',
#                      enabled_when='not alive',
#                      show_label=False),
#                 Item('stop_button', enabled_when='alive',
#                       show_label=False),
#
#                 Item('graph', show_label=False, style='custom'),
#
#
#                  resizable=True)
#        return v
#    def _correct_dac(self, det, dac):
#        #        dac is in axial units
#
# #        convert to detector
#        dac *= det.relative_position
#
#        '''
#        convert to axial detector
#        dac_a=  dac_d / relpos
#
#        relpos==dac_detA/dac_axial
#
#        '''
#        #correct for deflection
#        dev = det.get_deflection_correction()
#
#        dac += dev
#
# #        #correct for hv
#        dac *= self.spectrometer.get_hv_correction(current=True)
#        return dac
