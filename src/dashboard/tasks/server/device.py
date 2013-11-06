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
from traits.api import HasTraits, Str, Either, Float, Property, Bool, List, Instance, \
    Event
from traitsui.api import View, Item, ListEditor, InstanceEditor, UItem, VGroup, HGroup

#============= standard library imports ========================
import time
#============= local library imports  ==========================
from src.hardware.core.i_core_device import ICoreDevice
from src.helpers.datetime_tools import convert_timestamp
from src.loggable import Loggable


class ProcessValue(HasTraits):
    name = Str
    tag = Str
    func_name = Str

    period = Either(Float, Str) #"on_change" or number of seconds
    last_time = Float
    last_time_str = Property(depends_on='last_time')
    enabled = Bool
    last_value = Float

    def traits_view(self):
        v = View(VGroup(HGroup(UItem('enabled'), Item('name')),
                        VGroup(Item('tag'),
                               Item('period'),
                               Item('last_time_str', style='readonly'),
                               Item('last_value', style='readonly'),
                               enabled_when='enabled')))
        return v

    def _get_last_time_str(self):
        r = ''
        if self.last_time:
            r = convert_timestamp(self.last_time)

        return r


class DashboardDevice(Loggable):
    name = Str
    use = Bool

    values = List
    _device = Instance(ICoreDevice)

    publish_event = Event

    def trigger(self):
        """
            trigger a new value if appropriate
        """

        for value in self.values:
            if not value.enabled:
                continue

            st = time.time()
            dt = st - value.last_time
            if value.period == 'on_change':
                if value.timeout and dt > value.timeout:
                    self._push_value(value, 'timeout')

                continue

            if dt > value.period:
                try:
                    nv = getattr(self._device, value.func_name)()
                    value.last_value = nv
                    self._push_value(value, nv)
                except Exception:
                    import traceback

                    self.debug(traceback.format_exc(limit=2))
                    value.use_pv = False

    def add_value(self, n, tag, func_name, period, use):
        pv = ProcessValue(name=n,
                          tag=tag,
                          func_name=func_name,
                          period=period,
                          enabled=use)

        if period == 'on_change':
            self.debug('bind to {}'.format(n))

            self._device.on_trait_change(lambda a, b, c, d: self._handle_change(pv, a, b, c, d), n)
            #self._device.on_trait_change(lambda new: self._push_value(pv, new), n)

        self.values.append(pv)

    def _handle_change(self, pv, obj, name, old, new):
        self.debug('handle change {} {}'.format(name, new))
        self._push_value(pv, new)

    def _push_value(self, pv, new):
        if pv.enabled:
            tag = pv.tag
            self.publish_event = '{} {}'.format(tag, new)
            pv.last_time = time.time()

    def traits_view(self):
        hgrp = HGroup(UItem('use'), UItem('name', style='readonly'))
        dgrp = VGroup(UItem('values',
                            editor=ListEditor(editor=InstanceEditor(),
                                              style='custom',
                                              mutable=False), ),
                      show_border=True,
                      enabled_when='use')
        v = View(VGroup(hgrp,
                        dgrp))
        return v

#============= EOF =============================================
