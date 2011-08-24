#============= enthought library imports =======================
from traits.api import on_trait_change, HasTraits, Instance, List, Enum, Str, Float, Button, Property, Event
from traitsui.api import View, Item, HGroup, spring
from traitsui.tabular_adapter import TabularAdapter
from traitsui.editors.tabular_editor import TabularEditor
from src.helpers.filetools import parse_file
from pyface.api import FileDialog, OK
import os
from src.helpers.paths import scripts_dir

#============= standard library imports ========================

#============= local library imports  ==========================
class HeatStepAdapter(TabularAdapter):
    can_drop = True
    kind = Str
    state_image = Property
    state_text = Property
    state_width = Property

    def _columns_default(self):
        hp = ('Temp', 'temp_or_power')

        if self.kind == 'power':
            hp = ('Power', 'temp_or_power')

        return [
                #('', 'step'), 
                ('', 'state'), hp ,
                ('Duration (sec)', 'duration'),
                ('Elapsed (sec)', 'elapsed_time')
                ]

#    def insert(self, object, name, row, item):
#        print object, name, row, item
#        object.steps.insert(row - 1, HeatStep())

    def get_width(self, object, trait, column):
        w = -1
        if column == 0:
            w = 20
#        elif column == 1:
#            w = 20
        return w

    def get_can_edit(self, obj, name, row):
        edit = True

        if getattr(obj, name)[row].state in ['success', 'fail']:
            edit = False
        return edit

#    def get_default_value(self, obj, name):
#        print obj, name

    def _get_state_text(self):
        return ''

    def _set_state_text(self, v):
        pass

    def get_format(self, obj, name, row, column):
        if column == 3: #elapsed_time
            fmt = '%0.3f'
        else:
            fmt = '%s'

        return fmt

    def _get_state_image(self):
        if self.item:
            im = 'gray'

            if self.item.state == 'running':
                im = 'orange'
            elif self.item.state == 'success':
                im = 'green'
            elif self.item.state == 'fail':
                im = 'red'

            #get the source path
            root = os.path.split(__file__)[0]
            while not root.endswith('src'):
                root = os.path.split(root)[0]
            root = os.path.split(root)[0]
            root = os.path.join(root, 'resources')
            return os.path.join(root, '{}_ball.png'.format(im))

class HeatStep(HasTraits):
    temp_or_power = Float
    duration = Float
    elapsed_time = Float
    state = Enum('not run', 'running', 'success', 'fail')
    step = Str
    update = Event

    @on_trait_change('elapsed_time,state')
    def _update_table(self):
        #update the analysis table
        self.update = True

class HeatSchedule(HasTraits):
    steps = List(HeatStep)
    kind = Enum('power', 'temp')
    path = Str

    load_button = Button
    current_step = Instance(HeatStep)

    elapsed_time = Float

    @on_trait_change('current_step:elapsed_time')
    def update_elapsed_time(self, o, n, oo, nn):
#        print o, n, oo, nn
        self.elapsed_time = nn

    def _load_button_fired(self):

        d = os.path.join(scripts_dir, 'laserscripts', 'heat_schedules')
        dlg = FileDialog(action = 'open',
                         default_directory = d)
        if dlg.open() == OK:
            self.load(dlg.path)

    def load(self, p = None):
        if p is None:
            p = self.path
        else:
            self.path = p

        self.steps = []
        for args in parse_file(p, split = ','):
            if len(args) == 2:
                self.steps.append(HeatStep(temp_or_power = float(args[0]),
                                           duration = float(args[1])
                                           ))
            elif len(args) == 4:
                for i in range(*map(int, args[:3])):
                    self.steps.append(HeatStep(temp_or_power = float(i),
                                               duration = float(args[3])
                                               ))

    def reset_steps(self):
        for s in self.steps:
            s.state = 'not run'
            s.elapsed_time = 0

    def _steps_default(self):
        return [
                HeatStep(temp_or_power = 0,
                               duration = 5),

                HeatStep(temp_or_power = 0,
                               duration = 5),

                ]
    def traits_view(self):
        editor = TabularEditor(adapter = HeatStepAdapter(kind = self.kind),
                                operations = ['move', 'delete',
                                              'append', 'insert',
                                              'edit'
                                              ],
                                multi_select = True,
                                editable = True,
                                update = 'object.current_step.update'
                                )
        v = View(

                 HGroup(spring, Item('elapsed_time', format_str = '%0.3f', style = 'readonly')),
                 Item('steps', show_label = False, editor = editor),
                 HGroup(spring, Item('load_button', show_label = False)),
#                 Item('save_button', show_label = False),

                 )
        return v

#============= EOF ====================================
