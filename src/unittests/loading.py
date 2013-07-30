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
from traits.api import HasTraits
from traitsui.api import View, Item
import unittest
from src.experiment.loading.load_task import LoadingTask
from src.unittests.database import get_test_database
from src.experiment.loading.loading_manager import LoadingManager
#============= standard library imports ========================
#============= local library imports  ==========================

class LoadingTest(unittest.TestCase):
    def setUp(self):
#         self.t = LoadingTask()
        db = get_test_database().db
        lm = LoadingManager(db=db)

#         lm.irradiation = 'NM-251'
#         lm.level = 'H'
        self.t = LoadingTask(manager=lm)

    def testSave(self):
        lm = self.t.manager
        c = lm.make_canvas('1401')

        self.t.canvas = c
        self.t.save_loading()

#============= EOF =============================================