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
def func(word):
    rs = []
    groups = word.split(':')
    if len(groups) > 1:
        for gi in groups:
            if '-' in gi:
                owner, vs = gi.split('-')
            else:
                owner, vs = '', gi
            rs.append((owner, vs.split(',')))
    print rs

#=============enthought library imports=======================
from traits.api import Any, Dict, List, Bool
from pyface.timer.do_later import do_later
#=============standard library imports ========================
import os
import pickle
from pickle import PickleError
from Queue import Queue
from threading import Timer, Thread, Event
import time
import random
import weakref
from itertools import groupby
#=============local library imports  ==========================
from src.globals import globalv
from src.managers.manager import Manager
from src.extraction_line.explanation.explanable_item import ExplanableValve
from src.hardware.valve import HardwareValve
from src.extraction_line.section import Section
from src.paths import paths
from src.helpers.parsers.valve_parser import ValveParser
from src.loggable import Loggable
from src.constants import ALPHAS
# from src.ui.gui import invoke_in_main_thread
# from src.codetools.memory_usage import get_current_mem

class ValveGroup(object):
    owner = None
    valves = None


class ValveManager(Manager):
    '''
    Manager to interface with the UHV and HV pneumatic valves
    
    '''
    valves = Dict
    explanable_items = List
    extraction_line_manager = Any
    sampletime = 0.1
    # actuator = Any
    actuators = List
    canvas3D = Any
    sections = List

    sample_gas_type = None  # valid values None,sample,air
    sector_inlet_valve = None
    quad_inlet_valve = None

    query_valve_state = Bool(True)

    systems = None
    valve_groups = None

    use_explanation = True

    _prev_keys = None

    def show_valve_properties(self, name):
        v = self.get_valve_by_name(name)
        if v is not None:
            v.edit_traits()

    def kill(self):
        super(ValveManager, self).kill()
        self._save_soft_lock_states()

    def create_device(self, name, *args, **kw):
        '''
        '''
        dev = super(ValveManager, self).create_device(name, *args, **kw)
        if 'actuator' in name or 'controller' in name:
            if dev is not None:
                self.actuators.append(dev)
#        if name in ['valve_actuator', 'valve_controller']:
#            self.actuator = dev
            return dev

    def finish_loading(self, update=False):
        '''
   
        '''
        if self.actuators:
            for a in self.actuators:
                self.info('setting actuator {}'.format(a.name))

                self.info('comm. device = {} '.format(a._cdevice.__class__.__name__))

        # open config file
        setup_file = os.path.join(paths.extraction_line_dir, 'valves.xml')
        self._load_valves_from_file(setup_file)

        if globalv.load_valve_states:
            self._load_states()
        if globalv.load_soft_locks:
            self._load_soft_lock_states()

        self._load_system_dict()
        # self.info('loading section definitions file')
        # open config file
        # setup_file = os.path.join(paths.extraction_line_dir, 'section_definitions.cfg')
        # self._load_sections_from_file(setup_file)
    def _save_soft_lock_states(self):

        p = os.path.join(paths.hidden_dir, '{}_soft_lock_state'.format(self.name))
        self.info('saving soft lock state to {}'.format(p))
        with open(p, 'wb') as f:
            obj = dict([(k, v.software_lock) for k, v in self.valves.iteritems()])

            pickle.dump(obj, f)

    def load_valve_states(self, refresh=True):
        elm = self.extraction_line_manager
        word = self.get_state_word()
        changed = False
