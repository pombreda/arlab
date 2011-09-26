'''
Copyright 2011 Jake Ross

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
#=============enthought library imports=======================
from traits.api import  Str, implements, Any
from pyface.timer.api import Timer

#=============standard library imports ========================
import random
from threading import Lock#, Thread

#=============local library imports  ==========================
from communicators.serial_communicator import SerialCommunicator as serial
from communicators.modbus.modbus_communicator import ModbusCommunicator as modbus
from communicators.ethernet_communicator import EthernetCommunicator as ethernet
from communicators.gpib_communicator import GPIBCommunicator as gpib

#from streamable import Streamable
from viewable_device import ViewableDevice
from i_core_device import ICoreDevice
from src.managers.data_managers.csv_data_manager import CSVDataManager
class CoreDevice(ViewableDevice):
    '''
    '''
    implements(ICoreDevice)
    _communicator = None
    name = Str
    id_query = ''
    id_response = ''

    
    scan_device = False
    scan_func = None
    scan_lock = None
    timer = None
    scan_period = 1000
    scan_units = 'ms'
    record_scan_data = True
    
    current_value = 0
    
    time_dict = dict(ms=1, s=1000, m=60.0 * 1000, h=60.0 * 60.0 * 1000)
    application = Any
    
    no_response_counter = 0
    def get(self):
        return self.current_value
#        if self.simulation:
#            return 'simulation'

    def set(self, v):
        pass

    def _communicator_factory(self, communicator_type):
        if communicator_type is not None:
            gdict = globals()
            if communicator_type in gdict:
                return gdict[communicator_type](name='_'.join((self.name, communicator_type)),
                                   id_query=self.id_query,
                                   id_response=self.id_response
                                )

    def load(self, *args, **kw):
        '''
            Load a configuration file.  
            Get Communications info to make a new communicator
        '''
        config = self.get_configuration()
        if config:
            if config.has_section('Communications'):
                type = self.config_get(config, 'Communications', 'type')

                communicator = self._communicator_factory(type)
                if communicator is not None:
                    #give the _communicator the config object so it can load its args
                    communicator.load(config, self.config_path)

                    if hasattr(self, 'id_query'):
                        communicator.id_query = getattr(self, 'id_query')
                    self._communicator = communicator
                else:
                    return False
            #load additional child specific args
            r = self.load_additional_args(config)
            if r:
                self._loaded = True
            return r

    def load_additional_args(self, config):
        '''
        '''
        return True

    def open(self, **kw):
        '''
        '''
        if self._communicator is not None:
            return self._communicator.open(**kw)


    def ask(self, cmd, **kw):
        '''
        '''
        if self._communicator is not None:
            r = self._communicator.ask(cmd, **kw)
            self.last_command = cmd
            self.last_response = str(r)
            return r
        else:
            self.info('no communicator for this device {}'.format(self.name))

    def write(self, *args, **kw):
        '''
        '''
        self.tell(*args, **kw)

    def tell(self, *args, **kw):
        '''
        '''
        if self._communicator is not None:
            self.last_command = ' '.join(map(str, args) + map(str, kw.iteritems()))
            self.last_response = '-'
            return self._communicator.tell(*args, **kw)

    def read(self, *args, **kw):
        '''
        '''
        if self._communicator is not None:
            return self._communicator.read(*args, **kw)

    def get_random_value(self, min=0, max=10):
        '''
            convienent method for getting a random integer between min and max
            
            Defaults:
                min=0
                max=10

        '''
        return random.randint(min, max)

    def set_scheduler(self, s):
        if self._communicator is not None:
            self._communicator.scheduler = s

#===============================================================================
# streamin interface
#===============================================================================
    def setup_scan(self, pdev):
        
        
        #should get scan settings from the config file not the initialization.xml
        
        config = self.get_configuration()
        if config.has_section('Scan'):
            if config.getboolean('Scan', 'enabled'):
                self.set_attribute(config, 'scan_period', 'Scan', 'period', cast='float')
                self.set_attribute(config, 'scan_units', 'Scan', 'units')
                self.set_attribute(config, 'record_scan_data', 'Scan', 'record', cast='boolean')
                self.start_scan()
        

                
    def _scan_(self, *args):
        '''

        '''
        if self.scan_func:
            try:
                v = getattr(self, self.scan_func)()
            except AttributeError, e:
                print e
                return

            if v is not None:
                self.current_value = v
                if self.record_scan_data:
                    x = self.graph.record(v)        
                    self.data_manager.write_to_frame((x, v))
            
            else:
                '''
                    scan func must return a value or we will stop the scan
                    since the timer runs on the main thread any long comms timeouts
                    slow user interaction
                '''
                if self.no_response_counter > 3:
                    self.info('no response. stopping scan')
                    self.timer.Stop()
                    self.no_response_counter = 0
                else:
                    self.info('no response {}'.format(self.no_response_counter))
                    self.no_response_counter += 1

    def scan(self, *args, **kw):
        '''

        '''
        if self.scan_lock is None:
            self.scan_lock = Lock()

        self.scan_lock.acquire()
        self._scan_(*args, **kw)
        self.scan_lock.release()
        
    def start_scan(self):
        if self.timer is not None:
            self.timer.Stop()

#        if not self.simulation:
        self.info('Starting scan')
        if self.record_scan_data:
            self.data_manager = CSVDataManager()
            self.frame_name = self.data_manager.new_frame()
        
        sp = self.scan_period * self.time_dict[self.scan_units]
        
        self.timer = Timer(sp, self.scan)
        self.timer.Start()

    def stop_scan(self):
        if self.timer is not None:
            self.timer.Stop()

#========================= EOF ============================================
