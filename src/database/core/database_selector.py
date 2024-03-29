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
from traits.api import Button, List, Any, Dict, Bool, Int, Enum, Event, \
    on_trait_change, Str, Instance
from traitsui.api import View, Item, \
    HGroup, spring, ListEditor, InstanceEditor, Handler, VGroup
from pyface.timer.do_later import do_later
#============= standard library imports ========================
#============= local library imports  ==========================
from src.database.core.database_adapter import DatabaseAdapter

from src.graph.time_series_graph import TimeSeriesGraph

from src.database.core.query import Query, compile_query
from src.viewable import Viewable

from traits.api import HasTraits
from src.traits_editors.tabular_editor import myTabularEditor
# from src.database.core.base_results_adapter import BaseResultsAdapter
from src.traits_editors.custom_label_editor import CustomLabel
from traitsui.tabular_adapter import TabularAdapter

class BaseTabularAdapter(TabularAdapter):
    columns = [('ID', 'record_id'),
               ('Timestamp', 'timestamp')
               ]

class ColumnSorterMixin(HasTraits):
    _sort_field = None
    _reverse_sort = False
    column_clicked = Any

    def _column_clicked_changed(self, event):
        values = event.editor.value

        fields = [name for _, name in event.editor.adapter.columns]
        field = fields[event.column]
        self._reverse_sort = not self._reverse_sort

        self._sort_columns(values, field)

    def _sort_columns(self, values, field=None):
        # get the field to sort on
        if field is None:
            field = self._sort_field
            if field is None:
                return

        values.sort(key=lambda x: getattr(x, field),
                    reverse=self._reverse_sort)
        self._sort_field = field


class SelectorHandler(Handler):
    def init(self, info):
        pass
# #        if info.initialized:
#        import wx
#        for control in info.ui.control.GetChildren()[0].GetChildren():
#            if isinstance(control, wx.Button):
#                if control.GetLabel() == 'Search':
#                    control.Bind(wx.EVT_KEY_DOWN, info.object.onKeyDown)
#                    control.SetFocus()
#                    info.ui.control.SetDefaultItem(control)
#                    break

class DatabaseSelector(Viewable, ColumnSorterMixin):
    records = List

    search = Button
#    open_button = Button
#    open_button_label = 'Open'

    db = Instance(DatabaseAdapter)
    tabular_adapter = BaseTabularAdapter
    dbstring = Str
    title = ''

    dclicked = Any
    selected = Any
    scroll_to_row = Int
#    activated = Any
    update = Event
    selected_row = Any

    wx = 0.4
    wy = 0.1
    opened_windows = Dict

    query_table = None
    record_klass = None
    query_klass = None

    omit_bogus = Bool(True)

    limit = Int(200, enter_set=True, auto_set=False)
    date_str = 'Run Date'

    multi_select_graph = Bool(False)
    multi_graphable = Bool(False)

    queries = List(Query)
    lookup = Dict
    style = Enum('normal', 'panel', 'simple', 'single')

    verbose = False
#    def onKeyDown(self, evt):
#        import wx
#        print evt
#        if evt.GetKeyCode() == wx.WXK_RETURN:
#            print 'ffoasdf'
#        evt.Skip()


    def __init__(self, *args, **kw):
        super(DatabaseSelector, self).__init__(*args, **kw)
        self._load_hook()

#    def _activated_changed(self):
#        print self.activated
#        if self.activated:
#            print self.activated.rid
#
#    def _selected_changed(self):
#        print self.selected
    def load_records(self, dbs, load=True, append=False):
        if not append:
            self.records = []

        self._load_records(dbs)
#        self._sort_columns(self.records)

        self.scroll_to_row = len(self.records)

    def query_factory(self, **kw):
        return self._query_factory(**kw)

    def add_query(self, parent_query, parameter, criterion):
        q = self._query_factory(
                                parent_parameters=parent_query.parent_parameters + [parameter],
                                parent_criterions=parent_query.parent_criterions + [criterion])
        self.queries.append(q)
        parent_query.on_trait_change(q._update_parent_parameter, 'parameter')
        parent_query.on_trait_change(q._update_parent_criterion, 'criterion')

    def remove_query(self, q):
        self.queries.remove(q)

    def load_recent(self):
        dbs = self._get_recent()
        self.load_records(dbs, load=False)

    def load_last(self, n=200):
        dbs, _stmt = self._get_selector_records(limit=n)
        self.load_records(dbs, load=False)

