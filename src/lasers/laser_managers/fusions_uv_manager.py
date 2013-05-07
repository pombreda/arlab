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
from traits.api import Instance, Enum, Bool, Button, Str, DelegatesTo, Event, Property, \
    Int
from traitsui.api import View, Item, Group, HGroup, VGroup, Label, \
    EnumEditor, spring, ButtonEditor

#============= standard library imports ========================
import time

#============= local library imports  ==========================
from fusions_laser_manager import FusionsLaserManager
from src.hardware.fusions.fusions_uv_logic_board import FusionsUVLogicBoard
from src.hardware.fusions.atl_laser_control_unit import ATLLaserControlUnit
# from src.lasers.laser_managers.laser_shot_history import LaserShotHistory
from src.monitors.fusions_uv_laser_monitor import FusionsUVLaserMonitor
# from src.machine_vision.mosaic_manager import MosaicManager
from src.lasers.laser_managers.uv_gas_handler_manager import UVGasHandlerManager
from src.lasers.stage_managers.stage_map import UVStageMap
from src.lasers.laser_managers.laser_script_executor import UVLaserScriptExecutor
from src.geometry.geometry import calc_point_along_line
from src.ui.led_editor import LEDEditor
from src.paths import paths
from threading import Thread

class FusionsUVManager(FusionsLaserManager):
    '''
    '''
    name = 'fusions_uv'
#    attenuation = DelegatesTo('laser_controller')
#    attenuationmin = DelegatesTo('laser_controller')
#    attenuationmax = DelegatesTo('laser_controller')
#    update_attenuation = DelegatesTo('laser_controller')
    monitor_name = 'uv_laser_monitor'
    monitor_klass = FusionsUVLaserMonitor

    atl_controller = Instance(ATLLaserControlUnit)
    simulation = DelegatesTo('atl_controller')
    single_shot = Button('Single Shot')
    laser_status = Str

    fire_button = Event
    fire_label = Property(depends_on='firing')
    firing = Bool
    mode = Enum('Burst', 'Continuous', 'Single')
#    single_shot = Bool

    gas_handler = Instance(UVGasHandlerManager)
#    laseronoff = Event
#    laseronoff_label = Property(depends_on='_enabled')
#    _enabled = DelegatesTo('atl_controller')
#    fire_label = Property(depends_on='triggered')
#    triggered = DelegatesTo('atl_controller')

#    energy = DelegatesTo('atl_controller')
#    energymin = DelegatesTo('atl_controller')
#    energymax = DelegatesTo('atl_controller')
    energy_readback = DelegatesTo('atl_controller')
    pressure_readback = DelegatesTo('atl_controller')
    burst_readback = DelegatesTo('atl_controller')
    status_readback = DelegatesTo('atl_controller')
    action_readback = DelegatesTo('atl_controller')

    burst_shot = Int(enter_set=True, auto_set=False)
    reprate = Int(enter_set=True, auto_set=False)

    execute_button = DelegatesTo('laser_script_executor')
    execute_label = DelegatesTo('laser_script_executor')
    names = DelegatesTo('laser_script_executor')

    _is_tracing = False
    _cancel_tracing = False

    dbname = paths.uvlaser_db
    db_root = paths.uvlaser_db_root

    def prepare(self):
        controller = self.laser_controller
        return controller.prepare()

    def is_ready(self):
        controller = self.laser_controller
        atl = self.atl_controller
        # is nitrogen purged and flowing
        lc = controller.is_ready()

        # is atl on and warmed up
        ac = atl.is_enabled()
        return lc and ac
