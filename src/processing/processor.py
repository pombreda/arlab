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
#============= standard library imports ========================
from datetime import datetime, timedelta

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql.expression import and_
from traits.api import HasTraits, Int, Str

#============= local library imports  ==========================
from src.database.isotope_database_manager import IsotopeDatabaseManager
from src.database.orms.isotope.gen import gen_AnalysisTypeTable, gen_MassSpectrometerTable

from src.database.orms.isotope.meas import meas_AnalysisTable, meas_MeasurementTable
from src.processing.analysis import Analysis
# from src.processing.plotters.spectrum import Spectrum
# from src.processing.plotters.ideogram import Ideogram
# from src.processing.plotters.inverse_isochron import InverseIsochron
# from src.processing.plotters.series import Series
from src.helpers.iterfuncs import partition
# from src.processing.plotters import plotter_options


class IrradiationPositionRecord(HasTraits):
    position = Int
    identifier = Str
    sample = Str

    def create(self, rec):
        self.position = int(rec.position)
        if rec.labnumber:
            self.identifier = rec.labnumber.identifier
            if rec.labnumber.sample:
                self.sample = rec.labnumber.sample.name


class Processor(IsotopeDatabaseManager):
    def find_associated_analyses(self, analysis, delta=12, atype=None, **kw):
        """
            find atype analyses +/- delta hours (12 hours default)
            if atype is None use "blank_{analysis.analysis_type}"
        """
        if not isinstance(analysis, Analysis):
            analysis = self.make_analysis(analysis)
            #             analysis.load_isotopes()

        ms = analysis.mass_spectrometer
        post = analysis.timestamp

        #         delta = -2
        if atype is None:
            atype = 'blank_{}'.format(analysis.analysis_type)
        br = self._find_analyses(ms, post, -delta, atype, **kw)

        #         delta = 2
        ar = self._find_analyses(ms, post, delta, atype, **kw)

        return br + ar

    def group_level(self, level, irradiation=None, monitor_filter=None):
        if monitor_filter is None:
            def monitor_filter(pos):
                if pos.sample == 'FC-2':
                    return True

        if isinstance(level, str):
            level = self.db.get_level(level, irradiation)

        refs = []
        unks = []
        if level:
            positions = level.positions

            if positions:
                def pos_factory(px):
                    ip = IrradiationPositionRecord()
                    ip.create(px)
                    return ip

                positions = [pos_factory(pp) for pp in positions]
                refs, unks = partition(positions, monitor_filter)

        return refs, unks

        #def load_series(self, analysis_type, ms, ed, weeks=0, days=0, hours=0):
        #    self.debug('{} {} {}'.format(analysis_type, ms, ed))
        #    db = self.db
        #    sess = db.get_session()
        #    q = sess.query(meas_AnalysisTable)
        #    q = q.join(meas_MeasurementTable)
        #    q = q.join(gen_AnalysisTypeTable)
        #    q = q.join(gen_MassSpectrometerTable)
        #    if ed:
        #        q = q.join(meas_ExtractionTable)
        #        q = q.join(gen_ExtractionDeviceTable)
        #        #         q = q.join(gen_LabTable)
        #
        #    d = datetime.datetime.today()
        #    today = datetime.datetime.today()  # .date()#.datetime()
        #    d = d - datetime.timedelta(hours=hours, weeks=weeks, days=days)
        #    attr = meas_AnalysisTable.analysis_timestamp
        #    q = q.filter(and_(attr <= today, attr >= d))
        #    q = q.filter(gen_AnalysisTypeTable.name == analysis_type)
        #    q = q.filter(gen_MassSpectrometerTable.name == ms)
        #
        #    if ed:
        #    #             ed = ed.capitalize()
        #    #             print ed
        #        q = q.filter(gen_ExtractionDeviceTable.name == ed)
        #
        #    self.debug(compile_query(q))
        #    return self._make_analyses_from_query(q)


        #def load_sample_analyses(self, labnumber, sample, aliquot=None):
        #    db = self.db
        #    sess = db.get_session()
        #    q = sess.query(meas_AnalysisTable)
        #    q = q.join(gen_LabTable)
        #    q = q.join(gen_SampleTable)
        #
        #    q = q.filter(gen_SampleTable.name == sample)
        #    if aliquot is not None:
        #        q = q.filter(meas_AnalysisTable.aliquot == aliquot)
        #
        #    if sample == 'FC-2':
        #        q = q.filter(gen_LabTable.identifier == labnumber)
        #
        #    #        q = q.limit(10)
        #    return self._make_analyses_from_query(q)

        #def _make_analyses_from_query(self, q):
        #    ans = None
        #    try:
        #        ans = q.all()
        #        self.debug('{}'.format(ans))
        #    except Exception, e:
        #        import traceback
        #
        #        traceback.print_exc()
        #
        #    if ans:
        #        ans = self.make_analyses(ans)
        #        return ans

        #     def auto_blank_fit(self, irradiation, level, kind):
        #         if kind == 'preceeding':
        #             '''
        #             1. supply a list of labnumbers/ supply level and extract labnumbers (with project minnabluff)
        #             2. get all analyses for the labnumbers
        #             3. sort analyses by run date
        #             4. calculate blank
        #                 1. preceeding/bracketing
        #                     get max 2 predictors
        #
        #                 2. fit
        #                     a. group analyses by run date
        #                     b. get n predictors based on group date
        #             5. save blank
        #             '''
        #             db = self.db
        #             level = db.get_irradiation_level(irradiation, level)
        #
        #             labnumbers = [pi.labnumber for pi in level.positions
        #                             if pi.labnumber.sample.project.name in ('j', 'Minna Bluff', 'Mina Bluff')]
        #             ans = [ai
        #                     for ln in labnumbers
        #                         for ai in ln.analyses
        #                         ]
        #             pd = self.open_progress(n=len(ans))
        #             for ai in ans:
        #                 self.preceeding_blank_correct(ai, pd=pd)
        #             db.commit()

    #def refit_isotopes(self, meas_analysis, pd=None, fits=None, keys=None, verbose=False):
    #
    ##         if not isinstance(analysis, Analysis):
    #    analysis = self.make_analysis(meas_analysis)
    #
    #    #         analysis.load_isotopes()
    #    dbr = meas_analysis
    #    #         dbr = analysis.dbrecord
    #    if keys is None:
    #        keys = [iso.molecular_weight.name for iso in dbr.isotopes
    #                if iso.kind == 'signal']
    #
    #    '''
    #        if spectrometer is map use all linear
    #
    #        if spectrometer is Jan or Obama
    #            if counts >150 use parabolic
    #            else use linear
    #    '''
    #    if fits is None:
    #        if analysis.mass_spectrometer in ('pychron obama', 'pychron jan', 'jan', 'obama'):
    #            n = 0
    #            if keys:
    #                n = analysis.isotopes[keys[0]].xs.shape[0]
    #
    #            if n >= 150:
    #                fits = ['parabolic', ] * len(keys)
    #            else:
    #                fits = ['linear', ] * len(keys)
    #
    #        else:
    #            fits = ['linear', ] * len(keys)
    #
    #    db = self.db
    #
    #    if not dbr.selected_histories:
    #        db.add_selected_histories(dbr)
    #        db.sess.flush()
    #
    #    msg = 'fitting isotopes for {}'.format(analysis.record_id)
    #    if pd is not None:
    #        pd.change_message(msg)
    #    self.debug(msg)
    #    dbhist = db.add_fit_history(dbr)
    #    for key, fit in zip(keys, fits):
    #        dbiso_baseline = next((iso for iso in dbr.isotopes
    #                               if iso.molecular_weight.name == key and iso.kind == 'baseline'), None)
    #        if dbiso_baseline:
    #            if verbose:
    #                self.debug('{} {}'.format(key, fit))
    #
    #            vv = analysis.isotopes[key]
    #            baseline = vv.baseline
    #            if not baseline:
    #                continue
    #
    #            v, e = baseline.value, baseline.error
    #            db.add_fit(dbhist, dbiso_baseline, fit='average_sem', filter_outliers=True,
    #                       filter_outlier_std_devs=2)
    #            db.add_isotope_result(dbiso_baseline, dbhist, signal_=float(v), signal_err=float(e))
    #
    #            dbiso = next((iso for iso in dbr.isotopes
    #                          if iso.molecular_weight.name == key and iso.kind == 'signal'), None)
    #            if dbiso:
    #                vv = analysis.isotopes[key]
    #                v, e = vv.value, vv.error
    #
    #                db.add_fit(dbhist, dbiso, fit=fit, filter_outliers=True,
    #                           filter_outlier_std_devs=2)
    #                db.add_isotope_result(dbiso, dbhist, signal_=float(v), signal_err=float(e))
    #
    #    if pd is not None:
    #        pd.increment()

    #def _get_preceeding_analysis(self, ms, post, atype):
    #    if isinstance(post, float):
    #        post = datetime.datetime.fromtimestamp(post)
    #
    #    sess = self.db.get_session()
    #    q = sess.query(meas_AnalysisTable)
    #    q = q.join(meas_MeasurementTable)
    #    q = q.join(gen_AnalysisTypeTable)
    #    q = q.join(gen_MassSpectrometerTable)
    #
    #    q = q.filter(and_(
    #        gen_AnalysisTypeTable.name == atype,
    #        gen_MassSpectrometerTable.name == ms,
    #        meas_AnalysisTable.analysis_timestamp < post,
    #    )
    #    )
    #
    #    q = q.order_by(meas_AnalysisTable.analysis_timestamp.desc())
    #    try:
    #        return q.first()
    #    except NoResultFound:
    #        pass

    #def preceeding_blank_correct(self, analysis, keys=None, pd=None):
    #    from src.regression.interpolation_regressor import InterpolationRegressor
    #
    #    if not isinstance(analysis, Analysis):
    #        analysis = self.make_analysis(analysis)
    #        #             analysis.load_isotopes()
    #
    #    msg = 'applying preceeding blank for {}'.format(analysis.record_id)
    #    if pd is not None:
    #        pd.change_message(msg)
    #        pd.increment()
    #
    #    #         self.info(msg)
    #    ms = analysis.mass_spectrometer
    #
    #    post = analysis.timestamp
    #
    #    #         delta = -5
    #    atype = 'blank_{}'.format(analysis.analysis_type)
    #
    #    an = self._get_preceeding_analysis(ms, post, atype)
    #
    #    if not an:
    #        self.warning('no preceeding blank for {}'.format(analysis.record_id))
    #        return
    #
    #    ai = self.make_analyses(an)
    #    #         ai.load_isotopes()
    #
    #    if keys is None:
    #        keys = analysis.isotope_keys
    #
    #    kind = 'blanks'
    #    history = self.add_history(an, kind)
    #
    #    fit = 'preceeding'
    #
    #    reg = InterpolationRegressor(kind=fit)
    #    for key in keys:
    #    #             predictors = [ai for ai in br if key in ai.isotopes]
    #        if key in ai.isotopes:
    #            r_xs, r_y = (ai.timestamp,), (ai.isotopes[key].baseline_corrected_value(),)
    #            #             if predictors:
    #            #                 r_xs, r_y = zip(*[(ai.timestamp, ai.isotopes[key].baseline_corrected_value()
    #            #                                           )
    #            #                                         for ai in predictors])
    #            r_ys, r_es = zip(*[(yi.nominal_value, yi.std_dev) for yi in r_y])
    #
    #            reg.trait_set(xs=r_xs,
    #                          ys=r_ys,
    #                          yserr=r_es,
    #            )
    #
    #            fit_obj = Fit(name=key, fit=fit)
    #            v, e = reg.predict(post), reg.predict_error(post)
    #            analysis.set_blank(key, (v[0], e[0]))
    #            self.apply_correction(history, analysis, fit_obj, [ai], kind)

    def save_arar(self, analysis, meas_analysis):
        with self.db.session_ctx():
            hist = meas_analysis.selected_histories.selected_arar
            if not hist:
                hist = self.db.add_arar_history(meas_analysis)
                arar = self.db.add_arar(hist)
            else:
                arar = hist.arar_result

            #force analysis to recalculate age
            #potentially redundant
            analysis.calculate_age(force=True)

            units = analysis.arar_constants.age_scalar

            attr = ('Ar40', 'Ar39', 'Ar38', 'Ar37', 'Ar36',
                    'rad40', 'cl36', 'ca37', 'k39')
            for ai in attr:
                a = getattr(analysis, ai)
                v, e = float(a.nominal_value), float(a.std_dev)
                setattr(arar, ai, v)
                setattr(arar, '{}_err'.format(ai), e)

            age = analysis.age * units
            v, e = age.nominal_value, age.std_dev

            je = analysis.age_error_wo_j * units

            arar.age = float(v)
            arar.age_err = float(e)
            arar.age_err_wo_j = je

            #update arar_history timestamp
            arar.history.create_date = datetime.now()

    #===============================================================================
    # corrections
    #===============================================================================
    def add_history(self, dbrecord, kind):
    #         dbrecord = analysis.dbrecord
        db = self.db

        # new history
        func = getattr(db, 'add_{}_history'.format(kind))
        history = func(dbrecord, user=db.save_username)
        #        history = db.add_blanks_history(dbrecord, user=db.save_username)

        # set analysis' selected history
        sh = db.add_selected_histories(dbrecord)
        setattr(sh, 'selected_{}'.format(kind), history)
        db.sess.flush()

        #        sh.selected_blanks = history
        return history

    def apply_fixed_correction(self, history, isotope, value, error, correction_name):
        func = getattr(self.db, 'add_{}'.format(correction_name))
        func(history, isotope=isotope, use_set=False,
             user_value=value, user_error=error)

    def apply_fixed_value_correction(self, phistory, history, fit_obj, correction_name):
        db = self.db
        if phistory:
            bs = getattr(phistory, correction_name)
            bs = reversed(bs)
            prev = next((bi for bi in bs if bi.isotope == fit_obj.name), None)
            if prev:
                uv = prev.user_value
                ue = prev.user_error
                func = getattr(db, 'add_{}'.format(correction_name))
                func(history,
                     isotope=prev.isotope,
                     fit=prev.fit,
                     user_value=uv,
                     user_error=ue
                )

    def apply_correction(self, history, analysis, fit_obj, predictors, kind):
        #meas_analysis = self.db.get_analysis_uuid(analysis.uuid)

        func = getattr(self, '_apply_{}_correction'.format(kind))
        func(history, analysis, fit_obj, predictors)

    def _apply_detector_intercalibration_correction(self, history, analysis, fit_obj, predictors):
        n, d = fit_obj.name.split('/')
        ic = analysis.get_isotope(detector=d).temporary_ic_factor
        if ic is None:
            self.debug('************************* no ic factor for {} {}'.format(analysis.record_id,
                                                                                 fit_obj))
            return

        ic_v, ic_e = map(float, ic)
        db = self.db
        item = db.add_detector_intercalibration(history,
                                                detector=d,
                                                user_value=ic_v,
                                                user_error=ic_e,
                                                fit=fit_obj.fit)
        if predictors:
            for pi in predictors:
                dbr = db.get_analysis_uuid(pi.uuid)
                db.add_detector_intercalibration_set(item, dbr)


    def _apply_blanks_correction(self, history, analysis, fit_obj, predictors):
        if not fit_obj.name in analysis.isotopes:
            return

        ss = analysis.isotopes[fit_obj.name]

        #ss=next((iso for iso in analysis.isotopes
        #        if iso.kind=='signal' and iso.molecular_weight.name==fit_obj.name), None)

        '''
            the blanks_editor may have set a temporary blank
            use that instead of the saved blank
        '''
        if hasattr(ss, 'temporary_blank'):
            blank = ss.temporary_blank
        else:
            blank = ss.blank

        db = self.db
        item = db.add_blanks(history,
                             isotope=fit_obj.name,
                             user_value=float(blank.value),
                             user_error=float(blank.error),
                             fit=fit_obj.fit)

        #        ps = self.interpolation_correction.predictors
        if predictors:

            lns = set([si.labnumber for si in predictors])
            ids = [si.uuid for si in predictors]

            def f(t, t2):
                return t2.identifier.in_(lns), t.uuid.in_(ids)

            ans = db.get_analyses(uuid=f)
            for ai in ans:
                db.add_blanks_set(item, ai)
                #for pi in predictors:
                #    dbr = db.get_analysis_uuid(pi.uuid)
                #    #                 self.db.add_blanks_set(item, pi.dbrecord)
                #    db.add_blanks_set(item, dbr)

    def _find_analyses(self, ms, post, delta, atype, step=0.5, maxtries=10, **kw):
        if delta < 0:
            step = -step

        for i in range(maxtries):
            rs = self._filter_analyses(ms, post, delta + i * step, 5, atype, **kw)
            if rs:
                return rs
        else:
            return []

    def _filter_analyses(self, ms, post, delta, lim, at, filter_hook=None):
        '''
            ms= spectrometer
            post= timestamp
            delta= time in hours
            at=analysis type

            if delta is negative
            get all before post and after post-delta

            if delta is post
            get all before post+delta and after post
        '''
        sess = self.db.get_session()
        q = sess.query(meas_AnalysisTable)
        q = q.join(meas_MeasurementTable)
        q = q.join(gen_AnalysisTypeTable)
        q = q.join(gen_MassSpectrometerTable)

        win = timedelta(hours=delta)
        if isinstance(post, float):
            post = datetime.fromtimestamp(post)

        dt = post + win
        if delta < 0:
            a, b = dt, post
        else:
            a, b = post, dt

        q = q.filter(and_(
            gen_AnalysisTypeTable.name == at,
            meas_AnalysisTable.analysis_timestamp >= a,
            meas_AnalysisTable.analysis_timestamp <= b,
            gen_MassSpectrometerTable.name == ms
        ))

        if filter_hook:
            q = filter_hook(q)

        q = q.order_by(meas_AnalysisTable.analysis_timestamp.desc())
        q = q.limit(lim)

        try:
            return q.all()
        except NoResultFound:
            pass

