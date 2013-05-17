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
from traits.api import HasTraits, Property, List, Str, Float, Int
from traitsui.api import View, Item, UItem, TabularEditor, VSplit, VGroup, HGroup
from src.database.isotope_analysis.summary import Summary, SummaryAdapter, \
    TextTable, TextRow, TextCell, BoldCell
from traitsui.tabular_adapter import TabularAdapter
from src.helpers.formatting import floatfmt, errorfmt, calc_percent_error
from src.constants import PLUSMINUS, PLUSMINUS_ERR
from src.ui.qt.text_table_editor import TextTableEditor
from kiva.fonttools import Font
#============= standard library imports ========================
#============= local library imports  ==========================
class SignalAdapter(TabularAdapter):
    columns = [
               ('Isotope', 'isotope'),
               ('Detector', 'detector'),
               ('Signal (fA)', 'signal_value'),
               ('{} 1s'.format(PLUSMINUS), 'signal_error'),
               ('Error Comp. %', 'error_component')
               ]

    isotope_width = Int(50)
    detector_width = Int(70)
    error_component_width = Int(100)
    signal_value_width = Int(100)
    signal_error_width = Int(80)

    signal_value_text = Property
    signal_error_text = Property
    error_component_text = Property

    def _get_error_component_text(self, *args, **kw):
        return floatfmt(self.item.error_component, n=2)
    def _get_signal_value_text(self, *args, **kw):
        return floatfmt(self.item.signal_value)
    def _get_signal_error_text(self, *args, **kw):
        return floatfmt(self.item.signal_error)

class RatiosAdapter(TabularAdapter):
    columns = [
               ('Ratio', 'name'),
               ('Value', 'value'),
               ('{}1s'.format(PLUSMINUS), 'error'),
#               ('*40Ar %', 'rad40_error'),

               ]

    name_width = Int(100)
    value_width = Int(80)
    error_width = Int(80)
    value_text = Property
    error_text = Property

#    rad40_error_text = Property

    def _get_value_text(self):
        return floatfmt(self.item.value)

    def _get_error_text(self):
        return floatfmt(self.item.error)
#    def _get_rad40_error_text(self):
#        return floatfmt(self.item.rad40_error)


ERROR_PERCENT_WIDTH = 50
VALUE_WIDTH = 60
ERROR_WIDTH = 60
class RawAdapter(TabularAdapter):
    columns = [
               ('Isotope', 'isotope'),
               ('Detector', 'detector'),
               ('Raw (fA)', 'raw_value'),
               ('{}1s'.format(PLUSMINUS), 'raw_error'),
               ('{}%'.format(PLUSMINUS), 'raw_error_percent'),
               ('Fit', 'fit'),

               ('Baseline (fA)', 'baseline_value'),
               ('{} 1s'.format(PLUSMINUS), 'baseline_error'),
               ('{}%'.format(PLUSMINUS), 'baseline_error_percent'),

               ('Blank (fA)', 'blank_value'),
               ('{} 1s'.format(PLUSMINUS), 'blank_error'),
               ('{}%'.format(PLUSMINUS), 'blank_error_percent'),

               ]


    isotope_width = Int(50)
    detector_width = Int(60)

    raw_value_width = Int(VALUE_WIDTH)
    raw_error_width = Int(ERROR_WIDTH)
    raw_error_percent_width = Int(ERROR_PERCENT_WIDTH)

    blank_value_width = Int(VALUE_WIDTH)
    blank_error_width = Int(ERROR_WIDTH)
    blank_error_percent_width = Int(ERROR_PERCENT_WIDTH)

    baseline_value_width = Int(VALUE_WIDTH + 20)
    baseline_error_width = Int(ERROR_WIDTH)
    baseline_error_percent_width = Int(ERROR_PERCENT_WIDTH)

    raw_value_text = Property
    raw_error_text = Property
    raw_error_percent_text = Property

    baseline_value_text = Property
    baseline_error_text = Property
    baseline_error_percent_text = Property

    blank_value_text = Property
    blank_error_text = Property
    blank_error_percent_text = Property

    def get_font(self, *args, **kw):
        from PySide.QtGui import QFont
        font = QFont()
        font.setPointSize(10)
        return font
