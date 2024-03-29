#===============================================================================
# Copyright 2011 Jake Ross
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

#=============enthought library imports=======================
from traits.api import HasTraits, List, Float, Str, Button, Int, on_trait_change
from traitsui.api import View, Item, CustomEditor, Handler, HGroup, spring

#=============standard library imports ========================
import wx
import wx.richtext as rt
from src.helpers.color_generators import colors8i
from pyface.timer.do_later import do_later, do_after
from email.mime.base import MIMEBase
from src.paths import paths
from src.viewable import ViewableHandler, Viewable
#=============local library imports  ==========================

def gui_decorator(func):
    def decorator(*args, **kw):
        if not 'gui' in kw or kw['gui']:
#            if kw['gui']:
            do_after(1, func, *args, **kw)
        else:
            func(*args, **kw)

#        if 'gui' in kw['gui'] and kw['gui']:
#            do_later(func, *args, **kw)
#        else:
#            func(*args, **kw)

    return decorator

#class DisplayHandler(Handler):
class DisplayHandler(ViewableHandler):
    def closed(self, info, is_ok):
        obj = info.object
        obj._opened = False
        obj.was_closed = True

        return super(DisplayHandler, self).closed(info, is_ok)

    def init(self, info):
        super(DisplayHandler, self).init(info)
#        print 'rrrrr', info
#        info.object.ui = info.ui
        if not info.object._opened and not info.object.was_closed:
            info.object.load_text_buffer()
            
        info.object._opened = True
        
#    @on_trait_change('object:disposed')  
#    def _update_disposed(self):
#        ui=self.ui
#        print ui, 'ffffff'
##    def object__disposed_fired(self, info):
##        print self, info.ui, 'sadsdffsd'
#        if ui:
#           ui.dispose()
# class RichTextDisplay(HasTraits):
class RichTextDisplay(Viewable):
    '''
    '''
    _display = None
    title = Str
    ui = None
    width = Float(625)
    height = Float(415)
#    delegated_text = List
#    text = List
    editable = False
    ok_to_open = True
    scroll_to_bottom = True

    _opened = False
    was_closed = False

    default_color = Str('red')
    default_size = Int(9)
#    bg_color = Str('white')
    bg_color = None

    x = Float(10)
    y = Float(20)

    # height of the text panel == height-_hspacer
    _hspacer = 25
    _text_buffer = List
    selectable = False
    id = ''

    font_name = 'Consolas'
#    font_name = 'Helvetica'

    @property
    def visible(self):
        return self._display is not None

#    def close(self):
#        if self.ui is not None:
#            self.ui.dispose()

    def traits_view(self):
        '''
        '''
        return View(
#                    VGroup(
                        Item('_display', show_label=False,
                         editor=CustomEditor(factory=self.factory,
                                             ),
                             height=1.0),
#                         )
#                           ),
                     handler=DisplayHandler,
                     title=self.title,
                     resizable=True,
#                     width=self.width,
#                     height=self.height,
                     x=self.x,
                     y=self.y,
                     id=self.id
                     )

    def factory(self, window, editor):
        '''
        '''
        panel = wx.Panel(window,
                       - 1,
                       wx.DefaultPosition,
                       )

        rtc = rt.RichTextCtrl(panel,
                              - 1,
                            size=wx.Size(self.width, self.height - self._hspacer),
                            style=wx.VSCROLL | wx.HSCROLL | wx.TE_READONLY
                            )

#        prevent moving the cursor
        if not self.selectable:
            rtc.Bind(wx.EVT_LEFT_DOWN, lambda x: x)

#        print self.bg_color
#        rtc.SetBackgroundColour(self.bg_color)
        if self.bg_color:
            rtc.SetBackgroundColour(self.bg_color)
#        panel.SetBackgroundColour(self.bg_color)

        rtc.SetEditable(self.editable)
        self._display = rtc
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(rtc, 1, wx.EXPAND | wx.ALL, 5)
        panel.SetSizer(sizer)

        return panel

    def load_text_buffer(self):
        self.add_text(self._text_buffer)
        self._text_buffer = []

#    @gui_decorator
    def clear(self, gui=True):
        self._text_buffer = []
        if gui:
            do_later(self._clear)
        else:
            self._clear()

    def _clear(self):
        d = self._display
        if d:
            d.Freeze()
            d.SelectAll()
            d.Delete(d.Selection)
            d.SelectNone()
            d.SetInsertionPoint(0)
            d.Thaw()


