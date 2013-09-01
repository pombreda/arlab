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
from traits.api import HasTraits, Int
#============= standard library imports ========================
#============= local library imports  ==========================
from src.pdf.base_pdf_writer import BasePDFWriter
from src.helpers.formatting import floatfmt
from src.pdf.items import Row, Subscript, Superscript, NamedParameter, \
    FootNoteRow, FooterRow
from reportlab.lib.units import inch
from reportlab.lib import colors

def DefaultInt(value=40):
    return Int(value)



class SummaryTablePDFWriter(BasePDFWriter):
    def _build(self, doc, samples, title):

        title_para = self._new_paragraph(title)
        flowables = [title_para, self._vspacer(0.1)]

        t, t2 = self._make_table(samples)
        flowables.append(t)
        flowables.append(self._vspacer(0.1))
        flowables.append(t2)

        return flowables, None

    def _make_table(self, samples):
        style = self._new_style(
#                                 debug_grid=True,
                                header_line_idx=1
                                )

        style.add('ALIGN', (0, 0), (-1, -1), 'LEFT')
        style.add('LEFTPADDING', (0, 0), (-1, -1), 1)
        self._new_line(style, 0, cmd='LINEABOVE')

        data = []

        # make meta
#         meta = self._make_meta(analyses, style)
#         data.extend(meta)
#
        # make header
        header = self._make_header(style)
        data.extend(header)

        cnt = len(data)
        for i, sam in enumerate(samples):

            r = self._make_sample_row(sam)
            data.append(r)

            idx = cnt + i * 2
            style.add('BACKGROUND', (0, idx), (-1, idx),
                      colors.lightgrey,
                      )

        idx = len(data) - 1
        self._new_line(style, idx)
