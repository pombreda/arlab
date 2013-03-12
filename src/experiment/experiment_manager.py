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
from traits.api import Instance, List, Str, Property
from apptools.preferences.preference_binding import bind_preference
# import apptools.sweet_pickle as pickle
#============= standard library imports ========================
from threading import Thread
import time
import hashlib
#============= local library imports  ==========================
from src.experiment.experiment_set import ExperimentSet
from src.paths import paths
from src.database.adapters.isotope_adapter import IsotopeAdapter
from src.experiment.selection_view import SelectionView
from src.experiment.file_listener import FileListener
from src.experiment.entry.labnumber_entry import LabnumberEntry
from src.experiment.set_selector import SetSelector
from src.managers.manager import Manager, SaveableManagerHandler
from pyface.timer.do_later import do_later
from src.helpers.alphas import ALPHAS
from src.saveable import Saveable


class ExperimentManagerHandler(SaveableManagerHandler):
    def object_experiment_set_changed(self, info):
        if info.initialized:
            if info.object.experiment_set is not None:
#                info.ui.title = 'Experiment {}'.format(info.object.title)
                info.ui.title = info.object.title

    def object_path_changed(self, info):
        if info.initialized:
            if info.object.experiment_set is not None:
#                info.ui.title = 'Experiment {}'.format(info.object.title)
                info.ui.title = info.object.title

class ExperimentManager(Manager, Saveable):
    handler_klass = ExperimentManagerHandler
    experiment_set = Instance(ExperimentSet)
    set_selector = Instance(SetSelector)
    db = Instance(IsotopeAdapter)
#    repository = Instance(Repository)

#    repo_kind = Str
    experiment_sets = List

    title = Property(depends_on='experiment_set')  # DelegatesTo('experiment_set', prefix='name')
#    path = DelegatesTo('experiment_set')
#    path = Property(depends_on='experiment_set')
#    editing_signal = None
    filelistener = None
    username = Str

    _text = None
    _experiment_hash = None


#===============================================================================
# processing
# @todo: refractor to separate manager
#===============================================================================
#    def plot_series1(self):
#        db=self.db
#        dbs=db.get_labnumber(1203)
#        from src.processing.analysis import Analysis
#        from src.database.records.isotope_record import IsotopeRecord
#        ans=[Analysis(dbrecord=IsotopeRecord(_dbrecord=di)) for di in dbs.analyses]
#
#        #from src.graph.time_series_graph import TimeSeriesGraph
#        from src.graph.regression_graph import RegressionTimeSeriesGraph
#        g=RegressionTimeSeriesGraph(container_dict=dict(padding=5))
#        p=g.new_plot()
#        p.value_range.tight_bounds=False
#        x,y=zip(*[(ai.timestamp,(ai.signals['Ar40'].value-ai.signals['Ar40bs'].value)/ai.signals['Ar36'].value-ai.signals['Ar36bs'].value) for ai in ans])
#
#        p,s,l=g.new_series(x,y,
#                     type='scatter', marker_size=1.5, fit='average_SEM')
#        g.edit_traits()
#
#        for ri in g.regressors:
#            print ri.coefficients
#
#        db.close()
#
#    def plot_series(self):
#        db=self.db
#        from src.processing.analysis import Analysis
#        from src.database.records.isotope_record import IsotopeRecord
#        dbs=db.get_labnumber(4)
#        ans=[Analysis(dbrecord=IsotopeRecord(_dbrecord=di)) for di in dbs.analyses]
#        bg=next((ai for ai in ans if ai.aliquot==8))
#
#        dbs=db.get_labnumber(3)
#        ans=[Analysis(dbrecord=IsotopeRecord(_dbrecord=di)) for di in dbs.analyses]
#        bu=next((ai for ai in ans if ai.aliquot==23))
#
#        dbs=db.get_labnumber(1203)
#        ans=[Analysis(dbrecord=IsotopeRecord(_dbrecord=di)) for di in dbs.analyses]
#        a=next((ai for ai in ans if ai.aliquot==10))
#
#
#
#        bg40=bg.signals['Ar40'].value-bg.signals['Ar40bs'].value
#        bg36=bg.signals['Ar36'].value-bg.signals['Ar36bs'].value
#
#        b40=a.signals['Ar40bl'].value-bg40
#        b36=a.signals['Ar36bl'].value-bg36
#
#        c40=a.signals['Ar40'].value-a.signals['Ar40bs'].value-b40
#        c36=a.signals['Ar36'].value-a.signals['Ar36bs'].value-b36
#
#        print c40/c36
#
#        cbg40=c40-bg40
#        cbg36=c36-bg36
#        print cbg40/cbg36




    def __init__(self, *args, **kw):
        super(ExperimentManager, self).__init__(*args, **kw)
        self.bind_preferences()
        self.populate_default_tables()

    def _reload_from_disk(self):
