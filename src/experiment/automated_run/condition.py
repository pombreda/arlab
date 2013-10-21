#===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import HasTraits, Str, Either, Float, Int, Callable, Bool
from uncertainties import AffineScalarFunc

#============= standard library imports ========================
#============= local library imports  ==========================
class AutomatedRunCondition(HasTraits):
    attr = Str
    comp = Str
    value = Either(Float, Int)
    start_count = Int
    frequency = Int
    message = Str
    def __init__(self, attr, comp, value,
                 start_count=0,
                 frequency=10,
                  *args, **kw):
        self.attr = attr
        self.comp = comp
        self.value = value
        self.start_count = start_count
        self.frequency = frequency
        super(AutomatedRunCondition, self).__init__(*args, **kw)

    def check(self, obj, cnt):
        '''
             check condition if cnt is greater than start count
             cnt-start count is greater than 0
             and cnt-start count is divisable by frequency
        '''

        if cnt > self.start_count and \
            (cnt - self.start_count) > 0 and \
                (cnt - self.start_count) % self.frequency == 0:
            return self._check(obj)

    def _check(self, obj):
        if hasattr(obj, self.attr):
            gvalue = getattr(obj, self.attr)
            comp = self.comp
            value = self.value

            if isinstance(gvalue, AffineScalarFunc):
                gvalue = gvalue.nominal_value

            cmd = '{}{}{}'.format(gvalue, comp, value)
            if eval(cmd):
                self.message = '{}, {} is True'.format(self.attr, cmd)
                return True

class TruncationCondition(AutomatedRunCondition):
    abbreviated_count_ratio = 1.0

class TerminationCondition(AutomatedRunCondition):
    pass

class ActionCondition(AutomatedRunCondition):
    action = Either(Str, Callable)
    resume = Bool  # resume==True the script continues execution else break out of measure_iteration
    def perform(self, script):
        action = self.action
        if isinstance(action, str):
            script.execute_snippet(action)
        else:
            action()

#============= EOF =============================================
