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

#============= standard library imports ========================
from numpy import asarray, argmax

from uncertainties import ufloat, umath
import math
from src.processing import constants
from copy import deepcopy
#============= local library imports  ==========================

def calculate_error_F(signals, F, k4039, ca3937, ca3637):
    '''
        McDougall and Harrison
        p92 eq 3.43
     
    '''

    m40, m39, m38, m37, m36 = signals
    G = m40 / m39
    B = m36 / m39
    D = m37 / m39
    C1 = 295.5
    C2 = ca3637.nominal_value
    C3 = k4039.nominal_value
    C4 = ca3937.nominal_value

    ssD = D.std_dev() ** 2
    ssB = B.std_dev() ** 2
    ssG = G.std_dev() ** 2
    G = G.nominal_value
    B = B.nominal_value
    D = D.nominal_value

    ssF = ssG + C1 ** 2 * ssB + ssD * (C4 * G - C1 * C4 * B + C1 * C2) ** 2
    return ssF ** 0.5

def calculate_error_t(F, ssF, j, ssJ):
    '''
        McDougall and Harrison
        p92 eq. 3.43
    '''
    JJ = j * j
    FF = F * F

    ll = constants.lambdak.nominal_value ** 2
    sst = (JJ * ssF + FF * ssJ) / (ll * (1 + F * j) ** 2)
    return sst ** 0.5

def calculate_flux(rad40, k39, age):
    '''
        rad40: radiogenic 40Ar
        k39: 39Ar from potassium
        age: age of monitor in years
        
        solve age equation for J
    '''
    if isinstance(rad40, (list, tuple, str)):
        rad40 = ufloat(rad40)
    if isinstance(k39, (list, tuple, str)):
        k39 = ufloat(k39)
    if isinstance(age, (list, tuple, str)):
        age = ufloat(age)
#    age = (1 / constants.lambdak) * umath.log(1 + JR)
    r = rad40 / k39

    j = (umath.exp(age * constants.lambdak) - 1) / r
    return j.nominal_value, j.std_dev()
#    return j

def calculate_decay_factor(dc, segments):
    '''
        McDougall and Harrison 
        p.75 equation 3.22
        
        the book suggests using ti==analysis_time-end of irradiation segment_i
        
        mass spec uses ti==analysis_time-start of irradiation segment_i
        
        using start seems more appropriate
    '''


    a = sum([pi * ti for pi, ti, _ in segments])

    b = sum([pi * ((1 - math.exp(-dc * ti)) / (dc * math.exp(dc * dti)))
                                                    for pi, ti, dti in segments])

    return a / b

def calculate_arar_age(signals, baselines, blanks, backgrounds,
                       j, irradinfo,
                       ic=(1.0, 0),
                       abundant_sensitivity=0,
                       a37decayfactor=None,
                       a39decayfactor=None
                       ):
    '''
        signals: measured uncorrected isotope intensities, tuple of value,error pairs
            value==intensity, error==error in regression coefficient
        baselines: measured baseline intensity
        !!!
            this method will not work if you want to make a time dependent baseline correction
            mass spec corrects each signal point with a modeled baseline. 
        !!!
        blanks: time dependent background, same format as signals
        background: static spectrometer background, same format as signals
        j: flux, tuple(value,error)
        irradinfo: tuple of production ratios + chronology + decay_time
            production_ratios = k4039, k3839, k3739, ca3937, ca3837, ca3637, cl3638
        
        ic: CDD correction factor
         
         
        return:
            returns a results dictionary with computed values
            result keys
                age_err_wo_jerr,
                rad40,
                tot40,
                k39,
                ca37,
                atm36,
                cl36,
                
                s40,
                s39,
                s38,
                s37,
                s36,
                ar39decayfactor,
                ar37decayfactor
            
    '''
    def to_ufloat(v):
        if isinstance(v, tuple):
            v = ufloat(v)
        return v
#    if isinstance(signals[0], tuple):
    s40, s39, s38, s37, s36 = map(to_ufloat, signals)

#    if isinstance(baselines[0], tuple):
    s40bs, s39bs, s38bs, s37bs, s36bs = map(to_ufloat, baselines)

#    if isinstance(blanks[0], tuple):
    s40bl, s39bl, s38bl, s37bl, s36bl = map(to_ufloat, blanks)

#    if isinstance(backgrounds[0], tuple):
    s40bk, s39bk, s38bk, s37bk, s36bk = map(to_ufloat, backgrounds)

    k4039, k3839, k3739, ca3937, ca3837, ca3637, cl3638, chronology_segments , decay_time = irradinfo

    ca3637 = ufloat(ca3637)
    ca3937 = ufloat(ca3937)
    ca3837 = ufloat(ca3837)
    k4039 = ufloat(k4039)
    k3839 = ufloat(k3839)
    cl3638 = ufloat(cl3638)
    k3739 = ufloat(k3739)
    ic = ufloat(ic)
    j = ufloat(j)