#        if not self._alive:
        ts = self._parse_experiment_file(self.experiment_set.path)
        for ei, ti in zip(self.experiment_sets, ts):
#                ei._cached_runs = None
            ei.load_automated_runs(text=ti)

        self._update_aliquots()

    def check_for_file_mods(self):
        path = self.experiment_set.path
        if path:
            with open(path, 'r') as f:
                diskhash = hashlib.sha1(f.read()).hexdigest()
            return self._experiment_hash != diskhash

    def save(self):
        self.save_experiment_sets()

    def save_as(self):
        self.save_as_experiment_sets()

    def save_as_experiment_sets(self):
        # test sets before saving
        for exp in self.experiment_sets:
            if not exp.test():
                return

        p = self.save_file_dialog(default_directory=paths.experiment_dir)
        if p:
            p = self._dump_experiment_sets(p)
            self.save_enabled = True

    def save_experiment_sets(self):
        for exp in self.experiment_sets:
            if not exp.test():
                return
        self._dump_experiment_sets(self.experiment_set.path)
        self.save_enabled = False

    def _dump_experiment_sets(self, p):

        if not p:
            return
        if not p.endswith('.txt'):
            p += '.txt'



        self.info('saving experiment to {}'.format(p))
        with open(p, 'wb') as fp:
            n = len(self.experiment_sets)
            for i, exp in enumerate(self.experiment_sets):
                exp.path = p
                exp.dump(fp)
                if i < (n - 1):
                    fp.write('\n')
                    fp.write('*' * 80)

        return p

    def start_file_listener(self, path):
        fl = FileListener(
                          path,
                          callback=self._reload_from_disk,
                          check=self.check_for_file_mods
                          )
        self.filelistener = fl

    def stop_file_listener(self):
        self.filelistener.stop()

    def opened(self):
        self.info_display.clear()

    def close(self, isok):
        if self.filelistener:
            self.filelistener.stop()
        return isok

    def test_connections(self):
        if not self.db:
            return

        if not self.db.connect():
            self.warning_dialog('Failed connecting to database. {}'.format(self.db.url))
            return

#        if not self.repository.connect():
#            self.warning_dialog('Failed connecting to repository {}'.format(self.repository.url))
#            return

        return True

    def populate_default_tables(self):
        db = self.db
        if self.db:
            if db.connect():

                from src.database.defaults import load_isotopedb_defaults
                load_isotopedb_defaults(db)

    def bind_preferences(self):
        if self.db is None:
            self.db = self._db_factory()

        prefid = 'pychron.experiment'

        bind_preference(self, 'username', '{}.username'.format(prefid))
#        bind_preference(self, 'repo_kind', '{}.repo_kind'.format(prefid))

#        if self.repo_kind == 'FTP':
#            bind_preference(self.repository, 'host', '{}.ftp_host'.format(prefid))
#            bind_preference(self.repository, 'username', '{}.ftp_username'.format(prefid))
#            bind_preference(self.repository, 'password', '{}.ftp_password'.format(prefid))
#            bind_preference(self.repository, 'remote', '{}.repo_root'.format(prefid))

        bind_preference(self.db, 'kind', '{}.db_kind'.format(prefid))
        if self.db.kind == 'mysql':
            bind_preference(self.db, 'host', '{}.db_host'.format(prefid))
            bind_preference(self.db, 'username', '{}.db_username'.format(prefid))
            bind_preference(self.db, 'password', '{}.db_password'.format(prefid))

        bind_preference(self.db, 'name', '{}.db_name'.format(prefid))

        if not self.db.connect():
            self.warning_dialog('Not Connected to Database {}'.format(self.db.url))
            self.db = None

    def selector_factory(self, style):
        db = self.db
        sel = db.selector_factory(style=style)
