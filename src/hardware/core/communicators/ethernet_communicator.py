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



#============= enthought library imports =======================
#============= standard library imports ========================
import socket
#============= local library imports  ==========================
from communicator import Communicator
from src.loggable import Loggable


class Handler(Loggable):
    sock = None

    def get_packet(self):
        pass

    def send_packet(self, p):
        pass

    def open_socket(self, addr, timeout=0.1):
        self.address = addr
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.connect(addr)
        self.sock.settimeout(timeout)

    def end(self):
        pass


class TCPHandler(Handler):

    def get_packet(self):
        pass

    def send_packet(self, p):
        pass

    def end(self):
        self.sock.close()


class UDPHandler(Handler):
    datasize = 2 ** 10

    def open_socket(self, addr, timeout=0.75):
        self.address = addr
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.sock.connect(addr)
        self.sock.settimeout(timeout)

    def get_packet(self):
        r = None
#        cnt = 3
        cnt = 1
        for _ in range(cnt):
            try:
                r, _address = self.sock.recvfrom(self.datasize)
                break
            except socket.error, e:
                pass
        else:
            self.warning('get packet {}'.format(e))

        return r

    def send_packet(self, p):
#        self.sock.sendto(p, self.address)
        ok = False
        try:
            self.sock.sendto(p, self.address)
            ok = True
        except socket.error, e:
            self.warning('send packet {}'.format(e))

        return ok


class EthernetCommunicator(Communicator):
    '''
    '''
    host = None
    port = None
    handler = None
    kind = 'UDP'
    def load(self, config, path):
        '''
        '''
        self.host = self.config_get(config, 'Communications', 'host')
        # self.host = 'localhost'
        self.port = self.config_get(config, 'Communications', 'port', cast='int')

        self.kind = self.config_get(config, 'Communications', 'kind', optional=True)

        if self.kind is None:
            self.kind = 'UDP'

        return True

    def open(self, *args, **kw):

        self.simulation = False

        handler = self.get_handler()
        # send a test command so see if wer have connection
        if handler.send_packet('***'):
            r = handler.get_packet()
            if r is None:
                self.simulation = True
        else:
            self.simulation = True

        return True

    def get_handler(self):
        if self.kind.lower() == 'udp':
            if self.handler is None:
                h = UDPHandler()
                h.open_socket((self.host, self.port))
            else:
                h = self.handler
        else:
            h = TCPHandler()

        self.handler = h
        return h

    def _reset_connection(self):
        self.handler = None

    def ask(self, cmd, retries=3, verbose=True, info=None, *args, **kw):
        '''

        '''

        def _ask():
            if handler.send_packet(cmd):
                return handler.get_packet()

        if self.simulation:
            if verbose:
                self.info('no handle    {}'.format(cmd.strip()))
            return

        r = None
        with self._lock:
#            self._lock.acquire()
            re = 'ERROR: Connection refused {}:{}'.format(self.host, self.port)
            handler = self.get_handler()
            if self.simulation:
#                self._lock.release()
                return 'simulation'

            for _ in range(retries):
                r = _ask()
                if r is not None:
                    break
                else:
                    self._reset_connection()
#            self._lock.release()

        if r is not None:
            re = self.process_response(r)

        handler.end()
        if verbose:
            self.log_response(cmd, re, info)

        return re

    def tell(self, cmd, verbose=True, info=None):
        self._lock.acquire()
        handler = self.get_handler()

        if handler.send_packet(cmd):
            if verbose:
                self.log_tell(cmd, info)
        self._lock.release()

#============= EOF ====================================
