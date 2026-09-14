# -*- coding: utf-8 -*-
"""A whole picture from a game state — SCRN-1, SCRN-2, SCRN-4, SCRN-5, END-4.

40 columns by 30 rows: 29 rows of maze, then the status row (SCRN-1). Every
cell is a character (SCRN-2) and a named colour; nothing here knows how a
terminal produces either.

## The geometry, measured rather than assumed

A maze square is **two terminal columns wide**, and neighbouring squares share
the column between them — so 19 squares occupy `2 x 19 - 1 = 37` columns, and
**square `x` is drawn at column `2x`**, the even columns 0 to 36. The three
columns left over, 37 to 39, are the blank right margin MAZE-1 asks for.

The odd column `2x + 1` is the **joiner** between square `x` and square
`x + 1`. Its rule was derived from the specification's own picture, over all
518 joiner positions in it:

* **both squares are wall** -> `═`, the horizontal double line, 122 times with
  no exceptions;
* **otherwise** -> blank, 396 times, with exactly four exceptions — and all
  four are the side columns of the two actor glyphs, which are drawn last and
  over everything.

Two adjacent wall squares always join horizontally, because each is the
other's east or west wall neighbour, so each glyph already has an arm pointing
at the other. That is WI-5a's joining-up property, and it is why the joiner
rule needs no case analysis.

## The draw order is fixed, and the ghost goes last

Walls, then the joiners, then dots, then the **player**, then the **ghost**
(END-4). Drawing the ghost after the player means that when they are on the
same square the picture shows the ghost — which is what a loss looks like, and
the reason END-4 exists.

An actor glyph is three columns wide, centred on its square, so it covers the
joiner columns on either side and can erase a `═` that was there. That is not
a defect: the actor is closer to the viewer than the wall behind it, and the
whole frame is rebuilt next pass anyway.

**The actor can never run off an edge.** MAZE-3's border ring means an actor
only ever stands on squares 1 to 17 of 0 to 18, so the glyph spans columns 1
to 35 of 0 to 36. `Frame.put` therefore keeps raising on an out-of-range cell
and nothing here clips — ruled in M0 and measured again on the
specification's picture, where the ghost at square 1 spans columns 1 to 3 and
leaves the border wall in column 0 untouched.

## The whole frame, every pass

`compose` builds a new `Frame` every time it is called and fills every cell.
There is no dirty-cell path and nowhere for one to live (caution C9): a
three-column actor glyph overwrites part of its neighbours' squares, so
repainting only what moved would leave debris.

## Row 29 is a seam, not this module's row

The plan gives row 29 to WI-6 and rows 0 to 28 to WI-5b, deliberately, so the
two lanes own disjoint rows. **WI-6 has not landed yet**, so `compose` leaves
row 29 blank unless a caller hands it a status line. When WI-6 arrives it
supplies that string — including whatever it decides about the leading space,
which is its question — and nothing in this module needs to change.
"""

from __future__ import annotations

from terminalgame.presentation.wall_glyphs import (
    HORIZONTAL,
    WALL_COLOUR,
    joins_up_with,
    wall_glyph,
)
from terminalgame.screen.port import BLANK, Colour, Frame

#: The window the launcher creates, and the picture composed to fit it exactly.
WIDTH = 40
HEIGHT = 30

#: 29 rows of maze, then the status row (SCRN-1).
MAZE_ROWS = 29
STATUS_ROW = 29

#: Two columns to a square, sharing the column between neighbours: 2 x 19 - 1.
PICTURE_WIDTH = 37
#: What is left of the 40, and MAZE-1's "narrow blank margin down the right".
MARGIN_WIDTH = WIDTH - PICTURE_WIDTH          # 3

#: The join drawn between two horizontally adjacent wall squares.
JOINER = HORIZONTAL

#: SCRN-4 — "a small dim gold square, one to a corridor square".
DOT = "▪"                                 # ▪ BLACK SMALL SQUARE

