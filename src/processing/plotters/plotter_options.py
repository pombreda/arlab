#===============================================================================
# Copyright 2012 Jake Ross
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
from traits.api import HasTraits, List, Property, Str, Enum, Int, Float, Bool
from traitsui.api import View, Item, HGroup, Label, Group, \
    EnumEditor, Spring, spring, VGroup, UItem
import apptools.sweet_pickle as pickle
#============= standard library imports ========================
import os
#============= local library imports  ==========================
from src.pychron_constants import NULL_STR, FIT_TYPES
from traitsui.table_column import ObjectColumn
from traitsui.editors.table_editor import TableEditor
from traitsui.extras.checkbox_column import CheckboxColumn
from kiva.fonttools.font import str_to_font
from traits.trait_errors import TraitError


def _table_column(klass, *args, **kw):
    kw['text_font'] = 'arial 10'
    return klass(*args, **kw)


def object_column(*args, **kw):
    return _table_column(ObjectColumn, *args, **kw)


def checkbox_column(*args, **kw):
    return _table_column(CheckboxColumn, *args, **kw)


class PlotterOption(HasTraits):
    use = Bool
    name = Str(NULL_STR)
    plot_names = Property

    scale = Enum('linear', 'log')
    height = Int(100, enter_set=True, auto_set=False)
    x_error = Bool(False)
    y_error = Bool(False)
    show_labels = Bool(False)

    def _name_changed(self):
        if self.name != NULL_STR:
            self.use = True

    def _get_plot_names(self):
        return {NULL_STR: NULL_STR,
                'analysis_number_stacked': 'Analysis Number Stacked',
                'analysis_number': 'Analysis Number',
                'radiogenic_yield': 'Radiogenic 40Ar',
                'kca': 'K/Ca',
                'kcl': 'K/Cl',
                'moles_K39': 'K39 Moles',
                'relative_probability': 'Ideogram'}


class FitPlotterOption(PlotterOption):
    fit = Enum(['', ] + FIT_TYPES)


class SpectrumPlotOption(PlotterOption):
    def _get_plot_names(self):
        return {NULL_STR: NULL_STR,
                'radiogenic_yield': 'Radiogenic 40Ar',
                'kca': 'K/Ca',
                'kcl': 'K/Cl',
                'moles_K39': 'K39 Moles',
                'age_spectrum': 'Age'}


class InverseIsochronPlotOption(PlotterOption):
    def _get_plot_names(self):
        return {NULL_STR: NULL_STR,
                #'radiogenic_yield': 'Radiogenic 40Ar',
                #'kca': 'K/Ca',
                #'kcl': 'K/Cl',
                #'moles_K39': 'K39 Moles',
                'inverse_isochron': 'Inv. Isochron'}


FONTS = ['modern', 'arial']
SIZES = [6, 8, 9, 10, 11, 12, 14, 16, 18, 24, 36]


class BasePlotterOptions(HasTraits):
    aux_plots = List
    name = Str
    plot_option_klass = PlotterOption
    plot_option_name = None

    def __init__(self, root, clean=False, *args, **kw):
        super(BasePlotterOptions, self).__init__(*args, **kw)
        if not clean:
            self._load(root)

    def get_aux_plots(self):
        return reversed([pi
                         for pi in self.aux_plots
                         if pi.name != NULL_STR and pi.use])

    def traits_view(self):
        v = View()
        return v

    # ==============================================================================
    # persistence
    #===============================================================================
    def _get_dump_attrs(self):
        return tuple()

    def dump(self, root):
        self._dump(root)

    def _make_dir(self, root):
        if os.path.isdir(root):
            return
        else:
            self._make_dir(os.path.dirname(root))
            os.mkdir(root)

    def _dump(self, root):
        if not self.name:
            return
        p = os.path.join(root, self.name)
        #         print root, self.name
        self._make_dir(root)

        with open(p, 'w') as fp:
            d = dict()
            attrs = self._get_dump_attrs()
            for t in attrs:
                d[t] = getattr(self, t)
            try:
                pickle.dump(d, fp)
            except (pickle.PickleError, TypeError, EOFError, TraitError):
                pass


    def _load(self, root):
        p = os.path.join(root, self.name)
        if os.path.isfile(p):
            with open(p, 'r') as fp:
                try:
                    obj = pickle.load(fp)
                    self.trait_set(**obj)
                except (pickle.PickleError, TypeError, EOFError, TraitError):
                    pass

        klass = self.plot_option_klass
        name = self.plot_option_name
        if name:
            pp = next((p for p in self.aux_plots if p.name == name), None)
            if not pp:
                po = klass(name=name, height=0)
                self.aux_plots.append(po)

    def __repr__(self):
        return self.name


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


class AgeOptions(PlotterOptions):
    include_j_error = Bool(True)
    include_irradiation_error = Bool(True)
    include_decay_error = Bool(False)
    nsigma = Enum(1, 2, 3)
    show_info = Bool(True)

    def _get_dump_attrs(self):
        attrs = super(AgeOptions, self)._get_dump_attrs()
        attrs += ['include_j_error',
                  'include_irradiation_error',
                  'include_decay_error',
                  'nsigma',
                  'show_info'
        ]
        return attrs


