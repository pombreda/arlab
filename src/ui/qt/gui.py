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

'''
    http://stackoverflow.com/questions/10991991/pyside-easier-way-of-updating-gui-from-another-thread
'''

from PySide import QtCore
from PySide.QtGui import QColor


class InvokeEvent(QtCore.QEvent):
    EVENT_TYPE = QtCore.QEvent.Type(QtCore.QEvent.registerEventType())

    def __init__(self, fn, *args, **kwargs):
        QtCore.QEvent.__init__(self, InvokeEvent.EVENT_TYPE)
        self.fn = fn
        self.args = args
        self.kwargs = kwargs


class Invoker(QtCore.QObject):
    def event(self, event):
        event.fn(*event.args, **event.kwargs)
        del event
        return True


_invoker = Invoker()


def invoke_in_main_thread(fn, *args, **kwargs):
#     invoker = Invoker()
    QtCore.QCoreApplication.postEvent(_invoker,
                                      InvokeEvent(fn, *args, **kwargs))

    QtCore.QCoreApplication.processEvents()

#def invoke_in_main_thread2(fn, *args, **kw):
#    _FutureCall(1, fn, *args, **kw)

def convert_color(color, output='rgbF'):
    if isinstance(color, QColor):
        rgb = color.toTuple()

    tofloat = lambda x: x / 255.
    if output == 'rgbF':
        return map(tofloat, rgb[:3])
    elif output == 'rgbaF':
        return map(tofloat, rgb)


#============= EOF =============================================