#         s = self._make_summary_rows(means, idx + 1, style)
#         data.extend(s)

        t = self._new_table(style, data, repeatRows=3)

        r = Row()
        r.add_blank_item(10)
        fdata = [r]
        style = self._new_style()
        style.add('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey)
        self._make_footnote_rows(fdata, style)
        self._make_footer_rows(fdata, style)
        ft = self._new_table(style, fdata, extend_last=True)

        return t, ft



    def _make_header(self, style):
        PMS = u'\u00b1 1\u03c3'


        pr = Row()
        pr.add_blank_item(6)
        pr.add_item(value='Preferred Age', span=-1)
#         style.add('ALIGN', (0, 3), (0, -1), 'CENTER')
        self._new_line(style, 0, weight=0.75, start=4, end=-1)

        r = Row()

        r.add_item(value='Sample')
        r.add_item(value='L#')
        r.add_item(value='Irrad')
        r.add_item(value='Material')

        r.add_item(value='N')
        r.add_item(value='MSWD')
        r.add_item(value='K/Ca')
        r.add_item(value=PMS)
        r.add_item(value='Age')
        r.add_item(value=PMS)

        return (pr, r,)
#         sigma = u'\u00b1 1\u03c3'
# #         sigma = self._plusminus_sigma()
#         super_ar = lambda x: '{}Ar'.format(Superscript(x))
#
#         _102fa = '(10{} fA)'.format(Superscript(2))
#         _103fa = '(10{} fA)'.format(Superscript(3))
#         minus_102fa = '(10{} fA)'.format(Superscript(-2))
#
# #         blank = self._make_footnote('BLANK',
# #                                    'Blank Type', 'LR= Linear Regression, AVE= Average',
# #                                    'Blank')
# #         blank = 'Blank Type'
#         line = [
#                 ('', ''),
#                 ('N', ''),
#                 ('Power', '(%)'),
#                 (super_ar(40), ''),
#                 (super_ar(40), _103fa), (sigma, ''),
#                 (super_ar(39), _103fa), (sigma, ''),
#                 (super_ar(38), ''), (sigma, ''),
#                 (super_ar(37), ''), (sigma, ''),
#                 (super_ar(36), ''), (sigma, minus_102fa),
#                 ('%{}*'.format(super_ar(40)), ''),
#                 ('{}*/{}{}'.format(super_ar(40),
#                                    super_ar(39),
#                                    Subscript('K')), ''),
#                 ('Age', '(Ma)'), (sigma, ''),
#                 ('K/Ca', ''),
#                 (sigma, ''),
# #                 (blank, 'type'),
# #                 (super_ar(40), ''), (sigma, ''),
# #                 (super_ar(39), ''), (sigma, ''),
# #                 (super_ar(38), ''), (sigma, ''),
# #                 (super_ar(37), ''), (sigma, ''),
# #                 (super_ar(36), ''), (sigma, ''),
#               ]
#
#         name_row, unit_row = zip(*line)
#
#         default_fontsize = 8
#         nrow = Row(fontsize=default_fontsize)
#         for i, ni in enumerate(name_row):
#             nrow.add_item(value=ni)
#
#         default_fontsize = 7
#         urow = Row(fontsize=default_fontsize)
#         for ni in unit_row:
#             urow.add_item(value=ni)
#
#         name_row_idx = 2
#         unit_row_idx = 3
#         # set style for name header
#         style.add('LINEABOVE', (0, name_row_idx),
#                   (-1, name_row_idx), 1.5, colors.black)
#
#         # set style for unit header
#         style.add('LINEBELOW', (0, unit_row_idx),
#                   (-1, unit_row_idx), 1.5, colors.black)
#
#         return [
#                 nrow,
#                 urow
#                 ]

    def _make_sample_row(self, sample):
        row = Row()
        row.add_item(value=sample.sample)
        row.add_item(value=sample.identifier)
        row.add_item(value=sample.material)
        row.add_item(value=sample.irradiation)
        row.add_item(value=sample.nanalyses)
        row.add_item(value=floatfmt(sample.mswd))
        row.add_item(value=self._value()(sample.weighted_kca))
        row.add_item(value=self._error()(sample.weighted_kca))
        row.add_item(value=self._value()(sample.weighted_age))
        row.add_item(value=self._error()(sample.weighted_age))

        return row


    def _set_row_heights(self, table, data):
        a_idxs = self._get_idxs(data, (FooterRow, FootNoteRow))
        for a, v in a_idxs:
            table._argH[a] = 0.19 * inch

        idx = self._get_idxs(data, Row)
        for i, v in idx:
            if v.height:
                table._argH[i] = v.height * inch

#===============================================================================
# summary
#===============================================================================
#     def _make_summary_rows(self, means, idx, style):
#         mean = means[0]
#         platrow = Row(fontsize=7, height=0.25)
#         platrow.add_item(value='Weighted Mean Age', span=5)
#
#         platrow.add_blank_item(n=10)
#         wa = mean.weighted_age
#         platrow.add_item(value=self._value()(wa))
#         platrow.add_item(value=u' \u00b1{}'.format(self._error()(wa)))
#
#         return [platrow]
#===============================================================================
# blanks
#===============================================================================

#===============================================================================
# footnotes
#===============================================================================
    def _make_footnote_rows(self, data, style):
        return

        data.append(Row(height=0.1))
        def factory(f):
            r = FootNoteRow(fontsize=6)
            r.add_item(value=f)
            return r
        data.extend([factory(fi) for fi in self._footnotes])

#         _get_idxs = lambda x: self._get_idxs(rows, x)
        _get_se = lambda x: (x[0][0], x[-1][0])
        # set for footnot rows
        footnote_idxs = self._get_idxs(data, FootNoteRow)
        sidx, eidx = _get_se(footnote_idxs)
        style.add('VALIGN', (0, sidx), (-1, eidx), 'MIDDLE')
        for idx, _v in footnote_idxs:
            style.add('SPAN', (0, idx), (-1, idx))
#            style.add('VALIGN', (1, idx), (-1, idx), 'MIDDLE')

    def _make_footer_rows(self, data, style):
        return

        rows = []
        df = 6
        for v in ('<b>Constants used</b>', '<b>Atmospheric argon ratios</b>'):
            row = FooterRow(fontsize=df)
            row.add_item(value=v, span=-1)
            rows.append(row)
            for i in range(19):
                row.add_item(value='')

        for n, d, v, e, r in (
                          (40, 36, 295.5, 0.5, 'Nier (1950)'),
                          (40, 38, 0.1880, 0.5, 'Nier (1950)'),
                          ):
            row = FooterRow(fontsize=df)
            row.add_item(value='({}Ar/{}Ar){}'.format(
                                                Superscript(n),
                                                Superscript(d),
                                                Subscript('A'),
                                                ),
                         span=3
                         )
            row.add_item(value=u'{} \u00b1{}'.format(v, e),
                         span=2)
            row.add_item(value=r, span=-1)
            rows.append(row)

            row.add_item(value='')
            rows.append(row)

        row = FooterRow(fontsize=df)
        row.add_item(value='<b>Interferring isotope production ratios</b>', span=-1)
        rows.append(row)
        for n, d, s, v, e, r in (
                          (40, 39, 'K'  , 295.5     , 0.5   , 'Nier (1950)'),
                          (38, 39, 'K'  , 0.1880    , 0.5   , 'Nier (1950)'),
                          (37, 39, 'K'  , 0.1880    , 0.5   , 'Nier (1950)'),
                          (39, 37, 'Ca' , 295.5     , 0.5   , 'Nier (1950)'),
                          (38, 37, 'Ca' , 0.1880    , 0.5   , 'Nier (1950)'),
                          (36, 37, 'Ca' , 0.1880    , 0.5   , 'Nier (1950)'),
                          ):
            row = FooterRow(fontsize=df)
            row.add_item(value='({}Ar/{}Ar){}'.format(
                                                Superscript(n),
                                                Superscript(d),
                                                Subscript(s),
                                                ),
                         span=3
                         )
            row.add_item(value=u'{} \u00b1{}'.format(v, e),
                         span=2)
            row.add_item(value=r, span=-1)
            rows.append(row)

        row = FooterRow(fontsize=df)
        row.add_item(value='<b>Decay constants</b>', span=-1)
        rows.append(row)

        for i, E, dl, v, e, r in (
                                  (40, 'K', u'\u03BB\u03B5', 1, 0, 'Foo (1990)'),
                                  (40, 'K', u'\u03BB\u03B2', 1, 0, 'Foo (1990)'),
                                  (39, 'Ar', '', 1, 0, 'Foo (1990)'),
                                  (37, 'Ar', '', 1, 0, 'Foo (1990)'),
                                  ):
            row = FooterRow(fontsize=df)
            row.add_item(value=u'{}{} {}'.format(Superscript(i), E, dl), span=3)
            row.add_item(value=u'{} \u00b1{} a{}'.format(v, e, Superscript(-1)), span=2)
            row.add_item(value=r, span=-1)
            rows.append(row)

        data.extend(rows)

        _get_idxs = lambda x: self._get_idxs(data, x)
        _get_se = lambda x: (x[0][0], x[-1][0])

        footer_idxs = _get_idxs(FooterRow)
        sidx, eidx = _get_se(footer_idxs)
        style.add('VALIGN', (0, sidx), (-1, eidx), 'MIDDLE')

#         for idx, v in footer_idxs:
#             for si, se in v.spans:
#                 style.add('SPAN', (si, idx), (se, idx))

        return rows
#===============================================================================
#
#===============================================================================

#============= EOF =============================================
# class TableSpec(HasTraits):
#     status_width = Int(5)
#     id_width = Int(20)
#     power_width = Int(30)
#     moles_width = Int(50)
#
#
#     ar40_width = DefaultInt(value=45)
#     ar40_error_width = DefaultInt()
#     ar39_width = DefaultInt(value=45)
#     ar39_error_width = DefaultInt()
#     ar38_width = DefaultInt()
#     ar38_error_width = DefaultInt()
#     ar37_width = DefaultInt()
#     ar37_error_width = DefaultInt()
#     ar36_width = DefaultInt()
#     ar36_error_width = DefaultInt(value=50)
