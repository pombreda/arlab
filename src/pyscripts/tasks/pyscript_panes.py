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
from traits.api import List, Instance, Str, Property, Any
from traitsui.api import View, Item, UItem, InstanceEditor, ButtonEditor, VGroup
from pyface.tasks.traits_dock_pane import TraitsDockPane
from traitsui.tabular_adapter import TabularAdapter
from src.ui.tabular_editor import myTabularEditor

# from src.pyscripts.commands.core import ICommand
#============= standard library imports ========================
#============= local library imports  ==========================

class ControlPane(TraitsDockPane):
    name = 'Control'
    id = 'pychron.pyscript.control'
    def traits_view(self):
        v = View(
                 VGroup(
                     UItem('execute',
                           editor=ButtonEditor(label_value='execute_label')
                           ),
                     VGroup(
                         UItem('use_trace'),
                         UItem('trace_delay', label='Delay (ms)'),
                         show_border=True,
                         label='Trace'
                         )
                        )
                 )
        return v

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

class CommandsAdapter(TabularAdapter):
    columns = [('Name', 'name')]
    name_text = Property
#
    def _get_name_text(self, *args, **kw):
        return self.item

class CommandEditorPane(TraitsDockPane):
    name = 'Commands Editor'
    id = 'pychron.pyscript.commands_editor'
    command_object = Any
    def traits_view(self):
        v = View(UItem('command_object',
                       width=-275,
                       editor=InstanceEditor(),
                       style='custom'))
        return v

class CommandsPane(TraitsDockPane):
    name = 'Commands'
    id = 'pychron.pyscript.commands'

    commands = Property(depends_on='_commands')
    _commands = List
    name = Str

    selected_command = Any
    command_object = Any
    command_objects = List

    def _selected_command_changed(self):
        if self.selected_command:
            obj = next((ci for ci in self.command_objects
                             if ci.name == self.selected_command), None)
            self.command_object = obj

    def _set_commands(self, cs):
        self._commands = cs

    def _get_commands(self):
        return sorted(self._commands)

    def traits_view(self):
        v = View(Item('commands',
                      style='custom',
                      show_label=False,
                      editor=myTabularEditor(operations=['move'],
                                             adapter=CommandsAdapter(),
                                             editable=True,
                                             selected='selected_command'
                                             ),
                         width=200,
                        )
                 )
        return v
#============= EOF =============================================
