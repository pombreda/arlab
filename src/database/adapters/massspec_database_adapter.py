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

#=============enthought library imports=======================

#=============standard library imports ========================

#=============local library imports  ==========================
from src.database.orms.massspec_orm import IsotopeResultsTable, \
    AnalysesChangeableItemsTable, BaselinesTable, DetectorTable, \
     IsotopeTable, AnalysesTable, \
    IrradiationPositionTable, SampleTable, \
    PeakTimeTable, DetectorTypeTable, DataReductionSessionTable, \
    PreferencesTable, DatabaseVersionTable, FittypeTable, \
    BaselinesChangeableItemsTable, SampleLoadingTable, MachineTable, \
    AnalysisPositionTable, LoginSessionTable, RunScriptTable
from src.database.core.database_adapter import DatabaseAdapter

from src.database.core.functions import delete_one, get_first
from sqlalchemy.sql.expression import func

from src.database.selectors.massspec_selector import MassSpecSelector
import binascii


class MassSpecDatabaseAdapter(DatabaseAdapter):
    selector_klass = MassSpecSelector
    test_func = 'get_database_version'

    def get_analyses(self, **kw):
        return self._get_items(AnalysesTable, globals(), **kw)
    def get_samples(self, **kw):
        return self._get_items(SampleTable, globals(), **kw)

    def get_database_version(self):
        return self._retrieve_items(DatabaseVersionTable)
#===============================================================================
# getters
#===============================================================================
    def get_sample_loading(self, value):
        return self._retrieve_item(SampleLoadingTable, value, key='SampleLoadingID')

    def get_login_session(self, value):
        return self._retrieve_item(LoginSessionTable, value, key='LoginSessionID')

    def get_analysis(self, value):
        return self._retrieve_item(AnalysesTable, value, key='RID')

    def get_irradiation_position(self, value):
        return self._retrieve_item(IrradiationPositionTable, value, key='IrradPosition')

    def get_sample(self, value):
        return self._retrieve_item(SampleTable, value, key='Sample')

    def get_detector_type(self, value):
        return self._retrieve_item(DetectorTypeTable, value, key='Label')

    @get_first
    def get_detector(self, dtype):
        return DetectorTable, 'DetectorTypeID', \
                DetectorTable.DetectorID.desc() # gets the most recent value

    def get_isotope(self, value):
        return self._retrieve_item(IsotopeTable, value, key='AnalysisID')

    def get_data_reduction_session(self, value):
        return self._retrieve_item(DataReductionSessionTable, value,
                                   key='DataReductionSessionID')

    def get_preferences_set(self, value):
        return self._retrieve_item(PreferencesTable, value, key='PreferenceSetID')

    def get_system(self, value):
        return self._retrieve_item(MachineTable, value, key='Label')

    def get_fittype(self, label):
        '''
            convert label to mass spec format
        '''
        if isinstance(label, int):
            pass
        elif isinstance(label, str):
            label = label.capitalize()

        fit = self._get_fittype(label)
        if fit is None:
            fit = 0
        else:
            fit = fit.Fit

        return fit

    def _get_fittype(self, value):
        return self._retrieve_item(FittypeTable, value, key='Label')

    def get_runscript(self, value):
        return self._retrieve_item(RunScriptTable, value, key='RunScriptID')
#===============================================================================
# adders
#===============================================================================
    def add_sample_loading(self, ms, tray):

        if isinstance(ms, str):
            ms = ms.capitalize()
            system = self.get_system(ms)
            if system:
                ms = system.SpecSysN
            else:
                ms = 0

        sm = SampleLoadingTable(SampleHolder=tray,
                                SpecSysN=ms
                                )
        self._add_item(sm)
        return sm

    def add_analysis_positions(self, analysis, positions):
        if not isinstance(positions, list):
            positions = [positions]

        analysis = self.get_analysis(analysis)
        if analysis:
            for i, pi in enumerate(positions):
                try:
                    pi = int(pi)
                    self._add_analysis_position(analysis, pi, i + 1)
                except (ValueError, TypeError):
                    pass

    def _add_analysis_position(self, analysis, pi, po):
        a = AnalysisPositionTable(Hole=pi, PositionOrder=po)
        analysis.positions.append(a)


#    @add
    def add_analysis(self, rid, aliquot, step, irradpos, runtype, **kw):
        '''
        '''

        rid = '{}-{}'.format(rid, aliquot)
        analysis = self.get_analysis(rid)
        if analysis is None:
