#============= enthought library imports =======================
from data_manager import DataManager

#============= standard library imports ========================
import csv
from src.helpers.datetime_tools import generate_timestamp
#============= local library imports  ==========================
class CSVDataManager(DataManager):
    '''
    '''

    def write_metadata(self, md, frame_key = None):

        sline = ['#<metadata>===================================================']
        eline = ['#</metadata>===================================================']
        data = [sline] + md + [eline]
        self.write_to_frame(data, frame_key)

    def write_to_frame(self, datum, frame_key = None):

        if frame_key is None:
            frame_key = self._current_frame

        frame = self._get_frame(frame_key)
        if frame is not None:
            self.new_writer(frame, datum)

    def new_writer(self, p, datum, append = True):
        '''

        '''
        mode = 'w'
        if append:
            mode = 'a'
        with open(p, mode) as f:
            writer = csv.writer(f)
            if isinstance(datum[0], (list, tuple)):
                writer.writerows(datum)
            else:
                writer.writerow(datum)

    def add_time_stamped_value(self, value, frame_key):
        '''

        '''
        frame = self._get_frame(frame_key)
        if frame is not None:
            datum = (generate_timestamp(), value)
            self.new_writer(frame, datum)

    def _get_frame(self, key):
        if key in self.frames:
            return self.frames[key]

#============= EOF ====================================
