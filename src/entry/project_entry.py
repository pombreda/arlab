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
from traits.api import Str
from traitsui.api import View, Item

#============= standard library imports ========================
#============= local library imports  ==========================
from src.database.isotope_database_manager import IsotopeDatabaseManager


class ProjectEntry(IsotopeDatabaseManager):
    project = Str

    def edit_project(self, proj):
        self.information_dialog('Editing project not currently implemented')
        #db=self.db
        #with db.session_ctx():
        #    dbproj=db.get_project(proj)


    def add_project(self):
        self.info('adding project')
        while 1:
            info = self.edit_traits()
            if info.result:
                db = self.db
                name = self.project
                with db.session_ctx():
                    if not db.get_project(name):
                        db.add_project(name)
                    else:
                        self.warning_dialog('{} already exists'.format(name))
            else:
                break


    def traits_view(self):
        v = View(Item('project'),
                 kind='modal',
                 resizable=True, title='New Sample',
                 buttons=['OK', 'Cancel']
        )
        return v

#============= EOF =============================================