#         self.debug('valve state word= {}'.format(word))
        if word is not None:
            for k, v in self.valves.iteritems():
                if word.has_key(k):
                    s = word[k]
                    if s != v.state:
                        changed = True

                        v.set_state(s)
                        elm.update_valve_state(k, s)

        if refresh and changed:
            elm.refresh_canvas()

    def load_valve_lock_states(self, refresh=True):
        elm = self.extraction_line_manager
        word = self.get_lock_word()
        # self.debug('valve lock word= {}'.format(word))
        changed = False
        if word is not None:
            for k in self.valves.keys():
                if word.has_key(k):
                    v = self.get_valve_by_name(k)
                    s = word[k]
                    if v.software_lock != s:
                        changed = True

                        v.software_lock = s
                        elm.update_valve_lock_state(k, s)

        if refresh and changed:
            elm.refresh_canvas()

    def load_valve_owners(self, refresh=True):
        elm = self.extraction_line_manager

        '''
            needs to return all valves
            not just ones that are owned
        '''
        owners = self.get_owners_word()
        if not owners:
            self.debug('didnt not parse owners word')
            return

        changed = False
        ip = 'localhost'
        for owner, valves in owners:
            if owner != ip:
                for k in valves:
                    v = self.get_valve_by_name(k)
                    if v.owner != owner:
                        v.owner = owner
                        elm.update_valve_owner(k, owner)
                        changed = True

        if refresh and changed:
            elm.refresh_canvas()

    def get_owners_word(self):
        '''
         eg.
                1. 129.128.12.141-A,B,C:D,E,F
                2. A,B,C,D,E,F
                3. 129.128.12.141-A,B,C:129.138.12.150-D,E:F
                    A,B,C owned by 141,
                    D,E owned by 150
                    F free
        '''
        if self.actuators:
            rs = []
            actuator = self.actuators[0]
            word = actuator.get_owners()

            groups = word.split(':')
            if len(groups) > 1:
                for gi in groups:
                    if '-' in gi:
                        owner, vs = gi.split('-')
                    else:
                        owner, vs = '', gi

                    rs.append((owner, vs.split(',')))

            else:
                rs = [('', groups[0].split(',')), ]

            return rs

    def get_state_word(self):
        if self.actuators:
            actuator = self.actuators[0]
            word = actuator.get_state_word()
            return self._parse_word(word)

    def get_lock_word(self):
        if self.actuators:
            actuator = self.actuators[0]
            word = actuator.get_lock_word()
            return self._parse_word(word)

    def _parse_word(self, word):
        if word is not None:
            try:
                d = dict()
                if ',' in word:
                    for packet in word.split(','):
                        key = packet[:-1]
                        state = packet[-1:].strip()
                        if key[0] in ALPHAS \
                            and state in ('0', '1'):
                                d[key] = bool(int(state))
                else:
                    for i in xrange(0, len(word), 2):
                        packet = word[i:i + 2]
                        try:
                            key, state = packet[0], packet[1]
                        except IndexError:
                            return d

                        if key.upper() in ALPHAS:
                            if state in ('0', '1'):
                                d[key] = bool(int(state))

#                    d = dict([(word[i:i + 2][0], bool(int(word[i:i + 2][1]))) for i in xrange(0, len(word), 2)])
                return d
            except ValueError:
                pass

    def _load_states(self):
        elm = self.extraction_line_manager
        for k, v in self.valves.iteritems():
            s = v.get_hardware_state()
            elm.update_valve_state(k, s, refresh=False)
#             time.sleep(0.025)

    def _load_soft_lock_states(self):
        if self.extraction_line_manager.mode == 'client':
            for k, v in self.valves.iteritems():
                s = v.get_lock_state()
                func = self.lock if s else self.unlock
                func(k, save=False)
#                 time.sleep(0.025)

        else:
            p = os.path.join(paths.hidden_dir, '{}_soft_lock_state'.format(self.name))
            if os.path.isfile(p):
                self.info('loading soft lock state from {}'.format(p))

                with open(p, 'rb') as f:
                    try:
                        sls = pickle.load(f)
                    except PickleError:
                        pass

                    for v in self.valves:

                        if v in sls and sls[v]:
                            self.lock(v, save=False)
                        else:
                            self.unlock(v, save=False)

    def get_owners(self):
        '''
            eg.
                1. 129.128.12.141-A,B,C:D,E,F
                2. A,B,C,D,E,F
                3. 129.128.12.141-A,B,C:129.138.12.150-D,E:F
                    A,B,C owned by 141,
                    D,E owned by 150
                    F free
        '''
        vs = [(v.name, v.owner) for v in self.valves.itervalues()]
        key = lambda x: x[1]
        vs = sorted(vs, key=key)

        owners = []
        for owner, valves in groupby(vs, key=key):
            if owner:
                t = '{}-{}'.format(owner, ','.join(valves))
            owners.append(t)

        return ':'.join(owners)

    def get_software_locks(self):
#        locks = []
#        for k, v in self.valves.items():
#            locks.append(k)
#            locks.append('1' if v.software_lock else '0')