#    def execute_query(self, filter_str=None):
    def execute_query(self, queries=None, load=True):
        dbs = self._execute_query(queries)
        self.load_records(dbs, load=load)

    def get_recent(self):
        return self._get_recent()
#===============================================================================
# private
#===============================================================================
    def _get_recent(self):
        criterion = 'this month'
        q = self.queries[0]
        q.parameter = self.date_str
        q.comparator = '<'
        q.trait_set(criterion=criterion, trait_change_notify=False)

        return self._execute_query(queries=[q])

    def _assemble_query(self, q, queries, lookup):
        joined = []
        for qi in queries:
            if lookup.has_key(qi.parameter):
                tabs, attr = lookup[qi.parameter]
                for tab in tabs:
                    if not tab in joined:
                        joined.append(tab)
                        q = q.join(tab)

                q = qi.assemble_filter(q, attr)

        return q

    def _execute_query(self, queries=None):
        if queries is None:
            queries = self.queries

        # @todo: only get displayed columns
        dbs, query_str = self._get_selector_records(limit=self.limit,
                                                    queries=queries
                                                    )

        if not self.verbose:
            query_str = str(query_str)
            query_str = query_str.split('WHERE')[-1]
            query_str = query_str.split('ORDER BY')[0]

        self.info('query {} returned {} records'.format(query_str,
                                len(dbs) if dbs else 0))
        return dbs

    def _load_records(self, records):
        if records:
            '''
                using a IsotopeRecordView is significantly faster than loading a IsotopeRecord directly
            '''
            rs = [self._record_view_factory(di) for di in records]
            rs = [ri for ri in rs if ri]
            self.records.extend(rs)

#    def _changed(self, new):
#        db = self.db
#        db.commit()

    def _record_closed(self, obj, name, old, new):
        sid = obj.record_id
        if sid in self.opened_windows:
            self.opened_windows.pop(sid)
        obj.on_trait_change(self._record_closed, 'close_event', remove=True)
#        obj.on_trait_change(self._changed, '_changed', remove=True)

    def open_record(self, records):
        if not isinstance(records, (list, tuple)):
            records = [records]

        self.debug('open record')
        self._open_selected(records)

    def _open_selected(self, records=None):
        self.debug('open selected')
        if records is None:
            records = self.selected

        if records is not None:
            if isinstance(records, (list, tuple)):
                records = records[0]
            self._open_individual(records)

        self.debug('opened')

    def _open_individual(self, si):
        si = self._record_factory(si)

        if isinstance(si, str):
            si = self._record_factory(si)
        else:
            si.selector = self

        if not si.initialize():
            return

        sid = si.record_id
        try:
            si.load_graph()
            si.window_x = self.wx
            si.window_y = self.wy
            def do(si, sid):
                self.debug('{}'.format(si))
                info = si.edit_traits()
                self._open_window(sid, info)

            self.debug('do later open')
            do_later(do, si, sid)

        except Exception, e:
            import traceback
            traceback.print_exc()
            self.warning(e)

    def _record_view_factory(self, dbrecord):
        if hasattr(self, 'record_view_klass'):
            d = self.record_view_klass()
            if d.create(dbrecord):
                return d
        else:
            return self.record_klass(_dbrecord=dbrecord)

    def _open_window(self, wid, ui):
        self.opened_windows[wid] = ui
        self._update_windowxy()

        if self.db.application is not None:
            self.db.application.uis.append(ui)

    def _update_windowxy(self):
        self.wx += 0.005
        self.wy += 0.03

        if self.wy > 0.65:
            self.wx = 0.4
            self.wy = 0.1

    def _get_selector_records(self):
        pass

    def _get_records(self, q, queries, limit, timestamp='timestamp'):
        if queries:
            q = self._assemble_query(q, queries, self.lookup)

        tattr = getattr(self.query_table, timestamp)
        q = q.order_by(tattr.desc())
        if limit:
            q = q.limit(limit)

        q = q.from_self()
        q = q.order_by(tattr.asc())
        records = q.all()

        return records, compile_query(q)

    def _load_hook(self):
        pass

