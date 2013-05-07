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




#=============enthought library imports=======================

#=============standard library imports ========================
import os
import sys
import logging.handlers
#=============local library imports  =========================
from src.paths import paths
from filetools import unique_path
# from globals import globalv
# from pyface.timer.do_later import do_later
import shutil

NAME_WIDTH = 40
gFORMAT = '%(name)-{}s: %(asctime)s %(levelname)-7s (%(threadName)-10s) %(message)s'.format(NAME_WIDTH)
gLEVEL = logging.DEBUG

# LOGGER_LIST = []

# class DisplayHandler(logging.StreamHandler):
#    '''
#    '''
#    output = None
#    def emit(self, record):
#        '''
#
#        '''
#        if self.output is not None:
#            msg = '{record.name}{record.message}'.format(record=record)
# #            import wx
# #            print type(self.output._display), not isinstance(self.output._display, wx._core._wxPyDeadObject)
# #            if not isinstance(self.output._display, wx._core._wxPyDeadObject):
#
#            do_later(self.output.add_text, color='red' if record.levelno > 20 else 'black',
#                                 msg=msg,
#                                 kind='warning' if record.levelno > 20 else 'info',)
#            self.output.add_text(
#                                     color='red' if record.levelno > 20 else 'black',
#                                 msg=msg,
#                                 kind='warning' if record.levelno > 20 else 'info',
#                                 )
# def clean_logdir(p, cnt):
#    def get_basename(p):
#        p = os.path.basename(p)
#        basename, _tail = os.path.splitext(p)
#
#        while basename[-1] in '0123456789':
#            basename = basename[:-1]
#
#
#        return basename
#
#    d = os.path.dirname(p)
#    p = os.path.basename(p)
#    b = get_basename(p)
#    print 'cleaning {} for {}'.format(d, b)
#
#
#
#    import tarfile, time
#    name = 'logarchive-{}'.format(time.strftime('%m-%d-%y', time.localtime()))
#    cp, _cnt = unique_path(d, name, filetype='tar')
#
#    with tarfile.open(cp, 'w') as tar:
#        for i, pi in enumerate(os.listdir(d)):
#            if get_basename(pi) == b and i < (cnt - 5):
#                #print 'compress', i, cnt, pi
#                os.chdir(d)
#                tar.add(pi)
#                os.remove(pi)
#
#    print 'clean up finished'

rhandler = None

def logging_setup(name, **kw):
    '''
    '''

    # set up deprecation warnings
    import warnings
    warnings.simplefilter('default')

    # make sure we have a log directory
    bdir = os.path.join(paths.root, 'logs')
    if not os.path.isdir(bdir):
        os.mkdir(bdir)

    # create a new logging file
    logpath = os.path.join(bdir, '{}.current.log'.format(name))
    if os.path.isfile(logpath):
        backup_logpath, _cnt = unique_path(bdir, name, extension='log')
        shutil.copyfile(logpath, backup_logpath)
        os.remove(logpath)

    if sys.version.split(' ')[0] < '2.4.0':
        logging.basicConfig()
    else:

        root = logging.getLogger()
        shandler = logging.StreamHandler()

#        global rhandler
        rhandler = logging.handlers.RotatingFileHandler(
              logpath, maxBytes=1e7, backupCount=5)

        for hi in [shandler, rhandler]:
            hi.setLevel(gLEVEL)
            hi.setFormatter(logging.Formatter(gFORMAT))
            root.addHandler(hi)

#    new_logger('main')



def new_logger(name):
    name = '{:<{}}'.format(name, NAME_WIDTH)
    if name.strip() == 'main':
        l = logging.getLogger()
    else:
        l = logging.getLogger(name)
#    l = logging.getLogger(name)
    l.setLevel(gLEVEL)

    return l
#    '''
#    '''
#    return l
#============================== EOF ===================================

# MAXLEN = 30
# def add_console(logger=None, name=None,
#                display=None, level=LEVEL, unique=False):
# def add_console(logger=None, name=None):
#    '''
#
#    '''
#    if name:
#        n = '{:<{}}'.format(name, MAXLEN)
#        logger = new_logger(n)

#        if name == 'main':
#            shandler = logging.StreamHandler()
#    #        logger.setLevel(logging.NOTSET)
#            shandler.setLevel(logging.NOTSET)
#            shandler.setFormatter(logging.Formatter(gFORMAT))
#            logger.addHandler(shandler)
#        if unique:
#            i = 1
#            while logger in LOGGER_LIST:
#                n = '{}-{:03n}'.format(name, i)
#                n = '{:<{}}'.format(n, MAXLEN)
#
#                logger = new_logger(n)
#                i += 1

#    if logger and logger not in LOGGER_LIST:
#        LOGGER_LIST.append(logger)
#        #print use_debug_logger, name
#
#        if name == 'main' or not globalv.use_debug_logger:
#            console = logging.StreamHandler()
# ##
# ##            # tell the handler to use this format
#            console.setFormatter(logging.Formatter(gFORMAT))
# #            console.setLevel(logging.NOTSET)
# #
#            logger.addHandler(console)
            # rich text or styled text handlers
#            if display:
#
# #                _class_ = 'DisplayHandler'
# #                gdict = globals()
# #                if _class_ in gdict:
# #                    h = gdict[_class_]()
#                h = DisplayHandler()
#                h.output = display
#                h.setLevel(LEVEL)
#                h.setFormatter(FORMATTER)
#                logger.addHandler(h)

#    return logger
