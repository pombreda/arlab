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
from traits.api import String, Str, Property, Any, Float, Instance, Int, List, cached_property, on_trait_change, Bool, Button, \
    Event, Enum
# from traitsui.api import View, Item, EnumEditor, HGroup, VGroup, Group, Spring, spring, \
#    UItem, ButtonEditor, Label
#============= standard library imports ========================
import os
#============= local library imports  ==========================
from src.pychron_constants import NULL_STR, SCRIPT_KEYS, SCRIPT_NAMES, LINE_STR
from src.experiment.automated_run.factory_view import FactoryView
from src.experiment.utilities.identifier import convert_special_name, ANALYSIS_MAPPING, NON_EXTRACTABLE, \
    make_special_identifier, make_standard_identifier
from src.experiment.automated_run.spec import AutomatedRunSpec
from src.regex import TRANSECT_REGEX, POSITION_REGEX, SLICE_REGEX, PSLICE_REGEX, \
    SSLICE_REGEX
# from src.experiment.utilities.script_mixin import ScriptMixin
from src.paths import paths
from src.experiment.script.script import Script
from src.experiment.queue.increment_heat_template import IncrementalHeatTemplate
from src.loggable import Loggable
import yaml
from src.experiment.utilities.human_error_checker import HumanErrorChecker
from src.helpers.filetools import list_directory, add_extension
from src.lasers.pattern.pattern_maker_view import PatternMakerView
from src.ui.gui import invoke_in_main_thread


class UpdateSelectedCTX(object):
    _factory = None

    def __init__(self, factory):
        self._factory = factory

    def __enter__(self):
        self._factory.set_labnumber = False

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._factory.set_labnumber = True


def EKlass(klass):
    return klass(enter_set=True, auto_set=False)


def increment_value(self, m, increment=1):
    s = ','
    if s not in m:
        m = (m,)
        s = ''
    else:
        m = m.split(s)
    ms = []
    for mi in m:
        try:
            ms.append(str(int(mi) + increment))
        except ValueError:
            return s.join(m)

    return s.join(ms)


