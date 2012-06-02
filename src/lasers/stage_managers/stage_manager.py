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
from traits.api import DelegatesTo, Int, Property, Instance, \
    Button, List, String, Event, Bool, on_trait_change
from traitsui.api import View, Item, Group, HGroup, VGroup, HSplit, spring, \
     EnumEditor, InstanceEditor
from apptools.preferences.preference_binding import bind_preference
#=============standard library imports =======================
import os
from threading import Thread
import time
#=============local library imports  ==========================
from src.managers.manager import Manager
from src.canvas.canvas2D.laser_tray_canvas import LaserTrayCanvas
from src.managers.displays.rich_text_display import RichTextDisplay
from src.helpers.color_generators import colors8i as colors

from src.hardware.motion_controller import MotionController
from src.helpers.paths import map_dir, setup_dir, user_points_dir, hidden_dir
import pickle

from src.managers.motion_controller_managers.motion_controller_manager \
    import MotionControllerManager
from tray_calibration_manager import TrayCalibrationManager
from stage_component_editor import LaserComponentEditor
from src.canvas.canvas2D.markup.markup_items import CalibrationItem
from pattern.pattern_manager import PatternManager
from stage_map import StageMap
from affine import AffineTransform


class StageManager(Manager):
    '''
    '''
    stage_controller_class = String('Newport')
    stage_controller = Instance(MotionController)

    motion_controller_manager = Instance(MotionControllerManager)

    simulation = DelegatesTo('stage_controller')

    stage_map = Property(depends_on='_stage_map')
    stage_maps = Property(depends_on='_stage_maps')

    _stage_map = Instance(StageMap)
    _stage_maps = None

    canvas = Instance(LaserTrayCanvas)
    output = Instance(RichTextDisplay)

    #===========================================================================
    # buttons
    #===========================================================================
    home = Button('home')
    home_option = String('Home All')
    home_options = None

    ejoystick = Event
    joystick_label = String('Enable Joystick')
    joystick = Bool(False)
    joystick_timer = None

    buttons = List([('home', None, None),
#                    ('jog', 'jog_label', None),
                    ('stop_button', 'stop_label', None)
                      ])

    program_points = Event
    program_points_label = Property(depends_on='canvas.markup')
    load_points = Button
    save_points = Button
    clear_points = Button
    accept_point = Button

    pattern_manager = Instance(PatternManager)
    stop_button = Button()
    stop_label = String('Stop')

    hole_thread = None
    hole = Property(Int(enter_set=True, auto_set=False), depends_on='_hole')
    _hole = Int

    point_thread = None
    point = Property(Int(enter_set=True, auto_set=False), depends_on='_point')
    _point = Int

    canvas_editor_klass = LaserComponentEditor

    tray_calibration_manager = Instance(TrayCalibrationManager, ())

    motion_profiler = DelegatesTo('stage_controller')

    _temp_position = None

    def _test_fired(self):
