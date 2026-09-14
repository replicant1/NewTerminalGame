"""Which blue double-line glyph a wall square is drawn as (SCRN-3).

> **SCRN-3** The walls are drawn as blue double lines that join up neatly with
> their neighbours into corners, tees and crossings; a wall square with no wall
> next to it is drawn as a single blue block.

A pure mapping from a wall square's four neighbours to one character. The
Domain answers only "is the square on that side a wall"; the table below is
Presentation's and stays here (architecture caution C5, and the WI-5a row of
the implementation plan).

## The table was measured, not read off by eye

The specification's picture is 29 rows of 37 columns — square `x` is drawn at
column `2x`, and the odd columns are the joins between neighbouring squares.
That is 287 wall squares of worked example, and every neighbour pattern that
appears in it is drawn with **exactly one** glyph. Fifteen of the sixteen
patterns occur; the only one that does not is the four-way crossing, and
SCRN-3 names "crossings" in its own words, so `BOX DRAWINGS DOUBLE VERTICAL
AND HORIZONTAL` is the only candidate. The derivation is written up in
`docs/findings/WI-5a-glyph-table-from-the-picture.md`.

## Off the grid is *not* wall, and this is the trap

`Maze.square_at` answers `WALL` for any square off the grid. That is right for
an actor walking at the edge — MAZE-3 says nothing leaves the maze — and it is
**wrong here**. A wall square in the border ring has no neighbour beyond the
edge to join up with, so the top-left corner of the maze must be drawn `╔` and
not `╬`.

This is not a judgement call. Re-deriving the table from the picture under the
other convention makes five of the patterns ambiguous — one of them drawn
seven different ways — where the convention below leaves none ambiguous at
all. The picture settles it.

## Why a single wall neighbour gives a straight and not a stub

The double-line box-drawing set has no half-line characters: there is no
"double line coming from the north and stopping". So a wall square whose only
wall neighbour is to the west is drawn `═`, with an east arm pointing at a
corridor square. The specification's picture does exactly this — `════ ▪` — so
it is the intended appearance and not a compromise. The rule is that every
wall neighbour has an arm pointing at it, using the fewest extra arms
available.
"""

from __future__ import annotations

from terminalgame.screen.port import Colour

#: SCRN-3 — the walls are blue. One colour for every wall square; only the
#: character changes with the neighbours.
WALL_COLOUR = Colour.WALL

# The glyphs, named rather than pasted, so that a reader of this file can tell
# `╠` from `╣` without counting pixels.
HORIZONTAL = "═"      # ═  BOX DRAWINGS DOUBLE HORIZONTAL
VERTICAL = "║"        # ║  BOX DRAWINGS DOUBLE VERTICAL
DOWN_AND_RIGHT = "╔"  # ╔  corner: south and east
DOWN_AND_LEFT = "╗"   # ╗  corner: south and west
UP_AND_RIGHT = "╚"    # ╚  corner: north and east
UP_AND_LEFT = "╝"     # ╝  corner: north and west
VERTICAL_AND_RIGHT = "╠"   # ╠  tee: north, south and east
VERTICAL_AND_LEFT = "╣"    # ╣  tee: north, south and west
DOWN_AND_HORIZONTAL = "╦"  # ╦  tee: south, east and west
UP_AND_HORIZONTAL = "╩"    # ╩  tee: north, east and west
CROSSING = "╬"        # ╬  all four
LONE_BLOCK = "■"      # ■  SCRN-3's "single blue block"

#: Every wall square is drawn as one of these and nothing else.
GLYPHS = (HORIZONTAL, VERTICAL, DOWN_AND_RIGHT, DOWN_AND_LEFT, UP_AND_RIGHT,
          UP_AND_LEFT, VERTICAL_AND_RIGHT, VERTICAL_AND_LEFT,
          DOWN_AND_HORIZONTAL, UP_AND_HORIZONTAL, CROSSING, LONE_BLOCK)

