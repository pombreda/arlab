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
from traits.etsconfig.etsconfig import ETSConfig
from src.stats.core import kronecker
ETSConfig.toolkit = 'qt4'
from traits.api import Array
#============= enthought library imports =======================
from numpy import linspace, apply_along_axis, sign, roll, \
     where, Inf, vectorize, zeros, ones_like, identity
from scipy.optimize import fsolve
#============= standard library imports ========================
#============= local library imports  ==========================
from src.regression.ols_regressor import OLSRegressor
class YorkRegressor(OLSRegressor):
    xns = Array
    xds = Array

    yns = Array
    yds = Array

    xnes = Array
    xdes = Array

    ynes = Array
    ydes = Array

    def calculate(self, *args, **kw):
        super(YorkRegressor, self).calculate(*args, **kw)

        if not len(self.xserr):
            return
        if not len(self.yserr):
            return

        self._calculate_correlation_coefficients()
        self._calculate()

    def _calculate_correlation_coefficients(self):
        if len(self.xds):
            fd = self.xdes / self.xds  # f40Ar

            fyn = self.ynes / self.yns  # f36Ar
            fxn = self.xnes / self.xns  # f39Ar

            a = (1 + (fyn / fd) ** 2)
            b = (1 + (fxn / fd) ** 2)
            return (a * b) ** -0.5
        else:
            return 0

    def _calculate(self):
        raise NotImplementedError

    def _calculate_W(self, *args, **kw):
        raise NotImplementedError

    def _get_weights(self):
        Wx = 1 / self.xserr ** 2
        Wy = 1 / self.yserr ** 2
        return Wx, Wy

    def _calculate_UV(self, W):
        xs, ys = self.xs, self.ys
        x_bar, y_bar = self._calculate_xy_bar(W)
        U = xs - x_bar
        V = ys - y_bar
        return U, V

    def _calculate_xy_bar(self, W):
        xs, ys = self.xs, self.ys
        sW = sum(W)
        x_bar = sum(W * xs) / sW
        y_bar = sum(W * ys) / sW
        return x_bar, y_bar

    def get_slope(self):
        self.calculate()
        return self._slope

    def get_intercept(self):
        self.calculate()
        return self._intercept

    def get_intercept_error(self):
        return self.get_intercept_variance() ** 0.5

    def get_slope_error(self):
        return self.get_slope_variance() ** 0.5

class NewYorkRegressor(YorkRegressor):
    '''
        mahon 1996
    '''
    correlation_coefficient = 0

    def _calculate(self):
        b = 0
        cnt = 0
        b, a, cnt = self._calculate_slope_intercept(Inf, b, cnt)
        if cnt >= 500:
            self.warning('regression did not converge')
        else:
            self.info('regression converged after {} iterations'.format(cnt))
        self._slope = b
        self._intercept = a

    def _calculate_slope_intercept(self, pb, b, cnt, total=500, tol=1e-15):
        '''
            recursively calculate slope
            b=slope
            a=intercept
        '''

        if abs(pb - b) < tol and cnt < total:
            W = self._calculate_W(b)
            XBar, YBar = self._calculate_xy_bar(W)
            a = YBar - b * XBar
            return b, a, cnt
        else:
            sig_x = self.xserr
            sig_y = self.yserr

            r = self._calculate_correlation_coefficients()

            var_x = sig_x ** 2
            var_y = sig_y ** 2

            W = self._calculate_W(b)
            U, V = self._calculate_UV(W)
            sumA = sum(W ** 2 * V * (U * var_y + b * V * var_x - r * V * sig_x * sig_y))
            sumB = sum(W ** 2 * U * (U * var_y + b * V * var_x - b * r * U * sig_x * sig_y))
            nb = sumA / sumB

            return self._calculate_slope_intercept(b, nb, cnt + 1)


    def _calculate_W(self, b):
        sig_x = self.xserr
        sig_y = self.yserr
        var_x = sig_x ** 2
        var_y = sig_y ** 2
        r = self._calculate_correlation_coefficients()
        return (var_y + b ** 2 * var_x - 2 * b * r * sig_x * sig_y) ** -1


    def get_slope_variance(self):

        b = self._slope
        W = self._calculate_W(b)
        U, V = self._calculate_UV(W)

        sig_x = self.xserr
        sig_y = self.yserr
        var_x = sig_x ** 2
        var_y = sig_y ** 2

        r = self._calculate_correlation_coefficients()
        sig_xy = r * sig_x * sig_y

        aa = 2 * b * (U * V * var_x - U ** 2 * sig_xy)
        bb = U ** 2 * var_y - V ** 2 * var_x
        cc = W ** 3 * (sig_xy - b * var_x)

        da = b ** 2 * (U * V * var_x - U ** 2 * sig_xy)
        db = b * (U * 2 * var_y - V ** 2 * var_x)
        dc = U * V * var_y - V ** 2 * sig_xy
        dd = da + db - dc
        dVdb = sum(W ** 2 * (aa + bb)) + 4 * sum(cc * dd)

        kd = identity(W.shape[0])

        sW = sum(W)

        ee = W ** 2 * (kd - W / sW)

        dVdx = sum(ee * (b ** 2 * (V * var_x - 2 * U * sig_xy) + \
                     2 * b * U * var_y - V * var_y))

        dVdy = sum(ee * (b ** 2 * (U * var_x + 2 * V * sig_xy) - \
                     2 * b * V * var_x - U * var_y))

        a = sum(dVdx ** 2 * var_x + dVdy ** 2 * var_y + 2 * sig_xy * dVdx * dVdy)

        var_b = a / dVdb ** 2
        return var_b