#            if self.query_valve_state:
#                s = self.get_state_by_name(k)
#            else:
#                s = v.state

        return ','.join(['{}{}'.format(k, int(v.software_lock)) for k, v in self.valves.iteritems()])
#        return ''.join(locks)

    def get_states(self, timeout=1):
        '''
            get as many valves states before time expires
            remember last set of valves returned. 
        
            if last set of valves less than total return 
            states for the remainder valves
            
        '''
        st = time.time()
        states = []
        keys = []
        prev_keys = []
        if self._prev_keys:
            clear_prev_keys = True
            prev_keys = self._prev_keys

        for k, v in self.valves.iteritems():
            '''
                querying a lot of valves can add up hence timeout.
                
                most valves are not queried by default which also helps shorten
                execution time for get_states. 
                
            '''
            if k in prev_keys:
                continue

            keys.append(k)
            state = '{}{}'.format(k, int(self._get_state_by(v)))
            states.append(state)
            if time.time() - st > timeout:
                break
        else:
            # if loop completes before timeout dont save keys
            clear_prev_keys = True

        if clear_prev_keys:
            keys = None

        self._prev_keys = keys
        return ','.join(states)


#    def _get_states(self, times_up_event, sq):
#
#        def _gstate(ki):
#            sq.put(ki)
#            s = self.get_state_by_name(ki)
#            sq.put('1' if s else '0')
#
#        dv = []
#        for k, v in self.valves.iteritems():
# #        for k, _ in self.valves.items():
#            if v.query_state:
#                dv.append(k)
#                continue
#
#            if times_up_event.isSet():
#                break
#
#            _gstate(k)
#
#        if times_up_event.isSet():
#            return
#
#        for k in dv:
#            if times_up_event.isSet():
#                break
#            _gstate(k)
#    def get_states2(self, timeout=1):
#        '''
#            use event and timer to allow for partial responses
#            the timer t will set the event in timeout seconds
#
#            after the timer is started _get_states is called
#            _get_states loops thru the valves querying their state
#
#            each iteration the times_up_event is checked to see it
#            has fired if it has the the loop breaks and returns the
#            states word
#
#            to prevent the communicator from blocking longer then the times up event
#            the _gs_thread is joined and timeouts out after 1.01s
#        '''
#
#        states_queue = Queue()
#        times_up_event = Event()
#        t = Timer(1, lambda: times_up_event.set())
#        t.start()
#        try:
#
#            _gs_thread = Thread(name='valves.get_states',
#                                target=self._get_states, args=(times_up_event, states_queue))
#            _gs_thread.start()
#            _gs_thread.join(timeout=1.01)
#        except (Exception,), e:
#            pass
#
#        # ensure word has even number of elements
#        s = ''
#        i = 0
#        n = states_queue.qsize()
#        if n % 2 != 0:
#            c = n / 2 * 2
#        else:
#            c = n
#
#        while not states_queue.empty() and i < c:
#            s += states_queue.get_nowait()
#            i += 1
#
#        return s

    def get_valve_by_address(self, a):
        '''
        '''
        return self._get_valve_by(a, 'address')

    def get_valve_by_description(self, a):
        '''
        '''
        return self._get_valve_by(a, 'description')

    def _get_valve_by(self, a, attr):
        return next((valve for valve in self.valves.itervalues() \
                            if getattr(valve, attr) == a), None)

    def get_valve_by_name(self, n):
        '''    
        '''
        if n in self.valves:
            return self.valves[n]

    def get_name_by_address(self, k):
        '''
        '''
        v = self.get_valve_by_address(k)
        if v is not None:
            return v.name

    def get_name_by_description(self, d):
        v = self.get_valve_by_description(d)
        if v is not None:
            return v.name.split('-')[-1]


    def get_evalve_by_name(self, n):
        '''  
        '''
        return next((item for item in self.explanable_items if item.name == n), None)

    def get_state_by_name(self, n):
        '''
        '''
        v = self.get_valve_by_name(n)
        state = None
        if v is not None:
            state = self._get_state_by(v)

        return state

    def get_state_by_description(self, n):
        '''
        '''
        v = self.get_valve_by_description(n)
        state = None
        if v is not None:
            state = self._get_state_by(v)

        return state

    def _get_state_by(self, v):
        '''
        '''
        state = None
        if self.query_valve_state and v.query_state:
            state = v.get_hardware_state()  # actuator.get_channel_state(v)

        if state is None:
            state = v.state
        else:
            v.state = state

        return state

    def get_actuator_by_name(self, name):
        if self.actuators:
