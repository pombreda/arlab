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



from sqlalchemy import *
from migrate import *


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
#    meta = MetaData(bind=migrate_engine)
#    t = Table('ControllerTable', meta, autoload=True)
#    s = Column('script', String(40))
#    sp = Column('setpoint', Float)
#    d = Column('duration', Float)
#
#    s.create(t)
#    sp.create(t)
#    d.create(t)
    pass

def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
#    meta = MetaData(bind=migrate_engine)
#    t = Table('ControllerTable', meta, autoload=True)
#    t.c.duration.drop()
#    t.c.script.drop()
#    t.c.setpoint.drop()
    pass
