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
from traits.api import Instance, Button
from traitsui.api import View, Item, Group, HGroup, VGroup

#============= standard library imports ========================
#import csv
import struct
#import os
#from pylab import transpose
from numpy import array
#============= local library imports  ==========================
#from src.database.nmgrl_database_adapter import NMGRLDatabaseAdapter
#from src.loggable import Loggable
#from src.helpers.paths import data_dir
#from src.data_processing.regression.ols import OLS
from src.loggable import Loggable
from src.database.adapters.massspec_database_adapter import MassSpecDatabaseAdapter
from src.regression.ols_regressor import PolynomialRegressor
from src.regression.mean_regressor import MeanRegressor
from uncertainties import ufloat
from src.experiment.info_blob import encode_infoblob

mkeys = ['l2 value', 'l1 value', 'ax value', 'h1 value', 'h2 value']

'''
following information is necessary


'''

RUN_TYPE_DICT = dict(Unknown=1, Air=2, Blank=5)
SAMPLE_DICT = dict(Air=2, Blank=1)
ISO_LABELS = dict(H1='Ar40', AX='Ar39', L1='Ar38', L2='Ar37', CDD='Ar36')

DEBUG = True

class MassSpecDatabaseImporter(Loggable):
    db = Instance(MassSpecDatabaseAdapter)
    test = Button
    sample_loading_id = None
    data_reduction_session_id = None
    login_session_id = None

    def _test_fired(self):
        import numpy as np
        self.db.connect()
        xbase = np.linspace(430, 580, 150)
        ybase = np.zeros(150)
        cddybase = np.zeros(150)
#        ybase = np.random.random(150)
#        cddybase = np.random.random(150) * 0.001
        base = [zip(xbase, ybase),
                zip(xbase, ybase),
                zip(xbase, ybase),
                zip(xbase, ybase),
                zip(xbase, cddybase),
                ]

        xsig = np.linspace(20, 420, 410)
        y40 = np.ones(410) * 680
        y39 = np.ones(410) * 107
        y38 = np.zeros(410) * 1.36
        y37 = np.zeros(410) * 0.5
        y36 = np.ones(410) * 0.001

        sig = [zip(xsig, y40),
               zip(xsig, y39),
               zip(xsig, y38),
               zip(xsig, y37),
               zip(xsig, y36),

               ]


        regbs = MeanRegressor(xs=xbase, ys=ybase)
        cddregbs = MeanRegressor(xs=xbase, ys=cddybase)
        reg = PolynomialRegressor(xs=xsig, ys=y40, fit='linear')

        reg1 = PolynomialRegressor(xs=xsig, ys=y39, fit='linear')
        reg2 = PolynomialRegressor(xs=xsig, ys=y38, fit='linear')
        reg3 = PolynomialRegressor(xs=xsig, ys=y37, fit='linear')
        reg4 = PolynomialRegressor(xs=xsig, ys=y36, fit='linear')

        keys = [
                ('H1', 'Ar40'),
                ('AX', 'Ar39'),
                ('L1', 'Ar38'),
                ('L2', 'Ar37'),
                ('CDD', 'Ar36'),

                ]

        regresults = (dict(
                          Ar40=ufloat((reg.predict(0), reg.predict_error(0))),
                          
                          Ar39=ufloat((reg1.predict(0), reg1.predict_error(0))),
                          
                          Ar38=ufloat((reg2.predict(0), reg2.predict_error(0))),
                          
                          Ar37=ufloat((reg3.predict(0), reg3.predict_error(0))),
                          
                          Ar36=ufloat((reg4.predict(0), reg4.predict_error(0))),
                          
                          ),
                      dict(
                          Ar40=ufloat((regbs.predict(0), regbs.predict_error(0))),
                          Ar39=ufloat((regbs.predict(0), regbs.predict_error(0))),
                          Ar38=ufloat((regbs.predict(0), regbs.predict_error(0))),
                          Ar37=ufloat((regbs.predict(0), regbs.predict_error(0))),
                          Ar36=ufloat((cddregbs.predict(0), cddregbs.predict_error(0)))
                          ))
        blanks = [ufloat((1, 0.1)),
                  ufloat((0.1, 0.001)),
                  ufloat((0.01, 0.001)),
                  ufloat((0.01, 0.001)),
                  ufloat((0.00001, 0.0001)),

                  ]
        fits=(
              dict(zip(['Ar40','Ar39','Ar38','Ar37','Ar36'],
                       ['Linear','Linear','Linear','Linear','Linear'])),
              dict(zip(['Ar40','Ar39','Ar38','Ar37','Ar36'],
                       ['Average Y','Average Y','Average Y','Average Y','Average Y'])))
        mass_spectrometer = 'obama'
        extract_device = 'Laser Furnace'
        extract_value = 10
        position = 1
        duration = 10
        first_stage_delay = 0
        second_stage_delay = 30
        tray = '100-hole'

        self.add_login_session(mass_spectrometer)
        self.add_data_reduction_session()
        self.add_sample_loading(mass_spectrometer, tray)

        self.add_analysis('4318', '30', '', '4318',
                          base, sig, blanks,
                          keys,
                          regresults,
                          fits,

                          mass_spectrometer,
                          extract_device,
                          position,
                          extract_value, #power requested
                          extract_value, #power achieved

                          duration, #total extraction
                          duration, #time at extract_value

                          first_stage_delay,
                          second_stage_delay,
                          )

    def traits_view(self):
        v = View(Item('test', show_label=False))
        return v

    def _db_default(self):
        db = MassSpecDatabaseAdapter(kind='mysql',
#                                     host='localhost',
#                                     username='root',
#                                     password='Argon',
#                                     name='massspecdata_import'
                                     host='129.138.12.131',
                                     username='massspec',
                                     password='DBArgon',
                                     name='massspecdata_isotopedb'
                                     )