#            for a in self.actuators:
#                if a.name == name:
#                    return a
            return next((a for a in self.actuators if a.name == name), None)

    def get_software_lock(self, name, description=None, **kw):
        if description:
            v = self.get_valve_by_description(description)
        else:
            v = self.get_valve_by_name(name)

        if v is not None:
            return v.software_lock

    def check_soft_interlocks(self, name):
        ''' 
        '''
        cv = self.get_valve_by_name(name)

        if cv is not None:
            interlocks = cv.interlocks
            valves = self.valves
            for v in valves:

                if valves[v].name in interlocks:
                    if valves[v].state:
                        return True

    def open_by_name(self, name, mode='normal'):
        '''
        '''
        return self._open_(name, mode)

    def close_by_name(self, name, mode='normal'):
        '''
        '''
        return self._close_(name, mode)

    def sample(self, name, period):
        v = self.get_valve_by_name(name)
        if v and not v.state:
            self.info('start sample')
            self.open_by_name(name)

            time.sleep(period)

            self.info('end sample')
            self.close_by_name(name)

    def lock(self, name, save=True):
        '''
        '''
        v = self.get_valve_by_name(name)
        if v is not None:
#            ev = self.get_evalve_by_name(name)
#            if ev is not None:
#                ev.soft_lock = True

            v.lock()
            if save:
                self._save_soft_lock_states()

    def unlock(self, name, save=True):
        '''
        '''
        v = self.get_valve_by_name(name)
        if v is not None:
#            ev = self.get_evalve_by_name(name)
#            if ev is not None:
#                ev.soft_lock = False

            v.unlock()
            if save:
                self._save_soft_lock_states()

    def set_valve_owner(self, name, owner):
        v = self.get_valve_by_name(name)
        if v is not None:
            v.owner = owner

    def validate(self, v):
        '''
        return false if v's interlock valve(s) is(are) open
        else return true
        '''

        return next((False for vi in v.interlocks if self.get_valve_by_name(vi).state), True)

#        #check interlock conditions
#        for i in v.interlocks:
#            t = self.get_valve_by_name(i)
#            if t.state:
#                return False
#        else:
#            return True

    def _open_(self, name, mode):
        '''
        '''
        action = 'set_open'
        # check software interlocks and return None if True
        if self.check_soft_interlocks(name):
            self.warning('Software Interlock')
            return

        return self._actuate_(name, action, mode)

    def _close_(self, name, mode):
        '''
        '''
        action = 'set_closed'
        if self.check_soft_interlocks(name):
            self.warning('Software Interlock')
            return

        return self._actuate_(name, action, mode)

    def _actuate_(self, name, action, mode, address=None):
        '''
        '''
        changed = False
        if address is None:
            v = self.get_valve_by_name(name)
            vid = name
        else:
            v = self.get_valve_by_address(address)
            vid = address

        result = None
        if v is not None:
            if not v.enabled:
                self.warning_dialog('{} {} not enabled'.format(v.name, v.description))
            else:
                act = getattr(v, action)

                result, changed = act(mode='{}-{}'.format(self.extraction_line_manager.mode, mode))
#                 if isinstance(result, bool):  # else its an error message
#                     if result:
#                         ve = self.get_evalve_by_name(name)
#                         ve.state = True if action == 'open' else False

    #                update the section state
    #                for s in self.sections:
    #                    s.update_state(action, v, self.valves, self.sample_gas_type, self.canvas3D.scene_graph)

                    # result = True

        else:
            self.warning('Valve {} not available'.format(vid))
            # result = 'Valve %s not available' % id

        return result, changed

    def _get_system_address(self, name):
        return next((h for k, h in self.systems.iteritems() if k == name), None)

    def _load_system_dict(self):
#        config = self.configparser_factory()

        from src.helpers.parsers.initialization_parser import InitializationParser