#    temp_ic = ufloat(ic)

#===============================================================================
# debugging
#===============================================================================
    debug = False
    if debug:
        tmpj = ufloat(j)
        j = ufloat((tmpj.nominal_value, tmpj.std_dev() * 100))

        s40 = ufloat((300, 1))
        s39 = ufloat((90, 1))
        s38 = ufloat((1, 1))
        s37 = ufloat((0.2, 0.01))
        s36 = ufloat((0.005, 0.001))

        s40bl = ufloat((1, 0.1))
        s39bl = ufloat((1, 0.1))
        s38bl = ufloat((0.0001, 0.00005))
        s37bl = ufloat((0.0001, 0.00005))
        s36bl = ufloat((0.0001, 0.00005))

        s40bs = ufloat((0, 0))
        s39bs = ufloat((0, 0))
        s38bs = ufloat((0, 0))
        s37bs = ufloat((0, 0))
        s36bs = ufloat((0, 0))

        s40bk = ufloat((0, 0))
        s39bk = ufloat((0, 0))
        s38bk = ufloat((0, 0))
        s37bk = ufloat((0, 0))
        s36bk = ufloat((0, 0))

#===============================================================================
# 
#===============================================================================

    #subtract blanks and baselines (and backgrounds)
    s40 -= (s40bl + s40bs + s40bk)
    s39 -= (s39bl + s39bs + s39bk)
    s38 -= (s38bl + s38bs + s38bk)
    s37 -= (s37bl + s37bs + s37bk)
    s36 -= (s36bl + s36bs + s36bk)

    #apply intercalibration factor to corrected 36
    s36 *= ic

    #correct for abundant sensitivity
    #assumes symmetric and equal abundant sens for all peaks
    n40 = s40 - abundant_sensitivity * (0 + s39)
    n39 = s39 - abundant_sensitivity * (s40 + s38)
    n38 = s38 - abundant_sensitivity * (s39 + s37)
    n37 = s37 - abundant_sensitivity * (s38 + s36)
    n36 = s36 - abundant_sensitivity * (s37 + 0)
    s40, s39, s38, s37, s36 = n40, n39, n38, n37, n36

    #calculate decay factors
    if a37decayfactor is None:
        try:
            dc = constants.lambda_37.nominal_value
            a37decayfactor = calculate_decay_factor(dc, chronology_segments)
        except ZeroDivisionError:
            a37decayfactor = 1

    if a39decayfactor is None:
        try:
            dc = constants.lambda_39.nominal_value
            a39decayfactor = calculate_decay_factor(dc, chronology_segments)
        except ZeroDivisionError:
            a39decayfactor = 1

    #calculate interference corrections
    s37dec_cor = s37 * a37decayfactor
    s39dec_cor = s39 * a39decayfactor

    k37 = ufloat((0, 0))

    #iteratively calculate 37, 39
    for _ in range(5):
        ca37 = s37dec_cor - k37
        ca39 = ca3937 * ca37
        k39 = s39dec_cor - ca39
        k37 = k3739 * k39

    k38 = k3839 * k39
    ca36 = ca3637 * ca37
    ca38 = ca3837 * ca37
    ca39 = ca3937 * ca37

    '''
        McDougall and Harrison
        Roddick 1983
        Foland 1993
        
        iteratively calculate atm36
    '''
    m = cl3638 * constants.lambda_cl36.nominal_value * decay_time
    atm36 = ufloat((0, 0))
    for _ in range(5):
        ar38atm = constants.atm3836.nominal_value * atm36
        cl38 = s38 - ar38atm - k38 - ca38
        cl36 = cl38 * m
        atm36 = s36 - ca36 - cl36

    #calculate rodiogenic
    #dont include error in 40/36
    atm40 = atm36 * constants.atm4036.nominal_value
    k40 = k39 * k4039
    ar40rad = s40 - atm40 - k40

    age_with_jerr = ufloat((0, 0))
    age_wo_jerr = ufloat((0, 0))
    try:
        R = ar40rad / k39

        #dont include error in decay constant
        age = age_equation(j, R)
        age_with_jerr = deepcopy(age)

        #dont include error in decay constant
        j.set_std_dev(0)
        age = age_equation(j, R)
        age_wo_jerr = deepcopy(age)

    except (ZeroDivisionError, ValueError):
        age = ufloat((0, 0))
        age_wo_jerr = ufloat((0, 0))

#    print s40 / s36
    result = dict(
                  age=age_with_jerr,
#                 age=age_wo_jerr,
                  age_err_wo_jerr=age_wo_jerr.std_dev(),
                  rad40=ar40rad,
                  tot40=s40,
                  k39=k39,
                  ca37=ca37,
                  atm36=atm36,
                  cl36=cl36,

                  s40=s40,
                  s39=s39,
                  s38=s38,
                  s37=s37,
                  s36=s36,

                  s37decay_cor=s37dec_cor,
                  s39decay_cor=s39dec_cor,

                  ar39decayfactor=a39decayfactor,
                  ar37decayfactor=a37decayfactor
                  )
    return result

