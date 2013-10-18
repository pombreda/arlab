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
from traits.api import HasTraits
from traitsui.api import View, Item
from pyface.tasks.action.task_action import TaskAction
from pyface.image_resource import ImageResource
from src.paths import paths
#============= standard library imports ========================
#============= local library imports  ==========================

class AddTextBoxAction(TaskAction):
    method = 'add_text_box'
    name = 'Annotate'
    image = ImageResource(name='annotate.png',
                          search_path=paths.icon_search_path
    )


class SaveFigureAction(TaskAction):
    method = 'save_figure'
    name = 'Save Figure'
    image = ImageResource(name='database_save.png',
                          search_path=paths.icon_search_path
    )


class OpenFigureAction(TaskAction):
    method = 'open_figure'
    name = 'Open Figure'
    image = ImageResource(name='page_white_database.png',
                          search_path=paths.icon_search_path
    )


class NewIdeogramAction(TaskAction):
    name = 'New Ideogram'
    method = 'tb_new_ideogram'
    image = ImageResource(name='ideo.png',
                          search_path=paths.icon_search_path
    )


class AppendIdeogramAction(TaskAction):
    name = 'Append Ideogram'
    method = 'append_ideogram'
    tooltip = '''Add selected analyses to current ideogram.
If no analyses selected add all from the selected sample'''

    image = ImageResource(name='ideo_add.png',
                          search_path=paths.icon_search_path
    )


class NewSpectrumAction(TaskAction):
    name = 'New Spectrum'
    method = 'tb_new_spectrum'
    image = ImageResource(name='chart_curve.png',
                          search_path=paths.icon_search_path
    )


class AppendSpectrumAction(TaskAction):
    name = 'Append Spectrum'
    method = 'append_spectrum'
    tooltip = '''Add selected analyses to current spectrum.
If no analyses selected add all from the selected sample'''

    image = ImageResource(name='chart_curve_add.png',
                          search_path=paths.icon_search_path
    )

#============= EOF =============================================
