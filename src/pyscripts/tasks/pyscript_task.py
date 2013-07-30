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
from traits.api import HasTraits, String, List, Instance, Property, Any, Enum, \
    on_trait_change, Bool, Event, Int
from traitsui.api import View, Item, EnumEditor, UItem, Label
from pyface.tasks.task_layout import PaneItem, TaskLayout, Tabbed, Splitter
#============= standard library imports ========================
#============= local library imports  ==========================
from src.envisage.tasks.base_task import BaseManagerTask
from src.envisage.tasks.editor_task import EditorTask
from src.pyscripts.tasks.pyscript_editor import ExtractionEditor, MeasurementEditor, \
    BakeoutEditor
from src.pyscripts.tasks.pyscript_panes import CommandsPane, DescriptionPane, \
    ExamplePane, EditorPane, CommandEditorPane, ControlPane
from src.paths import paths
from src.ui.preference_binding import bind_preference
from src.pyscripts.extraction_line_pyscript import ExtractionPyScript
import os
from src.lasers.laser_managers.ilaser_manager import ILaserManager
from src.execute_mixin import ExecuteMixin
from src.pyscripts.laser_pyscript import LaserPyScript



class PyScriptTask(EditorTask, ExecuteMixin):
    name = 'PyScript'
    kind = String
    kinds = List(['Extraction', 'Measurement'])
    commands_pane = Instance(CommandsPane)

    wildcard = '*.py'
    auto_detab = Bool(False)

    _current_script = Any
    use_trace = Bool(False)
    trace_delay = Int(50)
    def _runner_factory(self):
        # get the extraction line manager's mode
        man = self._get_el_manager()

        if man is None:
            self.warning_dialog('No Extraction line manager available')
            mode = 'normal'
        else:
            mode = man.mode

        if mode == 'client':
#            em = self.extraction_line_manager
            from src.helpers.parsers.initialization_parser import InitializationParser
            ip = InitializationParser()
            elm = ip.get_plugin('Experiment', category='general')
            runner = elm.find('runner')
            host, port, kind = None, None, None

            if runner is not None:
                comms = runner.find('communications')
                host = comms.find('host')
                port = comms.find('port')
                kind = comms.find('kind')

            if host is not None:
                host = host.text  # if host else 'localhost'
            if port is not None:
                port = int(port.text)  # if port else 1061
            if kind is not None:
                kind = kind.text  # if kind else 'udp'

            from src.pyscripts.pyscript_runner import RemotePyScriptRunner
            runner = RemotePyScriptRunner(host, port, kind)
        else:
            from src.pyscripts.pyscript_runner import PyScriptRunner
            runner = PyScriptRunner()

        return runner

    def _get_el_manager(self):
        app = self.window.application
        man = app.get_service('src.extraction_line.extraction_line_manager.ExtractionLineManager')
        return man

    def _do_execute(self):
        self.debug('do execute')

        self._current_script = None
        ae = self.active_editor
        if isinstance(ae, ExtractionEditor):
            root, fn = os.path.split(ae.path)
            kind = self._extract_kind(ae.path)
            klass = ExtractionPyScript
            if kind == 'Laser':
                klass = LaserPyScript

            script = klass(
                            application=self.window.application,
                            root=root,
                            name=fn,
                            runner=self._runner)

            if script.bootstrap():
                script.set_default_context()
                try:
                    script.test()
                except Exception, e:
                    return
                self._current_script = script
                script.setup_context(extract_device='fusions_diode')
                if self.use_trace:
                    self.active_editor.trace_delay = self.trace_delay

                t = script.execute(
#                                    new_thread=True,
                                   trace=self.use_trace
                                   )