def age_equation(j, R, scalar=1):
    if isinstance(j, (tuple, str)):
        j = ufloat(j)
    if isinstance(R, (tuple, str)):
        R = ufloat(R)

    return (1 / constants.lambdak.nominal_value) * umath.log(1 + j * R) / float(scalar)
#def calculate_arar_age(signals, baselines, blanks, backgrounds,
#                       j, irradinfo,
#                       ic=(1.0, 0),
#                       a37decayfactor=None,
#                       a39decayfactor=None
#                       ):
##    s40, s39, s38, s37, s36 = signals
#    s40bs, s39bs, s38bs, s37bs, s36bs = baselines
#    s40bl, s39bl, s38bl, s37bl, s36bl = blanks
#    s40bk, s39bk, s38bk, s37bk, s36bk = backgrounds
#
##    k4039, k3839, ca3937, ca3837, ca3637, cl3638, t = irradinfo
#    pr, t = irradinfo[:-1], irradinfo[-1]
#
#    s40, s39, s38, s37, s36 = map(ufloat, signals)
#    s40bs, s39bs, s38bs, s37bs, s36bs = map(ufloat, baselines)
#    s40bl, s39bl, s38bl, s37bl, s36bl = map(ufloat, blanks)
#    s40bk, s39bk, s38bk, s37bk, s36bk = map(ufloat, blanks)
#    k4039, k3839, ca3937, ca3837, ca3637, cl3638 = map(ufloat, pr)
#
#    j = ufloat(j)
#    ic = ufloat(ic)
#
#    s36 *= ic
#    s36bs *= ic
#
#    #subtract blanks and baselines
#    s40 -= (s40bl + s40bs + s40bk)
#    s39 -= (s39bl + s39bs + s39bk)
#    s38 -= (s38bl + s38bs + s38bk)
#    s37 -= (s37bl + s37bs + s37bk)
#    s36 -= (s36bl + s36bs + s36bk)
#
#    #calculate decay factors
#    #2004-11-16 21:16:00
#    if a37decayfactor is None:
#        try:
##            a37decayfactor = 1 / umath.exp(-t * (1 * constants.lambda_37.nominal_value * 365.25))
#            a37decayfactor = 1 / umath.exp(-t * (1 * constants.lambda_37.nominal_value * 365.25))
#            #t = umath.log(a39decayfactor) / (constants.lambda_39.nominal_value * 365.25)
#        except ZeroDivisionError:
#            a37decayfactor = 1
#
#    if a39decayfactor is None:
#        try:
##            a39decayfactor = 1 / umath.exp(-t * (1 * constants.lambda_39.nominal_value * 365.25))
#            a39decayfactor = 1 / umath.exp(-t * (1 * constants.lambda_39.nominal_value * 365.25))
#            #t1 = umath.log(a37decayfactor) / (constants.lambda_37.nominal_value * 365.25)
#        except ZeroDivisionError:
#            a39decayfactor = 1
#
#    #calculate interference corrections
#    ca37 = s37 * a37decayfactor
#    s39 = s39 * a39decayfactor
#    ca36 = ca3637 * ca37
#    ca38 = ca3837 * ca37
#    ca39 = ca3937 * ca37
#    k39 = s39 - ca39
#    k38 = k3839 * k39
#
#    if constants.lambda_cl36 < 0.1:
#        m = cl3638 * constants.lambda_cl36 * 365.25 * t
#    else:
#        m = cl3638
#
#    mcl = m / (m * constants.atm3836 - 1)
#    cl36 = mcl * (constants.atm3836 * (s36 - ca36) - s38 + k38 + ca38)
#    atm36 = s36 - ca36 - cl36
#
#    #calculate rodiogenic
#    #dont include error in 40/36
#    atm40 = atm36 * constants.atm4036.nominal_value
#    k40 = k39 * k4039
#    ar40rad = s40 - atm40 - k40
#
#    try:
#        JR = j * ar40rad / k39
#        #dont include error in decay constant
#        age = (1 / constants.lambdak.nominal_value) * umath.log(1 + JR)
#
##        j.set_std_dev(0)
##        JR = j * ar40rad / k39
##        #dont include error in decay constant
##        age_wo_jerr = (1 / constants.lambdak.nominal_value) * umath.log(1 + JR)
#    except (ZeroDivisionError, ValueError):
#        age = ufloat((0, 0))
##        age_wo_jerr = ufloat((0, 0))
#
#    result = dict(age=age,
##                  age_wo_jerr=age_wo_jerr,
#                  rad40=ar40rad,
#                  tot40=s40,
#                  k39=k39,
#                  ca37=ca37,
#                  atm36=atm36,
#
#                  s40=s40,
#                  s39=s39,
#                  s38=s38,
#                  s37=s37,
#                  s36=s36,
#                  ar39decayfactor=a39decayfactor,
#                  ar37decayfactor=a37decayfactor
#                  )
#    return result

