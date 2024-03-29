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



#============= enthought library imports =======================

#============= standard library imports ========================

#============= local library imports  ==========================
from src.lasers.plugins.laser_plugin import LaserPlugin

class SynradCO2Plugin(LaserPlugin):
    '''
    '''
    id = 'pychron.synrad.co2'
    MANAGERS = 'pychron.hardware.managers'

    name = 'synrad_co2_manager'
    klass = ('src.managers.laser_managers.synrad_co2_manager', 'SynradCO2Manager')

