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
from traits.api import Property, Dict, Float, Any, Instance
from traitsui.api import View, VGroup, Item, RangeEditor
from pyface.timer.api import Timer
# from src.helpers.timer import Timer
#============= standard library imports ========================
import os

#============= local library imports  ==========================
from src.hardware.core.core_device import CoreDevice
from src.hardware.core.motion.motion_profiler import MotionProfiler
import time
from pyface.timer.do_later import do_later
from threading import Thread


class MotionController(CoreDevice):
    '''
    '''
    axes = Dict
    xaxes_max = Property
    xaxes_min = Property
    yaxes_max = Property
    yaxes_min = Property
    zaxes_max = Property
    zaxes_min = Property

    group_parameters = None
    timer = None
    parent = Any

    x = Property(trait=Float(enter_set=True, auto_set=False),
               depends_on='_x_position')
    _x_position = Float
    y = Property(trait=Float(enter_set=True, auto_set=False),
               depends_on='_y_position')
    _y_position = Float

    z = Property(trait=Float(enter_set=True, auto_set=False),
           depends_on='_z_position')

    _z_position = Float
    z_progress = Float
    motion_profiler = Instance(MotionProfiler, ())

    groupobj = None

    def update_axes(self):
        for a in self.axes:
            pos = self.get_current_position(a)
#            print 'pos', pos, a
            if pos is not None:
                setattr(self, '_{}_position'.format(a), pos)
#            time.sleep(0.075)
        self.z_progress = self._z_position

#        def _update():
#        print self._x_position, self._y_position
        self.parent.canvas.set_stage_position(self._x_position,
                                              self._y_position)


#        do_later(_update)

    def timer_factory(self, func=None):
        '''
        '''
        if self.timer is not None:
            self.timer.Stop()

        if func is None:
            func = self._inprogress_update
        self._not_moving_count = 0
        return Timer(250, func)

    def set_z(self, v, **kw):
        self.single_axis_move('z', v, **kw)
#        setattr(self, '_{}_position'.format('z'), v)
        self._z_position = v
        self.axes['z'].position = v

    def block(self, *args, **kw):
        self._block_(*args, **kw)

    def axes_factory(self, config=None):
        if config is None:

            config = self.get_configuration(self.config_path)

        mapping = self.config_get(config, 'General', 'mapping')
        if mapping is not None:
            mapping = mapping.split(',')
        else:
            mapping = 'x,y,z'

        lp = self.config_get(config, 'General', 'loadposition')
        if lp is not None:
            loadposition = [float(f) for f in lp.split(',')]
        else:
            loadposition = [0, 0, 0]

        config_path = self.configuration_dir_path
        for i, a in enumerate(mapping):
            self.info('loading axis {},{}'.format(i, a))
            limits = [float(v) for v in config.get('Axes Limits', a).split(',')]
            na = self._axis_factory(config_path,
                                  name=a,
                                  id=i + 1,
                                  negative_limit=limits[0],
                                  positive_limit=limits[1],
                                  loadposition=loadposition[i]
                                  )

            self.axes[a] = na

#===============================================================================
# define in subclass
#===============================================================================
    def save_axes_parameters(self):
        pass

    def get_xyz(self):
        return 0, 0, 0

    def get_current_position(self, *args, **kw):
        return 0

    def execute_command_buffer(self, *args, **kw):
        pass
#    def enqueue_move(self, *args, **kw):
#        pass

    def set_smooth_transitions(self, *args, **kw):
        pass

    def set_program_mode(self, *args, **kw):
        pass

    def linear_move(self, *args, **kw):
        pass

    def set_home_position(self, *args, **kw):
        pass

    def single_axis_move(self, *args, **kw):
        pass

    def define_home(self):
        pass

    def set_single_axis_motion_parameters(self, *args, **kw):
        pass