#            rid, aliquot = rid.split('-')
#            r = int(args[0])
#            d = int(args[1]) if len(args) == 2 else None


            #query the IrradiationPositionTable
            irradpos = self.get_irradiation_position(irradpos)
            params = dict(RID=rid,
                         Aliquot=aliquot,
                         RunDateTime=func.current_timestamp(),
                         LoginSessionID=1,
                         SpecRunType=runtype,
                         Increment=step
                         )

            #IrradPosition cannot be null
            if irradpos is not None:
                ip = irradpos.IrradPosition
                sa = irradpos.SampleID
            else:
                ip = -2
                sa = 0

            params['RedundantSampleID'] = sa
            params['IrradPosition'] = ip
            params.update(kw)
            analysis = AnalysesTable(**params)

            self._add_item(analysis)

        return analysis

    def add_baseline(self, blob, label, cnts, iso, **kw):
        bs = BaselinesTable(PeakTimeBlob=blob,
                            Label=label,
                            NumCnts=cnts)
        if iso is not None:
            iso.baseline = bs
#            return bs, True

        return bs

#    @add
    def add_baseline_changeable_item(self, data_reduction_session_id, fit, infoblob):
        fit = self.get_fittype(fit)
#        print data_reduction_session,'dd'
#        dr=self.get_data_reduction_session(data_reduction_session)
#        print dr, 'db dr'
        bs = BaselinesChangeableItemsTable(Fit=fit,
                                           DataReductionSessionID=data_reduction_session_id,
                                           InfoBlob=infoblob
                                           )
        self._add_item(bs)
        return bs
#        return bs, True

#    @add
    def add_peaktimeblob(self, blob1, blob2, iso, **kw):
        iso = self.get_isotope(iso)
        pk = PeakTimeTable(PeakTimeBlob=blob1,
                           PeakNeverBslnCorBlob=blob2
                           )
        if iso is not None:
#            iso.peak_time_series= pk
            iso.peak_time_series.append(pk)
        return pk

    def add_detector(self, det_type, **kw):
        dtype = self.get_detector_type(det_type)
        d = DetectorTable()
        if dtype is not None:
            dtype.detectors.append(d)

        self._add_item(d)
        return d

    def add_isotope(self, rid, det, label, **kw):
        detector = None
        analysis = self.get_analysis(rid)
        if isinstance(det, str):
            #assume is a detector label e.i H1
            dettype = self.get_detector_type(det)
            if dettype is not None and len(dettype.detectors):
                det = dettype.detectors[-1]

            detector = self.get_detector(det)

        iso = IsotopeTable(Label=label,
                           NumCnts=1
                           )

        if analysis is not None:
            analysis.isotopes.append(iso)
        if detector is not None:
            detector.isotopes.append(iso)
            iso.BkgdDetectorID = detector.DetectorID

        self._add_item(iso)
        return iso

    def add_isotope_result(self, isotope, data_reduction_session_id,
                           intercept, baseline, blank,
                           fit
#                           intercept, intercept_err,
#                           baseline, baseline_err,
#                           blank, blank_err
                           ):
        '''
            intercept, baseline and blank should be ufloats
            
            mass spec does not propogate baseline error
        '''

        isotope = self.get_isotope(isotope)

        #in mass spec intercept is baseline corrected
        #mass spec does not propogate baseline error
        #convert baseline to scalar
        baseline = baseline.nominal_value

        intercept = intercept - baseline

        #isotope is corrected for background (blank in pychron parlance)
        isotope_value = intercept - blank

        fit = self.get_fittype(fit)

        iso_r = IsotopeResultsTable(DataReductionSessionID=data_reduction_session_id,
                                    Intercept=intercept.nominal_value,
                                    InterceptEr=intercept.std_dev(),

                                    Iso=isotope_value.nominal_value,
                                    IsoEr=isotope_value.std_dev(),

                                    Bkgd=blank.nominal_value,
                                    BkgdEr=blank.std_dev(),

                                    BkgdDetTypeID=1,

                                    Fit=fit
                                    )
        if isotope:
            isotope.results.append(iso_r)

        return isotope

    def add_data_reduction_session(self, **kw):
        drs = DataReductionSessionTable(
                                   SessionDate=func.current_timestamp()
                                   )
        self._add_item(drs)
        return drs

    def add_login_session(self, ms, **kw):

        if isinstance(ms, str):
            ms = ms.capitalize()
            system = self.get_system(ms)
            if system:
                ms = system.SpecSysN
            else:
                ms = 0

        drs = LoginSessionTable(SpecSysN=ms)
        self._add_item(drs)
        return drs

    def add_changeable_items(self, rid, drs_id):
        item = AnalysesChangeableItemsTable()
        analysis = self.get_analysis(rid)
        if analysis is not None:
            #get the lastest preferencesetid
