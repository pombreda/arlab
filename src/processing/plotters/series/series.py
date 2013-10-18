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
from traits.api import Array
#============= standard library imports ========================
from numpy import array
#============= local library imports  ==========================
from src.processing.plotters.arar_figure import BaseArArFigure

N = 500


class Series(BaseArArFigure):
    xs = Array

    def build(self, plots):
        graph = self.graph
        for po in plots:
            if po.use:
                p = graph.new_plot(padding=self.padding,
                                   ytitle=po.name,
                )
                #p.value_scale=po.scale
                p.padding_left = 75
                p.value_range.tight_bounds = False

    def plot(self, plots):
        """
            plot data on plots
        """
        graph = self.graph
        self.xs = array([ai.timestamp for ai in self.sorted_analyses]) / 3600.
        self.xs -= self.xs[0]
        with graph.no_regression(refresh=True):
            plots = [po for po in plots if po.use]
            for i, po in enumerate(plots):
                self._plot_series(po, i)

            if plots:
                graph.set_x_limits(min_=0, max_=max(self.xs), pad='0.1',
                                   plotid=0)

    def _plot_series(self, po, pid):
        graph = self.graph

        ys = [ai.nominal_value for ai in self._unpack_attr(po.name)]
        yerr = [ai.std_dev for ai in self._unpack_attr(po.name)]

        scatter, p = graph.new_series(x=self.xs,
                                      y=ys,
                                      yerror=yerr,
                                      fit=po.fit,
                                      plotid=pid,
                                      type='scatter'
        )
        p.value_scale = po.scale
        self._add_error_bars(scatter, yerr, 'y', 1,
                             visible=po.y_error)

    def _unpack_attr(self, attr):
        if attr.endswith('bs'):
            return (ai.isotopes[attr[:-2]].baseline.uvalue
                    for ai in self.sorted_analyses)
        elif '/' in attr:
            n, d = attr.split('/')
            return (getattr(ai, n) / getattr(ai, d)
                    for ai in self.sorted_analyses)
        elif attr == 'PC':
            return (getattr(ai, 'peak_center')
                    for ai in self.sorted_analyses)
        else:
            return super(Series, self)._unpack_attr(attr)

#===============================================================================
# plotters
#===============================================================================

#===============================================================================
# overlays
#===============================================================================

#===============================================================================
# utils
#===============================================================================

#===============================================================================
# labels
#===============================================================================

#============= EOF =============================================