#                 t.join()


        self.executing = False

    def _start_execute(self):
        self.debug('start execute')

        # make a script runner
        self._runner = None
        runner = self._runner_factory()
        if runner is None:
            return
        else:
            self._runner = runner
            return True

    def _cancel_execute(self):
        self.debug('cancel execute')
        if self._current_script:
            self._current_script.cancel()

    def __init__(self, *args, **kw):
        super(PyScriptTask, self).__init__(*args, **kw)
        bind_preference(self, 'auto_detab', 'pychron.pyscript.auto_detab')

    def activated(self):
        from pyface.timer.do_later import do_later
        do_later(self.window.reset_layout)

    def _default_directory_default(self):
        return paths.scripts_dir

    def _default_layout_default(self):
        return TaskLayout(
                          id='pychron.pyscript',
                          left=Splitter(

                                        PaneItem('pychron.pyscript.control',
                                          height=100),

                                        PaneItem('pychron.pyscript.commands_editor',
                                          height=100,
                                          width=510,
                                          ),
#                                      Tabbed(
                                            PaneItem('pychron.pyscript.editor',
                                              width=510,
                                              ),
#                                             PaneItem('pychron.pyscript.commands',
#                                               width=525,
#                                               ),
                                        orientation='vertical',
                                     ),
#                                 ),
                          right=PaneItem('pychron.pyscript.commands',
                                         width=175),
#                          top=PaneItem('pychron.pyscript.description'),
#                           bottom=
                          )
    def create_dock_panes(self):
        self.commands_pane = CommandsPane()
        self.command_editor_pane = CommandEditorPane()
        self.editor_pane = EditorPane()
        self.control_pane = ControlPane(model=self)
        return [
                self.commands_pane,
                self.command_editor_pane,
                self.editor_pane,
                self.control_pane,
                ]

    @on_trait_change('commands_pane:command_object')
    def _update_selected(self, new):
        self.command_editor_pane.command_object = new

    def _active_editor_changed(self):
        if self.active_editor:
            self.commands_pane.name = self.active_editor.kind

            self.commands_pane.command_objects = self.active_editor.commands.command_objects
            self.commands_pane.commands = self.active_editor.commands.script_commands
            self.editor_pane.editor = self.active_editor.editor

    def _save_file(self, path):
        self.active_editor.dump(path)

    def find(self):
        if self.active_editor:
            self.active_editor.control.enable_find()

    def replace(self):
        if self.active_editor:
            self.active_editor.control.enable_replace()

    def new(self):

        # todo ask for script type
        info = self.edit_traits(view='kind_select_view')
        if info.result:
            self._open_editor(path='')
            return True

    def open(self):
#         path = '/Users/ross/Pychrondata_diode/scripts/measurement/jan_unknown.py'
#         path = '/Users/ross/Pychrondata_diode/scripts/extra/jan_unknown.py'
#        path = '/Users/ross/Pychrondata_diode/scripts/extraction/jan_diode.py'
#        path = '/Users/ross/Pychrondata_demo/scripts/laser/zoom_scan.py'
#         path = os.path.join(paths.scripts_dir, 'lasers', 'video_test.py')
        path = os.path.join(paths.scripts_dir, 'laser', 'power_map.py')
        self._open_file(path)
        return True

    def _open_file(self, path, **kw):
        self.info('opening pyscript: {}'.format(path))
        self._open_editor(path, **kw)

    def _extract_kind(self, path):
        with open(path, 'r') as fp:
            for line in fp:
                if line.startswith('#!'):
                    return line.strip()[2:]

    def _open_editor(self, path, kind=None):
        if path:
            kind = self._extract_kind(path)

        if kind == 'Measurement':
            klass = MeasurementEditor
        elif kind == 'Bakeout':
            klass = BakeoutEditor
        else:
            klass = ExtractionEditor

        editor = klass(path=path,
                       auto_detab=self.auto_detab,
                       )

        super(PyScriptTask, self)._open_editor(editor)

    @on_trait_change('_current_script:trace_line')
    def _update_lineno(self, new):
        self.active_editor.highlight_line = new

    def _get_description(self):
        if self.selected:
            return self.selected.description
        return ''

    def _get_example(self):
        if self.selected:
            return self.selected.example
        return ''

#============= EOF =============================================