#        def _clear():
#    #        self.text = []
#            self._text_buffer = []
#
#            d = self._display
#            if d:
#    #            d.Freeze()
#    #            for i in range(4):
#                d.SelectAll()
#    #                d.DeleteSelection()
#                d.Delete(d.Selection)
#                d.SelectNone()
#                d.SetInsertionPoint(0)
# #            d.Thaw()
#        if gui:
#            do_after(1, _clear)
#        else:
#            _clear()

    def freeze(self):
        if self._display:
            self._display.Freeze()

    def thaw(self):
        if self._display:
            self._display.Thaw()

    def _create_font(self, size, name):
        family = wx.FONTFAMILY_MODERN
        style = wx.FONTSTYLE_NORMAL
        weight = wx.FONTWEIGHT_NORMAL
        font = wx.Font(size, family, style, weight, False, name)
        return font

    def _add_(self, msg, color=None, size=None,
              bold=False,
              underline=False, new_line=True,
              **kw):
        '''
            
        '''
        if not isinstance(msg, (str, unicode)):
            # print 'not str or unicode ', msg
            if not isinstance(msg, tuple):
                return
            msg = msg[0]

        d = self._display
        if color is None:
            color = wx.Colour(*colors8i[self.default_color])

        if size is None:
            size = self.default_size

        elif isinstance(color, str):
            if color in colors8i:
                color = wx.Colour(*colors8i[color])
            else:
                color = wx.Colour(*colors8i[self.default_color])
        else:
            color = wx.Colour(*color)

        font = self._create_font(size, name=self.font_name)
        d.BeginFont(font)
        d.BeginTextColour(color)

        if underline:
            d.BeginUnderline()
        if bold:
            d.BeginBold()

        d.WriteText(msg)

        if underline:
            d.EndUnderline()
        if bold:
            d.EndBold()

        d.EndTextColour()
        d.EndFont()
        if new_line:
            d.Newline()

        if self.scroll_to_bottom:
            n = 300
            ls = d.GetValue().split('\n')
            if len(ls) > n:
                s = sum(len(ls[i]) + 1 for i in xrange(10))
                d.Remove(0, s)
                lp = d.GetLastPosition()
                d.SetInsertionPoint(lp)

            lp = d.GetLastPosition()
            self.show_positon(lp + 10)

    def show_positon(self, ipos):
        try:
            d = self._display
    #        def _ShowPosition(self, ipos):
            line = d.GetVisibleLineForCaretPosition(ipos)
            ppuX, ppuY = d.GetScrollPixelsPerUnit()  # unit = scroll
    # step
            startYUnits = d.GetViewStart()[1]
            sy = d.GetVirtualSize()[1]

            if ppuY == 0:
                return False  # since there's no scrolling, hence no
    # adjusting

            syUnits = sy / ppuY
            r = line.GetRect()
            ry = r.GetY()
            rh = r.GetHeight()
            csY = d.GetClientSize()[1]
            csY -= d.GetBuffer().GetBottomMargin()

    #        if self.center_caret:
            if ry >= startYUnits * ppuY + csY - rh / 2:
                yUnits = startYUnits + csY / ppuY / 2
                d.SetScrollbars(ppuX, ppuY, 0, syUnits, 0, yUnits)
                d.PositionCaret()
        except AttributeError:
            pass
    #                return True
#        return False

    def _add_text(self, msg, **kw):
        '''
        '''

        disp = self._display
        if disp:
            if isinstance(msg, (list, tuple)):
                for mi in msg:
                    if isinstance(mi, tuple):
                        if len(mi) == 2:
                            kw = mi[1]
                        mi = mi[0]
                    self._add_(mi, **kw)
            else:
                self._add_(msg, **kw)
        else:
            self._text_buffer.append((msg, kw))

    def add_text(self, msg, gui=True, **kw):
        if gui:
            do_later(self._add_text, msg, **kw)
        else:
            self._add_text(msg, **kw)

#        def _add(msg, **kw):
#            disp = self._display
#            if disp:
#    ##            tappend = self.text.append
#    #            if isinstance(msg, (list, tuple)):
#    #                self.text += [len(mi) + 1 for mi in msg]
#    ##                for mi in msg:
#    ##                    tappend(len(mi) + 1)
#    #            else:
#    #                self.text.append(len(msg) + 1)
#    #                tappend(len(msg) + 1)
#
#                if isinstance(msg, (list, tuple)):
#                    for mi in msg:
#                        if isinstance(mi, tuple):
#                            if len(mi) == 2:
#                                kw = mi[1]
#                            mi = mi[0]
#                        self._add_(mi, **kw)
#
#    #                    print 'add', msg
#                else:
#                    self._add_(msg, **kw)
#            else:
#    #            pass
#                self._text_buffer.append((msg, kw))
#
#
#        if gui:
#            do_later(_add, msg, **kw)
# #            do_after(1, _add, msg, **kw)
#        else:
#            _add(msg, **kw)


from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import Encoders
import smtplib
from threading import Thread
import os
class ErrorDisplay(RichTextDisplay):
    report = Button
    _hspacer = 60
    def _report_fired(self):
        def send_report():
            try:
                msg = MIMEMultipart()
                msg['From'] = 'pychron'
                msg['To'] = 'nmgrlab@gmail.com'
                msg['Subject'] = 'Error Stack'

                msg.attach(MIMEText('\n'.join([t[0] for t in self.text])))

                # attach the most recent log file
                logdir = os.path.join(paths.root_dir, 'logs')
                logs = os.listdir(logdir)
                logs.reverse()
                for pi in logs:
                    if pi.startswith('pychron'):
                        pi = os.path.join(logdir, pi)
                        break

                with open(pi, 'rb') as f:
                    part = MIMEBase('application', "octet-stream")
                    part.set_payload(f.read())
                    Encoders.encode_base64(part)
                    part.add_header('Content-Disposition', 'attachment; filename="%s"' % os.path.basename(pi))
                    msg.attach(part)

                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login('nmgrlab', 'argon4039')

                server.sendmail('pychron', msg['To'], msg.as_string())
            except Exception, err:
                print err  # for debugging only
            finally:
                do_later(self.ui.dispose)

        t = Thread(target=send_report)
        t.start()

    def traits_view(self):
        v = super(ErrorDisplay, self).traits_view()
        v.content.content[0].content.append(HGroup(spring, Item('report', show_label=False)))
        return v
