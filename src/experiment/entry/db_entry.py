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
#============= standard library imports ========================
#============= local library imports  ==========================
from src.viewable import Viewable

class DBEntry(Viewable):
    db = Any
    def _db_default(self):
        #=======================================================================
        # debug
        #=======================================================================
        from src.database.adapters.isotope_adapter import IsotopeAdapter
        db = IsotopeAdapter(name='isotopedb_dev',
                          username='root',
                          host='localhost',
                          kind='mysql',
                          password='Argon',
                          save_username='root_debug'
                          )
        db.connect()
        return db
        #=======================================================================
        # 
        #=======================================================================
#============= EOF =============================================
