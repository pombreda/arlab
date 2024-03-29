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
from traits.api import List
#============= standard library imports ========================
from reportlab.platypus.doctemplate import SimpleDocTemplate
from reportlab.lib.units import inch
# from reportlab.lib.pagesizes import cm
#============= local library imports  ==========================
from src.processing.publisher.writers.writer import BaseWriter
from src.processing.publisher.templates.tables.ideogram_table import IdeogramTable
from src.processing.publisher.templates.tables.spectrum import SpectrumTable
from reportlab.lib.pagesizes import legal, landscape
from reportlab.platypus.flowables import Image


class PDFWriter(BaseWriter):
    _text = ''
#    def __init__(self,*args,**kw):
    _flowables = List

    def add_ideogram_table(self, analyses,
                           widths=None,
#                           configure_table=True,
                           add_title=False, add_header=False, tablenum=1, **kw):
        ta = IdeogramTable()
#        if widths is None:
#            info = ta.edit_traits(kind='modal')
#            if not info.result:
#                return True
#        else:
#            ta.set_widths(widths)

        ta.add_header = add_header
        ta.add_title = add_title
        ta.number = tablenum
        fta = ta.make(analyses)
        self._flowables.append(fta)
        return ta

    def add_spectrum_table(self, samples):

        ta = SpectrumTable()
        fta = ta.make(samples)
        self._flowables.append(fta)


    def add_pychron_graph(self, gc):
        self._flowables.append(gc)

    def add_image(self, path):
        im = Image(path)
        self._flowables.append(im)

    def add_sample(self):
        pass

    def publish(self):
        doc = SimpleDocTemplate(self.filename,
                                leftMargin=0.5 * inch,
                                rightMargin=0.5 * inch,
                                pagesize=landscape(legal)
#                                pagesize=(20 * inch, 10 * inch)
                                )
        doc.build(self._flowables)
#============= EOF =============================================
