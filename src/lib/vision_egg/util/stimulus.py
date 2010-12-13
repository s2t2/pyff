__copyright__ = """ Copyright (c) 2010 Torsten Schmits

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, see <http://www.gnu.org/licenses/>.

"""

from time import sleep
import datetime, collections, logging, itertools

import pygame, VisionEgg

from lib.vision_egg.util.frame_counter import FrameCounter

def time():
    """ Return microsecond-accurate time since last midnight. 
    Workaround for time() having only 10ms accuracy when VE is running.
    """
    n = datetime.datetime.now()
    return 60. * (60 * n.hour + n.minute) + n.second + n.microsecond / 1000000.

class StimulusPainter(object):
    """ Painter for a series of stimuli. """
    def __init__(self, prepare, wait, view, flag, wait_style_fixed=False,
                 print_frames=False, suspendable=True, pre_stimulus=None,
                 frame_transition=False):
        self._prepare_func = prepare
        self._wait_times = itertools.cycle(wait)
        self._view = view
        self._flag = flag
        self._wait_style_fixed = wait_style_fixed
        self._print_frames = print_frames
        self._suspendable = suspendable
        self._pre_stimulus = pre_stimulus
        self._frame_transition = frame_transition
        self._wait_time = 0.1
        self._logger = logging.getLogger('StimulusPainter')
        self._frame_counter = FrameCounter(self._flag)
        self._suspended_time = 0.
        self._wait = self._frame_wait if frame_transition else self._time_wait

    def run(self):
        if self._print_frames:
            self._frame_counter.start()
        if self._prepare():
            self._last_start = time()
            self._frame_counter.lock()
            self._present()
            while self._prepare():
                self._wait()
                self._present()
            if self._flag:
                self._wait()
        if self._print_frames:
            self._logger.debug('Frames rendered during last sequence: %d' %
                               self._frame_counter.frame)

    def _frame_wait(self):
        next_interval = self._next_wait_time
        while self._frame_counter.last_interval < next_interval:
            sleep(0.01)
        if self._print_frames:
            self._logger.debug('Frames after waiting: %d' %
                               self._frame_counter.last_interval)

    def _time_wait(self):
        next_wait_time = self._next_wait_time + self._suspended_time
        self._suspended_time = 0.
        wait_time = self._last_start - time() + next_wait_time
        try:
            if wait_time > 0:
                sleep(wait_time)
        except IOError, e:
            self._logger.error('Encountered "%s" with wait_time of %s'
                               % (e, wait_time))
        if self._wait_style_fixed:
            self._last_start += next_wait_time
        else:
            self._last_start = time()
        if self._print_frames:
            self._logger.debug('Frames after waiting: %d' %
                               self._frame_counter.last_interval)

    def _prepare(self):
        if self._flag:
            if self._suspendable and self._flag.suspended:
                suspend_start = time()
                self._flag.wait()
                self._suspended_time = time() - suspend_start
            return self._do_prepare()

    def _present(self):
        if self._print_frames:
            self._logger.debug('Frames before stimulus change: %d' %
                               self._frame_counter.last_interval)
            self._frame_counter.lock()
        if self._pre_stimulus is not None:
            self._pre_stimulus()
        self._view.update()

    @property
    def _next_wait_time(self):
        return self._wait_times.next()

class StimulusSequence(StimulusPainter):
    def _do_prepare(self):
        return self._prepare_func()

class StimulusIterator(StimulusPainter):
    """ Painter using an iterator. """
    def _do_prepare(self):
        try:
            self._prepare_func.next()
            return True
        except StopIteration:
            return False

class StimulusSequenceFactory(object):
    """ This class instantiates StimulusPainter in create().
    Depending on whether the supplied prepare object is a function or a
    generator, StimulusSequence or StimulusIterator are used,
    respectively.
    """
    def __init__(self, view, flag, print_frames=False, vsync_times=False,
                 frame_transition=False):
        self._view = view
        self._flag = flag
        self._print_frames = print_frames
        self._vsync_times = vsync_times
        self._frame_transition = frame_transition
        self._refresh_rate = VisionEgg.config.VISIONEGG_MONITOR_REFRESH_HZ
        self._frame_length = 1. / self._refresh_rate
        self._logger = logging.getLogger('StimulusSequenceFactory')

    def create(self, prepare, times, wait_style_fixed, suspendable=True,
               pre_stimulus=None):
        """ Create a StimulusPainter using the preparation object
        prepare, with given presentation times and wait style.
        If suspendable is True, the sequence halts when on_pause is
        pressed.
        Global parameters from pyff are used as given in __init__.
        """
        if not isinstance(times, collections.Sequence):
            times = [times]
        times = self._adapt_times(times)
        typ = StimulusIterator if hasattr(prepare, '__iter__') else \
               StimulusSequence
        return typ(prepare, times, self._view, self._flag,
                   wait_style_fixed=wait_style_fixed,
                   print_frames=self._print_frames, suspendable=suspendable,
                   pre_stimulus=pre_stimulus,
                   frame_transition=self._frame_transition)

    def _adapt_times(self, times):
        frames = [round(float(time) * self._refresh_rate) for time in times]
        new_times = [round(t * self._frame_length, 6) for t in frames]
        if self._frame_transition:
            text = ('Adapted stimulus times %s to %s frames (%s)' %
                    (times, frames, new_times))
            times = frames
            self._logger.debug(text)
        elif self._vsync_times:
            text = 'Adapted stimulus times %s to %s' % (times, new_times)
            times = new_times
            self._logger.debug(text)
        return times
