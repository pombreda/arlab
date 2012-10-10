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
from traits.api import HasTraits
from traitsui.api import View, Item, TableEditor
#============= standard library imports ========================
#============= local library imports  ==========================
from src.experiment.processing.export.base import Exporter
import csv
class CSVExporter(Exporter):
    def _export(self, p):
        fp = open(p, 'w')
        writer = csv.writer(fp, delimiter='\t')
        analyses = self.figure.analyses
        header = self.header
        writer.writerow(header)
        for ai in analyses:

            row = self._make_raw_row(ai)
            writer.writerow(row)

            blank = ['', ] * len(header)
            writer.writerow(blank)
        fp.close()



#============= EOF =============================================
