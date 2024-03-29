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
from traits.api import Any, Float, Instance, on_trait_change
from traitsui.api import View, Item, Handler
import apptools.sweet_pickle as pickle
#============= standard library imports ========================
from os import path
#============= local library imports  ==========================
from src.managers.manager import Manager
from src.paths import paths
# from src.machine_vision.detectors.co2_detector import CO2HoleDetector
# from src.machine_vision.detectors.tray_mapper import TrayMapper
# from src.machine_vision.detectors.brightness_detector import BrightnessDetector
from src.image.video import Video
from src.machine_vision.detectors.hole_detector import HoleDetector
# from pyface.timer.do_later import do_later


class ImageHandler(Handler):
    def init(self, info):
        info.object.ui = info.ui

class MachineVisionManager(Manager):
    video = Any
    laser_manager = Any
    pxpermm = Float(23.1)
    detector = Instance(HoleDetector)

    def get_new_frame(self):
        src = self.video.get_frame()
        return src

    def _video_default(self):
        if self.parent is None:
            v = Video()
            v.open(identifier=1)
        else:
            v = self.parent.video

        return v

    @on_trait_change('laser_manager:zoom')
    def update_zoom(self, new):
        self.pxpermm = self._calc_pxpermm_by_zoom(new)

    def _calc_pxpermm_by_zoom(self, z):
        from numpy import polyval

        c = map(float, self.parent._camera_xcoefficients.split(','))
        pxpercm = polyval(c, z)

        return pxpercm / 10.0
    def load_detector(self):
        pass
    def dump_detector(self):
        pass
    def _detector_default(self):
        return self.load_detector()

    def _dump_detector(self, name, obj):
        p = path.join(paths.hidden_dir, name)
        with open(p, 'wb') as f:
            pickle.dump(obj, f)

    def _load_detector(self, name, klass):
        p = path.join(paths.hidden_dir, name)
        if path.isfile(p):
            with open(p, 'rb') as f:
                try:
                    hd = pickle.load(f)
                    if not isinstance(hd, klass):
                        hd = klass()

                except Exception, e:
                    print e
        else:
            hd = klass()

        hd.parent = self
        if self.laser_manager is not None:
            motor = self.laser_manager.get_motor('zoom')
            if motor is not None:
                z = motor.data_position
                hd.pxpermm = self._calc_pxpermm_by_zoom(z)

        hd.name = name
        return hd

