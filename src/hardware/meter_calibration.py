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

#============= standard library imports ========================
from numpy import poly1d
from scipy import optimize

#============= local library imports  ==========================

class MeterCalibration(object):
    coefficients = None
    bounds = None

    def __init__(self, *args):
        if args:
            coeffs = args[0]
            if isinstance(coeffs, str):
                coeffs = map(float, coeffs.split(','))

            self.coefficients = coeffs

    def get_input(self, response):
        '''
            return the input required to produce the requested response
        '''
        if self.bounds:
            for c, b in zip(self.coefficients, self.bounds):
                if b[0] < response <= b[1]:
                    break
            else:
                closest = 0
                min_d = 1000
                for i, b in enumerate(self.bounds):
                    d = min(abs(b[0] - response), abs(b[1] - response))
                    if d < min_d:
                        closest = i
                c = self.coefficients[closest]
        else:
            c = self.coefficients

        #say y=ax+b (watts=a*power_percent+b)
        #calculate x for a given y
        #solvers solve x for y=0
        #we want x for y=power, therefore
        #subtract the requested power from the intercept coeff (b)
        #find the root of the polynominal

        if c is not None and len(c):
            c[-1] -= response
            power = optimize.newton(poly1d(c), 1)
            c[-1] += response
        else:
            power = response
        return power, c
#============= EOF =============================================