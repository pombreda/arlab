'''
Copyright 2011 Jake Ross

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
from traits.api import Instance, Float, Bool, Any
from traitsui.api import View, Item, HGroup, Spring
from src.managers.manager import Manager
from src.hardware.core.pid_object import PIDObject
import os
from src.helpers.paths import hidden_dir
import apptools.sweet_pickle as pickle
from src.helpers.timer import Timer
from src.graph.stream_graph import StreamGraph
import random

class BrightnessPIDManager(Manager):
    pid_object = Instance(PIDObject)
    brightness_timer = None
    pid_loop_period = 200
    setpoint = Float(auto_set=False, enter_set=True)
    output = Float
    error = Float
    graph = Instance(StreamGraph, transient=True)
    machine_vision = Any(transient=True)
    _collect_baseline = Bool(True)

    def _graph_default(self):
        g = StreamGraph(container_dict=dict(padding=5),)
        g.new_plot(data_limit=60)
        g.new_series()
        g.new_series()

        return g

    def _setpoint_changed(self):
        if self._collect_baseline:
            self._collect_baseline = False
            if self.machine_vision:
                self.machine_vision.collect_baseline_intensity()
        self.set_brightness_setpoint(self.setpoint)

    def set_brightness_setpoint(self, b):
        #start a timer for the pid loop
        self.info('setting brightness {}'.format(b))
        #stop the timer if its already running
        if self.brightness_timer:
            self.brightness_timer.Stop()

        if b:
            self.brightness_timer = Timer(self.pid_loop_period, self.set_output, b)

    def set_output(self, sp):
        #get the current brightness
        if self.machine_vision:
            intensity = self.machine_vision.get_intensity(verbose=False)
            err = sp - intensity
        else:
            err = sp + random.random()
#        val = sp + random.random()
#        err = val - sp

        out = self.pid_object.iterate(err, self.pid_loop_period)

        if self.parent:
            self.parent.set_laser_power(out)

        self.output = out
        self.error = err
        self.graph.record_multiple((err, out), do_after=10)

    def _pid_object_default(self):
        return self.load_pid_object()

    def load_pid_object(self):
        p = os.path.join(hidden_dir, 'brightness_pid_object')
        if os.path.isfile(p):
            self.info('loading pid object from {}'.format(p))
            try:
                with open(p, 'rb') as f:
                    po = pickle.load(f)
            except pickle.PickleError, e:
                self.info('error loading pid object from {}, {}'.format(p, e))
                po = PIDObject()
        else:
            po = PIDObject()

        return po

    def dump_pid_object(self):

        try:
            p = os.path.join(hidden_dir, 'brightness_pid_object')
            self.info('dumping pid object to {}'.format(p))
            with open(p, 'wb') as f:
                pickle.dump(self.pid_object, f)
        except pickle.PickleError:
            pass


    def close(self, is_ok):
        self.dump_pid_object()
        return True

    def traits_view(self):
        v = View(Item('pid_object', style='custom', show_label=False),
                 Item('setpoint'),
                 HGroup(Item('output', style='readonly', format_str='%0.3f'),
                        Spring(width=60, springy=False),
                         Item('error', style='readonly', format_str='%0.3f')),
                 Item('graph', show_label=False, style='custom'),
                 handler=self.handler_klass(),
                 resizable=True,
                 title='Configure Brightness Meter',
                 id='pychron.fusions.co2.brightness_meter'
                 )

        return v

if __name__ == '__main__':
    from src.helpers.logger_setup import logging_setup
    logging_setup('bm')
    b = BrightnessPIDManager()
    b.configure_traits()
