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
from traits.api import Any, List, HasTraits, Bool, Instance, Str, on_trait_change
from traitsui.api import View, Item, TableEditor, ListEditor
from apptools.preferences.ui.api import PreferencesPage
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
#============= standard library imports ========================
#============= local library imports  ==========================
from src.helpers.parsers.initialization_parser import InitializationParser


class Plugin(HasTraits):
    '''
    '''
    name = Str
    enabled = Bool
    category = Str


class PluginCategory(HasTraits):
    plugins = List
    name = Str
    parser = Any

    @on_trait_change('plugins:enabled')
    def _update(self, obj, name, old, new):
        '''
        '''
        parser = self.parser
        if obj.enabled:
            parser.enable_plugin(obj.name, category=obj.category)
        else:
            parser.disable_plugin(obj.name, category=obj.category)

    def traits_view(self):
        cols = [
                CheckboxColumn(name='enabled'),
                ObjectColumn(name='name', editable=False)]
        editor = TableEditor(columns=cols)

        return View(Item('plugins', editor=editor, show_label=False))


class PychronPluginPreferencesPage(PreferencesPage):
    '''
    '''
    categories = List(transient=True)
    preferences_path = 'pychron.workbench'
    name = 'Plugins'

    parser = Instance(InitializationParser, (), transient=True)


    def _categories_default(self):
        '''
        '''
        parser = self.parser
        cats = []
        for g in parser.get_plugin_groups():
            ps = parser.get_plugins(g, element=True, all=True)
            if not ps:
                continue

            plugins = []
            for pi in ps:
                plugin = Plugin(name=pi.text.strip(),
                              enabled=True if pi.get('enabled').lower() == 'true' else False,
                              category=g
                              )
                plugins.append(plugin)

            cat = PluginCategory(name=g.capitalize(),
                                 plugins=plugins,
                                 parser=self.parser
                                 )
            cats.append(cat)

        return cats

    def traits_view(self):
        '''
        '''
        editor = ListEditor(use_notebook=True,
                            dock_style='tab',
                            page_name='.name'
                            )
        v = View(Item('categories', editor=editor,
                       show_label=False,
                       style='custom'
                       ),
                 resizable=True
                 )
        return v

if __name__ == '__main__':
    d = PychronPluginPreferencesPage()
    d.configure_traits()
#============= views ===================================
#============= EOF ====================================
