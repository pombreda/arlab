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
from traits.api import Bool

#============= standard library imports ========================
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
#============= local library imports  ==========================
from src.canvas.canvas2D.irradiation_canvas import IrradiationCanvas
from src.entry.level import load_holder_canvas
from src.loading.component_flowable import ComponentFlowable
from src.pdf.base_pdf_writer import BasePDFWriter
from src.pdf.items import Row


class IrradiationPDFWriter(BasePDFWriter):
    page_break_between_levels = Bool(True)
    show_page_numbers = True

    def _build(self, doc, irrad, *args, **kw):
        return self._make_levels(irrad)

    def _make_levels(self, irrad, progress=None):
        flowables = []
        irradname = irrad.name

        for level in sorted(irrad.levels, key=lambda x: x.name):
            if progress is not None:
                progress.change_message('Making {}{}'.format(irradname, level.name))
                progress.increment()

            c = self._make_canvas(level)
            fs = self._make_level_table(irrad, level, c)
            if c:
                c = ComponentFlowable(c, bounds=(200, 200),
                                      fixed_scale=True)
                flowables.append(c)

            flowables.extend(fs)

        return flowables, None

    def _make_level_table(self, irrad, level, c):
        rows = []
        flowables = []
        flowables.append(self._make_table_title(irrad, level))
        row = Row()
        for v in ('Pos.', 'L#', 'Sample', 'Note'):
            row.add_item(value=self._new_paragraph('<b>{}</b>'.format(v)))
        rows.append(row)

        srows = sorted([self._make_row(pi, c) for pi in level.positions],
                       key=lambda x: x[0])

        rows.extend(srows)

        ts = self._new_style(header_line_idx=0, header_line_width=2)

        ts.add('LINEBELOW', (0, 1), (-1, -1), 1.0, colors.black)

        t = self._new_table(ts, rows)
        t._argW[0] = 0.35 * inch
        t._argW[1] = 1. * inch
        t._argW[2] = 2 * inch

        flowables.append(t)
        if self.page_break_between_levels:
            flowables.append(self._page_break())
        else:
            flowables.append(self._new_spacer(0, 0.25 * inch))
        return flowables

    def _make_table_title(self, irrad, level):
        t = '{}{}'.format(irrad.name, level.name)
        p = self._new_paragraph(t, s='Heading1')
        return p

    def _make_row(self, pos, canvas):
        ln = pos.labnumber
        sample = ''
        identifier = ''
        if ln:
            if ln.sample:
                sample = ln.sample.name
            identifier = ln.identifier

        r = Row()
        r.add_item(value=pos.position)
        r.add_item(value=identifier)
        r.add_item(value=sample)
        r.add_item(value='')

        if sample:
            item = canvas.scene.get_item(pos.position)
            item.fill = True

        return r

    def _make_canvas(self, level):
        if level.holder:
            geom = level.holder.geometry
            canvas = IrradiationCanvas()
            load_holder_canvas(canvas, geom)
            return canvas


class LabbookPDFWriter(IrradiationPDFWriter):
    def _build(self, doc, irrads, progress=None, *args, **kw):
        flowables = []

        flowables.extend(self._make_title_page(irrads))

        for irrad in irrads:
            fs, _ = self._make_levels(irrad, progress)
            flowables.extend(self._make_summary(irrad))

            flowables.extend(fs)

        return flowables, None

    def _make_title_page(self, irrads):
        start = irrads[0].name
        end = irrads[-1].name
        l1 = 'New Mexico Geochronology Research Laboratory'
        l2 = 'Irradiation Labbook'
        if start != end:
            l3 = '{} to {}'.format(start, end)
        else:
            l3 = start

        t = '<br/>'.join((l1, l2, l3))
        p = self._new_paragraph(t, s='Title')
        return p, self._page_break()

    def _make_summary(self, irrad):
        fontsize = lambda x, f: '<font size={}>{}</font>'.format(f, x)

        name = irrad.name
        levels = ', '.join(sorted([li.name for li in irrad.levels]))

        date = '1/1/1'
        chron = irrad.chronology
        dur = 0
        if chron:
            doses = chron.get_doses()
            for st, en in doses:
                dur += (en - st).total_seconds()
            _, date = chron.get_doses(tofloat=False)[-1]

        dur /= (60 * 60.)
        date = 'Irradiation Date: {}'.format(date)
        dur = 'Irradiation Duration: {:0.1f} hrs'.format(dur)

        name = fontsize(name, 40)
        #levels = fontsize(levels, 28)
        #dur = fontsize(dur, 28)
        txt = '<br/>'.join((name, levels, date, dur))
        p = self._new_paragraph(txt,
                                s='Title',
                                textColor=colors.green,
                                alignment=TA_CENTER)

        return p, self._page_break()

#============= EOF =============================================