#        self.do_pattern('testpattern')
        self.do_pattern('pattern003')

    def _clear_points_fired(self):
        self.canvas.clear_points()
        self._point = 0

    def _get_program_points_label(self):
        return 'Program Points' if not self.canvas.markup else 'End Program'

    def _program_points_fired(self):
        if not self.canvas.markup:
            self.canvas.tool_state = 'point'
        else:
            self.canvas.tool_state = 'select'
            if self.canvas.selected_element:
                self.canvas.selected_element.set_state(False)
                self.canvas.request_redraw()
        self.canvas.markup = not self.canvas.markup

    def _accept_point_fired(self):
        npt = self.canvas.new_point()
        if npt:
            self.info('added point {}:{:0.5f},{:0.5f}'.format(npt.identifier, npt.x, npt.y))

    def _load_points_fired(self):
        p = self.open_file_dialog(default_directory=os.path.join(setup_dir,
                                                                 'tray_maps',
                                                                 'user_points')
                                  )
        if p:
            self.canvas.load_points_file(p)

    def _save_points_fired(self):
        p = self.save_file_dialog(default_directory=user_points_dir)

        if p:
            self.canvas.save_points(p)

    def __init__(self, *args, **kw):
        '''

        '''
        super(StageManager, self).__init__(*args, **kw)
        self.add_output('Welcome')
        self.stage_controller = self._stage_controller_factory()

    def kill(self):
        r = super(StageManager, self).kill()

        p = os.path.join(hidden_dir, 'stage_map')
        self.info('saving stage_map {} to {}'.format(self.stage_map, p))
        with open(p, 'wb') as f:
            pickle.dump(self.stage_map, f)
        return r

    def bind_preferences(self, pref_id):
        bind_preference(self.canvas, 'show_grids', '{}.show_grids'.format(pref_id))

        self.canvas.change_grid_visibility()

        bind_preference(self.canvas, 'show_laser_position', '{}.show_laser_position'.format(pref_id))
        bind_preference(self.canvas, 'show_desired_position', '{}.show_laser_position'.format(pref_id))
        bind_preference(self.canvas, 'render_map', '{}.render_map'.format(pref_id))

        bind_preference(self.canvas, 'crosshairs_kind', '{}.crosshairs_kind'.format(pref_id))
        bind_preference(self.canvas, 'crosshairs_color', '{}.crosshairs_color'.format(pref_id))
        bind_preference(self.canvas, 'crosshairs_offset', '{}.crosshairs_offset'.format(pref_id))

        bind_preference(self.canvas, 'scaling', '{}.scaling'.format(pref_id))

        bind_preference(self.tray_calibration_manager, 'calibration_style', '{}.calibration_style'.format(pref_id))

        self.canvas.change_indicator_visibility()

    def _load_previous_stage_map(self):
        p = os.path.join(hidden_dir, 'stage_map')

        if os.path.isfile(p):
            self.info('loading previous stage map')
            with open(p, 'rb') as f:
                try:
                    return pickle.load(f)
                except pickle.PickleError:
                    pass

    def load(self):
        self._stage_maps = []
        config = self.get_configuration()
        #load the stage maps
        mapfiles = self.config_get(config, 'General', 'mapfiles')
        for mapfile in mapfiles.split(','):
            path = os.path.join(map_dir, mapfile.strip())
            sm = StageMap(file_path=path,

                        )
            sm.load_correction_file()
            self._stage_maps.append(sm)

        #load the saved stage map
        sp = self._get_stage_map_by_name(self._load_previous_stage_map())
        if sp is not None:
            sm = sp

        self._stage_map = sm

        #load the calibration file
        #should have calibration files for each stage map
        self.tray_calibration_manager.load_calibration()

        #load the points file
        #self.canvas.load_points_file(self.points_file)

        #load defaults
        self._default_z = self.config_get(config, 'Defaults', 'z', default=13, cast='float')

    def initialize_stage(self):
        self.canvas.parent = self
        self.update_axes()
        axes = self.stage_controller.axes
        self.home_options = ['Home All', 'XY'] + sorted([axes[a].name.upper() for a in axes])

    def finish_loading(self):
        self.update_axes()

    def set_stage_map(self, v):
        return self._set_stage_map(v)

    def add_output(self, msg, color=None):
        '''

        '''
        if not color:
            color = colors['black']

        self.output.add_text(msg=msg, color=color)

    def single_axis_move(self, *args, **kw):
        return self.stage_controller.single_axis_move(*args, **kw)

    def linear_move(self, x, y, update_hole=True, calibrated_space=True, **kw):

        #x = self.stage_controller._sign_correct(x, 'x')
        #y = self.stage_controller._sign_correct(y, 'y')
        if update_hole:
            hole = self._get_hole_by_position(x, y)
            if hole is not None:
                self._hole = int(hole.id)

        pos = (x, y)
        if calibrated_space:
            pos = self._map_calibrated_space(pos)

        self.stage_controller.linear_move(*pos, **kw)

    def set_xy(self, x, y):
        hole = self._get_hole_by_position(x, y)
        if hole:
            self.hole = int(hole.id)
        else:
            self.linear_move(x, y)

    def _get_hole_by_position(self, x, y, tol=0.1):
        if self._stage_map:
            return self._stage_map._get_hole_by_position(x, y)

