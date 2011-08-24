#============= enthought library imports =======================
from traits.api import  Float, Str, Bool, Property

from src.spectrometer.spectrometer_device import SpectrometerDevice
#from traitsui.api import View, Item, Group, HGroup, VGroup

#============= standard library imports ========================

#============= local library imports  ==========================
charge = 1.6021764874e-19
class Detector(SpectrometerDevice):
    name = Str
    relative_position = Float(1)

    deflection = Property(Float(enter_set = True, auto_set = False), depends_on = '_deflection')
    _deflection = Float

    intensity = Float
    active = Bool
    def finish_loading(self):
        self.read_deflection()

    def _set_deflection(self, v):
        self._deflection = v
        self.microcontroller.ask('SetDeflection {},{}'.format(self.name,
                                                                   v))
    def _get_deflection(self):
        return self._deflection

    def read_deflection(self):
        r = self.microcontroller.ask('GetDeflection {}'.format(self.name))
        try:
            self._deflection = float(r)
        except ValueError:
            pass

if __name__ == '__main__':
    d = Detector()


#============= EOF =============================================
#    def calc_deflection(self, ht):
#        ht *= 1000 #accelerating voltage V
#        mass = 39.962
#        L = 1
#        velocity = math.sqrt(2 * charge * ht / mass)
#        flight_time = L / velocity
#        d = 0.1
#        E = -self._deflection / d
#        F = charge * E
#        delta = 0.5 * math.sqrt(F / mass) * flight_time ** 2
