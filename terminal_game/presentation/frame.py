"""The whole 40 x 30 field of glyph-and-colour, as data.

This is Presentation with nothing impure in it: it takes a maze, a dot field
and two actor positions, and returns a grid of characters and colour names.
It never paints, never names a toolkit and never reads a pixel.  WI-5 turns
what comes out of here into light; WI-7 and WI-14 join the two.

**What WI-4 owns and what it does not.**  Rows 0 to 28 are the maze
(SCRN-1), and they are composed here.  **Row 29 is supplied from outside** —
WI-12 owns its content, this module only places it — so
:func:`compose_frame` takes it as an argument and copies it in unexamined
apart from its width.

**The grid mapping, which is measured rather than assumed.**  Ruling C-2:
maze square ``x`` is drawn at screen column ``2 * x`` for ``x`` in 0..18, so a
maze row occupies 37 of the 40 columns and the last three are a blank right
margin.  The odd columns between squares are *connectors*, and a connector
carries the horizontal double line only when the squares on both sides of it
are walls; otherwise it is blank.  Every one of those facts was read off the
specimen picture in ``docs/FUNCTIONAL_REQUIREMENTS.md``, which assumption P5
makes normative, and ``tests/test_frame.py`` re-derives the whole picture from
this module on every run.

**Three cells to an actor.**  The player and the ghost each occupy the
square's own column plus the connector either side — the specimen draws the
player at columns 19, 20, 21 and the ghost at 1, 2, 3.  That is safe because a
connector beside a corridor square is always blank: a horizontal wall join
needs walls on *both* sides, and an actor stands on a corridor.  So a
three-cell actor can never overwrite a wall glyph, and the tests check that
rather than trusting it.

**The order the layers go down is load-bearing.**  Ground, then walls, then
dots, then the player, then **the ghost last** — END-4: *"when both actors are
on one square the ghost is what you see."*  The final picture of a loss has to
show what happened.
"""

from __future__ import annotations

import enum
from typing import Iterable, List, NamedTuple, Sequence, Tuple

from terminal_game.domain.maze import HEIGHT, WIDTH, Maze, Position
from terminal_game.presentation.wall_glyphs import wall_glyph

# --------------------------------------------------------------------------
# The shape of the field
# --------------------------------------------------------------------------

#: WIN-2.  The window is 40 characters wide and 30 rows deep.
COLUMNS = 40
ROWS = 30

#: SCRN-1.  The top 29 rows are the maze; the bottom row is the status line.
MAZE_ROWS = HEIGHT
STATUS_ROW = ROWS - 1

#: Ruling C-2.  19 squares at ``2x`` spans columns 0 to 36 — 37 columns — and
#: leaves three blank ones down the right-hand edge (MAZE-1's *"narrow blank
#: margin"*).
MAZE_COLUMNS = 2 * WIDTH - 1
RIGHT_MARGIN = COLUMNS - MAZE_COLUMNS


class Colour(enum.Enum):
    """The colours the specification names, as names rather than as pixels.

    Presentation produces data; turning a name into something a screen can
    show is WI-5's, and it is the only part of the program that should know
    what "gold" is in hexadecimal.  Each member cites the requirement that
    asks for it.
    """

    #: SCRN-3, ruled to WI-4: the walls, *and* the lone block, are one blue.
    BLUE = "blue"
    #: SCRN-4: *"a small dim gold square"*.
    GOLD = "gold"
    #: SCRN-5: the player is *"a bright yellow block"*.
    YELLOW = "yellow"
    #: SCRN-5: the ghost is *"a pink block of a different shape"*.
    PINK = "pink"
    #: SCRN-6: the status line.  WI-12 owns row 29's content; this member is
    #: here because the colour vocabulary is one vocabulary, and section 7
    #: makes WI-4 the item that defines the seam WI-12 fills.
    CYAN = "cyan"
    #: WIN-2: the black ground.  The colour of a cell with nothing in it.
    BLACK = "black"

    def __str__(self) -> str:
        return self.value


class Cell(NamedTuple):
    """One character of the picture: what it is, and what colour it is."""

    glyph: str
    colour: Colour


#: Nothing here.  A space on the black ground.
BLANK = Cell(" ", Colour.BLACK)

# --------------------------------------------------------------------------
# The glyphs that are not walls
# --------------------------------------------------------------------------

#: SCRN-4, U+25AA BLACK SMALL SQUARE — one to an undisturbed corridor square.
DOT_GLYPH = "▪"

#: U+2550 BOX DRAWINGS DOUBLE HORIZONTAL, on a connector between two walls.
#: The same character WI-3 returns for an east-west wall, because it is the
#: same line continuing.
CONNECTOR_GLYPH = "═"

#: SCRN-5.  Each actor is three cells wide: the connector to its west, its own
#: column, the connector to its east.  The player is a solid block flanked by
#: half blocks; the ghost is the same block on two feet, which is the
#: *"different shape"* the requirement asks for — so the two differ by outline
#: even where a photograph of one cell would not tell them apart.
PLAYER_GLYPHS = ("▐", "█", "▌")  # ▐ █ ▌
GHOST_GLYPHS = ("▗", "█", "▖")  # ▗ █ ▖


