"""The whole picture: from the game's state to 40 x 30 cells the shell paints.

SCRN-1, SCRN-4, SCRN-5, MAZE-1 (grid to cells), END-4, SCORE-4 (drawing).

A frame is 30 rows of 40 ``(character, role)`` cells, the shape the shell's
frame check accepts (lane C, ``terminal_game/shell/frame.py``).  Row 0 is the
top of the window and cell 0 its left edge.

* **Rows 0 to 28 are the maze.**  Grid square *n* of a row is drawn in cell
  ``2n`` and its joining cell to the east in ``2n + 1`` (architecture A6), so the
  19 squares fill cells 0 to 36.  Cells 37, 38 and 39 are always blank.
* A wall square is its wall glyph (WI-4) in wall blue; the joining cell between
  two wall squares is ``═`` in wall blue.
* A corridor square holding a dot is ``▪`` in dot gold; one without is blank.
* The player is ``▐█▌`` in bright yellow and the ghost ``▗█▖`` in pink, each
  centred on its square's cell and spilling into the joining cells either side.
  The ghost is drawn after the player, so when they share a square the ghost is
  what shows (END-4).  On horizontally adjacent squares the ghost's edge covers
  the player's, and both centre blocks show.  A dot under the ghost is hidden
  while it stands there and comes back when it moves off, because every frame
  is drawn afresh from the state.
* **Row 29 is the status line** exactly as WI-5 gives it.
* Every blank cell in the maze rows is in the background role.  The status
  row is WI-5's, blanks included: all 40 of its cells are in the status role.

What it reads from the state, and nothing else: ``maze`` (with ``width``,
``height``, ``is_wall(square)`` and ``is_corridor(square)``), ``dots`` (the
squares that still hold one), ``player``, ``ghost`` (squares as ``(col, row)``),
``score`` and ``outcome``.  The domain's ``GameState`` (WI-7) has exactly these.
It changes nothing: composing is a pure function of the state.
"""

from __future__ import annotations

from typing import List, Tuple

from terminal_game.presentation import roles
from terminal_game.presentation.status_line import status_row
from terminal_game.presentation.wall_glyphs import joining_cell, square_glyph

COLUMNS = 40
ROWS = 30
MAZE_ROWS = 29
STATUS_ROW = 29
#: 19 squares fill cells 0 to 36, leaving 37 to 39 blank (MAZE-1's margin).
MAX_MAZE_WIDTH = 19

DOT = "▪"
PLAYER_SPRITE = "▐█▌"
GHOST_SPRITE = "▗█▖"
BLANK = (" ", roles.BACKGROUND)

Cell = Tuple[str, str]
Frame = List[List[Cell]]


def _maze_row(maze, dots, row: int) -> List[Cell]:
    def is_wall(col: int, r: int) -> bool:
        return maze.is_wall((col, r))

    cells: List[Cell] = [BLANK] * COLUMNS
    for col in range(maze.width):
        square = (col, row)
        if maze.is_wall(square):
            cells[2 * col] = (square_glyph(is_wall, maze.width, maze.height, col, row), roles.WALL)
        elif square in dots:
            cells[2 * col] = (DOT, roles.DOT)
        if col < maze.width - 1:
            join = joining_cell(is_wall, maze.width, maze.height, col, row)
            if join != " ":
                cells[2 * col + 1] = (join, roles.WALL)
    return cells


def _draw_sprite(frame: Frame, square, sprite: str, role: str) -> None:
    col, row = square
    centre = 2 * col
    for offset, character in zip((-1, 0, 1), sprite):
        cell = centre + offset
        if 0 <= cell < COLUMNS and 0 <= row < MAZE_ROWS:
            frame[row][cell] = (character, role)


def compose(state) -> Frame:
    """The 30 x 40 frame for ``state``.  Reads the state; changes nothing."""
    maze = state.maze
    if maze.height > MAZE_ROWS or maze.width > MAX_MAZE_WIDTH:
        raise ValueError("the frame holds a maze of up to %d x %d squares, not %d x %d"
                         % (MAX_MAZE_WIDTH, MAZE_ROWS, maze.width, maze.height))
    frame: Frame = [_maze_row(maze, state.dots, row) if row < maze.height else [BLANK] * COLUMNS
                    for row in range(MAZE_ROWS)]
    _draw_sprite(frame, state.player, PLAYER_SPRITE, roles.PLAYER)
    _draw_sprite(frame, state.ghost, GHOST_SPRITE, roles.GHOST)
    frame.append(status_row(state.score, state.outcome))
    return frame
