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
from traits.api import Instance
#============= standard library imports ========================
#============= local library imports  ==========================
from src.processing.tasks.figures.figure_editor import FigureEditor
from src.processing.plotters.figure_container import FigureContainer
from src.processing.plotter_options_manager import SeriesOptionsManager, PlotterOptionsManager


class SeriesEditor(FigureEditor):
    plotter_options_manager = Instance(PlotterOptionsManager)
    plotter_options_manager_klass = SeriesOptionsManager
    pickle_path = 'series'
    basename = 'Series'

    def _plotter_options_manager_default(self):
        return self.plotter_options_manager_klass()

    def _update_unknowns_hook(self):
        po = self.plotter_options_manager.plotter_options

        ref = self.unknowns[0]
        po.load_aux_plots(ref)

        self._set_name()

    def get_component(self, ans, plotter_options):
    #         print plotter_options
        if plotter_options is None:
            pom = self.plotter_options_manager_klass()
            plotter_options = pom.plotter_options

        #         ref = ans[0]
        #         plotter_options.load_aux_plots(ref)
        #             plotter_options.load_fits(ref)

        from src.processing.plotters.series.series_model import SeriesModel

        model = SeriesModel(plot_options=plotter_options)
        model.analyses = ans
        iv = FigureContainer(model=model)

        return model, iv.component

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


#class AutoSeriesEditor(SeriesEditor):
#    auto_figure_control = Instance(AutoSeriesControl, ())


#============= EOF =============================================
