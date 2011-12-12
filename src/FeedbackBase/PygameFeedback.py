# PygameFeedback.py -
# Copyright (C) 2009  Bastian Venthur
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

"""This module contains the PygameFeedback baseclass."""

import os

import pygame

from MainloopFeedback import MainloopFeedback


class PygameFeedback(MainloopFeedback):
    """Baseclass for Pygame based Feedbacks.
    
    This class is derived from MainloopFeedback and brings some common 
    functinality shared by most Feedbacks using Pygame.

    Upon start it initializes pygame and calls initialize_graphics which can be
    overwritten by derived classes.

    It also takes care of shutting down pygame automatically upon stop, quit or 
    crash of the feedback.

    After initialization of the feedback, it has some object variables which 
    influence the Feedback's behaviour:
    
    * FPS: (frames per second) influencees how much the Feedback advances in \
            time during a tick call.
    * geometry: List of integers holding the initial position and size of the pygame \
            window.
    * pygame_display_flags: flags specifying display pygame display options
    * videodriver: videodriver to be used
    * fullscreen: Boolean
    * centerWindow: Boolean. Centers the pygame window on the screen
    * caption: String holding the initial value of the window caption.
    * elapsed: Fload holding the elapsed second since the last tick
    * backgroundColor: List of three integers holding the initial background \
            colour
    * keypressed: Boolean holding if a key was pressed
    * lastkey: Last key
    """

    def init(self):
        """Set some PygameFeedback variables to default values."""
        self.FPS = 30
        self.geometry = [0,0,800,600]  # screen position and size
        self.fullscreen = False
        self.centerScreen = False
        self.caption = "PygameFeedback"
        self.pygame_display_flags = pygame.DOUBLEBUF
        self.elapsed = 0
        self.backgroundColor = [0, 0, 0]
        # For keys
        self.keypressed = False
        self.lastkey = None


    def pre_mainloop(self):
        """Initialize pygame and graphics."""
        self.init_pygame()
        self.init_graphics()


    def post_mainloop(self):
        """Quit pygame."""
        self.quit_pygame()


    def tick(self):
        """Process pygame events and advance time for 1/FPS seconds."""
        self.process_pygame_events()
        self.elapsed = self.clock.tick(self.FPS)

        

    def pause_tick(self):
        pass


    def play_tick(self):
        pass


    def init_pygame(self):
        """
        Set up pygame and the screen and the clock.
        """
        os.environ['SDL_VIDEO_WINDOW_POS'] = "%d,%d" % (self.geometry[0],
                                                        self.geometry[1])
        # set directx driver only on windows systems
        if os.name == 'nt':
            os.environ['SDL_VIDEODRIVER'] = 'directx'
        if self.centerScreen:
            os.environ['SDL_VIDEO_CENTERED'] = '1'

        pygame.init()
        pygame.display.set_caption(self.caption)
        if self.fullscreen:
            self.screen = pygame.display.set_mode((self.geometry[2],
                                                   self.geometry[3]),
                                                   pygame.FULLSCREEN|self.pygame_display_flags)
        else:
            self.screen = pygame.display.set_mode((self.geometry[2],
                                                   self.geometry[3]),
                                                   pygame.RESIZABLE|self.pygame_display_flags)
        self.clock = pygame.time.Clock()

    def quit_pygame(self):
        pygame.quit()


    def init_graphics(self):
        """
        Called after init_pygame.

        Derived Classes overwrite this method.
        """
        pass


    def process_pygame_events(self):
        """
        Process the the pygame event queue and react on VIDEORESIZE.
        """
        for event in pygame.event.get():
            self.process_pygame_event(event)

            
    def process_pygame_event(self, event):
        """Process a signle pygame event."""
        if event.type == pygame.VIDEORESIZE:
            e = max(event.w, int(round(event.h * 0.9)))
            self.screen = pygame.display.set_mode((e, event.h), pygame.RESIZABLE|self.display_opts)
            self.resized = True
            self.geometry[2:] = [self.screen.get_width(), self.screen.get_height()]
            self.init_graphics()
        elif event.type == pygame.QUIT:
            self.on_stop()
        elif event.type == pygame.KEYDOWN:
            self.keypressed = True
            self.lastkey = event.key
            self.lastkey_unicode = event.unicode
                
    
    def wait_for_pygame_event(self):
        """Wait until a pygame event orcurs and process it."""
        event = pygame.event.wait()
        self.process_pygame_event(event)