#        sel.set_data_manager(kind=self.repo_kind,
#                                      repository=self.repository,
#                                      workspace_root=paths.default_workspace_dir
#                                      )
        return sel

    def open_recent(self):
        db = self.db
        if db.connect():
            db.reset()
            selector = self.selector_factory('simple')

            selector.load_recent()
            v = SelectionView(table=selector)
            v.build_graph()

            self.open_view(v)

    def _extract_experiment_text(self, path, i):
        ts = self._parse_experiment_file(path)
        return ts[i]

    def _parse_experiment_file(self, path):
        with open(path, 'r') as f:
            ts = []
            tis = []
            a = ''
            for l in f:
                a += l
                if l.startswith('*' * 80):
                    ts.append(''.join(tis))
                    tis = []
                    continue

                tis.append(l)
            ts.append(''.join(tis))
            self._experiment_hash = hashlib.sha1(a).hexdigest()
            self._text = a
            return ts

    def _get_all_automated_runs(self):
        return [ai for ei in self.experiment_sets
                    for ai in ei.automated_runs]

    def _update_aliquots(self):

        ans = self._get_all_automated_runs()
        # update the aliquots
        self._modify_aliquots(ans)

        # update the steps
        self._modify_steps(ans)

    def _modify_steps(self, ans):
        db = self.db
        idcnt_dict = dict()
        stdict = dict()
        extract_group = 1
        aoffs = dict()
        for arun in ans:
            arunid = arun.labnumber
            if arun.skip:
                arun.aliquot = 0
                continue

            if arun.extract_group:
                if not arun.extract_group == extract_group:
                    if arunid in aoffs:
                        aoffs[arunid] += 1
                    else:
                        aoffs[arunid] = 1

#                    aoff += 1
                    idcnt_dict, stdict = dict(), dict()
                    c = 1
                else:
                    if arunid in idcnt_dict:
                        c = idcnt_dict[arunid]
                        c += 1
                    else:
                        c = 1

                ln = db.get_labnumber(arunid)
                if ln is not None:
                    an = ln.analyses[-1]
                    if an.aliquot != arun.aliquot:
                        st = 0
                    else:
                        try:
                            st = an.step
                            st = list(ALPHAS).index(st) + 1
                        except (IndexError, ValueError):
                            st = 0
                else:
                    st = stdict[arunid] if arunid in stdict else 0

                arun._step = st + c
                idcnt_dict[arunid] = c
                stdict[arunid] = st
                extract_group = arun.extract_group


            if arunid in aoffs:
                aoff = aoffs[arunid]
            else:
                aoff = 0
#            print arun.labnumber, aoff
            arun.aliquot += aoff

    def _modify_aliquots(self, ans):
        offset = 0
        if self.experiment_set and self.experiment_set.selected:
            offset = len(self.experiment_set.selected)

        db = self.db
        # update the aliquots
        idcnt_dict = dict()
        stdict = dict()
        for arun in ans:
            if arun.skip:
                continue

            arunid = arun.labnumber
            c = 1
#            print arunid, idcnt_dict.keys()
            if arunid in idcnt_dict:
                c = idcnt_dict[arunid]
                if not arun.extract_group:
                    c += 1
#                else:
#                    c = 1
#            else:
#                c = 1
            ln = db.get_labnumber(arunid)
            if ln is not None:
                try:
                    st = ln.analyses[-1].aliquot
                except IndexError:
                    st = 0
            else:
                st = stdict[arunid] if arunid in stdict else 0
#                if arunid in stdict:
#                    st = stdict[arunid]
#                else:
#                    st = 0
            arun.aliquot = st + c - offset
#            print '{:<20s}'.format(str(arun.labnumber)), arun.aliquot, st, c
            idcnt_dict[arunid] = c
            stdict[arunid] = st

    def _update_dirty(self):
        pass
#===============================================================================
# experiment set
#===============================================================================
    def new_experiment_set(self, clear=True):
        if clear:
            self.experiment_sets = []

        exp = self._experiment_set_factory()
        arun = exp.automated_run_factory()
        exp.automated_run = arun
#        exp.automated_runs.append(arun)
        self.experiment_set = exp
        self.experiment_sets.append(exp)

#    def close(self, isok):
#        self.dirty_save_as = False
#===============================================================================
# persistence
#===============================================================================
    def load_experiment_set(self, path=None, edit=True, saveable=False):