# class MachineVisionManager(Manager):
#    video = Any
#    stage_controller = Any
#    laser_manager = Any
#    autofocus_manager = Any
#
#    croppixels = None
#
# #    crosshairs_offsetx = 0
# #    crosshairs_offsety = 0
#
#    threshold = Property(Range(0, 255, 65), depends_on='_threshold')
#    _threshold = Int
#    test = Button
#
#    title = Property
#
#    hole_detector = Instance(CO2HoleDetector)
#    brightness_detector = Instance(BrightnessDetector)
#
#
#    calibration_detector = Any
#
# #    testing = False
# #    _debug = Bool(False)
#
#    application = DelegatesTo('parent')
#
# #    def _zoom_calibration(self):
# #        d = ZoomCalibrationDetector(parent=self,
# #                                    image=self.image,
# #                                    pxpermm=self.pxpermm)
# #        self._spawn_thread(d.do_zoom_calibration())
#
#    def learn(self):
#        '''
#        when user hits locate center, save that image
#
#
#        '''
#        from src.machine_vision.stage_learner import StageLearner
#        sl = StageLearner(laser_manager=self.laser_manager,
#                          machine_vision=self)
#
#        sl.edit_traits()
# #        sl.teach_learner()
#
#
#    def locate_target(self, cx, cy, holenum, *args, **kw):
#        try:
#            if self.parent:
#                sm = self.parent._stage_map
#                holedim = sm.g_dimension / 2.
#            else:
#                holedim = 1.5
# #            cx = 0
# #            cy = 0
#            params = self.hole_detector.locate_sample_well(cx, cy, holenum, holedim, **kw)
#            msg = 'Target found at {:0.3n}, {:0.3n}'.format(*params) if params else 'No target found'
#            self.info(msg)
#            return params
#
#        except TypeError:
#            import traceback
#            traceback.print_exc()
#
#    def dump_hole_detector(self):
#        p = path.join(paths.hidden_dir, 'hole_detector')
#        with open(p, 'wb') as f:
#            pickle.dump(self.hole_detector, f)
#
#    def load_hole_detector(self):
#        return self._load_detector('hole_detector', CO2HoleDetector)
#
#    def load_brightness_detector(self):
#        return self._load_detector('brightness_detector', BrightnessDetector)
#
#    def get_intensity(self, **kw):
#        det = self.brightness_detector
#        return det.get_intensity(**kw)
#
#    def collect_baseline_intensity(self, **kw):
#        self.video.open()
#        det = self.brightness_detector
#        return det.collect_baseline_intensity(**kw)
#
#    def cancel_calibration(self):
#        self._cancel_calibration = True
#
#    def do_auto_calibration(self, calibration_item):
#        self._cancel_calibration = False
#        cx, cy, rx, ry = self._calculate_calibration()
#
#        if cx and cy and rx and ry:
#            calibration_item.set_center(cx, cy)
#            calibration_item.set_right(rx, ry)
#
#        #now move thru all the holes mapping each one
#        sm = self.parent._stage_map
#        for h in  sm.sample_holes:
#            if self._cancel_calibration:
#                break
#            self.parent._move_to_hole(h.id)
#
#        #interpolate correct positions for holes that could not be
#        #identified
#        sm.interpolate_noncorrected()
#
#    def _calculate_calibration(self):
#        cx = None
#        cy = None
#        rx = None
#        ry = None
#        sm = self.parent._stage_map
#        #move to a set of calibration holes
#        #n,e,s,w,c
#        if sm.calibration_holes is None:
#            self.warning('no calibration holes')
#            return
#
#        for ch in sm.calibration_holes:
#            if self._cancel_calibration:
#                self.info('moving to calibration hole {}'.format(ch))
#                self.parent._move_to_hole(ch)
#                return
#
#        print sm.calibration_holes
#        #calculate the center pos
#        npos = [[], []]
#        for a, b, i in [(0, 2, 1), (1, 3, 0)]:
#            a = sm.calibration_holes[a]
#            b = sm.calibration_holes[b]
#            cpos1 = sm.get_corrected_hole_pos(a)
#            cpos2 = sm.get_corrected_hole_pos(b)
#            if cpos1 and cpos2:
#                d = abs(cpos1[i] - cpos2[i]) / 2.0
#                npos[i].append(min(cpos1[i], cpos2[i]) + d)
#
#        ccpos = sm.get_corrected_hole_pos(sm.calibration_holes[4])
#        if ccpos:
#            npos[0].append(ccpos[0])
#            npos[1].append(ccpos[1])
#
#        if npos[0] and npos[1]:
#            print 'npos', npos
#            cx = sum(npos[0]) / len(npos[0])
#            cy = sum(npos[1]) / len(npos[1])
#
#            rots = []
#            #calculate the rotations between c and n,s, c and e,w
#            for i, offset in [(0, -90), (2, -90), (1, 0), (3, 0)]:
#                npos = sm.get_corrected_hole_pos(sm.calibration_holes[i])
#                if npos is not None:
#                    rot = math.atan2((cx - npos[0]), (cy - npos[1]))\
#                            + math.radians(offset)
#                    rots.append(rot)
#
#            rightx, righty = sm.get_hole_pos(sm.calibration_holes[1])
#            centerx, centery = sm.get_hole_pos(sm.calibration_holes[4])
#
#            L = ((centerx - rightx) ** 2 + (centery - righty) ** 2) ** 0.5
#
#            print 'calculated rotations', rots
#            if rots:
#                rot = sum(rots) / len(rots)
#                rx = cx + L * math.cos(rot)
#                ry = cy + L * math.sin(rot)
#
#        return cx, cy, rx, ry
#
#    def map_holes(self):
# #        self._load_source()
# #        self.get_new_frame()
# #        self.image.panel_size = 450
#        if self.parent is None:
#            from src.lasers.stage_managers.stage_map import StageMap
#            p = path.join(paths.setup_dir, 'tray_maps', '221-hole.txt')
#            sm = StageMap(file_path=p)
#            center_mx, center_my = 3.596, -13.321
#            cpos = -2.066, -0.695
#            rot = 358.099
#
#        else:
#            sm = self.parent._stage_map
#            ca = self.parent.canvas.calibration_item
#            if ca is not None:
#                rot = ca.rotation
#                cpos = ca.center
#
#        tm = TrayMapper(
#                        #image=self.image,
#
#                        #working_image=self.working_image,
#                        stage_map=sm,
# #                        center_mx=center_mx,
# #                        center_my=center_my,
#                        calibrated_center=cpos,
#                        calibrated_rotation=rot,
#                        pxpermm=self.pxpermm,
# #                        _debug=self._debug,
#                        parent=self
#                        )
#
#        self.hole_detector = tm
#        if self.parent is not None:
#            center_mx = self.parent.stage_controller.x
#            center_my = self.parent.stage_controller.y
#
#        regions = [(0, 0)]
#        for r in regions:
#            #move to a new region
#            if self.parent is not None:
#                self.parent.stage_controller.linear_move(*r, block=True)
#
#            tm.center_my = center_my
#            tm.center_mx = center_mx
#            tm.map_holes()
#
#        sm.interpolate_noncorrected()
#
#        for s in sm.sample_holes:
#            if s.interpolated:
#                cx, cy = s.x_cor, s.y_cor
#    #            if abs(cx) > 1e-6 or abs(cy) > 1e-6:
#
#                cx, cy = sm.map_to_uncalibration((cx, cy), cpos, rot)
#                cx, cy = tm.map_screen(cx, cy)
#
#    #                print 'draw ind for {} {},{}'.format(s.id, cx, cy)
#    #                cy = 250
#                tm._draw_indicator(tm.image.get_frame(0), (cx, cy), color=(255, 0, 0))
#
# #        center_mx = 3.596
# #        center_my = -13.321
# #        cpos = -2.066, -0.695
# #        rot = 358.099
#    def close_images(self):
#        self.hole_detector.close_images()
#
    def traits_view(self):
        v = View('test')
        return v

    def configure_view(self):

        v = View(
                 Item('detector', show_label=False,
                      style='custom'
                      ),
                 buttons=['OK', 'Cancel'],
                 title='Configure Hole Detector',
                 resizable=True,
                 width=400
                )

        return v
