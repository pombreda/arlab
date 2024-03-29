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
from traits.api import HasTraits, List, Instance, on_trait_change, Str, Dict, \
    Color, Property, Any, Event
from traitsui.api import View, Item, TreeEditor, TreeNode
#============= standard library imports ========================
#============= local library imports  ==========================
from src.helpers.parsers.canvas_parser import CanvasParser
from src.canvas.canvas2D.scene.primitives.primitives import Primitive
from src.canvas.canvas2D.scene.browser import SceneBrowser
from src.canvas.canvas2D.scene.layer import Layer
class PrimitiveNode(TreeNode):
    add = List([Primitive])
    move = List([Primitive])
#    def can_insert(self, obj):
#        print obj, 'asdf'

class Scene(HasTraits):
    layers = List
    parser = Instance(CanvasParser)
    scene_browser = Instance(SceneBrowser)
    selected = Any
    layout_needed = Event

    @on_trait_change('layers:visible')
    def _refresh(self):
        self.layout_needed = True

    def set_canvas(self, c):
        for li in self.layers:
            for ci in li.components:
                ci.set_canvas(c)

    def reset_layers(self):
        self.layers = [Layer(name='0'), Layer(name='1')]

    def load(self, pathname):
        '''
        '''
        pass

    def render_components(self, gc, canvas):
        for li in self.layers:
            if li.visible:
                for ci in li.components:
                    ci.set_canvas(canvas)
                    ci.render(gc)

    def get_items(self, klass):
        return [ci for li in self.layers
                for ci in li.components
                    if isinstance(ci, klass)]

    def get_item(self, name, layer=None, klass=None):
        def test(la):
            nb = la.name == name
            ib = la.identifier == name
            cb = True
            if klass is not None:
                cb = isinstance(la, klass)

            return cb and (nb or ib)

        layers = self.layers
        if layer is not None:
            layers = layers[layer:layer + 1]

        for li in layers:
            nn = next((ll for ll in li.components if test(ll)), None)
            if nn is not None:
                return nn


    def add_item(self, v, layer=None):
        if layer is None:
            layer = -1

        n = len(self.layers)
        if layer > n - 1:
            self.layers.append(Layer(name='{}'.format(n)))

        layer = self.layers[layer]
        layer.add_item(v)

    def remove_item(self, v, layer=None):
        if layer is None:
            layers = self.layers
        else:
            layers = (self.layers[layer],)

        if isinstance(v, str):
            v = self.get_item(v)

        if v:
            for li in layers:
                li.remove_item(v)

    def pop_item(self, v, layer=None, klass=None):
        if layer is None:
            layers = self.layers
        else:
            layers = (self.layers[layer],)

        for li in layers:
            li.pop_item(v, klass=klass)

#        layer[key] = v
#===============================================================================
# handlers
#===============================================================================
    def _selected_changed(self, name, old, new):
        if issubclass(type(new), Primitive):
            if issubclass(type(old), Primitive):
                old.set_selected(False)
            new.set_selected(True)

        self.layout_needed = True

    def _get_canvas_parser(self, p=None):
        if p is not None:
            cp = CanvasParser(p)
            self.parser = cp
        elif self.parser:
            cp = self.parser

        return cp

    def _get_canvas_view_range(self):
        xv = (-25, 25)
        yv = (-25, 25)
        cp = self._get_canvas_parser()
        tree = cp.get_tree()
        if tree:
            elm = tree.find('xview')
            if elm is not None:
                xv = map(float, elm.text.split(','))

            elm = tree.find('yview')
            if elm is not None:
                yv = map(float, elm.text.split(','))

        return xv, yv

    def traits_view(self):
        nodes = [TreeNode(node_for=[SceneBrowser],
                          children='layers',
                          label='=layers',
                          auto_open=True
                          ),
                 TreeNode(node_for=[Layer],
                          label='label',
                          children='components',
                          auto_open=True
                          ),
                 PrimitiveNode(node_for=[Primitive],
                               children='primitives',
                               label='label',
#                               auto_open=True
                          ),
                 ]

        editor = TreeEditor(nodes=nodes,
                            selected='selected',
                            orientation='vertical')
        v = View(Item('scene_browser',
                      show_label=False,
                      editor=editor))
        return v


    def _scene_browser_default(self):
        sb = SceneBrowser(layers=self.layers)
#        self.on_trait_change(sb._update_layers, 'layers, layers[]')
        return sb
#============= EOF =============================================
