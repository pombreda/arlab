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
from traits.api import HasTraits, Int, Bool, String, Float, on_trait_change, Str, \
    List
from traitsui.api import View, Item, HGroup, VGroup, Group, spring, ListEditor, \
    InstanceEditor, UItem, Label, Spring, EnumEditor
#============= standard library imports ========================
import os
import re
#============= local library imports  ==========================
from src.pyscripts.editor import PyScriptEditor
from src.paths import paths
from src.helpers.filetools import str_to_bool
from src.pyscripts.hop import Hop
from src.constants import FIT_TYPES, NULL_STR

STR_FMT = "{}= '{}'"
FMT = '{}= {}'
#===============================================================================
# multicollect
#===============================================================================
MULTICOLLECT_COUNTS_REGEX = re.compile(r'(MULTICOLLECT_COUNTS) *= *\d+$')
MULTICOLLECT_ISOTOPE_REGEX = re.compile(r'(MULTICOLLECT_ISOTOPE) *= *')
MULTICOLLECT_DETECTOR_REGEX = re.compile(r'(MULTICOLLECT_DETECTOR) *= *')
ACTIVE_DETECTORS_REGEX = re.compile(r'(ACTIVE_DETECTORS) *= *')
FITS_REGEX = re.compile(r'(FITS) *= *')

# MULTICOLLECT_COUNTS_FMT = num_fmt
MULTICOLLECT_ISOTOPE_FMT = STR_FMT
MULTICOLLECT_DETECTOR_FMT = STR_FMT
# ACTIVE_DETECTORS_FMT = '{}= {}'
# FITS_FMT = '{}= {}'

#===============================================================================
# baseline
#===============================================================================
BASELINE_COUNTS_REGEX = re.compile(r'(BASELINE_COUNTS) *= *\d+$')
BASELINE_DETECTOR_REGEX = re.compile(r'(BASELINE_DETECTOR) *= *')
BASELINE_MASS_REGEX = re.compile(r'(BASELINE_MASS) *= *')
BASELINE_BEFORE_REGEX = re.compile(r'(BASELINE_BEFORE) *= *')
BASELINE_AFTER_REGEX = re.compile(r'(BASELINE_AFTER) *= *')
BASELINE_SETTLING_TIME_REGEX = re.compile(r'(BASELINE_SETTLING_TIME) *= *')

# BASELINE_COUNTS_FMT = '{}= {}'
BASELINE_DETECTOR_FMT = STR_FMT
# BASELINE_MASS_FMT = '{}= {}'
# BASELINE_BEFORE_FMT = '{}= {}'
# BASELINE_AFTER_FMT = '{}= {}'
# BASELINE_SETTLING_TIME_FMT = '{}= {}'

#===============================================================================
# peak center
#===============================================================================
PEAK_CENTER_BEFORE_REGEX = re.compile(r'(PEAK_CENTER_BEFORE) *= *')
PEAK_CENTER_AFTER_REGEX = re.compile(r'(PEAK_CENTER_AFTER) *= *')
PEAK_CENTER_DETECTOR_REGEX = re.compile(r"(PEAK_CENTER_DETECTOR) *= *")
PEAK_CENTER_ISOTOPE_REGEX = re.compile(r"(PEAK_CENTER_ISOTOPE) *= *")

# PEAK_CENTER_BEFORE_FMT = '{}= {}'
# PEAK_CENTER_AFTER_FMT = '{}= {}'
PEAK_CENTER_DETECTOR_FMT = STR_FMT
PEAK_CENTER_ISOTOPE_FMT = STR_FMT
#===============================================================================
# equilibration
#===============================================================================
EQ_TIME_REGEX = re.compile(r"(EQ_TIME) *= *")
EQ_INLET_REGEX = re.compile(r"(EQ_INLET) *= *")
EQ_OUTLET_REGEX = re.compile(r"(EQ_OUTLET) *= *")
EQ_DELAY_REGEX = re.compile(r"(EQ_DELAY) *= *")

# EQ_TIME_FMT = '{}= {}'
EQ_INLET_FMT = STR_FMT
EQ_OUTLET_FMT = STR_FMT
# EQ_DELAY_FMT = '{}= {}'

