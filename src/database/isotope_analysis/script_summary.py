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
from traits.api import HasTraits, Property, cached_property, Any
from traitsui.api import View, Item, CodeEditor
# from src.database.isotope_analysis.summary import Summary

#============= standard library imports ========================
#============= local library imports  ==========================

class ScriptSummary(HasTraits):
    record = Any
    script_text = Property
    editor_klass = CodeEditor
    style = 'readonly'
    def traits_view(self):
        v = View(self._get_script_text_item())
        return v
    def _get_script_text_item(self, **kw):
        return Item('script_text',
                      width=self.record.item_width,
                      style=self.style,
                      editor=self.editor_klass(),
                      show_label=False, **kw)

class MeasurementSummary(ScriptSummary):
    @cached_property
    def _get_script_text(self):
        txt = None
        try:
            txt = self.record.measurement.script.blob
        except AttributeError:
            pass

        if txt is None:
            txt = 'No Measurement script saved with analysis'

        return txt

class ExtractionSummary(ScriptSummary):

    @cached_property
    def _get_script_text(self):
        txt = None
        try:
            txt = self.record.extraction.script.blob
        except AttributeError, e:
            print e

        if txt is None:
            txt = 'No Extraction script saved with analysis'
        return txt


class ExperimentSummary(ScriptSummary):
    @cached_property
    def _get_script_text(self):
        txt = None
        try:
            txt = self.record.extraction.experiment.blob
        except AttributeError:
            pass

        if txt is None:
            txt = 'No Experiment Set saved with analysis'
        return txt

#============= EOF =============================================
