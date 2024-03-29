#===============================================================================
# Copyright 2011 Jake Ross
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
#=============enthought library imports=======================
from traits.api import  Str, Property, Bool, CStr, Button
from traitsui.api import View, Item, Group, VGroup
#=============standard library imports ========================

#=============local library imports  ==========================
from src.config_loadable import ConfigLoadable


class ViewableDevice(ConfigLoadable):
    '''
    '''

    simulation = Property

    connected = Property(depends_on='simulation')
    com_class = Property

    loaded = Property(depends_on='_loaded')
    _loaded = Bool

    klass = Property
    config_short_path = Property

    last_command = Str
    last_response = Str

    current_scan_value = CStr

    reinitialize_button = Button('Reinitialize')

    display_address = Property
    def _get_display_address(self):

        if hasattr(self._communicator, 'host'):
            return self._communicator.host
        elif hasattr(self, 'port'):
            return self._communicator.port

        return ''

    def _reinitialize(self):
        self.bootstrap()

    def _reinitialize_button_fired(self):
        self._reinitialize()

    def _get_config_short_path(self):
        '''
            config_path is an attribute of 
        '''
        items = self.config_path.split('/')
        return '/'.join(items[6:])

    def _get_loaded(self):
        return 'Yes' if self._loaded else 'No'

    def _get_klass(self):
        return self.__class__.__name__

    def _get_com_class(self):
        return self._communicator.__class__.__name__

    def _get_connected(self):
        return 'Yes' if not self._get_simulation() else 'No'

    def _get_simulation(self):
        '''
        '''
        if self._communicator is not None:
            return self._communicator.simulation
        else:
            return True

    def get_control_group(self):
        pass

    def get_configure_group(self):
        pass

    def current_state_view(self):
        gen_grp = Group(
                     # Item('name'),
                     Item('last_command', style='readonly'),
                     Item('last_response', style='readonly'),
                     Item('current_scan_value', style='readonly'),
                     label='General'
                     )
        v = View(gen_grp)

        return v

    def info_view(self):

        info_grp = VGroup(
                         Item('reinitialize_button', show_label=False),
                         Item('name', style='readonly'),
                         Item('display_address', style='readonly'),
                         Item('klass', style='readonly', label='Class'),
                         Item('connected', style='readonly'),
                         Item('com_class', style='readonly', label='Com. Class'),
                         Item('config_short_path', style='readonly'),
                         Item('loaded', style='readonly'),
                         label='Info',
                         )

        v = View(
                 Group(
                       info_grp,

                       layout='tabbed'
                       )
                 )

        cg = self.get_control_group()

        config_group = self.get_configure_group()
        if cg:
            cg.label = 'Control'
            v.content.content.insert(0, cg)

        if config_group:
            config_group.label = 'Configure'
            v.content.content.insert(1, config_group)
        return v

    def traits_view(self):
        v = View()
        cg = self.get_control_group()
        if cg:
            v.content.content.append(cg)
        return v


#============= EOF =====================================