#            sess = self.get_session()
#            q = sess.query(PreferencesTable)
#            q = q.order_by(PreferencesTable.PreferencesSetID.desc())
#            q = q.limit(1)
#            pref = q.one()

            pref = self.get_preferences_set(None)
            if pref is not None:
                pref.changeable_items.append(item)
            else:
                item.PreferencesSetID = 0
            item.AnalysisID = analysis.AnalysisID
#            analysis.changeable.append(item)

            item.DataReductionSessionID = drs_id
#            drs.changeable_items.append(item)
            self._add_item(item)

        return item

    def add_runscript(self, label, text, **kw):
        '''
            runscripttable does not autoincrement primary key
            
            uses a crc-32 of text as the RunScriptID
        '''
        crc = binascii.crc32(text)
        rs = self.get_runscript(crc)
        if rs is None:
            rs = RunScriptTable(RunScriptID=crc, Label=label, TheText=text)
            self._add_item(rs)
        return rs

#===============================================================================
# deleters
#===============================================================================
    @delete_one
    def delete_analysis(self, rid):
        return AnalysesTable, 'RID'

#==================EOF======================================================
##    def add_detector(self, detector_id, kw, sess=None):
##        '''
##        '''
###        if sess is None:
###            sess = self.session_factory()
##
###        print det_args, sess, detector_id
##        if detector_id is not None:
###            #get the detector row
##            det, sess = self.get_detector(detector_id, sess=sess)
##            #print det
##            for a in kw:
##                setattr(det, a, kw[a])
##        else:
##            det = DetectorTable(**kw)
##            sess.add(det)
##
##        return det, sess
#    def add_detector(self, args):
#        return self._add_tableitem(DetectorTable(**args))
#
#    def add_analysis_changeable(self, args, dbanalysis=None):
#        anal = self._get_dbrecord(dbanalysis, 'get_analysis')
#        if anal:
#            c = AnalysesChangeableItemsTable(**args)
#            anal.changeable = c
#            return c
#
#    def add_isotope_result(self, args, dbisotope=None):
##        if sess is None:
##            sess = self.session_factory()
#
#        iso = self._get_dbrecord(dbisotope, 'get_isotope')
#        if iso is not None:
#            iso_result = IsotopeResultsTable(**args)
#            iso.results.append(iso_result)
#            return iso_result
#
#    def add_isotope(self, args, dbanalysis=None, dbdetector=None, dbbaseline=None):
#        '''
#

#        '''
##        if sess is None:
##            sess = self.session_factory()
#
#        analysis = self._get_dbrecord(dbanalysis, 'get_analysis')
#
#        if analysis is not None:
#            detector = self._get_dbrecord(dbdetector, 'get_detector')
#            if detector is not None:
#                iso = IsotopeTable(**args)
#
#                analysis.isotopes.append(iso)
#                detector.isotopes.append(iso)
#
#                return iso
##
#    def add_peaktimeblob(self, blob, dbisotope=None):
#        iso = self._get_dbrecord(dbisotope, 'get_isotope')
#        if iso is not None:
#            pk = PeakTimeTable(PeakTimeBlob=blob)
#            iso.peak_time_series.append(pk)
#            return pk
#    def _get_tables(self):
#        return globals()
#
#    def clear_table(self, tablename):
#        sess = self.get_session()
#        try:
#            table = globals()[tablename]
#        except KeyError, e:
#            print e
#            a = None
#
#        try:
#            a = sess.query(table)
#        except Exception, e:
#            print e
#            a = None
#        if a is not None:
#            a.delete()
#
#    def get_rids(self, limit=1000):
#        '''
#        '''
##        if sess is None:
##            sess = self.session_factory()
#        sess = self.get_session()
#        q = sess.query(AnalysesTable.AnalysisID, AnalysesTable.RID)
#        p = q.limit(limit)
#        return p
#
#    def get_project(self, project):
#        '''
#        '''
#        return self._get_one(ProjectTable, dict(Project=project))
#
#    def get_araranalysis(self, aid):
#        '''
#        '''
#        return self._get_one(ArArAnalysisTable, dict(AnalysisID=aid))
#
#    def get_araranalyses(self, aid):
#        '''
#        '''
#        return self._get(ArArAnalysisTable, dict(AnalysisID=aid), func='all')

#    def get_analyses(self, **kw):
#        '''
#        '''
#        table = AnalysesTable