#    try:
#    except ValueError, e:
#        print e
#        return e
#============= EOF =====================================

##=============enthought library imports=======================oup
#
##=============standard library imports ========================
#from uncertainties import ufloat
#from uncertainties.umath import log, exp
#
##=============local library imports  ==========================
#import constants
##from data_adapter import new_unknown
#
#plateau definition
plateau_criteria = {'number_steps':3}

def overlap(a1, a2, e1, e2):
    e1 *= 2
    e2 *= 2
    if a1 - e1 < a2 + e2 and a1 + e1 > a2 - e2:
        return True

#===============================================================================
# non-recursive
#===============================================================================
def find_plateaus(ages, errors, signals):
    plats = []
    platids = []
    for i in range(len(ages)):
        ids = _find_plateau(ages, errors, signals, i)
        if ids is not None and ids.any():
            start, end = ids
            plats.append(end - start)
            platids.append((start, end))

#    print plats, platids
    if plats:
        plats = asarray(plats)
        platids = asarray(platids)

        return platids[argmax(plats)]

def _find_plateau(ages, errors, signals, start):
    plats = []
    platids = []
    for i in range(1, len(ages)):
        if check_plateau(ages, errors, signals, start, i):
            plats.append(i - start)
            platids.append((start, i))
    if plats:
        plats = asarray(plats)
        platids = asarray(platids)
        return platids[argmax(plats)]

def check_plateau(ages, errors, signals, start, end):
    for i in range(start, min(len(ages), end + 1)):
        for j in range(start, min(len(ages), end + 1)):
            if i != j:
                obit = not overlap(ages[i], ages[j], errors[i], errors[j])
                mswdbit = not check_mswd(ages, errors, start, end)
                percent_releasedbit = not check_percent_released(signals, start, end)
                n_steps_bit = (end - start) + 1 < 3
                if (obit or
                    mswdbit or
                    percent_releasedbit or
                    n_steps_bit):
                    return False

    return True

def check_percent_released(signals, start, end):
    tot = sum(signals)
    s = sum(signals[start:end + 1])
    return s / tot >= 0.5

def check_mswd(ages, errors, start, end):
#    a_s = ages[start:end + 1]
#    e_s = errors[start:end + 1]
#    print calculate_mswd(a_s, e_s)
    return True
#===============================================================================
# recursive
# from timeit testing recursive method is not any faster
#  use non recursive method instead purely for readablity
#===============================================================================

def find_plateaus_r(ages, errors, start=0, end=1, plats=None, platids=None):
    if plats is None:
        plats = []
        platids = []

    if start == len(ages) or end == len(ages):
        plats = asarray(plats)
        platids = asarray(platids)
        return platids[argmax(plats)]
    else:
        a = check_plateau_r(ages, errors, start, end)
        if a:
            plats.append((end - start))
            platids.append((start, end))

            return find_plateaus_r(ages, errors, start, end + 1, plats, platids)
        else:
            return find_plateaus_r(ages, errors, start + 1, end + 1, plats, platids)

def check_plateau_r(ages, errors, start, end, isplat=True):
    if end < len(ages):
        return isplat and check_plateau_r(ages, errors, start, end + 1, isplat)
    else:
        for i in range(start, min(len(ages), end + 1)):
            for j in range(start, min(len(ages), end + 1)):
                if i != j:
                    if not overlap(ages[i], ages[j], errors[i], errors[j]):
                        return False
        return True

ages = [10] * 50
errors = [1] * 1

def time_recursive():
    find_plateaus_r(ages, errors)

def time_non_recursive():
    find_plateaus(ages, errors)

if __name__ == '__main__':
    #21055-02
