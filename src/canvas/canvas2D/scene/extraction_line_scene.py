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
from traits.api import HasTraits, Instance, Dict
from traitsui.api import View, Item, TableEditor
from src.canvas.canvas2D.scene.scene import Scene
from src.canvas.canvas2D.base_data_canvas import BaseDataCanvas
from src.canvas.canvas2D.scene.primitives import RoundedRectangle, Valve, \
    RoughValve, Label, BorderLine, Rectangle
#============= standard library imports ========================
#============= local library imports  ==========================


class ExtractionLineScene(Scene):
    canvas = Instance(BaseDataCanvas)

    valves = Dict
    def _get_floats(self, elem, name):
        return map(float, elem.find(name).text.split(','))

    def _new_rectangle(self, elem, c, bw=3, origin=None):
        if origin is None:
            ox, oy = 0, 0
        else:
            ox, oy = origin

        key = elem.text.strip()
        x, y = self._get_floats(elem, 'translation')
        w, h = self._get_floats(elem, 'dimension')
        rect = RoundedRectangle(x + ox, y + oy, width=w, height=h,
                                            name=key,
                                            border_width=bw,
                                            default_color=c)
        self.add_item(key, rect, layer=1)

    def _new_connection(self, conn, key, start, end):
        skey = start.text.strip()
        ekey = end.text.strip()
        try:
            orient = conn.get('orientation')
        except Exception, e:
#            print'a', e
            orient = None

        sanchor = self.get_item(skey)
        x, y = sanchor.x, sanchor.y
        try:
            ox, oy = map(float, start.get('offset').split(','))
        except Exception, e:
#            print 'b', e
            ox = 1
            oy = sanchor.height / 2.0

        x += ox
        y += oy

        eanchor = self.get_item(ekey)
        x1, y1 = eanchor.x, eanchor.y
        try:
            ox, oy = map(float, end.get('offset').split(','))
        except Exception, e:
#            print 'c', e
            ox = 1
            oy = eanchor.height / 2.0

        x1 += ox
        y1 += oy
        if orient == 'vertical':
            x1 = x
        elif orient == 'horizontal':
            y1 = y

        klass = BorderLine
        l = klass((x, y), (x1, y1), default_color=(0.29, 0.29, 0.43),
                 width=10)
        self.add_item(key, l, layer=0)

    def load(self, pathname):
        self.reset_layers()

        cp = self._get_canvas_parser(pathname)

        xv, yv = self._get_canvas_view_range()
        self.canvas.view_x_range = xv
        self.canvas.view_y_range = yv

        tree = cp.get_tree()

        if tree is None:
            return

        color_dict = dict()
        # get default colors
        for c in tree.findall('color'):
            t = c.text.strip()
            k = c.get('tag')
            co = map(float, t.split(',')) if ',' in t else t

            if k == 'bgcolor':
                self.bgcolor = co
            else:
                color_dict[k] = co

        # get an origin offset
        ox = 0
        oy = 0
        o = tree.find('origin')
        if o is not None:
            ox, oy = map(float, o.text.split(','))

        origin = ox, oy
        ndict = dict()
        for v in cp.get_elements('valve'):
            key = v.text.strip()
            x, y = self._get_floats(v, 'translation')
            v = Valve(x + ox, y + oy, name=key,
#                                    canvas=self,
                                    border_width=3
                                    )
            # sync the states
            if key in self.valves:
                vv = self.valves[key]
                v.state = vv.state
                v.soft_lock = vv.soft_lock

            self.add_item(key, v, layer=1)
            ndict[key] = v

        for rv in cp.get_elements('rough_valve'):
            key = rv.text.strip()
            x, y = self._get_floats(rv, 'translation')
            v = RoughValve(x + ox, y + oy, name=key)
            self.add_item(key, v, layer=1)
            ndict[key] = v

        self.valves = ndict
        for key in ('stage', 'laser', 'spectrometer', 'turbo', 'getter'):
            for b in cp.get_elements(key):
                if key in color_dict:
                    c = color_dict[key]
                else:
                    c = (0.8, 0.8, 0.8)
                self._new_rectangle(b, c, bw=5, origin=origin)

        for i, l in enumerate(cp.get_elements('label')):
            x, y = map(float, l.find('translation').text.split(','))
            l = Label(x + ox, y + oy,
                      text=l.text.strip())
            self.add_item('{:03}'.format(i), l, layer=1)

        for g in cp.get_elements('gauge'):
            if 'gauge' in color_dict:
                c = color_dict['gauge']
            else:
                c = (0.8, 0.8, 0.8)
            self._new_rectangle(g, c, origin=origin)

        for i, conn in enumerate(cp.get_elements('connection')):
            start = conn.find('start')
            end = conn.find('end')
            self._new_connection(conn, 'con{:03}'.format(i), start, end)

        xv, yv = self._get_canvas_view_range()

        x, y = xv[0], yv[0]
        w = xv[1] - xv[0]
        h = yv[1] - yv[0]

        brect = Rectangle(x, y, width=w, height=h,
                          fill=False, line_width=20, default_color=(0, 0, 0.4))
        self.add_item('brect', brect)

#============= EOF =============================================