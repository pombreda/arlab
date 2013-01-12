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
from traits.api import HasTraits, List, Property, cached_property
#============= standard library imports ========================
from numpy import array
#============= local library imports  ==========================

class Mean(HasTraits):
    analyses = List
    nanalyses = Property(depends_on='analyses:[status,temp_status]')
    age = Property(depends_on='analyses:[status,temp_status]')
    identifier = Property

    def _calculate_mean(self, attr):
        vs = array([getattr(ai, attr) for ai in self.analyses
                    if ai.status == 0 and ai.temp_status == 0])
        return vs.mean()

    @cached_property
    def _get_identifier(self):
        return self.analyses[0].labnumber

    @cached_property
    def _get_age(self):
        return self._calculate_mean('age')

    @cached_property
    def _get_nanalyses(self):

        return len([ai for ai in self.analyses
                    if ai.status == 0 and ai.temp_status == 0])

class AnalysisRatioMean(Mean):
    Ar40_39 = Property
    Ar37_39 = Property
    Ar36_39 = Property
    kca = Property
    kcl = Property

    def _get_Ar40_39(self):
        return self._calculate_mean('Ar40_39')
#        return self._calculate_mean('rad40') / self._calculate_mean('k39')

    def _get_Ar37_39(self):
        return self._calculate_mean('Ar37_39')
#        return self._calculate_mean('Ar37') / self._calculate_mean('Ar39')

    def _get_Ar36_39(self):
        return self._calculate_mean('Ar36_39')
#        return self._calculate_mean('Ar36') / self._calculate_mean('Ar39')

    def _get_kca(self):
        return self._calculate_mean('kca')

    def _get_kcl(self):
        return self._calculate_mean('kcl')


class AnalysisIntensityMean(Mean):
    Ar40 = Property
    Ar39 = Property
    Ar38 = Property
    Ar37 = Property
    Ar36 = Property

    def _get_Ar40(self):
        return self._calculate_mean('Ar40')
    def _get_Ar39(self):
        return self._calculate_mean('Ar39')
    def _get_Ar38(self):
        return self._calculate_mean('Ar38')
    def _get_Ar37(self):
        return self._calculate_mean('Ar37')
    def _get_Ar36(self):
        return self._calculate_mean('Ar36')

#============= EOF =============================================