#    signals = ((8.681775, 0.004059),
#                   (9.557604, 0.003301),
#                   (0.128056, 0.000320),
#                   (0.055542, 0.000151), (0.000267, 0.000013))
#    baselines = ((0, 0), (0, 0), (0, 0), (0, 0), (0, 0))
#    blanks = ((0.013131, 0.00069),
#              (0.0008725, 0.00007),
#              (0.00003314, 0.0000088),
#
#              (0.0002788, 0.000013), (0.00005382, 0.0000048))
#    t = 
#    print 'asdfs', 1 / umath.exp(-constants.lambda_37 * t)
#    print 1 / (constants.lambda_37) * umath.log(3.801e1)
    #60754-10
    signals = ((2655.294, 0.12),
               (377.5964, 0.046),
               (4.999, 0.012),
               (0.0853, 0.014),
               (0.013245, 0.00055)
               )
    baselines = ((0, 0), (0, 0), (0, 0), (0, 0), (0, 0))
    blanks = ((1.5578, 0.023),
              (0.0043, 0.024),
              (-0.0198, 0.011),
              (0.0228, 0.012),
              (0.00611, 0.00033))
    backgrounds = ((0, 0), (0, 0), (0, 0), (0, 0), (0, 0))
    j = (2.2408e-3, 1.7795e-6)
    irradinfo = ((1e-2, 2e-3),
                     (1.3e-2, 0),

                     (7e-4, 2e-6),
                     (0, 0),
                     (2.8e-4, 2e-5),
                     (2.5e2, 0), 0.50429815306)
    calculate_arar_age(signals, baselines, blanks, backgrounds, j, irradinfo,

#                       a37decayfactor=1.956,
#                       a39decayfactor=1.0
#                       a37decayfactor=3.801e1, a39decayfactor=1.001
                       )
#    from timeit import Timer
#    t = Timer('time_recursive', 'from __main__ import time_recursive')
#
#    n = 5
#    tr = t.timeit(n)
#    print 'time r', tr / 5
#
#    t = Timer('time_non_recursive', 'from __main__ import time_non_recursive')
#    tr = t.timeit(n)
#    print 'time nr', tr / 5
#    find_plateaus(ages, errors)
#def find_plateaus(ages, errors):
#    def __add_plateau(s, e, p, di):
#        d = e - s
#        if d >= plateau_criteria['number_steps']:
#            p.append((s, e))
#            di.append(d)
#
#    start_i = 0
#    end_i = 0
#    plateaus = []
#    plateau_lengths = []
#    for i in range(1, len(ages)):
#        a1 = ages[start_i]
#        a2 = ages[i]
#        
#        e1 = 2 * errors[start_i]
#        e2 = 2 * errors[i]
#        #a1 = aa1.nominal_value
#        #a2 = aa2.nominal_value
#        #e1 = 2.0 * aa1.std_dev()
#        #e2 = 2.0 * aa2.std_dev()
#        print a1, a2, e1, e2
#        if not (a1 - e1) >= (a2 + e2) and not (a1 + e1) <= (a2 - e2):
#            end_i += 1
#        else:
#            __add_plateau(start_i, end_i, plateaus, plateau_lengths)
#
#            start_i = end_i + 1
#            end_i = start_i
#
#    __add_plateau(start_i, end_i, plateaus, plateau_lengths)
#
#    if len(plateau_lengths) == 0:
#        return
#
#    #get and return the indices of the longest plateau
#    max_i = plateau_lengths.index(max(plateau_lengths))
#
#    return (plateaus[max_i][0], plateaus[max_i][1] + 1)


