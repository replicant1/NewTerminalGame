# -*- coding: utf-8 -*-
"""The whole picture — ``render(state) -> Frame``. SCRN-1..6, STAT-1..3.

Pure, and comparable as text with no terminal anywhere near it. The frame
carries **style identifiers**, never curses attributes (plan §2.4,
architecture C6): that is the only reason the strongest test in this project
— the specification's own picture, rendered back character for character —
can run at all.

The geometry, derived from the specification's mock-up rather than guessed::

    picture column = 2 x maze column     maze col 0..18  ->  cols 0..36
    picture row    = maze row            maze row 0..28  ->  rows 0..28
    picture row 29 = the status line                                [SCRN-1]
    picture cols 37..39 = the narrow blank margin                   [MAZE-1]

Odd picture columns are *joiner* columns, filled by
:func:`termgame.theme.joiner_glyph`.

The draw order is walls, then dots, then the player, then **the ghost last**.
That single ordering is the whole of END-4: on a loss the player and the
ghost stand on the same square and the ghost is what the final picture shows.
"""

from typing import Tuple

from termgame import theme
from termgame.model import (
    MAZE_COLS,
    SCREEN_COLS,
    SCREEN_ROWS,
    STYLE_DEFAULT,
    Frame,
    FrameBuilder,
    GameState,
    Maze,
    Outcome,
    Position,
)

#: The row the status line lives on — the last one (SCRN-1).
STATUS_ROW = SCREEN_ROWS - 1

#: The first picture column of the blank right-hand margin (MAZE-1). The
#: maze's 19 columns occupy 0..36; 37, 38 and 39 are the margin.
MARGIN_FIRST_COL = 2 * MAZE_COLS - 1


def picture_col(maze_col: int) -> int:
    """The picture column maze column ``maze_col`` is drawn at."""
    return 2 * maze_col


def picture_row(maze_row: int) -> int:
    """The picture row maze row ``maze_row`` is drawn at."""
    return maze_row


def margin_columns(maze: Maze) -> Tuple[int, ...]:
    """The picture columns of the blank right-hand margin, for this maze."""
    first = 2 * maze.width - 1
    return tuple(range(first, SCREEN_COLS))


# --------------------------------------------------------------------------
# The layers, in draw order
# --------------------------------------------------------------------------


def draw_maze(builder: FrameBuilder, maze: Maze) -> None:
    """Layer one — the walls and the joiners between them (SCRN-3)."""
    for row in range(maze.height):
        for col in range(maze.width):
            if maze.is_wall((row, col)):
                builder.put(
                    picture_row(row),
                    picture_col(col),
                    theme.wall_glyph(maze, Position(row, col)),
                    theme.STYLE_WALL,
                )
            if col + 1 < maze.width and theme.joins_horizontally(maze, row, col):
                builder.put(
                    picture_row(row),
                    picture_col(col) + 1,
                    theme.JOINER_GLYPH,
                    theme.STYLE_WALL,
                )


def draw_dots(builder: FrameBuilder, dots) -> None:
    """Layer two — one dim gold dot to a corridor square (SCRN-4)."""
    for dot in sorted(dots):
        builder.put(
            picture_row(dot[0]),
            picture_col(dot[1]),
            theme.DOT_GLYPH,
            theme.STYLE_DOT,
        )


def draw_entity(builder: FrameBuilder, position, glyphs, style: str) -> None:
    """Draw a three-character entity centred on a maze cell (SCRN-5).

    It spills one column either side, into the joiner columns. That is safe
    without a special case because an entity only ever stands on a corridor
    cell, and a joiner beside a corridor cell is blank
    (:func:`termgame.theme.joins_horizontally`).
    """
    row = picture_row(position[0])
    centre = picture_col(position[1])
    for offset, glyph in zip((-1, 0, 1), glyphs):
        builder.put(row, centre + offset, glyph, style)


def draw_status(builder: FrameBuilder, outcome: Outcome, score: int) -> None:
    """The bottom row: the score and the keys, in cyan, and nothing else.

    STAT-1, STAT-2, STAT-3, SCRN-6 and SCORE-5's "the score is shown". The
    one-column indent is assumption **A3**, not a ruling — see
    :data:`termgame.theme.STATUS_INDENT`.
    """
    builder.put_text(
        STATUS_ROW,
        theme.STATUS_INDENT,
        theme.status_text(outcome, score),
        theme.STYLE_STATUS,
    )


# --------------------------------------------------------------------------
# The whole picture
# --------------------------------------------------------------------------


def render(state: GameState) -> Frame:
    """The picture of ``state`` — a 30 x 40 frame of character-plus-style.

    Walls, then dots, then the player, then **the ghost last** (END-4).
    """
    builder = FrameBuilder(
        SCREEN_ROWS, SCREEN_COLS, theme.BLANK_GLYPH, STYLE_DEFAULT
    )
    draw_maze(builder, state.maze)
    draw_dots(builder, state.dots)
    draw_entity(builder, state.player, theme.PLAYER_GLYPHS, theme.STYLE_PLAYER)
    draw_entity(builder, state.ghost, theme.GHOST_GLYPHS, theme.STYLE_GHOST)
    draw_status(builder, state.outcome, state.score)
    return builder.build()


def render_rows(state: GameState) -> Tuple[str, ...]:
    """The picture as 30 plain strings — what the golden fixture compares."""
    return render(state).rows()
