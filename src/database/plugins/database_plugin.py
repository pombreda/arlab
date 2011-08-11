#============= enthought library imports =======================
try:
    from src.database.pychron_database_adapter import PychronDatabaseAdapter
except ImportError, e:
    PychronDatabaseAdapter = None


from apptools.preferences.preference_binding import bind_preference
#============= standard library imports ========================

#============= local library imports  ==========================
from src.envisage.core.core_plugin import CorePlugin

class DatabasePlugin(CorePlugin):
    '''
        G{classtree}
    '''

    id = 'pychron.database'
    name = 'Database'
    def _service_offers_default(self):
        '''
        '''

        database_so = self.service_offer_factory(
                                 protocol = PychronDatabaseAdapter,
                                 #protocol = 'src.database.pychron_database_adapter.PychronDatabaseAdapter',
                                 factory = self._database_factory)
        return [database_so]
    def _database_factory(self):
        '''
        '''
        if PychronDatabaseAdapter is not None:
            prefs = self.application.preferences
            base = 'pychron.database.%s'
            use_db = True if prefs.get(base % 'use_db') == 'True' else False

            adapter = PychronDatabaseAdapter(kind = 'mysql')

            #bind the preferences to the Database adapter
            for key in ['dbname', 'user', 'password', 'host', 'use_db']:
                prefname = base % key
                bind_preference(adapter, key, prefname)

            if use_db:
                adapter.connect()

            return adapter

#============= views ===================================
#============= EOF ====================================
