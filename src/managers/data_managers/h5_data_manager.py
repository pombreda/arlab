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
from traits.api import Any
#============= standard library imports ========================
from tables import openFile, Filters
#============= local library imports  ==========================
from data_manager import DataManager
from table_descriptions import table_description_factory
import os
import weakref


def get_table(name, group, frame):
    try:
        if isinstance(group, str):
            group = getattr(frame.root, group)
        return getattr(group, name)
    except AttributeError:
        try:
            return getattr(frame.root, name)
        except AttributeError:
            pass


class TableCTX(object):
    def __init__(self, p, t, g, complevel, mode):
        self._file = openFile(p, mode,
                              filters=Filters(complevel=complevel))
        self._t = t
        self._g = g

    def __enter__(self):
        return get_table(self._t, self._g, self._file)

    def __exit__(self, *args):
        self._file.close()
        del self._file


class FileCTX(object):
    def __init__(self, parent, p, m, complevel):
        self._file = openFile(p, m,
                              filters=Filters(complevel=complevel))
        self._parent = parent
        self._parent._frame = self._file

    def __enter__(self):
        return self._file

    def __exit__(self, *args, **kw):
    #         self._file.flush()
        self._parent.close_file()
        self._file.close()

        del self._file
        del self._parent


class H5DataManager(DataManager):
    '''
    '''
    #    _extension = 'h5'
    _extension = 'hdf5'
    repository = Any
    workspace_root = None
    compression_level = 5

    def set_group_attribute(self, group, key, value):
        f = self._frame

        if isinstance(group, str):
            group = getattr(f, group)

        setattr(group._v_attrs, key, value)

    #        print group._v_attrs[]
    #        group.flush()
    #    def set_table_attribute(self, key, value, table):
    #        '''
    #
    #        '''
    #        _df, table = self._get_parent(table)
    #        setattr(table.attrs, key, value)
    #        table.flush()

    def record(self, values, table):
        '''

        '''
        _df, ptable = self._get_parent(table)
        nr = ptable.row
        for key in values:
            nr.__setitem__(key, values[key])

        nr.append()
        ptable.flush()

    def get_current_path(self):
        if self._frame is not None:
        #            for d in dir(self._frame):
        #                print d
            return self._frame.filename

    def lock_path(self, p):
        import stat

        os.chmod(p, stat.S_IROTH | stat.S_IRGRP | stat.S_IREAD)

    def delete_frame(self):
        p = self.get_current_path()
        try:
            os.remove(p)
        except Exception, e:
            print e

    def new_frame_ctx(self, *args, **kw):
        p = self._new_frame_path(*args, **kw)
        return self.open_file(p, 'w')


    def new_frame(self, *args, **kw):
        '''

        '''
        p = self._new_frame_path(*args, **kw)
        try:
            self._frame = openFile(p, mode='w',
                                   #                                    filters=Filters(complevel=self.compression_level)
            )
            #             self._frame = openFile(p, mode='w',
            #                                    filters=Filters(complevel=self.compression_level))
            return self._frame
        except ValueError:
            pass

            #        self.lock_path(p)


    def new_group(self, group_name, parent=None, description=''):
        '''
            if group already exists return it otherwise create a new group
        '''
        if parent is None:
            parent = self._frame.root

        grp = self.get_group(group_name, parent)

        if grp is None:
            grp = self._frame.createGroup(parent, group_name, description)

        return grp

    def new_table(self, group, table_name, table_style='TimeSeries'):
        '''
            if table already exists return it otherwise create a new table
        '''
        tab = self.get_table(table_name, group)
        if tab is None:
            tab = self._frame.createTable(group, table_name,
                                          table_description_factory(table_style))

        tab.flush()
        return tab

    def new_array(self, group, name, data):
        self._frame.createArray(group, name, data)

    def get_table(self, name, group, frame=None):
        if frame is None:
            frame = self._frame

        return get_table(name, group, frame)

    def get_group(self, name, grp=None):
        return next((g for g in self.get_groups(grp=grp) if g._v_name == name), None)

    def get_groups(self, grp=None):
        if grp is not None:
            if isinstance(grp, str):
                grp = getattr(self._frame.root, grp)
                #            print 'wget', grp
            return [g for g in grp._f_walkGroups() if g != grp]
        else:
            return [g for g in self._frame.walkGroups() if g != self._frame.root]

    def get_tables(self, grp):
        if isinstance(grp, str):
            grp = '/{}'.format(grp)

        f = self._frame
        return [n for n in f.walkNodes(grp, 'Table')]

    def isfile(self, path):
        return os.path.isfile(path)

    def open_data(self, path, mode='r', caller=None):
    #        print 'open data', caller
        if self.repository:
            out = os.path.join(self.workspace_root, path)
            path = os.path.join(self.repository.root, path)
            if not os.path.isfile(out):
                self.info('copying {} to repository {}'.format(path, os.path.dirname(out)))
                if not self.repository.retrieveFile(path, out):
                    return False
            path = out

        try:
            self._frame = openFile(path, mode, filters=Filters(complevel=self.compression_level))
            return True
        except Exception:
            self._frame = None
            import traceback

            traceback.print_exc()
            return True

    def close_file(self):
        try:
            self.debug('flush and close file {}'.format(self._frame.filename))

            for node in self._frame.walkNodes('/', 'Table'):
                node.flush()

            self._frame.flush()
            self._frame.close()
            self._frame = None
        #             del self._frame

        except Exception, e:
            print 'exception closing file', e

    def open_file(self, path, mode='r+'):
        return FileCTX(
            #                         self,
            weakref.ref(self)(),
            path, mode, self.compression_level)

    def open_table(self, path, table, group='/', mode='r'):
        return TableCTX(path, table, group, self.compression_level, mode)

    def kill(self):
        self.close_file()

        #        for table in f.walkNodes('/', 'Table'):

