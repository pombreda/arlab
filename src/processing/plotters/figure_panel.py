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
from traits.api import HasTraits, Any, on_trait_change, List
#============= standard library imports ========================
from itertools import groupby
from src.graph.stacked_graph import StackedGraph
from src.processing.plotters.ideogram.ideogram import Ideogram
from numpy.core.numeric import Inf

#============= local library imports  ==========================
class FigurePanel(HasTraits):
    figures = List
    graph = Any
    analyses = Any
    plot_options = Any
    _index_attr = None
    equi_stack = False
    graph_klass = StackedGraph
    meta = Any

    @on_trait_change('analyses[]')
    def _analyses_items_changed(self):
        self.figures = self._make_figures()

    def _make_figures(self):
        key = lambda x: x.group_id
        ans = sorted(self.analyses, key=key)
        gs = [self._figure_klass(analyses=list(ais), group_id=gid)
              for gid, ais in groupby(ans, key=key)]
        return gs

    def dump_metadata(self):
        return self.graph.dump_metadata()

    def load_metadata(self, md):
        self.graph.load_metadata(md)

    def make_graph(self):

        g = self.graph_klass(panel_height=200,
                             equi_stack=self.equi_stack,
                             container_dict=dict(padding=0), )

        po = self.plot_options
        attr = self._index_attr
        mi, ma = -Inf, Inf
        if attr:
            xmas, xmis = zip(*[(i.max_x(attr), i.min_x(attr))
                               for i in self.figures])
            mi, ma = min(xmis), max(xmas)

        for i, fig in enumerate(self.figures):
            fig.trait_set(xma=ma, xmi=mi,
                          options=po,
                          graph=g,
            )

            plots = list(po.get_aux_plots())

            if i == 0:
                fig.build(plots)

            fig.plot(plots)

        #meta=self.meta
        #print 'meta',meta
        #if meta:
        #    g.load_metadata(meta)

        self.graph = g
        #print self.graph
        return g.plotcontainer

    #============= EOF =============================================
