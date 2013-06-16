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
from traits.api import HasTraits, Any, Instance, on_trait_change, List, File
from traitsui.api import View, Item, UItem
#============= standard library imports ========================
#============= local library imports  ==========================
from enable.component_editor import ComponentEditor as EnableComponentEditor
from src.envisage.tasks.base_editor import BaseTraitsEditor
from src.processing.plotter_options_manager import IdeogramOptionsManager, \
    SpectrumOptionsManager, InverseIsochronOptionsManager
import os
from src.processing.tasks.analysis_edit.graph_editor import GraphEditor

class FigureEditor(GraphEditor):
#     path = File
    component = Any
#     tool = Any
    plotter_options_manager = Any
#     processor = Any
#     unknowns = List
#     _unknowns = List
    _cached_unknowns = List

    def traits_view(self):
        v = View(UItem('component',
                       style='custom',
                       width=650,
                       editor=EnableComponentEditor()))
        return v

    @on_trait_change('unknowns[]')
    def _update_unknowns(self):
        self.rebuild()

    def set_group(self, idxs, gid):
        for i, (ui, uu) in enumerate(zip(self._unknowns, self.unknowns)):
            if i in idxs:
                ui.group_id = gid
                uu.group_id = gid

        self.rebuild()

    def rebuild(self):
        ans = self._gather_unknowns()
        po = self.plotter_options_manager.plotter_options
        comp = self._get_component(ans, po)
        self.component = comp

    def _gather_unknowns(self):
        if self._cached_unknowns:
            # removed items:
            if len(self.unknowns) < len(self._cached_unknowns):
                ans = [ui for ui, ci in zip(self._unknowns, self._cached_unknowns)
                                        if ci in self.unknowns]
            # added items
            elif len(self.unknowns) > len(self._cached_unknowns):
                nonloaded = list(set(self.unknowns) - set(self._cached_unknowns))
                nonloaded = self.processor.make_analyses(nonloaded)
                self.processor.load_analyses(nonloaded)
                self._unknowns.extend(nonloaded)

            ans = self._unknowns
        else:
            unks = self.unknowns
            unks = self.processor.make_analyses(unks)
            self.processor.load_analyses(unks)
            ans = unks

        self._cached_unknowns = self.unknowns[:]
        if ans:
            self._unknowns = ans
            return ans

    def _get_component(self, ans, po):
        raise NotImplementedError

class IdeogramEditor(FigureEditor):
    plotter_options_manager = Instance(IdeogramOptionsManager, ())
    def _get_component(self, ans, po):
        comp = self.processor.new_ideogram(ans=ans, plotter_options=po)
        return comp

class SpectrumEditor(FigureEditor):
    plotter_options_manager = Instance(SpectrumOptionsManager, ())
    def _get_component(self, ans, po):
        comp = self.processor.new_spectrum(ans=ans, plotter_options=po)
        return comp

class InverseIsochronEditor(FigureEditor):
    plotter_options_manager = Instance(InverseIsochronOptionsManager, ())
    def _get_component(self, ans, po):
        comp = self.processor.new_inverse_isochron(ans=ans, plotter_options=po)
        return comp


#============= EOF =============================================
