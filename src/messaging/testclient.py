#============= enthought library imports =======================
from traits.api import HasTraits, String, Button, Int, Str, Enum, Float, Bool, Event, Property
from traitsui.api import View, Item, Group, HGroup, VGroup, ButtonEditor

#============= standard library imports ========================

#============= local library imports  ==========================

#============= views ===================================
#============= EOF ====================================

import socket
from numpy import array, mean, std, savez, load
from pylab import hist, show, xlim
from timeit import Timer
import time
import os
from datetime import timedelta
from threading import Thread


class Client(HasTraits):
    command = String('Read argus_temp_monitor', enter_set = True, auto_set = False)
    resend = Button
    response = String
    port = Int(1068)
    host = Str('localhost')
    kind = Enum('UDP', 'TCP')

    period = Float(100)
    periodic = Event
    periodic_label = Property(depends_on = '_alive')

    n_periods = Int(100)
    _alive = Bool(False)

    def _periodic_fired(self):
        self._alive = not self._alive
        if self._alive:
            t = Thread(target = self._loop)
            t.start()

    def _loop(self):
        i = 0
        while self._alive and i <= self.n_periods:
            self._send()
            time.sleep(self.period / 1000.0)
            i += 1
        self._alive = False

    def _get_periodic_label(self):
        return 'Periodic' if not self._alive else 'Stop'
    def _resend_fired(self):
        self._send()

    def _command_changed(self):
        self._send()

    def _send(self):
        #open connection
        conn = self.get_connection()

        #send command
        conn.send(self.command)
        self.response = conn.recv(4096)

    def get_connection(self):
        packet_kind = socket.SOCK_STREAM
        family = socket.AF_INET
        addr = (self.host, self.port)
        if self.kind == 'UDP':
            packet_kind = socket.SOCK_DGRAM

        sock = socket.socket(family, packet_kind)


        sock.connect(addr)
        return sock
    def traits_view(self):
        v = View(
                 VGroup(
                     Item('command'),
                     Item('response', show_label = False, style = 'custom',
                          width=-300
                          ),
                     Item('resend',show_label = False),
                     
                     HGroup(Item('periodic',
                                 editor = ButtonEditor(label_value = 'periodic_label'),
                                 show_label = False), Item('period', show_label = False),
                                 Item('n_periods')
                            ),
                     Item('kind', show_label = False),
                     Item('port'),
                     Item('host')),

                 resizable = True
                 )
        return v



def send_command(addr, cmd, kind = 'UDP'):
    p = socket.SOCK_STREAM
    if kind == 'UDP':
        p = socket.SOCK_DGRAM

    sock = socket.socket(socket.AF_INET, p)

    sock.connect(addr)
    sock.settimeout(2)
    sock.send(cmd)
    resp = sock.recv(1024)
    return resp

def client(kind, port):
    while 1:
        data = raw_input('    >> ')
        if kind == 'inet':
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('127.0.0.1', port))
        else:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.connect("/tmp/hardware")

        s.send(data)
        datad = s.recv(1024)
        print 'Received', repr(datad)
        s.close()

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('localhost', 1063))

    cmd = 'Read bakeout1'
    s.send(cmd)
    s.recv(1024)
    s.close()

def main2():
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.connect('/tmp/hardware')

    cmd = 'System|Read bakeout1'
    s.send(cmd)
    s.recv(1024)
    s.close()

def plothist(name):
    p = os.path.join(os.getcwd(), name)
    files = load(p)
    hist(files['times'], 1000 / 4.)
    xlim(0, 0.040)
    show()

def benchmark(me, im, fp):
    t = Timer(me, im)
    st = time.time()
    n = 1000
    times = array(t.repeat(n, number = 1))
    dur = time.time() - st

    etime = timedelta(seconds = dur)
    avg = mean(times)
    stdev = std(times)
    mi = min(times) * 1000
    ma = max(times) * 1000

    print 'n trials', n, 'execution time %s' % etime
    print 'mean %0.2f' % (avg * 1000), ' std %0.2f' % (stdev * 1000)
    print 'min %0.2f ms' % mi, 'max %0.2f ms' % ma

    stats = array([n, etime, avg, stdev, mi, ma])
    p = os.path.join(os.getcwd(), fp)
    savez(p, times = times, stats = stats)

    foo = load(p)
    hist(foo['times'], n / 4.)
    show()


if __name__ == '__main__':
    #plothist('benchmark_unix_only.npz')
#    benchmark('main()', 'from __main__ import main',
#              'benchmark_unix_tcp_no_log.npz'
#              )
#   

    c = Client()
    c.configure_traits()
#    host = '129.138.12.145'
#
##    host = 'localhost'
#    port = 1069
#    cmds = ['SetIntegrationTime 1.048576']
##    cmds = ['GetHighVoltage', 'GetTrapVoltage']
#    #cmds = ['DoJog standard_short']
#    for c in cmds:
#        r = send_command((host, port), c)
#        print '{} ===> {}'.format(c, r)
