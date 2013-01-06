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



#============= enthought library imports =======================
#from traits.api import HasTraits, on_trait_change, Str, Int, Float, Button
#from traitsui.api import View, Item, Group, HGroup, VGroup

#============= standard library imports ========================

#============= local library imports  ==========================
from aerotech_axis import AerotechAxis
from src.hardware.motion_controller import MotionController


ACK = chr(6)
NAK = chr(15)
EOS = chr(10)


class AerotechMotionController(MotionController):
    def initialize(self, *args, **kw):
        '''
        '''
        self._communicator._terminator = None
        self.tell('##')
        self._communicator._terminator = chr(10)

#        for a in self.axes.itervalues():
#            a.load_parameters()

        return True

    def load_additional_args(self, config):
        '''

        '''
        path = self.configuration_dir_path
        for i, a in enumerate(['x', 'y', 'z']):
            ma = 5
            mi = -ma
            self.axes[a] = self._axis_factory(
#                                            path,
                                            name=a.upper(),
                                            parent=self,
                                            id=i + 1,
                                            negative_limit=mi,
                                            positive_limit=ma)

        return True

#    def single_axis_move(self, key, value):
#        '''
#        '''
#        axis = self.axes[key]
#        name = axis.name
#
#        # self._relative_move([name], [value-axis.position])
#        cmd = EIC + '%s%i' % (name, value - axis.position)
#
#        self.ask(cmd)
#
#        #for debugging 
#        #axis.position=value
#        #self._moving_()
#
#    def _relative_move(self, axes, values):
#        '''
#        '''
#
#        cmd = 'INDEX'
#
#        cmd = self._build_command(cmd, axes, values=values)
#        resp = self.ask(cmd)
#        return self._parse_response(resp)
#
#    def enable(self):
#        '''
#        '''
#
#        cmd = 'EN'
#
#        axes = ['X', 'Y']
#        axes = ' '.join(axes)
#        cmd = self._build_command(cmd, axes)
#        self.tell(cmd)
#        #resp=self.ask(cmd)
#        #return self._parse_response(resp)
#
#    def disable(self):
#        '''
#        '''
#
#        cmd = 'DI'
#
#        axes = ['X', 'Y', 'Z']
#        axes = ' '.join(axes)
#        cmd = self._build_command(cmd, axes)
#        self.tell(cmd)
#        #resp=self.ask(cmd)
#        #return self._parse_response(resp)
#
#    def home(self, *args, **ke):
#        '''
#        '''
#        cmd = 'HO'
#
#        axes = ['X', 'Y']
#        axes = ' '.join(axes)
#        cmd = self._build_command(cmd, axes)
#        resp = self.ask(cmd)
#        return self._parse_response(resp)
#
#    def get_current_position(self, key):
#        '''
#
#        '''
#        cmd = 'P'
#        axis = self.axes[key]
#        rtype = 4  # absolute command posisiton
#        axis = '%s%i' % (axis.name, rtype)
#        cmd = self._build_command(cmd, axis, remote=False)
#        r = self.ask(cmd)
#
#        return r
#
#    def set_parameter(self, pid, value):
#        '''
#
#        '''
#        cmd = 'WP%i,%s' % (pid, value) + EOS
#        r = self.ask(cmd)
#        self._ensure_ack(r)
#
#    def save_parameters(self):
#        '''
#        '''
#        cmd = 'SP'
#        r = self.ask(cmd)
#        self._ensure_ack(r)
#
#    def _ensure_ack(self, r):
#        '''
#
#        '''
#        r = r.strip()
#        if not r == ACK:
#            w = r
#            if r == NAK:
#                w = 'NAK'
#
#            self.warning('%s' % w)
#
#    def _build_command(self, cmd, axes, values=None, remote=True):
#        '''
#        '''
#
#        if values is None:
#            parameters = axes
#        else:
#            parameters = ' '.join(['{}{}'.format(*pi) for pi in zip(axes, values)])
#
#        if cmd.startswith('P'):
#            args = (cmd, parameters, EOS)
#            cmd = ''.join(args)
#        else:
#            args = (cmd, parameters, EOS)
#            cmd = '{} {}{}' % args
#
#        if remote:
#            cmd = EIC + cmd
#        return cmd
#
#    def _moving_(self):
#        '''
#        '''
##        n='5'
##        status=self._get_status(n)
##
##
##        status=[s for s in status]
##        status.reverse()        
##        #1 not in position
##        #0 in position
##        return status[4] or status[5] or status[6]
##    
#        pass
#
#    def _get_status(self, n):
#        '''
#
#        '''
#        cmd = 'PS'
#
#        cmd = self._build_command(cmd, n, remote=False)
#        r = self.ask(cmd)
#        if self.simulation:
#            r = '4'
#
#        return self._parse_status(r)
#
#    def _parse_status(self, r):
#        '''
#
#        '''
#
#        r = self._parse_response(r)
#        return make_bitarray(int(r), width=32)
#
#    def _parse_response(self, resp):
#        '''
#
#        '''
#        if resp is not None:
#            return resp.strip()

    def _axis_factory(self, **kw):
        '''
        '''
        a = AerotechAxis(**kw)
        return a

#if __name__ == '__main__':
#    amc = Aero


#============= EOF ====================================