#: The mapping, keyed by `(north, south, east, west)` — each a bool saying
#: whether the square on that side is a wall square of this maze. Read the
#: keys as a picture: `(False, True, True, False)` is a wall with wall to the
#: south and to the east, so it is the corner that opens down and right.
BY_NEIGHBOURS = {
    #  N      S      E      W
    (False, False, False, False): LONE_BLOCK,

    # One neighbour: no half-lines exist, so the straight through that axis.
    (True,  False, False, False): VERTICAL,
    (False, True,  False, False): VERTICAL,
    (False, False, True,  False): HORIZONTAL,
    (False, False, False, True):  HORIZONTAL,

    # Two opposite: the straights proper.
    (True,  True,  False, False): VERTICAL,
    (False, False, True,  True):  HORIZONTAL,

    # Two adjacent: the corners.
    (True,  False, True,  False): UP_AND_RIGHT,
    (True,  False, False, True):  UP_AND_LEFT,
    (False, True,  True,  False): DOWN_AND_RIGHT,
    (False, True,  False, True):  DOWN_AND_LEFT,

    # Three: the tees.
    (True,  True,  True,  False): VERTICAL_AND_RIGHT,
    (True,  True,  False, True):  VERTICAL_AND_LEFT,
    (False, True,  True,  True):  DOWN_AND_HORIZONTAL,
    (True,  False, True,  True):  UP_AND_HORIZONTAL,

    # Four: the crossing.
    (True,  True,  True,  True):  CROSSING,
}


class NotAWallSquare(ValueError):
    """A wall glyph was asked for a square that is not wall.

    Refused rather than answered with something plausible: the question has no
    answer and a default would put a wall glyph on a corridor square where
    nothing would notice. Plan §11.8 — where an argument makes a requirement
    impossible, refuse and say which requirement.
    """

    def __init__(self, x, y):
        self.x = x
        self.y = y
        super().__init__(
            "the square at ({0}, {1}) is not a wall square, so SCRN-3 has "
            "nothing to say about how it is drawn".format(x, y))


def glyph_for_neighbours(north, south, east, west):
    """The glyph for a wall square with these four neighbours.

    Each argument says whether the square on that side **is a wall square of
    the maze**. A square beyond the edge of the grid is not one — see the
    module docstring; this is the distinction that draws the border ring as a
    rectangle rather than as a mesh of crossings.
    """
    return BY_NEIGHBOURS[(bool(north), bool(south), bool(east), bool(west))]


def wall_neighbours(maze, x, y):
    """Which of the four sides of `(x, y)` are wall squares of this maze.

    Returns `(north, south, east, west)`. **`maze.contains` first**: without
    it `square_at` would answer `WALL` for everything beyond the edge, which
    is the right answer to "can I walk there" and the wrong answer to "does my
    wall join up with it".
    """
    def is_wall_square(nx, ny):
        return maze.contains(nx, ny) and maze.is_wall(nx, ny)

    return (is_wall_square(x, y - 1),   # north: y counts down from the top
            is_wall_square(x, y + 1),   # south
            is_wall_square(x + 1, y),   # east
            is_wall_square(x - 1, y))   # west


def wall_glyph(maze, x, y):
    """How the wall square at `(x, y)` of this maze is drawn.

    Raises `NotAWallSquare` if it is not a wall square.
    """
    if not (maze.contains(x, y) and maze.is_wall(x, y)):
        raise NotAWallSquare(x, y)
    return glyph_for_neighbours(*wall_neighbours(maze, x, y))


def wall_glyphs(maze):
    """Every wall square of the maze and its glyph, in reading order.

    `[(x, y, glyph), …]`. What WI-5b's frame builder walks.
    """
    return [(x, y, glyph_for_neighbours(*wall_neighbours(maze, x, y)))
            for (x, y) in maze.squares()
            if maze.is_wall(x, y)]
