#===============================================================================
# Copyright 2013 Jake Ross
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
from threading import Thread, Event

from traits.api import Str, Int, Callable, List
import zmq

from src.loggable import Loggable


#============= standard library imports ========================
#============= local library imports  ==========================

class Subscriber(Loggable):
    host = Str
    port = Int
    callback = Callable

    _stop_signal = None
    _subscriptions = List

    def connect(self, timeout=None):
        context = zmq.Context()
        sock = context.socket(zmq.SUB)
        h, p = self.host, self.port
        url = 'tcp://{}:{}'.format(h, p)
        sock.connect(url)
        self._sock = sock
        return self.check_server_availability(context, url, timeout)

    def check_server_availability(self, ctx, url, timeout=3):
        ret = True
        if timeout:
            alive_sock = ctx.socket(zmq.REQ)
            alive_sock.connect(url)

            poll = zmq.Poller()
            poll.register(alive_sock, zmq.POLLIN)
            request = 'ping'
            alive_sock.send(request)
            socks = dict(poll.poll(timeout * 1000))
            if not socks.get(alive_sock) == zmq.POLLIN:
                self.warning('subscription server at {} not available'.format(url))
                alive_sock.setsockopt(zmq.LINGER, 0)
                alive_sock.close()
                poll.unregister(alive_sock)
                ret = False

        return ret

    def subscribe(self, f, cb):
        sock = self._sock
        sock.setsockopt(zmq.SUBSCRIBE, f)
        self._subscriptions.append((f, cb))

    def listen(self):
        self.info('starting subscription')
        self._stop_signal = Event()
        t = Thread(target=self._listen)
        t.setDaemon(True)
        t.start()

    def stop(self):
        if self._stop_signal:
            self._stop_signal.set()

    def _listen(self):
        sock = self._sock
        while not self._stop_signal.is_set():
            resp = sock.recv()
            self.debug('raw notification {}'.format(resp))
            for si, cb in self._subscriptions:
                if resp.startswith(si):
                    resp = resp.split(si)[-1].strip()
                    self.info('received notification {}'.format(resp))
                    cb(resp)
                    break

#============= EOF =============================================