#
#    def do_pattern(self, patternname):
#        return self.pattern_manager.execute_pattern(patternname)

    def update_axes(self, update_hole=True):
        '''
        '''
        self.info('querying axis positions')
        self.stage_controller.update_axes()
        if update_hole:
            #check to see if we are at a hole         
            hole = self._get_hole_by_position(self.stage_controller._x_position,
                                              self.stage_controller._y_position,
                                              )
            if hole is not None:
                self._hole = int(hole.id)

    def move_to_load_position(self):
        '''
        '''
        x, y, z = self.stage_controller.get_load_position()
        self.info('moving to load position, x={}, y={}, z={}'.format(x, y, z))

        self.stage_controller.linear_move(x, y, grouped_move=False, block=False)

        self.stage_controller._set_z(z)
        self.stage_controller._block_()

#    def single_axis_move(self, *args, **kw):
#        self.stage_controller.single_axis_move(*args, **kw)

#    def linear_move_to(self, x, y, **kw):
#        '''
#    
#        '''
#        sc = self.stage_controller
#
#        #calc the displacement
#        dx = sc._x_position - x
#        dy = sc._y_position - y
#
#        d = math.sqrt(math.pow(dx, 2) + math.pow(dy, 2))
#
#        #d = ((self._x_position - x) ** 2 + (self._y_position - y) ** 2) ** 0.5
#
#        tol = 0.001 #should be set to the motion controllers resolution 
#        if d > tol:
#            kw['displacement'] = d
#
#            self.canvas.set_stage_position(x, y)
#
#            sc._x_position = x
#            sc._y_position = y
#
#            sc.timer = sc.timer_factory()
#            sc.linear_move(dict(x = x, y = y), **kw)
#        else:
#            self.info('displacement of move too small {} < {}'.format(d, tol))

    @on_trait_change('stop_button')
    def stop(self, ax_key=None):

        self.stage_controller.stop(ax_key=ax_key)


    def moving(self, **kw):
        return self.stage_controller._moving_(**kw)

    def define_home(self, **kw):
        self.stage_controller.define_home(**kw)

    def _home_(self):
        '''
        '''
#        define_home = True
        if self.home_option == 'Home All':

            msg = 'homing all motors'
            homed = ['x', 'y', 'z']
            home_kwargs = dict(x= -25, y= -25, z=50)

        elif self.home_option == 'XY':
            msg = 'homing x,y'
            homed = ['x', 'y']
            home_kwargs = dict(x= -25, y= -25)
        else:
#            define_home = 
            msg = 'homing {}'.format(self.home_option)
            home_kwargs = {self.home_option:-25 if self.home_option in ['X', 'Y'] else 50}
            homed = [self.home_option.lower().strip()]

        self.info(msg)

        #if define_home:
        self.stage_controller.set_home_position(**home_kwargs)

        self.stage_controller.home(homed)
        if 'z' in homed and 'z' in self.stage_controller.axes:
            #will be a positive limit error in z
#            self.stage_controller.read_error()

            time.sleep(0.25)
            self.info('setting z to nominal position. {} mm '.format(self._default_z))
            self.stage_controller.single_axis_move('z', self._default_z, block=True)
            self.stage_controller._z_position = self._default_z

#            self.stage_controller._set_z(self._default_z)
##            time.sleep(0.1)
#            self.stage_controller._block_(axis='z')

        if self.home_option in ['XY', 'Home All']:
            time.sleep(0.25)

            #the stage controller should  think x and y are at -25,-25
            self.stage_controller._x_position = -25
            self.stage_controller._y_position = -25

            self.info('moving to center')
            self.stage_controller.linear_move(0, 0, block=True, sign_correct=False)

#======================= Button handlers =======================
    def _ejoystick_fired(self):
        '''
        '''
        self.joystick = not self.joystick
        if self.joystick:
            self.stage_controller.enable_joystick()
            self.joystick_label = 'Disable Joystick'

            self.joystick_timer = self.timer_factory(func=self._joystick_inprogress_update)
        else:
            if self.joystick_timer is not None:
                self.joystick_timer.Stop()

            self.stage_controller.disable_joystick()
            self.joystick_label = 'Enable Joystick'

    def _home_fired(self):
        '''
        '''
        t = Thread(name='stage.home',
                   target=self._home_)
        t.start()

