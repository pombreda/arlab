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
from traits.api import HasTraits, Any, Instance
from src.displays.rich_text_display import RichTextDisplay
from pyface.timer.do_later import do_later
#============= standard library imports ========================
#============= local library imports  ==========================

class Summary(HasTraits):
    display = Instance(RichTextDisplay)
    record = Any

    @classmethod
    def calc_percent_error(cls, v, e):
        if v:
            sigpee = '{:0.2f}%'.format(abs(e / v * 100))
        else:
            sigpee = 'Inf'
        return sigpee

    def __init__(self, *args, **kw):
        super(Summary, self).__init__(*args, **kw)
        self.refresh()

    def refresh(self):
        self.build_summary()

    def build_summary(self, *args, **kw):
        def do():
            d = self.display
            d.freeze()

            #double clear for safety 
            d.clear(gui=False)
            d.clear(gui=False)

            self._build_summary(*args, **kw)
            d.thaw()

        do_later(do)

    def add_text(self, *args, **kw):
        kw['gui'] = False
        self.display.add_text(*args, **kw)

    def _build_summary(self, *args, **kw):
        pass

    def _display_default(self):
        return RichTextDisplay(default_size=12,
                               width=700,
                               selectable=True,
                               default_color='black',
                               scroll_to_bottom=False,
                               font_name='courier'
#                               font_name='Bitstream Vera Sans Mono'
#                               font_name='monospace'
                               )

#============= EOF =============================================
