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
from traits.api import HasTraits, Str, Password
from traitsui.api import View, Item, VGroup, VFold
#============= standard library imports ========================
#============= local library imports  ==========================

class DBConnectionSpec(HasTraits):
    database = Str('massspecdata_import')
    username = Str('root')
    password = Password('Argon')
#    host = Str('129.138.12.131')
    host = Str('localhost')
    def make_url(self):
        return '{}:{}@{}/{}'.format(self.username, self.password, self.host, self.database)

    def make_connection_dict(self):
        return dict(name=self.database, username=self.username, password=self.password, host=self.host)

    def traits_view(self):
        return View(VGroup(
                           Item('host'),
                           Item('database'),
                           Item('username'),
                           Item('password'),
                           )
                    )

#============= EOF =============================================