#===============================views=====================

    def edit_traits(self, *args, **kw):
#        self.canvas.reset()
#        self.canvas.parent = self
        self.initialize_stage()
#        self.load_calibration()
#        self.update_axes()
        return super(StageManager, self).edit_traits(*args, **kw)


    def traits_view(self):
        '''
        '''
        self.initialize_stage()

        editor = self._canvas_editor_factory()

        canvas_group = VGroup(
                            # Item('test'),
                             HGroup(Item('stage_map', show_label=False,
                                         editor=EnumEditor(name='object.stage_maps')),
                                    Item('_stage_map',
                                          show_label=False),

                                     spring),
                             Item('canvas', style='custom', editor=editor ,
                                   show_label=False,
                                   resizable=False
                                   ),
                             )

        vg = VGroup()
        hooks = [h for h in dir(self) if '__group__' in h]
        for h in hooks:
            vg.content.append(getattr(self, h)())

        return View(HSplit(vg, canvas_group),
                    resizable=True,
                    #title = self.title,
                    #width=self.window_width,
                    #height=self.window_height
#                    handler=self.handler_klass
                    )
#===============================groups=====================
    def _hole__group__(self):
        g = Group(HGroup(Item('hole'), Item('point'), spring))
        return g

    def _button__group__(self):
        '''
        '''
        vg = VGroup()

        home = self._button_factory(*self.buttons[0])
        calibrate_stage = self._button_factory(*self.buttons[1])

        vg.content.append(HGroup(calibrate_stage, home,
                                 Item('home_option',
                                      editor=EnumEditor(values=self.home_options),
                                      show_label=False)))

        if len(self.buttons) > 2:
        #vg.content.append(self._button_group_factory(self.buttons[:2], orientation = 'h'))
            vg.content.append(self._button_group_factory(self.buttons[2:], orientation='h'))
        return vg

    def _axis__group__(self):
        '''
        '''
        return Item('stage_controller', show_label=False, style='custom')


    def _sconfig__group__(self):
        '''
        '''
        return Group(
                     Item('pattern_manager',
                          label='Pattern',
                          editor=InstanceEditor(view='execute_view'),
                           show_label=False, style='custom'
                          ),

                     Group(

                           Item('canvas', show_label=False,
                                editor=InstanceEditor(view='config_view'),
                                 style='custom'),
                           label='Canvas'),

                     Group(Item('motion_controller_manager', editor=InstanceEditor(view='configure_view'),
                                 style='custom', show_label=False),
                           Item('motion_profiler', style='custom', show_label=False),
                           label='Motion'
                           ),

                     Group(
                           self._button_factory('program_points', 'program_points_label'),
                            Item('accept_point', show_label=False),
                            Item('load_points', show_label=False),
                            Item('save_points', show_label=False),
                            Item('clear_points', show_label=False),
                           label='Points'),
                     Item('tray_calibration_manager',
                          label='Calibration',
                           show_label=False, style='custom'),
#                     Item('pattern_manager',
#                          label='Pattern',
#                          editor=InstanceEditor(view='execute_view'),
#                           show_label=False, style='custom'
#                          ),

#                     Item('output', show_label = False, style = 'custom'),

#                     Item('jog_manager', show_label = False, style = 'custom',
#                          resizable=False
#                          ),
                     layout='tabbed'
                     )

