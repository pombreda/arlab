#============= enthought library imports =======================
from traits.api import HasTraits, List, Instance, Any, on_trait_change, String, Event, Property, Bool
from traitsui.api import View, Item, HGroup, spring, ButtonEditor
from src.managers.displays.rich_text_display import RichTextDisplay
from src.scripts.core.scripts_manager import ScriptSelector

#============= standard library imports ========================

#============= local library imports  ==========================

#============= views ===================================

class ProcessView(HasTraits):
    '''
        G{classtree}
    '''
    name = String
    execute = Event
    execute_label = Property(depends_on = 'alive')

    #experiment = Any
    #script = Any
    selected = Any
    dirty = Bool(True)
    alive = Bool(False)

    display = Instance(RichTextDisplay)
    selector = Instance(ScriptSelector)
    script_manager = Any

    scripts = List

    @on_trait_change('selector:selected')
    def selector_update(self, obj, name, old, new):
        self.script_manager.script_klass = new[0]
        self.script_manager.script_package = new[1]
        self.script_manager.manager_protocol = new[2]

    def _selector_default(self):
        return ScriptSelector()

    def _display_default(self):
        return RichTextDisplay(height = 300)

    def _get_execute_label(self):

        return 'STOP' if self.alive else 'EXECUTE'

    def _execute_fired(self):
        '''
        '''

        if self.selected:
            obj = self.selected
            if self.alive:
                obj.kill()
                self.alive = False
            else:
                obj.execute()

    def _selected_changed(self, old, new):
        if new:
            new._script.on_trait_change(self.update_alive, '_alive')
            new._script.on_trait_change(self.update_display, '_display_msg')

    def update_display(self, obj, name, old, new):
        self.display.add_text(new)

    def update_alive(self, obj, name, old, new):
        '''
           handle the script death ie not alive
            
        '''
        self.alive = new

    def update_dirty(self, obj, name, old, new):
        print 'ud', obj, name, old, new
        self.dirty = new

    def selected_update(self, obj, name, old, new):
        if name == 'selected':
            self.selected = new
            if new is not None:
                self.name = new.name
#                self.dirty = False
                new.on_trait_change(self.update_dirty, 'dirty')

    @on_trait_change('selected:name')
    def name_change(self, obj, name, old, new):
        '''
            @type obj: C{str}
            @param obj:

            @type name: C{str}
            @param name:

            @type old: C{str}
            @param old:

            @type new: C{str}
            @param new:
        '''
        #print obj, name, old, new
        if new is not None:
            self.name = new

    def traits_view(self):
        '''
        '''
        return View(
                    HGroup(Item('name'), spring),
                    HGroup(
                           Item('execute',
                                editor = ButtonEditor(label_value = 'execute_label'),
                                       #enabled_when = 'experiment or script',
                                       enabled_when = 'not dirty',
                                       show_label = False)
                            ),
                            #spring
                    #Item('selector', show_label = False, style = 'custom'),
                    Item('display', show_label = False, style = 'custom')
                    )

#============= EOF ====================================