#    def add_table(self, table, table_style='Timestamp', parent='root'):
#        '''
#        '''
#        df, pgrp = self._get_parent(parent)
#
#        alpha = [chr(i) for i in range(65, 91)]
#        s = array([[''.join((b, a)) for a in alpha] for b in alpha]).ravel()
#
#        add = True
#        cnt = 0
#        base_table = table
#        while add:
#            try:
#                df.createTable(pgrp, table, table_description_factory(table_style))
#            except NodeError:
#
#                table = '%s%s' % (base_table, s[cnt])
#                cnt += 1
#                add = True
#            finally:
#                add = False
#        return table
#
#    def add_group(self, group, parent='root'):
#        '''
#
#
#        '''
#
#        df, pgrp = self._get_parent(parent)
#        df.createGroup(pgrp, group)
#
#        self._frame = df
#
#    def _get_parent(self, parent, df=None):
#        '''
#
#
#        '''
#        if not df:
#            df = self._frame
#
#        p = parent.split('.')
#        pgrp = None
#        prev_obj = None
#        for i, pi in enumerate(p):
#            if i == 0:
#                obj = df
#            else:
#                obj = prev_obj
#
#            pgrp = getattr(obj, pi)
#            prev_obj = pgrp
#
#        return df, pgrp
#
#    def _get_tables(self, df=None, path=None):
#        '''
#        '''
#        names = []
#        tabs = {}
#        #tabs=[]
#        if path is not None:
#            df = openFile(path, mode='r')
#
#        for group in df.walkGroups('/'):
#
# #            grpname = self._get_group_name(group)
#            for table in df.listNodes(group, classname='Table'):
#                #name = '%s.%s' % (grpname, table.name)
#                #tabs.append((grpname, table.name))
#                tabs[table.name] = table
#                names.append(table.name)
#
#        return names, tabs
#
#    def _get_groups(self, df):
#        '''
#
#        '''
#        grps = df.root._v_groups.keys()
#        self.selected_group = grps[0]
#        return grps
#
#    def _get_group_name(self, group):
#        '''
#        '''
#        s = group.__str__()
#        p, _c, _d = s.split(' ')
#        return p.split('/')[-1:][0]
if __name__ == '__main__':
    d = H5DataManager()
    print d
#============= EOF ====================================
#    def add_note(self, note = None):
#        df = self.data_frames[len(self.data_frames) - 1]
#        self._available_tables = self._get_tables(df)
#        info = self.edit_traits(view = 'note_view')
#        if info.result:
#            table = self._get_tables(df)[self.selected_table]
#            setattr(table.attrs, 'note', self.note)