#        db.connect()

        return db

    def add_sample_loading(self, ms, tray):
        if self.sample_loading_id is None:
            db = self.db
            sl = db.add_sample_loading(ms, tray)
            db.flush()
            self.sample_loading_id=sl.SampleLoadingID

    def add_login_session(self, ms):
        if self.login_session_id is None:
            db = self.db
            ls = db.add_login_session(ms)
            db.flush()
            self.login_session_id=ls.LoginSessionID

    def add_data_reduction_session(self):
        if self.data_reduction_session_id is None:
            db = self.db
            dr = db.add_data_reduction_session()
            db.flush()
            self.data_reduction_session_id=dr.DataReductionSessionID
            
            
    def add_analysis(self, rid, aliquot, step, irradpos,
                     baselines, signals, blanks, keys,
#                     regression_results,
                     intercepts,
                     fits,
                     spectrometer,
                     heating_device_name,
                     position,
                     power_requested,
                     power_achieved,
                     duration,
                     duration_at_request,
                     first_stage_delay,
                     second_stage_delay
                     ):
        '''
            
        '''
        if rid.startswith('B'):
            runtype = 'Blank'
            irradpos = -1
        elif rid.startswith('A'):
            runtype = 'Air'
            irradpos = -2
        else:
            runtype = 'Unknown'

        db = self.db
        #=======================================================================
        # add analysis
        #=======================================================================
        #save spectrometer, cleanup, position, heating device

        analysis = db.add_analysis(rid,
                                   aliquot,
                                   step,
                                   irradpos,
                                   RUN_TYPE_DICT[runtype],

                                   HeatingItemName=heating_device_name,
                                   PwrAchieved_Max=power_achieved,
                                   PwrAchievedSD=0,
                                   FinalSetPwr=power_requested,
                                   TotDurHeating=duration,
                                   TotDurHeatingAtReqPwr=duration_at_request,
                                   FirstStageDly=first_stage_delay,
                                   SecondStageDly=second_stage_delay
                                   )
        
        if self.sample_loading_id:
            analysis.SampleLoadingID=self.sample_loading_id
                
#            self.sample_loading.analyses.append(analysis)

        if self.login_session_id:
            analysis.LoginSessionID=self.login_session_id
#            ls=self.db.get_login_session(self.login_session_id)
#            if ls:
#                ls.analyses.append(analysis)

        db.add_analysis_positions(analysis, position)
#        drs = db.add_data_reduction_session()

        #=======================================================================
        # add changeable items
        #=======================================================================
        print self.data_reduction_session_id
        item = db.add_changeable_items(analysis, self.data_reduction_session_id)
        db.flush()
        analysis.ChangeableItemsID = item.ChangeableItemsID

        add_results = True

        signal_dict, baseline_dict = intercepts
        signal_fits, baseline_fits = fits
        for ((det, isok), si, bi, ublank) in zip(keys, signals, baselines, blanks):

            #===================================================================
            # isotopes
            #===================================================================
            iso = db.add_isotope(analysis, det, isok)
            #===================================================================
            # baselines
            #===================================================================
            tb, vb = zip(*bi)
            blob = self._build_timeblob(tb, vb)
            label = '{} Baseline'.format(det.upper())
            ncnts = len(tb)
            db.add_baseline(blob, label, ncnts, iso)

#            baseline = array(vb).mean()
#            baseline = regression_results['{}bs'.format(det)].coefficients[-1]
#            baseline_err = regression_results['{}bs'.format(det)].coefficient_errors[-1]
            baseline = baseline_dict[isok]

            infoblob = self._make_infoblob(baseline.nominal_value, baseline.std_dev())
            db.add_baseline_changeable_item(self.data_reduction_session_id, baseline_fits[isok], infoblob)
            #===================================================================
            # peak time
            #===================================================================
            '''
                build two blobs
                blob 1 PeakTimeBlob
                x, y - mean(baselines)
                
                blob 2
                y list
            '''

            tb, vb = zip(*si)
            vb = array(vb) - baseline.nominal_value
            blob1 = self._build_timeblob(tb, vb)

            blob2 = [struct.pack('>f', float(v)) for v in vb]
            db.add_peaktimeblob(blob1, blob2, iso)

            if add_results:
#                i = regression_results[det].coefficients[-1]
#                ierr = regression_results[det].coefficient_errors[-1]
#                fit = regression_results[det].fit
                intercept = signal_dict[isok]
                fit = signal_fits[isok]
                #in mass spec the intercept is alreay baseline corrected
                #mass spec also doesnt propograte baseline errors

                db.add_isotope_result(iso, self.data_reduction_session_id,
#                                      ufloat((i, ierr)),
                                      intercept,
                                      baseline,
#                                      ufloat((baseline, baseline_err)),
                                      ublank,
                                      fit
                                      )



        db.commit()

    def _build_timeblob(self, t, v):
        '''
        '''
        blob = ''
        for ti, vi in zip(t, v):
            blob += struct.pack('>ff', float(vi), float(ti))
        return blob

    def _make_infoblob(self, baseline, baseline_err):
        rpts = 0
        pos_segments = []
        bs_segments = [1.0000000200408773e+20]
        bs_seg_params = [[baseline, 0, 0, 0]]
        bs_seg_errs = [baseline_err]
        return encode_infoblob(rpts, pos_segments, bs_segments, bs_seg_params, bs_seg_errs)

if __name__ == '__main__':
    from src.helpers.logger_setup import logging_setup
    
    logging_setup('db_import')
    d = MassSpecDatabaseImporter()

    d.configure_traits()

#============= EOF ====================================