#===============================defaults=====================
    def _motion_controller_manager_default(self):
        return self.motion_configure_factory()

    def motion_configure_factory(self, **kw):
        return MotionControllerManager(motion_controller=self.stage_controller, **kw)

    def _stage_controller_factory(self):
        '''
        '''
        if self.stage_controller_class == 'Newport':
            from src.hardware.newport.newport_motion_controller import NewportMotionController
            factory = NewportMotionController
        elif self.stage_controller_class == 'Aerotech':
            from src.hardware.aerotech.aerotech_motion_controller import AerotechMotionController
            factory = AerotechMotionController

        m = factory(name='{}controller'.format(self.name),
                    configuration_dir_name=self.configuration_dir_name,
                    parent=self
                    )
        return m

    def _canvas_default(self):
        '''
        '''
        return self._canvas_factory()

    def _canvas_factory(self):
        '''
        '''

        w = 640 / 2.0 / 23.2
        h = 0.75 * w
        l = LaserTrayCanvas(parent=self,
                               padding=[30, 5, 5, 30],
                               map=self._stage_map,
                               view_x_range=[-w, w],
                               view_y_range=[-h, h],
                               )

        return l

    def _canvas_editor_factory(self):

        canvas = self.canvas

        w = 640 * canvas.scaling / 10.0
        h = w * 0.75

        return self.canvas_editor_klass(width=w + canvas.padding_left + canvas.padding_right,
                                          height=h + canvas.padding_top + canvas.padding_bottom

                                          )
    def _output_default(self):
        '''
        '''
        return RichTextDisplay(height=175,
                               width=100
                               )

    def _title_default(self):
        '''
        '''
        return '%s Stage Manager' % self.name[:-5].capitalize()

    def _pattern_manager_default(self):
        return PatternManager(parent=self)
#    def _jog_manager_default(self):
#        return JogManager(parent = self)

    def _tray_calibration_manager_default(self):
        t = TrayCalibrationManager(parent=self,
                                   canvas=self.canvas)
        return t

#======================= Property methods ======================
    def _get_stage_maps(self):
        return [s.name for s in self._stage_maps]

    def _get_stage_map(self):
        if self._stage_map:
            return self._stage_map.name

    def _get_stage_map_by_name(self, name):
        return next((sm for sm in self._stage_maps if sm.name == name), None)

    def _set_stage_map(self, v):
        s = self._get_stage_map_by_name(v)
        if s is not None:
            self.canvas.set_map(s)
            self.tray_calibration_manager.load_calibration(stage_map=s.name)
            self._stage_map = s
            self.info('setting stage map to {}'.format(v))
            return True
        else:
            return False

    def __stage_map_changed(self):
        self.canvas.set_map(self._stage_map)
        self.tray_calibration_manager.load_calibration(stage_map=self._stage_map)
        self.canvas.request_redraw()

    def _get_calibrate_stage_label(self):
        if self._calibration_state == 'set_center':
            r = 'Locate Center'
        elif self._calibration_state == 'set_right':
            r = 'Locate Right'
        else:
            r = 'Calibrate Stage'
        return r

#    def _get_home_options(self):
#        '''
#        '''
#
#        axes = self.stage_controller.axes
#        return ['Home All'] + [axes[a].name.upper() for a in axes]
    def get_z(self):
        return self.stage_controller._z_position

    def get_uncalibrated_xy(self):

        pos = (self.stage_controller._x_position, self.stage_controller._y_position)
        if self.stage_controller.axes['x'].id == 2:
            pos = pos[1], pos[0]

        a = AffineTransform()
        canvas = self.canvas
        ca = canvas.calibration_item
        if ca:
            rot = ca.get_rotation()
            cpos = ca.get_center_position()
#            a.translate(-cpos[0], -cpos[1])
#            a.translate(*cpos)
#            a.rotate(-rot)
#            a.translate(-cpos[0], -cpos[1])
#
#            pos = a.transformPt(pos)
            pos = self._stage_map.map_to_uncalibration(pos, cpos, rot)

        return pos

    def _map_calibrated_space(self, pos, key=None):
        smap = self._stage_map

        #use a affine transform object to map

##        #load the calibration from file every time
#        self.tray_calibration_manager.load_calibration()

        canvas = self.canvas
        ca = canvas.calibration_item

        if ca:
            rot = ca.get_rotation()
            cpos = ca.get_center_position()
            t = None
            if key in ca.tweak_dict and isinstance(ca, CalibrationItem):
                t = ca.tweak_dict[key]
