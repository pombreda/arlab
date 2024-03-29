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
from traits.api import HasTraits, Any, String, Str, Instance, Bool, \
    on_trait_change
# from traitsui.api import View, Item, TableEditor
#============= standard library imports ========================
import os
#============= local library imports  ==========================
from src.paths import paths
from src.constants import NULL_STR, SCRIPT_KEYS, SCRIPT_NAMES
from src.experiment.script.script import Script
import yaml

class ScriptMixin(HasTraits):
    application = Any
    mass_spectrometer = String
    extract_device = Str

    extraction_script = Instance(Script)
    measurement_script = Instance(Script)
    post_measurement_script = Instance(Script)
    post_equilibration_script = Instance(Script)
    can_edit = Bool(False)


    @on_trait_change('mass_spectrometer, can_edit')
    def _update_value(self, name, new):
        for si in SCRIPT_NAMES:
            script = getattr(self, si)
            setattr(script, name, new)


    def _script_factory(self, label, name, kind='ExtractionLine'):
        return Script(label=label,
#                      names=getattr(self, '{}_scripts'.format(name)),
                      application=self.application,
                      mass_spectrometer=self.mass_spectrometer,
                      kind=kind,
                      can_edit=self.can_edit
                      )

    def _extraction_script_default(self):
        return self._script_factory('Extraction', 'extraction')

    def _measurement_script_default(self):
        return self._script_factory('Measurement', 'measurement', kind='Measurement')

    def _post_measurement_script_default(self):
        return self._script_factory('Post Measurement', 'post_measurement')

    def _post_equilibration_script_default(self):
        return self._script_factory('Post Equilibration', 'post_equilibration')

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

    def _load_default_scripts(self, key):
        self.debug('load default scripts for {}'.format(key))
        setter = lambda ski, sci:setattr(getattr(self, '{}_script'.format(ski)), 'name', sci)

        # open the yaml config file
        p = os.path.join(paths.scripts_dir, 'defaults.yaml')
        if not os.path.isfile(p):
            self.warning('Script defaults file does not exist {}'.format(p))
            return

        with open(p, 'r') as fp:
            defaults = yaml.load(fp)

        # convert keys to lowercase
        defaults = dict([(k.lower(), v) for k, v in defaults.iteritems()])

        # if labnumber is int use key='U'
        try:
            _ = int(key)
            key = 'u'
        except ValueError:
            pass

        key = key.lower()

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
            if key.lower() in ('u', 'bu') and self.extract_device != NULL_STR:
                e = self.extract_device.split(' ')[1].lower()
                if sk == 'extraction':
                    sc = e
                elif sk == 'post_equilibration':
                    sc = 'pump_{}'.format(e)
            elif key =='dg':
                e = self.extract_device.split(' ')[1].lower()
                sc='{}_{}'.format(e,sc)
                
            script = getattr(self, '{}_script'.format(sk))
            if not sc in script.names:
                sc = NULL_STR
            setter(sk, sc)
#============= EOF =============================================
