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
from traits.api import Str, Enum, Bool, Instance, String, Dict, Property, \
     Event, Button, Any, List, Int
from traitsui.api import View, Item, HGroup, Group, spring, \
    Handler, VGroup, HTMLEditor, CodeEditor, ShellEditor, ListStrEditor, InstanceEditor

#============= standard library imports ========================
import os
#============= local library imports  ==========================
from src.managers.manager import Manager
from traitsui.menu import Action
from src.paths import paths
from pyface.api import warning
#from src.pyscripts.pyscript import PyScript, HTML_HELP
from src.pyscripts.pyscript_runner import PyScriptRunner
import time
from pyface.message_dialog import information
from src.saveable import SaveableHandler
from src.pyscripts.code_editor import PyScriptCodeEditor
#from traitsui.wx.code_editor import SourceEditor
#from traitsui.wx.basic_editor_factory import BasicEditorFactory
#from traitsui.editors.code_editor import ToolkitEditorFactory

SCRIPT_PKGS = dict(Bakeout='src.pyscripts.bakeout_pyscript',
                    ExtractionLine='src.pyscripts.extraction_line_pyscript',
                    Measurement='src.pyscripts.measurement_pyscript'
                    )
#SCRIPT_PATHS = dict(Bakeout=('src.scripts.pyscripts.bakeout_pyscript', 'BakeoutScript',
#                             'src.scripts.bakeout_script_parser',
#                             'BakeoutScriptParser',
#                             ),
#
#                    ExtractionLine=('src.scripts.extraction_line_pyscript',
#                                             'ExtractionLineScript',
#                            'src.scripts.extraction_line_script_parser',
#                            'ExtractionLineScriptParser',
#                                             )
#                            )

SCRIPT_EXTENSIONS = dict(bakeout='.bo')

class ScriptHandler(SaveableHandler):
    def init(self, info):
        info.object.ui = info.ui
        if not info.initialized:
#            info.object.load_help()
            info.object.load_context()
            info.object.load_commands()

    def open_script(self, info):
        info.object.open_script()

    def test_script(self, info):
        info.object.test_script()

#    def execute_script(self, info):
#        info.object.execute_script()

    def object_save_path_changed(self, info):
        if info.initialized:
            info.ui.title = 'Script Editor - {}'.format(info.object.save_path)


class PyScriptManager(Manager):
    show_kind = Bool(False)
    kind = Enum('ExtractionLine', 'Bakeout', 'Measurement')
    body = String('''def main():
    sleep(10)
    ramp(100,10)
    setpoint(150,4)
    ramp(0,-75)
''')

    save_enabled = Bool(False)
    _executing = Bool(False)
    execute_enabled = Bool(False)
    execute_visible = Bool(True)

    save_path = String
    _original_body = Str
    _parser = None
    title = 'Script Editor - '

    default_directory_name = Str
    context = Dict

    execute_button = Event
    execute_label = Property(depends_on='_executing')

    calc_graph_button = Button('Graph Profile')
#    help_button = Button('Help')

    runner = Instance(PyScriptRunner, ())
    name_count = 0

    scripts = Dict

    core_commands = List
    script_commands = List
    selected_command = Str
    selected_index = Int
    selected_command_object = Property(depends_on='selected_command')

    def _get_execute_label(self):
        return 'Stop' if self._executing else 'Execute'

    def _execute_button_fired(self):
        if self._executing:
            self._executing = False
            self.stop_script()
        else:
            self._executing = True
            self.execute_script()

    def _calc_graph_button_fired(self):
        ps = self._pyscript_factory(self.kind, runner=self.runner)
        ps.set_text(self.body)

        #graph calculated in secs
        ps.calculate_graph()

    def _check_save(self):
        return self.test_script(report_success=False)

    def _get_default_directory(self):
        if self.default_directory_name:
            return os.path.join(paths.scripts_dir, self.default_directory_name)
        else:
            return paths.scripts_dir

    def save_as(self):
        if not self._check_save():
            return

        p = self.save_file_dialog(default_directory=self._get_default_directory())
