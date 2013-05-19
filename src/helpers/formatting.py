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
import math
from functools import partial
#============= local library imports  ==========================
def calc_percent_error(v, e):
        try:

            sigpee = '{:0.2f}'.format(abs(e / v * 100))
        except ZeroDivisionError:
            sigpee = 'NaN'
        return sigpee

def errorfmt(v, e):
        pe = calc_percent_error(v, e)
        return '{} ({}%)'.format(floatfmt(e), pe)

def floatfmt(f, n=4, s=2, max_width=None):
    if abs(f) < 1e-20:
        v = '0.0'
    else:

        if abs(f) < math.pow(10, -(n - 1)) or abs(f) > math.pow(10, s + 1):
            fmt = '{{:0.{}E}}'.format(s)
        else:
            fmt = '{{:0.{}f}}'.format(n)

        v = fmt.format(f)
        if max_width:
            if len(v) > max_width:
                v = v[:max_width]

    return v

def pfloatfmt(**kw):
    return partial(floatfmt, **kw)

#============= EOF =============================================
