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
from pyface.timer.do_later import do_later
from traits.api import Instance, on_trait_change
#============= standard library imports ========================
#============= local library imports  ==========================
from src.processing.tasks.figures.figure_editor import FigureEditor
from src.processing.plotters.figure_container import FigureContainer
from src.processing.plotter_options_manager import InverseIsochronOptionsManager


class InverseIsochronEditor(FigureEditor):
    plotter_options_manager = Instance(InverseIsochronOptionsManager, ())
    basename = 'iso'

    parent_editor = None

    @on_trait_change('model:panels:figures:refresh_unknowns_table')
    def _handle_refresh(self, obj, name, old, new):
        #print 'rebuild parent', obj.suppress
        if self.parent_editor and not obj.suppress:
            self.parent_editor.rebuild()

    def load_fits(self, refiso):
        pass

    def get_component(self, ans, plotter_options):

        if plotter_options is None:
            pom = InverseIsochronOptionsManager()
            plotter_options = pom.plotter_options

        from src.processing.plotters.isochron.isochron_model \
            import InverseIsochronModel

        model = InverseIsochronModel(plot_options=plotter_options)
        model.analyses = ans
        iv = FigureContainer(model=model)

        #force are refresh
        model.refresh()

        return model, iv.component

        #def replot(self):
        #    print self.model

#============= EOF =============================================