#        ip = InitializationParser(os.path.join(setup_dir, 'initialization.xml'))
        ip = InitializationParser()

        self.systems = dict()
        for name, host in ip.get_systems():
            self.systems[name] = host

#        config.read(os.path.join(setup_dir, 'system_locks.cfg'))
#
#        for sect in config.sections():
#            name = config.get(sect, 'name')
#            host = config.get(sect, 'host')
# #            names.append(name)
#            self.systems[name] = host
#
    def _load_sections_from_file(self, path):
        '''
        '''
        self.sections = []
        config = self.get_configuration(path=path)
        if config is not None:
            for s in config.sections():
                section = Section()
                comps = config.get(s, 'components')
                for c in comps.split(','):
                    section.add_component(c)

                for option in config.options(s):
                    if 'test' in option:
                        test = config.get(s, option)
                        tkey, prec, teststr = test.split(',')
                        t = (int(prec), teststr)
                        section.add_test(tkey, t)

                self.sections.append(section)

    def _load_valves_from_file(self, path):
        '''
        '''
        self.info('loading valve definitions file  {}'.format(path))
        def factory(v):
            name, hv = self._valve_factory(v)
            if self.use_explanation:
                self._load_explanation_valve(hv)
            self.valves[name] = hv
            return hv

#         self.valve_groups = dict()
        parser = ValveParser(path)
        for g in parser.get_groups():
            for v in parser.get_valves(group=g):
                factory(v)

#             valves = [factory(v) for v in parser.get_valves(group=g)]
#             vg = ValveGroup()
#             vg.valves = valves
#             self.valve_groups[g.text.strip()] = vg

        for v in parser.get_valves():
            factory(v)

    def _valve_factory(self, v_elem):
        name = v_elem.text.strip()
        address = v_elem.find('address')
        act_elem = v_elem.find('actuator')
        description = v_elem.find('description')
        interlocks = [i.text.strip() for i in v_elem.findall('interlock')]
        if description is not None:
            description = description.text.strip()

        actname = act_elem.text.strip() if act_elem is not None else 'valve_controller'
        actuator = self.get_actuator_by_name(actname)
        if actuator is None:
            if not globalv.ignore_initialization_warnings:
                self.warning_dialog('No actuator for {}. Valve will not operate. Check setupfiles/extractionline/valves.xml'.format(name))

        qs = True
        vqs = v_elem.get('query_state')
        if vqs:
            qs = vqs == 'true'

        hv = HardwareValve(name,
                           address=address.text.strip() if address is not None else '',
                           actuator=actuator,
                           description=description,
                           query_state=qs,
                           interlocks=interlocks
                           )
        return name, hv

    def _load_explanation_valve(self, v):
#        s = v.get_hardware_state()
        # update the extraction line managers canvas
#            self.extraction_line_manager.canvas.update_valve_state(v.name[-1], s)
        name = v.name.split('-')[1]
#        self.extraction_line_manager.update_valve_state(name, s)
#        args = dict(
#                    )
        ev = ExplanableValve(name=name,
                    address=v.address,
                    description=v.description,
#                    canvas=self.extraction_line_manager.canvas,
                    )
#        ev.state = s if s is not None else False
#        ev=weakref.ref(ev)()
        v.evalve = ev
#        v.evalve = weakref.ref(ev)()
        self.explanable_items.append(ev)
#===============================================================================
# deprecated
#===============================================================================
    #     def claim_section(self, section, addr=None, name=None):
#         try:
#             vg = self.valve_groups[section]
#         except KeyError:
#             return True
#
#         if addr is None:
#             addr = self._get_system_address(name)
#
#         vg.owner = addr
#
#     def release_section(self, section):
#         try:
#             vg = self.valve_groups[section]
#         except KeyError:
#             return True
#
#         vg.owner = None
#     def get_system(self, addr):
#         return next((k for k, v in self.systems.iteritems() if v == addr), None)
#     def check_group_ownership(self, name, claimer):
#         grp = None
#         for g in self.valve_groups.itervalues():
#             for vi in g.valves:
#                 if vi.is_name(name):
#                     grp = g
#                     break
#         r = False
#         if grp is not None:
#             r = grp.owner == claimer
#
# #        print name, claimer,grp, r
#         return r




