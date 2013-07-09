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
from traits.api import HasTraits
from traitsui.api import View, Item, VGroup, HGroup, EnumEditor, spring, \
    Label, Spring, ListEditor, Group, InstanceEditor, HSplit, UItem, ButtonEditor
from pyface.tasks.traits_task_pane import TraitsTaskPane
from pyface.tasks.traits_dock_pane import TraitsDockPane
#============= standard library imports ========================
#============= local library imports  ==========================

class ScanPane(TraitsTaskPane):
    def traits_view(self):
        v = View(UItem('graph', style='custom'))
        return v

class ReadoutPane(TraitsDockPane):
    id = 'pychron.spectrometer.readout'
    name = 'Readout'
    def traits_view(self):
        v = View(Group(UItem('readout_view', style='custom'), show_border=True))
        return v

class IntensitiesPane(TraitsDockPane):
    id = 'pychron.spectrometer.intensities'
    name = 'Intensities'
    def traits_view(self):
        intensity_grp = VGroup(
                   HGroup(spring, Label('Intensity'),
                          Spring(springy=False, width=90),
                          Label(u'1\u03c3'),
                          Spring(springy=False, width=87)),
                   Item('detectors',
                       show_label=False,
                       editor=ListEditor(style='custom', mutable=False,
                                         editor=InstanceEditor(view='intensity_view'))),
                   show_border=True
                   )
        v = View(intensity_grp)
        return v

class ControlsPane(TraitsDockPane):
    id = 'pychron.spectrometer.controls'
    name = 'Controls'
    def traits_view(self):
        def hitem(n, l, **kw):
            return HGroup(Label(l), spring, Item(n, show_label=False, **kw),
                          Spring(springy=False, width=275))

        magnet_grp = VGroup(
                            HGroup(
                                UItem('detector',
                                     editor=EnumEditor(name='detectors')),
                                UItem('isotope',
                                     editor=EnumEditor(name='isotopes')
                                     )),
                            UItem('magnet', style='custom'),
                            UItem('scanner', style='custom'),
                            label='Magnet'
                            )
        detector_grp = VGroup(
                              HGroup(
                                     spring,
                                     Label('Deflection'),
                                     Spring(springy=False, width=70),
                                     ),
                              Item('detectors',
                                   show_label=False,
                                   editor=ListEditor(style='custom', mutable=False, editor=InstanceEditor())),
                              label='Detectors'
                              )

        rise_grp = UItem('rise_rate', style='custom')
        source_grp = UItem('source', style='custom')

        graph_cntrl_grp = VGroup(
                                 Item('graph_scan_width', label='Scan Width (mins)'),
                                 Item('graph_scale', label='Scale'),
                                 Item('graph_y_auto', label='Autoscale Y'),
                                 Item('graph_ymax', label='Max', format_str='%0.3f'),
                                 Item('graph_ymin', label='Min', format_str='%0.3f'),
                                 HGroup(UItem('record_button', editor=ButtonEditor(label_value='record_label')),
                                        Item('add_marker_button',
                                             show_label=False,
                                             enabled_when='_recording')),
                                 label='Graph'
                                 )
        control_grp = Group(
                          graph_cntrl_grp,
                          detector_grp,
                          rise_grp,
                          magnet_grp,
                          source_grp,
                          layout='tabbed')

        v = View(
                 control_grp
#                  Group(
#                        magnet_grp,
#                        detector_grp,
#                        layout='tabbed'
                       )
#                  )
        return v
#
#        custom = lambda n:Item(n, style='custom', show_label=False)
#
#        magnet_grp = VGroup(
#                            HGroup(
#                                Item('detector',
#                                     show_label=False,
#                                     editor=EnumEditor(name='detectors')),
#                                Item('isotope',
#                                     show_label=False,
#                                     editor=EnumEditor(name='isotopes')
#                                     )),
#                            custom('magnet'),
#                            custom('scanner'),
#                            label='Magnet'
#                            )
#        detector_grp = VGroup(
#                              HGroup(
#                                     spring,
#                                     Label('Deflection'),
#                                     Spring(springy=False, width=70),
#                                     ),
#                              Item('detectors',
#                                   show_label=False,
#                                   editor=ListEditor(style='custom', mutable=False, editor=InstanceEditor())),
#                              label='Detectors'
#                              )
#
#        rise_grp = custom('rise_rate')
#        source_grp = custom('source')
#
#        right_spring = Spring(springy=False, width=275)
#        def hitem(n, l, **kw):
#            return HGroup(Label(l), spring, Item(n, show_label=False, **kw), right_spring)
#
#        graph_cntrl_grp = VGroup(
#                                 hitem('graph_scan_width', 'Scan Width (mins)'),
#                                 hitem('graph_scale', 'Scale'),
#                                 hitem('graph_y_auto', 'Autoscale Y'),
#                                 hitem('graph_ymax', 'Max', format_str='%0.3f'),
#                                 hitem('graph_ymin', 'Min', format_str='%0.3f'),
#                                 HGroup(self._button_factory('record_button', label='record_label'),
#                                        Item('add_marker_button',
#                                             show_label=False,
#                                             enabled_when='_recording')),
#                                 label='Graph'
#                                 )
#        control_grp = Group(
#                          graph_cntrl_grp,
#                          detector_grp,
#                          rise_grp,
#                          magnet_grp,
#                          source_grp,
#                          layout='tabbed')
#        intensity_grp = VGroup(
#                               HGroup(spring, Label('Intensity'),
#                                      Spring(springy=False, width=90),
#                                      Label(u'1\u03c3'),
#                                      Spring(springy=False, width=87)),
#                               Item('detectors',
#                                   show_label=False,
#                                   editor=ListEditor(style='custom', mutable=False,
#                                                     editor=InstanceEditor(view='intensity_view'))),
#                               label='Intensities',
#                               show_border=True
#                               )
#        display_grp = VGroup(
#                          Group(custom('readout_view'), show_border=True, label='Readout'),
#                          intensity_grp,
#                          )
#        graph_grp = custom('graph')
#        v = View(
#                    HSplit(
# #                           VGroup(control_grp, intensity_grp),
#                           VGroup(control_grp, display_grp),
#                           graph_grp,
#                           )
#                 )
#        return v
#============= EOF =============================================
