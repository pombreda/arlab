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
from traits.api import HasTraits, List, Any, Event
from traitsui.api import View, Item, TableEditor
from src.graph.graph import Graph
#============= standard library imports ========================
from numpy import linspace, random, hstack, polyval, \
    delete, bitwise_and, polyfit, ones
from chaco.tools.broadcaster import BroadcasterTool
#============= local library imports  ==========================
from src.graph.tools.rect_selection_tool import RectSelectionTool
from src.graph.tools.data_tool import DataTool, DataToolOverlay
from src.graph.time_series_graph import TimeSeriesGraph
from src.graph.stacked_graph import StackedGraph
from src.regression.ols_regressor import PolynomialRegressor
from src.regression.mean_regressor import MeanRegressor


class RegressionGraph(Graph):
    filters = List
    selected_component = Any
    regressors = List
    regression_results = Event
    suppress_regression=False
    use_data_tool=True
#    fits = List
#    def clear(self):
#        super(RegressionGraph, self).clear()
#        self.regressors = []
#    def set_fits(self, fits):
#        self.fits = fits
#        for fi, pi in zip(fits, self.plots):
#            scatter = pi.plots['data'][0]
#            scatter.fit = fi

    def _update_graph(self):
        if self.suppress_regression:
            return
        
        self.regressors = []
        for plot in self.plots:
            ks = plot.plots.keys()
            try:
                scatters, kkk= zip(*[(plot.plots[k][0],k) for k in ks if k.startswith('data')])
                ind=kkk[0][-1]
                fls=[plot.plots[kk][0] for kk in ks if kk=='fit{}'.format(ind)]
                uls=[plot.plots[kk][0] for kk in ks if kk=='upper CI{}'.format(ind)]
                lls=[plot.plots[kk][0] for kk in ks if kk=='lower CI{}'.format(ind)]
                
                #fls = [plot.plots[k][0] for k in ks if k.startswith('fit')]
                #uls = [plot.plots[k][0] for k in ks if k.startswith('upper')]
                #lls = [plot.plots[k][0] for k in ks if k.startswith('lower')]
                for si, fl, ul, ll in zip(scatters, fls, uls, lls):
                    self._plot_regression(plot, si, fl, ul, ll)
            except ValueError,e:
                break
        else:
            self.regression_results = self.regressors

    def _plot_regression(self, plot, scatter, line, uline, lline):
        try:
            sel = scatter.index.metadata.get('selections', [])
            args = self._regress(selection=sel,
                                           plot=plot,
                                           fit=scatter.fit,
                                           x=scatter.index.get_data(),
                                           y=scatter.value.get_data())
            if args:
                fx, fy, ly, uy = args
                line.index.set_data(fx)
                line.value.set_data(fy)

                lline.index.set_data(fx)
                lline.value.set_data(ly)

                uline.index.set_data(fx)
                uline.value.set_data(uy)
        except KeyError:
            pass

    def _regress(self, 
                 x,y,
#                 x=None, y=None,
                 selection=None,
                 plotid=0,
                 plot=None,
                 component=None,
                 filterstr=None,
                 fit=None):

        fit = self._convert_fit(fit)
        if fit is None:
            return

        if plot is None:
            plot = self.plots[plotid]

#        if x is None or y is None:
#            x = plot.data.get_data('x0')
#            y = plot.data.get_data('y0')
        if filterstr:
            x, y = self._apply_filter(filterstr, x, y)
            
        if selection:
            x = delete(x[:], selection, 0)
            y = delete(y[:], selection, 0)

        low = plot.index_range.low
        high = plot.index_range.high
        if fit in [1, 2, 3]:
            if len(y) < fit + 1:
                return
            st = low
            xn = x - st
            r = PolynomialRegressor(xs=xn, ys=y,
                                    degree=fit)
            self.regressors.append(r)
            fx = linspace(0, (high - low), 200)

            fy = r.predict(fx)
            if fy is None:
                return

            ci = r.calculate_ci(fx)
            if ci is not None:
                ly, uy = ci
            else:
                ly, uy = fy, fy
            fx += low

        else:
            r = MeanRegressor(xs=x, ys=y)
            self.regressors.append(r)
            n = 10
            fx = linspace(low, high, n)
            m = r.coefficients[0]
            if fit.endswith('SEM'):
                s = r.coefficient_errors[1]
                r.error_calc = 'SEM'
            else:
                r.error_calc = 'SD'
                s = r.coefficient_errors[0]

            fy = ones(n) * m
            uy = fy + s
            ly = fy - s

        return fx, fy, ly, uy

    def _convert_fit(self, f):
        if isinstance(f, str):
            f = f.lower()
            fits = ['linear', 'parabolic', 'cubic']
            if f in fits:
                f = fits.index(f) + 1
            elif not 'average' in f:
                f = None

        return f

    def _apply_filter(self, filt, xs, ys):