#===============================================================================
# peak hops
#===============================================================================
USE_PEAK_HOP_REGEX = re.compile(r'(USE_PEAK_HOP) *= *')
NCYCLES_REGEX = re.compile(r'(NCYCLES) *= *')
BASELINE_NCYCLES_REGEX = re.compile(r'(BASELINE_NCYCLES) *= *')
HOPS_REGEX = re.compile(r'(HOPS) *= *\[')

# USE_PEAK_HOP_FMT = '{}= {}'
# NCYCLES_FMT = '{}= {}'
# BASELINE_NCYCLES_FMT = '{}= {}'

class Detector(HasTraits):
    fit = Str
    use = Bool
    label = Str
    ref = Bool
    isotope = Str
    isotopes = [NULL_STR, 'Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36']
    def traits_view(self):
        v = View(HGroup(
                        UItem('use'),
                        UItem('label',
                              width= -30,
                              style='readonly'),
                        UItem('isotope',
                             editor=EnumEditor(name='isotopes'),
                             enabled_when='use'),
                        UItem('fit',
                            enabled_when='use',
                            editor=EnumEditor(values=[NULL_STR] + FIT_TYPES))
                        )
                 )
        return v

    def _use_changed(self):
        if self.use and not self.fit:
            self.fit = 'linear'

