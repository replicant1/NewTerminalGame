"""The maze: a grid of squares, each one corridor or wall.

The model, not the generator. A `Maze` is an immutable fact — 19 squares
across and 29 deep (MAZE-1), each one corridor or wall (MAZE-2) — and it can
answer the questions the rest of the game wants to ask of it: is this square
corridor, which of the four sides can I go on to from here, which squares are
corridor at all.

**There is no screen geometry in here** (architecture caution C5). A square is
a square. That two columns of the terminal are spent drawing one of them, and
that an actor glyph is three columns wide, is Presentation's business and is
not represented anywhere in this file. Keeping it out is what lets MAZE-5 and
MAZE-6 be checked by walking the grid rather than by parsing a picture.

Coordinates are `(x, y)` with `x` the column, counted from 0 at the left edge,
and `y` the row, counted from 0 at the top. So `(0, 0)` is the top-left
square, which is always wall, because a solid wall runs right around the
outside (MAZE-3).
"""

from __future__ import annotations

from typing import Iterable, Iterator, List, Sequence, Tuple

#: The grid the specification asks for: 19 squares across, 29 deep (MAZE-1).
#: These are squares of the maze, not columns and rows of a terminal.
WIDTH = 19
HEIGHT = 29

WALL = "wall"
CORRIDOR = "corridor"


class Direction:
    """One of the four sides of a square.

    Corridors run only north-south and east-west (MAZE-2), so these four are
    the whole of the maze's geometry. `dx` and `dy` are in squares.
    """

    __slots__ = ("name", "dx", "dy")

    def __init__(self, name, dx, dy):
        self.name = name
        self.dx = dx
        self.dy = dy

    def from_square(self, x, y):
        """The square one step this way from `(x, y)`."""
        return (x + self.dx, y + self.dy)

    def opposite(self):
        return _OPPOSITES[self.name]

    def __repr__(self):
        return "Direction({0!r})".format(self.name)


NORTH = Direction("north", 0, -1)
SOUTH = Direction("south", 0, 1)
EAST = Direction("east", 1, 0)
WEST = Direction("west", -1, 0)

#: North, south, east, west — in a fixed order, so that anything built on top
#: of a neighbour query is reproducible rather than dependent on set ordering.
DIRECTIONS = (NORTH, SOUTH, EAST, WEST)

_OPPOSITES = {
    "north": SOUTH,
    "south": NORTH,
    "east": WEST,
    "west": EAST,
}


