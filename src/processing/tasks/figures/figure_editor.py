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
from traits.api import HasTraits, Any, Instance, on_trait_change, \
    List, Bool, Int, Float, Event
from traitsui.api import View, Item, UItem
from enable.component_editor import ComponentEditor as EnableComponentEditor
#============= standard library imports ========================
from itertools import groupby
#============= local library imports  ==========================
from src.processing.plotter_options_manager import IdeogramOptionsManager, \
    SpectrumOptionsManager, InverseIsochronOptionsManager, SeriesOptionsManager
from src.processing.tasks.analysis_edit.graph_editor import GraphEditor
from src.codetools.simple_timeit import timethis
from src.processing.plotters.figure_container import FigureContainer
from src.processing.tasks.analysis_edit.plot_editor_pane import flatten_container
from src.processing.tasks.figures.annotation import AnnotationTool, AnnotationOverlay


class FigureEditor(GraphEditor):
#     path = File
    table_editor = Any
    component = Any
    #     plotter = Any
    #     tool = Any
    plotter_options_manager = Any
    associated_editors = List
    #     processor = Any
    #     unknowns = List
    #     _unknowns = List
    #     _cached_unknowns = List
    #     _suppress_rebuild = False

    annotation_tool = Any

    model = Any

    @on_trait_change('model:panels:figures:refresh_unknowns_table')
    def _handle_refresh(self):
        pass
        #self.suppress_rebuild=True
        print 'figure editor refresh', id(self)
        for e in self.associated_editors:
            if isinstance(e, FigureEditor):
                #e.rebuild_graph()
                if e.model:
                    for p in e.model.panels:
                        for f in p.figures:
                            f.replot()

                            #e.replota()

                            #e.rebuild(refresh_data=False)

    #    self.suppress_rebuild=False
    def traits_view(self):
        v = View(UItem('component',
                       style='custom',
                       width=650,
                       editor=EnableComponentEditor()))
        return v

    def add_text_box(self):
        if self.annotation_tool is None:
            an = AnnotationOverlay(component=self.component)
            at = AnnotationTool(an, components=[an])
            an.tools.append(at)
            self.annotation_tool = at
            self.component.overlays.append(an)

        elif not self.annotation_tool.active:
            an = AnnotationOverlay(component=self.component)
            self.annotation_tool.components.append(an)
            self.annotation_tool.component = an
            an.tools.append(self.annotation_tool)
            self.component.overlays.append(an)

        else:
            self.annotation_tool = None

    def set_group(self, idxs, gid, refresh=True):

        for i, uu in enumerate(self.unknowns):
        #         for i, (ui, uu) in enumerate(zip(self._unknowns, self.unknowns)):
            if i in idxs:
            #                 ui.group_id = gid
                uu.group_id = gid

        if refresh:
            self.rebuild(refresh_data=False)

    def _rebuild_graph(self):
        self.rebuild(refresh_data=False)

    def _update_unknowns_hook(self):
        ans = self.unknowns
        for e in self.associated_editors:
            if isinstance(e, FigureEditor):
                e.analysis_cache = self.analysis_cache
                #e.trait_set(unknowns=ans, trait_change_notify=False)
                e.unknowns = ans
            else:
                e.items = ans

    def rebuild(self, refresh_data=True, compress_groups=True):
        ans = self._gather_unknowns(refresh_data, compress_groups=compress_groups)

        if ans:
            po = self.plotter_options_manager.plotter_options

            model, comp = timethis(self.get_component, args=(ans, po),
                                   msg='get_component {}'.format(self.__class__.__name__))
            #comp = self._get_component(ans, po)

            #if set_model:
            self.model = model
            self.component = comp
            self.component_changed = True

    def get_component(self, ans, po):
        pass

        #         return self._get_component()

#         func = getattr(self.processor, self.func)
#         return func(ans=ans, plotter_options=po)


# class SeriesEditor(FigureEditor):
#     plotter_options_manager = Instance(SeriesOptionsManager, ())
#     func = 'new_series'
#     plotter_options_manager = Instance(SeriesOptionsManager, ())
#     def _get_component(self, ans, po):
#         if ans:
#             comp, plotter = self.processor.new_series(ans=ans,
#                                                       options=dict(fits=self.tool.fits),
#                                                       plotter_options=po)
#             self.plotter = plotter
#             return comp

#     def show_series(self, key, fit='Linear'):
#         fi = next((ti for ti in self.tool.fits if ti.name == key), None)
# #         self.tool.suppress_refresh_unknowns = True
#         if fi:
#             fi.trait_set(
#                          fit=fit,
#                          show=True,
#                          trait_change_notify=False)
#
#         self.rebuild(refresh_data=False)
#             fi.fit = fit
#             fi.show = True

#         self.tool.suppress_refresh_unknowns = False








#============= EOF =============================================
#
#     def _gather_unknowns_cached(self):
#         if self._cached_unknowns:
#             # removed items:
# #             if len(self.unknowns) < len(self._cached_unknowns):
#             # added items
# #             else:
#
#             # get analyses not loaded
#             cached_recids = [ui.record_id for ui in self._cached_unknowns]
#             nonloaded = [ui for ui in self.unknowns
#                             if not ui.record_id in cached_recids]
#             if nonloaded:
#                 nonloaded = self.processor.make_analyses(nonloaded)
#                 self.processor.load_analyses(nonloaded)
#                 self._unknowns.extend(nonloaded)
#
#             # remove analyses in _unknowns but not in unknowns
#             recids = [ui.record_id for ui in self.unknowns]
#             ans = [ui for ui in  self._unknowns
#                    if ui.record_id in recids]
# #             for i,ci in enumerate(self._cached_unknowns):
# #                 if ci in self.unknowns:
# #             ans = self._unknowns
# #             ans = [ui for ui, ci in zip(self._unknowns, self._cached_unknowns)
# #                                     if ci in self.unknowns]
#         else:
#             unks = self.unknowns
#             unks = self.processor.make_analyses(unks)
#             self.processor.load_analyses(unks)
#             ans = unks
#
# #         self._cached_unknowns = self.unknowns[:]
#         if ans:
#
#             # compress groups
#             self._compress_unknowns(ans)
#
#             self._unknowns = ans
#             return ans