#        return Font(f, size=10)

    def _get_raw_value_text(self, *args, **kw):
        return floatfmt(self.item.raw_value)

    def _get_raw_error_text(self, *args, **kw):
        return floatfmt(self.item.raw_error)

    def _get_raw_error_percent_text(self, *args, **kw):
        v = self.item.raw_value
        e = self.item.raw_error
        return calc_percent_error(v, e)

    def _get_baseline_value_text(self, *args, **kw):
        return floatfmt(self.item.baseline_value)

    def _get_baseline_error_text(self, *args, **kw):
        return floatfmt(self.item.baseline_error)

    def _get_baseline_error_percent_text(self, *args, **kw):
        v = self.item.baseline_value
        e = self.item.baseline_error
        return calc_percent_error(v, e)

    def _get_blank_value_text(self, *args, **kw):
        return floatfmt(self.item.blank_value)

    def _get_blank_error_text(self, *args, **kw):
        return floatfmt(self.item.blank_error)

    def _get_blank_error_percent_text(self, *args, **kw):
        v = self.item.blank_value
        e = self.item.blank_error
        return calc_percent_error(v, e)

class Signal(HasTraits):
    isotope = Str
    detector = Str
    fit = Str
    raw_value = Float
    raw_error = Float
    baseline_value = Float
    baseline_error = Float
    blank_value = Float
    blank_error = Float
    signal_value = Float
    signal_error = Float
    error_component = Float

class Ratio(HasTraits):
    value = Float
    error = Float
    name = Str
#    rad40_error = Float

class AnalysisSummaryAdapter(SummaryAdapter):
#    columns = 10
    def _make_tables(self, record):
        info_table = self._make_info_table(record)
        return [info_table]

    def _make_info_table(self, record):

        irrad = ''
        if record.irradiation:
            irrad = '{}{}'.format(record.irradiation.name,
                                  record.irradiation_level.name)

        j, je = record.j.nominal_value, record.j.std_dev
        flux = '{} {}{}'.format(floatfmt(j), PLUSMINUS, errorfmt(j, je))
        sens = ''
        tt = TextTable(
                       TextRow(
                               BoldCell('Analysis ID:'),
                               TextCell('{}'.format(record.record_id)),
                               BoldCell('Irradiation:'),
                               TextCell(irrad),
                               BoldCell('Sample:'),
                               TextCell('{}'.format(record.sample))
                               ),
                       TextRow(
                               BoldCell('Date:'),
                               TextCell('{}'.format(record.rundate)),
                               BoldCell('Time:'),
                               TextCell('{}'.format(record.runtime))
                               ),
                       TextRow(
                               BoldCell('Spectrometer:'),
                               TextCell('{}'.format(record.mass_spectrometer)),
                               BoldCell('Device:'),
                               TextCell('{}'.format(record.extract_device))
                               ),
                       TextRow(
                               BoldCell('J:'),
                               TextCell(flux),
                               BoldCell('Sensitivity:'),
                               TextCell(sens)
                               ),
                       TextRow(
                               BoldCell('Position:'),
                               TextCell(record.position),
                               BoldCell('Extract ({}):'.format(record.extract_units)),
                               TextCell(record.extract_value),
                               BoldCell('Duration (s):'),
                               TextCell(record.extract_duration),
                               BoldCell('Cleanup (s):'),
                               TextCell(record.cleanup_duration),
                               )
                       )
        return tt


class AnalysisSummary(Summary):
    signals = Property(List, depends_on='record')
    ratios = Property(List, depends_on='record')
    def _make_ratio(self, name, n, d, scalar=1):
        rr = (n / d) * scalar
        v, e = rr.nominal_value, rr.std_dev
        r = Ratio(
                  name=name,
                  value=v,
                  error=e
                )
        return r

    def _get_ratios(self):

        ratios = []
        self.record.age
        record = self.record
        arar_result = record.arar_result
        if arar_result:
            rad40 = arar_result['rad40']
            k39 = arar_result['k39']
            s36 = arar_result['s36']
            s39dec_cor = arar_result['s39decay_cor']
            s40 = arar_result['s40']

            ratios = [
                    self._make_ratio('40Ar%', rad40, s40, scalar=100),
                    self._make_ratio('40/36', s40, s36),
                    self._make_ratio('40/39K', s40, k39),
                    self._make_ratio('40/39', s40, s39dec_cor),
                    self._make_ratio('40*/36', rad40, s36),
                    self._make_ratio('40*/39K', rad40, k39),
                    self._make_ratio('K/Ca', record.kca, 1),
                    self._make_ratio('K/Cl', record.kcl, 1),

                    ]

