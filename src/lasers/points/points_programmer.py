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
from traits.api import HasTraits, Color, Button, Event, Property, \
    Any, List, Bool, Enum, Float, Int, Instance, cached_property, Str, String
from traitsui.api import View, Item, ButtonEditor, Group, HGroup, VGroup
#============= standard library imports ========================
import yaml
import os
from numpy import array, hstack, vstack
import re
#============= local library imports  ==========================
from src.paths import paths
from src.managers.manager import Manager
from src.lasers.points.maker import BaseMaker, LineMaker, PointMaker, \
    PolygonMaker, TransectMaker
from src.canvas.scene_viewer import SceneViewer, LaserMineViewer
from src.regex import TRANSECT_REGEX
maker_dict = dict(polygon=PolygonMaker, point=PointMaker, line=LineMaker, transect=TransectMaker)



class PointsProgrammer(Manager):

    maker = Property(Instance(BaseMaker), depends_on='mode')

#===============================================================================
#
#===============================================================================

    stage_manager = Any
    canvas = Any
    program_points = Event
    show_hide = Event
    is_programming = Bool
    is_visible = Bool

    program_points_label = Property(depends_on='is_programming')
    show_hide_label = Property(depends_on='is_visible')

    load_points = Button
    save_points = Button

    stage_map_klass = Any
    mode = Enum('polygon', 'point', 'line', 'transect')

    point = Any
    line = Any
    polygon = Any

#    point_entry = Property(Int(enter_set=True, auto_set=False))
#    line_entry = Property(Int(enter_set=True, auto_set=False))
#    polygon_entry = Property(Int(enter_set=True, auto_set=False))
#    _polygon_entry = Int
#    scan_size = Int(50)
#    plot_scan = Button('Plot')
#    use_move = Bool(False)

    position_entry = String(enter_set=True, auto_set=False)

    show_scene_viewer = Button('Scene Viewer')

    _path = None

    def load_stage_map(self, sm):
#        if not (hasattr(sm, 'lines') and hasattr(sm, 'points') and hasattr(sm, 'polygons')):
#            return

        canvas = self.canvas
        canvas.clear_all()

        ptargs = dict(radius=0.05,
                      vline_length=0.1, hline_length=0.1)
        if hasattr(sm, 'lines'):
            self._load_lines(sm.lines, ptargs)
        if hasattr(sm, 'points'):
            self._load_points(sm.points, ptargs)
        if hasattr(sm, 'polygons'):
            self._load_polygons(sm.polygons, ptargs)
        if hasattr(sm, 'transects'):
            self._load_transects(sm.transects, ptargs)

        self.is_visible = True

        canvas.show_all()
        canvas.invalidate_and_redraw()

    def _set_entry(self, v):
        canvas = self.canvas
        v = v.lower()
        if v.startswith('l'):
            self.line = canvas.get_line(v)
        elif v.startswith('t'):
            if TRANSECT_REGEX.match(v):
                t, p = v[1:].split('-')
                tran = canvas.get_transect(t)
                if tran:
                    point = tran.get_point(int(p))
                    if point:
                        self.point = point
        elif v.startswith('r'):
            self.polygon = canvas.get_polygon(v[1:])
        elif v.startswith('p'):
            self.point = canvas.get_point(v[1:])
        else:
            try:
                int(v)
                self.point = canvas.get_point(v)
            except ValueError:
                pass

#===============================================================================
# handlers
#===============================================================================
    def _position_entry_changed(self):
        self._set_entry(self.position_entry)

    def _show_scene_viewer_fired(self):
