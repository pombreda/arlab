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
from traits.api import HasTraits, Any
from traitsui.api import View, Item, TableEditor
from src.pyscripts.pyscript import PyScript, verbose_skip
#============= standard library imports ========================
#============= local library imports  ==========================

ELPROTOCOL = 'src.extraction_line.extraction_line_manager.ExtractionLineManager'

class ValvePyScript(PyScript):
    runner = Any
    def _runner_changed(self):
        self.runner.scripts.append(self)

    def get_script_commands(self):
        cmds = [('open', '_m_open'), 'close',
               'is_open', 'is_closed']
        return cmds

    def gosub(self, *args, **kw):
        kw['runner'] = self.runner
        super(ValvePyScript, self).gosub(*args, **kw)

    @verbose_skip
    def _m_open(self, name=None, description=''):

        if description is None:
            description = '---'

        self.info('opening {} ({})'.format(name, description))

        self._manager_action([('open_valve', (name,), dict(
                                                      mode='script',
                                                      description=description
                                                      ))], protocol=ELPROTOCOL)

    @verbose_skip
    def close(self, name=None, description=''):

        if description is None:
            description = '---'

        self.info('closing {} ({})'.format(name, description))
        self._manager_action([('close_valve', (name,), dict(
                                                      mode='script',
                                                      description=description
                                                      ))], protocol=ELPROTOCOL)

    @verbose_skip
    def is_open(self, name=None, description=''):
        self.info('is {} ({}) open?'.format(name, description))
        result = self._get_valve_state(name, description)
        if result:
            return result[0] == True

    @verbose_skip
    def is_closed(self, name=None, description=''):
        self.info('is {} ({}) closed?'.format(name, description))
        result = self._get_valve_state(name, description)
        if result:
            return result[0] == False

    def _get_valve_state(self, name, description):
        return self._manager_action([('open_valve', (name,), dict(
                                                      mode='script',
                                                      description=description
                                                      ))], protocol=ELPROTOCOL)

#============= EOF =============================================