#        if filt:
        '''
            100   == filters out t>100
            10,100 == fitlers out t<10 and t>100

        '''
        filt = map(float, filt.split(','))
        ge = filt[-1]
        sli = xs.__le__(ge)

        if len(filt) == 2:
            le = filt[0]
            sli = bitwise_and(sli, xs.__ge__(le))
            if le > ge:
                return

#        dplot.index.metadata['selections'] = list(invert(sli).nonzero()[0])
        return xs[sli], ys[sli]#, list(invert(sli).nonzero()[0])

    def new_series(self, x=None, y=None,
                   ux=None, uy=None, lx=None, ly=None,
                   fx=None, fy=None,
                   fit='linear',
                   marker='circle',
                   marker_size=2,
                   plotid=0, *args, **kw):

        self.filters.append(None)
        kw['marker'] = marker
        kw['marker_size'] = marker_size
        if not fit:
            return super(RegressionGraph, self).new_series(x, y,
                                                           plotid=plotid,
                                                           *args, **kw)


        kw['type'] = 'scatter'
        plot, names, rd = self._series_factory(x, y, plotid=plotid, **kw)
        si = len([p for p in plot.plots.keys() if p.startswith('data')])

        rd['selection_color'] = 'red'
        rd['selection_marker'] = marker
        rd['selection_marker_size'] = marker_size + 2

        scatter = plot.plot(names, **rd)[0]
        self.set_series_label('data{}'.format(si), plotid=plotid)
        scatter.index.on_trait_change(self._update_graph, 'metadata_changed')

        scatter.fit = fit

        if x is not None and y is not None:
            args = self._regress(x, y,plotid=plotid)
            if args:
                fx, fy, ly, uy = args

        kw['color'] = 'black'
        kw['type'] = 'line'
        kw['render_style'] = 'connectedpoints'
        plot, names, rd = self._series_factory(fx, fy, plotid=plotid, **kw)
        line = plot.plot(names, **rd)[0]
        self.set_series_label('fit{}'.format(si), plotid=plotid)

        kw['color'] = 'red'
        plot, names, rd = self._series_factory(fx, uy, line_style='dash', plotid=plotid, **kw)
        plot.plot(names, **rd)[0]
        self.set_series_label('upper CI{}'.format(si), plotid=plotid)

        plot, names, rd = self._series_factory(fx, ly, line_style='dash', plotid=plotid, **kw)
        plot.plot(names, **rd)[0]
        self.set_series_label('lower CI{}'.format(si), plotid=plotid)

        try:
            self._set_bottom_axis(plot, plot, plotid)
        except:
            pass
        
        self._add_tools(scatter, plotid)
        return plot, scatter, line

    def _add_tools(self, scatter, plotid):
        plot = self.plots[plotid]

        broadcaster = BroadcasterTool()
        self.plots[plotid].container.tools.append(broadcaster)

        rect_tool = RectSelectionTool(scatter,
                                      parent=self,
                                      plot=plot,
                                      plotid=plotid)
        scatter.overlays.append(rect_tool)

#        o = ScatterInspectorOverlay(scatter,
#                                  hover_color='blue'
#                                  )
#        scatter.overlays.append(o)

        #add a broadcaster so scatterinspector and rect selection will received events
        broadcaster.tools.append(rect_tool)
        data_tool = DataTool(component=plot,
                             plot=scatter,
                             plotid=plotid,
                             parent=self
                             )
        data_tool_overlay = DataToolOverlay(component=scatter,
                                            tool=data_tool,
                                            )
        scatter.overlays.append(data_tool_overlay)

        broadcaster.tools.append(data_tool)
        if not self.use_data_tool:
            data_tool.visible=False

    def set_x_limits(self, *args, **kw):
        '''
        '''
        super(RegressionGraph, self).set_x_limits(*args, **kw)
        self._update_graph()

class RegressionTimeSeriesGraph(RegressionGraph, TimeSeriesGraph):
    pass

class StackedRegressionGraph(RegressionGraph, StackedGraph):
    pass

class StackedRegressionTimeSeriesGraph(StackedRegressionGraph, TimeSeriesGraph):
    pass
if __name__ == '__main__':
    rg = RegressionGraph()
    rg.new_plot()
    x = linspace(0, 10, 100)
    y = 2 * x + random.rand(100) * 50
    rg.new_series(x, y)
    rg.configure_traits()
#============= EOF =============================================