#===============================================================================
# private
#===============================================================================
    def _set_axis(self, name, v, **kw):
        if v is None:
            return

        c = getattr(self, '_{}_position'.format(name))
        disp = abs(c - v)
        self.single_axis_move(name, v, update=disp > 4, **kw)

        setattr(self, '_{}_position'.format(name), v)
        self.axes[name].position = v

        if disp <= 4:
            self.parent.canvas.clear_desired_position()

    def _z_inprogress_update(self):
        '''
        '''
        if not self._moving_():
            self.timer.Stop()

        z = self.get_current_position('z')
        self.z_progress = z

    def _inprogress_update(self):
        '''
        '''

        if not self._moving_():
            self.timer.Stop()
            self.parent.canvas.clear_desired_position()
            self.update_axes()
        else:
            x = self.get_current_position('x')
            y = self.get_current_position('y')
            self.parent.canvas.set_stage_position(x, y)

    def _sign_correct(self, val, key, ratio=True):
        '''
        '''
        if val is not None:
            axis = self.axes[key]
            r = 1
            if ratio:
                r = axis.drive_ratio
    #            self.info('using drive ratio {}={}'.format(key, r))

            return val * axis.sign * r

    def _block_(self, axis=None, event=None):
        '''
        '''
        if event is not None:
            event.clear()

        func = lambda: self._moving_(axis=axis)
        if self.timer is not None:
            # timer is calling self._moving_
            func = lambda: self.timer.IsRunning()

#        print func, self.timer
        time.sleep(0.25)

        a = func()
        while a:
            a = func()
#            print a
            time.sleep(0.2)

        if event is not None:
            event.set()
#===============================================================================
# property get/set
#===============================================================================
    def _get_x(self):
        return self._x_position

    def _get_y(self):
        return self._y_position

    def _get_z(self):
        return self._z_position

    def _set_x(self, v):
        self._set_axis('x', v)

    def _set_y(self, v):
        self._set_axis('y', v)

    def _set_z(self, v):
        if v is not None:
            self.set_z(v)

    def _validate_x(self, v):
        return self._validate(v, 'x', self._x_position)

    def _validate_y(self, v):
        return self._validate(v, 'y', self._y_position)

    def _validate_z(self, v):
        return self._validate(v, 'z', self._z_position)

    def _validate(self, v, key, cur):
        '''
        '''
        mi = self.axes[key].negative_limit
        ma = self.axes[key].positive_limit

        try:
            v = float(v)
            if not mi <= v <= ma:
                v = None

            if v is not None:
                if abs(v - cur) <= 0.001:
                    v = None
        except ValueError:
            v = None

        return v

    def _get_xaxes_max(self):
        return self._get_positive_limit('x')

    def _get_xaxes_min(self):
        return self._get_negative_limit('x')

    def _get_yaxes_max(self):
        return self._get_positive_limit('y')

    def _get_yaxes_min(self):
        return self._get_negative_limit('y')

    def _get_zaxes_max(self):
        return self._get_positive_limit('z')

    def _get_zaxes_min(self):
        return self._get_negative_limit('z')

    def _get_positive_limit(self, key):
        return self.axes[key].positive_limit if self.axes.has_key(key) else 0
    def _get_negative_limit(self, key):
        return self.axes[key].negative_limit if self.axes.has_key(key) else 0

#===============================================================================
# view
#===============================================================================
    def traits_view(self):
        return View(self.get_control_group())

    def get_control_group(self):
        g = VGroup(show_border=True,
                   label='Axes')

        keys = self.axes.keys()
        keys.sort()
        for k in keys:

            editor = RangeEditor(low_name='{}axes_min'.format(k),
                                  high_name='{}axes_max'.format(k),
                                  mode='slider',
                                  format='%0.3f')

            g.content.append(Item(k, editor=editor))
            if k == 'z':
                g.content.append(Item('z_progress', show_label=False,
                                      editor=editor,
                                      enabled_when='0'
                                      ))
        return g
#===============================================================================
# defaults
#===============================================================================
    def _motion_profiler_default(self):
        mp = MotionProfiler()
        if self.configuration_dir_path:
            p = os.path.join(self.configuration_dir_path, 'motion_profiler.cfg')
            mp.load(p)
        return mp
#============= EOF ====================================