#===============================================================================
# handlers
#===============================================================================
    def _dclicked_changed(self):
        self.debug('dclicked changed {}'.format(self.dclicked))
        if self.dclicked:
            self._open_selected()

    def _open_button_fired(self):
        self.debug('open button fired')
        self._open_selected()

    def _search_fired(self):
        self.execute_query(load=False)

    def _limit_changed(self):
        self.execute_query(load=False)

    @on_trait_change('db.[name,host]')
    def _dbstring_change(self):
        if self.db.kind == 'mysql':
            self.dbstring = 'Database: {} at {}'.format(self.db.name, self.db.host)
        else:
            self.dbstring = 'Database: {}'.format(self.db.name)


    def _selected_changed(self):
        if self.selected:
            sel = self.selected
            if self.style != 'single':
                sel = sel[0]
            self.selected_row = self.records.index(sel)
            self.update = True
#===============================================================================
# factories
#===============================================================================
    def _query_factory(self, removable=True, **kw):
        q = self.query_klass(selector=self,
                  removable=removable,
                  date_str=self.date_str,
                  )

        q.trait_set(trait_change_notify=False, **kw)
        return q

    def _record_factory(self, di):
        di.on_trait_change(self._record_closed, 'close_event')
        return di
#===============================================================================
# views
#===============================================================================
    def _get_button_grp(self):
        return HGroup(spring, Item('search', show_label=False), defined_when='style=="normal"')

    def panel_view(self):
        v = self._view_factory()
        return v

    def traits_view(self):
        v = self._view_factory()
        v.title = self.title
        v.width = 600
        v.height = 650
        v.x = 0.1
        v.y = 0.1

        return v

    def _view_factory(self):
        editor = myTabularEditor(adapter=self.tabular_adapter(),
                               dclicked='object.dclicked',
                               selected='object.selected',
                               selected_row='object.selected_row',
                               update='update',
#                               auto_update=True,
                               column_clicked='object.column_clicked',
                               editable=False,
                               multi_select=not self.style == 'single',

                               )

        button_grp = self._get_button_grp()
        qgrp = Item('queries', show_label=False,
                    style='custom',
                    height=0.25,
                    editor=ListEditor(mutable=False,
                                      style='custom',
                                      editor=InstanceEditor()),
                     defined_when='style in ["normal","panel"]')
        v = View(
#                 HGroup(Item('multi_select_graph',
#                             defined_when='multi_graphable'
#                             ),
#                             spring, Item('limit')),
                VGroup(
                       CustomLabel('dbstring', color='red'),
                       Item('records',
                          style='custom',
                          editor=editor,
                          show_label=False,
                          height=0.75,
                          width=600,
                          ),

                          qgrp,
                          button_grp,
                    ),
                 resizable=True,
                 handler=SelectorHandler
                 )

        if self.style == 'single':
            v.buttons = ['OK', 'Cancel']
        return v

#===============================================================================
# defaults
#===============================================================================
    def _queries_default(self):
        return [self._query_factory(removable=False)]


#============= EOF =============================================
#        if criteria is None:
#            criteria = self.criteria
#        self.criteria = criteria
#
#        db = self.db
#        if db is not None:
#
#            s = self._get_filter_str(param, comp, criteria)
#            if s is None:
#                return

#            kw = dict(filter_str=s,
#                      limit=self.limit,
#                      order=self._get_order()
#                      )
#            table, _ = param.split('.')
#            if not table == self.query_table.__tablename__:
#                kw['join_table'] = table

#            elif self.join_table:
#                kw['join_table'] = self.join_table
#                kw['filter_str'] = s + ' and {}.{}=="{}"'.format(self.join_table,
#                                                               self.join_table_col,
#                                                                        self.join_table_parameter
#                                                                        )
