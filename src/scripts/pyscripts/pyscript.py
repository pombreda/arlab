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

from traits.api import Str, Any, Bool, Enum
import time
from threading import Thread, Event, Timer, currentThread, Condition
from src.loggable import Loggable
import os
from pyface.timer.do_later import do_later
from Queue import Queue, Empty
from src.scripts.wait_dialog import WaitDialog
from pyface.wx.dialog import confirmation


def verbose_skip(func):
    def decorator(obj, *args, **kw):
        if obj._syntax_checking or obj._cancel:
            return
        obj.debug('{} {} {}'.format(func.__name__, args, kw))
        return func(obj, *args, **kw)
    return decorator

def skip(func):
    def decorator(obj, *args, **kw):
        if obj._syntax_checking or obj._cancel:
            return
        return func(obj, *args, **kw)
    return decorator

class DummyManager(Loggable):
    def open_valve(self, *args, **kw):
        self.info('open valve')

    def close_valve(self, *args, **kw):
        self.info('close valve')


class GosubError(Exception):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return 'GosubError: {} does not exist'.format(self.path)


class PyscriptError(Exception):
    def __init__(self, err):
        self.err = err
    def __str__(self):
        return 'Pyscript error: {}'.format(self.err)


class IntervalError(Exception):
    def __str__(self):
        return 'Poorly matched BeginInterval-CompleteInterval'


class MainError(Exception):
    def __str__(self):
        return 'No "main" function defined'


HTML_HELP = '''
<body>
<table border="1">
    <tr>
        <th>Keyword</th>
        <th>Parameters</th>
        <th>Description</th>
        <th>Example</th>
    </tr>
    <tr><td colspan="4" align="center" bgcolor=#C0C0C0>
        Script Specific</td></tr>
    {}
    <tr><td colspan="4" align="center" bgcolor=#C0C0C0>
        General</td></tr>
    <tr>
        <td>sleep</td>
        <td>seconds</td>
        <td>delay execution</td>
        <td>sleep(1.5)</td>
    </tr>
    <tr>
        <td>begininterval</td>
        <td>seconds</td>
        <td>start an interval (t>=5 opens a wait dialog)</td>
        <td>begininterval(40)</td>
    </tr>
    <tr>
        <td>completeinterval</td>
        <td></td>
        <td>blocks execution until begininterval is released</td>
        <td>completeinterval</td>
    </tr>
    <tr>
        <td>info</td>
        <td>message</td>
        <td>log an info message</td>
        <td>info("hello info world")</td>
    </tr>
</table>
</body>
'''


class PyScript(Loggable):
    _text = None
    manager = Any
    laser_manager = Any
    parent = Any
    root = Str
    parent_script = Any

    _interval_stack = Queue
    _interval_flag = None

    _cancel = Bool(False)
    _completed = False

    _syntax_checking = False
    _syntax_checked = False
    _gosub_script = None
    _wait_dialog = None

    cancel_flag = Bool
    hash_key = None

    def _cancel_flag_changed(self, v):
        if v:
            result = confirmation(None, 'Are you sure you want to cancel {}'.format(self.logger_name))
            if result != 5104:
                self.cancel()
            else:
                self.cancel_flag = False

    def get_help(self):
        return HTML_HELP.format(self._get_help_hook())

    def _get_help_hook(self):
        return ''

    def get_context(self):
        ks = [((k[0], k[1]) if isinstance(k, tuple) else (k, k))
               for k in self.get_commands()]

        return dict([(k, getattr(self, fname)) for k, fname in ks])

    def get_commands(self):
        cmds = ['sleep',
            'begin_interval', 'complete_interval',
            'gosub', 'exit', ('info', '_m_info'),

            ]
        return cmds

    def set_text(self, t):
        self._text = t

    @property
    def state(self):
        #states
        #0=running
        #1=canceled
        #2=completed
        if self._cancel:
            return '1'

        if self._completed:
            return '2'

        return '0'

    def cancel(self):
        self._cancel = True
        if self._gosub_script is not None:
            if not self._gosub_script._cancel:
                self._gosub_script.cancel()

        if self.parent:
            self.parent._executing = False

        if self.parent_script:
            if not self.parent_script._cancel:
                self.parent_script.cancel()

        if self._wait_dialog:
            self._wait_dialog.close()

        self._cancel_hook()

    def _cancel_hook(self):
        pass

    def bootstrap(self, load=True, **kw):
        self._interval_flag = Event()
        self._interval_stack = Queue()
        if self.root and self.name and load:
            p = os.path.join(self.root, self.name)
            with open(p, 'r') as f:
                self._text = f.read()
            return True

    def report_result(self, r):
#        n = currentThread().name
#        if n == 'MainThread':
#            print r
        pass

#==============================================================================
# commands
#==============================================================================
    def gosub(self, name):
        if not name.endswith('.py'):
            name += '.py'

        if '/' in name:
            d = '/'
        elif ':' in name:
            d = ':'

        dirs = name.split(d)
        name = dirs[0]
        for di in dirs[1:]:
            name = os.path.join(name, di)

        p = os.path.join(self.root, name)
        if not os.path.isfile(p):
            raise GosubError(p)
