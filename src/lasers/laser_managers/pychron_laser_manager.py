#===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import Int, CInt, Str, String, on_trait_change, Button, Float, \
    Property, Event, Bool, Enum, cached_property, Range

from traitsui.api import View, Item, VGroup, HGroup, spring, RangeEditor, EnumEditor, \
    TextEditor
import apptools.sweet_pickle as pickle
#============= standard library imports ========================
import time
from threading import Thread
#============= local library imports  ==========================
from src.hardware.core.communicators.ethernet_communicator import EthernetCommunicator
from src.lasers.laser_managers.laser_manager import BaseLaserManager
from src.helpers.filetools import str_to_bool
import os
from src.paths import paths
from src.regex import TRANSECT_REGEX


class PychronLaserManager(BaseLaserManager):
    '''
    A PychronLaserManager is used to control an instance of 
    pychron remotely. 
    
    Common laser functions such as enable_laser are converted to 
    the RemoteHardwareServer equivalent and sent by the _communicator
    
    e.g enable_laser ==> self._communicator.ask('Enable')
    
    The communicators connection arguments are set in initialization.xml
    
    use a communicator block
    <plugin enabled="true" fire_mode="client">FusionsDiode
        ...
        <communications>
          <host>129.138.12.153</host>
          <port>1069</port>
          <kind>UDP</kind>
        </communications>
    </plugin>
    '''

    port = CInt
    host = Str

    _cancel_blocking = False

    position = String(enter_set=True, auto_set=False)
    x = Property(depends_on='_x')
    y = Property(depends_on='_y')
    z = Property(depends_on='_z')
    _x = Float
    _y = Float
    _z = Float
    connected = Bool
    test_connection_button = Button('Test Connection')

    mode = 'client'

    def _test_connection_button_fired(self):
        self.test_connection()
        if self.connected:
            self.opened(None)

    def test_connection(self):
        self.connected = self._communicator.open()
        return self.connected

    def bind_preferences(self, pref_id):
        pass

    def open(self):
        host = self.host
        port = self.port

        self._communicator = ec = EthernetCommunicator(host=host,
                                                       port=port)
        r = ec.open()
        if r:
            self.connected = True
        return r

    def opened(self, ui):
        self.update_position()
        self._opened_hook()

    def _opened_hook(self):
        pass

    def update_position(self):
        self.trait_set(**dict(zip(('_x', '_y', '_z'),
                                  self.get_position())))

#===============================================================================
# patterning
#===============================================================================
    def execute_pattern(self, name=None, block=False):
        '''
            name is either a name of a file 
            of a pickled pattern obj
        '''
        if name:
            return self._execute_pattern(name)
#        pm = self.pattern_executor
#        pattern = pm.load_pattern(name)
#        if pattern:
#            t = Thread(target=self._execute_pattern,
#                       args=(pattern,))
#            t.start()
#            if block:
#                t.join()
#
#            return True

    def _execute_pattern(self, name):
        '''
        '''
#        name = pattern.name
        self.info('executing pattern {}'.format(name))
#        pm = self.pattern_executor

#        pm.start()

        # set the current position
#        xyz = self.get_position()
#        if xyz:
#            pm.set_current_position(*xyz)
#        '''
#            look for pattern name in local pattern dir
#            if exists send the pickled pattern string instead of
#            the name
#        '''
#        if pm.is_local_pattern(name):
#            txt = pickle.dumps(pattern)
#            msg = 'DoPattern <local pickle> {}'.format(name)
#        else:
#            msg = 'Do Pattern {}'.format(name)


#        '''
#            display an alternate message
#            if is local pattern then txt is a binary str
#            log msg instead of cmd
#        '''
        if not name.endswith('.lp'):
            name = '{}.lp'.format(name)

        cmd = 'DoPattern {}'.format(name)
        self._ask(cmd, verbose=False)
#        self._communicator.info(msg)

        time.sleep(0.5)

        if not self._block('IsPatterning',
                           period=1
#                           position_callback=pm.set_current_position
                           ):
            cmd = 'AbortPattern'
            self._ask(cmd)

#        pm.finish()

    @on_trait_change('pattern_executor:pattern:canceled')
    def pattern_canceled(self):
        '''
            this patterning window was closed so cancel the blocking loop
        '''
        self._cancel_blocking = True

