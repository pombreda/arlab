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
from traits.api import HasTraits, Long, Str, Any, Instance, Date, Time, \
    Button
from traitsui.api import View, Item, Group, HGroup, VGroup, spring
#============= standard library imports ========================
import os
#============= local library imports  ==========================
from src.managers.data_managers.csv_data_manager import CSVDataManager
from src.graph.graph import Graph
from src.managers.data_managers.h5_data_manager import H5DataManager


class BaseDBResult(HasTraits):
    rid = Long
    _db_result = Any


class DBResult(BaseDBResult):
    title = Str
    summary = Str
    graph = Instance(Graph)
    rundate = Date
    runtime = Str#('%H:%M:%s')

    directory = Str
    filename = Str
    window_x = 0.1
    window_y = 0.1
    window_width = None
    window_height = None

    title_str = Str('Base')
    data_manager = None

    _loadable = True

    export_button = Button('Export CSV')
    exportable = True
    resizable = True
    def _export_button_fired(self):
        self._export_csv()

    def _export_csv(self):
        p = os.path.join(self.directory, self.filename)
        if os.path.isfile(p) and self.graph is not None:
            self.graph.export_data(plotid=0)

    def initialize(self):
        return self.isloadable()

    def load(self):
        dbr = self._db_result
        if dbr is not None:
            self.rid = dbr.id
            self.rundate = dbr.rundate
            self.runtime = dbr.runtime.strftime('%H:%M:%S')
            p = dbr.path
            if p is not None:
                self.directory = p.root if p.root else ''
                self.filename = p.filename if p.filename else ''

            self.title = '{} {}'.format(self.title_str, self.rid)
            self._load_hook(dbr)
        elif self.directory is not None and self.filename is not None:
            self._load_hook('')

    def _load_hook(self, dbr):
        pass

    def isloadable(self):
        dm = self._data_manager_factory()
        try:
            self._loadable = dm.open_data(self._get_path())
        except Exception, e:
            self._loadable = False
        finally:
            dm.close()
        return self._loadable

    def _get_path(self):
        return os.path.join(self.directory, self.filename)

    def _data_manager_factory(self):
#        dm = self.data_manager
#        if dm is None:
        data = self._get_path()
        _, ext = os.path.splitext(self.filename)

        if ext in ['.h5', '.hdf5']:
            dm = H5DataManager()
            if os.path.isfile(data):
                #is it wise to actually open the file now?
#                    self._loadable = dm.open_data(data)
                self._loadable = True

        else:
            self._loadable = False
            dm = CSVDataManager()

        return dm

    def load_graph(self):
        pass

    def _graph_factory(self, klass=None):

        if klass is None:
            klass = Graph
        g = klass(container_dict=dict(padding=10),
                  width=500,
                  height=300
                  )
        return g

    def _get_additional_tabs(self):
        return []

    def _get_graph_item(self):
        g = Item('graph',
                    show_label=False,
                    style='custom',
                    height=1.0)
        return g
    def _get_info_grp(self):
        return VGroup(
                          VGroup(Item('rid', style='readonly', label='ID'),
                                    Item('rundate', style='readonly', label='Run Date'),
                                    Item('runtime', style='readonly', label='Run Time'),
                                    Item('directory', style='readonly'),
                                    Item('filename', style='readonly')),
                            VGroup(Item('summary',
                                    show_label=False,
                                    style='readonly',
                                    visible_when='object.summary'
                                    )),
                            HGroup(spring,
                              Item('export_button',
                                            show_label=False),
                       visible_when='object.exportable'
                       ),
#                    label='Info',
                    )

    def traits_view(self):

        grps = Group(self._get_info_grp())
#        grps = Group()

        agrps = self._get_additional_tabs()
        g = self._get_graph_item()
        if g is not None:
            agrps.append(g)

        for i, ai in enumerate(agrps):
            grps.content.insert(i, ai)

        return self._view_factory(grps)

    def _view_factory(self, grps):
        v = View(grps,
                    resizable=self.resizable,
                    x=self.window_x,
                    y=self.window_y,
                    title=self.title
                    )
        if self.window_width:
            v.width = self.window_width
        if self.window_height:
            v.height = self.window_height
        return v

class RIDDBResult(DBResult):
    runid = Str
#============= EOF =============================================