#
#    def goto_named_position(self, pos):
#        sm = self.stage_manager
# #        smap = sm._stage_map
#        pos = pos.lower()
# #        if pos.startswith('p'):
# #            pt = smap.get_point(pos)
# #            sm.set_z(pt['z'])
# #            sm.linear_move(pt['xy'][0], pt['xy'][1], block=False)
# #        elif pos.startswith('l'):
# #            lines = smap.get_line(pos)
# #            sm.move_polyline(lines)
# #        elif pos.startswith('d'):
# #            pt = smap.get_point(pos)
#
#        if pos.startswith('d'):
#            sm.canvas.get_
#        return 'OK'

    def set_motors_for_point(self, pt):
        for motor in ('mask', 'attenuator'):
            if hasattr(pt, motor):
                self.set_motor(motor, getattr(pt, motor), block=True)

    def goto_point(self, pos):
        sm = self.stage_manager
        pt = sm.canvas.get_point(pos)
#        sm = self.stage_manager._stage_map
#        pt = sm.get_point(pos)
        if pt:
            self.set_motors_for_point(pt)
            self.stage_manager.move_to_point(pt)
#            x,y=pt.x,pt.y
#            x, y = pt['xy']
#            self.info('goto point {}'.format(pos, x, y))
#            self.stage_manager.linear_move(x, y, block=False)
            result = True
        else:
            result = 'Invalid point'
        return result

    def drill_point(self, value, name):
        self.stage_manager.drill_point()

    def isTracing(self):
        return self._is_tracing

    def stop_trace(self):
        self._cancel_tracing = True
        self.stage_manager.stop()

    def trace_path(self, value, pathname, kind):
        pathname = pathname.lower()
        self._is_tracing = True
        self._cancel_tracing = False

        if pathname.startswith('r'):
            self._raster_polygon(pathname)
        else:
            if kind == 'continuous':
                func = self._continuous_trace_path
    #            self._continuous_trace_path(value, pathname)
            else:
                func = self._step_trace_path
    #            self._step_trace_path(value, pathname)
#            self._is_tracing = True
#            self._cancel_tracing = False

            t = Thread(target=func, args=(value, pathname))
            t.start()
        return 'OK'

    def _raster_polygon(self, name):
        atl = self.atl_controller
        atl.set_burst_mode(False)
        sm = self.stage_manager

        smap = sm._stage_map
        poly = smap.get_polygon(name)

        print poly
        sm._move_polygon(poly['points'], velocity=poly['velocity'],
                         motors=poly['motors'],
                         use_outline=poly['use_outline'],
                         offset=poly['offset'],
                         use_convex_hull=poly['use_convex_hull'],
                         scan_size=poly['scan_size'],
                         start_callback=atl.laser_run,
                         end_callback=atl.laser_stop
                         )

    def _continuous_trace_path(self, value, path, mode='smooth'):
        if mode == 'smooth':
            atl = self.atl_controller
            atl.set_burst_mode(False)
            sm = self.stage_manager
            sc = sm.stage_controller

            smap = sm._stage_map
            line = smap.get_line(path)

            # do smooth transitions between points
            sc.set_smooth_transitions(True)

            # enqueue all points
            sm._move_polyline(line,
                              start_callback=atl.laser_run,
                              end_callback=atl.laser_stop,
                              )

            # turn off smooth transitions
            sc.set_smooth_transitions(False)
        else:
            smap = sm._stage_map
            line = smap.get_line(path)
            seg = line[0]
            x, y = seg['xy']
            z = seg['z']
            sm.set_z(z, block=True)
            sm.linear_move(x, y, block=True)
            atl.laser_run()
            for si in line[1:]:
                if self._cancel_tracing:
                    break

                x, y = si['xy']
                z = si['z']
                v = si['velocity']
                sm.set_z(z, block=False)
                sm.linear_move(x, y, velocity=v,
                                   update_hole=False,
                                   use_calibration=False,
                                   block=True)
            atl.laser_stop()

        self._is_tracing = False

    def _step_trace_path(self, value, path):
        def step_func(x, y):
            self.stage_manager.linear_move(x, y, block=True)
            self.single_burst()

        sm = self.stage_manager._stage_map
        line = sm.get_line(path)
        points = line.points
        pt = points[0]

        tol = 0.001
        L = 1

        x1, y1 = pt.x, pt.y
        # move to first point
        step_func(x1, y1)