#                a.translate(*ca.tweak_dict[key])
            pos = smap.map_to_calibration(pos, cpos, rot, translate=t)

        return pos

    def _set_hole(self, v):
        if self.canvas.calibrate:
            self.warning_dialog('Cannot move while calibrating')
            return

        if self.canvas.markup:
            self.warning_dialog('Cannot move while adding/editing points')
            return

        if self.hole_thread is None and v is not self._hole:
            pos = self._stage_map.get_hole_pos(str(v))
            if pos is not None:
                self._hole = v
                self.hole_thread = Thread(name='stage.move_to_hole',
                                          target=self._move_to_hole, args=(str(v),))
                self.hole_thread.start()
            else:
                err = 'Invalid hole {}'.format(v)
                self.warning(err)
                return  err

    def _get_hole(self):
        return self._hole

    def _set_point(self, v):
        if self.canvas.calibrate:
            self.warning_dialog('Cannot move while calibrating')
            return

        if self.canvas.markup:
            self.warning_dialog('Cannot move while adding/editing points')
            return

        if self.point_thread is None and v is not self._point:
            pos = self.canvas.get_item('point', int(v) - 1)
            if pos is not None:
                self._point = v
                self.point_thread = Thread(target=self._move_to_point, args=(pos,))
                self.point_thread.start()
            else:
                err = 'Invalid point {}'.format(v)
                self.warning(err)
                return  err

    def _get_point(self):
        return self._point

    def _move_to_point(self, pt):
        pos = pt.x, pt.y
        self.info('Move to point {}'.format(pt.identifier))
        self.stage_controller.linear_move(block=True, *pos)

        self._move_to_point_hook()

        self.info('Move complete')
        self.point_thread = None

    def _move_to_hole(self, key):
        self.info('Move to hole {}'.format(key))
#        holes = self._stage_map.holes
        pos = self._stage_map.get_corrected_hole_pos(key)
        if pos is not None:
            correct = True
            if abs(pos[0]) < 1e-6:
                pos = self._stage_map.get_hole_pos(key)
                pos = self._map_calibrated_space(pos, key=key)
            else:
                self.info('using previously calculated corrected position')
                correct = False
            #map the position to calibrated space
            self.stage_controller.linear_move(block=True, *pos)
            if self.tray_calibration_manager.calibration_style == 'MassSpec':
                if not self.tray_calibration_manager.isCalibrating():
                    self._move_to_hole_hook(key, correct)
            else:
                self._move_to_hole_hook(key, correct)

            self.info('Move complete')
            self.update_axes(update_hole=False)
            self.hole_thread = None

    def _move_to_hole_hook(self, *args):
        pass

    def _move_to_point_hook(self):
        pass

    def get_video_database(self):
#        from src.helpers.paths import co2laser_db

        from src.database.adapters.video_adapter import VideoAdapter

#        db = PowerAdapter(dbname='co2laserdb',
#                                   password='Argon')
        db = VideoAdapter(dbname=self.parent.dbname,
                          kind='sqlite')

        return db
#class DummyParent(HasTraits):
#    zoom = Float
#    zoommin = Float
#    zoommax = Float(10)
#    update_zoom = Float
#
#    beam = Float
#    beammin = Float
#    beammax = Float(10)
#    update_beam = Float
#    enable = Button
#    request_power = Float
#    request_powermin = Float
#    request_powermax = Float(100)

#    enabled_led = Instance(LED, ())
#    simulation_led = Instance(LED, ())

if __name__ == '__main__':
    from src.helpers.logger_setup import logging_setup

    logging_setup('stage_manager')
    name = 'diode'
    s = StageManager(
                     name='{}stage'.format(name),
                     configuration_dir_name=name,
                     #parent = DummyParent(),
                     window_width=945,
                     window_height=545

                     )
#    from src.initializer import Initializer
#
#    i = Initializer()
#    i.add_initialization(dict(name = 'stage_manager',
#                              manager = s
#                              ))
#    i.run()
#    s.update_axes()
    s.load()
    s.stage_controller.bootstrap()
    s.configure_traits()