#============= EOF =============================================

#============= EOF =============================================
#     def new_ideogram2(self, ans, plotter_options=None):
#         '''
#             return a plotcontainer
#         '''
#
#         probability_curve_kind = 'cumulative'
#         mean_calculation_kind = 'weighted_mean'
#         data_label_font = None
#         metadata_label_font = None
# #        highlight_omitted = True
#         display_mean_indicator = True
#         display_mean_text = True
#
#         p = Ideogram(
# #                     db=self.db,
# #                     processing_manager=self,
#                      probability_curve_kind=probability_curve_kind,
#                      mean_calculation_kind=mean_calculation_kind
#                      )
#         options = dict(
#                        title='',
#                        data_label_font=data_label_font,
#                        metadata_label_font=metadata_label_font,
#                        display_mean_text=display_mean_text,
#                        display_mean_indicator=display_mean_indicator,
#                        )
#
#         if plotter_options is None:
#             pom = IdeogramOptionsManager()
#             plotter_options = pom.plotter_options
#
#         if ans:
# #             self.analyses = ans
#             gideo = p.build(ans, options=options,
#                             plotter_options=plotter_options)
#             if gideo:
#                 gideo, _plots = gideo
#
#             return gideo, p
#     def new_spectrum(self, ans, plotter_options=None):
#         pass
#
#         p = Spectrum()
#
#         if plotter_options is None:
#             pom = SpectrumOptionsManager()
#             plotter_options = pom.plotter_options
#
#         options = {}
#
#         self._plotter_options = plotter_options
#         if ans:
# #             self.analyses = ans
#             gspec = p.build(ans, options=options,
#                             plotter_options=plotter_options)
#             if gspec:
#                 gspec, _plots = gspec
#
#             return gspec, p
