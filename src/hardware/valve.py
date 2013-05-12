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
from traits.api import  Str, Any, Bool, List, Float, Int, Property
from traitsui.api import View, Item, VGroup
#============= standard library imports ========================
#============= local library imports  ==========================
from state_machine.valve_FSM_sm import Valve_sm
from src.loggable import Loggable


class HardwareValve(Loggable):
    '''
    '''
    name = Str
    display_name = Str
    display_state = Property(depends_on='state')
    display_software_lock = Property(depends_on='software_lock')

    address = Str
    actuator = Any

#    success = Bool(False)
    interlocks = List
    state = Bool(False)
#    debug = False
#    error = None
    software_lock = False

    cycle_period = Float(1)
    cycle_n = Int(10)
    sample_period = Float(1)

    actuator_name = Property(depends_on='actuator')
#    actuator_name = DelegatesTo('actuator', prefix='name')

    canvas_valve = Any
    position = Property
#    shaft_low = Property
#    shaft_high = Property

    query_state = Bool(True)
    description = Str

    enabled = Bool(True)

    def __init__(self, name, *args, **kw):
        '''
     
        '''
        self.display_name = name
        kw['name'] = 'VALVE-{}'.format(name)

        super(HardwareValve, self).__init__(*args, **kw)
        self._fsm = Valve_sm(self)

    def is_name(self, name):
        if len(name) == 1:
            name = 'VALVE-{}'.format(name)
        return name == self.name

    def get_lock_state(self):
        if self.actuator:
            return self.actuator.get_lock_state(self)

    def set_state(self, state):
        self.state = state

    def get_hardware_state(self):
        '''
        '''
        result = None
        if self.actuator is not None:
            result = self.actuator.get_channel_state(self)
            if isinstance(result, bool):
                self.set_state(result)
            else:
                result = False

        return result

    def set_open(self, mode='normal'):
        self.info('open mode={}'.format(mode))
#        current_state = copy(self.state)
        state_change = False
        success = True
        if self.software_lock:
            self._software_locked()
        else:
            success = self._open_()
            if success:
                if self.state == False:
                    state_change = True
                self.state = True

        return success, state_change

    def set_closed(self, mode='normal'):
        self.info('close mode={}'.format(mode))
#        current_state = copy(self.state)
        state_change = False
        success = True
        if self.software_lock:
            self._software_locked()
        else:
#            print 'pre state', self.state, current_state
            success = self._close_()
            if success:
#                print 'self.state',self.state, current_state
                if self.state == True:
                    state_change = True
                self.state = False

        return success, state_change

    def _software_locked(self):
        self.info('{}({}) software locked'.format(self.name, self.description))

    def lock(self):
        self.software_lock = True

    def unlock(self):
        self.software_lock = False

    def _open_(self, mode='normal'):
        '''
        '''
        actuator = self.actuator
        r = True
        if mode == 'debug':
            r = True
        elif self.actuator is not None:
            if mode.startswith('client'):
                # always actuate if mode is client
                r = True if actuator.open_channel(self) else False
            else:
                # dont actuate if already open
                if self.state == True:
                    r = True
                else:
                    r = True if actuator.open_channel(self) else False

            if actuator.simulation:
                r = True
        return r

    def _close_(self, mode='normal'):
        '''
        '''
        r = True
        actuator = self.actuator
        if mode == 'debug':
            r = True

        elif actuator is not None:
            if mode.startswith('client'):
                print 'close', self.state
                r = True if actuator.close_channel(self) else False
            else:
                # dont actuate if already closed
                if self.state == False:
                    r = True
                else:
                    r = True if actuator.close_channel(self) else False

            if actuator.simulation:
                r = True
        return r

#    def _get_shaft_low(self):
#        if self.canvas_valve:
#            return self.canvas_valve.low_side.orientation
#
#    def _get_shaft_high(self):
#        if self.canvas_valve:
#            return self.canvas_valve.high_side.orientation

    def _get_position(self):
        if self.canvas_valve:
            return ','.join(map(str, self.canvas_valve.translate))

    def _get_display_state(self):
        return 'Open' if self.state else 'Close'

    def _get_display_software_lock(self):
        return 'Yes' if self.software_lock else 'No'

    def _get_actuator_name(self):
        name = ''
        if self.actuator:
            name = self.actuator.name
        return name

    def traits_view(self):
        info = VGroup(
                    Item('display_name', label='Name', style='readonly'),
                    Item('display_software_lock', label='Locked', style='readonly'),
                    Item('address', style='readonly'),
                    Item('actuator_name', style='readonly'),
                    Item('display_state', style='readonly'),
                    show_border=True,
                    label='Info'
                    )
        sample = VGroup(
                       Item('sample_period', label='Period (s)'),
                       label='Sample',
                       show_border=True
                       )
        cycle = VGroup(
                   Item('cycle_n', label='N'),
                   Item('sample_period', label='Period (s)'),
                   label='Cycle',
                   show_border=True
                   )
        geometry = VGroup(
                          Item('position', style='readonly'),
#                          Item('shaft_low', style='readonly'),
#                          Item('shaft_high', style='readonly'),
                          label='Geometry',
                          show_border=True
                          )
        return View(
                    VGroup(info, sample, cycle, geometry),

#                    buttons=['OK', 'Cancel'],
                    title='{} Properties'.format(self.name)
                    )

#============= EOF ====================================
#    def open(self, mode='normal'):
#        '''
#
#        '''
#        self._state_change = False
#        self.info('open mode={}'.format(mode))
#        self.debug = mode == 'debug'
#        self._fsm.Open()
#
# #        if mode in ['auto', 'manual', 'debug', 'remote']:
# #            self._fsm.Open()
#
#        result = self.success
#        if self.error is not None:
#            result = self.error
#            self.error = None
#
#        if not result:
#            pass
#            #self._fsm.RClose()
#
#        return result, self._state_change
#
#    def close(self, mode='normal'):
#        '''
#
#        '''
#        self._state_change = False
#        self.info('close mode={}'.format(mode))
#
#        self.debug = mode == 'debug'
# #        if mode in ['auto', 'manual', 'debug', 'remote']:
# #            self._fsm.Close()
#        self._fsm.Close()
#
#        result = self.success
#        if self.error is not None:
#            result = self.error
#            self.error = None
#
#        if not result:
#            pass
#            #self._fsm.ROpen()
#
#        return result, self._state_change

#    def acquire_critical_section(self):
#        self._critical_section = True
#
#    def release_system_lock(self):
#        self._critical_section = False
#
#    def isCritical(self):
#        return self._critical_section
#    def _error_(self, message):
#        self.error = message
#        self.warning(message)

#    def warning(self, msg):
#        '''
#            @type msg: C{str}
#            @param msg:
#        '''
# #        super(HardwareValve, self).warning(msg)
#        Loggable.warning(self, msg)
#        self.success = False
#    def get_hard_lock(self):
#        '''
#        '''
#        if self.actuator is not None:
#            r = self.actuator.get_hard_lock_indicator_state(self)
#        else:
#            r = False
#
#        return r
#
#    def get_hard_lock_indicator_state(self):
#        '''
#        '''
#
#        s = self.get_hardware_state()
#        r = self.get_hard_lock()
#
#        if r:
#            if s:
#                self._fsm.HardLockOpen()
#            else:
#                self._fsm.HardLockClose()
#        else:
#            self._fsm.HardUnLock()
#        #print self.auto
#        return r
