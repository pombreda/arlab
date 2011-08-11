#============= enthought library imports =======================

#============= standard library imports ========================
import wx
#============= local library imports  ==========================

#          RED                      YELLOW                  GREEN                  BLACK  
COLORS = [wx.Colour(220, 10, 10), wx.Colour(250, 200, 0), wx.Colour(10, 220, 10), wx.Colour(0, 0, 0)]
def change_intensity(color, fac):
    '''
        @type fac: C{str}
        @param fac:
    '''
    rgb = [color.Red(), color.Green(), color.Blue()]
    for i, intensity in enumerate(rgb):
        rgb[i] = min(int(round(intensity * fac, 0)), 255)

    return wx.Color(*rgb)

class wxLED(wx.Control):
    def __init__(self, parent):
        '''
            @type parent: C{str}
            @param parent:
        '''

        wx.Control.__init__(self, parent, -1, (0, 0), (20, 20), style = wx.NO_BORDER)


        self.set_state(0)

        self._blink = 0
        self.blink = False

        self.timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(200)

        self.Bind(wx.EVT_PAINT, self.OnPaint, self)

#    def set_blinking(self, blink):
#        self.blink = blink
#        self._blink = 0

    def OnTimer(self, event):
        '''
            @type event: C{str}
            @param event:
        '''
        if self.blink:
            if self._blink % 3 == 0:
                self._set_led_color(0, color = change_intensity(COLORS[self._state], 0.5))
            else:
                self._set_led_color(self._state)

            self._blink += 1
            if self._blink >= 100:
                self._blink = 0

    def set_state(self, s):
        '''
            @type s: C{str}
            @param s:
        '''
        self.blink = False
        #use negative values for blinking
        if s < 0:
            self.blink = True
        s = abs(s)
        self._state = s
        self._set_led_color(s)

    def _set_led_color(self, state, color = None):
        '''
            @type state: C{str}
            @param state:

            @type color: C{str}
            @param color:
        '''
        if color is not None:
            color1 = color
            color2 = color
        else:
            base_color = COLORS[state]
            color1 = base_color
            color2 = change_intensity(base_color, 0.5)

        ascii_led = '''
        000000-----000000      
        0000---------0000
        000-----------000
        00-----XXX-----00
        0----XXXXXXX----0
        0---XXXXXXXXX---0
        ----XXXXXXXXX----
        ---XXXXXXXXXXX---
        ---XXXXXXXXXXX---
        ---XXXXXXXXXXX---
        ----XXXXXXXXX----
        0---XXXXXXXXX---0
        0----XXXXXXX----0
        00-----XXX-----00
        000-----------000
        0000---------0000
        000000-----000000
        '''.strip()

        xpm = ['17 17 3 1', # width height ncolors chars_per_pixel
               '0 c None',
               'X c %s' % color1.GetAsString(wx.C2S_HTML_SYNTAX).encode('ascii'),
               '- c %s' % color2.GetAsString(wx.C2S_HTML_SYNTAX).encode('ascii'),
               #'= c %s' % shadow_color.GetAsString(wx.C2S_HTML_SYNTAX).encode('ascii'),
               #'* c %s' % highlight_color.GetAsString(wx.C2S_HTML_SYNTAX).encode('ascii')
               ]


        xpm += [s.strip() for s in ascii_led.splitlines()]
        self.bmp = wx.BitmapFromXPMData(xpm)
        self.Refresh()


    def OnPaint(self, e):
        '''
            @type e: C{str}
            @param e:
        '''
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bmp, 0, 0, True)
#============= EOF ====================================
#
#        ascii_led = '''
#        000000-----000000      
#        0000---------0000
#        000-----------000
#        00-----XXX----=00
#        0----XX**XXX-===0
#        0---X***XXXXX===0
#        ----X**XXXXXX====
#        ---X**XXXXXXXX===
#        ---XXXXXXXXXXX===
#        ---XXXXXXXXXXX===
#        ----XXXXXXXXX====
#        0---XXXXXXXXX===0
#        0---=XXXXXXX====0
#        00=====XXX=====00
#        000===========000
#        0000=========0000
#        000000=====000000
#        '''.strip()
#        
#        xpm = ['17 17 5 1', # width height ncolors chars_per_pixel
#               '0 c None', 
#               'X c %s' % base_color.GetAsString(wx.C2S_HTML_SYNTAX).encode('ascii'),
#               '- c %s' % light_color.GetAsString(wx.C2S_HTML_SYNTAX).encode('ascii'),
#               '= c %s' % shadow_color.GetAsString(wx.C2S_HTML_SYNTAX).encode('ascii'),
#               '* c %s' % highlight_color.GetAsString(wx.C2S_HTML_SYNTAX).encode('ascii')]
#