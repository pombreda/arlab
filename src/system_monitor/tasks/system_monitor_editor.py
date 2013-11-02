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
from datetime import datetime, timedelta
from threading import Thread
import time
from traits.api import Instance, Property, Int, Bool, on_trait_change, Any

#============= standard library imports ========================
#============= local library imports  ==========================
from src.displays.display import DisplayController
from src.messaging.notify.subscriber import Subscriber
from src.processing.plotter_options_manager import SystemMonitorOptionsManager
from src.processing.tasks.figures.editors.series_editor import SeriesEditor
from src.system_monitor.tasks.connection_spec import ConnectionSpec
from src.system_monitor.tasks.controls import SystemMonitorControls
from src.ui.gui import invoke_in_main_thread
from src.processing.utils.grouping import group_analyses_by_key

"""
    subscribe to pyexperiment
    or poll database for changes

    use poll to check subscription availability
    suspend db poll when subscription becomes available

"""


def camel_case(name):
    args = name.split('_')
    return ''.join(map(str.capitalize, args))


class SystemMonitorEditor(SeriesEditor):
    conn_spec = Instance(ConnectionSpec, ())
    name = Property(depends_on='conn_spec:+')
    tool = Instance(SystemMonitorControls)
    subscriber = Instance(Subscriber)
    plotter_options_manager_klass = SystemMonitorOptionsManager

    use_poll = Bool(False)
    _poll_interval = Int(10)
    _db_poll_interval = Int(10)
    _polling = False
    pickle_path = 'system_monitor'

    console_display = Instance(DisplayController)
    _ideogram_editor = None
    _spectrum_editor = None

    _air_editor = None
    _blank_air_editor = None
    _cocktail_editor = None
    _blank_cocktail_editor = None
    _background_editor = None

    task = Any

    def prepare_destroy(self):
        self.stop()
        self.dump_tool()
        for e in ('ideogram', 'spectrum',
                  'air', 'blank_air',
                  'cocktail', 'blank_cocktail',
                  'background'):
            e = getattr(self, '_{}_editor'.format(e))
            if e is not None:
                e.dump_tool()

    def stop(self):
        self._polling = False
        self.subscriber.stop()

    def console_message_handler(self, msg):
        color = 'green'
        if '|' in msg:
            color, msg = msg.split('|')

        self.console_display.add_text(msg, color=color)

    def run_added_handler(self, last_run_uuid=None):
        """
            add to sys mon series
            if atype is blank, air, cocktail, background
                add to atype series
            else
                if step heat
                    add to spectrum
                else
                    add to ideogram
        """
        self.info('refresh analyses. last UUID={}'.format(last_run_uuid))
        return

        proc = self.processor
        db = proc.db
        with db.session_ctx():
            dbrun = db.get_analysis_uuid(last_run_uuid)
            if not dbrun:
                dbrun = db.get_last_analysis(spectrometer=self.conn_spec.system_name)

            if dbrun:
                an = proc.make_analysis(dbrun)
                self._refresh_sys_mon_series(an)
                self._refresh_figures(an)

    def start(self):
        self.load_tool()

        if self.conn_spec.host:
            sub = self.subscriber
            connected = sub.connect(timeout=1)

            sub.subscribe('RunAdded', self.run_added_handler, True)
            sub.subscribe('ConsoleMessage', self.console_message_handler)

            if connected:
                sub.listen()
                self.task.connection_pane.connection_status = 'Connected'
                self.task.connection_pane.connection_color = 'green'

            else:
                self.task.connection_pane.connection_status = 'Not Connected'
                self.task.connection_pane.connection_color = 'red'

                url = self.conn_spec.url
                self.warning('System publisher not available url={}'.format(url))

        t = Thread(name='poll', target=self._poll)
        t.setDaemon(True)
        t.start()

    def _dump_tool(self):
        return self.tool

    def _load_tool(self, obj):
        self.tool = obj

    def _poll(self):
        self._polling = True
        last_run_uuid = self._get_last_run_uuid()
        sub = self.subscriber

        db_poll_interval = self._db_poll_interval
        poll_interval = self._poll_interval

        st = time.time()
        while 1:
            #check subscription availablity
            if sub.check_server_availability(timeout=0.5, verbose=True):
                if not sub.is_listening():
                    self.info('Subscription server now available. starting to listen')
                    self.subscriber.listen()
            else:
                if sub.was_listening:
                    self.warning('Subscription server no longer available. stop listen')
                    self.subscriber.stop()

            if self._wait(poll_interval):
                if not sub.is_listening():
                    if time.time() - st > db_poll_interval:
                        st = time.time()
                        lr = self._get_last_run_uuid()
                        self.debug('current uuid {} <> {}'.format(last_run_uuid, lr))
                        if lr != last_run_uuid:
                            last_run_uuid = lr
                        invoke_in_main_thread(self.run_added_handler, lr)
            else:
                break

    def _wait(self, t):
        st = time.time()
        while time.time() - st < t:
            if not self._polling:
                return
            time.sleep(0.5)

        return True

    def _get_last_run_uuid(self):
        db = self.processor.db
        with db.session_ctx():
            dbrun = db.get_last_analysis(spectrometer=self.conn_spec.system_name)
            if dbrun:
                return dbrun.uuid

    def _refresh_sys_mon_series(self, an):

        ms = an.mass_spectrometer
        kw = dict(weeks=self.tool.weeks,
                  days=self.tool.days,
                  hours=self.tool.hours,
                  limit=self.tool.limit)

        ans = self.processor.analysis_series(ms,
                                             **kw)
        self.unknowns = ans

    def _refresh_figures(self, an):
        if an.analysis_type == 'unknown':
            if an.step:
                self._refresh_spectrum(an.labnumber, an.aliquot)
            else:
                self._refresh_ideogram(an.labnumber)
        else:
            atype = an.analysis_type

            func = getattr(self, '_refresh_{}'.format(atype))
            func(an.labnumber)

    def _refresh_air(self, identifier):
        self._set_series('air', identifier)

    def _refresh_blank_air(self, identifier):
        self._set_series('blank_air', identifier)

    def _refresh_cocktail(self, identifier):
        self._set_series('cocktail', identifier)

    def _refresh_blank_cocktail(self, identifier):
        self._set_series('blank_coctkail', identifier)

    def _refresh_background(self, identifier):
        self._set_series('background', identifier)

    def _set_series(self, attr, identifier):
        name = '_{}_editor'.format(attr)
        editor = getattr(self, name)

        def new():
            e = self.task.new_series(ans=[],
                                     add_table=False,
                                     add_iso=False)
            self.task.tab_editors(0, -1)
            e.basename = '{} Series'.format(camel_case(attr))
            return e

        editor = self._update_editor(editor, new, identifier, None, layout=False)
        setattr(self, name, editor)

    def _refresh_ideogram(self, identifier):
        """
            open a ideogram editor if one is not already open
        """
        editor = self._ideogram_editor
        f = lambda: self.task.new_ideogram(add_table=False, add_iso=False)
        editor = self._update_editor(editor, f, identifier, None)
        self._ideogram_editor = editor

    def _refresh_spectrum(self, identifier, aliquot):
        editor = self._spectrum_editor
        f = lambda: self.task.new_spectrum(add_table=False, add_iso=False)
        editor = self._update_editor(editor, f, identifier, aliquot)
        self._spectrum_editor = editor

    def _update_editor(self, editor, editor_factory,
                       identifier, aliquot, layout=True,
                       use_date_range=False):
        if editor is None:
            editor = editor_factory()
            if layout:
                self.task.split_editors(-2, -1)
        else:
            if not self._polling:
                self.task.activate_editor(editor)

        #gather analyses
        ans = self._get_analyses(identifier,
                                 aliquot, use_date_range)

        editor.unknowns = ans
        group_analyses_by_key(editor, editor.unknowns, 'labnumber')
        #        self.task.group_by_labnumber()

        return editor

    def _get_analyses(self, identifier, aliquot=None, use_date_range=False):
        db = self.processor.db
        with db.session_ctx():
            limit = self.tool.limit
            if aliquot is not None:
                def func(a, l):
                    return l.identifier == identifier, a.aliquot == aliquot

                ans = db.get_analyses(func=func, limit=limit)
            elif use_date_range:
                end = datetime.now()
                start = end - timedelta(hours=self.tool.hours,
                                        weeks=self.tool.weeks,
                                        days=self.tool.days)

                ans = db.get_analyses_date_range(start, end,
                                                 labnumber=identifier,
                                                 limit=limit)
            else:
                ans = db.get_labnumber_analyses(identifier, limit=limit)

            return self.processor.make_analyses(ans)

    @on_trait_change('tool:[+, refresh_button]')
    def _handle_tool_change(self):
        self.run_added_handler()

    def _load_refiso(self, ref):
        pass

    def _set_name(self):
        pass

    def _get_name(self):
        return '{}-{}'.format(self.conn_spec.system_name,
                              self.conn_spec.host)

    def _tool_default(self):
        tool = SystemMonitorControls()
        return tool

    def _console_display_default(self):
        return DisplayController(
            bg_color='black',
            default_color='limegreen',
            max_blocks=100)

    def _subscriber_default(self):
        h = self.conn_spec.host
        p = self.conn_spec.port

        self.info('Creating subscriber to {}:{}"'.format(h, p))
        sub = Subscriber(host=self.conn_spec.host,
                         port=self.conn_spec.port,
                         verbose=False)
        return sub
        #============= EOF =============================================