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
from traits.api import Any, on_trait_change, Event, List, Unicode
# from traitsui.api import View, Item
from pyface.tasks.task import Task
from pyface.tasks.action.schema import SMenu, SMenuBar, SGroup
# from pyface.tasks.action.task_toggle_group import TaskToggleGroup
# from envisage.ui.tasks.action.task_window_toggle_group import TaskWindowToggleGroup
from envisage.ui.tasks.action.api import TaskWindowLaunchGroup
from pyface.action.api import ActionItem, Group
# from pyface.tasks.action.task_action import TaskAction
from envisage.ui.tasks.action.task_window_launch_group import TaskWindowLaunchAction
from pyface.tasks.task_window_layout import TaskWindowLayout
from src.envisage.tasks.actions import GenericSaveAction, GenericSaveAsAction, \
    GenericFindAction, RaiseAction, RaiseUIAction, ResetLayoutAction, \
    MinimizeAction, PositionAction, IssueAction, CloseAction, CloseOthersAction
from pyface.file_dialog import FileDialog
from pyface.constant import OK, CANCEL
from itertools import groupby
from pyface.confirmation_dialog import ConfirmationDialog
from src.loggable import Loggable
from pyface.timer.do_later import do_later

#============= standard library imports ========================
#============= local library imports  ==========================

class WindowGroup(Group):
    items = List
    manager = Any

    def _manager_default(self):
        manager = self
        while isinstance(manager, Group):
            manager = manager.parent



        #         application = self.manager.controller.task.window.application

        #         t = 'active_window, window_opened, window_closed, windows, uis[]'
        #         application.on_trait_change(self._rebuild, t)
        return manager

    def _items_default(self):
        application = self.manager.controller.task.window.application

        t = 'active_window, window_opened, window_closed, windows, uis[]'
        application.on_trait_change(self._rebuild, t)
        #         application = self.manager.controller.task.window.application
        #         application.on_trait_change(self._rebuild, 'window_opened, window_closed, uis[]')
        return []

    def _make_actions(self, vs):
        items = []
        if self.manager.controller.task.window is not None:
            application = self.manager.controller.task.window.application
            added = []
            for vi in application.windows + vs:
                if hasattr(vi, 'active_task'):
                    if vi.active_task:
                        if not vi.active_task.id in added:
                            checked = vi == application.active_window
                            items.append(ActionItem(action=RaiseAction(window=vi,
                                                                       checked=checked,
                                                                       name=vi.active_task.name
                            )))
                            added.append(vi.active_task.id)
                else:
                    items.append(ActionItem(action=RaiseUIAction(
                        name=vi.title or vi.id,
                        ui=vi,
                        checked=checked,
                    )))

        return items

    def _rebuild(self, obj, name, old, vs):
        self.destroy()

        if name == 'window_opened':
            vs = vs.window
        else:
            vs = []

        if not isinstance(vs, list):
            vs = [vs]

        self.items = self._make_actions(vs)
        self.manager.changed = True


class myTaskWindowLaunchAction(TaskWindowLaunchAction):
    '''
        modified TaskWIndowLaunchAction default behaviour
        
        .perform() previously created a new window on every event. 
        
        now raise the window if its available else create it
    '''

    style = 'toggle'

    def perform(self, event):
        application = event.task.window.application
        application.open_task(self.task_id)

        self.checked = True

    @on_trait_change('task:window:opened')
    def _window_opened(self):
        if self.task:
            if self.task_id == self.task.id:
                self.checked = True

    @on_trait_change('task:window:closed')
    def _window_closed(self):
        if self.task:
            if self.task_id == self.task.id:
                self.checked = False

#             window = self.task.window
#             print win, window
#             print self.task_id, self.task.id
#             self.checked=self.task.window==win
#             print window.active_task, self.task
#
#             self.checked = (window is not None
#                             and window.active_task == self.task)

#     @on_trait_change('task:window:opened')
#     def _window_o(self):
#         self.checked=True

#     @on_trait_change('task:window:closed')
#     def _window_c(self):
#         self.checked=False
#         print 'asdfsafdasdf'

#     @on_trait_change('foo')
#     def _update_checked(self):
#         print 'fffff'
#         self.checked=True
# #         if self.task:
#             window = self.task.window
#             self.checked = (window is not None
#                             and window.active_task == self.task)
#         print self.checked
# class myTaskWindowLaunchGroup(TaskWindowLaunchGroup):
#     '''
#         uses myTaskWindowLaunchAction instead of enthoughts TaskWindowLaunchLaunchGroup
#     '''
#     def _items_default(self):
#         manager = self
#         while isinstance(manager, Group):
#             manager = manager.parent
#
#         task = manager.controller.task
#         application = task.window.application
#
#         groups = []
#         def groupfunc(task_factory):
#             gid = 0
#             if hasattr(task_factory, 'task_group'):
#                 gid = task_factory.task_group
#
#             return gid
#
#         for gi, factories in groupby(application.task_factories, groupfunc):
#             items = []
#             for factory in factories:
# #         for factory in application.task_factories:
#                 for win in application.windows:
#                     if win.active_task:
#                         if win.active_task.id == factory.id:
#                             checked = True
#                             break
#                 else:
#                     checked = False
#
#                 action = myTaskWindowLaunchAction(task_id=factory.id,
#                                                   checked=checked)
#
#                 if hasattr(factory, 'accelerator'):
#                     action.accelerator = factory.accelerator
#                     print action.accelerator
#                     items.append(ActionItem(action=action))
#                 print items
#             groups.append(Group(*items))
#
#         return groups
#
class TaskGroup(Group):
    items = List