#        return self._get_all((AnalysesTable.RID,))
#        if sess is None:
#            sess = self.session_factory()
#        p = sess.query(AnalysesTable.RID).all()

#        return p, sess

#    def get_detector(self, did, sess=None):
#        '''
#        '''
#        return self._get_one(DetectorTable, dict(DetectorID=did))

#    def get_material(self, material, sess=None):
#        '''
#        '''
#        return self._get_one(MaterialTable, dict(Material=material))

#    def get_sample(self, sample, sess=None):
#        '''
#        '''
#        return self._get_one(SampleTable, dict(Sample=sample))


#    def get_isotopes(self, aid, sess=None):
#        '''
#        '''
#        sess = self.get_session()
#        isos = sess.query(IsotopeTable).filter_by(AnalysisID=aid).all()
#        return isos

#    def get_irradiation_position(self, irp):
#        return self._get_one(IrradiationPositionTable, dict(IrradPosition=irp))

#    def get_peaktimeblob(self, isoid, sess=None):
#        '''
#        '''
#        return self._get_one(PeakTimeTable, dict(IsotopeID=isoid))
#        if sess is None:
#            sess = self.session_factory()
#        try:
#            q = sess.query(PeakTimeTable)
#            ptb = q.filter_by(IsotopeID=IsotopeID).one()
#        except:
#            ptb = None
#        return ptb, sess

#    def _get_dbrecord(self, record_or_id, func):
#        '''
#        '''
#        if record_or_id is not None:
#            if isinstance(record_or_id, (long, int)):
#                record_or_id = getattr(self, func)(record_or_id)
#
#        return record_or_id

##    def add_peaktimeblob(self, iso_id, blob, dbisotope=None, sess=None):
##        '''
##        '''
###        if sess is None:
###            sess = self.session_factory()
##        
##        isotope = dbisotope
##        if dbisotope is None:
##            isotope, sess = self.get_isotope(iso_id, sess=sess)
##
##        if isotope is not None:
##            pk = PeakTimeTable(PeakTimeBlob=blob)
##            isotope.peak_time_series.append(pk)
##
##        return sess

#    def add_project(self, args):
#        '''
#        '''
#        p = self.get_project(args['Project'])
#        if p is None:
#            return self._add_tableitem(ProjectTable(**args))
##        if sess is None:
##            sess = self.session_factory()
#
##        p, sess = self.get_project(args['Project'], sess=sess)
##        if p is None:
##        p = ProjectTable(**args)
##        sess.add(p)
##        return p
#
#    def add_sample(self, args, project=None):
#        '''
#        '''
#        s = self.get_sample(args['Sample'])
#        if s is None:
#            p = self.get_project(project)
##            self._add_tableitem(SampleTable(**args))
#            if p is not None:
#                s = SampleTable(**args)
#                p.samples.append(s)
#
#        return s
##        if sess is None:
##            sess = self.session_factory()
##        #check to see if sample already exists
##        s, sess = self.get_sample(args['Sample'], sess=sess)
##        if s is None:
##            p, sess = self.get_project(args['Project'], sess=sess)
##
##            s = SampleTable(**args)
##            p.samples.append(s)
##            sess.add(s)
##        return s, sess
#
#    def add_material(self, args):
#        '''
#
#        '''
##        if sess is None:
##            sess = self.session_factory()
##        m = MaterialTable(**args)
##        sess.add(m)
##        return m, sess
#        return self._add_tableitem(MaterialTable(**args))
#
##    def add_irradiation_position(self, args):
##        '''
##        '''
##       
##
##        ip, sess = self.get_irradiation_position((args['IrradiationLevel'],
##                                                 args['HoleNumber']),
##                                                 sess=sess)
##        if ip is None:
##            material, sess = self.get_material(args['Material'], sess=sess)
##            #if the material doesnt exist add it
##            if material is None:
##                material, sess = self.add_material(dict(Material=args['Material']),
##                                                   sess=sess)
##            sample, sess = self.get_sample(args['Sample'], sess=sess)
##            args.pop('Sample')
##
##            ip = IrradiationPositionTable(**args)
##            sample.irradpositions.append(ip)
##            material.irradpositions.append(ip)
##
##        return ip, sess
#
#    def debug_delete_table(self, table, sess=None):
#        def _delete_table(t):
#            rows = sess.query(t).all()
#            for r in rows:
#                sess.delete(r)
#
#        if sess is None:
#            sess = self.session_factory()
#
#        if isinstance(table, list):
#            for ti in table:
#                _delete_table(ti)
#        else:
#            _delete_table(table)

