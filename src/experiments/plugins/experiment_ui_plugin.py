#============= enthought library imports =======================
from traits.api import on_trait_change
#============= standard library imports ========================

#============= local library imports  ==========================
from src.envisage.core.core_ui_plugin import CoreUIPlugin

class ExperimentUIPlugin(CoreUIPlugin):
    '''
        G{classtree}
    '''
    id = 'pychron.experiment.ui'
    name = 'Experiment UI'

    def _action_sets_default(self):
        '''
        '''
        from experiment_action_set import ExperimentActionSet
        return [ExperimentActionSet]

    def _views_default(self):
        '''
        '''
        return [self._create_analysis_graph_view]


    def _create_analysis_graph_view(self, **kw):
        '''
            @type **kw: C{str}
            @param **kw:
        '''
        app = self.application
        obj = app.get_service('src.experiments.analysis_graph_view.AnalysisGraphView')
        manager = app.get_service('src.experiments.experiments_manager.ExperimentsManager')
        manager.on_trait_change(obj.update, 'selected')

        args = dict(id = 'experiment.analysis.graph.view',
                         name = 'GraphView',
                         obj = obj
                         )

        return self.traitsuiview_factory(args, kw)

    @on_trait_change('application.gui:started')
    def _started(self, obj, name, old, new):
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
        if new  is True:
            app = self.application
            window = app.workbench.active_window
            manager = app.get_service('src.experiments.experiments_manager.ExperimentsManager')
            manager.window = window
            manager.open_default()
#============= views ===================================
#============= EOF ====================================
