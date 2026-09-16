# -*- coding: utf-8 -*-
"""WI-12 — the frame composer: a game state becomes a picture.

Rows 0–28 of the frame, composed from a :class:`GameState`:

* **37 columns of maze.** Square *c* is drawn at column ``2 * c``, so columns
  0, 2, … 36; the odd columns are connectors (plan section 5, assumption A6).
* **A blank 3-column right margin**, columns 37–39.  The architecture's
  MAZE-1 prose says 38 columns and a 2-column margin and is simply wrong;
  its own measurement V8, the technical lead's parse and mine all give 37
  and 3 (contradiction C-1).
* **Dots** as the dim gold ``▪``, one to a corridor square that still has one.
* **The player** as the three-column bright yellow ``▐█▌`` and **the ghost**
  as the three-column pink ``▗█▖``, each centred on its square's column and
  so covering the connector on either side.  That is safe: a connector next
  to a corridor square is always blank, because the horizontal wall glyph
  only ever appears between two horizontally joined wall squares.
* **The player painted first and the ghost second** (END-4), so that on a
  loss the ghost covers the player and the final picture shows what happened.

Who owns what, where this item meets its neighbours
---------------------------------------------------
**WI-8 owns every wall glyph and the connector rule; this module declares
none of them.**  The walls arrive as a finished layer from
:func:`terminal_game.presentation.wall_glyphs.wall_layer`, which WI-8
announced for this item: one tuple of :class:`Cell` per grid row, square *c*
already at index ``2c`` and the connector at ``2c + 1``, corridor squares
blank.  The composer lays the dots and the actors over it and never needs to
know a single wall character.

**WI-13 owns row 29 and produces it as a value; this module places whatever
it is given and writes nothing there itself** (STAT-1).  There is not a
status-line literal anywhere in this file, and there must never be one.

**The dot glyph and the two actor motifs are this module's**, per the
ownership table.  WI-8 declares none of them.

Layer
-----
Presentation.  It may name Application and Domain, and it may not name the
Shell or any toolkit.  It draws nothing: it returns a value.
"""

from __future__ import annotations

from typing import Optional, Sequence

from terminal_game.domain.game_state import GameState
from terminal_game.domain.maze import Maze, Square
from terminal_game.presentation.frame import (
    BLANK,
    FRAME_COLUMNS,
    MAZE_COLUMNS,
    MAZE_ROWS,
    RIGHT_MARGIN_COLUMNS,
    STATUS_ROW,
    Cell,
    Colour,
    Frame,
    FrameBuilder,
)
from terminal_game.presentation.wall_glyphs import wall_layer

__all__ = [
    "DOT_GLYPH",
    "PLAYER_MOTIF",
    "GHOST_MOTIF",
    "column_of_square",
    "compose_frame",
]


#: SCRN-4 — a small dim gold square, one to a corridor square.  **WI-12's**,
#: per the ownership table; WI-8 declares it nowhere.
DOT_GLYPH = "▪"

#: SCRN-5 — the player, bright yellow, three columns centred on its square.
PLAYER_MOTIF = "▐█▌"

#: SCRN-5 — the ghost, pink, three columns centred on its square.  A
#: different shape as well as a different colour, so the two can be told
#: apart by outline and not only by hue.
GHOST_MOTIF = "▗█▖"


def column_of_square(column_index: int) -> int:
    """Which frame column a maze square is drawn at: square *c* at ``2c``."""
    if column_index < 0:
        raise IndexError(
            "there is no square at column {0}".format(column_index)
        )
    column = 2 * column_index
    if column >= MAZE_COLUMNS:
        raise IndexError(
            "square {0} would be drawn at column {1}, past the {2} columns "
            "of maze".format(column_index, column, MAZE_COLUMNS)
        )
    return column


def _place_motif(
    builder: FrameBuilder,
    row: int,
    square: Square,
    motif: str,
    colour: Colour,
) -> None:
    """Draw a three-column motif centred on *square*'s column.

    It covers ``2c - 1`` … ``2c + 1``, overwriting the connector on each
    side.  At the very edge of the maze there is no column to the left of 0
    or right of 36, so the motif is clipped rather than refused — a square on
    the border ring is a wall and cannot hold an actor, but clipping keeps
    the function total rather than making the picture depend on it.
    """
    centre = column_of_square(square.column)
    for offset, glyph in zip((-1, 0, 1), motif):
        column = centre + offset
        if 0 <= column < MAZE_COLUMNS:
            builder.set_cell(row, column, glyph, colour)


def compose_frame(
    state: GameState,
    status_row: Sequence[Cell],
    walls=wall_layer,
) -> Frame:
    """The whole picture: rows 0–28 from *state*, row 29 as given.

    *status_row* is 40 cells produced by WI-13, placed exactly as handed
    over.  This function writes nothing into row 29 and reads nothing from
    it.

    *walls* is WI-8's :func:`~terminal_game.presentation.wall_glyphs.wall_layer`
    and normally wants no argument.  It is overridable only so that this
    item's own tests can stand the walls in with an obviously fake
    vocabulary: which glyph a wall is drawn as belongs to WI-8's tests, and
    re-asserting it here would turn one defect into two red files.

    The state is not modified and nothing is taken from the dot field: a dot
    under the ghost is still there afterwards (SCORE-4), because composing a
    picture is a question and not a move.
    """
    maze = state.maze
    # A maze must *fit*, rather than be exactly the real one's size, so that
    # a test can compose a small hand-built maze and read the whole picture.
    # The real game always hands over 19 x 29, which fills the 37 columns and
    # 29 rows exactly; there is a test for that.
    if maze.height > MAZE_ROWS:
        raise ValueError(
            "the maze is {0} rows deep and the picture has room for "
            "{1}".format(maze.height, MAZE_ROWS)
        )
    if 2 * maze.width - 1 > MAZE_COLUMNS:
        raise ValueError(
            "a maze {0} squares across needs {1} columns and a maze row has "
            "{2}".format(maze.width, 2 * maze.width - 1, MAZE_COLUMNS)
        )

    builder = FrameBuilder()

    # The walls, exactly as WI-8 lays them out — square c already at 2c and
    # the connector at 2c + 1, corridor squares blank.
    layer = walls(maze)
    expected_width = 2 * maze.width - 1
    if len(layer) != maze.height:
        raise ValueError(
            "the wall layer is {0} rows and the maze is {1}".format(
                len(layer), maze.height
            )
        )
    for row, cells in enumerate(layer):
        if len(cells) != expected_width:
            raise ValueError(
                "wall layer row {0} is {1} cells and a {2}-square maze row "
                "is {3}".format(row, len(cells), maze.width, expected_width)
            )
        for column, cell in enumerate(cells):
            if cell != BLANK:
                builder.set_cell(row, column, cell.glyph, cell.colour)

    # SCRN-4: a dot on every corridor square that still has one.  Asking the
    # dot field rather than the maze is what makes an eaten square show
    # blank rather than a dot.
    for square in state.dots.squares():
        builder.set_cell(
            square.row,
            column_of_square(square.column),
            DOT_GLYPH,
            Colour.DOT_GOLD,
        )

    # END-4: the player first and the ghost second, so that when they share a
    # square the ghost is what is seen and the last picture shows the loss.
    _place_motif(
        builder, state.player.row, state.player, PLAYER_MOTIF,
        Colour.PLAYER_YELLOW,
    )
    _place_motif(
        builder, state.ghost.row, state.ghost, GHOST_MOTIF,
        Colour.GHOST_PINK,
    )

    builder.place_row(STATUS_ROW, status_row)
    return builder.build()