#    def get_data_reduction_session_dates(self, data_reduction_id_list, sess = None):
#        if sess is None:
#            sess = Session()
#        p = sess.query(DataReductionSessionTable.SessionDate).filter(
#                                DataReductionSessionTable.DataReductionSessionID.in_(data_reduction_id_list)).order_by(DataReductionSessionTable.DataReductionSessionID).all()
#        return p, sess
#    def get_discrimination(self, detector_ids, sess = None):
#        if sess is None:
#            sess = Session()
#        p = sess.query(DetectorTable.DetectorID, DetectorTable.Disc).filter(DetectorTable.DetectorID.in_(detector_ids)).all()
#        return p, sess
#    def get_isotopes(self, iso_ids, sess = None):
#        if sess is None:
#            sess = Session()
#        p = sess.query(IsotopeResultsTable.IsotopeID,
#                     IsotopeResultsTable.Intercept,
#                     IsotopeResultsTable.Bkgd).filter(IsotopeResultsTable.IsotopeID.in_(iso_ids)).\
#        order_by(IsotopeResultsTable.DataReductionSessionID).\
#                     order_by(IsotopeResultsTable.IsotopeID).all()
#        return p, sess
#    def get_isotope_ids(self, aids, sess = None):
#        if sess is None:
#            sess = Session()
#
#        p = sess.query(IsotopeTable.IsotopeID,
#                    IsotopeTable.Label,
#                    IsotopeTable.DetectorID
#                     ).filter(IsotopeTable.AnalysisID.in_(aids)).all()
#        return p, sess
#    def get_analysis_by_ln(self, ln, sess = None):
#        '''
#        like syntax
#        % allows you to match any string of any length (including zero length)
#
#        _ allows you to match on a single character
#        '''
#        if sess is None:
#            sess = Session()
#
#        p = sess.query(AnalysesTable.AnalysisID,
#                     AnalysesTable.RID).filter(AnalysesTable.RID.like(ln)).all()
#        return p, sess
#    def get_analysis_by_rid(self, rid, sess = None):
#        if sess is None:
#            sess = Session()
#        p = sess.query(AnalysesTable.AnalysisID).filter_by(RID = rid).first()
#        return p, sess
#    def get_araranalysis_rids(self, run_list):
#        sess = Session()
#        p = sess.query(AnalysesTable.AnalysisID,
#                     AnalysesTable.RID
#                     ).filter(AnalysesTable.RID.in_(run_list)).all()
#        return p, sess
#    def get_araranalyses(self, aid_list, sess = None):
#        if sess is None:
#            sess = Session()
#        p = sess.query(ArArAnalysisTable.AnalysisID,
#                     ArArAnalysisTable.DataReductionSessionID,
#                     ArArAnalysisTable.Tot40,
#                     ArArAnalysisTable.Tot39,
#                     ArArAnalysisTable.Tot38,
#                     ArArAnalysisTable.Tot37,
#                     ArArAnalysisTable.Tot36,
#                     ArArAnalysisTable.Tot40Er,
#                     ArArAnalysisTable.Tot39Er,
#                     ArArAnalysisTable.Tot38Er,
#                     ArArAnalysisTable.Tot37Er,
#                     ArArAnalysisTable.Tot36Er,
#                     ArArAnalysisTable.JVal,
#                     ArArAnalysisTable.JEr,
#
#                     ).filter(ArArAnalysisTable.AnalysisID.in_(aid_list)).order_by(ArArAnalysisTable.DataReductionSessionID).\
#                     order_by(ArArAnalysisTable.AnalysisID).all()
#        return p, sess
#    def get_araranalysis(self,a_id,sess=None):
#        if sess is None:
#            sess=Session()
#        p=sess.query(ArArAnalysisTable.Tot40,
#                     ArArAnalysisTable.Tot39,
#                     ArArAnalysisTable.Tot38,
#                     ArArAnalysisTable.Tot37,
#                     ArArAnalysisTable.Tot36,
#                     ArArAnalysisTable.Tot40Er,
#                     ArArAnalysisTable.Tot39Er,
#                     ArArAnalysisTable.Tot38Er,
#                     ArArAnalysisTable.Tot37Er,
#                     ArArAnalysisTable.Tot36Er,
#                     ArArAnalysisTable.DataReductionSessionID,
#                     ).filter_by(AnalysisID=a_id).all()
#        return p,sess
if __name__ == '__main__':
    from src.helpers.logger_setup import logging_setup
    logging_setup('ia')
    ia = MassSpecDatabaseAdapter()
    ia.connect()

#    ia.selector_factory()
    dbs = ia.selector
    dbs.load_recent()

    dbs.configure_traits()
