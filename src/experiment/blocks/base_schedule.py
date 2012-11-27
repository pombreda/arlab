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
from traits.api import Any, Instance, List, Str, Property, Button, Dict, Enum
from traitsui.api import Item, EnumEditor, VGroup, HGroup
#============= standard library imports ========================
#============= local library imports  ==========================
from src.loggable import Loggable
from src.experiment.automated_run import AutomatedRun
from src.experiment.automated_run_tabular_adapter import AutomatedRunAdapter
from src.constants import NULL_STR, SCRIPT_KEYS
import os
from src.paths import paths
import yaml
from src.helpers.filetools import str_to_bool
from src.saveable import Saveable

class RunAdapter(AutomatedRunAdapter):
    can_edit = True
    def _columns_default(self):
        cf = self._columns_factory()
        #remove state
        cf.pop(0)

        cf.remove(('Aliquot', 'aliquot'))
        cf.remove(('Sample', 'sample'))
        return cf

    def _set_float(self, attr, v):
        try:
            setattr(self.item, attr, float(v))
        except ValueError:
            pass

    def _set_position_text(self, v):
        self._set_float('position', v)

    def _set_duration_text(self, v):
        self._set_float('position', v)

    def _set_cleanup_text(self, v):
        self._set_float('position', v)

class BaseSchedule(Saveable):
    automated_runs = List(AutomatedRun)
    automated_run = Instance(AutomatedRun, ())

    mass_spectrometer = Str(NULL_STR)
    extract_device = Str(NULL_STR)
    tray = Str(NULL_STR)

    measurement_script = Str
    measurement_scripts = Property(depends_on='mass_spectrometer')
    post_measurement_script = Str
    post_measurement_scripts = Property(depends_on='mass_spectrometer')
    post_equilibration_script = Str
    post_equilibration_scripts = Property(depends_on='mass_spectrometer,extract_device')
    extraction_script = Str
    extraction_scripts = Property(depends_on='mass_spectrometer')

    loaded_scripts = Dict

    add = Button
    copy_button = Button('copy')
    paste_button = Button('paste')

    selected = Any
    _copy_cache = Any

    def update_loaded_scripts(self, new):
#        print self.loaded_scripts, 'loadded scripts'
        if new:
            self.loaded_scripts[new.name] = new
            if self.automated_run:
                self.automated_run.scripts = self.loaded_scripts

    def _load_default_scripts(self, setter=None, key=None):
        if key is None:
            if self.automated_run is None:
                return
            key = self.automated_run.labnumber

        if setter is None:
            setter = lambda ski, sci:setattr(self, '{}_script'.format(ski), sci)

        # open the yaml config file
#        import yaml
        p = os.path.join(paths.scripts_dir, 'defaults.yaml')
        if not os.path.isfile(p):
            return 
        
        with open(p, 'r') as fp:
            defaults = yaml.load(fp)

        #convert keys to lowercase
        defaults = dict([(k.lower(), v) for k, v in defaults.iteritems()])

        #if labnumber is int use key='U'
        try:
            _ = int(key)
            key = 'u'
        except ValueError:
            pass

        key = key.lower()

#        print key, defaults
        if not key in defaults:
            return

        scripts = defaults[key]
        for sk in SCRIPT_KEYS:

            sc = NULL_STR
            try:
                sc = scripts[sk]
                sc = sc if sc else NULL_STR
            except KeyError:
                pass

            sc = self._remove_file_extension(sc)
            if sk == 'extraction' and key.lower() in ['u', 'bu']:
                if self.extract_device != NULL_STR:
                    sc = self.extract_device.split(' ')[1].lower()
            if not sc in getattr(self, '{}_scripts'.format(sk)):
                sc = NULL_STR
#            print setter, sk, sc
            setter(sk, sc)

#===============================================================================
# persistence
#===============================================================================
    def dump(self, stream):
        self.dirty = False

        header, attrs = self._get_dump_attrs()

        writeline = lambda m: stream.write(m + '\n')

#        with open(p, 'wb') as f:
        tab = lambda l: writeline('\t'.join(map(str, l)))

        #write metadata

        self._meta_dumper(stream)
        writeline('#' + '=' * 80)

        tab(header)
        for arun in self.automated_runs:
            vs = arun.to_string_attrs(attrs)
#            vs = [getattr(arun, ai) for ai in attrs]
            vals = [v if v and v != NULL_STR else '' for v in vs]
            tab(vals)

        return stream