#===============================================================================
# pyscript commands
#===============================================================================
    def take_snapshot(self, name):
        self.info('Take snapshot')
        self._ask('Snapshot {}'.format(name))

    def prepare(self):
        self.info('Prepare laser')
        self._ask('Prepare')

        cnt = 0
        tries = 0
        maxtries = 200  # timeout after 50 s
        nsuccess = 1
        self._cancel_blocking = False
        ask = self._ask
        period = 1
        cmd = 'IsReady'
        while tries < maxtries and cnt < nsuccess:
            if self._cancel_blocking:
                break
            time.sleep(period)
            resp = ask(cmd)
            if resp is not None:
                try:
                    if str_to_bool(resp):
                        cnt += 1
                except:
                    cnt = 0
            else:
                cnt = 0
            tries += 1

        return cnt >= nsuccess

    def extract(self, value, units=''):
        self.info('set laser output')
        return self._ask('SetLaserOutput {} {}'.format(value, units)) == 'OK'


    def enable_laser(self, *args, **kw):
        self.info('enabling laser')
        return self._ask('Enable') == 'OK'

    def disable_laser(self, *args, **kw):
        self.info('disabling laser')
        return self._ask('Disable') == 'OK'

    def set_laser_power(self, v, *args, **kw):
        self.info('set laser power {}'.format(v))
        return self._ask('SetLaserPower {}'.format(v)) == 'OK'

    def set_motor_lock(self, name, value):
        v = 'YES' if value else 'NO'
        self.info('set motor {} lock to {}'.format(name, v))
        self._ask('SetMotorLock {} {}'.format(name, int(value)))
        return True

    def set_motor(self, name, value):
        self.info('set motor {} to {}'.format(name, value))
        self._ask('SetMotor {} {}'.format(name, value))
        time.sleep(0.5)
        r = self._block(cmd='GetMotorMoving {}'.format(name))
        return r

    def get_position(self):
        xyz = self._ask('GetPosition')
        if xyz:
            try:
                x, y, z = map(float, xyz.split(','))
                return x, y, z
            except Exception, e:
                print 'pychron laser manager get_position', e
                return 0, 0, 0

        if self._communicator.simulation:
            return 0, 0, 0
#===============================================================================
# pyscript private
#===============================================================================
    def _move_to_position(self, pos):
        cmd = 'GoToHole {}'.format(pos)
        if isinstance(pos, tuple):
            cmd = 'SetXY {}'.format(pos[:2])
#            if len(pos) == 3:
#                cmd = 'SetZ {}'.format(pos[2])

        self.info('sending {}'.format(cmd))
        self._ask(cmd)
        time.sleep(0.5)
        r = self._block()
        self.update_position()
        return r

    def _block(self, cmd='GetDriveMoving', period=0.25, position_callback=None):

        ask = self._ask

        cnt = 0
        tries = 0
        maxtries = 200  # timeout after 50 s
        nsuccess = 4
        self._cancel_blocking = False
#        period = 0.25
        while tries < maxtries and cnt < nsuccess:
            if self._cancel_blocking:
                break

            time.sleep(period)
            resp = ask(cmd)

            if self._communicator.simulation:
                resp = 'False'

            if resp is not None:
                try:
                    if not str_to_bool(resp):
                        cnt += 1
                except:
                    cnt = 0

                if position_callback:

                    if self._communicator.simulation:
                        x, y, z = cnt / 3., cnt / 3., 0
                        position_callback(x, y, z)
                    else:
                        xyz = self.get_position()
                        if xyz:
                            position_callback(*xyz)

            else:
                cnt = 0
            tries += 1

        state = cnt >= nsuccess
        if state:
            self.info('Move completed')
        else:
            if self._cancel_blocking:
                self.info('Move failed. canceled by user')
            else:
                self.info('Move failed. timeout after {}s'.format(maxtries * period))

        return state

    def _ask(self, cmd, **kw):
        self._communicator.get_handler()
        return self._communicator.ask(cmd, **kw)

    def _enable_fired(self):
        if self.enabled:
            self.disable_laser()
            self.enabled = False
        else:
            if self.enable_laser():
                self.enabled = True

    def _position_changed(self):
        if self.position is not None:
            t = Thread(target=self._move_to_position, args=(self.position,))
            t.start()
            self._position_thread = t
#     def traits_view(self):
#         v = View(
#                  Item('test_connection_button', show_label=False),
#                  self.get_control_button_group(),
#                  Item('position'),
#                  Item('x', editor=RangeEditor(low= -25.0, high=25.0)),
#                  Item('y', editor=RangeEditor(low= -25.0, high=25.0)),
#                  Item('z', editor=RangeEditor(low= -25.0, high=25.0)),
#                  title='Laser Manager',
#                  handler=self.handler_klass
#                  )
#         return v

    def _set_x(self, v):
        self._ask('SetX {}'.format(v))
        self.update_position()
#        self._x=v

    def _set_y(self, v):
        self._ask('SetY {}'.format(v))
        self.update_position()
#        self._y=v

    def _set_z(self, v):
        self._ask('SetZ {}'.format(v))
        self.update_position()
#        self._z=v

    def _get_x(self):
        return self._x
    def _get_y(self):
        return self._y
    def _get_z(self):
        return self._z


