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
from traits.api import HasTraits, Dict, Bool
#============= standard library imports ========================
#============= local library imports  ==========================

from src.extraction_line.graph.nodes import ValveNode, RootNode, \
    PumpNode, Edge, SpectrometerNode, LaserNode, TankNode, PipetteNode, \
    GaugeNode

from src.canvas.canvas2D.scene.primitives.valves import Valve

from src.canvas.canvas2D.scene.canvas_parser import CanvasParser
from src.extraction_line.graph.traverse import BFT

#@todo: add volume calculation


def get_volume(elem, tag='volume', default=0):
    """
        get volume tag from xml
    """
    vol = elem.find(tag)
    if vol is not None:
        vol = float(vol.text.strip())
    else:
        vol = default
    return vol


def split_graph(n):
    """
        valves only have binary connections
        so can only split in half
    """

    if len(n.edges) == 2:
        e1, e2 = n.edges
        return e1.get_node(n), e2.get_node(n)
    else:
        return n.edges[0].get_node(n),


class ExtractionLineGraph(HasTraits):
    nodes = Dict
    suppress_changes = False
    inherit_state = Bool

    def load(self, p):

        cp = CanvasParser(p)
        if cp.get_root() is None:
            return

        nodes = dict()

        #=======================================================================
        # load nodes
        #=======================================================================
        # load roots
        for t, klass in (('stage', RootNode),
                         ('spectrometer', SpectrometerNode),
                         ('valve', ValveNode),
                         ('rough_valve', ValveNode),
                         ('turbo', PumpNode),
                         ('ionpump', PumpNode),
                         ('laser', LaserNode),
                         ('tank', TankNode),
                         ('pipette', PipetteNode),
                         ('gauge', GaugeNode),
        ):
            for si in cp.get_elements(t):
                n = si.text.strip()
                if t in ('valve', 'rough_valve'):
                    o_vol = get_volume(si, tag='open_volume', default=10)
                    c_vol = get_volume(si, tag='closed_volume', default=5)
                    vol = (o_vol, c_vol)
                else:
                    vol = get_volume(si)

                node = klass(name=n, volume=vol)
                nodes[n] = node

        #=======================================================================
        # load edges
        #=======================================================================
        for ei in cp.get_elements('connection'):
            sa = ei.find('start')
            ea = ei.find('end')
            vol = get_volume(ei)
            edge = Edge(volume=vol)
            s_name = ''
            if sa.text in nodes:
                s_name = sa.text
                sa = nodes[s_name]
                edge.a_node = sa
                sa.add_edge(edge)

            e_name = ''
            if ea.text in nodes:
                e_name = ea.text
                ea = nodes[e_name]
                edge.b_node = ea
                ea.add_edge(edge)

            edge.name = '{}_{}'.format(s_name, e_name)

        self.nodes = nodes

    def set_valve_state(self, name, state, *args, **kw):
        if name in self.nodes:
            v_node = self.nodes[name]
            v_node.state = 'open' if state else 'closed'

    def set_canvas_states(self, canvas, name):
        scene = canvas.canvas2D.scene
        if not self.suppress_changes:
            if name in self.nodes:
                s_node = self.nodes[name]

                # new algorithm
                # if valve closed
                #    split tree and fill each sub tree
                # else:
                #    for each edge of the start node
                #        breath search for the max state
                #
                #    find max max_state
                #    fill nodes with max_state
                #        using a depth traverse
                #
                # new variant
                # recursively split tree if node is closed

                self._set_state(scene, s_node)
                self._clear_visited()

    def _set_state(self, scene, n):
        if n.state == 'closed' and not n.visited:
            n.visited = True
            for ni in split_graph(n):
                self._set_state(scene, ni)
        else:
            state, term = self._find_max_state(n)
            self._clear_fvisited()
            self.fill(scene, n, state, term)

        self._clear_fvisited()

    def calculate_volumes(self, node):
        if isinstance(node, str):
            if node not in self.nodes:
                return [(0, 0), ]

            node = self.nodes[node]

        if node.state == 'closed':
            nodes = split_graph(node)
        else:
            nodes = (node, )

        vs = [(ni.name, self._calculate_volume(ni)) for ni in nodes]
        self._clear_fvisited()
        return vs

    def _calculate_volume(self, node, k=0):
        """
            use a Depth-first Traverse
            accumulate volume
        """
        debug = False
        vol = node.volume
        node.f_visited = True
        if debug:
            print '=' * (k + 1), node.name, node.volume, vol

        for i, ei in enumerate(node.edges):
            n = ei.get_node(node)
            if n is None:
                continue

            vol += ei.volume
            if debug:
                print '-' * (k + i + 1), ei.name, ei.volume, vol

            if not n.f_visited:
                n.f_visited = True
                if n.state == 'closed':
                    vol += n.volume
                    if debug:
                        print 'e' * (k + i + 1), n.name, n.volume, vol

                else:
                    v = self._calculate_volume(n, k=k + 1)
                    vol += v
                    if debug:
                        print 'n' * (k + i + 1), n.name, v, vol

        return vol


    def _find_max_state(self, node):
        """
            use a Breadth-First Traverse
            accumulate the max state at each node
        """
        m_state, term = False, ''
        for ni in BFT(self, node):

            if isinstance(ni, PumpNode):
                return 'pump', ni.name

            if isinstance(ni, LaserNode):
                m_state, term = 'laser', ni.name
            elif isinstance(ni, PipetteNode):
                m_state, term = 'pipette', ni.name
            elif isinstance(ni, GaugeNode):
                m_state, term = 'gauge', ni.name

            if m_state not in ('laser', 'pipette'):
                if isinstance(ni, SpectrometerNode):
                    m_state, term = 'spectrometer', ni.name
                elif isinstance(ni, TankNode):
                    m_state, term = 'tank', ni.name
        else:
            return m_state, term

    def fill(self, scene, root, state, term):
        self._set_item_state(scene, root.name, state, term)
        for ei in root.edges:
            n = ei.get_node(root)
            if n is None:
                continue
            self._set_item_state(scene, ei.name, state, term)

            if n.state != 'closed' and not n.f_visited:
                n.f_visited = True
                self.fill(scene, n, state, term)

    def _set_item_state(self, scene, name, state, term, color=None):
        if not isinstance(name, str):
            raise ValueError('name needs to be a str. provided={}'.format(name))

        obj = scene.get_item(name)

        if obj is None \
            or obj.type_tag in ('turbo', 'tank', 'ionpump'):
            return

        if not color and state:
            color = scene.get_item(term).default_color

        if isinstance(obj, Valve):

            # set the color of the valve to
            # the max state if the valve is open
            if self.inherit_state:
                if obj.state != 'closed':
                    if state:
                        obj.active_color = color
                    else:
                        obj.active_color = obj.oactive_color
                        #                         obj.active_color = 0, 255, 0
            return

        if state:
            obj.active_color = color
            obj.state = True
        else:
            obj.state = False

    def _clear_visited(self):
        for ni in self.nodes.itervalues():
            ni.visited = False
            #             for ei in ni.edges:
            #                 ei.visited = False

    def _clear_fvisited(self):
        for ni in self.nodes.itervalues():
            ni.f_visited = False

    def __getitem__(self, key):
        if not isinstance(key, str):
            key = key.name

        if key in self.nodes:
            return self.nodes[key]


if __name__ == '__main__':
    elg = ExtractionLineGraph()
    elg.load('/Users/ross/Pychrondata_dev/setupfiles/canvas2D/canvas.xml')
    elg.set_valve_state('H', True)

    print elg.calculate_volumes('Obama')
    #print elg.calculate_volumes('Bone')
    #state, root = elg.set_valve_state('H', True)
    #state, root = elg.set_valve_state('H', False)

    #print '-------------------------------'
    #print state, root

#============= EOF =============================================

