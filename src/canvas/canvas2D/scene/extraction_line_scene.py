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
from traits.api import Instance, Dict
#============= standard library imports ========================
#============= local library imports  ==========================
from src.canvas.canvas2D.scene.scene import Scene
from src.canvas.canvas2D.base_data_canvas import BaseDataCanvas
from src.canvas.canvas2D.scene.primitives.primitives import RoundedRectangle, Valve, \
    RoughValve, Label, BorderLine, Rectangle
import os
from src.helpers.filetools import str_to_bool


class ExtractionLineScene(Scene):
    canvas = Instance(BaseDataCanvas)

    valves = Dict
    def _get_floats(self, elem, name):
        return map(float, elem.find(name).text.split(','))

    def _make_color(self, c):
        if not isinstance(c, str):
            c = ','.join(map(str, map(int, c)))
            c = '({})'.format(c)
        return c

    def _new_rectangle(self, elem, c, bw=3, origin=None, type_tag=''):
        if origin is None:
            ox, oy = 0, 0
        else:
            ox, oy = origin

        key = elem.text.strip()
        display_name = str_to_bool(elem.get('display_name', 'T'))
        x, y = self._get_floats(elem, 'translation')
        w, h = self._get_floats(elem, 'dimension')

        color = elem.find('color')
        if color is not None:
            c = color.text.strip()

        c = self._make_color(c)

        rect = RoundedRectangle(x + ox, y + oy, width=w, height=h,
                                            name=key,
                                            border_width=bw,
                                            display_name=display_name,
                                            default_color=c,
                                            type_tag=type_tag)
        self.add_item(rect, layer=1)

    def _new_connection(self, conn, key, start, end):

        skey = start.text.strip()
        ekey = end.text.strip()
        try:
            orient = conn.get('orientation')
        except Exception:
            orient = None

        x, y = 0, 0
        sanchor = self.get_item(skey)
        if sanchor:
            x, y = sanchor.x, sanchor.y
            try:
                ox, oy = map(float, start.get('offset').split(','))
            except Exception:
                ox = 1
                oy = sanchor.height / 2.0

            x += ox
            y += oy


        x1, y1 = x, y
        eanchor = self.get_item(ekey)
        if eanchor:
            x1, y1 = eanchor.x, eanchor.y

            try:
                ox, oy = map(float, end.get('offset').split(','))
            except Exception:
                ox = 1
                oy = eanchor.height / 2.0

            x1 += ox
            y1 += oy

        if orient == 'vertical':
            x1 = x
        elif orient == 'horizontal':
            y1 = y

        klass = BorderLine
        l = klass((x, y), (x1, y1),
                  default_color=(204, 204, 204),
                  name=key,
                 width=10)
        self.add_item(l, layer=0)

    def load(self, pathname, configpath):
        self.reset_layers()

        origin, color_dict = self._load_config(configpath)
        ox, oy = origin

        cp = self._get_canvas_parser(pathname)

        ndict = dict()
        for v in cp.get_elements('valve'):
            key = v.text.strip()
            x, y = self._get_floats(v, 'translation')
            v = Valve(x + ox, y + oy, name=key,
#                                    canvas=self,
                                    border_width=3
                                    )
            v.translate = x + ox, y + oy
            # sync the states
            if key in self.valves:
                vv = self.valves[key]
                v.state = vv.state
                v.soft_lock = vv.soft_lock

            self.add_item(v, layer=1)
            ndict[key] = v

        for rv in cp.get_elements('rough_valve'):
            key = rv.text.strip()
            x, y = self._get_floats(rv, 'translation')
            v = RoughValve(x + ox, y + oy, name=key)
            self.add_item(v, layer=1)
            ndict[key] = v

        self.valves = ndict
        self._load_rects(cp, origin, color_dict)

        for i, l in enumerate(cp.get_elements('label')):
            x, y = map(float, l.find('translation').text.split(','))
            if 'label' in color_dict:
                c = color_dict['label']
            else:
                c = (204, 204, 204)

            c = self._make_color(c)
            l = Label(x + ox, y + oy,
                      bgcolor=c,
                      name='{:03}'.format(i),
                      text=l.text.strip())
            self.add_item(l, layer=1)

        for g in cp.get_elements('gauge'):
            if 'gauge' in color_dict:
                c = color_dict['gauge']
            else:
                c = (255, 255, 0)
            self._new_rectangle(g, c, origin=origin)

        for i, conn in enumerate(cp.get_elements('connection')):
            start = conn.find('start')
            end = conn.find('end')
            name = '{}_{}'.format(start.text, end.text)
            self._new_connection(conn, name, start, end)

#         xv, yv = self._get_canvas_view_range()
        xv = self.canvas.view_x_range
        yv = self.canvas.view_y_range
        x, y = xv[0], yv[0]
        w = xv[1] - xv[0]
        h = yv[1] - yv[0]

        brect = Rectangle(x, y, width=w, height=h,
                          identifier='bounds_rect',
                          fill=False, line_width=20, default_color=(0, 0, 102))
        self.add_item(brect)

    def _load_rects(self, cp, origin, color_dict):
        for key in ('stage', 'laser', 'spectrometer',
                     'turbo', 'getter', 'tank', 'pipette',
                     'ionpump'):
            for b in cp.get_elements(key):
                if key in color_dict:
                    c = color_dict[key]
                else:
                    c = (204, 204, 204)

                self._new_rectangle(b, c, bw=5, origin=origin, type_tag=key)

    def _load_config(self, p):
        color_dict = dict()

        if os.path.isfile(p):
            cp = self._get_canvas_parser(p)

            tree = cp.get_tree()
            if tree:
                xv, yv = self._get_canvas_view_range(cp)

                self.canvas.view_x_range = xv
                self.canvas.view_y_range = yv
                # get label font
                font = tree.find('font')
                if font is not None:
                    self.font = font.text.strip()

                # get default colors
                for c in tree.findall('color'):
                    t = c.text.strip()
                    k = c.get('tag')

                    t = map(float, t.split(',')) if ',' in t else t
        #            co = self._make_color(t)

                    if k == 'bgcolor':
                        self.canvas.bgcolor = t
                    else:
                        color_dict[k] = t

                # get an origin offset
                ox = 0
                oy = 0
                o = tree.find('origin')
                if o is not None:
                    ox, oy = map(float, o.text.split(','))

        return (ox, oy), color_dict
#============= EOF =============================================