#
#    def get_new_frame(self, path=None):
# #        if self._debug:
# #            if path is None:
# #                src = '/Users/Ross/Downloads/Archive/puck_screen_shot3.tiff'
# #                src = '/Users/ross/Desktop/tray_screen_shot3.tiff'
# #                src = '/Users/ross/Sandbox/tray_screen_shot3.596--13.321-an2.tiff'
# #
# ##                src = self._debug_path
# #                src = '/Users/ross/Sandbox/pos_err/pos_err_53001.jpg'
# #                src = '/Users/ross/Sandbox/pos_err/pos_err_3_0-002.jpg'
# #            else:
# #                src = path
# #
# #        else:
#        src = self.video.get_frame()
#
#        return src
#
#    @on_trait_change('laser_manager:zoom')
#    def update_zoom(self, new):
#
#        v = self._calc_pxpermm_by_zoom(new)
#        self.hole_detector.pxpermm = v
#        self.brightness_detector.pxpermm = v
#
#    def _calc_pxpermm_by_zoom(self, z):
#        from numpy import polyval
#        c = map(float, self.parent._camera_xcoefficients.split(','))
#        pxpercm = polyval(c, z)
#        return pxpercm / 10.0
#
#    def _load_detector(self, name, klass):
# #        hd = CO2HoleDetector()
# #        hd = klass()
#        p = path.join(paths.hidden_dir, name)
#        if path.isfile(p):
#            with open(p, 'rb') as f:
#                try:
#                    hd = pickle.load(f)
#                    if not isinstance(hd, klass):
#                        hd = klass()
#
#                except Exception, e:
#                    print e
#        else:
#            hd = klass()
#
#        hd.parent = self
#        if self.laser_manager is not None:
#            z = self.laser_manager.zoom
#            hd.pxpermm = self._calc_pxpermm_by_zoom(z)
#
# #        hd._debug = self._debug
#        hd.name = name
#        return hd
#
#    def _hole_detector_default(self):
#        return self.load_hole_detector()
#
#    def _brightness_detector_default(self):
#        return self.load_brightness_detector()
#
#    def _spawn_thread(self, func, *args, **kw):
#
#        from threading import Thread
#        t = Thread(target=func, args=args, kwargs=kw)
#        t.start()
#    def _video_default(self):
#        if self.parent is None:
#            v = Video()
#            v.open()
#        else:
#            v = self.parent.video
#
#        return v
#
#    def _test_fired(self):
# #        if not self.testing:
# #            self.hole_detector._debug = self._debug
# #            self.show_image()
# #        do_later(self.hole_detector.target_image.edit_traits)
# #            self.testing = True
# #            self.brightness_detector.collect_baseline_intensity()
# #            self.get_intensity()
# #            self._spawn_thread(self.map_holes)
# #            self._zoom_calibration()
#        self._spawn_thread(self.locate_target,
#                           0, 0, 1
#                           )
#
# #            self._spawn_thread(self.learn)
# #            self.learn()
# #        else:
# #            self.testing = False
#
# #
# #    def _test_view(self):
# #        v = View(
# #                 Item('hole_detector', show_label=False, style='custom'))
# #        return v