#: SCRN-5 — distinguishable by **both** colour and outline. Three columns
#: each, centred on the actor's square, and taken from the specification's own
#: picture rather than invented.
PLAYER_GLYPH = "▐█▌"            # ▐█▌ half, full, half
GHOST_GLYPH = "▗█▖"             # ▗█▖ quadrant, full, quadrant

#: How wide an actor is drawn, and how far left of its square it starts.
ACTOR_WIDTH = 3


class StatusLineTooWide(ValueError):
    """A status line that will not fit the window.

    Refused rather than clipped: a status line wider than the window cannot be
    drawn, and SCRN-1 gives it exactly one row. Plan §11.8 — where an argument
    makes a requirement impossible, refuse and name the requirement.
    """

    def __init__(self, text, width=WIDTH):
        self.text = text
        self.width = width
        super().__init__(
            "the status line is {0} columns wide and the window is {1}; "
            "SCRN-1 gives it one row and there is nowhere else to put it"
            .format(len(text), width))


def column_of(x):
    """Which terminal column maze square `x` is drawn in."""
    return 2 * x


def joiner_column(x):
    """The column between square `x` and square `x + 1`."""
    return 2 * x + 1


def compose(state, status_line=None):
    """The whole picture for one game state.

    A new `Frame` every call, every cell filled — caution C9. `status_line` is
    WI-6's row 29; left blank when none is given, because that row is not this
    module's to write.
    """
    frame = Frame(WIDTH, HEIGHT, BLANK, Colour.DEFAULT)
    draw_maze(frame, state.maze)
    draw_dots(frame, state)
    draw_player(frame, state)
    draw_ghost(frame, state)      # after the player: END-4
    if status_line is not None:
        draw_status_line(frame, status_line)
    return frame


def draw_maze(frame, maze):
    """Every wall square and the joins between them (SCRN-3)."""
    for (x, y) in maze.squares():
        if maze.is_wall(x, y):
            frame.put(column_of(x), y, wall_glyph(maze, x, y), WALL_COLOUR)
    for y in range(maze.height):
        for x in range(maze.width - 1):
            # Both squares wall means both glyphs already have an arm pointing
            # at the other -- WI-5a's joining-up property -- so the join is
            # drawn without asking which glyphs they are.
            if joins_up_with(maze, x, y) and joins_up_with(maze, x + 1, y):
                frame.put(joiner_column(x), y, JOINER, WALL_COLOUR)


def draw_dots(frame, state):
    """A dim gold dot on every corridor square that still has one (SCRN-4).

    Reads the state's dots rather than the maze's corridors, so a dot that has
    been eaten is simply absent — there is no "eaten" flag to get wrong.
    """
    for (x, y) in sorted(state.dots):
        frame.put(column_of(x), y, DOT, Colour.DOT)


def draw_player(frame, state):
    """The player: a bright yellow block, three columns wide (SCRN-5)."""
    _draw_actor(frame, state.player, PLAYER_GLYPH, Colour.PLAYER)


def draw_ghost(frame, state):
    """The ghost: a pink block of a different shape (SCRN-5).

    Drawn after the player (END-4) and over whatever is underneath, including
    a dot. It does not touch the dot in the state — SCORE-4, "a dot under the
    ghost is still there to be taken" — because nothing here writes to the
    state at all.
    """
    _draw_actor(frame, state.ghost, GHOST_GLYPH, Colour.GHOST)


def _draw_actor(frame, square, glyph, colour):
    x, y = square
    frame.put_text(column_of(x) - 1, y, glyph, colour)


def draw_status_line(frame, text):
    """WI-6's row, written where WI-6 asks for it (SCRN-1, SCRN-6).

    The text is taken exactly as given, leading spaces and all: what it says
    is STAT-1 to STAT-3's business and not this module's.
    """
    if len(text) > WIDTH:
        raise StatusLineTooWide(text)
    frame.put_text(0, STATUS_ROW, text, Colour.STATUS)


def picture_rows(frame):
    """The 29 maze rows as text, margin trimmed. For reading a failure."""
    return [row[:PICTURE_WIDTH] for row in frame.text_rows()[:MAZE_ROWS]]
