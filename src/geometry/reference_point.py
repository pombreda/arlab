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
from traits.api import HasTraits, Float, String
from traitsui.api import View, HGroup
#============= standard library imports ========================
#============= local library imports  ==========================
from src.traits_editors.custom_label_editor import CustomLabel

HELP_TAG = '''Enter the x, y for this point {:0.3f},{:0.3f}
in data space i.e mm
'''

class ReferencePoint(HasTraits):
    x = Float
    y = Float
    help_tag = String(HELP_TAG)
    def __init__(self, pt, *args, **kw):
        self.help_tag = HELP_TAG.format(*pt)
        super(ReferencePoint, self).__init__(*args, **kw)

    def traits_view(self):
        v = View(
                 CustomLabel('help_tag',
                             top_padding=10,
                             left_padding=10,
#                             align='center',
                             color='maroon'),
                 HGroup('x', 'y'),
                 buttons=['OK', 'Cancel'],
                 kind='modal',
                 title='Reference Point'
                 )
        return v
#============= EOF =============================================
