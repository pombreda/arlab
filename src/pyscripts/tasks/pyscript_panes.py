#===============================================================================
# Copyright 2013 Jake Ross
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
from traits.api import HasTraits, List, Instance, Str, Property
from traitsui.api import View, Item, ListStrEditor, UItem, TabularEditor
from pyface.tasks.traits_dock_pane import TraitsDockPane
from traitsui.list_str_adapter import ListStrAdapter
from traitsui.tabular_adapter import TabularAdapter
#============= standard library imports ========================
#============= local library imports  ==========================
class DescriptionPane(TraitsDockPane):
    name = 'Description'
    id = 'pychron.pyscript.description'
    def traits_view(self):
        v = View(
                 UItem('description',
                       style='readonly'
                       )

#                 'object.selected_command_object',
#                 show_label=False,
#                 style='custom',
#                 height=0.25,
#                 editor=InstanceEditor(view='help_view')
                 )
        return v

class ExamplePane(TraitsDockPane):
    name = 'Example'
    id = 'pychron.pyscript.example'
    def traits_view(self):
        v = View(
                 UItem('example',
                       style='readonly'
                       )

#                 'object.selected_command_object',
#                 show_label=False,
#                 style='custom',
#                 height=0.25,
#                 editor=InstanceEditor(view='help_view')
                 )
        return v


class EditorPane(TraitsDockPane):
    name = 'Editor'
    id = 'pychron.pyscript.editor'
    editor = Instance('src.pyscripts.parameter_editor.ParameterEditor')
    def traits_view(self):
        v = View(UItem('editor', style='custom'))
        return v

class myListStrAdapter(TabularAdapter):
    columns = [('Name', 'name')]
    name_text = Property
    def _get_name_text(self):
        return self.item

class CommandsPane(TraitsDockPane):
    name = 'Commands'
    id = 'pychron.pyscript.commands'

    commands = Property(depends_on='_commands')
    _commands = List
    name = Str

    def _set_commands(self, cs):
        self._commands = cs

    def _get_commands(self):
        return sorted(self._commands)

    def _get_commands_group(self):
        return Item('commands',
                      style='custom',
                      show_label=False,
                      editor=TabularEditor(operations=['move'],

                                    adapter=myListStrAdapter(),
#                                    editable=False,
                                    editable=True,
                                    dclicked='dclicked',
#                                        right_clicked='',
                                    selected='selected_command'
                                    ),
                         width=200,
                        ),

    def traits_view(self):
        v = View(
                 self._get_commands_group())
        return v
#============= EOF =============================================