#        self._is_tracing = True
#        self._cancel_tracing = False
        for pi in points[1:]:
            x2, y2 = pi.x, pi.y
            # step along line until cp >=pi
            while not self._cancel_tracing:
                x1, y1 = calc_point_along_line(x1, y1, x2, y2, L)
                step_func(x1, y1)

                if abs(pi.x - x1) < tol and abs(pi.y - y1) < tol:
                    break

        self._is_tracing = False

    def fire_laser(self, action):
        atl = self.atl_controller
        if atl.is_enabled():
            if action == 'burst':
                atl.set_burst_mode(True)
                atl.laser_run()
            elif action == 'continuous':
                atl.set_burst_mode(False)
                atl.laser_run()
            else:
                atl.laser_stop()

            return True
        else:
            return 'laser not on'

    def set_reprate(self, r):
        self.atl_controller.set_reprate(r, save=False)
        return True

    def set_nburst(self, n):
        self.atl_controller.set_nburst(n, save=False)
        return True

    def get_nburst(self):
        return self.atl_controller.get_nburst()

    def get_burst_mode(self):
        return self.atl_controller.is_burst_mode()

    def update_parameters(self):
        if self.atl_controller is not None:
            self.atl_controller.update_parameters()

    def single_burst(self, delay=4):
        atl = self.atl_controller
        atl.laser_run()
        time.sleep(delay)
        atl.laser_stop()

#===============================================================================
# private
#===============================================================================
    def _enable_hook(self):
        resp = self.laser_controller._enable_laser()
        if self.laser_controller.simulation:
            resp = True

        if resp:
            self.atl_controller.laser_on()

        return resp

    def _disable_hook(self):
        # pause for the monitor to stop
        time.sleep(0.25)

        resp = self.laser_controller._disable_laser()
        if self.laser_controller.simulation:
            resp = True
        if resp:
            self.atl_controller.laser_off()
        self.status_readback = ''
        self.action_readback = ''
        self.firing = False
        return resp

#===============================================================================
# handlers
#===============================================================================

    def _fire_button_fired(self):
        if self.firing:
            self.info('stopping laser')
            self.firing = False
            self.atl_controller.laser_stop()
        else:
            self.info('firing laser')
            if self.mode == 'Single':
                self.atl_controller.laser_single_shot()
#            elif self.mode=='Burst':
#                self.atl_controller.laser_burst()
#                self.firing = True
            else:
                self.atl_controller.laser_run()
                self.firing = True

    def _burst_shot_changed(self):
        if self.burst_shot:
            self.set_nburst(self.burst_shot)

    def _reprate_changed(self):
        if self.reprate:
            self.set_reprate()

    def _mode_changed(self):
        if self.mode == 'Burst':
            self.atl_controller.set_burst_mode(True)
        else:
            self.atl_controller.set_burst_mode(False)
#===============================================================================
# property get/set
#===============================================================================
    def _get_fire_label(self):
        return 'Fire' if not self.firing else 'Stop'
#===============================================================================
# views
#===============================================================================
    def get_control_group(self):
        cg = VGroup(
                      HGroup(
                             Item('enabled_led', show_label=False, style='custom', editor=LEDEditor()),
                             self._button_factory('enable', 'enable_label'),
                             self._button_factory('execute_button', 'execute_label'),
                             Item('names', show_label=False),
                             spring
                             ),
#                      Item('execute_button', show_label=False, editor=ButtonEditor(label_value='execute_label')),
                      HGroup(
                             Item('action_readback', width=100, style='readonly', label='Action'),
                             Item('status_readback', style='readonly', label='Status'),
                             ),
                      HGroup(self._button_factory('fire_button', 'fire_label'),
                             Item('mode', show_label=False),
                             enabled_when='object.enabled and object.status_readback=="Laser On"'
                             ),
                      HGroup(
                             Item('burst_shot', label='N Burst', enabled_when='mode=="Burst"'),
                             Item('reprate', label='Rep. Rate')
                             ),
                      HGroup(
                             Item('burst_readback', label='Burst Rem.', width=50, style='readonly'),
                             Item('energy_readback', label='Energy (mJ)',
                                  style='readonly', format_str='%0.2f'),
                             Item('pressure_readback', label='Pressure (mbar)',
                                  style='readonly', width=100, format_str='%0.1f'),
                             spring,
                             enabled_when='object.enabled'
                             ),
                      show_border=True,
                      label='Power')

        ac = self.get_additional_group()
        return HGroup(cg, ac)