#               
    def _get_dump_attrs(self):
        header = ['labnumber',
                  'position',
                  'overlap',
                  'extract_group',
                  'extract_value',
                  'extract_units',
                  'duration',
                  'cleanup',
                  'autocenter',
                  'extraction', 'measurement', 'post_equilibration', 'post_measurement']
        attrs = ['labnumber',
                  'position',
                  'overlap',
                  'extract_group',
                  'extract_value',
                  'extract_units',
                  'duration',
                  'cleanup',
                  'autocenter',
                  'extraction_script', 'measurement_script',
                  'post_equilibration_script', 'post_measurement_script']

        return header, attrs

    def _meta_dumper(self, fp=None):
        pass

    @classmethod
    def _run_parser(cls, header, line, meta, delim='\t'):
        params = dict()
        if not isinstance(line, list):
            line = line.split(delim)

        args = map(str.strip, line)

        #load strings
        for attr in ['labnumber',
                     'measurement', 'extraction', 'post_measurement',
                     'post_equilibration',
                     ]:
            params[attr] = args[header.index(attr)]

        #load booleans
        for attr in ['autocenter']:
            try:
                param = args[header.index(attr)]
                if param.strip():
                    bo = str_to_bool(param)
                    if bo is not None:
                        params[attr] = bo
                    else:
                        params[attr] = False
            except (IndexError, ValueError):
                params[attr] = False

        #load numbers

        for attr in ['duration', 'position', 'overlap', 'cleanup', 'extract_group']:
            try:
                param = args[header.index(attr)].strip()
                if param:
                    params[attr] = float(param)
            except IndexError:
                pass

        #default extract_units to watts
        extract_value = args[header.index('extract_value')]
        extract_units = args[header.index('extract_units')]
        if not extract_units:
            extract_units = '---'

        params['extract_value'] = extract_value
        params['extract_units'] = extract_units

        def make_script_name(n):
            na = args[header.index(n)]
            if na.startswith('_'):
                if meta:
                    na = meta['mass_spectrometer'] + na

            if na and not na.endswith('.py'):
                na = na + '.py'
            return na

        params['configuration'] = cls._build_configuration(make_script_name)
        return params
#===============================================================================
# handlers
#===============================================================================
    def _copy_button_fired(self):
        self._copy_cache = [a.clone_traits() for a in self.selected]

    def _paste_button_fired(self):
        ind = None
        if self.selected:
            ind = self.automated_runs.index(self.selected[-1])

        if ind is None:
            self.automated_runs.extend(self._copy_cache[:])
        else:
            _rcopy_cache = reversed(self._copy_cache)
            for ri in _rcopy_cache:
                self.automated_runs.insert(ind + 1, ri)
        self.selected = []


#===============================================================================
# views
#===============================================================================


    def _get_script_group(self):
        script_grp = VGroup(
                        Item('extraction_script',
                             label='Extraction',
                             editor=EnumEditor(name='extraction_scripts')),
                        Item('measurement_script',
                             label='Measurement',
                             editor=EnumEditor(name='measurement_scripts')),
                        Item('post_equilibration_script',
                             label='Post Equilibration',
                             editor=EnumEditor(name='post_equilibration_scripts')),
                        Item('post_measurement_script',
                             label='Post Measurement',
                             editor=EnumEditor(name='post_measurement_scripts')),
                        show_border=True,
                        label='Scripts'
                        )
        return script_grp

#===============================================================================
# scripts
#===============================================================================
    @classmethod
    def _build_configuration(cls, make_script_name):
        def make_path(dname, name):
            return os.path.join(getattr(paths, '{}_dir'.format(dname)), name)
        args = [('{}_script'.format(ni), make_path(ni, make_script_name(ni)))
                for ni in SCRIPT_KEYS]
        return dict(args)

    def _load_script_names(self, name):
        p = os.path.join(paths.scripts_dir, name)
#        print 'fff', name, p
        if os.path.isdir(p):
            prep = lambda x:x
    #        prep = lambda x: os.path.split(x)[0]

            return [prep(s)
                    for s in os.listdir(p)
                        if not s.startswith('.') and s.endswith('.py')
                        ]
        else:
            self.warning_dialog('{} script directory does not exist!'.format(p))

    def _get_scripts(self, es):
        if self.mass_spectrometer != '---':
            k = '{}_'.format(self.mass_spectrometer)
            es = [self._clean_script_name(ei) for ei in es if ei.startswith(k)]

        es = [NULL_STR] + es
        return es

    def _clean_script_name(self, name):
        name = self._remove_mass_spectrometer_name(name)
        return self._remove_file_extension(name)

    def _remove_file_extension(self, name, ext='.py'):
        if name is NULL_STR:
            return NULL_STR

        if name.endswith('.py'):
            name = name[:-3]

        return name

    def _remove_mass_spectrometer_name(self, name):
        if self.mass_spectrometer:
            name = name.replace('{}_'.format(self.mass_spectrometer), '')
        return name

    def _add_mass_spectromter_name(self, name):
        if self.mass_spectrometer:
            name = '{}_{}'.format(self.mass_spectrometer, name)
        return name

    def _bind_automated_run(self, a):
        a.on_trait_change(self.update_loaded_scripts, '_measurement_script')
        a.on_trait_change(self.update_loaded_scripts, '_extraction_script')
        a.on_trait_change(self.update_loaded_scripts, '_post_measurement_script')
        a.on_trait_change(self.update_loaded_scripts, '_post_equilibration_script')

#===============================================================================
# property get/set
#===============================================================================
    def _get_extraction_scripts(self):
        ms = self._load_script_names('extraction')
        ms = self._get_scripts(ms)
        return ms

    def _get_measurement_scripts(self):
        ms = self._load_script_names('measurement')
        ms = self._get_scripts(ms)
        return ms

    def _get_post_measurement_scripts(self):
        ms = self._load_script_names('post_measurement')
        ms = self._get_scripts(ms)
        return ms

    def _get_post_equilibration_scripts(self):
        ms = self._load_script_names('post_equilibration')
        ms = self._get_scripts(ms)
        return ms

#===============================================================================
# views
#===============================================================================
    def _get_copy_paste_group(self):
        return HGroup(
             Item('copy_button', enabled_when='object.selected'),
             Item('paste_button', enabled_when='object._copy_cache'),
              show_labels=False)

#============= EOF =============================================
