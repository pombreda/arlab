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
from traits.api import Instance, Button

#============= standard library imports ========================
#============= local library imports  ==========================
from src.database.adapters.massspec_database_adapter import MassSpecDatabaseAdapter
from src.database.database_connection_spec import DBConnectionSpec
from src.loggable import Loggable
from src.processing.analyses.mass_spec_analysis import MassSpecAnalysis


class MassSpecRecaller(Loggable):
    dbconn_spec = Instance(DBConnectionSpec, ())
    connect_button = Button('Connect')
    db = Instance(MassSpecDatabaseAdapter, ())

    def _dbconn_spec_default(self):
    #        return DBConnectionSpec(database='massspecdata_minnabluff',
    #                                username='root',
    #                                password='Argon',
    #                                host='localhost'
    #                                )
    #    return DBConnectionSpec(database='massspecdata',
    #                            username='root',
    #                            password='DBArgon',
    #                            host='129.138.12.160')

        return DBConnectionSpec(database='massspecdata_minnabluff',
                                username='root',
                                password='Argon',
                                host='localhost')

    def _connect_button_fired(self):
        self.connect()

    def connect(self):
        self.db.name = self.dbconn_spec.database
        self.db.username = self.dbconn_spec.username
        self.db.password = self.dbconn_spec.password
        self.db.host = self.dbconn_spec.host
        self.db.kind = 'mysql'
        return self.db.connect()

    def find_analysis(self, labnumber, aliquot, step):
        db = self.db
        with db.session_ctx():
            dbrec = db.get_analysis(labnumber, aliquot, step)
            rec = MassSpecAnalysis()
            rec.sync(dbrec)

            return rec


#============= EOF =============================================
