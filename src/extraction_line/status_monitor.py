from src.loggable import Loggable
from threading import Event, Timer

class StatusMonitor(Loggable):
    valve_manager=None
    _stop_evt=None
    _clients=0
    state_freq=3
    lock_freq=5
    period=1
    def start(self):
        if not self._clients:
            if self._stop_evt:
                self._stop_evt.set()
                self._stop_evt.wait(0.25)
            
            self._stop_evt=Event()
        
        self._iter(1)
        self._clients+=1
            
    
    def isAlive(self):
        if self._stop_evt:
            return not self._stop_evt.isSet()
        
    def stop(self):
        self._clients-=1
        
        if not self._clients:
            self._stop_evt.set()
        else:
            self.debug('Alive clients {}'.format(self._clients))
            
    def _iter(self, i):
        vm=self.valve_manager
        if not i%self.state_freq:
            vm.load_valve_states()
        if not i%self.lock_freq:
            vm.load_valve_lock_states()
         
        if i>1000:
            i=0
        if not self._stop_evt.isSet():
            t=Timer(self.period, self._iter, (i+1,))
            t.start()
    