#        self.bind_preferences()
        # make sure we have a database connection
        if not self.test_connections():
            return

        if path is None:
            path = self.open_file_dialog(default_directory=paths.experiment_dir)

        if path is not None:

            self.experiment_set = None
            self.experiment_sets = []
            # parse the file into individual experiment sets
            ts = self._parse_experiment_file(path)
            ws = []
            for text in ts:
                exp = self._experiment_set_factory(path=path)
                exp._warned_labnumbers = ws
                if exp.load_automated_runs(text=text):
                    self.experiment_sets.append(exp)

                    if edit:
                        exp.automated_run = exp.automated_runs[-1].clone_traits()
#                        exp.set_script_names()
                ws = exp._warned_labnumbers

            self._update_aliquots()
            if self.experiment_sets:
                self.experiment_set = self.experiment_sets[0]
                self.start_file_listener(self.experiment_set.path)
                def func():
                    self.set_selector.selected_index = -2
                    self.set_selector.selected_index = 0

                do_later(func)

                return True
#===============================================================================
# property get/set
#===============================================================================
    def _get_title(self):
        if self.experiment_set:
            return 'Experiment {}'.format(self.experiment_set.name)

#    def _get_path(self):
#        if self.experiment_set:
#            return self.experiment_set.path
#
#===============================================================================
# handlers
#===============================================================================
#    def _experiment_set_changed(self):
#        if self.filelistener:
#            self.filelistener.stop()
#
#        path = self.experiment_set.path
#        self.start_file_listener(path)
#===============================================================================
# views
#===============================================================================

#===============================================================================
# factories
#===============================================================================
    def _experiment_set_factory(self, **kw):
        exp = ExperimentSet(
                             db=self.db,
                             application=self.application,
                             **kw)
        exp.on_trait_change(self._update_aliquots, 'update_aliquots_needed')
#        exp.on_trait_change(self._update_dirty, 'dirty')
        return exp

    def _labnumber_entry_factory(self):
        lne = LabnumberEntry(db=self.db)
        return lne

    def _db_factory(self):
        db = IsotopeAdapter(application=self.application)
        return db

#===============================================================================
# defaults
#===============================================================================
    def _default_save_directory_default(self):
        return paths.experiment_dir

    def _set_selector_default(self):
        s = SetSelector(experiment_manager=self,
                        addable=True
                        )
        return s

    def _db_default(self):
        return self._db_factory()

#    def _repository_default(self):
#        if self.repo_kind == 'local':
#            klass = Repository
#        else:
#            klass = FTPRepository
#
#        repo = klass()
#        #use local data dir
#        repo.root = paths.isotope_dir
#        return repo

# def main():
#    paths.build('_experiment')
#    from src.helpers.logger_setup import logging_setup
#
#    logging_setup('experiment_manager')
#
#    globalv.show_infos = False
#
# #    s = SpectrometerManager()
# #    s.bootstrap()
# #    s.molecular_weight = 'Ar40'
# #    ini = Initializer()
# #    ini.add_initialization(dict(name = 'spectrometer_manager',
# #                                manager = s
# #                                ))
# #    ini.run()
#
# #    e = ExperimentManager(spectrometer_manager=s)
#    e = ExperimentManager()
#
# #    e.configure_traits(view='test_view')
# #    e.analyze_data()
#    e.configure_traits(view='execute_view')

def dum_run(r):
    print 'start ', r
    time.sleep(1)
    print 'finish   ', r
#    for i in range(5):


def test():

    runs = (ri for ri in range(4))
    while 1:
        try:
            run = runs.next()
        except StopIteration:
            break
        t = Thread(target=dum_run, args=(run,))
        t.start()
        time.sleep(1.8)

# if __name__ == '__main__':
#    main()
#    test()
#============= EOF ====================================

