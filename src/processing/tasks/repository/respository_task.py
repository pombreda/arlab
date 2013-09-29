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
from traits.api import HasTraits, Any, on_trait_change, Bool, DelegatesTo
from src.processing.tasks.analysis_edit.analysis_edit_task import AnalysisEditTask
from pyface.tasks.task_layout import TaskLayout, Tabbed, PaneItem, HSplitter
from enaml.widgets.splitter import Splitter
from src.processing.tasks.browser.browser_task import BaseBrowserTask
from src.processing.tasks.browser.panes import BrowserPane
from src.processing.tasks.repository.panes import RepositoryPane
from src.processing.repository.geochron_repo import GeochronRepository
from src.processing.repository.igsn import IGSN
#============= standard library imports ========================
#============= local library imports  ==========================

class RepositoryTask(AnalysisEditTask, BaseBrowserTask):
    name = 'Repository'
    repository = Any
    igsn = Any

    igsn_enabled = DelegatesTo('igsn', prefix='enabled')
    repo_enabled = DelegatesTo('repository', prefix='enabled')

    def _selected_project_changed(self, new):
        project = ''
        if new:
            project = new.name

        self.igsn.project = project
        BaseBrowserTask._selected_project_changed(self, new)

    def _selected_sample_changed(self, new):
        sample = ''
        if new:
            sample = new[0].name
        self.igsn.sample = sample

    def _repository_default(self):
        return GeochronRepository()

    def _igsn_default(self):
        return IGSN()

    def create_central_pane(self):
        return RepositoryPane(model=self)

    def create_dock_panes(self):
        ps = AnalysisEditTask.create_dock_panes(self)
        ps.extend([BrowserPane(model=self)])
        return ps

    def _save_to_db(self):
        '''
            save the sample igsn to the database
        '''
        db = self.manager.db
        with db.session_ctx():
            s = self.selected_sample
            p = self.selected_project
            dbsample = db.get_sample(s.name, project=p.name)
            if dbsample is not None:
                dbsample.igsn = s.igsn
            else:
                msg = 'Sample: {}, Project: {} \
                not found in database'.format(s.name, p.name)
                self.warning_dialog(msg)

        self.info('Sample: {}, Project: {}. IGSN set to {}'.format(s.name,
                                                                   p.name,
                                                                   s.igsn))

#===============================================================================
# handlers
#===============================================================================
    @on_trait_change('igsn:new_igsn')
    def _new_igsn(self, new):
        '''
            associate the new igsn with the current sample and save to the 
            database
        '''
        sample = self.igsn.sample
        project = self.igsn.project
        self.debug('Retrieved new IGSN:{} for project: {} sample: {}'.format(new, sample, project))

        self.selected_sample.igsn = new
        self._save_to_db()

#     @on_trait_change('igsn:[sample, username, password]')
#     def _update_igsn(self):
#         self.igsn_enabled = all([getattr(self.igsn, a)
#                                  for a in ('sample', 'username', 'password')])
#
#     @on_trait_change('repository:enabl')
#     def _update_repo(self):
#         self.repo_enabled = all([getattr(self.repository, a)
#                                  for a in ('username', 'password')])
#===============================================================================
# defaults
#===============================================================================
    def _default_layout_default(self):
        return TaskLayout(id='pychron.repository',
                          left=HSplitter(
                                         PaneItem('pychron.browser'),
                                         )
#                           left=HSplitter(

#                                     PaneItem('pychron.browser'),
#                                     Splitter(
#                                          Tabbed(
#                                                 PaneItem('pychron.analysis_edit.unknowns'),
# #                                                 PaneItem('pychron.processing.figures.plotter_options')
#                                                 ),
# #                                          Tabbed(
# #                                                 PaneItem('pychron.analysis_edit.controls'),
# #                                                 PaneItem('pychron.processing.editor'),
# #                                                 ),
#                                          orientation='vertical'
#                                          )
#                                     ),

                          )
#============= EOF =============================================
