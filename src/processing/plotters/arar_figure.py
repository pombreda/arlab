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
from chaco.array_data_source import ArrayDataSource
from traits.api import HasTraits, Any, Int, Str, Tuple, Property, \
    Event, Bool, cached_property
from chaco.tools.data_label_tool import DataLabelTool
#============= standard library imports ========================
#============= local library imports  ==========================
from src.graph.error_bar_overlay import ErrorBarOverlay
from src.processing.plotters.sparse_ticks import SparseLogTicks, SparseTicks
from src.stats.core import calculate_mswd, validate_mswd
from src.helpers.formatting import floatfmt
from src.processing.plotters.flow_label import FlowDataLabel
from chaco.tools.broadcaster import BroadcasterTool
from src.graph.tools.rect_selection_tool import RectSelectionOverlay, \
    RectSelectionTool
from src.graph.tools.analysis_inspector import AnalysisPointInspector
from src.graph.tools.point_inspector import PointInspectorOverlay


class BaseArArFigure(HasTraits):
    analyses = Any
    sorted_analyses = Property(depends_on='analyses')

    group_id = Int
    padding = Tuple((60, 10, 5, 40))
    ytitle = Str
    replot_needed = Event
    _reverse_sorted_analyses = False
    graph = Any

    options = Any

    x_grid_visible = Bool(True)
    y_grid_visible = Bool(True)
    use_sparse_ticks = Bool(True)

    refresh_unknowns_table = Event
    _suppress_table_update = False

    def build(self, plots):
        """
            make plots
        """
        self._plots = plots

        def _setup_plot(pp, po):
            pp.value_range.tight_bounds = False
            pp.x_grid.visible = self.x_grid_visible
            pp.y_grid.visible = self.y_grid_visible
            if po:
                pp.value_scale=po.scale

            if self.use_sparse_ticks:
                if pp.value_scale == 'log':
                    pp.value_axis.tick_generator = SparseLogTicks()
                else:
                    pp.value_axis.tick_generator = SparseTicks()

        graph = self.graph

        vertical_resize = not all([p.height for p in plots])

        graph.vertical_resize = vertical_resize

        for i, po in enumerate(plots):
            kw = {'padding': self.padding,
                  'ytitle': po.name}

            if po.height:
                kw['bounds'] = [50, po.height]

            if i == 0:
                kw['ytitle'] = self.ytitle

            p = graph.new_plot(**kw)
            _setup_plot(p, po)
            
    def plot(self, *args, **kw):
        pass

    def replot(self, *args, **kw):
        pass

    def _get_omitted(self, ans, omit=None):
        def test(a):
            r = ai.temp_status
            if omit:
                r = r or getattr(ai, omit)
            return r or ai.tag == 'omit'

        return [i for i, ai in enumerate(ans)
                if test(ai)]

    def _set_selected(self, ans, sel):
        #print self.group_id, sel
        for i, a in enumerate(ans):
            a.temp_status = 1 if i in sel else 0

        self.refresh_unknowns_table = True
        #if not self._suppress_table_update:
        #    self.refresh_unknowns_table = True

    def _filter_metadata_changes(self, obj, func, ans):
        sel = obj.metadata.get('selections', [])
        if sel:
            obj.was_selected = True

            prev = None
            if hasattr(obj, 'prev_selection'):
                prev = obj.prev_selection

            if prev != sel:
                self._set_selected(ans, sel)
                func(sel)

            obj.prev_selection = sel

        elif hasattr(obj, 'was_selected'):
            if obj.was_selected:
                self._set_selected(ans, sel)
                func(sel)
            obj.was_selected = False
            obj.prev_selection = None
        else:
            obj.prev_selection = None

        return sel

    def _get_mswd(self, ages, errors):
        mswd = calculate_mswd(ages, errors)
        n = len(ages)
        valid_mswd = validate_mswd(mswd, n)
        return mswd, valid_mswd, n

    def _cmp_analyses(self, x):
        return x.timestamp

    def _unpack_attr(self, attr):
        return (getattr(ai, attr) for ai in self.sorted_analyses)

    def _set_y_limits(self, a, b, min_=None, max_=None,
                      pid=0, pad=None):
        mi, ma = self.graph.get_y_limits(plotid=pid)
        mi = min(mi, a)
        ma = max(ma, b)
        if min_ is not None:
            mi = min_
        if max_ is not None:
            ma = max_
        self.graph.set_y_limits(min_=mi, max_=ma, pad=pad)

    #===========================================================================
    # aux plots
    #===========================================================================
    def _plot_radiogenic_yield(self, po, plot, pid):

        ys, es = zip(*[(ai.nominal_value, ai.std_dev)
                       for ai in self._unpack_attr('rad40_percent')])
        return self._plot_aux('%40Ar*', 'rad40_percent', ys, po, plot, pid, es)

    def _plot_kcl(self, po, plot, pid):
        ys, es = zip(*[(ai.nominal_value, ai.std_dev)
                       for ai in self._unpack_attr('kcl')])
        return self._plot_aux('K/Cl', 'kcl', ys, po, plot, pid, es)

    def _plot_kca(self, po, plot, pid):
        ys, es = zip(*[(ai.nominal_value, ai.std_dev)
                       for ai in self._unpack_attr('kca')])
        return self._plot_aux('K/Ca', 'kca', ys, po, plot, pid, es)

    def _plot_moles_K39(self, po, plot, pid):
        ys, es = zip(*[(ai.nominal_value, ai.std_dev)
                       for ai in self._unpack_attr('k39')])

        return self._plot_aux('K39(fA)', 'k39', ys, po, plot, pid, es)

    #===============================================================================
    #
    #===============================================================================
    def _add_error_bars(self, scatter, errors, axis, nsigma,
                        visible=True):
        ebo = ErrorBarOverlay(component=scatter,
                              orientation=axis,
                              nsigma=nsigma,
                              visible=visible)

        scatter.underlays.append(ebo)
        setattr(scatter, '{}error'.format(axis), ArrayDataSource(errors))
        return ebo

    def _add_scatter_inspector(self,
                               # container,
                               # plot,
                               scatter,
                               add_tool=True,
                               value_format=None,
                               additional_info=None
    ):
        if add_tool:
            broadcaster = BroadcasterTool()
            scatter.tools.append(broadcaster)

            rect_tool = RectSelectionTool(scatter)
            rect_overlay = RectSelectionOverlay(tool=rect_tool)

            scatter.overlays.append(rect_overlay)
            broadcaster.tools.append(rect_tool)

            if value_format is None:
                value_format = lambda x: '{:0.5f}'.format(x)
            point_inspector = AnalysisPointInspector(scatter,
                                                     analyses=self.sorted_analyses,
                                                     convert_index=lambda x: '{:0.3f}'.format(x),
                                                     value_format=value_format,
                                                     additional_info=additional_info
            )

            pinspector_overlay = PointInspectorOverlay(component=scatter,
                                                       tool=point_inspector,
            )
            #
            scatter.overlays.append(pinspector_overlay)
            broadcaster.tools.append(point_inspector)

            u = lambda a, b, c, d: self.update_graph_metadata(a, b, c, d)
            scatter.index.on_trait_change(u, 'metadata_changed')

            #===============================================================================
            # labels
            #===============================================================================

    def _add_data_label(self, s, text, point, bgcolor='transparent',
                        label_position='top right', color=None, append=True, **kw):
        if color is None:
            color = s.color

        label = FlowDataLabel(component=s, data_point=point,
                              label_position=label_position,
                              label_text=text,
                              border_visible=False,
                              bgcolor=bgcolor,
                              show_label_coords=False,
                              marker_visible=False,
                              text_color=color,

                              # setting the arrow to visible causes an error when reading with illustrator
                              # if the arrow is not drawn
                              arrow_visible=False,
                              **kw
        )
        s.overlays.append(label)
        tool = DataLabelTool(label)
        if append:
            label.tools.append(tool)
        else:
            label.tools.insert(0, tool)
        return label

    def _build_label_text(self, x, we, mswd, valid_mswd, n):
        display_n = True
        display_mswd = n >= 2
        if display_n:
            n = 'n= {}'.format(n)
        else:
            n = ''

        if display_mswd:
            vd = '' if valid_mswd else '*'
            mswd = '{}mswd= {:0.2f}'.format(vd, mswd)
        else:
            mswd = ''

        x = floatfmt(x, 3)
        we = floatfmt(we, 4)
        pm = '+/-'

        return u'{} {}{} {} {}'.format(x, pm, we, mswd, n)

    def _set_renderer_selection(self, rs, sel):
        for rend in rs:
            meta = {'selections': sel}
            rend.index.trait_set(metadata=meta,
                                 trait_change_notify=False)

    #===============================================================================
    # property get/set
    #===============================================================================
    @cached_property
    def _get_sorted_analyses(self):
        return sorted(self.analyses,
                      key=self._cmp_analyses,
                      reverse=self._reverse_sorted_analyses
        )

        #============= EOF =============================================