if __name__ == '__main__':

    from src.helpers.logger_setup import logging_setup
    logging_setup('machine_vision')
    from globals import globalv
    globalv._test = True

    m = MachineVisionManager(
#                             _debug=True,
                             )
#    m.locate_target(0, 0, 3)
    m.configure_traits()  # view='_test_view')
#    m.configure_traits(view='configure_view')

#    time_comp()
#============= EOF =====================================
#    def close_image(self):
#        if self.ui is not None:
#            do_later(self.ui.dispose)
#        self.ui = None
#
#    def show_image(self, reopen_image=False):
#        self.info('show image')
#        if reopen_image:
#            if self.ui is not None:
#                self.close_image()
#            do_after(50, self.edit_traits, view='image_view')
#        elif self.ui is None:
#            do_after(50, self.edit_traits, view='image_view')
# #        else:
# #            self.ui.control.Raise()
#        if self._debug:
#            do_after(50, self.edit_traits, view='working_image_view')


#    def working_image_view(self):
#
#        imgrp = Item('working_image', show_label=False, editor=ImageEditor(),
#                      width=self.image_width,
#                      height=self.image_height
#                      )
#        v = View(imgrp,
#                 handler=ImageHandler,
#                 x=0.6,
#                 y=35,
#                 width=680,
#                 height=self.image_height + 100,)
#        return v
#
#    def image_view(self):
#        v = View(
#                 HGroup(
#                        Item('segmentation_style', show_label=False),
# #                        Item('threshold', format_str='%03i',
#                             #style='readonly'
# #                             ),
#                        #spring,
#                        Item('nominal_position', label='Nom. Pos.',
#                             style='readonly'),
#
#                        Item('corrected_position', label='Cor. Pos.',
#                             style='readonly')
#                        ),
#                 Item('image', show_label=False, editor=ImageEditor(),
#                      width=self.image_width,
#                      height=self.image_height
#                      ),
#                 title=self.title,
#                 handler=ImageHandler,
#                 x=35,
#                 y=35,
#                 width=680,
#                 height=self.image_height + 100,
#                 resizable=True,
#                 id='pychron.machine_vision.image_view'
#                 )
#        return v

#    def load_source(self, path=None):
#        im = self.image
#        src = self.get_new_frame(path=path)
#        im.load(src)
#        return im.source_frame
#    def _image_default(self):
#        return Image(width=self.image_width,
#                     height=self.image_height)
#
#    def _working_image_default(self):
#        return Image(width=self.image_width,
#                     height=self.image_height)
#        #use map holes to move to multiple regions and
#        #determine corrected position
#        self.map_holes()
#
#        sm = self.parent._stage_map
#        #now stage map has corrected positions
#
#        #use stage map to get corrected center and corrected right
#        cx, cy = sm.get_corrected_center()
#        rx, ry = sm.get_corrected_right()

#        return cx, cy, rx, ry
