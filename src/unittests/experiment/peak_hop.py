import time
from src.ui import set_toolkit

set_toolkit('qt4')

from src.paths import paths, build_directories

paths.build('_unittest')
build_directories(paths)

from src.helpers.logger_setup import logging_setup

logging_setup('peak_hop')

from threading import Thread
from src.experiment.utilities.mass_spec_database_importer import MassSpecDatabaseImporter
from src.processing.arar_age import ArArAge
from src.spectrometer.ion_optics_manager import IonOpticsManager
from src.spectrometer.spectrometer_manager import SpectrometerManager
from src.experiment.automated_run.automated_run import AutomatedRun
from src.experiment.automated_run.spec import AutomatedRunSpec

import unittest

HOPS = [('Ar40:H1:10,     Ar39:AX,     Ar36:CDD', 5, 1),
        #('Ar40:L2,     Ar39:CDD',                   5, 1)
        #('Ar38:CDD',                                5, 1)
        ('Ar37:CDD', 5, 1)
]

#from traits.api import HasTraits, Str, Button
#from traitsui.api import View
#
#class A(HasTraits):
#    a=Button
#    traits_view=View('a')
#    def _a_fired(self):
#        unittest.main(exit=False)

class PeakHopTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        aspec = AutomatedRunSpec()
        aspec.mass_spectrometer = 'jan'
        aspec.labnumber = '17005'
        aspec.aliquot = 81

        a = AutomatedRun()
        a.script_info.measurement_script_name = 'unknown_peak_hop'
        s = SpectrometerManager()
        ion = IonOpticsManager(spectrometer=s.spectrometer)

        s.load(db_mol_weights=False)
        a.spectrometer_manager = s
        a.ion_optics_manager = ion
        a.arar_age = ArArAge()

        a._alive = True
        a.uuid = '12345-ABCDE'

        a.spec = aspec
        a._measured = True
        a._save_enabled = True

        cls.arun = a

    def setUp(self):
        a = self.arun
        a._save_isotopes = []
        a._pre_measurement_save()

        a._integration_seconds = 0.1

        self.save_isotopes = [('Ar40', 'H1', 'signal'),
                              ('Ar39', 'AX', 'signal'),
                              ('Ar36', 'CDD', 'signal'),
                              ('Ar37', 'CDD', 'signal')
        ]

    def measure(self):
        t = Thread(name='run', target=self._measure)
        t.start()
        t.join()

    def _measure(self):
        cycles = 1
        counts = 10
        dets = ['H2', 'H1', 'AX', 'L1', 'L2', 'CDD']
        a = self.arun
        a.measurement_script.ncounts = 100
        a.py_position_magnet('Ar40', 'H1')
        a.py_activate_detectors(dets)
        a.py_peak_hop(cycles, counts, HOPS,
                      time.time(),
                      0,
                      series=0, group='signal')

    def test_peak_hop_save(self):
        self.measure()

        msi = MassSpecDatabaseImporter()
        msi.connect()
        arun = self.arun
        arun.massspec_importer = msi
        ret = arun.post_measurement_save()
        self.assertTrue(ret)

        #def test_peak_hop_setup(self):
        #    a=self.arun
        #    self.measure()
        #    self.assertEqual(a._save_isotopes,
        #                     self.save_isotopes)


if __name__ == '__main__':
    unittest.main()
    #a=A()
    #a.configure_traits()
