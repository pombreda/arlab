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

#============= standard library imports ========================
#============= local library imports  ==========================

# from src.ui.thread import Thread
from threading import Thread
from Queue import Queue, Empty

class ConsumerMixin(object):
    def setup_consumer(self, func=None, buftime=None, auto_start=True):
        self._consume_func = func
        self._buftime = buftime  # ms
        self._consumer_queue = Queue()
        self._consumer = Thread(target=self._consume)
        self._should_consume = True
        if auto_start:
            self._consumer.start()

    def queue_size(self):
        qs = 0
        if self._consumer_queue:
            qs = self._consumer_queue.qsize()
        return qs

    def is_empty(self):
        if self._consumer_queue:
            return self._consumer_queue.empty()

    def start(self):
        if self._consumer:
            self._consumer.start()

    def stop(self):
        if self._consumer:
            self._should_consume = False

    def add_consumable(self, v):
        self._consumer_queue.put_nowait(v)

    def _consume(self):
        bt = self._buftime
        if bt:
            bt = bt / 1000.
            def get_func():
                q = self._consumer_queue
                v = None
                while 1:
                    try:
                        v = q.get(timeout=bt)
                    except Empty:
                        break
                return v
        else:
            def get_func():
                try:
                    return self._consumer_queue.get(timeout=1)
                except Empty:
                    return

        cfunc = self._consume_func

        while 1:
            v = get_func()
            if v:
                if cfunc:
                    cfunc(v)
                elif isinstance(v, tuple):
                    func, a = v
                    func(a)

            if not self._should_consume:
                break


class consumable(object):
    _func = None
    _consumer = None
    def __init__(self, func=None):
        self._func = func

    def __enter__(self):
        self._consumer = c = ConsumerMixin()
        c.setup_consumer(func=self._func)
        return c

    def __exit__(self, *args, **kw):
        self._consumer.stop()

        self._consumer._consumer_queue=None
        self._consumer._consume_func=None
        
        self._consumer = None
        self._func = None


#============= EOF =============================================
