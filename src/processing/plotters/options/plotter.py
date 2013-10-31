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
from kiva.fonttools import str_to_font
from traits.api import Str, Bool, Property, Enum
from traitsui.api import View, Item, HGroup, Label, spring, Spring, \
    VGroup, Group, EnumEditor, TableEditor

#============= standard library imports ========================
#============= local library imports  ==========================
from traitsui.extras.checkbox_column import CheckboxColumn
from traitsui.table_column import ObjectColumn
from src.processing.plotters.options.base import BasePlotterOptions

FONTS = ['modern', 'arial']
SIZES = [6, 8, 9, 10, 11, 12, 14, 16, 18, 24, 36]


def _table_column(klass, *args, **kw):
    kw['text_font'] = 'arial 10'
    return klass(*args, **kw)


def object_column(*args, **kw):
    return _table_column(ObjectColumn, *args, **kw)


def checkbox_column(*args, **kw):
    return _table_column(CheckboxColumn, *args, **kw)


class PlotterOptions(BasePlotterOptions):
    title = Str
    auto_generate_title = Bool
    #     data_type = Str('database')


    xtick_font = Property
    xtick_font_size = Enum(*SIZES)
    xtick_font_name = Enum(*FONTS)

    xtitle_font = Property
    xtitle_font_size = Enum(*SIZES)
    xtitle_font_name = Enum(*FONTS)

    ytick_font = Property
    ytick_font_size = Enum(*SIZES)
    ytick_font_name = Enum(*FONTS)

    ytitle_font = Property
    ytitle_font_size = Enum(*SIZES)
    ytitle_font_name = Enum(*FONTS)
    #     data_type_editable = Bool(True)


    #    def closed(self, isok):
    #        self._dump()

    #    def close(self, isok):
    #        if isok:
    #            self._dump()
    #        return True

    def construct_plots(self, plist):
        '''
            plist is a list of dictionaries
        '''
        ps = [self.plot_option_klass(**pi) for pi in plist]
        self.aux_plots = ps

    def add_aux_plot(self, **kw):
        ap = self.plot_option_klass(**kw)
        self.aux_plots.append(ap)

    def _create_axis_group(self, axis, name):

        hg = HGroup(
            Label(name.capitalize()),
            spring,
            Item('{}{}_font_name'.format(axis, name), show_label=False),
            Item('{}{}_font_size'.format(axis, name), show_label=False),
            Spring(width=125, springy=False)
        )
        return hg

    def _get_dump_attrs(self):
        attrs = ['title', 'auto_generate_title',
                 #                  'data_type',
                 'aux_plots',
                 'xtick_font_size',
                 'xtick_font_name',
                 'xtitle_font_size',
                 'xtitle_font_name',
                 'ytick_font_size',
                 'ytick_font_name',
                 'ytitle_font_size',
                 'ytitle_font_name',
        ]
        return attrs

    #===============================================================================
    # property get/set
    #===============================================================================
    def _get_xtick_font(self):
        return self._get_font('xtick', default_size=10)

    def _get_xtitle_font(self):
        return self._get_font('xtitle', default_size=12)

    def _get_ytick_font(self):
        return self._get_font('ytick', default_size=10)

    def _get_ytitle_font(self):
        return self._get_font('ytitle', default_size=12)

    def _get_font(self, name, default_size=10):
        xn = getattr(self, '{}_font_name'.format(name))
        xs = getattr(self, '{}_font_size'.format(name))
        if xn is None:
            xn = FONTS[0]
        if xs is None:
            xs = default_size
        return str_to_font('{} {}'.format(xn, xs))

    #===============================================================================
    # defaults
    #===============================================================================
    def _xtitle_font_size_default(self):
        return 12

    def _xtick_font_size_default(self):
        return 10

    def _ytitle_font_size_default(self):
        return 12

    def _ytick_font_size_default(self):
        return 10

    def _aux_plots_default(self):
        return [self.plot_option_klass() for _ in range(5)]

    #===============================================================================
    # views
    #===============================================================================
    def _get_groups(self):
        pass

    def _get_x_axis_group(self):
        v = VGroup(
            self._create_axis_group('x', 'title'),
            self._create_axis_group('x', 'tick'),
            #                    show_border=True,
            label='X')
        return v

    def _get_main_group(self):
        main_grp = Group(
            VGroup(
                HGroup(Item('auto_generate_title', tooltip='Auto generate a title based on the analysis list'),
                       Item('title', springy=True, enabled_when='not auto_generate_title',
                            tooltip='User specified plot title')),
            ),
            self._get_aux_plots_group(),
            label='Plot')

        return main_grp

    def _get_aux_plots_group(self):
        cols = [checkbox_column(name='use', ),
                object_column(name='name',
                              width=130,
                              editor=EnumEditor(name='plot_names')),
                object_column(name='scale'),
                object_column(name='height',
                              format_func=lambda x: str(x) if x else ''),
                checkbox_column(name='show_labels', label='Labels'),
                checkbox_column(name='x_error', label='X Error'),
                checkbox_column(name='y_error', label='Y Error')]

        aux_plots_grp = Item('aux_plots',
                             style='custom',
                             show_label=False,
                             editor=TableEditor(columns=cols,
                                                sortable=False,
                                                deletable=False,
                                                reorderable=False,
                             ))
        return aux_plots_grp

    def traits_view(self):
        axis_grp = VGroup(
            self._get_x_axis_group(),
            VGroup(
                self._create_axis_group('y', 'title'),
                self._create_axis_group('y', 'tick'),
                label='Y'),
            label='Axes')

        main_grp = self._get_main_group()

        g = Group(main_grp,
                  axis_grp,
                  layout='tabbed')
        grps = self._get_groups()
        if grps:
            g.content.extend(grps)

        v = View(g)
        return v

#============= EOF =============================================
