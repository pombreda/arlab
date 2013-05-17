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
from traits.api import HasTraits, Property, Instance, on_trait_change
from traitsui.api import View, Item, ListEditor
from pyface.tasks.api import IEditor, IEditorAreaPane
from src.envisage.tasks.base_task import BaseTask, BaseManagerTask
from src.processing.tasks.processing_panes import ProcessorPane, OptionsPane
from src.processing.processor import Processor
from pyface.tasks.action.schema import SToolBar
from pyface.tasks.action.task_action import TaskAction
from pyface.image_resource import ImageResource
from src.paths import paths
from src.processing.tasks.processing_editor import ProcessingEditor
from src.graph.graph import Graph
from pyface.tasks.task_layout import PaneItem, TaskLayout, Splitter, Tabbed
from pyface.file_dialog import FileDialog
from pyface.constant import OK
from src.loggable import Loggable
from src.processing.plotter_options_manager import PlotterOptionsManager
#============= standard library imports ========================
#============= local library imports  ==========================

class ProcessingTask(BaseManagerTask, Loggable):
    active_editor = Property(Instance(IEditor),
                             depends_on='editor_area.active_editor'
                             )
#    active_editor = Instance(IEditor)
    editor_area = Instance(IEditorAreaPane)
    active_plotter_options = Instance(PlotterOptionsManager, ())
#    processor = Instance(Processor)
#    active_processor = Property(Instance(Processor),
#                             depends_on='_active_processor'
# #                             'editor_area.active_editor'
#                             )
#    _active_processor = Instance(Processor)

    tool_bars = [ SToolBar(TaskAction(method='new',
                                      tooltip='New file',
                                      image=ImageResource(
                                                          'document_new',
                                                          search_path=[paths.resources]
                                                          )),
                           TaskAction(method='open',
                                      tooltip='Open a file',
                                      image=ImageResource('document_open',
                                                          search_path=[paths.resources])),
                           TaskAction(method='save',
                                      tooltip='Save the current file',
                                      image=ImageResource('document_save',
                                                          search_path=[paths.resources]
                                                          )),

                           TaskAction(method='print_pdf',
                                      tooltip='Save current figure as PDF',
                                      image=ImageResource('file_pdf',
                                                          search_path=[paths.resources]
                                                          )),

                           image_size=(32, 32)), ]

    def _default_layout_default(self):
        return TaskLayout(left=PaneItem('pychron.processing.options'),
                                )
    def create_central_pane(self):
        self.editor_area = ProcessorPane()
        return self.editor_area

    def create_dock_panes(self):
        return [
                OptionsPane(model=self)
#                OptionsPane(model=self.active_editor)
                ]

    #===========================================================================
    # actions
    #===========================================================================
    def print_pdf(self):
        if self.active_editor:
            from chaco.pdf_graphics_context import PdfPlotGraphicsContext
            dialog = FileDialog(parent=self.window.control,
                                action='save as',
                                wildcard='*.pdf')
            if dialog.open() == OK:
                p = dialog.path
    #            p = '/Users/ross/Sandbox/figure_export.pdf'
                if p:
                    gc = PdfPlotGraphicsContext(filename=p,
                                                  pagesize='letter',
                                                  dest_box_units='inch')
                    gc.render_component(self.active_editor.component, valign='center')
                    gc.save()
                    self.info('saving figure to {}'.format(p))

    def new(self):
        ''' Opens a new empty window
        '''

        n = len(self.editor_area.editors)
        processor = Processor(application=self.application)
        editor = ProcessingEditor(
                                  processor=processor,
                                  name='Figure {:03n}'.format(n + 1),
                                  )


        po = editor.options_manager.plotter_options
        ideogram_container = processor.new_ideogram(plotter_options=po)
        editor.component = ideogram_container

        self.editor_area.add_editor(editor)
#        self.processor.active_editor = editor
        self.editor_area.activate_editor(editor)

        self.active_plotter_options = editor.options_manager

    def open(self):
        ''' Shows a dialog to open a file.
        '''
        dialog = FileDialog(parent=self.window.control, wildcard='*.py')
        if dialog.open() == OK:
            self._open_file(dialog.path)

#    @on_trait_change('editor_area:active_editor')
#    def _update_active_editor(self):
#        self.processor.active_editor = self.active_editor
    @on_trait_change('''active_plotter_options:plotter_options:[+, aux_plots:+]
''')
    def _options_update(self, name, new):
#        print name, 'new', new
        if name == 'initialized':
            return

        if self.active_editor:
            po = self.active_plotter_options.plotter_options
            pro = self.active_editor.processor
            cont = pro.new_ideogram(plotter_options=po, ans=pro.analyses)
            self.active_editor.component = cont
#        if self.analyses:

#            comp = self.new_ideogram(ans=self.analyses)
#            self.component = comp
#            if comp:
#                self.active_editor.component = comp
    @on_trait_change('editor_area:active_editor')
    def _update_plotter_options(self):
        if self.active_editor:
            self.active_plotter_options = self.active_editor.options_manager
#===============================================================================
# property get/set
#===============================================================================
    def _get_active_editor(self):
        if self.editor_area is not None:
            return self.editor_area.active_editor

        return None

#    def _processor_default(self):
#        return Processor(application=self.application)

#    def _get_active_processor(self):
# #        if self.editor_area is not None:
# #            print 'get active process 2', self.editor_area.active_editor
# #            if self.editor_area.active_editor:
# #                return self.editor_area.active_editor.processor
# #        active_editor = self.active_editor
# #        print 'get active process', self.editor_area, self.active_editor
#        if self._active_processor:
#            return self._active_processor
# #        if active_editor:
# #            return active_editor.processor
#        else:
#            return Processor(application=self.application)

#============= EOF =============================================