#========================EOF============================
#    def arc_move_to(self,cp=None, rot=None):
#        if cp is None:
#            cp=self.center_point
#        if rot is None:
#            rot=self.stage_rotation
#
#        self.stage_controller.arc_move(cp,rot)
#        
#        
#        self._xaxis=cp[0]+(self.stage_length)*math.cos(rot)
#        self._yaxis=cp[1]+ (self.stage_length)*math.sin(rot)
#        
#        print self._xaxis,self._yaxis,(self.stage_length)*math.cos(rot)
#        self.timer=self.timer_factory()
#    def apply_stage_rotation(self, x, y):
#        '''
#        
#        @param x:
#        @param y:
#        '''
#        if self.stage_rotation is None:
#            return x, y
#        #translate pt
#        p = matrix([[x], [y]])
#        t1 = matrix([[-self.center_point[0]], [-self.center_point[1]]])
#        t2 = matrix([[self.center_point[0]], [self.center_point[1]]])
#
#        a = -self.stage_rotation
#        #rotation 
#        r = matrix([[math.cos(a), math.sin(a)],
#                    [-math.sin(a), math.cos(a)]])
#
#        p = r * (p + t1) + t2
#        return p.item(0), p.item(1)
##        #self.add_output('%f,%f\n%s'%(x,y,p))
#    def _calibrate_stage_fired(self):
#        '''
#        '''
#        cal = self.calibration
#        if self._calibration_state == 'start':
#            self.add_output('Calibrate Stage')
#            self.add_output('Locate center')
#            self._calibration_state = 'set_center'
#
#        elif self._calibration_state == 'set_center':
#
#            #at the appropriate center pos
#            cal.center_pt = self.x, self.y
#
#            self.add_output('Locate right')
#            self._calibration_state = 'set_right'
#
#        else:
#
#            cal.end_pt = self.x, self.y
#
#            self.canvas.center_pos = cal.center_pt
#            self.canvas.stage_rotation = theta = cal.calc_stage_rotation()
#            self.canvas.request_redraw()
#            self.add_output('Stage Rotation %0.2f' % theta)
#
#            self.add_output('Calibration finished')
#            self._calibration_state = 'start'
#===============================================================================
# Old jogging code
#===============================================================================
#def do_jog(self, name):
#        #load jog parameters from file into the jogmanager
#
#        do_later(self.jog_manager.edit_traits)
#        self.jog_manager.load_file(name)
#        self._jog_fired()
#
#
#    def _jog_(self):
#        '''
#        '''
#        #self.canvas.reset_plots()
#
#        sc = self.stage_controller
#
##        if sc.set_group(low_speed = True):
#        if sc.configure_group(True):
#            if not self._stop_jog:
#                self._jogging = True
#
#                #assume current position is the center of the contour jogging
#                cx = self.stage_controller._x_position
#                cy = self.stage_controller._y_position
#
#                #single jog 
#                #self._single_jog(0.25,1,6)
#
#                #spirograh 1
##                self._spirograph_jog(6, 0.25, 0.75, 3, cx, cy, 10)
#
#                #spiral jog
##                self._circle_spiral_jog(cx, cy, 10, 0.2)
#
#                #angular spiral jog
#                jk = self.jog_manager.kind
#                args = (cx, cy, self.jog_manager.opattern.R,
#                                                self.jog_manager.opattern.ns,
#                                                self.jog_manager.opattern.p)
#                if jk == 'line_spiral':
#                    args += (self.jog_manager.opattern.step_scalar,)
#
#
#                func = getattr(self, '_%s_jog' % jk)
#                rargs = func(*args)
#
#                if jk == 'line_spiral':
#                    x = cx
#                    y = cy
#                else:
#                    x = rargs[0]
#                    y = rargs[1]
#
#                args = (x, y) + args[2:]
#
#                if jk == 'line_spiral':
#                    args = (x, y) + args[2:-1] + (self.jog_manager.ipattern.step_scalar,)
#                func(*args, ox = cx, oy = cy, direction = 'in')
#
#                #move to start
#                self.stage_controller.linear_move(cx, cy, block = True)
#                self.jog_manager.update_position(cx, cy)
#                self._jogging = False
#
#                self.jog_manager.close_ui()
#
#    def _single_jog(self, m, R, nc, cx, cy, low_speed, zero_displacement = True):
#        '''
#            do nc cirles with radius from m to R
#        '''
#        for r in linspace(m, R, nc):
#            if self._stop_jog:
#                break
#            #move to circumfrence
#            self.stage_controller.linear_move(cx + r, cy, low_speed = low_speed, block = True)
#
#            self.arc_move(cx, cy, 360, low_speed = low_speed)
#
#        if zero_displacement and not self._stop_jog:
#            #move back to center position
#            self.stage_controller.linear_move(cx, cy, low_speed = low_speed, block = True)
#
#    def _spirograph_jog(self, na, m, R, nc, cx, cy, low_speed, counter_rotate = True):
#
#        #start with a single jog at center
#        self._single_jog(m, R, nc, cx, cy, low_speed)
#
#        for theta in linspace(0, 360, na + 1):
#            if self._stop_jog:
#                break
#            theta = math.radians(theta)
#            x = cx + R * math.cos(theta)
#            y = cy + R * math.sin(theta)
#            if counter_rotate:
#                y = -y
#            self._single_jog(m, R, nc, x, y, low_speed, zero_displacement = False)
#
#
#    def _arc_spiral_jog(self, cx, cy, ns, R, ifactor):
#        #spiral out
#        #move to circum
#        self.stage_controller.linear_move(cx + R, cy)
#        ns = 4 * ns + 1
#        for li in range(1, ns):
#
#            self.arc_move(cx, cy, 90)
#
#            px = self._x_position
#            py = self._y_position
#
#            r = R * (1 + li * ifactor)
#            rem = (li - 1) % 4
#            if rem == 0:
#                py = cx + r
#            elif rem == 1:
#                px = cx - r
#            elif rem == 2:
#                py = cy - r
#            elif rem == 3:
#                px = cx + r
#
#            if li < ns:
#                #move to next circum
#                self.stage_controller.linear_move(px, py, block = True)
#
#        #spiral in
#        #move to circum
#        self.stage_controller.linear_move(cx + R * (1 + (li - 1) * p), py)
#        for li in range(ns % 4, ns):
#
#            self.arc_move(cx, cy, 90)
#
#            px = self._x_position
#            py = self._y_position
#
#            r = R * (1 + (ns - li - 2) * ifactor)
#            rem = (li - 1) % 4
#            if rem == 0:
#                py = cx + r
#            elif rem == 1:
#                px = cx - r
#            elif rem == 2:
#                py = cy - r
#            elif rem == 3:
#                px = cx + r
#
#            #move to next circum
#            self.stage_controller.linear_move(px, py, block = True)
#
#
#
#    def _square_spiral_jog(self, cx, cy, ns, R, ifactor, direction = 'out', **kw):
#        jogger = square_jogger(cx, cy, ns, R, ifactor, direction = direction, **kw)
#        first = True
#        while 1:
#            try:
#                if self._stop_jog:
#                    break
#                cx, cy = jogger.next()
#                if direction == 'in' and first:
#                    first = False
#                    continue
#
#                self.stage_controller.linear_move(cx, cy, block = True)
#                #self.jog_manager.update_position(cx, cy)
#
#                if self.simulation:
#                    time.sleep(1)
#            except StopIteration:
#                break
#
#        return cx, cy
#
#    def _line_spiral_jog(self, cx, cy, R, ns, ifactor, ss, direction = 'out', **kw):
#        jogger = line_jogger(cx, cy, R, ns, ifactor, ss, direction = direction)
#        first = True
#
#        while 1:
#            try:
#                x, y = jogger.next()
#                if direction == 'in' and first:
#                    first = False
#                    continue
#
#                if self._stop_jog:
#                    break
#
#                self.stage_controller.linear_move(x, y, block = True)
#
#                if self.simulation:
#
#                    def u():
#                        self.canvas.set_stage_position(x, y)
#                        self.jog_manager.update_position(x, y)
#
#                    do_after(1, u)
#                    time.sleep(0.5)
#
#            except StopIteration:
#                break