#        p = '/Users/ross/Desktop/foo.txt'
        if p is not None:
#            ext = SCRIPT_EXTENSIONS[self.kind.lower()]
            ext = '.py'
            if not p.endswith(ext):
                p += ext

            self._dump_script(p)
            self.save_path = p

    def save(self):
        if not self._check_save():
            return

        p = self.save_path
        self._dump_script(p)
        self.save_enabled = False

    def _pyscript_factory(self, klassname, **kw):

        klassname = '{}PyScript'.format(klassname)
        m = __import__(SCRIPT_PKGS[self.kind], fromlist=[klassname])
        klass = getattr(m, klassname)
        if self.save_path:
            r, n = os.path.split(self.save_path)
            kw['root'] = r
            kw['name'] = n
        else:
            kw['root'] = os.path.join(paths.scripts_dir, 'pyscripts')

        return klass(manager=self.parent,
                     parent=self,
                     **kw)

    def load_context(self):
#        ps = PyScript(manager=self.parent)
        ps = self._pyscript_factory(self.kind)
        ps.bootstrap()

        self.context = ps.get_context()

    def load_commands(self):
        ps = self._pyscript_factory(self.kind)
        prepcommands = lambda cmds: [c[0] if isinstance(c, tuple) else c for c in cmds]

#        self.core_commands = prepcommands(ps.get_core_commands())
#        self.script_commands = prepcommands(ps.get_script_commands())
        self.script_commands = prepcommands(ps.get_commands())
        self.script_commands.sort()

    def open_script(self, path=None):
        if path is None:
            path = self.open_file_dialog(default_directory=self._get_default_directory())
#        p = os.path.join(self._get_default_directory(), 'btest.py')
        if path is not None:
            self._load_script(path)
            self.save_path = path

    def test_script(self, report_success=True):
        self.execute_enabled = False
#        if os.path.isfile(self.save_path):
#            root, name = os.path.split(self.save_path)
#            ps = PyScript(root=root,
#                        name=name)
        ps = self._pyscript_factory(self.kind)
        ps.set_text(self.body)

        ps.bootstrap(load=False)
        try:
            err = ps._test()
        except Exception, err:
            pass

        if err:
            warning(None, 'This is not a valid PY script\n{}'.format(err))
        else:
            if report_success:
                n = 'new script' if not self.save_path else os.path.basename(self.save_path)
                msg = 'No syntax errors found in {}'.format(n)
                information(None, msg)
                self.info(msg)
            self.execute_enabled = True
            return True

    def stop_script(self):
        self.script.cancel()

    def execute_script(self, path=None):
#        open_manager(self.application,
#                     self.runner)

        ps = self._pyscript_factory(self.kind, runner=self.runner)
        load = False
        if path is None:
            ps.set_text(self.body)
        else:
            load = True
            r, n = os.path.split(path)
            ps.root = r
            ps.name = n
            ps.logger_name = self._generate_unique_name(n)

        ps.bootstrap(load=load)
        ps.execute(new_thread=True)
        self.script = ps

        key = self._generate_unique_key(ps)
        ps.hash_key = key
        self.scripts[key] = ps
        return key

    def get_script_state(self, key):
        try:
            ps = self.scripts[key]
            return ps.state
        except KeyError:
            #assume the script has completed
            # if it isnt in the scripts dictionary
            # the script is remove by the runner when it completes
            return '2k'

    def _generate_unique_key(self, ps):
        from hashlib import md5

        seed = '{}{}'.format(ps.logger_name, time.time())
        return md5(seed).hexdigest()

    def _generate_unique_name(self, name):
        self.name_count += 1
        return '{}-{:03n}'.format(name, self.name_count)

    def _load_script(self, p):
        self.info('loading script {}'.format(p))
        with open(p, 'r') as f:
            self.body = f.read()
            self._original_body = self.body

    def _dump_script(self, p):

        self.info('saving script to {}'.format(p))
        with open(p, 'w') as f:
            f.write(self.body)
        self._original_body = self.body


