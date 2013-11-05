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
from numpy import array
from tables import NoSuchNodeError
from traits.api import CStr, Str, CInt, Float, \
    TraitError, Property, Any, Either, Instance, Dict
from uncertainties import ufloat
from src.loggable import Loggable
from src.experiment.utilities.identifier import make_rid
#============= standard library imports ========================
#============= local library imports  ==========================
from src.managers.data_managers.h5_data_manager import H5DataManager


class ExportSpec(Loggable):
    rid = CStr
    aliquot = Either(CInt, Str)
    step = Str
    irradpos = CStr

    blanks = Dict
    signal_fits = Dict
    signal_intercepts = Dict

    spectrometer = Str
    extract_device = Str
    tray = Str
    position = Property(depends_on='_position')
    _position = Any

    power_requested = Float(0)
    power_achieved = Float(0)
    duration = Float(0)
    duration_at_request = Float(0)
    first_stage_delay = CInt(0)
    second_stage_delay = CInt(0)
    runscript_name = Str
    runscript_text = Str
    comment = Str

    data_path = Str
    data_manager = Instance(H5DataManager, ())

    def load_record(self, record):
        attrs = [('labnumber', 'labnumber'),
                 ('aliquot', 'aliquot'),
                 ('step', 'step'),
                 ('irradpos', 'labnumber'),
                 ('extract_device', 'extract_device'), ('tray', 'tray'),
                 ('position', 'position'), ('power_requested', 'extract_value'),
                 ('power_achieved', 'extract_value'), ('duration', 'duration'),
                 ('duration_at_request', 'duration'), ('first_stage_delay', 'cleanup'),
                 ('comment', 'comment')]

        for exp_attr, run_attr in attrs:
            if hasattr(record.spec, run_attr):
                try:
                    setattr(self, exp_attr, getattr(record.spec, run_attr))
                except TraitError, e:
                    self.debug(e)

        if hasattr(record, 'cdd_ic_factor'):
            ic = record.cdd_ic_factor
            if ic is None:
                self.debug('Using default CDD IC factor 1.0')
                ic = ufloat(1, 1.0e-20)

            self.ic_factor_v = float(ic.nominal_value)
            self.ic_factor_e = float(ic.std_dev)
        else:
            self.debug('{} has no ic_factor attribute'.format(record, ))

    def open_file(self):
        return self.data_manager.open_file(self.data_path)

    def iter_isotopes(self):
        def _iter():
            dm = self.data_manager
            hfile = dm._frame
            root = dm._frame.root
            signal = root.signal
            for isogroup in hfile.listNodes(signal):
                for dettable in hfile.listNodes(isogroup):
                    iso = isogroup._v_name
                    det = dettable.name
                    self.debug('iter_isotopes yield: {} {}'.format(iso, det))
                    yield iso, det

        return _iter()

    def get_blank_uvalue(self, iso):
        try:
            b = self.blanks[iso]
        except KeyError:
            self.debug('no blank for {} {}'.format(iso, self.blanks.keys()))
            b = ufloat(0, 0)

        return b

    def get_signal_uvalue(self, iso, det):
        try:
            ps = self.signal_intercepts['{}signal'.format(iso)]
        except KeyError, e:
            self.debug('no key {} {}'.format(iso,
                                             self.signal_intercepts.keys()))
            ps = ufloat(0, 0)

        return ps

    def get_signal_fit(self, iso, det):
        try:
            f = self.signal_fits[det]
        except KeyError:
            f = 'linear'
        return f

    def get_baseline_fit(self, det):
        return 'average_SEM'

    def get_baseline_data(self, iso, det):
        return self._get_data('baseline', iso, det)

    def get_signal_data(self, iso, det):
        return self._get_data('signal', iso, det)

    def get_baseline_uvalue(self, det):
        vb = []

        dm = self.data_manager
        hfile = dm._frame
        root = dm._frame.root
        v, e = 0, 0
        if hasattr(root, 'baseline'):
            baseline = root.baseline
            for isogroup in hfile.listNodes(baseline):
                for dettable in hfile.listNodes(isogroup):
                    if dettable.name == det:
                        vb = [r['value'] for r in dettable.iterrows()]
                        break

            vb = array(vb)
            v = vb.mean()
            e = vb.std()

        return ufloat(v, e)

    def _get_data(self, group, iso, det):
        dm = self.data_manager
        root = dm._frame.root

        try:
            group = getattr(root, group)
            isog = getattr(group, iso)
            tab = getattr(isog, det)
            data = [(row['time'], row['value'])
                    for row in tab.iterrows()]
            t, v = zip(*data)
        except (NoSuchNodeError, AttributeError):
            t, v = [0, ], [0, ]

        return t, v

    @property
    def record_id(self):
        return make_rid(self.labnumber, self.aliquot, self.step)

    def _set_position(self, pos):
        if ',' in pos:
            self._position = list(map(int, pos.split(',')))
        else:
            self._position = pos

    def _get_position(self):
        return self._position

        #============= EOF =============================================
