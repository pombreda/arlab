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
from traits.api import  Button, Enum, Any
from traitsui.api import View, UItem, HGroup, spring, Controller, ListEditor
from traitsui.tabular_adapter import TabularAdapter
#============= standard library imports ========================
#============= local library imports  ==========================
from src.processing.publisher.writers.pdf_writer import PDFWriter
from src.processing.publisher.writers.csv_writer import CSVWriter
from src.processing.publisher.writers.mass_spec_writer import MassSpecCSVWriter
from src.traits_editors.tabular_editor import myTabularEditor
from src.processing.publisher.writers.excel_writer import ExcelWriter


class SelectedTableAdapter(TabularAdapter):
    columns = [('RunID', 'runid')]

class SelectedTableController(Controller):
    make_button = Button('make')
    style = Enum('Publication', 'Data Repository')
    selected = Any

    def controller_make_button_changed(self, info):
#        print info
        # get an output path
        out = '/Users/ross/Sandbox/autoupdate_table.xls'
        out = '/Users/ross/Sandbox/autoupdate_table8.pdf'
        writer = self._new_writer(out)

        widths = None
        for i, gi in enumerate(self.model.groups):
            print i
            ta = writer.add_ideogram_table(gi.analyses,
                                           widths=widths,
                                           add_title=i == 0, add_header=True)
            if ta:
                widths = ta.get_widths()

        writer.publish()
        import webbrowser
        webbrowser.open('file://{}'.format(out))

    def _new_writer(self, out, kind='pdf'):
        if kind == 'pdf':
            klass = PDFWriter
        elif kind == 'csv':
            klass = CSVWriter
        elif kind == 'excel':
            klass = ExcelWriter
        elif kind == 'massspec':
            klass = MassSpecCSVWriter
        pub = klass(filename=out)
        return pub

    def traits_view(self):
        v = View(
                 HGroup(spring, UItem('controller.style'),
                        UItem('controller.make_button',
                              enabled_when='analyses'
                              )),
                 UItem('groups',
                       style='custom',
                       editor=ListEditor(style='custom',
                                         selected='controller.selected',
                                         use_notebook=True)
                       )
#                       editor=myTabularEditor(adapter=SelectedTableAdapter(),
#                                              ))
                 )
        return v
#============= EOF =============================================