#            self._make_ratio('%40*', rad40, s40, scalar=100)
        return ratios
    def _get_signals(self):
        record = self.record
        keys = record.isotope_keys
        isotopes = []
        for k in keys:
            iso = record.isotopes[k]
            name = iso.name
            det = iso.detector
            fit = iso.fit
            rv, re = iso.value, iso.error
            bv, be = iso.baseline.value, iso.baseline.error
            blv, ble = iso.blank.value, iso.blank.error
            s = iso.get_corrected_value()

            isotopes.append(Signal(isotope=name,
                                   detector=det,
                                   raw_value=rv,
                                   raw_error=re,
                                   fit=fit[0].upper(),
                                   baseline_value=bv,
                                   baseline_error=be,
                                   blank_value=blv,
                                   blank_error=ble,
                                   signal_value=s.nominal_value,
                                   signal_error=s.std_dev,
                                   error_component=record.get_error_component(k)
                                   )
                            )
        return isotopes

    def _calculate_error_components(self):
        record = self.record

#        keys = record.isotope_keys[:]
#        keys += ('j', 'ic_factor')
#        vs = []
#        mx = -1e20
#        for key in keys:
#            v = self.record.get_error_component(key)
#            vs.append(v)
#            if v > mx:
#                max_key = key
#                mx = v
#        components = dict()
#        for key, v in zip(keys, vs):
#            components[key] = v / 100.
#            if key == max_key:
#                self._print_value(key, v, int(v / 100.*50), color='red')
#            else:
#                self._print_value(key, v, int(v / 100.*50))

    def traits_view(self):
        v = View(
                 VSplit(
#                        UItem('record',
#                              editor=TextTableEditor(adapter=AnalysisSummaryAdapter()),
#                              height=0.5
#                              ),
                        UItem('record',
                              editor=TextTableEditor(adapter=AnalysisSummaryAdapter(),
                                                     bg_color='light yellow'
                                                     ),
                              height=0.2
                              ),
                        UItem('signals', editor=TabularEditor(adapter=RawAdapter(),
                                                       stretch_last_section=False,
                                                       auto_update=False,
                                                       editable=False
                                                       ),
                              height=0.5
                              ),
                       HGroup(
                              UItem('signals', editor=TabularEditor(adapter=SignalAdapter(),
                                                       stretch_last_section=False,
                                                       auto_update=False,
                                                       editable=False
                                                       ),
                                    height=0.8
                                    ),

                              UItem('ratios', editor=TabularEditor(adapter=RatiosAdapter(),
                                                       stretch_last_section=False,
                                                       auto_update=False,
                                                       editable=False
                                                       ),
                                    height=0.8
                                    ),

                              ),
                        )
                 )
        return v
#============= EOF =============================================