#        print self.__class__
        s = self.__class__(root=self.root,
#                          path=p,
                          name=name,
                          _syntax_checked=self._syntax_checked,
                          manager=self.manager,
                          parent_script=self
                          )
#        s.bootstrap()

        if self._syntax_checking:
            if not self._syntax_checked:
                self._syntax_checked = True
                s.bootstrap()
                err = s._test()
                if err:
                    raise PyscriptError(err)
        else:
            if not self._cancel:
                self.info('doing GOSUB')
                self._gosub_script = s
                s.execute()
                self._gosub_script = None
                if not self._cancel:
                    self.info('gosub finished')

    def exit(self):
        self.info('doing EXIT')
        self.cancel()

    def complete_interval(self):
        try:
            pi = self._interval_stack.get(timeout=0.01)
            if pi != 'b':
                raise IntervalError()
        except Empty:
            raise IntervalError()

        if self._syntax_checking:
            return

        if self._cancel:
            return

        self.info('COMPLETE INTERVAL waiting for begin interval completion')
        #wait until _interval_flag is set
        while not self._interval_flag.isSet():
            if self._cancel:
                break
            self._sleep(0.5)

        if not self._cancel:
            self._interval_flag.clear()

    @verbose_skip
    def begin_interval(self, timeout):
        def wait(t):
            self._sleep(t)
            if not self._cancel:
                self.info('interval finished')
                if self._interval_flag:
                    self._interval_flag.set()

        timeout = float(timeout)
#        if self._syntax_checking or self._cancel:
#            return
        self._interval_stack.put('b')

        self.info('BEGIN INTERVAL waiting for {}'.format(timeout))
        t = Thread(target=wait, args=(timeout,))
        t.start()

    @skip
    def _m_info(self, msg):

        self.info(msg)

    @verbose_skip
    def sleep(self, v):
#        if self._syntax_checking or self._cancel:
#            return

        self.info('SLEEP {}'.format(v))
        self._sleep(v)

    def execute(self, new_thread=False):

        def _ex_():
            self.bootstrap()

            ok = True
            if not self._syntax_checked:
                r = self._test()
#                if r is not None:
#                    return r

            if ok:
                self._execute()

        if new_thread:
            t = Thread(target=_ex_)
            t.start()
        else:
            _ex_()

    def _test(self):

        self._syntax_checking = True
        self.info('testing syntax')
        r = self._execute()

        if r is not None:
            self.info('invalid syntax')
            raise PyscriptError(r)
#            report the traceback
#            self.info(r)

        elif not self._interval_stack.empty():
            raise IntervalError()

        else:
            self.info('syntax checking passed')
        self._syntax_checking = False



    def _execute(self):

        if not self._text:
            return 'No script text'

        self._cancel = False
        self._completed = False
        safe_dict = self.get_context()

#        safe_dict['isblank'] = False
        try:
            code = compile(self._text, '<string>', 'exec')
            exec code in safe_dict
            safe_dict['main']()
        except KeyError:
            return MainError()

        except Exception, _e:
            import traceback
            traceback.print_exc()
            return traceback.format_exc()

        if self._syntax_checking:
            return

        self._post_execute_hook()

        if self._cancel:
            self.info('{} canceled'.format(self.name))
        else:
            self.info('{} completed successfully'.format(self.name))
            self._completed = True
            if self.parent:
                self.parent._executing = False
                del self.parent.scripts[self.hash_key]

    def _post_execute_hook(self):
        pass
#        if self.controller is not None:
#            self.controller.end()

    def _manager_action(self, func, manager=None, *args, **kw):
#        man = self._get_manager()
        man = self.manager
#        print man, manager, func
        if manager is not None and man is not None:
            app = man.application
            if app is not None:
                man = app.get_service(manager)

        if man is not None:

            if not isinstance(func, list):
                func = [(func, args, kw)]

            for f, a, k in func:
                getattr(man, f)(*a, **k)

#    def _get_manager(self):
#        return self.manager

#==============================================================================
# Sleep/ Wait
#==============================================================================
    def _sleep(self, v):
        v = float(v)
#        if self._syntax_checking or self._cancel:
#            return

        if v > 1:
            if v >= 5:
                self._block(v, dialog=True)
            else:
                self._block(v, dialog=False)

        else:
            time.sleep(v)

    def _block(self, timeout, dialog=False):
        if dialog:

            st = time.time()
            c = Condition()
            c.acquire()
            self._wait_dialog = wd = WaitDialog(wtime=timeout,
                                condition=c,
                                parent=self,
                                title='{} - Wait'.format(self.logger_name),
                                message='Waiting for {}'.format(timeout)
                                )

            do_later(wd.edit_traits)
            c.wait()
            c.release()
            do_later(wd.close)

            if wd._canceled:
                self.cancel()
            elif wd._continued:
                self.info('continuing script after {:0.3f} s'.format(time.time() - st))

        else:
            st = time.time()
            while time.time() - st < timeout:
                if self._cancel:
                    break
                self._sleep(0.5)

if __name__ == '__main__':
    from src.helpers.logger_setup import logging_setup

    logging_setup('pscript')
#    execute_script(t)
    from src.paths import paths

    p = PyScript(root=os.path.join(paths.scripts_dir, 'pyscripts'),
                      path='test.py',
                      _manager=DummyManager())

    p.execute()

