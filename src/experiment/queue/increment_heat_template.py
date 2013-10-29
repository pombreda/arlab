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
from traits.api import HasTraits, Float, Enum, List, Int, \
    File, Property, Button, on_trait_change, Any, Event
from traitsui.api import View, UItem, HGroup
from pyface.file_dialog import FileDialog
from pyface.constant import OK
from traitsui.tabular_adapter import TabularAdapter
#============= standard library imports ========================
import csv
import os
#============= local library imports  ==========================
from src.ui.tabular_editor import myTabularEditor
from src.paths import paths
from src.viewable import Viewable
from src.pychron_constants import alphas
# paths.build('_experiment')
# build_directories(paths)
class IncrementalHeatAdapter(TabularAdapter):
    columns = [('Step', 'step_id'),
               ('Value', 'value'),
               ('Units', 'units'),
               ('Duration (s)', 'duration'),
               ('Cleanup (s)', 'cleanup'),
    ]

    step_id_text = Property

    def _get_step_id_text(self):
        return alphas(self.item.step_id - 1)


class IncrementalHeatStep(HasTraits):
    step_id = Int
    duration = Float
    cleanup = Float
    value = Float
    units = Enum('watts', 'temp', 'percent')
    #    is_ok = Property


    def make_row(self):
        return self.value, self.units, self.duration, self.cleanup

    def make_dict(self, gdur, gcleanup):
        dur = self.duration
        if not dur:
            dur = gdur

        cleanup = self.cleanup
        if not cleanup:
            cleanup = gcleanup

        return dict(extract_value=self.value, extract_units=self.units,
                    duration=dur,
                    cleanup=cleanup)

    def to_string(self):
        return ','.join(map(str, self.make_row()))

#    def _get_is_ok(self):
#        return self.value and (self.duration or self.cleanup)


class IncrementalHeatTemplate(Viewable):
    steps = List()
    name = Property(depends_on='path')
    path = File

    save_button = Button('save')
    save_as_button = Button('save as')
    add_row = Button('add step')
    title = Property

    selected = Any
    copy_cache = List
    pasted = Event

    def _pasted_fired(self):
        if self.selected:
            idx = self.steps.index(self.selected[-1]) + 1
            for ci in self.copy_cache[::-1]:
                nc = ci.clone_traits()
                self.steps.insert(idx, nc)
        else:
            for ci in self.copy_cache:
                nc = ci.clone_traits()
                self.steps.append(nc)

    def _get_title(self):
        if self.path:
            return os.path.basename(self.path)
        else:
            return ' '

    def _steps_default(self):
        return [IncrementalHeatStep(step_id=i + 1) for i in range(20)]

    def _get_name(self):
        return os.path.basename(self.path)

    #===============================================================================
    # persistence
    #===============================================================================
    def load(self, path):

        self.path = path
        self.steps = []
        with open(path, 'r') as fp:
            reader = csv.reader(fp)
            header = reader.next()
            cnt = 1
            for row in reader:
                if row:
                    params = dict()
                    for a, cast in (('value', float), ('units', str),
                                    ('duration', float), ('cleanup', float)):
                        idx = header.index(a)
                        params[a] = cast(row[idx])

                    step = IncrementalHeatStep(step_id=cnt,
                                               **params
                    )
                    self.steps.append(step)
                    cnt += 1

    def dump(self, path):
        with open(path, 'w') as fp:
            writer = csv.writer(fp)
            header = ('value', 'units', 'duration', 'cleanup')
            writer.writerow(header)
            for step in self.steps:
                writer.writerow(step.make_row())
                #===============================================================================
                # handlers
                #===============================================================================

    @on_trait_change('steps[]')
    def _steps_updated(self):
        for i, si in enumerate(self.steps):
            si.step_id = i + 1

    def _add_row_fired(self):
        if self.selected:
            for si in self.selected:
                step = si.clone_traits()
                self.steps.append(step)
        else:
            if self.steps:
                step = self.steps[-1].clone_traits()
            else:
                step = IncrementalHeatStep()

            self.steps.append(step)

    def _save_button_fired(self):
        self.dump(self.path)
        self.close_ui()

    def _save_as_button_fired(self):
        dlg = FileDialog(action='save as',
                         default_directory=paths.incremental_heat_template_dir
        )
        if dlg.open() == OK:
            path = dlg.path
            if not path.endswith('.txt'):
                path = '{}.txt'.format(path)

            self.dump(path)
            self.path = path
            self.close_ui()

    def traits_view(self):
        editor = myTabularEditor(adapter=IncrementalHeatAdapter(),
                                 selected='selected',
                                 copy_cache='copy_cache',
                                 pasted='pasted',
                                 multi_select=True
        )
        v = View(
            HGroup(UItem('add_row')),
            UItem('steps',
                  style='custom',
                  editor=editor),

            HGroup(UItem('save_button', enabled_when='path'),
                   UItem('save_as_button')),
            height=500,
            width=600,
            resizable=True,
            title=self.title,
            handler=self.handler_klass
        )
        return v


if __name__ == '__main__':
    im = IncrementalHeatTemplate()
    im.load(os.path.join(paths.incremental_heat_template_dir,
                         'asdf.txt'
    ))

    #    for i in range(10):
    #        im.steps.append(IncrementalHeatStep(step_id=i + 1))
    im.configure_traits()
#============= EOF =============================================
