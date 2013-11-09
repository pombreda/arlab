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
from traits.api import Any, List, on_trait_change, Instance, Property, Event, File
from traitsui.api import View, UItem, InstanceEditor
from src.codetools.simple_timeit import timethis
#============= standard library imports ========================
from numpy import asarray
import os
from itertools import groupby
import pickle
#============= local library imports  ==========================
from src.paths import paths
from src.processing.tasks.analysis_edit.fits import FitSelector
from src.graph.regression_graph import StackedRegressionGraph
from src.processing.tasks.editor import BaseUnknownsEditor


class GraphEditor(BaseUnknownsEditor):
    tool = Instance(FitSelector, ())
    graph = Any
    processor = Any
    unknowns = List
    #     _unknowns = List
    component = Property
    _component = Any

    component_changed = Event
    path = File
    analysis_cache = List
    basename = ''
    pickle_path = '_'
    unpack_peaktime = False

    auto_plot = Property
    update_on_unknowns = True

    def prepare_destroy(self):
        self.dump_tool()

    def dump_tool(self):
        p = os.path.join(paths.hidden_dir, self.pickle_path)
        with open(p, 'w') as fp:
            tool = self._dump_tool()
            pickle.dump(tool, fp)

    def _dump_tool(self):
        if self.tool:
            return self.tool.fits

    def load_tool(self):
        p = os.path.join(paths.hidden_dir, self.pickle_path)
        if os.path.isfile(p):
            with open(p, 'r') as fp:
                try:
                    obj = pickle.load(fp)
                    self._load_tool(obj)
                except (pickle.PickleError, OSError, EOFError):
                    return

    def _load_tool(self, fits):
        for fi in fits:
            ff = next((fo for fo in self.tool.fits if fo.name == fi.name), None)
            if ff:
                ff.trait_set(fit=fi.fit,
                             use=fi.use,
                             show=fi.show)

    def normalize(self, xs, start=None):
        xs = asarray(xs)
        xs.sort()
        if start is None:
            start = xs[0]
        xs -= start

        # scale to hours
        xs = xs / (60. * 60.)
        return xs

    @on_trait_change('unknowns[]')
    def _update_unknowns(self, obj, name, old, new):
        #print '11111', len(self.unknowns)
        self._gather_unknowns(True)
        #print '22222', new, len(self.unknowns)
        if self.unknowns:
            if self.auto_plot:
                self.rebuild_graph()

            refiso = self.unknowns[0]
            self._load_refiso(refiso)
            self._set_name()
            self._update_unknowns_hook()
        else:
            self._null_component()
            self.component_changed = True

    def _null_component(self):
        self.graph = self._graph_factory()

    def _load_refiso(self, refiso):
        self.load_fits(refiso)

    def load_fits(self, refiso):
        if refiso.isotope_keys:
            if self.tool:
                self.tool.load_fits(refiso.isotope_keys,
                                    refiso.isotope_fits)
                self.load_tool()

    def _set_name(self):
        na = list(set([ni.sample for ni in self.unknowns]))
        na = self._grouped_name(na)
        self.name = '{} {}'.format(na, self.basename)

    def _update_unknowns_hook(self):
        pass

    @on_trait_change('tool:update_needed')
    def _tool_refresh(self):
        print 'tool update'
        self.rebuild_graph()
        #if not self.tool.suppress_refresh_unknowns:
        self.refresh_unknowns()

    def refresh_unknowns(self):
        pass

    def rebuild(self, *args, **kw):
        pass

    def rebuild_graph(self):
        #if not self.suppress_rebuild:
        graph = self.graph

        graph.clear()
        self._rebuild_graph()

        self.component_changed = True

    def _rebuild_graph(self):
        pass

    def traits_view(self):
        v = View(UItem('graph',
                       style='custom',
                       editor=InstanceEditor()))
        return v

    def _graph_default(self):
        return self._graph_factory()

    def _graph_factory(self, **kw):
        g = StackedRegressionGraph(container_dict=dict(stack_order='top_to_bottom',
                                                       spacing=5),
                                   **kw)
        return g

    def _graph_generator(self):
        for fit in self.tool.fits:
            if fit.fit and fit.show:
                yield fit

    def _get_component(self):
        return self.graph.plotcontainer

    def save_file(self, path):
        _, tail = os.path.splitext(path)
        if tail not in ('.pdf', '.png'):
            path = '{}.pdf'.format(path)

        c = self.component

        '''
            chaco becomes less responsive after saving if 
            use_backbuffer is false and using pdf 
        '''
        c.use_backbuffer = True

        _, tail = os.path.splitext(path)
        if tail == '.pdf':
            from chaco.pdf_graphics_context import PdfPlotGraphicsContext

            gc = PdfPlotGraphicsContext(filename=path,
                                        #                                         pagesize='letter'
            )
            gc.render_component(c, valign='center')
            gc.save()
        else:
            from chaco.plot_graphics_context import PlotGraphicsContext

            gc = PlotGraphicsContext((int(c.outer_width), int(c.outer_height)))
            gc.render_component(c)
            gc.save(path)

            #         with gc:
            #         self.rebuild_graph()

    def _gather_unknowns(self, refresh_data,
                         exclude='invalid',
                         compress_groups=True):
        '''
            use cached runs
            
            use exclude keyward to specific tags that will not be 
            gathered
            
        '''

        ans = self.unknowns
        if refresh_data or not ans:
            #ids = [ai.uuid for ai in self.analysis_cache]
            #aa = [ai for ai in self.unknowns if ai.uuid not in ids]
            #
            #nids = (ai.uuid for ai in self.unknowns if ai.uuid in ids)
            #bb = [next((ai for ai in self.analysis_cache if ai.uuid == i)) for i in nids]
            #aa = list(aa)
            #aa=self.unknowns

            if ans:
                ans = timethis(self.processor.make_analyses,
                               args=(ans,),
                               kwargs={'exclude': exclude,
                                       'unpack': self.unpack_peaktime},
                               msg='MAKE ANALYSES TOTAL')

                #unks = self.processor.make_analyses(list(aa),
                #                                    exclude=exclude)
                #ans = unks
            #    if bb:
            #        ans.extend(bb)
            #else:
            #    ans = bb

            if compress_groups:
                # compress groups
                self._compress_unknowns(ans)

            #self.trait_set(unknowns=ans, trait_change_notify=False)
            self.unknowns = ans
        else:
            if exclude:
                ans = self.processor.filter_analysis_tag(ans, exclude)

        return ans

    def _compress_unknowns(self, ans):
        if not ans:
            return

        key = lambda x: x.group_id
        ans = sorted(ans, key=key)
        groups = groupby(ans, key)

        mgid, analyses = groups.next()
        for ai in analyses:
            ai.group_id = 0

        for gid, analyses in groups:
            for ai in analyses:
                ai.group_id = gid - mgid

    def _get_auto_plot(self):
        return len(self.unknowns) == 1 or self.update_on_unknowns

        #============= EOF =============================================
