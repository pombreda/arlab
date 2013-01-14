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
from traits.api import Property, cached_property
from traitsui.api import View, Item, CodeEditor
from src.database.isotope_analysis.summary import Summary

#============= standard library imports ========================
#============= local library imports  ==========================

class ScriptSummary(Summary):
    script_text = Property
    def traits_view(self):
        v = View(Item('script_text',
                      width=755,
                      style='readonly',
                      editor=CodeEditor(), show_label=False))
        return v

class MeasurementSummary(ScriptSummary):
    @cached_property
    def _get_script_text(self):
        try:
            txt = self.record.dbrecord.measurement.script.blob
        except AttributeError:
            txt = ' '

        if txt is None:
            txt = ' '
        return txt

class ExtractionSummary(ScriptSummary):

    @cached_property
    def _get_script_text(self):
        try:
            txt = self.record.dbrecord.extraction.script.blob
        except AttributeError:
            txt = ' '
        if txt is None:
            txt = ' '
        return txt
#============= EOF =============================================
