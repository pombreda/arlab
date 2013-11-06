from src.ui import set_toolkit

set_toolkit('qt4')

from src.paths import paths, build_directories

paths.build('_unittest')
build_directories(paths)

from src.helpers.logger_setup import logging_setup

logging_setup('export_spec')
from src.experiment.export.export_spec import ExportSpec
from src.helpers.isotope_utils import sort_isotopes

import unittest


class ExportSpecTestCase(unittest.TestCase):
    def setUp(self):
        data_path = '/Users/ross/Sandbox/aaaa_isotope.h5'
        self.spec = ExportSpec(data_path=data_path)

    def test_sorted_iter_isotopes(self):
        e = self.spec
        with self.spec.open_file():
            isotopes = list(e.iter_isotopes())
            isotopes = sort_isotopes(isotopes, key=lambda x: x[0])

            for (iso, det), siso in zip(isotopes, ('Ar40', 'Ar39',
                                                   'Ar38', 'Ar37', 'Ar36')):
                self.assertEqual(iso, siso)

    def test_baseline(self):
        e = self.spec
        with e.open_file():
            det = 'CDD'
            tb, vb = e.get_baseline_data(det)
            self.assertEqual(len(tb), 10)

    def test_iter_isotopes(self):
        with self.spec.open_file():
            e = self.spec
            gen = e.iter_isotopes()
            iso, det = gen.next()
            self.assertEqual(iso, 'Ar36')
            self.assertEqual(det, 'CDD')

            iso, det = gen.next()
            self.assertEqual(iso, 'Ar37')
            self.assertEqual(det, 'CDD')

            iso, det = gen.next()
            self.assertEqual(iso, 'Ar38')
            self.assertEqual(det, 'CDD')

            iso, det = gen.next()
            self.assertEqual(iso, 'Ar39')
            self.assertEqual(det, 'CDD')

            iso, det = gen.next()
            self.assertEqual(iso, 'Ar40')
            self.assertEqual(det, 'CDD')


if __name__ == '__main__':
    unittest.main()
