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
from traits.api import List, Str, HasTraits, Float, Int
from traitsui.api import View, HGroup, Item, ListEditor, InstanceEditor, Group
#=============standard library imports ========================
from numpy import random, char

#=============local library imports  ==========================
from src.hardware.core.core_device import CoreDevice
# from src.ui.color_map_bar_editor import BarGaugeEditor
import time
from src.ui.color_map_bar_editor import BarGaugeEditor

# from numpy import linspace
# def gen():
#    for xi in linspace(5e-10, 5e-8, 25):
#        yield xi
#
# pgen = gen()

class Gauge(HasTraits):
    name = Str
    display_name = Str
    pressure = Float(1.0)
    low = 5e-10
    high = 1e-8
    color_scalar = 1
    width = Int(100)
    def traits_view(self):
        v = View(HGroup(Item('display_name', show_label=False, style='readonly',
                             width=-30,
                             ),
                         Item('pressure',
                              format_str='%0.2e',
                              show_label=False,
                              style='readonly'
                              ),
                        Item('pressure',
                             show_label=False,
                             width=self.width,
                             editor=BarGaugeEditor(low=self.low,
                                                   high=self.high,
                                                   color_scalar=self.color_scalar,
                                                   width=self.width
                                                   )
                             )

                        )
                 )
        return v

class MicroIonController(CoreDevice):
    scan_func = 'get_pressures'
    address = '01'
    gauges = List
    display_name = Str

    def gauge_view(self):
        v = View(
                 Group(
                     Item('gauges', style='custom',
                          show_label=False,
                          editor=ListEditor(mutable=False,
                                            style='custom',
                                        editor=InstanceEditor())),
                       show_border=True,
                       label=self.display_name
                       ),
#                 height= -100
                 )
        return v

    def load_additional_args(self, config, *args, **kw):
        self.address = self.config_get(config, 'General', 'address', optional=False)
        self.display_name = self.config_get(config, 'General', 'name', default=self.name)

        ns = self.config_get(config, 'Gauges', 'names')
        if ns:
            ans = self.config_get(config, 'Gauges', 'display_names', optional=True)
            if not ans:
                ans = ns

            lows = self.config_get(config, 'Gauges', 'lows', optional=True, default='1e-10, 1e-3, 1e-3')
            highs = self.config_get(config, 'Gauges', 'highs', optional=True, default='1e-6, 1, 1')
            cs = self.config_get(config, 'Gauges', 'color_scalars', optional=True, default='1, 1, 1')

            for gi in zip(*map(lambda x: x.split(','), (ns, ans, lows, highs, cs))):
                ni, ai, li, hi, ci = map(str.strip, gi)

                g = Gauge(name=ni, display_name=ai)
                try:
                    g.low = float(li)
                except ValueError, e:
                    self.warning_dialog('Invalid lows string. {}'.format(e), title=self.config_path)
                    continue

                try:
                    g.high = float(hi)
                except ValueError, e:
                    self.warning_dialog('Invalid highs string. {}'.format(e), title=self.config_path)
                    continue
                try:
                    g.color_scalar = int(ci)
                except ValueError, e:
                    self.warning_dialog('Invalid color_scalar string. {}'.format(e), title=self.config_path)
                    continue

                self.gauges.append(g)

        return True

    def graph_builder(self, g):
        super(MicroIonController, self).graph_builder(g, show_legend=True)
        g.new_series()
        g.set_series_label('IG', series=0)

        g.new_series()
        g.set_series_label('CG1', series=1)

        g.new_series()
        g.set_series_label('CG2', series=2)

    def get_gauge(self, name):
        return next((gi for gi in self.gauges
                            if gi.name == name or gi.display_name == name), None)

    def _set_gauge_pressure(self, name, v):
        g = self.get_gauge(name)
        if g is not None:
            try:
                g.pressure = float(v)
            except (TypeError, ValueError):
                pass

    def get_pressures(self, verbose=False):
#        self.debug('getting pressure')
        b = self.get_convectron_b_pressure(verbose=verbose)
        self._set_gauge_pressure('CG2', b)
        time.sleep(0.05)
        a = self.get_convectron_a_pressure(verbose=verbose)
        self._set_gauge_pressure('CG1', a)
        time.sleep(0.05)

        ig = self.get_ion_pressure(verbose=verbose)
        self._set_gauge_pressure('IG', ig)

        return ig, a, b
        # return self.get_convectron_a_pressure()

    def set_degas(self, state):
        key = 'DG'
        value = 'ON' if state else 'OFF'
        cmd = self._build_command(key, value)
        r = self.ask(cmd)
        r = self._parse_response(r)
        return r

    def get_degas(self):
        key = 'DGS'
        cmd = self._build_command(key)
        r = self.ask(cmd)
        r = self._parse_response(r)
        return r

    def get_ion_pressure(self, **kw):
        name = 'IG'
        return self._get_pressure(name, **kw)

    def get_convectron_a_pressure(self, **kw):
        name = 'CG1'
        return self._get_pressure(name, **kw)

    def get_convectron_b_pressure(self, **kw):
        name = 'CG2'
        return self._get_pressure(name, **kw)

    def set_ion_gauge_state(self, state):
        key = 'IG1'
        value = 'ON' if state else 'OFF'
        cmd = self._build_command(key, value)
        r = self.ask(cmd)
        r = self._parse_response(r)
        return r

    def get_process_control_status(self, channel=None):
        key = 'PCS'

        cmd = self._build_command(key, channel)

        r = self.ask(cmd)
        r = self._parse_response(r)

        if channel is None:
            if r is None:
                # from numpy import random,char
                r = random.randint(0, 2, 6)
                r = ','.join(char.array(r))

            r = r.split(',')
        return r

    def _get_pressure(self, name, verbose=False):
        key = 'DS'
        cmd = self._build_command(key, name)

        r = self.ask(cmd, verbose=False)
        r = self._parse_response(r, name)
        return r

    def _build_command(self, key, value=None):

        # prepend key with our address
        # example of new string formating
        # see http://docs.python.org/library/string.html#formatspec
        key = '#{}{}'.format(self.address, key)
        if value is not None:
            args = (key, value)
        else:
            args = (key,)
        c = ' '.join(args)

        return  c

    def _parse_response(self, r, name):
        if self.simulation or r is None:
            from numpy.random import normal
            if name == 'IG':
                loc, scale = 1e-9, 5e-10
#                return pgen.next()
            else:
                loc, scale = 1e-2, 5e-3
            return abs(normal(loc, scale))

#            r = self.get_random_value(0, 10000) / 10000.0

        return r


#============= EOF ====================================