#
# class AnalysisSummary(Summary):
#    fit_selector = Instance(FitSelector)
#    selected_history = Str
#    histories = Property
#
#    def _build_summary(self):
#        record = self.record
# #        isos = record.isotope_keys
# #        isos = []
#
# #        isos = list(reversed(isos))
# #        if not isos:
# #            isos = []
#
#        # add header
#        columns = [('Det.', 0),
#                   ('Iso.', 0),
#                   ('Int.', 12), (PLUSMINUS_ERR, 18),
#                   ('Fit', 4),
#                   ('Baseline', 10), (PLUSMINUS_ERR, 18),
#                   ('Blank', 13), (PLUSMINUS_ERR, 18)
#                   ]
#        widths = [w for _, w in columns]
#
#        header = 'Det. Iso.  Int.       ' + PLUSMINUS_ERR + '           Fit '
#        header += 'Baseline  ' + PLUSMINUS_ERR + '           Blank       ' + PLUSMINUS_ERR + '           '
#
#        underline_width = len(header)
#
#        # add metadata
#        self._make_keyword('Analysis ID', record.record_id, width=30)
#
#        self._make_keyword('Date', record.rundate)
#        self._make_keyword('Time', record.runtime, new_line=True)
#
#        # add extraction
#        self._make_keyword('Mass Spectrometer', record.mass_spectrometer, width=30)
#        self._make_keyword('Extraction Device', record.extract_device, new_line=True)
#        exs = [
#                ('Position', record.position),
#                ('Extract', '{} ({})'.format(record.extract_value, record.extract_units)),
#                ('Duration', '{} (s)'.format(record.extract_duration)),
#                ('Cleanup', '{} (s)'.format(record.cleanup_duration)),
#                ]
#        n = len(exs)
#        for i, (name, value) in enumerate(exs):
#            self._make_keyword(name, value, True if i == n - 1 else False)
#
#        # add j
#        j, je = record.j.nominal_value, record.j.std_dev
#        self._make_keyword('J', '{} {}{}'.format(j, PLUSMINUS, self.make_error(j, je)),
#                           new_line=True)
#
#        # add sensitivity
#        s = record.sensitivity
#        m = record.sensitivity_multiplier
#
#        if s is not None:
#            if m is None:
#                m = 1
#            ss = s * m
#        else:
#            ss = NULL_STR
#
#        ic, ic_e = record.ic_factor
#        ics = '{} {}{}'.format(ic, PLUSMINUS, self.make_error(ic, ic_e))
#        self._make_keyword('IC', ics, new_line=True)
#        self._make_keyword('Sensitivity', ss, new_line=True)
#        # added header
#        self.add_text(header, underline=True, bold=True)
#
#        keys = record.isotope_keys
#        for k in keys:
#            iso = record.isotopes[k]
#            self._make_isotope(iso, widths, last_line=i == n)
#
#        # add corrected signals
#        m = 'Baseline Corrected Signals            Fully Corrected Signals'
#        self.add_text('{{:<{}s}}'.format(underline_width).format(m), underline=True, bold=True)
#        widths = [5, 12, 18, 5, 12, 12]
#
#        # refresh arar_result
#        self.record.calculate_age()
#
#        keys = record.isotope_keys
#        for k in keys:
#            self._make_corrected_signals(k, widths, underline_width, last_line=i == n)
#
# #        for i, iso in enumerate(isos):
# #            self._make_corrected_signals(n, i, iso, widths, underline_width)
#
#        # add corrected values
#        m = 'Corrected Values'
#        self.add_text('{{:<{}s}}'.format(underline_width).format(m), underline=True, bold=True)
# #
#        arar_result = record.arar_result
#        if arar_result:
#            rad40 = arar_result['rad40']
#            k39 = arar_result['k39']
#            s36 = arar_result['s36']
#            s39dec_cor = arar_result['s39decay_cor']
#            s40 = arar_result['s40']
#
#            self._make_ratio('%40*', rad40, s40, scalar=100)
#            self._make_ratio('40/36', s40, s36)
#            self._make_ratio('40/39K', s40, k39)
#            self._make_ratio('40/39', s40, s39dec_cor)
#            self._make_ratio('40*/36', rad40, s36)
#            self._make_ratio('40*/39K', rad40, k39, underline_width=underline_width - 2)
#
#        self.add_text(' ')
#
#        age = record.age
#        wo_jerr = record.age_error_wo_j
#
#        kca = self.record.kca
#        kcl = self.record.kcl
#        self._make_keyword('K/Ca', '{} {}{}'.format(self.floatfmt(kca.nominal_value, n=2),
#                                                    PLUSMINUS,
#                                                    self.make_error(kca.nominal_value, kca.std_dev)),
#                            new_line=True)
#
#        self._make_keyword('K/Cl', '{} {}{}'.format(self.floatfmt(kcl.nominal_value, n=2),
#                                                    PLUSMINUS,
#                                                    self.make_error(kcl.nominal_value, kcl.std_dev)),
#                            new_line=True, underline=underline_width)
#
#        self.add_text('  ')
#        self._make_keyword('Age', '{} {}{} ({})'.format(self.floatfmt(age.nominal_value, n=4),
#                                                        PLUSMINUS,
#                                                        self.make_error(age.nominal_value, age.std_dev),
#                                                        record.age_units),
#                           new_line=True
#                           )
#        self.add_text('             {}{} (Exclude Error in J)'.format(PLUSMINUS,
#                                                                      self.make_error(age.nominal_value, wo_jerr)
#                                                                      ))
#
#    def _make_ratio(self, name, nom, dem, scalar=1, underline_width=0):
#        try:
#            rr = nom / dem * scalar
#            v, e = rr.nominal_value, rr.std_dev
#        except ZeroDivisionError:
#            v, e = 0, 0
#
#        ms = [self.floatfmt(v), self.make_error(v, e)]
#        msg = ''.join([self.fixed_width(m, 15) for m in ms])
#
#        underline = False
#        if underline_width:
#            underline = True
#            msg = '{{:<{}s}}'.format(underline_width).format(msg)
#
#        self.add_text(self.fixed_width(name, 10), bold=True, new_line=False,
#                   underline=underline)
#        self.add_text(msg, size=11, underline=underline)
#
#    def _make_corrected_signals(self, iso, widths, lh, last_line=False):
#        s1 = self.record.isotopes[iso].baseline_corrected_value()
#        sv1 = self.floatfmt(s1.nominal_value)
#        bse1 = self.make_error(s1.nominal_value, s1.std_dev)
#
#        arar = self.record.arar_result
#        s2 = None
#        if arar:
#            iso = iso.replace('Ar', 's')
#            if iso in arar:
#                s2 = arar[iso]
#
#        if s2 is not None:
#            sv2 = self.floatfmt(s2.nominal_value)
#            bse2 = self.make_error(s2.nominal_value, s2.std_dev)
#        else:
#            sv2 = NULL_STR
#            bse2 = NULL_STR
#
#        msgs = [sv1, bse1,
#                ' ',
#                sv2, bse2]
#        msg = ''.join([self.fixed_width(m, w) for m, w in zip(msgs, widths[1:])])
#        if last_line:
#            lh = lh + widths[0] - 2
#            msg = '{{:<{}s}}\n'.format(lh).format(msg)
#
#        self.add_text(self.fixed_width(iso, widths[0]), bold=True,
#                  new_line=False,
#                  underline=last_line)
#        self.add_text(msg, size=11, underline=last_line)
#
#    def _make_isotope(self, iso, widths, last_line=False):
#        name = iso.name
#        det = iso.detector
#        fit = iso.fit
#        sv, se = iso.value, iso.error
#        bv, be = iso.baseline.value, iso.baseline.error
#        blv, ble = iso.blank.value, iso.blank.error
#        msgs = [
#                self.floatfmt(sv),
#                self.make_error(sv, se),
#                fit[0].upper(),
#                self.floatfmt(bv),
#                self.make_error(bv, be),
#                self.floatfmt(blv),
#                self.make_error(blv, ble)
#                ]
#
#        msg = ''.join([self.fixed_width(m, w) for m, w in zip(msgs, widths[2:])])
#        if last_line:
#            msg += '\n'
#
#        self.add_text(self.fixed_width(det, 5),
#                   bold=True,
#                  new_line=False,
#                  underline=last_line)
#        self.add_text(self.fixed_width(name, 6),
#                   bold=True,
#                  new_line=False,
#                  underline=last_line)
#        self.add_text(msg, size=11, underline=last_line)
#
# #    def _make_signals(self, n, i, iso, widths):
# #        sg = self.record.signal_graph
# #        pi = n - i
# #
# #        det = sg.plots[pi].detector
# #        fit = sg.get_fit(pi) if sg else ' '
# #        sv, se = self._get_signal(iso)
# #        bv, be = self._get_signal('{}bs'.format(iso))
# #        blv, ble = self._get_signal('{}bl'.format(iso))
# #
# #        msgs = [
# #                self.floatfmt(sv),
# #                self.make_error(sv, se),
# #                fit[0].upper(),
# #                self.floatfmt(bv),
# #                self.make_error(bv, be),
# #                self.floatfmt(blv),
# #                self.make_error(blv, ble)
# #                ]
# #
# #        msg = ''.join([self.fixed_width(m, w) for m, w in zip(msgs, widths[2:])])
# #        if i == n:
# #            msg += '\n'
# #
# #        self.add_text(self.fixed_width(det, 5),
# #                   bold=True,
# #                  new_line=False,
# #                  underline=i == n)
# #        self.add_text(self.fixed_width(iso, 6),
# #                   bold=True,
# #                  new_line=False,
# #                  underline=i == n)
# #        self.add_text(msg, size=11, underline=i == n)
#
#    def _get_histories(self):
#        histories = []
#        if self.record.dbrecord.arar_histories:
#            histories = [hi.create_date for hi in self.record.dbrecord.arar_histories]
#
#        return ['Collection'] + histories
#
#    def traits_view(self):
#        v = View(
# #                 VGroup(
# #                     HGroup(Item('selected_history', show_label=False,
# #                                 editor=EnumEditor(name='histories'))),
#                     VSplit(
#                            UItem('record',
#                                 editor=TextTableEditor(adapter=AnalysisAdapter(),
#                                                 clear='clear_event',
#                                                 bg_color='lightgreen'
#                                                 ),
#                                  height=1.0,
#                                style='custom'),
#                            #                 Item('display', height=0.75, show_label=False, style='custom'),
#                            UItem('fit_selector',
#                                  height= -100,
#                                  style='custom')
#                            )
# #                        )
#                 )
#        return v
#
#
#
#
##============= EOF =============================================
# # class AnalysisSummary2(HasTraits):
# #    age = Float
# #    error = Float
# #    record = Any
# #
# #    summary = Property(depends_on='age,err')
# #
# #    header1 = ['ID', 'Date', 'Time']
# #    header2 = ['Detector', 'Signal']
# #
# #    def _get_summary(self):
# #        from jinja2 import Template
# #        doc = '''
# # {{header1}}
# # {{data1}}
# #
# # Name:{{record.filename}}
# # Root:{{record.directory}}
# #
# # {{header2}}
# # {%- for k,v in signals %}
# # {{k}}\t{{v}}
# # {%- endfor %}
# #
# # Age : {{obj.age}}\xb1{{obj.error}}
# # '''
# #
# #        data1 = map(lambda x: getattr(self.record, x), ['rid', 'rundate', 'runtime'])
# #
# #        temp = Template(doc)
# #        join = lambda f, n: ('\t' * n).join(f)
# # #        join = '\t\t\t'.join
# #        entab = lambda x:map('{}'.format, map(str, x))
# #        makerow = lambda x, n: join(entab(x), n)
# #        record = self.record
# #        r = temp.render(record=record,
# #                           header1=makerow(self.header1, 3),
# #                           header2=makerow(self.header2, 1),
# #                           data1=makerow(data1, 3),
# #                           signals=zip(record.det_keys,
# #                                       record.intercepts
# #                                       ),
# #                           obj=self,
# #                           )
# #        return r
# #
# #    def traits_view(self):
# # #        s = 51
# #        ha1 = wx.TextAttr()
# #        f = wx.Font(12, wx.MODERN, wx.NORMAL,
# #                         wx.NORMAL, False, u'Consolas')
# #        f.SetUnderlined(True)
# #        ha1.SetFont(f)
# #        ha1.SetTabs([200, ])
# #
# #        f.SetUnderlined(False)
# #        f.SetPointSize(10)
# #        f.SetWeight(wx.FONTWEIGHT_NORMAL)
# #
# #        da = wx.TextAttr(colText=(255, 100, 0))
# #        da.SetFont(f)
# #
# #        ha2 = wx.TextAttr()
# #        f.SetPointSize(12)
# #        f.SetUnderlined(True)
# #        ha2.SetFont(f)
# #
# #        ba = wx.TextAttr()
# #        f.SetUnderlined(False)
# #        ba.SetFont(f)
# #        f.SetPointSize(10)
# #
# #        styles = {1:ha1,
# #                  2:da,
# #                  (3, 4, 5, 6):ba,
# #                  7:ha2,
# #                  (8, 9, 10, 11):ba
# #                  }
# #
# #        v = View(Item('summary', show_label=False,
# # #                      editor=HTMLEditor()
# #                        style='custom',
# #                        editor=SelectableReadonlyTextEditor(
# #                        styles=styles,
# #                        )
# #                      )
# #                 )
# #        return v