if __name__ == '__main__':

    class Foo(Loggable):
        def get_state_by_name(self, m):
            b = random.randint(1, 5) / 50.0
            r = 0.1 + b
    #        r = 3
            self.info('sleep {}'.format(r))
            time.sleep(r)
            return True

        def _get_states(self, times_up_event, sq):
    #        self.states = []
            for k in ['A', 'B', 'Ca', 'Dn', 'Es', 'F', 'G', 'H', 'I']:
                if times_up_event.isSet():
                    break

                sq.put(k)
    #            self.info('geting state for {}'.format(k))
                s = self.get_state_by_name(k)
    #            self.info('got {} for {}'.format(s, k))
                if times_up_event.isSet():
                    break
                sq.put('1' if s else '0')

            # return ''.join(states)

        def get_states(self):
            '''
                with this method you need to ensure the communicators timeout
                is sufficiently low. the communicator will block until a response
                or a timeout. the times up event only breaks between state queries.
            
            '''
            states_queue = Queue()
            times_up_event = Event()
            t = Timer(1, lambda: times_up_event.set())
            t.start()
    #        states = self._get_states(times_up_event)
    #        return states
            t = Thread(target=self._get_states, args=(times_up_event, states_queue))
            t.start()
            t.join(timeout=1.1)
            s = ''

            n = states_queue.qsize()
            if n % 2 != 0:
                c = n / 2 * 2
            else:
                c = n

            i = 0
            while not states_queue.empty() and i < c:
                s += states_queue.get_nowait()
                i += 1

    #        n = len(s)
    #        if n % 2 != 0:
    #            sn = s[:n / 2 * 2]
    #        else:
    #            sn = s
    #        s = ''.join(self.states)
            self.info('states = {}'.format(s))
            return s

#    v = ValveManager()
#    p = os.path.join(paths.extraction_line_dir, 'valves.xml')
#    v._load_valves_from_file(p)
    from src.helpers.logger_setup import logging_setup

    logging_setup('foo')
    f = Foo()
    for i in range(10):
        r = f.get_states()
        time.sleep(2)
        # print r, len(r)

#==================== EOF ==================================
# def _load_valves_from_filetxt(self, path):
#        '''
#
#        '''
#        c = parse_setupfile(path)
#
#        self.sector_inlet_valve = c[0][0]
#        self.quad_inlet_valve = c[0][1]
#
#        actid = 6
#        curgrp = None
#        self.valve_groups = dict()
#
#        for a in c[1:]:
#            act = 'valve_controller'
#            if len(a) == actid + 1:
#                act = a[actid]
#
#            name = a[0]
#            actuator = self.get_actuator_by_name(act)
#            warn_no_act = True
#            if warn_no_act:
#                if actuator is None:
#                    self.warning_dialog('No actuator for {}. Valve will not operate. Check setupfiles/extractionline/valves.txt'.format(name))
#            print a
#            v = HardwareValve(name,
#                     address=a[1],
#                     actuator=self.get_actuator_by_name(act),
#                     interlocks=a[2].split(','),
#                     query_valve_state=a[4] in ['True', 'true']
# #                     group=a[4]
#                     )
#            try:
#                if a[5] and a[5] != curgrp:
#                    curgrp = a[5]
#                    if curgrp in self.valve_groups:
#                        self.valve_groups[curgrp].valves.append(v)
#                    else:
#                        vg = ValveGroup()
#                        vg.valves = [v]
#                        self.valve_groups[curgrp] = vg
#                else:
#                    self.valve_groups[curgrp].valves.append(v)
#
#            except IndexError:
#
#                #there is no group specified
#                pass
#
#            s = v.get_hardware_state()
#
#            #update the extraction line managers canvas
# #            self.extraction_line_manager.canvas.update_valve_state(v.name[-1], s)
#            self.extraction_line_manager.update_valve_state(v.name[-1], s)
#            args = dict(name=a[0],
#                        address=a[1],
#                        description=a[3],
#                        canvas=self.extraction_line_manager.canvas,
#
#                        )
#            ev = ExplanableValve(**args)
#            ev.state = s if s is not None else False
#
#            self.valves[name] = v
#            self.explanable_items.append(ev)

#        for k,g in self.valve_groups.iteritems():
#
#            for v in g.valves:
#                print k,v.name
