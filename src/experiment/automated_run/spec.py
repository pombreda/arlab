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
from traits.api import HasTraits, Str, CInt, Int, Bool, Float, Property, Enum, Either, on_trait_change
#============= standard library imports ========================
import uuid
#============= local library imports  ==========================
from src.experiment.automated_run.automated_run import AutomatedRun
from src.experiment.utilities.identifier import get_analysis_type, make_rid
from src.constants import SCRIPT_KEYS, SCRIPT_NAMES, ALPHAS
from src.loggable import Loggable

class AutomatedRunSpec(Loggable):
    '''
        this class is used to as a simple container and factory for 
        an AutomatedRun. the AutomatedRun does the actual work. ie extraction and measurement
    '''
#    state = Property(depends_on='_state')
    state = Enum('not run', 'extraction',
                 'measurement', 'success', 'failed', 'truncated', 'canceled')
    skip = Bool(False)
    end_after = Bool(False)
    #===========================================================================
    # queue globals
    #===========================================================================
    mass_spectrometer = Str
    extract_device = Str
    username = Str

    #===========================================================================
    # run id
    #===========================================================================
    labnumber = Str
    aliquot = Int
    step = Property(depends_on='_step')
    _step = Int
    user_defined_aliquot = False

    #===========================================================================
    # scripts
    #===========================================================================
    measurement_script = Str
    post_measurement_script = Str
    post_equilibration_script = Str
    extraction_script = Str

    #===========================================================================
    # extraction
    #===========================================================================
    extract_group = CInt
    extract_value = Float
    extract_units = Str
    position = Str
    duration = Float
    cleanup = Float
    pattern = Str
    beam_diameter = Float
    #===========================================================================
    # info
    #===========================================================================
    weight = Float
    comment = Str

    #===========================================================================
    # display only
    #===========================================================================
    sample = Str
    irradiation = Str

    analysis_type = Property(depends_on='labnumber')
    run_klass = AutomatedRun

    executable = Bool(True)
    frequency_added = False

    _estimated_duration = 0
    _changed = False

    def to_string(self):
        attrs = ['labnumber', 'aliquot', 'step',
                   'extract_value', 'extract_units',
                   'position', 'duration', 'cleanup', 'beam_diameter',
                   'mass_spectrometer', 'extract_device',
                   'extraction_script', 'measurement_script',
                   'post_equilibration_script', 'post_measurement_script'
                   ]
        return ','.join(map(str, self.to_string_attrs(attrs)))

    def get_estimated_duration(self, script_context, warned):
        '''
            use the pyscripts to calculate etd
            
            script_context is a dictionary of already loaded scripts
            
            this is a good point to set executable as well
        '''
        if not self._estimated_duration or self._changed:
            arun = None
            s = 0
            script_oks = []
            for si in SCRIPT_NAMES:
                name = getattr(self, si)
                if name in script_context:
                    if name not in warned:
                        self.debug('{:<30s} in script context. using previous estimated duration'.format(name))
                        warned.append(name)

                    script, ok = script_context[name]
                    s += script.get_estimated_duration()
                    script_oks.append(ok)
                else:
                    if arun is None:
                        arun = self.make_run(new_uuid=False)

                    script = getattr(arun, si)
                    if script is not None:
                        ok = script.syntax_ok()
                        script_oks.append(ok)
                        script_context[name] = script, ok
                        if ok:
                            s += script.get_estimated_duration()

            # set executable. if all scripts have OK syntax executable is True
            self.executable = all(script_oks)
            self._estimated_duration = s

        return self._estimated_duration

    def make_run(self, new_uuid=True):
        arun = self.run_klass()
        attrs = self._get_run_attrs()
        for ai in attrs:
            setattr(arun, ai, getattr(self, ai))

        for si in SCRIPT_KEYS:
            setattr(arun.script_info, '{}_script_name'.format(si),
                    getattr(self, '{}_script'.format(si)))

        if new_uuid:
            self.uuid = str(uuid.uuid4())
            arun.uuid = self.uuid
#        arun

        # bind to the runs state
        arun.on_trait_change(self._update_state, 'state')
        arun.on_trait_change(self._update_aliquot, 'aliquot')

        return arun

    def load(self, script_info, params):
        for k, v in script_info.iteritems():
            setattr(self, '{}_script'.format(k), v)

        for k, v in params.iteritems():
#            print 'param', k, v
            if hasattr(self, k):
                setattr(self, k, v)

        self._changed = False

    def _remove_mass_spectrometer_name(self, name):
        if self.mass_spectrometer:
            name = name.replace('{}_'.format(self.mass_spectrometer.lower()), '')
        return name

    def _remove_file_extension(self, name, ext='.py'):
        if name.endswith(ext):
            name = name[:-3]

        return name

    def to_string_attrs(self, attrs):
        def get_attr(attrname):
            if attrname == 'labnumber':
                if self.user_defined_aliquot:
                    v = make_rid(self.labnumber, self.aliquot)
                else:
                    v = self.labnumber
            elif attrname.endswith('script'):
                # remove mass spectrometer name
                v = getattr(self, attrname)
                v = self._remove_mass_spectrometer_name(v)
                v = self._remove_file_extension(v)
            else:
                try:
                    v = getattr(self, attrname)
                except AttributeError:
                    v = ''

            return v

        return [get_attr(ai) for ai in attrs]

    def _get_run_attrs(self):
        return ('labnumber', 'aliquot', 'step',
                   'extract_value', 'extract_units',
                   'position', 'duration', 'cleanup',
                   'pattern',
                   'beam_diameter',
                   'mass_spectrometer', 'extract_device',
                   'analysis_type',
                   'sample', 'irradiation', 'username', 'comment', 'skip', 'end_after'
                   )

#===============================================================================
# handlers
#===============================================================================
    def _update_state(self, new):
        self.state = new

    def _update_aliquot(self, new):
        self.aliquot = new

    @on_trait_change(''' 
    measurment_script, post_measurment_script,
    post_equilibration_script, extraction_script,extract_+, position, duration, cleanup
    ''')
    def _spec_changed(self):
        self._changed = True
#===============================================================================
# property get/set
#===============================================================================
#    def _get_state(self):
#        return self._state
#
#    def _set_state(self, s):
#        if self._state != 'truncate':
#            self._state = s

    def _get_analysis_type(self):
        return get_analysis_type(self.labnumber)

    def _set_step(self, v):
        if isinstance(v, str):
            v = v.upper()
            if v in ALPHAS:
                self._step = list(ALPHAS).index(v) + 1
        else:
            self._step = v

    def _get_step(self):
        if self._step == 0:
            return ''
        else:
            return ALPHAS[self._step - 1]
#============= EOF =============================================
