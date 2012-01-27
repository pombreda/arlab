'''
Copyright 2011 Jake Ross

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

   http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''
#=============enthought library imports=======================
from traits.api import  Any, Bool, Float, List, Int
#=============standard library imports ========================
from threading import Thread, Lock

#=============local library imports ===========================
from ctypes_opencv import cvCreateCameraCapture, cvQueryFrame, cvWriteFrame
#    cvIplImageAsBitmap, \
#    cvConvertImage, cvCloneImage, \
#    cvResize, cvWriteFrame, \
#    CV_CVTIMG_SWAP_RB

from image_helper import clone, save_image, new_video_writer
from image_helper import crop as icrop
import time
from src.image.image import Image
from src.image.image_helper import load_image


class Video(Image):
    '''
    '''
    cap = Any
    track_mouse = Bool
    mouse_x = Float
    mouse_y = Float
#    snapshot = Button
#    data_directory = Any

    users = List

    _recording = Bool(False)
    _lock = None

    def open(self, user=None):
        '''

        '''
        self._lock = Lock()
        if self.cap is None:
            try:
                self.cap = cvCreateCameraCapture(0)
                self.width = 640
                self.height = 480

            except:
                self.cap = None

        if not user in self.users:
            self.users.append(user)

    def shutdown(self):
        self.users = []
        del(self.cap)

    def close(self, user=None, force=False):
        '''
  
        '''
        if user in self.users:
            i = self.users.index(user)
            self.users.pop(i)
            if not self.users:
                del(self.cap)

    def _get_frame(self):
        if self.cap is not None:
            with self._lock:
                src = '/Users/ross/Desktop/tray_screen_shot3.tiff'
                return load_image(src)

                return  cvQueryFrame(self.cap)
    def start_recording(self, path):
        fps = 8.0
        def __record():
            if self.cap is not None:
                self._recording = True
                writer = new_video_writer(path, fps=fps)
#                for i in range(100):

#                start = time.time()
#                while time.time() - start < 5:
                while self._recording:
                    st = time.time()
                    cvWriteFrame(writer, self.get_frame(swap_rb=False))#swap_rb=False))
                    d = 1 / float(fps) - (time.time() - st)
                    if d >= 0:
                        time.sleep(d)

        t = Thread(target=__record)
        t.start()

    def stop_recording(self):
        '''
        '''
        self._recording = False

    def record_frame(self, path, crop=None, **kw):
        '''
        '''
        src = self.get_frame(**kw)
        if src is not None:

            if crop:
                icrop(*((src,) + crop))
            save_image(src, path)

        return clone(src)

#=================== EOF =================================================
