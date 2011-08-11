#@PydevCodeAnalysisIgnore

#=============enthought library imports=======================
from traits.api import Float, Button, Bool
from traitsui.api import View, Item

#=============standard library imports ========================
import time
#=============local library imports  ==========================
from src.scripts.file_script import FileScript

class LaserPulseScript(FileScript):
    '''
        G{classtree}
    '''
    fire = Button
    firing = Bool(False)
    request_power = Float
    pulse_length = Float
    def load_file(self):
        '''
        '''
        self.request_power = float(self._file_contents_[0])
        self.pulse_length = float(self._file_contents_[1])

    def run(self, *args):
        '''
            @type *args: C{str}
            @param *args:
        '''
        self.firing = True
        manager = self.manager

        manager.enable_laser()

        manager.set_laser_power(self.request_power)
        time.sleep(self.pulse_length)
        manager.disable_laser()
        self.firing = False

    def _fire_fired(self):
        '''
        '''
        self.start()

    def traits_view(self):
        '''
        '''
        v = View(Item('fire', show_label = False, enabled_when = 'not firing'),
               Item('request_power'),
               Item('pulse_length'),
               title = 'Laser Pulse'
               )
        return v