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
from traits.api import Property, Enum, Str, on_trait_change
from traitsui.api import View, Item, InstanceEditor
import apptools.sweet_pickle as pickle
#============= standard library imports ========================
#============= local library imports  ==========================
from src.lasers.pattern.patternable import Patternable
from src.saveable import Saveable, SaveableButtons
from src.paths import paths



class PatternMakerView(Saveable, Patternable):
    kind = Property(Enum(
                         'Polygon',
                         'Arc',
                         'LineSpiral',
                        'SquareSpiral',
                        'Random',
                        'CircularContour'
                        ),
                        depends_on='_kind')
    _kind = Str('CircularContour')

    def load_pattern(self):
        p = self.open_file_dialog(default_directory=paths.pattern_dir)
        if p:
            with open(p, 'r') as fp:
                pattern = self._load_pattern(fp, p)
                if pattern:
                    self._kind = pattern.__class__.__name__.replace('Pattern', '')

#        p = self.open_file_dialog(default_directory=paths.pattern_dir)
#        if p:
#            try:
#                with open(p, 'r') as fp:
#                    obj = pickle.load(fp)
#                    if isinstance(obj, Pattern):
#                        self.pattern = obj
#                        self.pattern.path = p
#                        self._kind = obj.__class__.__name__.replace('Pattern', '')
#
#            except pickle.PickleError, e:
#                print e

    @on_trait_change('pattern:+')
    def pattern_dirty(self):
        if self.pattern.path:
            self.save_enabled = True

    def save(self):
        if self.pattern.path:
            self._save(self.pattern.path)
            self.save_enabled = False

    def save_as(self):
        path = self.save_file_dialog(default_directory=paths.pattern_dir)
        if path:
            self._save(path)

    def _save(self, path):
        if not path.endswith('.lp'):
            path += '.lp'
        self.pattern.path = path
        with open(path, 'wb') as f:
            pickle.dump(self.pattern, f)
        self.info('pattern saved as {}'.format(path))

    def traits_view(self):
        v = View(
                 Item('pattern_name',
                      style='readonly', show_label=False),
                 Item('kind', show_label=False),
                 Item('pattern',
                      style='custom',
                      editor=InstanceEditor(view='maker_view'),
                       show_label=False),
                 handler=self.handler_klass,
                 buttons=SaveableButtons,
                 title='Pattern Editor'
                 )
        return v
#===============================================================================
# property get/set
#===============================================================================
    def _get_kind(self):
        return self._kind

    def _set_kind(self, v):
        self._kind = v
        self.pattern = self.pattern_factory(v)

#===============================================================================
# factories
#===============================================================================
    def pattern_factory(self, kind):
        name = '{}Pattern'.format(kind)
        try:
            factory = __import__('src.lasers.pattern.patterns',
                             fromlist=[name])
            pattern = getattr(factory, name)()
    #        pattern = globals()['{}Pattern'.format(kind)]()
            pattern.replot()
            pattern.calculate_transit_time()
            return pattern
        except ImportError:
            pass
#===============================================================================
# defaults
#===============================================================================
    def _pattern_default(self):
        p = self.pattern_factory(self.kind)
        return p
#============= EOF =============================================