class PychronUVLaserManager(PychronLaserManager):
    fire = Event
    fire_label = Property(depends_on='firing')
    firing = Bool
    fire_mode = Enum('Burst', 'Continuous')
    nburst = Property(depends_on='_nburst')
    _nburst = Int

    mask = Str(enter_set=True, auto_set=False)
    masks = Property
    attenuator = Str(enter_set=True, auto_set=False)
    attenuators = Property
    zoom = Range(0.0, 100.0)

    def extract(self, power):
        self._set_nburst(power)
        self._ask('Fire burst')

    def end_extract(self):
        self._ask('Fire stop')

    def trace_path(self, value, name, kind):
        if isinstance(name, list):
            name = name[0]

        # traces need to be prefixed with 'l'
        name = str(name)
        name = name.lower()
#        if not name.startswith('l'):
#            name = 'l{}'.format(name)

        cmd = 'TracePath {} {} {}'.format(value, name, kind)
        self.info('sending {}'.format(cmd))
        self._ask(cmd)
        return self._block(cmd='IsTracing')

    def drill_point(self, value, name):
        cmd = 'DrillPoint'

#===============================================================================
#
#===============================================================================
    def _fire_fired(self):
        if self.firing:
            mode = 'stop'
            self.firing = False
        else:
            if self.fire_mode == 'Continuous':
                mode = 'continuous'
            else:
                mode = 'burst'
            self.firing = True

        self._ask('Fire {}'.format(mode))

#     def _position_changed(self):
#         if self.position is not None:
#             t = Thread(target=self._move_to_position, args=(self.position,))
#             t.start()
# #            self._move_to_position(self.position)

    @on_trait_change('mask, attenuator, zoom')
    def _motor_changed(self, name, new):
        if new is not None:
            t = Thread(target=self.set_motor, args=(name, new))
            t.start()

#===============================================================================
#
#===============================================================================
    def _opened_hook(self):
        nb = self._ask('GetNBurst')
        self._nburst = self._get_int(nb)

        mb = self._ask('GetBurstMode')
        if mb is not None:
            self.fire_mode = 'Burst' if mb == '1' else 'Continuous'

#    def _set_motor(self, name, value):
#        self.info('setting motor {} to {}'.format(name,value))
#        cmd='SetMotor {} {}'.format(name, value)
#        time.sleep(0.5)
#        self._ask(cmd)
#        r = self._block(cmd='GetMotorMoving {}'.format(name))
#        return r

    def _move_to_position(self, pos):

        cmd = 'GoToPoint'
        if pos.startswith('t'):
            if not TRANSECT_REGEX.match(pos):
                cmd = None

        if isinstance(pos, (str, unicode)):
            if not pos:
                return

            if pos[0].lower() in ['t', 'l', 'd']:
                cmd = 'GoToNamedPosition'

        if cmd:
            cmd = '{} {}'.format(cmd, pos)
            self.info('sending {}'.format(cmd))
            self._ask(cmd)
            time.sleep(0.5)
            r = self._block()
            self.update_position()
            return r

    def traits_view(self):
        v = View(Item('test_connection_button', show_label=False),
                 VGroup(
                     self.get_control_button_group(),
                     HGroup(self._button_factory('fire', 'fire_label', enabled='enabled'),
                            Item('fire_mode', show_label=False),
                            Item('nburst')
                            ),
                     Item('position'),
                     Item('zoom', style='simple'),
                     HGroup(Item('mask', editor=EnumEditor(name='masks')), Item('mask', show_label=False)),
                     HGroup(Item('attenuator', editor=EnumEditor(name='attenuators')), Item('attenuator', show_label=False)),
                     Item('x', editor=RangeEditor(low= -25.0, high=25.0)),
                     Item('y', editor=RangeEditor(low= -25.0, high=25.0)),
                     Item('z', editor=RangeEditor(low= -25.0, high=25.0)),
                     enabled_when='connected'
                     ),
                 title='Laser Manager',
                 handler=self.handler_klass
                 )
        return v


#===============================================================================
# property get/set
#===============================================================================
    @cached_property
    def _get_masks(self):
        return self._get_motor_values('masks')

    @cached_property
    def _get_attenuators(self):
        return self._get_motor_values('attenuators')

    def _get_motor_values(self, name):
        p = os.path.join(paths.device_dir, 'uv', '{}.txt'.format(name))
        values = []
        if os.path.isfile(p):
            with open(p, 'r') as fp:
                for lin in fp:
                    lin = lin.strip()
                    if not lin or lin.startswith('#'):
                        continue
                    values.append(lin)

        return values


    def _get_int(self, resp):
        r = 0
        if resp is not None:
            try:
                r = int(resp)
            except (ValueError, TypeError):
                pass
        return r
    def _validate_nburst(self, v):
        try:
            return int(v)
        except (ValueError, TypeError):
            pass

    def _set_nburst(self, v):
        if v is not None:
            v = int(v)
            self._ask('SetNBurst {}'.format(v))
            self._nburst = v

    def _get_nburst(self):
        return self._nburst

    def _get_fire_label(self):
        return 'Stop' if self.firing else 'Fire'
#        else:
#
#            return super(PychronUVLaserManager, self)._move_to_position(pos)

#============= EOF =============================================
