import threading
import math
import random
import sys
import pygame

from pygame.locals import *

# SHARED DATA
BGCOLOR =           color.THECOLORS["black"]
TARGET =            (0, 0)
GAME_OVER =         False
NUM_PARTICLES =     30
DAMPING =           .2


class Particle(threading.Thread):
    """ Particle object based on threading.

        @args:
            x := x position
            y := y position

        @kwargs
            color   := (R, G, B)
            life    := how long this particle will run.
    """
    def __init__(self, (x, y), **kwargs):
        super(Particle, self).__init__()
        self.old_x = x
        self.old_y = y
        self.x = x
        self.y = y
        self.color = kwargs.get('color', (
            random.randint(60, 255),
            random.randint(60, 255),
            255))
        self.life = kwargs.get('life', 200)

    def integrate(self):
        """ Verlet integration. any change in position also updates velocity. """
        global DAMPING
        velocity_x = (self.x - self.old_x) * DAMPING
        velocity_y = (self.y - self.old_y) * DAMPING
        self.old_x = self.x
        self.old_y = self.y
        self.x += velocity_x
        self.y += velocity_y

    def attract(self, (x, y)):
        """ swarming effect """
        dx = x - self.x
        dy = y - self.y
        distance = math.sqrt((dx * dx) + (dy * dy))
        self.x += dx / distance
        self.y += dy / distance

    def move(self, (x, y)):
        """ simple move method. """
        self.x += x;
        self.y += y;

    def gravity_pull(self, flr):
        """ simple gravity """
        if self.y < flr:
            velocity = self.getVelocity()
            self.old_y = flr
            self.y = self.old_y - velocity.y * 0.3

    def run(self):
        global GAME_OVER
        while True:
            if GAME_OVER:
                return
            self.attract(TARGET)
            self.integrate()


class Game(object):
    title = "Particles"

    def __init__(self, width=640, height=480, fps=30, levels=None, assets=None, debug=False):
        # BEGIN boilerplate
        pygame.init()
        pygame.display.set_caption(self.title)
        self.width = width
        self.height = height
        self.display = pygame.display.set_mode((self.width, self.height),
            DOUBLEBUF)
        self.background = pygame.Surface(
            self.display.get_size()).convert_alpha()
        self.clock = pygame.time.Clock()
        self.fps = fps
        self.playtime = 0.0
        self.assets = assets
        self.font = None
        if self.assets:
            self.font = pygame.font.Font(
                self.assets + '/Fonts (10 files)/kenpixel_future.ttf', 12)
        # an object containing useful info about the display
        self.info = pygame.display.Info()
        self.debug = debug
        # END boilerplate

        self.particles = []

    def run(self):
        global NUM_PARTICLES, TARGET
        spawnpoint = (self.info.current_w / 2, self.info.current_h / 2)
        for i in xrange(NUM_PARTICLES):
            # create the threads, and add to self.particles
            self.particles.append(Particle(spawnpoint))
            # start the particle code in its own thread,
            # after it is added to the list
            self.particles[-1].start()
        while True:
            # screen is already cleared in the call to .draw_particles()
            # self.display.blit(self.background, (0, 0))  # clear screen

            # EVENT LOGIC
            for event in pygame.event.get():
                self._event_manager(event)
            # GAME LOGIC
            # the threads are handling their own logic.
            # DRAW
            self.draw_particles()
            if self.assets:
                self.show_fps()
            self.draw_text(str(TARGET), (10, 20))
            pygame.display.flip()

    def show_fps(self):
        """ Display current FPS, and PLAYTIME. """
        milliseconds = self.clock.tick(self.fps)
        self.playtime += milliseconds / 1000.
        self.draw_text("FPS: {:1g}".format(self.clock.get_fps()),
            (10, self.height - 20))
        self.draw_text("PLAYTIME: {:1g} SECONDS".format(self.playtime),
            (10, self.height))

    def quit(self):
        pygame.quit()
        sys.exit()

    def draw_text(self, text, pos):
        """ Helper method for drawing text on the screen
            <text> -- the string to show on screen.
            <pos> -- where to place the text, based on the top-left corner. """
        fw, fh = self.font.size(text)
        surface = self.font.render(text, True, (0, 255, 0))
        self.display.blit(surface, ((pos[0]) / 2, (pos[1] - fh)))

    def _event_manager(self, event):
        """ My attempt to simplify event handling. """
        global GAME_OVER
        if event.type == QUIT:
            GAME_OVER = True
            self.quit()
        elif event.type == KEYDOWN:
            self._key_event(event)
        elif event.type == MOUSEBUTTONDOWN:
            self._mouse_event(event)
        elif event.type == MOUSEMOTION:
            self._motion_event(event)

    def _key_event(self, event):
        """ Handle all key events. """
        global GAME_OVER
        if event.key == K_ESCAPE:
            GAME_OVER = True
            self.quit()

    def _mouse_event(self, event):
        """ Handle all mouse events. """
        pass

    def _motion_event(self, event):
        """ Handle all mouse motion events. """
        global TARGET
        TARGET = event.pos

    def draw_particles(self):
        """ Draw the grid and then fill the appropriate cells. """
        global BGCOLOR, GAME_OVER
        self.display.fill(BGCOLOR)

        for particle in self.particles:
            try:
                # draw a square of darker color, normal size
                pygame.draw.aaline(
                    self.display,
                    particle.color,
                    (particle.old_x, particle.old_y),
                    (particle.x, particle.y))
            except ValueError as e:
                print e
                for (k, v) in particle.__dict__.iteritems():
                    print "{}: {}".format(k, v)
                GAME_OVER = True
                self.quit()

if __name__ == "__main__":
    Game(800, 600, fps=20, assets="C:/backup/_scripts/usable_art/kenney").run()
