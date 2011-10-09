'''
Copyright 2011 Jake Ross

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
#============= enthought library imports =======================
from envisage.ui.action.api import Action#, Group, Menu, ToolBar
from envisage.ui.workbench.api import WorkbenchActionSet
#============= standard library imports ========================

#============= local library imports  ==========================
class SVNActionSet(WorkbenchActionSet):
    '''
        G{classtree}
    '''
    id = 'pychron.svn.action_set'
    actions = [
               Action(name='Update Software',
                      path='MenuBar/Help',
                      class_name='src.svn.plugins.svn_actions:UpdateToHeadAction'),


              ]
#============= EOF ====================================