#        from src.canvas.canvas2D.video_laser_tray_canvas import VideoLaserTrayCanvas

        xlim = self.canvas.get_mapper_limits('index')
        ylim = self.canvas.get_mapper_limits('value')

        canvas = self.canvas.__class__(use_pan=False, show_grids=True)
        if hasattr(self.canvas, 'video'):
            img = self.canvas.video.get_image_data()
            canvas.video_underlay._cached_image = img

        canvas.set_mapper_limits('index', xlim)
        canvas.set_mapper_limits('value', ylim)
        canvas.scene = self.canvas.scene.clone_traits()
        canvas.scene.set_canvas(canvas)

        sv = LaserMineViewer(canvas=canvas)

        sv.canvas.freeze()
        info = sv.edit_traits(kind='livemodal')
        if info.result:
            save = True
            if self._path is None:
                save = self.confirmation_dialog('Would you like to save these points?', title='Save Changes')

            if save:
                self.maker.canvas = canvas
                self._dump(self._path)
                self.canvas.scene = canvas.scene
        self.maker.canvas = self.canvas
        del sv

    def _show_hide_fired(self):
        canvas = self.canvas
        if self.is_visible:
            canvas.hide_all()
        else:
            canvas.show_all()

        canvas.request_redraw()
        self.is_visible = not self.is_visible

    def _program_points_fired(self):
        if self.is_programming:
            self.canvas.hide_all()
            self.is_programming = False
            self.is_visible = False
        else:
            self.canvas.show_all()
            self.is_programming = True
            self.is_visible = True

        self.canvas.request_redraw()

    def _load_points_fired(self):
        self._load()

    def _save_points_fired(self):
        self._dump()
#===============================================================================
# persistence
#===============================================================================
    def _load(self, p=None):
        if p is None:
            p = self.open_file_dialog(default_directory=paths.user_points_dir)
        if p:
            sm = self.stage_map_klass(file_path=p)
            self.load_stage_map(sm)

            self.is_programming = True
            self._path = p

    def _dump(self, p=None):
        if p is None:
            p = self.save_file_dialog(default_directory=paths.user_points_dir)

        if p:
            if not p.endswith('.yaml'):
                p = '{}.yaml'.format(p)
            d = self.maker.save()
            with open(p, 'w') as f:
                f.write(yaml.dump(d, default_flow_style=False))

            self.stage_manager.add_stage_map(p)
            head, _tail = os.path.splitext(os.path.basename(p))
            self.stage_manager.set_stage_map(head)

#===============================================================================
# property get/set
#===============================================================================
    @cached_property
    def _get_maker(self):
        if self.mode in maker_dict:
            maker = maker_dict[self.mode](canvas=self.canvas,
                                          stage_manager=self.stage_manager,
                                          )
            return maker

#    def _set_polygon_entry(self, v):
#        if self.use_move:
#            self._set_entry('polygon', v, ['point', 'line'])
#        else:
#            self._polygon_entry = v
#
#    def _set_line_entry(self, v):
#        self._set_entry('line', v, ['point', 'polygon'])
#
#    def _set_point_entry(self, v):
#        self._set_entry('point', v, ['line', 'polygon'])
#
#    def _get_line_entry(self):
#        return self._get_entry_identifer('line')
#
#    def _get_point_entry(self):
#        return self._get_entry_identifer('point')
#
#    def _get_polygon_entry(self):
#        return self._get_entry_identifer('polygon')
#
#    def _set_entry(self, name, value, onames):
#        for oi in onames:
#            setattr(self, oi, None)
#
#        objs = getattr(self.canvas, '{}s'.format(name))
#        pp = next((pi for pi in objs if pi.identifier == str(value)), None)
#
#        # trigger stage_manager move_... event handler
#        setattr(self, name, pp)

