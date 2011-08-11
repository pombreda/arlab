#=============enthought library imports=======================
from traits.api import Float, Property, Str
from traitsui.api import View, Item, EnumEditor
#=============standard library imports ========================
#import time
#=============local library imports  ==========================


#from modbus.modbus_device import ModbusDevice
#class TemperatureMonitor(ModbusDevice, Streamable):
#    def initialize(self):
#        pass
#    def scan(self, *args):
#        '''
#
#        '''
#        if super(TemperatureMonitor, self).scan(*args) is None:
#            self.current_value = v = self.read_temperature(verbose = False)
#            self.stream_manager.record(v, self.name)
from core.core_device import CoreDevice
from src.hardware.core.data_helper import make_bitarray
class ISeriesDevice(CoreDevice):
    '''
        G{classtree}
        http://www.omega.com/iseries/Pdf/M3397CO.pdf
    '''
    prefix = '*'
    scan_func = 'read_device'
    process_value = Float


    def _parse_response(self, re):
        '''
        '''
        if re is not None:
            if re == 'simulation':
                return self.get_random_value()

            args = re.split(' ')

            if len(args) > 1:
                try:
                    return float(args[1])
                except:
                    return -1

    def _build_command(self, cmd_type, cmd_indx):
        '''
        '''
        return '{}{}{}'.format(self.prefix, cmd_type, cmd_indx)

INPUT_CLASS_MAP = {0:'TC', 1:'RTD', 2:'PROCESS'}
TC_MAP = {0:'J', 1:'K', 2:'T', 3:'E', 4:'N', 5:'Din-J', 6:'R', 7:'S', 8:'B', 9:'C'}
TC_KEYS = ['J', 'K', 'T', 'E', 'N', 'Din-J', 'R', 'S', 'B', 'C']
class DPi32TemperatureMonitor(ISeriesDevice):
    '''
        G{classtree}
    '''
    scan_func = 'read_temperature'
    input_type = Property(depends_on = '_input_type')
    _input_type = Str
    id_query = '*R07'

    def id_response(self, response):
        r = False
        if response is not None:
            re = response.strip()
            #strip off first three command characters
            if re[:3] == 'R07':
                r = True

        return r


    def initialize(self):
        self.info('getting input type')
        self.read_input_type()


    def _get_input_type(self):
        '''
        '''
        return self._input_type

    def _set_input_type(self, v):
        '''
            @type v: C{str}
            @param v:
        '''
        self._input_type = v
        self.set_input_type(v)
#
    def get_process_value(self):
        '''
        '''
        return self.process_value

    def read_temperature(self):
        '''
        '''
        commandindex = '01'
        com = self._build_command('V', commandindex)
        x = self._parse_response(self.ask(com, # delay = 400,
                                              verbose = False
                                              ))
        if x is not None:
            self.process_value = x

            return x

    def set_input_type(self, v):
        '''
            @type v: C{str}
            @param v:
        '''
        commandindex = '07'

        input_class = '00'

        #bits 7,6 meaningless for thermocouple 
        bits = '00{}{}'.format(make_bitarray(TC_KEYS.index(v),
                                                  width = 4),
                                input_class
                                )
        value = '{:02X}'.format(int(bits, 2))

        self._write_command(commandindex, value = value)
#        
    def read_input_type(self):
        '''
        '''
        commandindex = '07'
        com = self._build_command('R', commandindex)

        re = self.ask(com)

        if re is not None:
            re = re.strip()
            #strip off first three command characters
            # compare with sent command for error checking
            if re[:3] == 'R07':
                re = make_bitarray(int(re[3:]))
                input_class = INPUT_CLASS_MAP[int(re[:2])]
                if input_class == 'TC':
                    self._input_type = TC_MAP[int(re[2:6])]

    def reset(self):
        '''
        '''
        c = self._build_command('Z', '02')
        self.ask(c)

    def _write_command(self, commandindex, value = None):
        '''
        '''
        args = [self.prefix, 'W', commandindex]

        if value is not None:
            args += [str(value)]
        self.ask(''.join(args),
                 #delay = 400
                 )

    def traits_view(self):
        '''
        '''
        return View(Item('process_value', style = 'readonly'),
                    Item('input_type', editor = EnumEditor(values = TC_KEYS), show_label = False))
#============= EOF ============================================
