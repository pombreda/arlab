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
from traits.api import HasTraits, Int
from traitsui.api import View, Item
from traitsui.tabular_adapter import TabularAdapter
#============= standard library imports ========================
#============= local library imports  ==========================

class UnknownsAdapter(TabularAdapter):
    columns = [('Run ID', 'record_id')]
    font = 'helvetica 12'
#    record_id_width = Int(50)

class ReferencesAdapter(TabularAdapter):
    columns = [('Run ID', 'record_id')]
    font = 'helvetica 12'
#     font = 'modern 10'
#    record_id_width = Int(50)
#============= EOF =============================================
