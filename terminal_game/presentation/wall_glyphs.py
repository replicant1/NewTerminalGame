# -*- coding: utf-8 -*-
"""WI-8 — the wall glyphs, and the rule for the connector column (SCRN-3).

A pure function from **a wall square's four neighbours** to the character that
square is drawn as: the double-line corners, tees, crossings and straights
that join up with their neighbours, and the lone blue block when the square
has no wall next to it.  Plus the rule for the odd "connector" columns that
sit between two square columns.

All of it is blue.  There is one colour in this module and it is
``Colour.WALL_BLUE``.

Ownership
---------
**WI-8 owns every wall glyph and the connector rule.  It declares neither the
dot glyph nor the two actor motifs** — those are WI-12's, and nothing in this
module has heard of them.  A later item that needs a wall character asks for
it here rather than retyping ``U+2560`` into its own source.

Where the table came from
-------------------------
Not from memory.  The specimen picture in ``FUNCTIONAL_REQUIREMENTS.md`` was
inverted back into a 19 x 29 grid of wall and corridor, and every wall
square's glyph was read off against the wall neighbours that square actually
has.  **Fifteen of the sixteen combinations occur in the specimen and every
one of them agrees with the table below.**  The sixteenth — a wall with walls
on all four sides, drawn ``U+256C`` — does not occur in the specimen, which is
the one entry reasoned rather than measured, and the implementation plan
(section 5) says so too.

The geometry, from section 5 of the plan
----------------------------------------
Square *c* of a maze row is drawn at frame column ``2 * c``.  The odd column
``2 * c + 1`` between squares *c* and *c + 1* is a **connector**: it carries
the horizontal glyph when both of those squares are wall, and is blank
otherwise.  That is the whole rule, and it is why a wall run reads as one
unbroken double line rather than as separated glyphs.

A consequence worth stating, because it is what makes the three-column actor
motifs safe: a connector next to a corridor square is always blank, since the
horizontal glyph appears only between **two** wall squares.

What this module cannot tell you
--------------------------------
Whether the strokes of adjacent double-line glyphs actually **meet** on
screen.  Their advance widths are uniform in Menlo — DEV-B measured that for
all 113 glyphs the picture uses, at 14, 16, 18 and 20pt — so they land in the
right places.  Whether the ink joins is a question about glyph shapes, not
metrics, and **only an eye can answer it**.  It is open, it belongs to WI-16,
and nothing in this file or its tests should be read as having settled it.

Layer
-----
Presentation.  This module names the Domain (``Maze``, ``Direction``,
``Square``) and its own frame vocabulary, and imports no windowing toolkit.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, Iterable, Tuple

from terminal_game.domain.maze import Direction, Maze, Square
from terminal_game.presentation.frame import BLANK, Cell, Colour

__all__ = [
    "WALL_COLOUR",
    "LONE_WALL_GLYPH",
    "HORIZONTAL_GLYPH",
    "VERTICAL_GLYPH",
    "CROSSING_GLYPH",
    "BLANK_CONNECTOR_GLYPH",
    "WALL_GLYPHS",
    "glyph_for_wall_neighbours",
    "wall_glyph_at",
    "wall_cell_at",
    "connector_glyph_east_of",
    "connector_cell_east_of",
    "wall_layer_text",
    "wall_layer",
    "NotAWallSquare",
]


#: Every wall character is drawn in this one colour (SCRN-3).
WALL_COLOUR = Colour.WALL_BLUE

#: A wall square with no wall beside it (SCRN-3, the lone blue block).
LONE_WALL_GLYPH = "■"  # BLACK SQUARE

#: The double horizontal — also what a connector between two walls carries.
HORIZONTAL_GLYPH = "═"  # BOX DRAWINGS DOUBLE HORIZONTAL

#: The double vertical.
VERTICAL_GLYPH = "║"  # BOX DRAWINGS DOUBLE VERTICAL

#: Walls on all four sides.  The one entry the specimen does not contain.
CROSSING_GLYPH = "╬"  # BOX DRAWINGS DOUBLE VERTICAL AND HORIZONTAL

#: What a connector column holds when it is not joining two walls.  A space,
#: on the black ground — not a blue space, because nothing is drawn there.
BLANK_CONNECTOR_GLYPH = " "


_N = Direction.NORTH
_E = Direction.EAST
_S = Direction.SOUTH
_W = Direction.WEST


#: All sixteen combinations of wall neighbours, each mapped to its glyph.
#:
#: Read it as: which sides this wall square must reach towards.  A stub with
#: one neighbour is drawn as the straight line it is part of, which is what
#: makes the end of a wall run look like a line and not like a corner.
WALL_GLYPHS: Dict[FrozenSet[Direction], str] = {
    frozenset(): LONE_WALL_GLYPH,                       # no neighbour
    frozenset((_N,)): VERTICAL_GLYPH,                   # north only
    frozenset((_E,)): HORIZONTAL_GLYPH,                 # east only
    frozenset((_S,)): VERTICAL_GLYPH,                   # south only
    frozenset((_W,)): HORIZONTAL_GLYPH,                 # west only
    frozenset((_N, _S)): VERTICAL_GLYPH,                # a vertical run
    frozenset((_E, _W)): HORIZONTAL_GLYPH,              # a horizontal run
    frozenset((_N, _E)): "╚",                      # bottom-left corner
    frozenset((_N, _W)): "╝",                      # bottom-right corner
    frozenset((_S, _E)): "╔",                      # top-left corner
    frozenset((_S, _W)): "╗",                      # top-right corner
    frozenset((_N, _E, _S)): "╠",                  # tee, opening east
    frozenset((_N, _W, _S)): "╣",                  # tee, opening west
    frozenset((_E, _S, _W)): "╦",                  # tee, opening south
    frozenset((_N, _E, _W)): "╩",                  # tee, opening north
    frozenset((_N, _E, _S, _W)): CROSSING_GLYPH,        # a crossing
}


class NotAWallSquare(ValueError):
    """Raised when a wall glyph is asked for a square that is corridor.

    A corridor square has no wall glyph at all — what goes there is a dot, an
    actor or nothing, and all three are WI-12's.  Answering with a space would
    let a composition bug draw a silently blank maze; raising will not.
    """


def glyph_for_wall_neighbours(neighbours: Iterable[Direction]) -> str:
    """The character a wall square is drawn as, given its wall neighbours.

    *neighbours* is the set of directions in which this square's orthogonal
    neighbour is itself a wall — exactly what ``Maze.wall_neighbours`` returns.
    A neighbour off the edge of the grid is not a wall, which is what makes
    the border ring resolve to the corner and edge glyphs the specimen shows.

    This is the whole of SCRN-3 in one lookup, and it is total: all sixteen
    combinations have an answer, including none of them.
    """
    try:
        key = frozenset(neighbours)
    except TypeError:
        raise TypeError(
            "wall neighbours must be an iterable of Direction, not "
            "{0!r}".format(neighbours)
        )
    for member in key:
        if not isinstance(member, Direction):
            raise TypeError(
                "{0!r} is not a Direction; the wall neighbours are the four "
                "orthogonal ones and nothing else".format(member)
            )
    return WALL_GLYPHS[key]


def wall_glyph_at(maze: Maze, square: Square) -> str:
    """The character the wall at *square* is drawn as.

    Raises :class:`NotAWallSquare` if *square* is corridor, and whatever
    ``Maze`` raises if it is outside the grid.
    """
    if not maze.is_wall(square):
        raise NotAWallSquare(
            "square {0!r} is corridor, and corridor has no wall glyph".format(
                tuple(square)
            )
        )
    return glyph_for_wall_neighbours(maze.wall_neighbours(square))


def wall_cell_at(maze: Maze, square: Square) -> Cell:
    """The wall at *square* as a frame cell — its glyph, in wall blue."""
    return Cell(wall_glyph_at(maze, square), WALL_COLOUR)


def connector_glyph_east_of(maze: Maze, square: Square) -> str:
    """What the connector column immediately east of *square* holds.

    That is frame column ``2 * square.column + 1``.  It is the horizontal
    glyph when *square* and its eastern neighbour are **both** wall, and a
    blank in every other case — including when either one is corridor.

    Asking about the last square of a row raises: there is no connector
    column after it, since a row of *w* squares is ``2 * w - 1`` columns wide.
    """
    east = square.neighbour(Direction.EAST)
    if not maze.contains(east):
        raise ValueError(
            "square {0!r} is the last of its row in a {1}-square-wide maze, "
            "so there is no connector column east of it".format(
                tuple(square), maze.width
            )
        )
    if maze.is_wall(square) and maze.is_wall(east):
        return HORIZONTAL_GLYPH
    return BLANK_CONNECTOR_GLYPH


def connector_cell_east_of(maze: Maze, square: Square) -> Cell:
    """The connector east of *square* as a frame cell.

    A joining connector is the horizontal glyph in wall blue; a blank one is
    the frame's blank — a space on the black ground, because nothing is drawn
    there and colouring an empty cell blue would be a lie about the picture.
    """
    glyph = connector_glyph_east_of(maze, square)
    if glyph == BLANK_CONNECTOR_GLYPH:
        return BLANK
    return Cell(glyph, WALL_COLOUR)


def wall_layer(maze: Maze) -> Tuple[Tuple[Cell, ...], ...]:
    """Every wall of *maze*, laid out as cells, with blanks everywhere else.

    One tuple per grid row, each ``2 * maze.width - 1`` cells long: square *c*
    at index ``2 * c`` and the connector at ``2 * c + 1``.  Corridor squares
    come back blank, so this is the wall skeleton and nothing more.

    **Announced for WI-12** (first-lander rule 4).  The frame composer owns
    rows 0-28 and lays the dots and the actors over this; it does not need to
    know a single wall character to do so.
    """
    rows = []
    for row in range(maze.height):
        cells = []
        for column in range(maze.width):
            square = Square(column, row)
            if maze.is_wall(square):
                cells.append(wall_cell_at(maze, square))
            else:
                cells.append(BLANK)
            if column < maze.width - 1:
                cells.append(connector_cell_east_of(maze, square))
        rows.append(tuple(cells))
    return tuple(rows)


def wall_layer_text(maze: Maze) -> str:
    """:func:`wall_layer` as lines of text, for asserting a picture.

    Trailing blanks are kept: every line is ``2 * maze.width - 1`` characters,
    because that is how wide the maze really is on screen.
    """
    return "\n".join(
        "".join(cell.glyph for cell in row) for row in wall_layer(maze)
    )