#def age_calculation(*args):
#    '''
#    j, m40, m39, m38, m37, m36, production_ratio, days_since_irradiation, irradiation_time
#    return age in years
#    '''
#    j_value = args[0]
#    isotope_components = get_isotope_components(*args[1:])
#    #calculate the age
#
#    JR = j_value * isotope_components['rad40'] / isotope_components['k39']
#    age = (1 / constants.lambdak) * log(1 + JR)
#
#    return age
#def j_calculation(*args):
#    '''
#    age, m40, m39, m38, m37, m36, production_ratio, days_since_irradiation, irradiation_time
#        age in a (years)
#    '''
#    age = args[0]
#    isotope_components = get_isotope_components(*args[1:])
#    j_val = (exp(age * constants.lambdak) - 1) * isotope_components['k39'] / isotope_components['rad40']
#    return j_val
#
#def get_isotope_components(m40, m39, m38, m37, m36, production_ratio, days_since_irradiation, irradiation_time):
#    #iteratively calculate 37 and 39
#    k37 = 0
#    for i in range(10):
#        ca37 = m37 - k37
#        ca39 = production_ratio.ca3937 * ca37
#        k39 = m39 - ca39
#        k37 = production_ratio.k3739 * k39
#
#    #correct for decay
#    k37, k39 = correct_for_decay(k37, k39, days_since_irradiation, irradiation_time)
#
#    #38 from potassium and calcium
#    k38 = k39 * production_ratio.k3839
#    ca38 = ca37 * production_ratio.ca3837
#
#    #36 from calcium 
#    ca36 = production_ratio.ca3637 * ca37
#
#    #cosmogenic 36 from cl
#    if constants.lambda_cl36 < 0.1:
#        m = production_ratio.cl3638 * constants.lambda_cl36 * days_since_irradiation
#    a3836 = 1 / constants.atm36_38
#    mcl = m / (m * a3836 - 1)
#    cl36 = mcl * (a3836 * (m36 - ca36) - m38 + k38 + ca38)
#
#    #36 from atm
#    atm36 = m36 - ca36 - cl36
#
#    #38 from atm and cl 
#    atm38 = atm36 / constants.atm36_38
#    cl38 = m38 - k38 - atm38 - ca38
#
#    #40 from atm
#    atm40 = atm36 * constants.atm40_36
#
#    #40 from potassium
#    k40 = production_ratio.k4039 * k39
#
#    rad40 = m40 - atm40 - k40
#    values = [rad40, atm40, atm38, atm36, k40, k39, k38, k37, cl38, cl36, ca39, ca38, ca37, ca36]
#    keys = ['rad40', 'atm40', 'atm38', 'atm36', 'k40', 'k39', 'k38', 'k37', 'cl38', 'cl36', 'ca39', 'ca38', 'ca37', 'ca36']
#
#    return dict(zip(keys, values))
#
#def correct_for_decay(m37, m39, days_since_irradiation, irradiation_time):
#    '''
#    '''
#    lam = constants.lambda_37
#    m37 *= lam * irradiation_time * exp(lam * days_since_irradiation) / (1 - exp(-lam * irradiation_time))
#
#    lam = constants.lambda_39
#    m39 *= lam * irradiation_time * exp(lam * days_since_irradiation) / (1 - exp(-lam * irradiation_time))
#    return m37, m39
#
#
#
#
##============= EOF ====================================
#
#
#
##def plateau_age(data):
##    '''
##    data = rowtuple of corrected data
##    '''
##    #calculate the ages and store ref to 39
##    ages = []
##    ar_39_signals = []
##
##    integrated = new_unknown()
##    keys = ['ar40', 'ar39', 'ar38', 'ar37', 'ar36']
##    integrated.j_value = data[0].j_value
##    for d in data:
##        for k in keys:
##            integrated.isotopes[k] += d.isotopes[k]
##        ar_39_signals.append(d.isotopes['ar39'])
##
##        ages.append(calc_corrected_age(d))
##    print 'integrated age :', calc_corrected_age(integrated)
##
##    indices = find_plateaus(ages)
##    if indices is None:
##        print 'no plateau'
##    for d in data[indices[0]:indices[1]+1]:
##        print 'plateau step',d.AnalysisID,d.DataReductionSessionID
##    
##def calc_corrected_age(corrected_unknown):
##    '''
##    return age in Ma
##    
##    '''
##
##    #correct unknown for blank value
##    corrected_unknown.correct_for_blank()
##    corrected_unknown.correct_for_decay()
##
##    days_since_irradiation = corrected_unknown.days_since_irradiation()
##
##    #set up some shorthand names
##    corrected_40 = corrected_unknown.isotopes['ar40']
##    corrected_39 = corrected_unknown.isotopes['ar39']
##    corrected_38 = corrected_unknown.isotopes['ar38']
##    corrected_37 = corrected_unknown.isotopes['ar37']
##    corrected_36 = corrected_unknown.isotopes['ar36']
##
##
##    j_value = corrected_unknown.j_value
##    production_ratio = corrected_unknown.production_ratio
##
##    return __corrected_age_calc__(corrected_40, corrected_39, corrected_38, corrected_37, corrected_36,
##                           j_value, production_ratio, days_since_irradiation) / 1e6
#
#
#
#def calculate_arar_age(signals, ratios, ratio_errs,
#                       a37decayfactor, a39decayfactor, j, jer, d, der):
#    s40, s40er, s39, s39er, s38, s38er, s37, s37er, s36, s36er = signals
#    p36cl38cl, k4039, k3839, ca3637, ca3937, ca3837 = ratios
#    k4039er, ca3637er, ca3937er = ratio_errs
##    a37decayfactor = 1
##    a39decayfactor = 1
#    #convert to ufloats
#    from uncertainties import ufloat
#    from uncertainties.umath import log
#
#    s40 = ufloat((s40, s40er))
#    s39 = ufloat((s39, s39er))
#    s38 = ufloat((s38, s38er))
#    s37 = ufloat((s37, s37er))
#    s36 = ufloat((s36, s36er))
#    k4039 = ufloat((k4039, k4039er))
#    ca3637 = ufloat((ca3637, ca3637er))
#    ca3937 = ufloat((ca3937, ca3937er))
#    j = ufloat((j, jer))
#    d = ufloat((d, der))
#
##    #calculate the age
#    ca37 = s37 * a37decayfactor
#    s39 = s39 * a39decayfactor
#    ca36 = ca3637 * ca37
#    ca38 = ca3837 * ca37
#    ca39 = ca3937 * ca37
#    k39 = s39 - ca39
#    k38 = k3839 * k39
#
#    time_since_irradiation = (log(1 / a37decayfactor) /
#                        (-1 * constants.lambda_37 * 365.25))
#
#    if constants.lambda_cl36 < 0.1:
#        m = p36cl38cl * constants.lambda_cl36 * time_since_irradiation
#    else:
#        m = p36cl38cl
#    mcl = m / (m * constants.atm3836 - 1)
#    cl36 = mcl * (constants.atm3836 * (s36 - ca36) - s38 + k38 + ca38)
#    atm36 = s36 - ca36 - cl36
#
#    atm40 = atm36 * constants.atm4036
#    k40 = k39 * k4039
#    ar40rad = s40 - atm40 - k40
#    JR = j * ar40rad / k39
##    age = (1 / constants.lambdak) * math.log(1 + JR)
#    age = (1 / constants.lambdak) * log(1 + JR)
#
#    #==========================================================================
#    # errors mass spec copy
#    #==========================================================================
#
#    square = lambda x: x * x
#
#    Tot40Er = s40er
#    Tot39Er = s39er
#    Tot38Er = s38er
#    Tot37Er = s37er
#    Tot36Er = s36er
#
#    D = d
#    D2 = d * d
#    D3 = d * D2
#    D4 = d * D3
#
#    T40 = s40 / D4
#    T39 = s39 / D3
#    T38 = s39 / D2
#    T37 = s39 / D
#    T36 = s36
#
#    A4036 = constants.atm4036
#    A3836 = constants.atm3836
#
#    s = ca3937 * D * T37
#    T = ca3637 * D * T37
#    G = D3 * T39 - s
##    P = mcl * (ca3837 * D * T37 + A3836 * (T36 - T) - D2 * T38 + k3839 * G)
#    R = (-k4039 * G - A4036 * (T36 - T - mcl * (ca3837 * D * T37 + A3836 * (T36 - T) - D2 * T38 + k3839 * G)) + D4 * T40)
#    G2 = G * G
#
#    er40 = square(D4 * j / G) * square(Tot40Er)
#
#    er39 = square((j * (-D3 * k4039 + A4036 * D3 * k3839 * mcl)) / G - (D3 * j * R) / G2) * square(Tot39Er)
#
#    er38 = square(A4036 * D2 * j * mcl / G) * square(Tot38Er)
#
#    er37 = square((j * (ca3937 * D * k4039 - A4036 *
#            (-ca3637 * D - (-A3836 * ca3637 * D + ca3837 * D - ca3937 * D * k3839) * mcl)))
#            / G + (ca3937 * D * j * R) / G2) * square(Tot37Er)
#
#    er36 = square(A4036 * j * (1 - A3836 * mcl) / G) * square(Tot36Er)
#    '''
#    square((j * (4 * T40 * D3 - K4039 * (3 * D2 * T39 - Ca3937 * T37) 
#        - A4036 * (-(Ca3637 * T37) - MCl * (-(A3836 * Ca3637 * T37) 
#        + Ca3837 * T37 + K3839 * (3 * D2 * T39 - Ca3937 * T37) 
#        - 2 * D * T38)))) 
#        / (D3 * T39 - s) - (1 * j * (3 * D2 * T39 - Ca3937 * T37) 
#        * (T40 * D4 - K4039 * (D3 * T39 - s) 
#        - A4036 * (T36 - T - MCl * (-(T38 * D2) + Ca3837 * T37 * D + A3836 * (T36 - T) + K3839 * (D3 * T39 - s))))) 
#        / square(D3 * T39 - s)) * square(DiscEr)
#      '''
#    erD = square((j * (4 * T40 * D3 - k4039 * (3 * D2 * T39 - ca3937 * T37)
#        - A4036 * (-(ca3637 * T37) - mcl * (-(A3836 * ca3637 * T37)
#        + ca3837 * T37 + k3839 * (3 * D2 * T39 - ca3937 * T37)
#        - 2 * D * T38))))
#        / (D3 * T39 - s) - (1 * j * (3 * D2 * T39 - ca3937 * T37)
#        * (T40 * D4 - k4039 * (D3 * T39 - s)
#        - A4036 * (T36 - T - mcl * (-(T38 * D2) + ca3837 * T37 * D + A3836 * (T36 - T) + k3839 * (D3 * T39 - s)))))
#        / square(D3 * T39 - s)) * square(der)
#
#    er4039 = square(j * (s - D3 * T39) / G) * square(k4039er)
#
#    er3937 = square((j * (D * k4039 * T37 - A4036 * D * k3839 * mcl * T37)) / G + (D * j * T37 * R) / G2) * square(ca3937er)
#
#    er3637 = square(-((A4036 * j * (-D * T37 + A3836 * D * mcl * T37)) / G)) * square(ca3637er)
#
#    erJ = square(R / G) * square(jer)
#    JRer = (er40 + er39 + er38 + er37 + er36 + erD + er4039 + er3937 + er3637 + erJ) ** 0.5
#    age_err = (1e-6 / constants.lambdak) * JRer / (1 + ar40rad / k39 * j)
##===============================================================================
## error pychron port 
##===============================================================================
##    s = ca3937 * s37 
##    T = ca3637 * s37
##    G = s39 - s
##    R = (-k4039 * G - constants.atm4036 * (s36 - T - mcl * (ca3837 * s37 + constants.atm3836 * (s36 - T) - s38 + k3839 * G)) + s40)
##    #ErComp(1) = square(D4 * j / G) * square(Tot40Er)
##    er40 = (d ** 4 * j / G) ** 2 * s40er ** 2
##    
##    #square((j * (-D3 * K4039 + A4036 * D3 * K3839 * MCl)) / G - (D3 * j * R) / G2) * square(Tot39Er)
##    d3 = d ** 3
##    er39 = ((j * (-d3 * k4039 + constants.atm4036 * d3 * k3839 * mcl)) / G - (d3 * j * R) / G ** 2) ** 2 * s39er ** 2
##    
##    #square(A4036 * D2 * j * MCl / G) * square(Tot38Er)
##    er38 = (constants.atm4036 * d * d * j * mcl / G) ** 2 * s38er ** 2
##    
##    #square((j * (Ca3937 * D * K4039 - A4036 * 
##    #        (-Ca3637 * D - (-A3836 * Ca3637 * D + Ca3837 * D - Ca3937 * D * K3839) * MCl))) 
##    #        / G + (Ca3937 * D * j * R) / G2) * square(Tot37Er)
##    er37 = ((j * (ca3937 * d * k4039 - constants.atm4036 
##            * (-ca3637 * d - (-constants.atm3836 * ca3637 * d + ca3837 * d - ca3937 * d * k3839) * mcl))) 
##            / G + (ca3937 * d * j * R) / G ** 2) ** 2 * s37er ** 2
##    
##    #square(A4036 * j * (1 - A3836 * MCl) / G) * square(Tot36Er)
##    er36 = (constants.atm4036 * j * (1 - constants.atm3836 * mcl) / G) ** 2 * s36er ** 2
##    
##    #square((j * (4 * T40 * D3 - K4039 * (3 * D2 * T39 - Ca3937 * T37) 
##    #    -A4036 * (-(Ca3637 * T37) - MCl * (-(A3836 * Ca3637 * T37) 
##    #    + Ca3837 * T37 + K3839 * (3 * D2 * T39 - Ca3937 * T37) 
##    #    - 2 * D * T38)))) 
##    #    / (D3 * T39 - s) - (1 * j * (3 * D2 * T39 - Ca3937 * T37) 
##    #    * (T40 * D4 - K4039 * (D3 * T39 - s) 
##    #    - A4036 * (T36 - T - MCl * (-(T38 * D2) + Ca3837 * T37 * D + A3836 * (T36 - T) + K3839 * (D3 * T39 - s))))) 
##    #    / square(D3 * T39 - s)) * square(DiscEr)
##        
##    erD = ((j * (4 * s40 / d - k4039 * (3 * s39 / d - ca3937 * s37 / d)
##        - constants.atm4036 * (-(ca3637 * s37 / d) - mcl * (-(constants.atm3836 * ca3637 * s37 / d)
##        + ca3837 * s37 / d + k3839 * (3 * s39 / d - ca3937 * s37 / d)
##        - 2 * s38 / d))))  
##        / (s39 / d - s) - (1 * j * (3 * s39 / d - ca3937 * s37 / d)
##        * (s40 / d - k4039 * (s40 / d - s)
##        - constants.atm4036 * (s36 - T - mcl * (-(s38 / d) + ca3837 * s37 + constants.atm3836 * (s36 - T) + k3839 * (s39 / d - s)))))
##        / (s39 / d - s) ** 2) ** 2 * der ** 2
##    #square(j * (s - D3 * T39) / G) * square(K4039Er)
##    er4039 = (j * (s - s39 / d) / G) ** 2 * k4039er ** 2
##    
##    #square((j * (D * K4039 * T37 - A4036 * D * K3839 * MCl * T37)) / G + (D * j * T37 * R) / G2) * square(Ca3937Er)
##    er3937 = ((j * (k4039 * s37 - constants.atm4036 * k3839 * mcl * s37)) / G + (j * s37 * R) / G ** 2) ** 2 * ca3937er ** 2
##    
##    #square(-((A4036 * j * (-D * T37 + A3836 * D * MCl * T37)) / G)) * square(Ca3637Er)
##    er3637 = (-((constants.atm4036 * j * (-s37 + constants.atm3836 * mcl * s37)) / G)) ** 2 * ca3637er ** 2
##    
##    #square(R / G) * square(JErLocal)
##    erJ = (R / G) ** 2 * jer ** 2
##    JRer = (er40 + er39 + er38 + er37 + er36 + erD + er4039 + er3937 + er3637 + erJ) ** 0.5
##    age_err = (1e-6 / constants.lambdak) * JRer / (1 + ar40rad / k39 * j)
#
#    return age / 1e6, age_err