class ReedYorkRegressor(YorkRegressor):
    '''
        reed 1992
    '''
    _degree = 1
#     def _set_degree(self, d):
#         '''
#             York regressor only for linear fit
#         '''
#         self._degree = 2
    def _calculate(self):
        if self.coefficients is None:
            return

        Wx, Wy = self._get_weights()
        def f(mi):
            W = self._calculate_W(mi, Wx, Wy)
            U, V = self._calculate_UV(W)

            suma = sum((W ** 2 * U * V) / Wx)
            S = sum((W ** 2 * U ** 2) / Wx)

            a = (2 * suma) / (3 * S)

            sumB = sum((W ** 2 * V ** 2) / Wx)
            B = (sumB - sum(W * U ** 2)) / (3 * S)

            g = -sum(W * U * V) / S

            ff = pow(mi, 3) - 3 * a * pow(mi, 2) + 3 * B * mi - g
            return ff

        m = self.coefficients[-1]
        roots = fsolve(f, (m,))
        slope = roots[0]

        self._slope = slope

        W = self._calculate_W(slope, Wx, Wy)
        X_bar, Y_bar = self._calculate_xy_bar(W)

        self._intercept = Y_bar - slope * X_bar

    def _calculate_W(self, slope, Wx, Wy):
        W = Wx * Wy / (slope ** 2 * Wy + Wx)
        return W

    def get_intercept_variance(self):
        var_slope = self.get_slope_variance()
        xs = self.xs
        Wx, Wy = self._get_weights()
        W = self._calculate_W(self._slope, Wx, Wy)
        return var_slope * sum(W * xs ** 2) / sum(W)

    def get_slope_variance(self):
        n = len(self.xs)

        Wx, Wy = self._get_weights()
        slope = self._slope
        W = self._calculate_W(slope, Wx, Wy)
        U, V = self._calculate_UV(W)
        sumA = sum(W * (slope * U - V) ** 2)

        sumB = sum(W * U ** 2)


        var = 1 / float(n - 2) * sumA / sumB
        return var


    def predict(self, x, *args, **kw):
        '''
            a=Y-bX
            
            a=y-intercept
            b=slope
            
        '''
        slope, intercept = self.get_slope(), self.get_intercept()
        return slope * x + intercept

if __name__ == '__main__':
    from numpy import ones, array
    from pylab import plot, show
    xs = [0.89, 1.0, 0.92, 0.87, 0.9, 0.86, 1.08, 0.86, 1.25,
            1.01, 0.86, 0.85, 0.88, 0.84, 0.79, 0.88, 0.70, 0.81,
            0.88, 0.92, 0.92, 1.01, 0.88, 0.92, 0.96, 0.85, 1.04
            ]
    ys = [0.67, 0.64, 0.76, 0.61, 0.74, 0.61, 0.77, 0.61, 0.99,
          0.77, 0.73, 0.64, 0.62, 0.63, 0.57, 0.66, 0.53, 0.46,
          0.79, 0.77, 0.7, 0.88, 0.62, 0.80, 0.74, 0.64, 0.93
          ]
    exs = ones(27) * 0.01
    eys = ones(27) * 0.01

    xs = [0, 0.9, 1.8, 2.6, 3.3, 4.4, 5.2, 6.1, 6.5, 7.4]
    ys = [5.9, 5.4, 4.4, 4.6, 3.5, 3.7, 2.8, 2.8, 2.4, 1.5]
    wxs = array([1000, 1000, 500, 800, 200, 80, 60, 20, 1.8, 1])
    wys = array([1, 1.8, 4, 8, 20, 20, 70, 70, 100, 500])
    exs = 1 / wxs ** 0.5
    eys = 1 / wys ** 0.5

    plot(xs, ys, 'o')

    reg = NewYorkRegressor(
                             ys=ys,
                             xs=xs,
                             xserr=exs,
                             yserr=eys
                             )
    m, b = reg.get_slope(), reg.get_intercept()
    xs = linspace(0, 8)
    plot(xs, polyval((m, b), xs))
    show()
#============= EOF =============================================