class MeasurementPyScriptEditor(PyScriptEditor):
    _kind = 'Measurement'

    #===========================================================================
    # counts
    #===========================================================================
    multicollect_counts = Int(100)
    active_detectors = List

    #===========================================================================
    # baselines
    #===========================================================================
    baseline_counts = Int(100)
    baseline_detector = String
    baseline_mass = Float
    baseline_before = Bool
    baseline_after = Bool
    baseline_settling_time = Int(3)

    #===========================================================================
    # peak center
    #===========================================================================
    peak_center_before = Bool
    peak_center_after = Bool
    peak_center_isotope = String
    peak_center_detector = String

    #===========================================================================
    # equilibration
    #===========================================================================
    eq_time = Float
    eq_outlet = String
    eq_inlet = String
    eq_delay = Float

    #===========================================================================
    # peak hop
    #===========================================================================
    ncycles = Int
    use_peak_hop = Bool
    baseline_ncycles = Int
    hops = List

    def _get_parameters_group(self):

        multicollect_grp = VGroup(
                                Group(
                                      Item('multicollect_counts', label='Counts',
                                           tooltip='Number of data points to collect'
                                           )
                                      ),
                                 HGroup(
                                        Label('Use'),
                                        Spring(springy=False, width= -32),
                                        Label('Ref. Iso'),
                                        Spring(springy=False, width= -35),
                                        Label('Fit')
                                        ),
                                 UItem('active_detectors',
                                       style='custom',
                                       editor=ListEditor(mutable=False,
                                                         style='custom',
#                                                         columns=2,
                                                         editor=InstanceEditor(),
                                                         ),
#                                        height= -50,
                                       ),

                                 label='Multicollect',
                                 show_border=True
                                 )
        baseline_grp = Group(
                             Item('baseline_before', label='Baselines at Start'),
                             Item('baseline_after', label='Baselines at End'),
                             Item('baseline_counts',
                                  tooltip='Number of baseline data points to collect',
                                  label='Counts'),
                             Item('baseline_detector', label='Detector'),
                             Item('baseline_settling_time',
                                  label='Delay (s)',
                                  tooltip='Wait "Delay" seconds after setting magnet to baseline position'
                                  ),
                             Item('baseline_mass', label='Mass'),
                             label='Baseline',
                             show_border=True
                             )

        peak_center_grp = Group(
                              Item('peak_center_before', label='Peak Center at Start'),
                              Item('peak_center_after', label='Peak Center at End'),
                              Item('peak_center_detector',
                                   label='Detector',
                                   enabled_when='peak_center_before or peak_center_after'
                                   ),
                              Item('peak_center_isotope',
                                   label='Isotope',
                                   enabled_when='peak_center_before or peak_center_after'
                                   ),
                              label='Peak Center',
                              show_border=True)

        equilibration_grp = Group(
                                Item('eq_time', label='Time (s)'),
                                Item('eq_outlet', label='Ion Pump Valve'),
                                Item('eq_delay', label='Delay (s)',
                                     tooltip='Wait "Delay" seconds before opening the Inlet Valve'
                                     ),
                                Item('eq_inlet', label='Inlet Valve'),
                                label='Equilibration',
                                show_border=True
                                )

        peak_hop_group = VGroup(
                                Group(
                                      Item('ncycles'),
                                      Item('baseline_ncycles')),
                                HGroup(Spring(springy=False, width=28),
                                        Label('position'), Spring(springy=False, width=10),
                                        Label('Detectors'), Spring(springy=False, width=188),
                                        Label('counts'),
                                        spring),
                                UItem('hops', editor=ListEditor(style='custom',
                                                              editor=InstanceEditor())),
                               label='Peak Hop',
                               visible_when='use_peak_hop',
                               show_border=True
                               )

        return Group(
#                     HGroup(

                            VGroup(
                                 Item('use_peak_hop'),
                                 peak_hop_group,
                                 Group(multicollect_grp,
                                       baseline_grp,
                                       layout='tabbed',
                                       visible_when='not use_peak_hop'
                                       ),
                                 peak_center_grp,
                                 equilibration_grp),

#                            spring,
#                            ),

                     label='Parameters')

    def _parse(self):
        str_to_str = lambda x: x.replace("'", '').replace('"', '')
        lines = self.body.split('\n')
        def extract_detectors(v):
            v = eval(v)
            for di in self.active_detectors:
                di.use = di.label in v

        def extract_fits(v):
            v = eval(v)
            if len(v) == 1:
                v = v * len(self.active_detectors)

            for vi, di in zip(v, self.active_detectors):
                di.fit = vi

        attrs = (
                ('multicollect_counts', int),
                ('active_detectors'   , extract_detectors),
                ('fits'               , extract_fits),

                ('baseline_before'    , str_to_bool),
                ('baseline_after'     , str_to_bool),
                ('baseline_counts'    , int),
                ('baseline_detector'  , str_to_str),
                ('baseline_mass'      , float),

                ('peak_center_before', str_to_bool),
                ('peak_center_after', str_to_bool),
                ('peak_center_detector', str_to_str),
                ('peak_center_isotope', str_to_str),

                ('eq_time', float),
                ('eq_inlet', str_to_str),
                ('eq_outlet', str_to_str),
                ('eq_delay', float),

                ('use_peak_hop', str_to_bool),
                ('ncycles', int),
                )
        found = []
        for li in lines:
            for v, cast in attrs:
                if self._extract_parameter(li, v, cast=cast):
                    found.append(v)
                    continue

        hoplist = self._extract_multiline_parameter(lines, 'hops')
        if hoplist:
            self.hops = self._extract_hops(hoplist)

        for name, _cast in attrs:
            if name not in found:
                nv = self._get_new_value(name, getattr(self, name))

                lines.insert(3, nv)

        self.body = '\n'.join(lines)

    def _extract_hops(self, hl):
        hops = []
        for _, (hi, cnts) in enumerate(hl):
            poss, dets = zip(*[it.split(':') for it in hi.split(',')])
            pos = poss[0]
            dets = ','.join(map(str.strip, dets))
            hop = Hop(position=pos, detectors=dets, counts=cnts)
            hops.append(hop)

        return hops

    def _endline(self, li, terminator=']'):
        '''
            use regex in future
        '''
        li = li.strip()
        if li.startswith('#'):
            return
        elif '#' in li:
            li = li.split('#')[0]

        if li.endswith(terminator):
            return True

    def _extract_multiline_parameter(self, lines, param):
        rlines = []
        start = None
        regex = self._get_regex(param)
        endline = self._endline
        for li in lines:
            if regex.match(li):
                li = li.split('=')[1]
                rlines.append(li)
                start = True
            elif start and endline(li):
                rlines.append(li)
                break
            elif start:
                rlines.append(li)

        r = '\n'.join(rlines)
        try:
            return eval(r)
        except Exception, e:
            self.debug(e)

    def _extract_parameter(self, line, attr, cast=None):

        regex = globals()['{}_REGEX'.format(attr.upper())]
#        if attr == 'multicollect_counts':
#            print regex.match(line), line
        if regex.match(line):
            _, v = line.split('=')
            v = v.strip()
            if cast:
                v = cast(v)