def _screen_column(x: int) -> int:
    """Ruling C-2: maze square ``x`` is drawn at screen column ``2x``."""
    return 2 * x


def _is_wall(maze: "Maze", x: int, y: int) -> bool:
    """Whether the square at ``(x, y)`` is a wall, counting outside as *not*.

    WI-3 measured this from the border corners of the specimen: the top-left
    square is drawn ``╔``, the glyph for *south and east only*, so the
    neighbours it does not have are open rather than solid.  ``Maze.is_wall``
    raises off the grid — deliberately, so an out-of-bounds bug cannot pass
    for a dead end — which is why the check is here rather than there.
    """
    if not (0 <= x < WIDTH and 0 <= y < HEIGHT):
        return False
    return maze.is_wall(Position(x, y))


def _blank_field() -> List[List[Cell]]:
    """A 40 x 30 field of black ground, ready to be drawn on."""
    return [[BLANK for _ in range(COLUMNS)] for _ in range(ROWS)]


def _draw_walls(field: List[List[Cell]], maze: "Maze") -> None:
    """SCRN-3: every wall square, and the connectors that join them up."""
    for y in range(HEIGHT):
        for x in range(WIDTH):
            if not _is_wall(maze, x, y):
                continue
            glyph = wall_glyph(
                north=_is_wall(maze, x, y - 1),
                south=_is_wall(maze, x, y + 1),
                east=_is_wall(maze, x + 1, y),
                west=_is_wall(maze, x - 1, y),
            )
            field[y][_screen_column(x)] = Cell(glyph, Colour.BLUE)

        # A connector carries the line only between two walls.  Anything else
        # stays blank, which is what leaves room for a three-cell actor.
        for x in range(WIDTH - 1):
            if _is_wall(maze, x, y) and _is_wall(maze, x + 1, y):
                field[y][_screen_column(x) + 1] = Cell(
                    CONNECTOR_GLYPH, Colour.BLUE
                )


def _draw_dots(field: List[List[Cell]], dots: Iterable["Position"]) -> None:
    """SCRN-4: one dim gold square on each corridor square that still has one."""
    for dot in dots:
        field[dot.y][_screen_column(dot.x)] = Cell(DOT_GLYPH, Colour.GOLD)


def _draw_actor(
    field: List[List[Cell]],
    position: "Position",
    glyphs: Tuple[str, str, str],
    colour: "Colour",
) -> None:
    """SCRN-5: an actor, three cells wide, centred on its own column.

    A column outside the field is skipped rather than wrapped.  MAZE-3's solid
    border means an actor can never stand on column 0 or 18, so this cannot
    happen in a real game — but a negative index in Python quietly addresses
    the far end of the row, and a silent wrap is a worse bug than a missing
    half-block.
    """
    centre = _screen_column(position.x)
    for offset, glyph in zip((-1, 0, 1), glyphs):
        column = centre + offset
        if 0 <= column < COLUMNS:
            field[position.y][column] = Cell(glyph, colour)


def compose_maze_rows(
    maze: "Maze",
    dots: Iterable["Position"],
    player: "Position",
    ghost: "Position",
) -> Tuple[Tuple[Cell, ...], ...]:
    """Rows 0 to 28 of the picture: the maze, the dots and the two actors.

    :param maze: which squares are wall and which are corridor.
    :param dots: the corridor squares that still hold a dot.  Read, never
        changed — SCORE-4 says an actor standing on a dot *hides* it.
    :param player: the player's square.
    :param ghost: the ghost's square.
    :returns: 29 rows of 40 :class:`Cell`.

    The order is ground, walls, dots, player, **ghost last** (END-4).
    """
    field = _blank_field()
    _draw_walls(field, maze)
    _draw_dots(field, frozenset(dots))
    _draw_actor(field, player, PLAYER_GLYPHS, Colour.YELLOW)
    _draw_actor(field, ghost, GHOST_GLYPHS, Colour.PINK)
    return tuple(tuple(row) for row in field[:MAZE_ROWS])


def compose_frame(
    maze: "Maze",
    dots: Iterable["Position"],
    player: "Position",
    ghost: "Position",
    status_row: Sequence[Cell],
) -> Tuple[Tuple[Cell, ...], ...]:
    """The whole 40 x 30 field: the maze rows, and row 29 placed beneath them.

    :param status_row: exactly 40 cells, whatever WI-12 says they are.  This
        function does not read them and owns nothing of their content — it
        checks the width, because a short row would silently ragged the field,
        and copies them in.
    :returns: 30 rows of 40 :class:`Cell`.
    """
    if len(status_row) != COLUMNS:
        raise ValueError(
            "the status row is {} cells wide (WIN-2); got {}".format(
                COLUMNS, len(status_row)
            )
        )
    return compose_maze_rows(maze, dots, player, ghost) + (tuple(status_row),)
