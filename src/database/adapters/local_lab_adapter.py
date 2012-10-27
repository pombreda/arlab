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
from traits.api import HasTraits
from traitsui.api import View, Item, TableEditor
from src.database.core.database_adapter import DatabaseAdapter
from src.database.orms.local_lab_orm import LabTable
from src.database.core.functions import add
from sqlalchemy.schema import MetaData, Table, Column
from sqlalchemy.types import Integer, BLOB, DateTime, String
import os

#============= standard library imports ========================
#============= local library imports  ==========================

class LocalLabAdapter(DatabaseAdapter):
    kind = 'sqlite'
    def build_database(self):
        self.connect(test=False)
        if not os.path.isfile(self.name):
            sess = self.get_session()
            meta = MetaData()
            bt = Table('LabTable', meta,
                        Column('id', Integer, primary_key=True),
                        Column('labnumber', Integer),
                        Column('aliquot', Integer),
                        Column('collection_path', String(200)),
                        Column('repository_path', String(200)),
                        Column('create_date', DateTime))
            bt.create(sess.bind)

    @add
    def add_analysis(self, **kw):
        l = LabTable(**kw)
        return l, True

if __name__ == '__main__':
    lb = LocalLabAdapter(name='/Users/ross/Sandbox/foo.db')
    lb.build_database()
#============= EOF =============================================