#===============================================================================
# defaults
#===============================================================================

    def _stage_manager_default(self):
        '''
        '''
        args = dict(name='stage',
                            configuration_dir_name='uv',
                             stage_controller_class='Aerotech',
                             stage_map_klass=UVStageMap,
                             use_modified=False
                             )

#        if self.video_manager.__class__.__name__ == 'VideoManager' and self._video_stage:
#        if self.use_video:
#            from src.lasers.stage_managers.video_stage_manager import VideoStageManager
#            factory = VideoStageManager
#            args['video_manager'] = self.video_manager
#        else:
#            from src.lasers.stage_managers.stage_manager import StageManager
#            factory = StageManager

        return self._stage_manager_factory(args)

    def _laser_controller_default(self):
        '''
        '''
        return FusionsUVLogicBoard(name='laser_controller',
                                   configuration_dir_name='uv')

    def _atl_controller_default(self):
        '''
        '''
        return ATLLaserControlUnit(name='atl_controller',
                                   configuration_dir_name='uv',
                                   )

    def _gas_handler_default(self):
        uv = UVGasHandlerManager(controller=self.atl_controller)
#        uv.bootstrap()
        return uv
    def _mode_default(self):
        return 'Burst'

    def _laser_script_executor_default(self):
        return UVLaserScriptExecutor(laser_manager=self)
#    def _shot_history_default(self):
#        '''
#        '''
#        return LaserShotHistory(view_mode='simple')
#============= EOF ====================================
#    def _auto_fired(self):
#        '''
#        '''
#        if self.gas_handling_state == 'none':
#            self.gas_handling_state = 'auto'
#            self.auto_led = True
#        else:
#            self.auto_led = False
#            self.gas_handling_state = 'none'

#    def _mirror_fired(self):
#        '''
#        '''
#        if self.gas_handling_state == 'none':
#            self.gas_handling_state = 'mirror'
#            self.mirror_led = True
#        else:
#            self.mirror_led = False
#            self.gas_handling_state = 'none'
#
#
#    def _get_auto_label(self):
#        '''
#        '''
#        return 'OFF' if self.gas_handling_state == 'auto' else 'ON'
#
#    def _get_mirror_label(self):
#        '''
#        '''
#        return 'OFF' if self.gas_handling_state == 'mirror' else 'ON'
#
#
#    def _get_laseronoff_label(self):
#        '''
#        '''
#        return 'OFF' if self._enabled else 'ON'
#
#    def _get_fire_label(self):
#        '''
#        '''
#        return 'STOP' if self.triggered else 'RUN'
#
#    def _laseronoff_fired(self):
#        '''
#        '''
#        if not self._enabled:
#            self.atl_controller.laser_on()
#            self.laser_status = 'Laser ON'
#        else:
#            self.atl_controller.laser_off()
#            self.laser_status = 'Laser OFF'
#
#    def _fire_fired(self):
#        '''
#        '''
#        if not self.triggered:
#            self.atl_controller.trigger_laser()
#            self.laser_status = 'Laser Triggered'
#            self.shot_history.add_shot()
#        else:
#            self.atl_controller.stop_triggering_laser()
#            self.laser_status = ''

#    def show_control_view(self):
#        '''
#        '''
#        self.edit_traits(view='control_view')
#
#    def get_control_buttons(self):
#        '''
#        '''
#        return []