#    def _get_entry_identifer(self, name):
#        p = self._polygon_entry
#        obj = getattr(self, name)
#        if obj:
#            p = obj.identifier
#
#        return p
    def _load_lines(self, lines, ptargs):
        canvas = self.canvas
        point_color = self.maker.point_color

        for li in lines:
            canvas._new_line = True
            for si in li:
                mi = si['mask'] if si.has_key('mask') else 0
                ai = si['attenuator'] if si.has_key('attenuator') else 0
                canvas.new_line_point(xy=si['xy'],
                                      z=si['z'],
                                      mask=mi, attenuator=ai,
                                      point_color=point_color,
                                       line_color=point_color,
                                       velocity=si['velocity'],
                                           **ptargs)

    def _load_points(self, points, ptargs):
        canvas = self.canvas
        point_color = self.maker.point_color
        for pi in points:
            mi = pi['mask'] if pi.has_key('mask') else 0
            ai = pi['attenuator'] if pi.has_key('attenuator') else 0
            canvas.new_point(xy=pi['xy'],
                             z=pi['z'],
                             mask=mi, attenuator=ai,
                             default_color=point_color,
                                    **ptargs)

    def _load_polygons(self, polygons, ptargs):
        point_color = self.maker.point_color
        canvas = self.canvas
        for k, po in polygons.iteritems():
            canvas._new_polygon = True
            v = po['velocity']
            use_convex_hull = po['use_convex_hull']
            scan_size = po['scan_size']
            mi = po['mask'] if po.has_key('mask') else 0
            ai = po['attenuator'] if po.has_key('attenuator') else 0
            for pi in po['points']:
                canvas.new_polygon_point(xy=pi['xy'],
                                         z=pi['z'],
                                         velocity=v,
                                         identifier=str(int(k) + 1),
                                         point_color=point_color,
                                         mask=mi, attenuator=ai,
                                         scan_size=scan_size,
                                         use_convex_hull=use_convex_hull,
                                         **ptargs)

    def _load_transects(self, trans, ptargs):
        canvas = self.canvas
        point_color = self.maker.point_color
        for ti in trans:
            canvas._new_transect = True
            points = ti['points']
            step = ti['step']
            for pi in points:
                canvas.new_transect_point(xy=pi['xy'],
                                              z=pi['z'],
                                              step=step,
                                              point_color=point_color,
                                              mask=pi['mask'], attenuator=pi['attenuator'],
                                              **ptargs
                                              )
    def _get_program_points_label(self):
        return 'End Program' if self.is_programming else 'Program Positions'

    def _get_show_hide_label(self):
        return 'Hide' if self.is_visible else 'Show'

    def _mode_default(self):
        return 'transect'

    def _clear_mode_default(self):
        return 'all'

    def traits_view(self):
        v = View(VGroup(
                       Item('show_scene_viewer', show_label=False),
                       Item('position_entry', label='Position'),
#                       Item('point_entry', label='Point'),
#                       Item('line_entry', label='Line'),
#                       Item('polygon_entry', label='Polygon'),

#                       HGroup(Item('polygon_entry', label='Polygon'),
#                              Item('use_move',
#                                   tooltip='If checked the polygon rasterization will execute.'),
#                              Item('plot_scan',
#                                   show_label=False,
#                                   tooltip='Display a plot of the calculated scan lines'
#                                   ),
#                              ),

                       Item('mode')
                       ),
                HGroup(Item('show_hide', show_label=False,
                         editor=ButtonEditor(label_value='show_hide_label')
                         ),
                    Item('program_points', show_label=False,
                         editor=ButtonEditor(label_value='program_points_label')
                         )
                       ),
                Item('maker', style='custom',
                     enabled_when='is_programming',
                     show_label=False),
                HGroup(Item('load_points', show_label=False),
                       Item('save_points', show_label=False)),
#                                 HGroup(Item('clear'), Item('clear_mode'), show_labels=False),
#                                 Item('finish', show_label=False, enabled_when='mode=="line" and object.is_programming'),
#                                 enabled_when='object.is_programming'
#                                 ),
        #                     label='Points'
#                             )
#                      )
               )
        return v

