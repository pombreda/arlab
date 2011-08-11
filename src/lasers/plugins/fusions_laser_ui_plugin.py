#============= enthought library imports =======================

#============= standard library imports ========================

#============= local library imports  ==========================
from src.envisage.core.core_ui_plugin import CoreUIPlugin

class FusionsLaserUIPlugin(CoreUIPlugin):

    def _perspectives_default(self):
        from fusions_laser_perspective import FusionsLaserPerspective
        return [FusionsLaserPerspective]

#    def _preferences_pages_default(self):
#        from fusions_laser_preferences_page import FusionsLaserPreferencesPage
#        return [FusionsLaserPreferencesPage]

    def _action_sets_default(self):
        from fusions_laser_action_set import FusionsLaserActionSet
        return [FusionsLaserActionSet]

#============= views ==================================
    def _views_default(self):
        service = self.application.get_service(self._protocol)
        views = []
        if service:
            pass
            #views.append(self.create_control_view)
            #views.append(self.create_stage_view)
            #views.append(self.create_power_map_view)


        return views

#    def create_power_map_view(self, **kw):
#        obj = PowerMapViewer(application = self.application)
#        root = os.path.join(paths.data_dir, 'powermap')
#        obj.set_data_files(root)
#        id = 'power_map'
#        args = dict(id = 'fusions.%s' % id,
#                  category = 'data',
#                  name = id,
#                  obj = obj
#                  )
#        return self.traitsuiview_factory(args, kw)

#    def create_stage_view(self, **kw):
#        obj = self.application.get_service(self._protocol)
#
#        obj = obj.stage_manager
#
#        bind_preference(obj, 'window_width', 'pychron.fusions.laser.window_width')
#        bind_preference(obj, 'window_height', 'pychron.fusions.laser.window_height')
#
#        #only applicable if using video
#        bind_preference(obj, 'video_scaling', 'pychron.fusions.laser.video_scaling')
#
#        id = 'stage'
#        args = dict(id = 'fusions.%s' % id,
#                  category = 'extraction devices',
#                  name = id,
#                  obj = obj
#                  )
#        return self.traitsuiview_factory(args, kw)
#
#    def create_control_view(self, **kw):
#        obj = self.application.get_service(self._protocol)
#        id = 'laser_control'
#        args = dict(id = 'fusions.%s' % id,
#                  category = 'extraction devices',
#                  name = id,
#                  obj = obj
#                  )
#        return self.traitsuiview_factory(args, kw)

#============= EOF ====================================