#    def get_menus(self):
#        '''
#        '''
#        m = super(FusionsUVManager, self).get_menus()
#
#        m.append(('Laser', [dict(name='Control',
#                               action='show_control_view')]))
#        return m

#        '''
#        '''
#        s = super(FusionsUVManager, self).get_control_sliders()
#        s.pop(len(s) - 1)
#    def get_control_items(self):
#        s = [
#             ('zoom', 'zoom', {}), ]
#
#        g = self._update_slider_group_factory(s)
#        return self.laser_controller.control_view()

#============= views ===================================

#    def _get_gas_contents(self):
#        '''
#        '''
#        hg = self._readonly_slider_factory('laser_head', 'laser_head')
#        sg = self._switch_group_factory([('auto', True, 'gas_handling_state in ["none","auto"]'),
#                                       ('mirror', True, 'gas_handling_state in ["none","mirror"]')])
#        return [hg,
#                sg
#                ]
#
#    def _get_control_contents(self):
#        '''
#        '''
#
#        stg = VGroup(#Label('Stab. Mode'),
#                    Item('stablization_mode', style='custom',
#                         show_label=False,
#                         editor=EnumEditor(values=self.stablization_modes,
#                                           cols=1),
#                         ),
#                    HGroup(Item('stop_at_low_e', show_label=False), Label('Stop at Low Energy')),
#                    label='STAB. MODE',
#                    show_border=True
#                    )
#        tbg = self._button_group_factory([('fire', 'fire_label', 'on'),
#                                               ('single_shot', '', 'on')
#                                               ], orientation='v')
#        bg = HGroup(VGroup(
#                         HGroup(Item('burst', show_label=False),
#                                Label('BURST'))
#                         ),
#                  Item('nburst', show_label=False),
#                  Item('cburst', show_label=False, enabled_when='0')
#                  )
#        tg = HGroup(VGroup(Label('TRIGGER MODE'),
#                         Item('trigger_mode', style='custom',
#                            show_label=False,
#                               editor=EnumEditor(values=self.trigger_modes,
#                                                        cols=1)),
#                         bg
#                         ),
#                    tbg
#                 )
#        tg.label = 'TRIGGER'
#        tg.show_border = True
#
#        lg = Group(self._button_factory('laseronoff', 'laseronoff_label', None))
#        lg.label = 'LASER'
#        lg.show_border = True
#        cg = HGroup(
#                    stg,
#                  lg,
#                  tg,
#                  )
#
#        sliders = [('energy', 'energy', None),
#                 ('hv', 'hv', None),
#                 ('reprate', 'reprate', None),
#                 ]
#
#        sg = self._update_slider_group_factory(sliders)
#        sg.content.append(self._readonly_slider_factory('laser_head', 'laser_head'))
#        sg.show_border = True
#
#        vg = VGroup(Item('cathode', enabled_when='0'),
#                  Item('reservoir', enabled_when='0'),
#                  Item('missing_pulses', enabled_when='0'),
#                  Item('halogen_filter', enabled_when='0'))
#
#        pg = HGroup(sg, vg)
#
#        hg = HGroup(Item('shot_history', show_label=False, style='custom')
#                  )
#        return [
#                cg,
#                pg,
#                hg,
#                HGroup(Item('laser_status', style='readonly'))
#                ]


#    def control_view(self):
#        '''
#        '''
#        control_contents = self._get_control_contents()
#        v = View(
#               resizable=True,
#               title='UV Laser Control'
#               )
#        for c in control_contents:
#
#            v.content.append(c)
#        return v
#
#    def gas_view(self):
#        '''
#        '''
#        contents = self._get_gas_contents()
#
#        v = View(
#               )
#        for c in contents:
#            v.content.append(c)
#        return v

#    def __test__group__(self):
#        '''
#        '''
#        vg = VGroup()
#        for c in self._get_gas_contents():
#            vg.content.append(c)
#        return vg

#    def get_lens_configuration_group(self):
#        return None
#
#    def load_lens_configurations(self):
#        pass
