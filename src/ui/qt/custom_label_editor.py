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
from traits.etsconfig.etsconfig import ETSConfig

ETSConfig.toolkit = 'qt4'
#============= enthought library imports =======================
from traits.api import HasTraits, Str, Int, Color, Button, Any, Instance
from traitsui.api import View, Item, UItem
from traitsui.qt4.editor import Editor
from traitsui.basic_editor_factory import BasicEditorFactory
# from traitsui.wx.basic_editor_factory import BasicEditorFactory
# import wx
#============= standard library imports ========================
import random
from PySide.QtGui import QLabel
#============= local library imports  ==========================

class _CustomLabelEditor(Editor):
#    txtctrl = Any
    color = Any

    def init(self, parent):
        self.control = self._create_control(parent)
        #        self.item.on_trait_change(self._set_color, 'color')
        self.sync_value(self.factory.color, 'color', mode='from')

    def _color_changed(self):
        color = self.color.name()
        control = self.control
        self._set_color(color, control)

    def _set_color(self, color, control):
        if color and control:
            css = '''QLabel {{ color:{}; font-size:{}px; font-weight:{};}}
    '''.format(color, self.item.size, self.item.weight)
            control.setStyleSheet(css)

    def update_editor(self):
        if self.control:
        #             print self.object, self.value
            if isinstance(self.value, (str, int, float, long, unicode)):
                self.control.setText(str(self.value))
            #            self.control.SetLabel(self.value)

    def _create_control(self, parent):
        control = QLabel()
        color = self.item.color.name()
        self._set_color(color, control)
        #        css = '''QLabel {{ color:{}; font-size:{}px; font-weight:{};}}
        # # '''.format(self.item.color.name(), self.item.size, self.item.weight)
        #        control.setStyleSheet(css)


        #        control.setAlignment(Qt.AlignCenter)
        #        control.setGeometry(0, 0, self.item.width, self.item.height)
        #        vbox = QVBoxLayout()
        #        vbox.setSpacing(0)

        #        hbox = QHBoxLayout()

        #        hbox.addLayout(vbox)
        #        parent.addLayout(vbox)

        control.setMargin(5)
        parent.setSpacing(0)
        #        print vbox.getContentsMargins()
        #        vbox.setContentsMargins(5, 5, 5, 5)
        #        vbox.setSpacing(-1)
        #        vbox.addSpacing(5)
        #        vbox.addSpacing(10)
        #        vbox.addWidget(control)
        #        vbox.addSpacing(5)
        #        vbox.addStretch()

        #        vbox.setSpacing(-1)
        #        vbox.setMargin(10)
        #        control.setLayout(vbox)
        #        parent.addWidget(control)
        return control

    #        panel = wx.Panel(parent, -1)
#        size = None
#        if self.item.width > 1 and self.item.height > 1:
#            size = (self.item.width, self.item.height)
#        txtctrl = wx.StaticText(panel, label=self.value,
#                                size=size
#                                )
#        family = wx.FONTFAMILY_DEFAULT
#        style = wx.FONTSTYLE_NORMAL
#        weight = wx.FONTWEIGHT_NORMAL
#        font = wx.Font(self.item.size, family, style, weight)
#        txtctrl.SetFont(font)
#        txtctrl.SetForegroundColour(self.item.color)
#        self.txtctrl = txtctrl
#
#        vsizer = wx.BoxSizer(wx.VERTICAL)
# #
#        if self.item.top_padding is not None:
#            self.add_linear_space(vsizer, self.item.top_padding)
# #
#        vsizer.Add(txtctrl)
# #
#        if self.item.bottom_padding is not None:
#            self.add_linear_space(vsizer, self.item.bottom_padding)
#        sizer = vsizer
#
#        hsizer = wx.BoxSizer(wx.HORIZONTAL)
#        if self.item.left_padding is not None:
#            self.add_linear_space(hsizer, self.item.left_padding)
#
#        hsizer.Add(sizer)
#        if self.item.right_padding is not None:
#            self.add_linear_space(hsizer, self.item.right_padding)
#        sizer = hsizer
#
#        panel.SetSizer(sizer)
#        return panel
#
#
#    def add_linear_space(self, sizer, pad):
#        orientation = sizer.GetOrientation()
#        if orientation == wx.HORIZONTAL:
#            sizer.Add((pad, 0))
#        else:
#            sizer.Add((0, pad))

class CustomLabelEditor(BasicEditorFactory):
    klass = _CustomLabelEditor
    color = Str


class CustomLabel(UItem):
    editor = Instance(CustomLabelEditor, ())
    size = Int(12)

    color = Color('black')
    color_name = Str
    weight = Str('normal')

    top_padding = Int(5)
    bottom_padding = Int(5)
    left_padding = Int(5)
    right_padding = Int(5)


    def _color_name_changed(self):
        self.editor.color = self.color_name

#===============================================================================
# demo
#===============================================================================
class Demo(HasTraits):
    a = Str('asdfsdf')
    foo = Button
    color = Color('blue')
    cnt = 0

    def _foo_fired(self):
        self.a = 'fffff {}'.format(random.random())
        if self.cnt % 2 == 0:
            self.color = 'red'
        else:
            self.color = 'blue'
        self.cnt += 1

    def traits_view(self):

        v = View(
            'foo',
            CustomLabel('a',
                        #                             color='blue',
                        size=24,
                        top_padding=10,
                        left_padding=10,
                        color_name='color'
            ),
            width=100,
            height=100)
        return v


if __name__ == '__main__':
    d = Demo()
    d.configure_traits()
#============= EOF =============================================