#===============================================================================
# handlers
#===============================================================================
    def _body_changed(self):
        if self._original_body:
            if self.body == self._original_body:
                self.save_enabled = False
            else:
                self.execute_enabled = False
                self.save_enabled = True

    def _command_text_factory(self, scmd):
        #convert to klass name.
        #camel_case

        cmd = self._command_object(scmd)
        return cmd.get_text()

    def _get_selected_command_object(self):
        a = self._command_object(self.selected_command)
        return a

    def _command_object(self, scmd):
        cmd = None
        words = scmd.split('_')
        klass = ''.join(map(str.capitalize, words))

        pkg = 'src.pyscripts.commands.api'
        cmd_name = '{}_command_editor'.format(scmd)
#        print cmd_name, klass
        try:
            cmd = getattr(self, cmd_name)
        except AttributeError:
            m = __import__(pkg, globals={}, locals={}, fromlist=[klass])
            try:
                cmd = getattr(m, klass)()
                setattr(self, cmd_name, cmd)
            except AttributeError, e :
                print e

        return cmd
#    def _selected_command_changed(self):
#        scmd = self.selected_command
#        if scmd:
#            cmd = self._command_text_factory(scmd)
#            m = cmd.get_text()
#            if m:
#                self.body += m + '\n'
#            self.selected_command = ''

#===============================================================================
# views
#===============================================================================
#    def help_view(self):
#        v = View(Item('help_message',
#                              editor=HTMLEditor(),
#                              show_label=False),
#                 resizable=True,
#                 width=700,
#                 height=0.85,
#                 x=0.5,
#                 title='{}PyScript Help'.format(self.kind)
#                 )
#        return v

    def _get_commands_group(self, name, label):
        return Group(Item(name,
                   style='custom',
                   show_label=False,
                   editor=ListStrEditor(operations=[],
                                        editable=False,
#                                        right_clicked='',
                                        selected='selected_command'
                                        ),
                         width=200,
                         height=400,
                         resizable=False
                           ),
                     label=label,
                     show_border=True,
                     )

    def traits_view(self):
        help_grp = Group(
                       Item('selected_command_object',
                            show_label=False,
                            style='custom',
                            height=300,
                            editor=InstanceEditor(view='help_view')
                            ),
#                       label='Help',
#                       show_border=True
                       )

        editor = VGroup(HGroup(spring, 'kind', visible_when='show_kind'),
                        Item('body', editor=PyScriptCodeEditor(),
                             show_label=False),
                        help_grp
                        )

        command_grp = VGroup(
#                             self._get_commands_group('core_commands', 'Core'),
                             self._get_commands_group('script_commands', self.kind),

                        )

        v = View(VGroup(
                    HGroup(
                            command_grp,
                            editor,
                            ),
                    HGroup(
                           self._button_factory('execute_button', 'execute_label',
                                  enabled_when='object.execute_enabled',
                                  visible_when='object.execute_visible',
                                  align='left'),
#                               Item('calc_graph_button', show_label=False)
                       ),
                 ),
                 resizable=True,
                 buttons=[
                          Action(name='Test', action='test_script'),
                          Action(name='Open', action='open_script'),
                          Action(name='Save', action='save',
                                enabled_when='object.save_enabled'),
                          Action(name='Save As', action='save_as')
                          ],
                 width=700,
                 height=575,
                 handler=ScriptHandler,
                 title=self.title
                 )
        return v

if __name__ == '__main__':
    from src.helpers.logger_setup import logging_setup

    logging_setup('scripts')
#    s = PyScriptManager(kind='ExtractionLine')
#    s = PyScriptManager(kind='Bakeout')
    s = PyScriptManager(kind='Measurement')
#    p = os.path.join(paths.scripts_dir, 'ms_runscripts', 'Quick Air x1.py')

#    s.open_script(path=p)
    s.configure_traits()
#============= EOF =============================================
