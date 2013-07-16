from sqlalchemy import *
from migrate import *

meta = MetaData()
lt = Table('loading_LoadTable', meta,
           Column('name', String(80), primary_key=True),
           Column('create_date', DateTime),
           Column('holder', String(80))
           )

lp = Table('loading_PositionsTable', meta,
            Column('id', Integer, primary_key=True),
            Column('lab_identifier', String(80)),
            Column('position', Integer),
            Column('load_identifier', String(80)),
         )

lpt = Table('meas_PositionsTable', meta,
            Column('id', Integer, primary_key=True),
            Column('load_identifier', String(80)),
            Column('extraction_id', Integer),
            Column('is_degas', Boolean),
            Column('position', Integer),
            )

ht = Table('gen_LoadHolderTable', meta,
         Column('name', String(80), primary_key=True),
         Column('geometry', BLOB)
         )



def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    meta.bind = migrate_engine
    lt.create()
    lpt.create()
    ht.create()
    lp.create()
def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    meta.bind = migrate_engine
    lt.drop()
    lpt.drop()
    ht.drop()
    lp.drop()
