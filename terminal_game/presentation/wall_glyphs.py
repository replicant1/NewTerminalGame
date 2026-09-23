"""Which character draws a wall square, and the cell that joins two squares.

SCRN-3: walls are blue double lines that join their neighbours into corners,
tees and crossings, and a wall square with no wall beside it is a single block.
Each grid square is drawn two cells wide (architecture A6): the square itself in
cell ``2n`` and a joining cell to its east in cell ``2n + 1``.

Pure: characters only.  The colour (wall blue) is the frame composer's business.
"""

from __future__ import annotations

from typing import Callable

#: A lone wall square, with no wall to the north, south, east or west.
LONE = "■"
#: The joining cell between two horizontally adjacent wall squares.
JOIN = "═"
#: The joining cell anywhere else.
BLANK = " "

# (north, south, east, west) -> character, for all 16 combinations.
_GLYPHS = {
    (False, False, False, False): LONE,
    (False, False, True, False): "═",
    (False, False, False, True): "═",
    (False, False, True, True): "═",
    (True, False, False, False): "║",
    (False, True, False, False): "║",
    (True, True, False, False): "║",
    (False, True, True, False): "╔",
    (False, True, False, True): "╗",
    (True, False, True, False): "╚",
    (True, False, False, True): "╝",
    (True, True, True, False): "╠",
    (True, True, False, True): "╣",
    (False, True, True, True): "╦",
    (True, False, True, True): "╩",
    (True, True, True, True): "╬",
}

#: Every character this module can draw on a wall square or a joining cell.
WALL_CHARACTERS = frozenset(_GLYPHS.values()) | {JOIN}


def wall_glyph(north: bool, south: bool, east: bool, west: bool) -> str:
    """The character for a wall square, from which of its neighbours are wall."""
    return _GLYPHS[(bool(north), bool(south), bool(east), bool(west))]


def joining_glyph(west_is_wall: bool, east_is_wall: bool) -> str:
    """The cell between two horizontally adjacent squares: ``═`` if both are wall."""
    return JOIN if (west_is_wall and east_is_wall) else BLANK


IsWall = Callable[[int, int], bool]


def _wall(is_wall: IsWall, width: int, height: int, col: int, row: int) -> bool:
    """Whether (col, row) is wall; a square beyond the edge of the grid is not."""
    return 0 <= col < width and 0 <= row < height and bool(is_wall(col, row))


def square_glyph(is_wall: IsWall, width: int, height: int, col: int, row: int) -> str:
    """The character for the wall square at (col, row) of a ``width`` x ``height`` grid.

    ``is_wall(col, row)`` answers for squares on the grid; squares beyond its
    edge count as not wall, whatever ``is_wall`` would say about them.
    """
    return wall_glyph(
        north=_wall(is_wall, width, height, col, row - 1),
        south=_wall(is_wall, width, height, col, row + 1),
        east=_wall(is_wall, width, height, col + 1, row),
        west=_wall(is_wall, width, height, col - 1, row),
    )


def joining_cell(is_wall: IsWall, width: int, height: int, col: int, row: int) -> str:
    """The cell east of square (col, row): ``═`` only if it and its east neighbour are wall."""
    return joining_glyph(_wall(is_wall, width, height, col, row),
                         _wall(is_wall, width, height, col + 1, row))