#===============================================================================
# ##analysis code
#===============================================================================
#    def analyze_data(self):
#        '''
#            provide a list of run numbers
#            get intercept and error for ni points
#            correct the data for baseline and blank
#            calculate blank intercept using nj points
#            calculate intercept
#            calculate mswd
#        '''
##===============================================================================
# # gather data
##===============================================================================
#        runlist = ['B-01', 'A-01', 'A-02', 'A-03', 'A-04', 'B-02',
#                   'A-05', 'A-06', 'A-07', 'B-03'
#                   ]
#
#        blanks, airs, unknowns, b_bs, a_bs, u_bs = self.gather_data(runlist)
# #        self.permuate_data(blanks, airs, a_bs, b_bs)
#
#        self.plot_air_series(blanks, airs, b_bs, a_bs)
#
#    def plot_air_series(self, blanks, airs,
#                        blank_baselines,
#                        air_baselines):
#        g = StackedGraph()
# #        g.new_plot(xtitle='npts',
# #                   ytitle='40/36')
# #        g.new_plot(ytitle='40/36 err')
#        g.new_plot(ytitle='Population SD',
#                   show_legend=True
#                   )
#
# #        xs = [100, 200, 500, 1000, 2000]
#        for si, fit in enumerate([
#                                  ('linear', 1), ('parabolic', 2),
#                                  ('cubic', 3),
#                                  ('exponential', 'quick_exponential')
#                                  ]):
#            self._plot_air_series(g, fit, si, blanks, airs, blank_baselines, air_baselines)
#
#        g.set_y_limits(0, 1)
#        g.edit_traits()
#
#    def _plot_air_series(self, g, fit, si, blanks, airs, blank_baselines, air_baselines):
#        xs = range(100, 2000, 100)
#        name, fit = fit
#        cor_ratioss = [self.calculate_ratios(ni, fit, blanks, airs,
#                                             blank_baselines,
#                                   air_baselines,
#                                  )
#                     for ni in xs
#                     ]
#
#        n = len(airs['h1'])
# #        scatter_args = dict(type='scatter', marker='circle',
# #                         marker_size=1.75)
#        scatter_args = dict()
# #        for i in range(n):
# ##            g.new_series(plotid=0, **scatter_args)
# ##            g.new_series(plotid=1, **scatter_args)
# #            g.new_series(plotid=0)
# #            g.new_series(plotid=1)
#
#        g.new_series(plotid=0, **scatter_args)
#
#        g.set_series_label(name, series=si)
#        for ci, xi in zip(cor_ratioss, xs):
# #            print ci
#            ms, sds = zip(*[(i.nominal_value, i.std_dev()) for i in ci])
#            ms = array(ms)
#            sds = array(sds)
# #            print SD
# #            for si in range(n):
# #                g.add_datum((xi, ms[si]), plotid=0, series=si)
# #                g.add_datum((xi, sds[si]), plotid=1, series=si)
#
#            g.add_datum((xi, ms.std()), plotid=0, series=si)
#
# #            g.new_series(xs, ms, type='scatter', plotid=0)
# #            g.new_series(xs, sds, type='scatter', plotid=1)
#
#        g.set_x_limits(0, xs[-1] + 100)
#
#    def gather_data(self, runlist):
#        blanks = dict()
#        airs = dict()
#        unknowns = dict()
#        air_baselines = dict()
#        blank_baselines = dict()
#        unknown_baselines = dict()
#
#        for rid in runlist:
#            self.info('loading run {} signal file'.format(rid))
#            #open signal file
#            p = os.path.join(paths.data_dir,
#                            'automated_runs',
#                            'mswd_counting_experiment',
#                            '{}-intensity001.txt'.format(rid))
#            xs, h1s, cdds = loadtxt(p, unpack=True, delimiter=',',
#                        skiprows=int(2 / 3. * self.equilibration_time))
#
#            self.info('loading run {} baseline file'.format(rid))
#            #open baseline file
#            p = os.path.join(paths.data_dir,
#                             'automated_runs',
#                             'mswd_counting_experiment',
#                             '{}-baseline001.txt'.format(rid))
#            _xs_baseline, h1s_baseline, cdds_baseline = loadtxt(p,
#                                            unpack=True, delimiter=',')
#
#            #calculate baseline
#            h1_baseline = ufloat((h1s_baseline.mean(), h1s_baseline.std()))
#            cdd_baseline = ufloat((cdds_baseline.mean(), cdds_baseline.std()))
#
##===============================================================================
# #
##===============================================================================
# #            h1_baseline = 0
# #            cdd_baseline = 0
#
#            #if the sample is a blank add to blank list
#            if rid.startswith('B'):
#                int_dict = blanks
#                baselines = blank_baselines
#            elif rid.startswith('A'):
#                int_dict = airs
#                baselines = air_baselines
#            else:
#                int_dict = unknowns
#                baselines = unknown_baselines
#
#            for k, v, b in [('h1', (xs, h1s), h1_baseline),
#                            ('cdd', (xs, cdds), cdd_baseline)]:
#                try:
#                    int_dict[k].append(v)
#                except KeyError:
#                    int_dict[k] = [v]
#                try:
#                    baselines[k].append(b)
#                except KeyError:
#                    baselines[k] = [b]
#
#        return (blanks, airs, unknowns,
#                blank_baselines, air_baselines, unknown_baselines)
#
#    def permuate_data(self, blanks, airs, blank_baselines, air_baselines):
#
#        g = Graph()
#        g.new_plot(xtitle='npoints',
#                   ytitle='mswd',
#                   title='MSWD {}-Airs vs Counting Time'.format(len(airs['h1']))
#                   )
#        g.edit_traits()
#
#        s = 10
#        e = 2000
#        step = 10
#        nxs = arange(s, e, step)
#
#        mswds = [self._calculate_mswd(ni,
#                blanks, airs, blank_baselines, air_baselines) for ni in nxs]
#
#        g.new_series(nxs, mswds)
#        snxs = smooth(nxs)
#        smswds = smooth(mswds)
#        g.new_series(snxs, smswds)
#        g.add_horizontal_rule(1)
#
#        g.redraw()
#
#    def _calculate_mswd(self, ni, fit, blanks, airs,
#                         blank_baselines, air_baselines):
#
#        cor_ratios = self.calculate_ratios(ni, fit, blanks, airs,
#                                           blank_baselines, air_baselines)
#        verbose = False
#        if verbose:
#            self.info('40Ar/36Ar for npts {}'.format(ni))
#            self.info('average={} n={}'.format(cor_ratios.mean(),
#                                           cor_ratios.shape[0]
#                                           ))
#
#        x, errs = zip(*[(cr.nominal_value,
#                         cr.std_dev()) for cr in cor_ratios])
# #
#        return calculate_mswd(x, errs)
#
#    def calculate_ratios(self, ni, fit, blanks, airs,
#                            blank_baselines,
#                            air_baselines):
#        permutate_blanks = False
#        if permutate_blanks:
#            ti = ni
#        else:
#            ti = -1
#
#        h1bs, cddbs = self._calculate_correct_intercept(fit, blanks, blank_baselines,
#                                                        dict(h1=0, cdd=0),
#                                                        truncate=ti)
#
#        h1bs, cddbs = h1bs.mean(), cddbs.mean()
# #        h1bs, cddbs = 0, 0
# #        print 'asdfas', len(airs['h1']), len(airs['cdd'])
# #        print 'asdfas', len(air_baselines['h1']), len(air_baselines['cdd'])
#        cor_h1, cor_cdd = self._calculate_correct_intercept(fit,
#                                                            airs,
#                                                            air_baselines,
#                                                                dict(h1=h1bs,
#                                                                     cdd=cddbs
#                                                                     ),
#                                                            truncate=ni
#                                                            )
#
#        cor_ratios = cor_h1 / cor_cdd
#
#        return cor_ratios
#
#    def _calculate_correct_intercept(self, fit, signals, baselines,
#                                      blanks, truncate= -1):
#        cor_h1 = []
#        cor_cdd = []
#
#        from src.data_processing.regression.regressor import Regressor
#        r = Regressor()
#
#        for (xs, h1s), h1b, (xs2, cdds), cddb in zip(signals['h1'],
#                                               baselines['h1'],
#                                               signals['cdd'],
#                                               baselines['cdd']
#                                               ):
#            if fit == 'quick_exponential':
#                c, ce = r.quick_exponential(xs[:truncate], h1s[:truncate])
#                h1_int = ufloat((c[0],
#                                 ce[0]))
#
#                c, ce = r.quick_exponential(xs2[:truncate], cdds[:truncate])
#
#                cdd_int = ufloat((c[0],
#                               ce[0]))
#            else:
#                o = OLS(xs[:truncate], h1s[:truncate], fitdegree=fit)
#                h1_int = ufloat((o.get_coefficients()[fit],
#                                o.get_coefficient_standard_errors()[fit]))
#                o = OLS(xs2[:truncate], cdds[:truncate], fitdegree=fit)
#                cdd_int = ufloat((o.get_coefficients()[fit],
#                                o.get_coefficient_standard_errors()[fit]))
#
#            #apply baseline correction
#            h1_cor_int = h1_int - h1b
#            cdd_cor_int = cdd_int - cddb
#
#            #apply blank correction
#            h1_cor_int -= blanks['h1']
#            cdd_cor_int -= blanks['cdd']
#
#            cor_h1.append(h1_cor_int)
#            cor_cdd.append(cdd_cor_int)
#
#        return array(cor_h1), array(cor_cdd)


