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

#=============enthought library imports=======================
from traits.api import HasTraits, Any, Event, List, Bool, Property
from traitsui.api import View, Item, TableEditor, \
    Handler, TabularEditor
from traitsui.table_column import ObjectColumn
from traitsui.tabular_adapter import TabularAdapter
import weakref
# from traitsui.extras.checkbox_column import CheckboxColumn

#=============standard library imports ========================

#=============local library imports  ==========================
# from filetools import parse_setupfile

# from explanable_item import ExplanableTurbo

class ELEHandler(Handler):
    def init(self, info):
        if not info.initialized:
            info.object.selection_ok = True

class ExplanationAdapter(TabularAdapter):
    columns = [('Name', 'name'), ('Description', 'description'),
             ('State', 'state'), ('Lock', 'lock')
             ]

    lock_text = Property
    state_text = Property

    def get_bg_color(self, obj, trait, row, column):
        item = self.item
        color = 'white'
#         color='#0000FF'
        if item.soft_lock:
            color = '#CCE5FF'

        return color
    def _get_lock_text(self):
        return 'Yes' if self.soft_lock else 'No'

    def _get_state_text(self):
        return 'Open' if self._state else 'Closed'


class ExtractionLineExplanation(HasTraits):
    '''
    '''
    explanable_items = List
    # show_all = Button
    # hide_all = Button
    show_hide = Event
    label = Property(depends_on='identify')

    identify = Bool(False)
    # canvas = Any
    selected = Any
    selection_ok = False

#     def on_selection(self, s):
# #        if self.selection_ok and
#         if s is not None:
#             for ei in self.explanable_items:
#                 if ei != s:
#                     ei.identify = False
#
#             s.identify = not s.identify

#    def _show_hide_fired(self):
#        '''
#        '''
#
#        self.identify = not self.identify
#        for c in self.explanable_items:
#            c.identify = self.identify
#
#        c.canvas.Refresh()

    def _get_label(self):
        return 'Hide All' if self.identify else 'Show All'

    def load_item(self, obj, name, old, new):
        if isinstance(new, list):
            for n in new:
                self.explanable_items.append(weakref.ref(n)())

    def load(self, l):
        '''
        '''
        if isinstance(l, list):
            for v in l:
                self.explanable_items.append(weakref.ref(v)())

    def traits_view(self):
        '''
        '''
#         ed = TableEditor(columns=[ObjectColumn(name='name',
#                                                         editable=False),
#            ObjectColumn(name='description', editable=False),
#            ObjectColumn(name='state', editable=False, label='State'),
# #                                           CheckboxColumn(name='identify'),
#            ObjectColumn(name='lock', editable=False, label='Lock')
#            ],
#            selected='selected',
# #            on_select=self.on_selection,
#                             editable=False,
#                             )
        v = View(
#               VGroup(
#                      HGroup(
#                       Item('show_hide', editor=ButtonEditor(label_value='label'),
#                           show_label=False,
#                           springy=False)),

                      Item('explanable_items',
                           editor=TabularEditor(
                                                adapter=ExplanationAdapter(),
                                                editable=False,
                                                selected='selected'),
                           style='custom',
                           show_label=False,
#                           height=300,
#                           width=200
#                           width= -50
#                           springy=False
                           ),
                           width=300,
                           height=500,

#                      ),
#                 handler=ELEHandler,
                 id='pychron.explanation',
                resizable=True,
                title='Explanation'
                # scrollable = True,
                )
        return v