class IdeogramOptions(AgeOptions):
    probability_curve_kind = Enum('cumulative', 'kernel')
    mean_calculation_kind = Enum('weighted mean', 'kernel')
    error_calc_method = Enum('SEM, but if MSWD>1 use SEM * sqrt(MSWD)', 'SEM')
    xlow = Float
    xhigh = Float
    use_centered_range = Bool
    centered_range = Float(0.5)
    display_mean_indicator = Bool(True)
    display_mean = Bool(True)
    plot_option_name = 'relative_probability'

    def _get_x_axis_group(self):
        vg = super(IdeogramOptions, self)._get_x_axis_group()

        limits_grp = HGroup(Item('xlow', label='Min.'),
                            Item('xhigh', label='Max.'),
                            enabled_when='not object.use_centered_range')
        centered_grp = HGroup(Item('use_centered_range', label='Center'),
                              Item('centered_range', show_label=False,
                                   enabled_when='object.use_centered_range'))
        vg.content.append(limits_grp)
        vg.content.append(centered_grp)

        return vg

    def _get_groups(self):
        g = Group(
            Item('show_info', label='Display Info.'),
            Item('_'),
            Item('probability_curve_kind',
                 width=-150,
                 label='Probability Curve Method'),
            Item('mean_calculation_kind',
                 width=-150,
                 label='Mean Calculation Method'),
            Item('error_calc_method',
                 width=-150,
                 label='Error Calculation Method'),
            Item('nsigma', label='Age Error NSigma'),
            Item('include_j_error'),
            Item('include_irradiation_error'),
            Item('include_decay_error'),

            label='Calculations'
        )
        return (g,)

    def _get_dump_attrs(self):
        attrs = super(IdeogramOptions, self)._get_dump_attrs()
        return attrs + [
            'probability_curve_kind',
            'mean_calculation_kind',
            'error_calc_method',
            'xlow', 'xhigh',
            'use_centered_range', 'centered_range'
        ]


import re

plat_regex = re.compile(r'\w{1,2}-{1}\w{1,2}$')


class SpectrumOptions(AgeOptions):
    step_nsigma = Int(2)
    plot_option_klass = SpectrumPlotOption

    force_plateau = Bool(False)
    plateau_steps = Property(Str)
    _plateau_steps = Str
    plot_option_name = 'age_spectrum'

    def _get_plateau_steps(self):
        return self._plateau_steps

    def _set_plateau_steps(self, v):
        self._plateau_steps = v

    def _validate_plateau_steps(self, v):
        if plat_regex.match(v):
            s, e = v.split('-')
            try:
                assert s < e
                return v
            except AssertionError:
                pass

    def _get_dump_attrs(self):
        attrs = super(SpectrumOptions, self)._get_dump_attrs()
        return attrs + ['step_nsigma',
                        'force_plateau',
                        '_plateau_steps']

    def _get_groups(self):

        plat_grp = Group(
            HGroup(
                Item('force_plateau',
                     tooltip='Force a plateau over provided steps'
                ),
                UItem('plateau_steps',
                      enabled_when='force_plateau',
                      tooltip='Enter start and end steps. e.g A-C '
                ),
            ),
            label='Plateau'
        )

        g = Group(
            plat_grp,
            label='Calculations'
        )
        return (g, )


class InverseIsochronOptions(AgeOptions):
    plot_option_name = 'inverse_isochron'
    plot_option_klass = InverseIsochronPlotOption


class SeriesOptions(BasePlotterOptions):
    def load_aux_plots(self, ref):
        def f(kii):
            ff = FitPlotterOption(name=kii)
            ff.trait_set(use=False, fit='')
            return ff

        keys = ref.isotope_keys
        keys.extend(['{}bs'.format(ki) for ki in keys])
        if 'Ar40' in keys:
            if 'Ar39' in keys:
                keys.append('Ar40/Ar39')
            if 'Ar36' in keys:
                keys.append('Ar40/Ar36')

            keys.append('PC')
            ap = [f(k) for k in keys]
            self.trait_set(
                aux_plots=ap,
            )

    def traits_view(self):
        cols = [
            CheckboxColumn(name='use'),
            ObjectColumn(name='name'),
            ObjectColumn(name='fit', width=135),
            ObjectColumn(name='scale', label='Y Scale'),
            #               ObjectColumn(name='height'),
            #               CheckboxColumn(name='x_error', label='X Error'),
            CheckboxColumn(name='y_error', label='Y Error'),
        ]
        aux_plots_grp = Item('aux_plots',
                             style='custom',
                             show_label=False,

                             editor=TableEditor(columns=cols,
                                                sortable=False,
                                                deletable=False,
                                                reorderable=False
                             ))
        v = View(aux_plots_grp)
        return v


if __name__ == '__main__':
    ip = IdeogramOptions()
    ip.configure_traits()
#============= EOF =============================================