class AutomatedRunFactory(Loggable):
    db = Any

    extraction_script = Instance(Script)
    measurement_script = Instance(Script)
    post_measurement_script = Instance(Script)
    post_equilibration_script = Instance(Script)
    load_defaults_button = Button('Defaults')

    human_error_checker = Instance(HumanErrorChecker, ())
    factory_view = Instance(FactoryView)
    factory_view_klass = FactoryView

    set_labnumber = True

    labnumber = String(enter_set=True, auto_set=False)
    update_labnumber = Event

    aliquot = EKlass(Int)
    special_labnumber = Str('Special Labnumber')

    _labnumber = String
    labnumbers = Property(depends_on='project, selected_level')

    project = Any
    projects = Property(depends_on='db')

    selected_irradiation = Str('Irradiation')
    irradiations = Property(depends_on='db')
    selected_level = Str('Level')
    levels = Property(depends_on='selected_irradiation, db')

    flux = Property(Float, depends_on='labnumber')
    flux_error = Property(Float, depends_on='labnumber')

    _flux = None
    _flux_error = None
    save_flux_button = Button

    skip = Bool(False)
    end_after = Property(Bool, depends_on='_end_after')
    _end_after = Bool(False)

    weight = Float
    comment = Str
    auto_fill_comment = Bool

    position = Property(depends_on='_position')
    _position = Str

    #===========================================================================
    # extract
    #===========================================================================
    extract_value = Property(
        EKlass(Float),
        depends_on='_extract_value')
    _extract_value = Float
    extract_units = Str(NULL_STR)
    extract_units_names = List(['', 'watts', 'temp', 'percent'])
    _default_extract_units = 'watts'

    extract_group = Int(enter_set=True, auto_set=False)
    extract_group_button = Button('Group Selected')

    ramp_duration = EKlass(Float)

    duration = EKlass(Float)
    cleanup = EKlass(Float)
    beam_diameter = Property(EKlass(Str), depends_on='beam_diameter')
    _beam_diameter = Any

    pattern = String('Pattern')
    patterns = List
    remote_patterns = List

    edit_pattern = Event
    edit_pattern_label = Property(depends_on='pattern')
    #===========================================================================
    # templates
    #===========================================================================
    template = String('Step Heat Template')
    templates = List

    edit_template = Event
    edit_template_label = Property(depends_on='template')

    #===========================================================================
    # truncation
    #===========================================================================
    trunc_attr = Enum('age', 'kca', 'kcl')
    trunc_comp = Enum('>', '<', '>=', '<=', '=')
    trunc_crit = Float(enter_set=True, auto_set=False)
    trunc_start = Int(100, enter_set=True, auto_set=False)

    truncation_str = Property(depends_on='trunc_+')
    truncation_path = Str
    truncations = List

    #===========================================================================
    # frequency
    #===========================================================================
    frequency = Int

    #===========================================================================
    # readonly
    #===========================================================================
    sample = Str
    irradiation = Str
    irrad_level = Str
    irrad_hole = Str

    info_label = Property(depends_on='labnumber')
    #===========================================================================
    # private
    #===========================================================================
    _selected_runs = List
    _spec_klass = AutomatedRunSpec
    _extract_group_cnt = 1

    extractable = Property(depends_on='labnumber')
    update_info_needed = Event
    refresh_table_needed = Event
    changed = Event
    suppress_update = False

    edit_mode = Bool(False)
    edit_mode_label = Property(depends_on='edit_mode')
    edit_enabled = Bool(False)

    mass_spectrometer = String
    extract_device = Str

    def update_selected_ctx(self):
        return UpdateSelectedCTX(self)

    def check_run_addition(self, runs, load_name):
        '''
            check if its ok to add runs to the queue.
            ie. do they have any missing values.
                does the labnumber match the loading
            
            return True if ok to add runs else False
        '''
        hec = self.human_error_checker
        ret = hec.check_runs(runs, test_all=True)
        if ret:
            hec.report_errors(ret)
            return False

        return True

    def load_templates(self):
        self.templates = self._get_templates()

    def load_patterns(self):
        self.patterns = self._get_patterns()

    def load_truncations(self):
        self.truncations = self._get_truncations()

    def use_frequency(self):
        return self.labnumber in ANALYSIS_MAPPING and self.frequency

    def load_from_run(self, run):
        self._clone_run(run)

    def set_selected_runs(self, runs):
        self.debug('len selected runs {}'.format(len(runs)))
        if runs:
            run = runs[0]
            self._clone_run(run, set_labnumber=self.set_labnumber)

        self._selected_runs = runs
        self.suppress_update = False

        if not runs:
            self.edit_mode = False
            self.edit_enabled = False
        elif len(runs) == 1:
            self.edit_enabled = True
        else:
            self.edit_enabled = False
            self.edit_mode = True

        if run and self.edit_mode:
            self._end_after = run.end_after

    def set_mass_spectrometer(self, new):
        new = new.lower()
        self.mass_spectrometer = new
        for s in SCRIPT_NAMES:
            sc = getattr(self, s)
            sc.mass_spectrometer = new

    def set_extract_device(self, new):
        new = new.lower()
        self.extract_device = new
        for s in SCRIPT_KEYS:
            s = getattr(self, '{}_script'.format(s))
            s.extract_device = new

    def new_runs(self, positions=None, auto_increment_position=False,
                 auto_increment_id=False,
                 extract_group_cnt=0):
        """
            returns a list of runs even if its only one run
            also returns self.frequency if using special labnumber else None
        """

        arvs, freq = self._new_runs(positions=positions,
                                    extract_group_cnt=extract_group_cnt)

        if auto_increment_id:
            self._labnumber = increment_value(self.labnumber)

        if auto_increment_position:
            pos = self.position
            if pos:
                if ',' in pos:
                    spos = map(int, pos.split(','))
                    increment = spos[-1] - spos[0] + 1
                    self.position = increment_value(pos, increment)
                else:
                    s = None
                    if SLICE_REGEX.match(pos):
                        s, e = map(int, pos.split('-'))
                    elif SSLICE_REGEX.match(pos) or PSLICE_REGEX.match(pos):
                        s, e = map(int, pos.split(':'))[:2]

                    if s is not None:
                        d = e - s
                        ns = e + 1
                        ne = ns + d
                        self.position = '{}-{}'.format(ns, ne)

        return arvs, freq

        #===============================================================================
        # private
        #===============================================================================

    def _new_runs(self, positions, extract_group_cnt=0):
        _ln, special = self._make_short_labnumber()
        freq = self.frequency if special else None

        arvs = None
        if not special:
            if not positions:
                positions = self.position

            template = self._use_template() and not freq
            arvs = self._new_runs_by_position(positions, template, extract_group_cnt)

        if not arvs:
            arvs = [self._new_run()]

        return arvs, freq

    def _new_runs_by_position(self, pos, template=False, extract_group_cnt=0):
        arvs = []
        s = None
        e = None
        inc = 1
        #(SLICE_REGEX, SSLICE_REGEX, PSLICE_REGEX,
        #          TRANSECT_REGEX, POSITION_REGEX)
        if SLICE_REGEX.match(pos):
            s, e = map(int, pos.split('-'))
        elif SSLICE_REGEX.match(pos):
            s, e, inc = map(int, pos.split(':'))
        elif PSLICE_REGEX.match(pos):
            s, e = map(int, pos.split(':'))[:2]
        else:
            try:
                s = int(self.position)
                e = s
            except ValueError:
                pass

        if e < s:
            self.warning_dialog('Endposition {} must greater than start position {}'.format(e, s))
            return

        set_pos = True
        if s is not None and e is not None:
            positions = range(s, e + 1, inc)
        else:
            if TRANSECT_REGEX.match(pos):
                positions = [pos]
            else:
                set_pos = False
                positions = [0]

        p = ''
        for i in positions:
            if set_pos:
                p = str(i)
            if template:
                arvs.extend(self._render_template(p, extract_group_cnt))
                extract_group_cnt += 1
            else:
                arvs.append(self._new_run(position=str(p),
                                          excludes=['position']))
        return arvs

    def _make_irrad_level(self, ln):
        il = ''
        ipos = ln.irradiation_position
        if ipos is not None:
            level = ipos.level
            irrad = level.irradiation
            hole = ipos.position

            self.irrad_hole = str(hole)
            self.irrad_level = str(level.name)

            il = '{} {}:{}'.format(irrad.name, level.name, hole)
        return il

    def _new_run(self, excludes=None, **kw):

        # need to set the labnumber now because analysis_type depends on it
        arv = self._spec_klass(labnumber=self.labnumber, **kw)

        if excludes is None:
            excludes = []

        if arv.analysis_type in ('blank_unknown', 'pause'):
            excludes.extend(('extract_value', 'extract_units', 'pattern', 'beam_diameter'))
            if arv.analysis_type == 'pause':
                excludes.extend(('cleanup', 'position'))
        elif arv.analysis_type not in ('unknown', 'degas'):
            excludes.extend(('position', 'extract_value', 'extract_units', 'pattern',
                             'cleanup', 'duration', 'beam_diameter'
            ))

        self._set_run_values(arv, excludes=excludes)
        return arv

    def _get_run_attr(self):
        return ['position',
                'extract_value', 'extract_units', 'cleanup', 'duration',
                'pattern', 'beam_diameter',
                'weight', 'comment',
                'sample', 'irradiation',
                'skip', 'mass_spectrometer', 'extract_device']

    def _set_run_values(self, arv, excludes=None):
        if excludes is None:
            excludes = []

        '''
            if run is not an unknown and not a degas then don't copy evalue, eunits and pattern
            if runs is an unknown but is part of an extract group dont copy the evalue
        '''
        for attr in self._get_run_attr():
        #for attr in (
        #'position',
        #'extract_value', 'extract_units', 'cleanup', 'duration',
        #'pattern', 'beam_diameter',
        #'weight', 'comment',
        #'sample', 'irradiation',
        #'skip', 'mass_spectrometer', 'extract_device'
        #):
            if attr in excludes:
                continue
            v = getattr(self, attr)
            if attr == 'pattern':
                if not self._use_pattern():
                    v = ''

            setattr(arv, attr, v)
            setattr(arv, '_prev_{}'.format(attr), v)

        if self.aliquot:
            self.debug('setting user defined aliquot')
            arv.user_defined_aliquot = int(self.aliquot)

        for si in SCRIPT_KEYS:
            name = '{}_script'.format(si)
            if name in excludes or si in excludes:
                continue

            s = getattr(self, name)
            setattr(arv, name, s.name)

    def _clone_run(self, run, excludes=None, set_labnumber=True):

        if excludes is None:
            excludes = []

        if not set_labnumber:
            excludes.append('labnumber')

        for attr in ('labnumber',
                     'extract_value', 'extract_units', 'cleanup', 'duration',
                     'extract_group',
                     'pattern', 'beam_diameter',
                     'position',
                     'weight', 'comment',
        ):
            if attr in excludes:
                continue

            setattr(self, attr, getattr(run, attr))

        if run.user_defined_aliquot:
            self.aliquot = int(run.aliquot)

        for si in SCRIPT_KEYS:
            name = '{}_script'.format(si)
            s = getattr(run, name)
            if name in excludes or si in excludes:
                continue

            setattr(self, name, Script(name=s,
                                       label=si,
                                       application=self.application,
                                       mass_spectrometer=self.mass_spectrometer))

    def _new_pattern(self):
        pm = PatternMakerView()

        if self._use_pattern():
            if pm.load_pattern(self.pattern):
                return pm
        else:
            return pm

    def _new_template(self):
        template = IncrementalHeatTemplate()
        if self._use_template():
            t = self.template
            if not t.endswith('.txt'):
                t = '{}.txt'.format(t)
            t = os.path.join(paths.incremental_heat_template_dir, t)
            template.load(t)

        return template

    def _render_template(self, position, cnt):
        arvs = []
        template = self._new_template()
        self.debug('rendering template {}'.format(template.name))

        for st in template.steps:
            if st.value or st.duration or st.cleanup:
                arv = self._new_run(extract_group=cnt + 1,
                                    step=st.step_id,
                                    position=position,
                                    excludes=['position'])
                arv.trait_set(**st.make_dict(self.duration, self.cleanup))
                arvs.append(arv)

        return arvs

    def _make_short_labnumber(self, labnumber=None):
        if labnumber is None:
            labnumber = self.labnumber
        if '-' in labnumber:
            labnumber = labnumber.split('-')[0]

        special = labnumber in ANALYSIS_MAPPING
        return labnumber, special

    def _load_extraction_info(self, script=None):
        if script is None:
            script = self.extraction_script

        if '##' in self.labnumber:
            mod = script.get_parameter('modifier')
            if mod is not None:
                if isinstance(mod, int):
                    mod = '{:02n}'.format(mod)

                self.labnumber = self.labnumber.replace('##', str(mod))

    def _clear_labnumber(self):
        self.labnumber = ''
        self._labnumber = NULL_STR

    def _template_closed(self):
        invoke_in_main_thread(self.load_templates)

    def _pattern_closed(self):
        invoke_in_main_thread(self.load_patterns)

    def _use_pattern(self):
        return self.pattern and not self.pattern in (LINE_STR, 'None', '',
                                                     'Pattern',
                                                     'Local Patterns',
                                                     'Remote Patterns')

    def _use_template(self):
        return self.template and not self.template in ('Step Heat Template',
                                                       LINE_STR, 'None')

    def _update_run_values(self, attr, v):
        if self.edit_mode and \
                self._selected_runs and \
                not self.suppress_update:
            for si in self._selected_runs:
                setattr(si, attr, v)

            if attr == 'extract_group':
                self.update_info_needed = True

            self.changed = True
            self.refresh_table_needed = True

    def _save_flux(self):
        if self._flux is None and self._flux_error is None:
            return

        if self._flux is None:
            self._flux = self.flux
        if self._flux_error is None:
            self._flux_error = self.flux_error

        if self._flux != self.flux or \
                        self._flux_error != self.flux_error:

            v, e = self._flux, self._flux_error
            db = self.db
            with db.session_ctx():
                dbln = db.get_labnumber(self.labnumber)
                if dbln:
                    dbpos = dbln.irradiation_position
                    dbhist = db.add_flux_history(dbpos)
                    dbflux = db.add_flux(float(v), float(e))
                    dbflux.history = dbhist
                    dbln.selected_flux_history = dbhist
                    self.information_dialog(u'Flux for {} {} \u00b1{} saved to database'.format(self.labnumber, v, e))

                    #===============================================================================
                    #
                    #===============================================================================

    def _load_extraction_defaults(self, ln):
        defaults = self._load_default_file()
        if defaults:
            if ln in defaults:
                grp = defaults[ln]
                for attr in ('extract_value', 'extract_units'):
                    v = grp.get(attr)
                    if v is not None:
                        setattr(self, attr, v)

    def _load_scripts(self, old, new):
    #        if not self.edit_mode:
    #            return

        """
            load default scripts if
                1. labnumber is special
                2. labnumber was a special and now unknown

            dont load if was unknown and now unknown
            this preserves the users changes
        """
        # if new is special e.g bu-01-01
        if '-' in new:
            new = new.split('-')[0]
        if '-' in old:
            old = old.split('-')[0]

        if new in ANALYSIS_MAPPING or \
                        old in ANALYSIS_MAPPING or not old and new:
            # set default scripts
            self._load_default_scripts(new)

    def _load_default_scripts(self, labnumber):

        self.debug('load default scripts for {}'.format(labnumber))
        # if labnumber is int use key='U'
        try:
            _ = int(labnumber)
            labnumber = 'u'
        except ValueError:
            pass

        labnumber = str(labnumber).lower()

        defaults = self._load_default_file()
        if defaults:
            if labnumber in defaults:
                default_scripts = defaults[labnumber]
                keys = SCRIPT_KEYS
                if labnumber == 'dg':
                    keys = ['extraction']

                for skey in keys:
                    new_script_name = default_scripts.get(skey) or ''

                    new_script_name = self._remove_file_extension(new_script_name)
                    if labnumber in ('u', 'bu') and self.extract_device != NULL_STR:

                        # the default value trumps pychron's
                        if self.extract_device:
                            e = self.extract_device.split(' ')[1].lower()
                            if skey == 'extraction':
                                new_script_name = e
                            elif skey == 'post_equilibration':
                                new_script_name = default_scripts.get(skey, 'pump_{}'.format(e))

                    elif labnumber == 'dg':
                        e = self.extract_device.split(' ')[1].lower()
                        new_script_name = '{}_{}'.format(e, new_script_name)

                    script = getattr(self, '{}_script'.format(skey))
                    script.name = new_script_name

    def _load_default_file(self):
        # open the yaml config file
        p = os.path.join(paths.scripts_dir, 'defaults.yaml')
        if not os.path.isfile(p):
            self.warning('Script defaults file does not exist {}'.format(p))
            return

        with open(p, 'r') as fp:
            defaults = yaml.load(fp)

        # convert keys to lowercase
        defaults = dict([(k.lower(), v) for k, v in defaults.iteritems()])
        return defaults

    #===============================================================================
    # property get/set
    #===============================================================================
    def _get_edit_mode_label(self):
        return 'Editing' if self.edit_mode else ''

    def _get_extractable(self):
        ln = self.labnumber
        if '-' in ln:
            ln = ln.split('-')[0]

        return not ln in NON_EXTRACTABLE

    @cached_property
    def _get_irradiations(self):
        irradiations = []
        if self.db:
            irradiations = [pi.name for pi in self.db.get_irradiations()]

        return ['Irradiation', LINE_STR] + irradiations

    @cached_property
    def _get_levels(self):
        levels = []
        if self.db:
            with self.db.session_ctx():
                if not self.selected_irradiation in ('IRRADIATION', LINE_STR):
                    irrad = self.db.get_irradiation(self.selected_irradiation)
                    if irrad:
                        levels = sorted([li.name for li in irrad.levels])
        if levels:
            self.selected_level = levels[0] if levels else 'LEVEL'

        return ['Level', LINE_STR] + levels

    @cached_property
    def _get_projects(self):

        if self.db:
            keys = [(pi, pi.name) for pi in self.db.get_projects()]
            keys = [(NULL_STR, NULL_STR)] + keys
            return dict(keys)
        else:
            return dict()

    @cached_property
    def _get_labnumbers(self):
        lns = []
        db = self.db
        if db:
            with db.session_ctx():
                if self.selected_level and not self.selected_level in ('Level', LINE_STR):
                    level = db.get_irradiation_level(self.selected_irradiation,
                                                     self.selected_level)
                    if level:
                        lns = [str(pi.labnumber.identifier)
                               for pi in level.positions]

        return sorted(lns)

    def _get_position(self):
        return self._position

    def _set_position(self, pos):
        self._position = pos

    def _get_info_label(self):
        return '{} {} {}'.format(self.labnumber, self.irradiation, self.sample)

    def _validate_position(self, pos):
        if not pos.strip():
            return ''

        for r in (SLICE_REGEX, SSLICE_REGEX, PSLICE_REGEX,
                  TRANSECT_REGEX, POSITION_REGEX):
            if r.match(pos):
                return pos
        else:
            for po in pos.split(','):
                try:
                    int(po)
                except ValueError:
                    ok = False
                    break
            else:
                ok = True

        if ok:
            return pos

    def _validate_extract_value(self, d):
        return self._validate_float(d)

    def _validate_float(self, d):
        try:
            return float(d)
        except ValueError:
            pass

    def _get_extract_value(self):
        return self._extract_value

    def _set_extract_value(self, t):
        if t is not None:
            self._extract_value = t
            if not t:
                self.extract_units = NULL_STR
            elif self.extract_units == NULL_STR:
                self.extract_units = self._default_extract_units
        else:
            self.extract_units = NULL_STR

    def _get_edit_pattern_label(self):
        return 'Edit' if self._use_pattern() else 'New'

    def _get_edit_template_label(self):
        return 'Edit' if self._use_template() else 'New'

    def _get_patterns(self):
        p = paths.pattern_dir
        extension = '.lp'
        patterns = list_directory(p, extension)
        return ['Pattern', 'None', LINE_STR, 'Remote Patterns'] + self.remote_patterns + \
               [LINE_STR, 'Local Patterns'] + patterns

    def _get_templates(self):
        p = paths.incremental_heat_template_dir
        extension = '.txt'
        temps = list_directory(p, extension)
        if self.template in temps:
            self.template = temps[temps.index(self.template)]
        else:
            self.template = 'Step Heat Template'

        return ['Step Heat Template', 'None', ''] + temps

    def _get_truncations(self):
        p = paths.truncation_dir
        extension = '.yaml'
        temps = list_directory(p, extension)
        return ['', ] + temps

    def _get_beam_diameter(self):
        bd = ''
        if self._beam_diameter is not None:
            bd = self._beam_diameter
        return bd

    def _set_beam_diameter(self, v):
        try:
            self._beam_diameter = float(v)
            self._update_run_values('beam_diameter', self._beam_diameter)
        except (ValueError, TypeError):
            pass

    def _get_truncation_str(self):
        if self.trunc_attr is not None and \
                        self.trunc_comp is not None and \
                        self.trunc_crit is not None:
            return '{}{}{}, {}'.format(self.trunc_attr, self.trunc_comp,
                                       self.trunc_crit, self.trunc_start)

    @cached_property
    def _get_flux(self):
        return self._get_flux_from_db()

    @cached_property
    def _get_flux_error(self):
        return self._get_flux_from_db(attr='j_err')

    def _get_flux_from_db(self, attr='j'):
        j = 0
        if self.labnumber:
            with self.db.session_ctx():
                dbln = self.db.get_labnumber(self.labnumber)
                if dbln:
                    if dbln.selected_flux_history:
                        f = dbln.selected_flux_history.flux
                        j = getattr(f, attr)
        return j

    def _set_flux(self, a):
        if self.labnumber and a is not None:
            self._flux = a

    def _set_flux_error(self, a):
        if self.labnumber and a is not None:
            self._flux_error = a

    def _get_end_after(self):
        return self._end_after

    def _set_end_after(self, v):
        self.set_end_after(v)
        self._end_after = v

    #===============================================================================

    # handlers
    #===============================================================================
    def _load_defaults_button_fired(self):
        if self.labnumber:
            self._load_default_scripts(self.labnumber)

    def _extract_group_button_fired(self):
        if self.edit_mode and \
                self._selected_runs and \
                not self.suppress_update:
            eg = self._selected_runs[0].extract_group + 1
            self.extract_group = eg

    @on_trait_change('trunc_+, truncation_path')
    def _edit_truncation(self, obj, trait, name, new):

        if self.edit_mode and \
                self._selected_runs and \
                not self.suppress_update:

            if name == 'truncation_path':
                t = add_extension(new, '.yaml') if new else None
            else:
                t = self.truncation_str

            if t:
                for s in self._selected_runs:
                    s.truncate_condition = t

            self.changed = True
            self.refresh_table_needed = True

    @on_trait_change('''cleanup, duration, extract_value,ramp_duration,
extract_units,
pattern,
position,
weight, comment, skip, extract_group''')
    def _edit_handler(self, name, new):
        if name == 'pattern':
            if not self._use_pattern():
                new = ''
                #print name, new, self._use_pattern()
        self._update_run_values(name, new)

    def _end_after_changed(self, new):
        print new
        self.clear_end_after = new

        #    if new:

    #        self.clear_end_after = True

    def set_end_after(self, v):
        self._update_run_values('end_after', v)

    @on_trait_change('''measurement_script:name, 
extraction_script:name, 
post_measurement_script:name,
post_equilibration_script:name
    ''')
    def _edit_script_handler(self, obj, name, new):
        if self.edit_mode and not self.suppress_update:
            if obj.label == 'Extraction':
                self._load_extraction_info(obj)

            if self._selected_runs:
                for si in self._selected_runs:
                    name = '{}_script'.format(obj.label)
                    setattr(si, name, new)
            self.changed = True
            self.refresh_table_needed = True

    def _skip_changed(self):
        self.update_info_needed = True

    def __labnumber_changed(self):
        if self._labnumber != NULL_STR:
            self.labnumber = self._labnumber

            #do go into edit mode if a run is selected
            if not self._selected_runs:
                self.edit_mode = True

    def _project_changed(self):
        self._clear_labnumber()

    def _selected_irradiation_changed(self):
        self._clear_labnumber()

    def _selected_level_changed(self):
        self._clear_labnumber()

    def _special_labnumber_changed(self):
        if not self.special_labnumber in ('Special Labnumber', LINE_STR):
            ln = convert_special_name(self.special_labnumber)
            if ln:
                if ln in ('dg', 'pa'):
                    pass
                else:
                    db = self.db
                    if not db:
                        return
                    with db.session_ctx():
                        ms = db.get_mass_spectrometer(self.mass_spectrometer)
                        ed = db.get_extraction_device(self.extract_device)
                        if ln in ('a', 'ba', 'c', 'bc', 'bg'):
                            ln = make_standard_identifier(ln, '##', ms.name[0].capitalize())
                        else:
                            msname = ms.name[0].capitalize()
                            edname = ''.join(map(lambda x: x[0].capitalize(), ed.name.split(' ')))
                            ln = make_special_identifier(ln, edname, msname)

                self.labnumber = ln
                self._load_extraction_info()

                self._labnumber = NULL_STR
            self._frequency_enabled = True

            if not self._selected_runs:
                self.edit_mode = True
        else:
            self._frequency_enabled = False

    def _labnumber_changed(self, old, labnumber):

        if not labnumber or labnumber == NULL_STR:
            return

        db = self.db
        if not db:
            return
        self.update_labnumber = labnumber

        special = False
        try:
            _ = int(labnumber)
        except ValueError:
            special = True

        # if labnumber has a place holder load default script and return
        if '##' in labnumber:
            self._load_scripts(old, labnumber)
            return

        self.irradiation = ''
        self.sample = ''

        self._aliquot = 0
        if labnumber:
            with db.session_ctx():
                # convert labnumber (a, bg, or 10034 etc)
                ln = db.get_labnumber(labnumber)
                if ln:
                    # set sample and irrad info
                    try:
                        self.sample = ln.sample.name
                    except AttributeError:
                        pass

                    try:
                        a = int(ln.analyses[-1].aliquot + 1)
                    except IndexError, e:
                        a = 1

                    self._aliquot = a

                    self.irradiation = self._make_irrad_level(ln)
                    if self.auto_fill_comment:
                        self.set_auto_comment()

                    self._load_scripts(old, labnumber)

                elif special:
                    ln = labnumber[:2]
                    if ln == 'dg':
                        self._load_extraction_defaults(ln)

                    if not (ln in ('pa', 'dg')):
                        '''
                            don't add pause or degas to database
                        '''
                        if self.confirmation_dialog(
                                'Lab Identifer {} does not exist. Would you like to add it?'.format(labnumber)):
                            db.add_labnumber(labnumber)
                            self._aliquot = 1
                            self._load_scripts(old, labnumber)
                        else:
                            self.labnumber = ''
                    else:
                        self._load_scripts(old, labnumber)
                else:
                    self.warning_dialog(
                        '{} does not exist. Add using "Labnumber Entry" or "Utilities>>Import"'.format(labnumber))

    def set_auto_comment(self):
        self.comment = '{}:{}'.format(self.irrad_level,
                                      self.irrad_hole)

    def _auto_fill_comment_changed(self):
        if self.auto_fill_comment:
            self.set_auto_comment()
        else:
            self.comment = ''

    def _edit_template_fired(self):
        temp = self._new_template()
        temp.on_trait_change(self._template_closed, 'close_event')

        self.open_view(temp)

    #         self._template = temp

    def _edit_pattern_fired(self):
        pat = self._new_pattern()
        pat.on_trait_change(self._pattern_closed, 'close_event')
        self.open_view(pat)

    #         self._pattern = pat

    def _edit_mode_button_fired(self):
        self.edit_mode = not self.edit_mode

    def _aliquot_changed(self):
        if self.edit_mode:
            for si in self._selected_runs:
                a = None
                if si.aliquot != self.aliquot:
                    a = int(self.aliquot)

                si.user_defined_aliquot = a
                #si.assigned_aliquot = int(self.aliquot)

            self.update_info_needed = True
            self.refresh_table_needed = True


            #def _edit_mode_changed(self):

            #    if self.edit_mode:

            #        self._load_default_scripts(self.labnumber)

    def _save_flux_button_fired(self):
        self._save_flux()

    #     def _application_changed(self):
    #         self.extraction_script.application = self.application
    #         self.measurement_script.application = self.application
    #         self.post_measurement_script.application = self.application
    #         self.post_equilibration_script.application = self.application


    @on_trait_change('mass_spectrometer, can_edit')
    def _update_value(self, name, new):
        for si in SCRIPT_NAMES:
            script = getattr(self, si)
            setattr(script, name, new)

            #===============================================================================
            # defaults
            #===============================================================================

    def _script_factory(self, label, name, kind='ExtractionLine'):
        return Script(label=label,
                      #                      names=getattr(self, '{}_scripts'.format(name)),
                      application=self.application,
                      mass_spectrometer=self.mass_spectrometer,
                      kind=kind,
                      #                       can_edit=self.can_edit
        )

    def _extraction_script_default(self):
        return self._script_factory('Extraction', 'extraction')

    def _measurement_script_default(self):
        return self._script_factory('Measurement', 'measurement', kind='Measurement')

    def _post_measurement_script_default(self):
        return self._script_factory('Post Measurement', 'post_measurement')

    def _post_equilibration_script_default(self):
        return self._script_factory('Post Equilibration', 'post_equilibration')

    def _clean_script_name(self, name):
        name = self._remove_mass_spectrometer_name(name)
        return self._remove_file_extension(name)

    def _remove_file_extension(self, name, ext='.py'):
        if not name:
            return name

        if name is NULL_STR:
            return NULL_STR

        if name.endswith('.py'):
            name = name[:-3]

        return name

    def _remove_mass_spectrometer_name(self, name):
        if self.mass_spectrometer:
            name = name.replace('{}_'.format(self.mass_spectrometer), '')
        return name

    def _factory_view_default(self):
        return self.factory_view_klass(model=self)

#============= EOF =============================================



