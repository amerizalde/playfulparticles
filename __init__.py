import threading
import math
import pygame

from pygame.locals import *

TARGET = (0, 0)
GAME_OVER = False
GRID = set()
GRID_LOCK = threading.Lock()
NUM_PARTICLES = 20

class Particle(threading.Thread):
    def __init__(self, (x, y), color=None):
        super(Particle, self).__init__()
        self.old_x = x
        self.old_y = y
        self.x = x
        self.y = y
        if color is None:
            self.color = (random.randint(60, 255),
                random.randint(60, 255),
                random.randint(60, 255))
        else:
            self.color = color

    def integrate(self):
        """ Verlet integration. any change in position also updates velocity."""
        velocity_x = self.x - self.old_x
        velocity_y = self.y - self.old_y
        self.old_x = self.x
        self.old_y = self.y
        self.x += velocity_x
        self.y += velocity_y

    def attract(self, (x, y)):
        """ swarming effect """
        dx = x - self.x
        dy = y - self.y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        self.x += dx / distance
        self.y += dy / distance

    def run(self):
        while True:
            if GAME_OVER:
                return
            self.attract(TARGET)
            self.integrate()
            GRID_LOCK.acquire()
            self.mark_position()
            GRID_LOCK.release()

    def mark_position(self):
        global GRID
        old_pos = set({'x': self.x, 'y': self.y})
        GRID = GRID - old_pos  # out with the old...
        pos = set({'x': self.x, 'y': self.y})
        GRID = GRID | pos  # ...in with the new!


class Game(object):
    SPACING = 20
    title = "Particles"
    cwd = os.getcwd()  # this is the folder the script is run from
    # change this to the folder your art and such is in
    assets = '../shared/kenney/'
    current_level = -1

    def __init__(self, width=640, height=480, fps=30, levels=None):
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
        self.font = pygame.font.Font(
        self.assets + 'Fonts (10 files)/kenpixel_future.ttf', 12)
        # an object containing useful info about the display
        self.info = pygame.display.Info()
        # END boilerplate

        self.particles = []

    def run(self):
        global NUM_PARTICLES
        spawnpoint = (self.info.current_w / 2, self.info.current_h / 2)
        for i in xrange(NUM_PARTICLES):
            # create the threads, and add to self.particles
            self.particles.append(Particle(spawnpoint))
            # start the particle code in its own thread,
            # after it is added to the list
            self.particles[-1].start()
        while True:
            # screen is already cleared in the call to .draw_grid()
            # self.display.blit(self.background, (0, 0))  # clear screen

            # EVENT LOGIC
            for event in pygame.event.get():
                self._event_manager(event)
            # GAME LOGIC
            # the threads are handling their own logic.

            # DRAW
            self.draw_grid()
            self.show_fps()
            pygame.display.flip()

    def show_fps(self):
        """ Display current FPS, and PLAYTIME. """
        milliseconds = self.clock.tick(self.fps)
        self.playtime += milliseconds / 1000.
        self.draw_text("FPS: {:1g}".format(self.clock.get_fps()),
            (10, self.height - 20))
        self.draw_text("PLAYTIME: {:1g} SECONDS".format(self.playtime),
            (10, self.height))

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
            pygame.quit()
            sys.exit()
        elif event.type == KEYDOWN:
            self._key_event(event)
        elif event.type == MOUSEBUTTONDOWN:
            self._mouse_event(event)

    def _key_event(self, event):
        """ Handle all key events. """
        global GAME_OVER
        if event.key == K_ESCAPE:
            GAME_OVER = True
            pygame.quit()
            sys.exit()

    def _mouse_event(self, event):
        """ Handle all mouse events. """
        pass

    def draw_grid(self):
        """ Draw the grid and then fill the appropriate cells. """
        global GRID, GRID_LOCK, CELLS_HIGH, CELLS_WIDE, BGCOLOR, GRID_LINES_COLOR
        self.display.fill(BGCOLOR)

        # draw a grid of lines covering the extent of the window
        map(
            lambda pos: pygame.draw.line(
                self.display,
                GRID_LINES_COLOR,
                (pos, 0),
                (pos, self.info.current_h)),
            range(0, self.info.current_w, CELL_SIZE))
        map(
            lambda pos: pygame.draw.line(
                self.display,
                GRID_LINES_COLOR,
                (0, pos),
                (self.info.current_w, pos)),
            range(0, self.info.current_h, CELL_SIZE))

        GRID_LOCK.acquire()
        # determine what color each cell should be this frame
        # and draw a rect representing that cell.
        for x in xrange(0, CELLS_WIDE):
            i_x = x
            for y in xrange(0, CELLS_HIGH):
                i_y = y
                # if None, dont draw anything and move on
                if GRID[i_x][i_y] is None:
                    continue
                # the inner cell color
                color = GRID[i_x][i_y]
                # the outer cell color
                darkerColor = (max(color[0] - 50, 0),
                    max(color[1] - 50, 0),
                    max(color[2] - 50, 0))
                # draw two rects, one of full CELL_SIZE but slightly darker
                # color to create a border effect...
                pygame.draw.rect(
                    self.display,
                    darkerColor,
                    (i_x * CELL_SIZE, i_y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
                # ...another of normal color but slightly smaller CELL_SIZE
                pygame.draw.rect(
                    self.display,
                    color,
                    (i_x * CELL_SIZE + 4, i_y * CELL_SIZE + 4,
                        CELL_SIZE - 8, CELL_SIZE - 8))

        GRID_LOCK.release()

    def setGridSquares(self, squares, color=(192, 192, 192)):
        """ Draw walls based on input string.
            [color] -- the wall color.
        """
        global GRID, GRID_LOCK, CELLS_HIGH, CELLS_WIDE
        squares = squares.split('\n')
        if squares[0] == '':
            del squares[0]
        if squares[-1] == '':
            del squares[-1]

        GRID_LOCK.acquire()
        for y in xrange(min(len(squares), CELLS_HIGH)):
            i_y = y
            for x in xrange(min(len(squares[i_y]), CELLS_WIDE)):
                i_x = x
                if squares[i_y][i_x] == " ":
                    GRID[i_x][i_y] = None
                elif squares[i_y][i_x] == ".":
                    pass
                else:
                    GRID[i_x][i_y] = color
        GRID_LOCK.release()

if __name__ == "__main__":
    level = ["""
    ...........................
    ...........................
    ...........................
    .H..H..EEE..L....L.....OO..
    .H..H..E....L....L....O..O.
    .HHHH..EE...L....L....O..O.
    .H..H..E....L....L....O..O.
    .H..H..EEE..LLL..LLL...OO..
    ...........................
    .W.....W...OO...RRR..MM.MM.
    .W.....W..O..O..R.R..M.M.M.
    .W..W..W..O..O..RR...M.M.M.
    .W..W..W..O..O..R.R..M...M.
    ..WW.WW....OO...R.R..M...M.
    ...........................
    ...........................
    """,]
    Game(800, 600, levels=level).run()