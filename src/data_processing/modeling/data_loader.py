'''
Copyright 2011 Jake Ross

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
#============= enthought library imports =======================
from traits.api import Str

#============= standard library imports ========================
import os
import csv
#============= local library imports  ==========================
from src.loggable import Loggable
from src.helpers.logger_setup import setup
TAB = chr(9)
LABTABLE = {"temp":67, "time":73, "39Armol":80, "er39Ar":81, "Age":19, "erAge":20, "terAge":21, "SenseMol":26} # autoupdate column numbers for each header of interest
REQUIRED_FILES = ['logr.samp', 'logr.dat', 'arr.samp', 'arr.dat']

class DataLoader(Loggable):
    '''
    '''
    root = Str
    def _open_reader(self, name, root=None, delimiter=TAB):
        '''
            
        '''

        if root is None:
            root = self.root
        path = os.path.join(root, name)

        if os.path.isfile(path):

            f = open(path, 'U')
            return f, csv.reader(f, delimiter=delimiter, skipinitialspace=True)
        else:
            self.warning('Path does not exist {}'.format(path))
            return None, None

    def _open_writer(self, name, delimiter=TAB):
        '''
          
        '''
        f = open(name, 'wb')
        return f, csv.writer(f, delimiter=delimiter)

    def load_autoupdate(self, path, tempoffset, timeoffset):
        '''
        '''
        samples, names = self.split_autoupdate(path)
        self.info('''split autoupdate file
                                    number samples = {}
                                    names = {}
                                    tempoffset={} (C)
                                    timeoffset={} (min)
                            '''.format(len(samples), ', '.join(names), tempoffset, timeoffset),
                            decorate=False)
        for i in range(len(samples) - 1):
            self.info('loading sample {}'.format(names[i]))
            self.load_sample(path, samples[i], samples[i + 1], names[i], tempoffset, timeoffset)

    def split_autoupdate(self, path):
        '''
        '''
        self.info('Splitting autoupdate {}'.format(path))
        root, name = os.path.split(path)
        f, reader = self._open_reader(name, root)

        cut_boundaries = []
        names = []
        RunID2 = ''
        if reader is not None:
            for i, row in enumerate(reader):
                if len(row) > 0 and len(row[0]) > 0 and i > 0:
                    RunID1 = row[0]
                    if RunID1[:8] != RunID2[:8]:
                        cut_boundaries.append(i)
                        names.append(RunID1[:8])
                        RunID2 = RunID1

                elif len(row) == 0:
                    cut_boundaries.append(i)
                    break
            f.close()
        return cut_boundaries, names

    def load_sample(self, path, TopRow, BottomRow, name, tempoffset, timeoffset):
        '''
        '''
        self.info('loading sample {}'.format(path))
        root, p = os.path.split(path)
        f, reader = self._open_reader(p, root=root)
        if reader is None:
            return

        path, _ext = os.path.splitext(path)
        path += '_data'
        if not os.path.exists(path):
            os.mkdir(path)
            self.info('made data directory {}'.format(path))
        cur_dir = os.path.join(path, name)
        if not os.path.exists(cur_dir):
            os.mkdir(cur_dir)
            self.info('made sample directory {}'.format(path))

        total_39 = 0
        IgnoreLines = 0
        TopRowIgnore = TopRow + IgnoreLines
        for i, row in enumerate(reader):
            try:
                a = row[LABTABLE["Age"]]
                age = float(a)
                if age < 0:
                    self.info('Skipping negative age {}'.format(age))
                    continue
            except ValueError:
                self.info('Invalid age {}'.format(a))
                continue
            except IndexError:
                self.info('Skipping row {} {}'.format(i, row))
                continue

            if TopRowIgnore <= i < BottomRow:
                total_39 = total_39 + float(row[LABTABLE["39Armol"]])

        f.close()

        f, reader = self._open_reader(p, root=root)
        op = os.path.join(cur_dir, '{}.in'.format(name))
        wf, writer = self._open_writer(op)
        CumAr39 = 0
        sensitivity = 0
        for i, row in enumerate(reader):
            if len(row) <= 4:
                continue
            if TopRowIgnore <= i < BottomRow:
                try:
                    age = float(row[LABTABLE["Age"]])
                except ValueError:
                    self.info('Invalid age {}'.format(a))
                    continue

                if age > 0:
                    if sensitivity == 0:
                        sensitivity = float(row[LABTABLE["SenseMol"]]) / float(row[LABTABLE["39Armol"]])

                    CumAr39 += float(row[LABTABLE["39Armol"]])
                    nrow = []
                    nrow.append(int(i - TopRowIgnore + 1))
                    nrow.append(int(row[LABTABLE["temp"]]) - tempoffset)
                    nrow.append(float(row[LABTABLE["time"]]) / 60 - timeoffset)
                    nrow.append(float(row[LABTABLE["39Armol"]]) * sensitivity)
                    nrow.append(float(row[LABTABLE["er39Ar"]]) * sensitivity)
                    nrow.append(CumAr39 / total_39 * 100)

                    nrow.append(age)
                    nrow.append(float(row[LABTABLE["erAge"]]))
                    nrow.append(float(row[LABTABLE["terAge"]]))
                    nrow.append(age)
                    nrow.append(float(row[LABTABLE["erAge"]]))

                    writer.writerow(nrow)
                else:
                    self.info("Negative age removed from file {}.in".format(name))


        self.info('finished writing to {}'.format(op))
        wf.close()
        f.close()

    def load_spectrum(self):
        '''
        '''
        self.info('load spectrum')
        f, reader = self._open_reader('age.in', delimiter=' ')
        if reader is None:
            return [], [], 0, 0

        age = []
        ar39 = []
        for row in reader:
            ar39.append(float(row[0]))
            age.append(float(row[1]))

            ar39.append(float(row[0]))
            age.append(float(row[1]))
        f.close()

        f, reader = self._open_reader('age-sd.smp', delimiter=' ')
        if reader is None:
            return
        age_err = []
        ar39_err = []
        for row in reader:
            ar39_err.append(float(row[0]))
            age_err.append(float(row[1]))

        f.close()
        return ar39[:-1], age[1:], ar39_err, age_err

    def load_arrhenius(self, name):
        '''
        '''
        self.info('load arrhenius')
        inv_temp = []
        log_d = []
        f, reader = self._open_reader(name, delimiter='\t')
        if reader is not None:
            for row in reader:
                if '&' not in row:
                    inv_temp.append(float(row[0]))
                    log_d.append(float(row[1]))

            f.close()
        return inv_temp, log_d

    def load_cooling_history(self):
        '''
        '''
        self.info('load cooling history')
        f, reader = self._open_reader('confmed.dat', delimiter=' ')

        if reader is None:
            return None

        age = []
        low_conf = []
        high_conf = []

        for row in reader:
            age.append(float(row[0]))
            low_conf.append(float(row[1]))
            high_conf.append(float(row[2]))
        f.close()
        return age, low_conf, high_conf

    def load_logr_ro(self, name):
        '''
        '''
        self.info('load log r/ro')

        f, reader = self._open_reader(name, delimiter=' ')
        if reader is None:
            return None

        logr = []
        logr39 = []
        for row in reader:
            if '&' not in row:
                logr.append(float(row[0]))
                logr39.append(float(row[1]))
        f.close()
        return logr, logr39

    def validate_data_dir(self, d):
        '''
        '''

#        for a in REQUIRED_FILES:
#            p = os.path.join(d, a)
#            if not os.path.isfile(p):
#                return False

        return True

if __name__ == '__main__':
    setup('dataloader')
    d = DataLoader()
    path = '/Users/Ross/Pychrondata_beta/data/modeling/ShapFurnace.txt'
    d.load_autoupdate(path, 0, 0)
#============= EOF ====================================