class BaseTask(Task, Loggable):
    def _show_pane(self, p):
        ctrl = p.control
        if not p.visible:
            ctrl.show()
        ctrl.raise_()

    def _menu_bar_factory(self, menus=None):
        if not menus:
            menus = []

        mb = SMenuBar(
            self._file_menu(),
            self._edit_menu(),
            self._view_menu(),
            self._tools_menu(),
            self._window_menu(),
            self._help_menu(),
            #                       SMenu(
            #                             ViewMenuManager(),
            #                             id='Window', name='&Window'),


            #                       *menus
        )
        if menus:
            for mi in reversed(menus):
                mb.items.insert(4, mi)

        return mb

    def _menu_bar_default(self):
        return self._menu_bar_factory()

    def _view_groups(self):
        def groupfunc(task_factory):
            gid = 0
            if hasattr(task_factory, 'task_group'):
                gid = task_factory.task_group
                if gid:
                    gid = ('hardware', 'experiment').index(gid) + 1
                else:
                    gid = 0

            return gid

        application = self.window.application
        groups = []
        for _, factories in groupby(sorted(application.task_factories,
                                           key=groupfunc),
                                    key=groupfunc):
            items = []
            for factory in factories:
                for win in application.windows:
                    if win.active_task:
                        if win.active_task.id == factory.id:
                            checked = True
                            break
                else:
                    checked = False

                action = myTaskWindowLaunchAction(task_id=factory.id,
                                                  checked=checked)

                if hasattr(factory, 'accelerator'):
                    action.accelerator = factory.accelerator
                add = True
                if hasattr(factory, 'include_view_menu'):
                    add = factory.include_view_menu
                if add:
                    items.append(ActionItem(action=action))

            groups.append(TaskGroup(items=items))
        return groups

    def _view_menu(self):
        grps = self._view_groups()
        view_menu = SMenu(
            *grps,
            id='View', name='&View')
        return view_menu

    def _edit_menu(self):
        edit_menu = SMenu(
            GenericFindAction(),
            id='Edit',
            name='Edit')
        return edit_menu

    def _file_menu(self):
        file_menu = SMenu(
            SGroup(id='Open'),
            SGroup(id='New'),
            SGroup(
                GenericSaveAsAction(),
                GenericSaveAction(),
                id='Save'
            ),
            SGroup(),
            #                         SMenu(id='Open', name='Open',),
            #                         SMenu(id='New', name='New'),

            #                         Group(
            #                                GenericSaveAsAction(),
            #                                GenericSaveAction(),
            #                                id='Save'
            #                                ),
            #
            #                           SGroup(),
            #
            #                                 ),

            id='File', name='File')
        return file_menu

    def _tools_menu(self):
        tools_menu = SMenu(id='Tools', name='Tools')
        return tools_menu

    def _window_menu(self):
        window_menu = SMenu(
            Group(
                CloseAction(),
                CloseOthersAction(),
                id='Close'
            ),
            Group(MinimizeAction(),
                  ResetLayoutAction(),
                  PositionAction(),
            ),
            WindowGroup(),
            id='Window',
            name='Window')

        return window_menu

    def _help_menu(self):
        menu = SMenu(
            IssueAction(),
            id='help.menu',
            name='Help')
        return menu

    def _confirmation(self, message=''):
        dialog = ConfirmationDialog(parent=self.window.control,
                                    message=message, cancel=True,
                                    default=CANCEL, title='Save Changes?')
        return dialog.open()


class BaseManagerTask(BaseTask):
    default_directory = Unicode
    wildcard = None
    manager = Any

    def open_file_dialog(self, action='open', **kw):
        if 'default_directory' not in kw:
            kw['default_directory'] = self.default_directory

        if 'wildcard' not in kw:
            if self.wildcard:
                kw['wildcard'] = self.wildcard

        dialog = FileDialog(parent=self.window.control,
                            action=action,
                            **kw)
        if dialog.open() == OK:
            r = dialog.path
            if action == 'open files':
                r = dialog.paths
            return r

    def save_file_dialog(self, **kw):
        if 'default_directory' not in kw:
            kw['default_directory'] = self.default_directory
        dialog = FileDialog(parent=self.window.control, action='save as',
                            **kw
        )
        if dialog.open() == OK:
            return dialog.path


class BaseExtractionLineTask(BaseManagerTask):
    def _get_el_manager(self):
        app = self.window.application
        man = app.get_service('src.extraction_line.extraction_line_manager.ExtractionLineManager')
        return man

    def prepare_destroy(self):
        man = self._get_el_manager()
        if man:
            man.deactivate()

        #     def activated(self):
        #         man = self._get_el_manager()
        #         if man:
        #             man.activate()

    def _add_canvas_pane(self, panes):
        app = self.window.application
        man = app.get_service('src.extraction_line.extraction_line_manager.ExtractionLineManager')
        if man:
            from src.extraction_line.tasks.extraction_line_pane import CanvasDockPane

            panes.append(CanvasDockPane(canvas=man.new_canvas(name='alt_config')))

        return panes

    @on_trait_change('window:opened')
    def _window_opened(self):
        man = self._get_el_manager()
        if man:
        #            do_later(man.activate)
            man.activate()

#            man.canvas.refresh()

class BaseHardwareTask(BaseManagerTask):
    pass

#     def _menu_bar_factory(self, menus=None):
#         extraction_menu = SMenu(id='Extraction', name='&Extraction')
#         measure_menu = SMenu(
# # #                              PeakCenterAction(),
#                             id='Measure', name='Measure',
#                             before='help.menu'
#                             )
#         ms = [extraction_menu, measure_menu]
#         if not menus:
#             menus = ms
#         else:
#             menus.extend(ms)
#         return super(BaseHardwareTask, self)._menu_bar_factory(menus=menus)
# class BaseManagerTask(BaseTask):
#    manager = Any

#============= EOF =============================================