class Maze:
    """A finished maze. Immutable once built.

    Built from rows of squares — one sequence per row, each entry `WALL` or
    `CORRIDOR`. The generator in `maze_generator` is the normal way to get
    one; tests build small ones by hand, which is why this constructor does
    not insist on 19 x 29.
    """

    def __init__(self, rows):
        grid = tuple(tuple(row) for row in rows)
        if not grid or not grid[0]:
            raise ValueError("a maze needs at least one square")
        row_widths = set(len(row) for row in grid)
        if len(row_widths) != 1:
            raise ValueError(
                "every row of a maze must be the same width; got widths {0}"
                .format(sorted(row_widths)))
        for row in grid:
            for square in row:
                if square not in (WALL, CORRIDOR):
                    raise ValueError(
                        "a square is either {0!r} or {1!r}; got {2!r}"
                        .format(WALL, CORRIDOR, square))
        self._grid = grid
        self.height = len(grid)
        self.width = len(grid[0])

    # -- asking about one square ------------------------------------------

    def contains(self, x, y):
        """Is `(x, y)` a square of this maze at all?"""
        return 0 <= x < self.width and 0 <= y < self.height

    def square_at(self, x, y):
        """`CORRIDOR` or `WALL`.

        Anything off the grid is `WALL`: the world outside the maze is solid,
        which is the same thing MAZE-3 says about the border ring, and it
        means callers walking a square off the edge get a sensible answer
        rather than an exception.
        """
        if not self.contains(x, y):
            return WALL
        return self._grid[y][x]

    def is_corridor(self, x, y):
        return self.square_at(x, y) == CORRIDOR

    def is_wall(self, x, y):
        return self.square_at(x, y) == WALL

    # -- asking about the four sides --------------------------------------

    def neighbours(self, x, y):
        """The four squares adjacent to `(x, y)`, as `(direction, x, y)`.

        All four, whether or not they are on the grid and whether or not they
        are corridor. Callers that want only the ways on want
        `open_neighbours`.
        """
        return [(direction,) + direction.from_square(x, y)
                for direction in DIRECTIONS]

    def open_neighbours(self, x, y):
        """The adjacent squares that are corridor — the ways on from here.

        MAZE-5 says there are always at least two of these from any corridor
        square, which is exactly what makes this the query to count.
        """
        return [(direction, nx, ny)
                for direction, nx, ny in self.neighbours(x, y)
                if self.is_corridor(nx, ny)]

    def ways_on(self, x, y):
        """How many ways on there are from `(x, y)`. MAZE-5 counts these."""
        return len(self.open_neighbours(x, y))

    # -- asking about the whole grid --------------------------------------

    def squares(self):
        """Every coordinate on the grid, row by row, left to right."""
        for y in range(self.height):
            for x in range(self.width):
                yield (x, y)

    def corridor_squares(self):
        """Every corridor square, in reading order. MAZE-6 walks these."""
        return [(x, y) for (x, y) in self.squares() if self.is_corridor(x, y)]

    def rows(self):
        """The grid, row by row, as tuples of `WALL` / `CORRIDOR`."""
        return self._grid

    def reachable_from(self, x, y):
        """Every corridor square that can be walked to from `(x, y)`.

        A breadth-first walk along corridors only, north-south and east-west
        only. `set()` if `(x, y)` is not corridor. MAZE-6 is the statement
        that this set is the whole of `corridor_squares()` for any corridor
        square you start from.
        """
        if not self.is_corridor(x, y):
            return set()
        seen = set([(x, y)])
        frontier = [(x, y)]
        while frontier:
            next_frontier = []
            for (cx, cy) in frontier:
                for _, nx, ny in self.open_neighbours(cx, cy):
                    if (nx, ny) not in seen:
                        seen.add((nx, ny))
                        next_frontier.append((nx, ny))
            frontier = next_frontier
        return seen

    # -- comparing and reading ---------------------------------------------

    def __eq__(self, other):
        if not isinstance(other, Maze):
            return NotImplemented
        return self._grid == other._grid

    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __hash__(self):
        return hash(self._grid)

    def __repr__(self):
        return "Maze({0} x {1}, {2} corridor squares)".format(
            self.width, self.height, len(self.corridor_squares()))

    def as_text(self, wall="#", corridor=" "):
        """The grid as lines of text.

        For a person reading a failure, and for tests that want to build a
        known maze and compare. **Not** how the game is drawn — that is
        Presentation's job and it uses neither of these characters.
        """
        return "\n".join(
            "".join(wall if square == WALL else corridor for square in row)
            for row in self._grid)

    @classmethod
    def from_text(cls, text, wall="#"):
        """Build a maze from the same lines `as_text` produces.

        Anything that is not the wall character is corridor. Blank lines at
        either end are ignored so a test can use a triple-quoted string.
        """
        lines = [line for line in text.strip("\n").splitlines()]
        rows = [[WALL if character == wall else CORRIDOR for character in line]
                for line in lines]
        return cls(rows)


def solid(width=WIDTH, height=HEIGHT):
    """A maze of nothing but wall, `width` by `height`.

    Where the generator starts: everything solid, and the carve opens squares
    out of it. The border ring of MAZE-3 is then simply the squares the carve
    never touches.
    """
    return [[WALL for _ in range(width)] for _ in range(height)]
