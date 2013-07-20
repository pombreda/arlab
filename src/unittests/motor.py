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
from traits.api import HasTraits, Int
from traitsui.api import View, Item
import unittest
from src.hardware.linear_mapper import LinearMapper
from src.hardware.core.motion.motion_profiler2 import MotionProfiler as MotionProfiler2
from src.hardware.core.motion.motion_profiler import MotionProfiler
#============= standard library imports ========================
#============= local library imports  ==========================


class MotionProfilerTest(unittest.TestCase):
    def setUp(self):
        self.mp = MotionProfiler()
        self.mp2 = MotionProfiler2()

    def testCheckParameters2(self):
        displacement = 5
        mv, mac, mdc = 0.1, 10, 10
        args2 = self.mp2.calculate_corrected_parameters(displacement,
                                                        mac, mdc)
        print args2
        print self.mp2.calculate_transit_parameters(displacement, *args2)
        args1 = self.mp.calculate_corrected_parameters(displacement,
                                                       mv, mac, mdc)
#         print nv, na, nd
        print args1
        print self.mp.calculate_transit_parameters(displacement, *args1)
        self.assertTupleEqual(args1, args2)

class LinearMapperTest(unittest.TestCase):
    def setUp(self):
        self.mapper = LinearMapper()

        self.mapper.low_data = 2
        self.mapper.high_data = 6
        self.mapper.low_step = 0
        self.mapper.high_step = 9500
    def testMapData(self):

        m = self.mapper

        # map from steps to data
        ds = 0
        steps = m.map_data(ds)
        self.assertEqual(steps, 2)

        ds = 9500
        steps = m.map_data(ds)
        self.assertEqual(steps, 6)
#
    def testMapSteps(self):
        # map from data to steps
        m = self.mapper

        ds = 2
        steps = m.map_steps(ds)
        self.assertEqual(steps, 0)

        ds = 6
        steps = m.map_steps(ds)
        self.assertEqual(steps, 9500)

        ds = 4
        steps = m.map_steps(ds)
        self.assertEqual(steps, 9500 / 2.)



#============= EOF =============================================
