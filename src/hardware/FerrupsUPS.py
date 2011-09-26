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
#============= enthought library imports =======================
#============= standard library imports ========================
from datetime import datetime
#============= local library imports  ==========================
from src.hardware.core.core_device import CoreDevice

class FerrupsUPS(CoreDevice):
    scan_func = 'power_outage_scan'
    _power_out = False
    min_voltage_in = 5
    def _parse_response(self, resp):
        if self.simulation:
            resp = 'query', self.get_random_value(0, 10)
        elif resp is not None:
            resp = resp.strip()
            if '\n' in resp:
                EOF = '\n'
            else:
                EOF = '\r'
            resp = resp.split(EOF)
        return resp

    def _build_command(self, cmd):
        return cmd

    def _build_query(self, qry):
        return qry
    
    def set_password(self, pwd):
        qry = 'password {}'.format(pwd)
        qry = self._build_query(qry)
        resp = self.ask(qry)
        return self._parse_response(resp)
        
    def get_parameter(self, pname, **kw):
        qry = 'pa {}'.format(pname)
        qry = self._build_query(qry)
        resp = self.ask(qry, **kw)
        return self._parse_response(resp)
        
    def get_parameters(self, start=1, end=2):
        qry = 'pa {} {}'.format(start, end)
        qry = self._build_query(qry)
        resp = self.ask(qry)
        return self._parse_response(resp)
        
    def get_status(self):
        qry = 'status'
        qry = self._build_query(qry)
        resp = self.ask(qry)
        return self._parse_response(resp)

    def get_ambient_temperature(self):
        qry = 'ambtemp'
        qry = self._build_query(qry)
        resp = self.ask(qry)
        return self._parse_response(resp)
    
    def power_outage_scan(self):
        outage = self.check_power_outage()
        if outage is None:
            return 
            
        if outage:
            if self.application:
                tm = self.application.get_service('src.social.twitter_manager.TwitterManager')
                tm.post('Power Outage {}'.format(datetime.strftime(datetime.today(), '%Y-%m-%d %H:%M:%S')))
            self._power_out = True
        elif self._power_out:
            if self.application:
                tm = self.application.get_service('src.social.twitter_manager.TwitterManager')
                tm.post('Power Returned {}'.format(datetime.strftime(datetime.today(), '%Y-%m-%d %H:%M:%S')))
            self._power_out = False
        
        return True
        

    def check_power_outage(self):
        '''
            check to see if the V In to the ups is 0 
            
            True if power is out
        '''
        _query, resp = self.get_parameter(1, verbose=False)
        
        if self.simulation:
            return not self._power_out
            
        
        vin = resp.split(' ')[-1]
        try:
            vin = float(vin)
        except ValueError, e:
            print e
            return
        
        return vin < self.min_voltage_in
    
                                 
if __name__ == '__main__':
    f = FerrupsUPS(name='ups')
    f.bootstrap()
    
    print f.check_power_outage() 
#============ EOF ==============================================