#============= EOF =============================================
#    def _plot_scan_fired(self):
#        polygons = self.canvas.polygons
#        if self.polygon_entry is not None and self.scan_size:
#            pp = next((pi for pi in polygons if pi.identifier == str(self.polygon_entry)), None)
#            scan_size = None
#            if hasattr(self.maker, 'scan_size'):
#                scan_size = self.maker.scan_size
#            else:
#                scan_size = pp.scan_size
#
#            poly = [(pi.x * 1000, pi.y * 1000) for pi in pp.points]
#
#            from src.geometry.polygon_offset import polygon_offset
#            from src.geometry.scan_line import make_raster_polygon
#            use_offset = True
#            if use_offset:
#                opoly = polygon_offset(poly, -10)
#                opoly = array(opoly, dtype=int)
#                opoly = opoly[:, (0, 1)]
#
# #            print opoly, scan_size
#            lines = make_raster_polygon(opoly, step=scan_size)
#            from src.graph.graph import Graph
#
#            g = Graph()
#            g.new_plot()
#
#            for po in (poly, opoly):
#                po = array(po, dtype=int)
#                try:
#                    xs, ys = po.T
#                except ValueError:
#                    xs, ys, _ = po.T
#                xs = hstack((xs, xs[0]))
#                ys = hstack((ys, ys[0]))
#                g.new_series(xs, ys)
#
#            for p1, p2 in lines:
#                xi, yi = (p1[0], p2[0]), (p1[1], p2[1])
#                g.new_series(xi, yi, color='green')
#
#            g.edit_traits()

# def _plot_raster(self, poly, scan_size, scale):
#        use_convex_hull = False
#        from src.geometry.scan_line import raster
#        from src.geometry.convex_hull import convex_hull
#        from src.geometry.polygon_offset import polygon_offset
#        from src.geometry.geometry import sort_clockwise
#
#        poly = sort_clockwise(poly, poly)
#        poly = array(poly)
#        poly *= scale
#
#        npoints, lens = raster(poly,
#                         step=200,
#                         offset= -500,
#                         use_convex_hull=use_convex_hull, find_min=True)
#
#        from src.graph.graph import Graph
#        g = Graph(window_height=700,
#                  window_title='Scan Line Minimization',
#                  window_y=30)
#
#        g.plotcontainer.padding = 5
#        g.new_plot(padding=[60, 30, 30, 50],
#                   bounds=[400, 400],
#                   resizable='h',
#                   xtitle='X (microns)',
#                   ytitle='Y (microns)')
#
#        if use_convex_hull:
#            poly = convex_hull(poly)
#            xs, ys = poly.T
#            xs = hstack((xs, xs[0]))
#            ys = hstack((ys, ys[0]))
#        else:
#            xs, ys = poly.T
#            xs = hstack((xs, xs[0]))
#            ys = hstack((ys, ys[0]))
#
#        # plot original
#        g.new_series(xs, ys)
#        g.set_x_limits(min(xs), max(xs), pad='0.1')
#        g.set_y_limits(min(ys), max(ys), pad='0.1')
#        for ps in npoints:
#            for i in range(0, len(ps), 2):
#                p1, p2 = ps[i], ps[i + 1]
#                g.new_series((p1[0], p2[0]),
#                             (p1[1], p2[1]), color='black')
#
#        # plot offset polygon
#        opoly = polygon_offset(poly, -500)
#        if use_convex_hull:
#            opoly = convex_hull(opoly)
#            opoly = vstack(opoly, opoly[:1])
#            xs, ys, _ = opoly.T
#
# #            xs = hstack((xs, xs[0]))
# #            ys = hstack((ys, ys[0]))
#        else:
#            opoly = array(opoly, dtype=int)
#            xs, ys, _ = opoly.T
#
#        g.new_series(xs, ys)
#
#        # plot theta vs num lines ie the scan line minimization
#        g.new_plot(padding=[50, 30, 30, 30],
#               xtitle='Theta (degrees)',
#               ytitle='Num. Scan Lines',
#               bounds=[400, 100],
#               resizable='h'
#               )
#
#        ts, ls = zip(*lens)
#        g.new_series(ts, ls)
#
#        g.edit_traits()