#            if attr == 'multicollect_counts':
#                print 'vvvvv', v
            if v is not None:
                setattr(self, attr, v)
                self._update_value(attr, v)
            return True

    @on_trait_change('hops:[counts,detectors, position]')
    def _update_hops(self, obj, name, new):

        hs = [hi.to_string()
              for hi in self.hops]
        hs = ['({}),'.format(hi) for hi in hs if hi]
        nhs = [hs[0]]
        for hi in hs[1:]:
            nhs.append('        {}'.format(hi))
        hopstr = 'HOPS = [{}]'.format('\n'.join(nhs))

        ho = self.hops[0]
        det = ho.detectors.split(',')[0]
        iso = ho.position
        self._modify_body('multicollect_detector', det)
        self._modify_body('multicollect_isotope', iso)

        self._modify_body_multiline('hops', hopstr)


    @on_trait_change('active_detectors:[use, fit, isotope]')
    def _update_active_detectors(self, obj, name, new):
        dets = self.active_detectors

        if name == 'isotope':
            if new != NULL_STR:
                for di in dets:
                    if not di == obj:
                        di.isotope = NULL_STR
                self._modify_body('multicollect_detector', obj.label)
                self._modify_body('multicollect_isotope', obj.isotope)
            return

        s = ''
        if name == 'use':
            if not new and obj.isotope != NULL_STR:
                fd = next((a for a in self.active_detectors if a.use))
                fd.isotope = obj.isotope

            attr = 'label'
            param = 'active_detectors'
        else:
            attr = 'fit'
            param = 'fits'

        new = []
        for di in dets:
            if di.use:
                new.append(getattr(di, attr))

        if len(new) == 1:
            s = "'{}',".format(new[0])
        else:
#            nn = []
#            for di, _label in self.detectors:
#                if di in new:
#                    nn.append(di)
            s = ','.join(map("'{}'".format, new))


        self._modify_body(param, '({})'.format(s))



    @on_trait_change('''peak_center_+, eq_+, multicollect_counts, baseline_+,
use_peak_hop, ncycles, baseline_ncycles
''')
    def _update_value(self, name, new):
        return self._modify_body(name, new)

    def _get_regex(self, name):
        return globals()['{}_REGEX'.format(name.upper())]

    def _get_new_value(self, name, new):
        p = name.upper()
        ff = '{}_FMT'.format(p)
        if ff in globals():
            fmt = globals()[ff]
        else:
            fmt = FMT

        p = '{:<25s}'.format(p)
        return fmt.format(p, new)

    def _modify_body_multiline(self, param, new):
        lines = self.body.split('\n')
        regex = self._get_regex(param)
        endline = self._endline
        rlines = []
        start = None
        # delete the previous entry
        for i, li in enumerate(lines):
            li = li.strip()
            if regex.match(li):
                idx = i
                start = True
                continue
            elif start :
                if endline(li):
                    start = False
                continue

            rlines.append(li)

        rlines.insert(idx, new)
        self.body = '\n'.join(rlines)

    def _modify_body(self, name, new):
        regex = self._get_regex(name)
        nv = self._get_new_value(name, new)
        ostr = []
        modified = False
        for li in self.body.split('\n'):
            if regex.match(li.strip()):
                ostr.append(nv)
                modified = True
            else:
                ostr.append(li)

        self.body = '\n'.join(ostr)

        return modified

#==============================================================================
# defaults
#==============================================================================
    def _hops_default(self):
        return [Hop(position='Ar40', detectors='H1, CDD')] + \
                [Hop(position='Ar39', detectors='CDD')] + \
                [Hop() for i in range(5)]

    def _active_detectors_default(self):
        return [Detector(label=di) for di in ['H2', 'H1', 'AX', 'L1', 'L2', 'CDD']]

if __name__ == '__main__':
    from launchers.helpers import build_version
    build_version('_experiment')
    from src.helpers.logger_setup import logging_setup
    logging_setup('scripts')

    s = MeasurementPyScriptEditor()

#    h = Hop(position='Ar40',
#            detectors='H1, CDD')
#    print h.to_string()
    p = os.path.join(paths.scripts_dir, 'measurement', 'jan_unknown_peak_hop.py')
    s.open_script(path=p)
# #    s.hops = [Hop(position='Ar40', detectors='H1, CDD', counts=403)]
    s.configure_traits()
#============= EOF =====================================po========
