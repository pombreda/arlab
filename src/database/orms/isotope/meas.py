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
from sqlalchemy import Column, Integer, String, \
     ForeignKey, BLOB, Float, Time, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import func
import uuid

#============= local library imports  ==========================
from src.database.orms.isotope.util import foreignkey, stringcolumn
from src.database.core.base_orm import BaseMixin, NameMixin

from util import Base

class meas_SignalTable(Base, BaseMixin):
    data = Column(BLOB)
    isotope_id = foreignkey('meas_IsotopeTable')
#    detector_id = foreignkey('gen_DetectorTable')


class meas_AnalysisTable(Base, BaseMixin):
    lab_id = foreignkey('gen_LabTable')
    extraction_id = foreignkey('meas_ExtractionTable')
    measurement_id = foreignkey('meas_MeasurementTable')
    experiment_id = foreignkey('meas_ExperimentTable')
    import_id = foreignkey('gen_ImportTable')
    user_id = foreignkey('gen_UserTable')

    uuid = stringcolumn(40, default=lambda:str(uuid.uuid4()))
    analysis_timestamp = Column(DateTime, default=func.now())
    endtime = Column(Time)
    status = Column(Integer, default=0)
    aliquot = Column(Integer)
    step = stringcolumn(10)
    comment = Column(BLOB)

    #tag = Column(String(40), ForeignKey('proc_TagTable.name'))

    # meas relationships
    isotopes = relationship('meas_IsotopeTable', backref='analysis',
#                             lazy='subquery'
                            )
    peak_center = relationship('meas_PeakCenterTable', backref='analysis', uselist=False)

    # proc relationships
    blanks_histories = relationship('proc_BlanksHistoryTable', backref='analysis')
    blanks_sets = relationship('proc_BlanksSetTable', backref='analysis')

    backgrounds_histories = relationship('proc_BackgroundsHistoryTable', backref='analysis')
    backgrounds_sets = relationship('proc_BackgroundsSetTable', backref='analysis')

    detector_intercalibration_histories = relationship('proc_DetectorIntercalibrationHistoryTable',
                                                       backref='analysis')
    detector_intercalibration_sets = relationship('proc_DetectorIntercalibrationSetTable',
                                                   backref='analysis')

    detector_param_histories = relationship('proc_DetectorParamHistoryTable',
                                                   backref='analysis')

    fit_histories = relationship('proc_FitHistoryTable',
                                  backref='analysis')

    selected_histories = relationship('proc_SelectedHistoriesTable',
                                      backref='analysis', uselist=False)
    arar_histories = relationship('proc_ArArHistoryTable', backref='analysis')
#     figure_analyses = relationship('proc_FigureAnalysisTable', backref='analysis')
    notes = relationship('proc_NotesTable', backref='analysis')
    monitors = relationship('meas_MonitorTable', backref='analysis')


class meas_ExperimentTable(Base, NameMixin):
    analyses = relationship('meas_AnalysisTable', backref='experiment')


class meas_ExtractionTable(Base, BaseMixin):
#    position = Column(Integer)
    extract_value = Column(Float)
    extract_duration = Column(Float)
    cleanup_duration = Column(Float)
#    experiment_blob = Column(BLOB)
    weight = Column(Float)
    sensitivity_multiplier = Column(Float)
    is_degas = Column(Boolean)

    sensitivity_id = foreignkey('gen_SensitivityTable')
    extract_device_id = foreignkey('gen_ExtractionDeviceTable')
    script_id = foreignkey('meas_ScriptTable')
    experiment_blob_id = foreignkey('meas_ScriptTable')
    image_id = foreignkey('med_ImageTable')

    analyses = relationship('meas_AnalysisTable', backref='extraction')
    positions = relationship('meas_PositionTable', backref='extraction')
    snapshots = relationship('med_SnapshotTable', backref='extraction')


class meas_PositionTable(Base, BaseMixin):
    position = Column(Integer)
    x = Column(Float)
    y = Column(Float)
    z = Column(Float)

    is_degas = Column(Boolean)
    extraction_id = foreignkey('meas_ExtractionTable')
    load_identifier = Column(String(80), ForeignKey('loading_LoadTable.name'))


class meas_SpectrometerParametersTable(Base, BaseMixin):
#    measurement_id = foreignkey('meas_MeasurementTable')
    extraction_lens = Column('extraction_lens', Float)
    ysymmetry = Column(Float)
    zsymmetry = Column(Float)
    zfocus = Column(Float)
    hash = Column(String(32))
    measurements = relationship('meas_MeasurementTable', backref='spectrometer_parameters')

class meas_SpectrometerDeflectionsTable(Base, BaseMixin):
    detector_id = foreignkey('gen_DetectorTable')
    measurement_id = foreignkey('meas_MeasurementTable')
    deflection = Column(Float)

class meas_IsotopeTable(Base, BaseMixin):
    molecular_weight_id = foreignkey('gen_MolecularWeightTable')
    analysis_id = foreignkey('meas_AnalysisTable')
    detector_id = foreignkey('gen_DetectorTable')
    kind = stringcolumn()

    signals = relationship('meas_SignalTable',
#                            lazy='subquery',
                           backref='isotope')
    fits = relationship('proc_FitTable',
#                         lazy='subquery',
                        backref='isotope')
    results = relationship('proc_IsotopeResultsTable',
#                            lazy='subquery',
                           backref='isotope')

class meas_MeasurementTable(Base, BaseMixin):
    mass_spectrometer_id = foreignkey('gen_MassSpectrometerTable')
    analysis_type_id = foreignkey('gen_AnalysisTypeTable')
    spectrometer_parameters_id = foreignkey('meas_SpectrometerParametersTable')
    script_id = foreignkey('meas_ScriptTable')
#    spectrometer_parameters = relationship('meas_SpectrometerParametersTable',
#                                         backref='measurement',
#                                         uselist=False
#                                         )
    analyses = relationship('meas_AnalysisTable', backref='measurement')
    deflections = relationship('meas_SpectrometerDeflectionsTable', backref='measurement')


class meas_PeakCenterTable(Base, BaseMixin):
    center = Column(Float(32))
    points = Column(BLOB)
    analysis_id = foreignkey('meas_AnalysisTable')

class meas_ScriptTable(Base, NameMixin):
    hash = Column(String(32))
    blob = Column(BLOB)
    measurements = relationship('meas_MeasurementTable', backref='script')
    extractions = relationship('meas_ExtractionTable',
                               primaryjoin='meas_ExtractionTable.script_id==meas_ScriptTable.id',
                               backref='script')

    experiments = relationship('meas_ExtractionTable',
                               primaryjoin='meas_ExtractionTable.experiment_blob_id==meas_ScriptTable.id',
                               backref='experiment')

class meas_MonitorTable(Base, NameMixin):
    data = Column(BLOB)

    parameter = stringcolumn()
    criterion = stringcolumn()
    comparator = stringcolumn()
    action = stringcolumn()
    tripped = Column(Boolean)

    analysis_id = foreignkey('meas_AnalysisTable')



# class meas_PositionsTable(Base, BaseMixin):
#     load_identifier = Column(String(80), ForeignKey('loading_LoadTable.name'))
#     extraction_id = foreignkey('meas_ExtractionTable')
#     is_degas = Column(Boolean)
#     position = Column(Integer)
#============= EOF =============================================
