"""What the picture *is*, for rows 0 to 28 — the maze, the dots and the actors.

This is Presentation with nothing impure in it: it takes a maze, a dot field
and two actor positions, and fills in a :class:`~terminal_game.presentation.field.Field`.
It never paints, never names a toolkit and never reads a pixel.
``terminal_game.presentation.surface`` is the only thing that turns a field
into light.

**What WI-4 owns and what it does not.**  Rows 0 to 28 are the maze (SCRN-1),
and they are composed here.  **Row 29 is supplied from outside** — WI-12 owns
its content, this module only places it — so :func:`compose_frame` takes it as
an argument and copies it in unexamined apart from its width.

**On the data type, and why this module changed shape.**  WI-4 and WI-5 landed
within minutes of each other and each invented this seam, differently: WI-4
returned a tuple of tuples with a colour *enum*, WI-5 built
:class:`~terminal_game.presentation.field.Field` with ``#rrggbb`` colours and
declared in its own docstring that *"WI-4 composes rows 0-28 and WI-12 supplies
row 29; both produce one of these"*.  WI-5's is the seam, for three reasons
that are in its code rather than in anyone's preference: it had already been
specified there, it enforces SCRN-2 *in the data* where a tuple of tuples
cannot, and ``surface.present`` already consumes it.  WI-4b is this module
moving to it.  Colours therefore come from
:mod:`terminal_game.presentation.palette` and not from anything here.

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
three-cell actor can never overwrite a wall glyph, and the tests check that by
standing the player on all 264 corridor squares of the specimen rather than
trusting it.

**The order the layers go down is load-bearing.**  Ground, then walls, then
dots, then the player, then **the ghost last** — END-4: *"when both actors are
on one square the ghost is what you see."*  The final picture of a loss has to
show what happened.
"""

from __future__ import annotations

from typing import Iterable, Sequence, Tuple

from terminal_game.domain.maze import HEIGHT, WIDTH, Maze, Position
from terminal_game.presentation import palette
from terminal_game.presentation.field import Cell, Field
from terminal_game.presentation.metrics import COLUMNS, ROWS
from terminal_game.presentation.wall_glyphs import wall_glyph

# --------------------------------------------------------------------------
# The shape of the field
# --------------------------------------------------------------------------

#: SCRN-1.  The top 29 rows are the maze; the bottom row is the status line.
#: ``COLUMNS`` and ``ROWS`` themselves belong to
#: :mod:`terminal_game.presentation.metrics`, which is where the window's size
#: is decided; this is only how SCRN-1 divides them up.
MAZE_ROWS = HEIGHT
STATUS_ROW = ROWS - 1

#: Ruling C-2.  19 squares at ``2x`` spans columns 0 to 36 — 37 columns — and
#: leaves three blank ones down the right-hand edge (MAZE-1's *"narrow blank
#: margin"*).
MAZE_COLUMNS = 2 * WIDTH - 1
RIGHT_MARGIN = COLUMNS - MAZE_COLUMNS

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


def _draw_walls(field: "Field", maze: "Maze") -> None:
    """SCRN-3: every wall square, and the connectors that join them up.

    The colour is :data:`palette.WALL` for both, which is the technical lead's
    ruling on SCRN-3 — *"a lone block renders in the same blue as a line,
    since SCRN-3 names one colour for both"*.
    """
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
            field[_screen_column(x), y] = Cell(glyph, palette.WALL)

        # A connector carries the line only between two walls.  Anything else
        # stays blank, which is what leaves room for a three-cell actor.
        for x in range(WIDTH - 1):
            if _is_wall(maze, x, y) and _is_wall(maze, x + 1, y):
                field[_screen_column(x) + 1, y] = Cell(
                    CONNECTOR_GLYPH, palette.WALL
                )


def _draw_dots(field: "Field", dots: Iterable["Position"]) -> None:
    """SCRN-4: one dim gold square on each corridor square that still has one."""
    for dot in dots:
        field[_screen_column(dot.x), dot.y] = Cell(DOT_GLYPH, palette.DOT)


def _draw_actor(
    field: "Field",
    position: "Position",
    glyphs: Tuple[str, str, str],
    colour: str,
) -> None:
    """SCRN-5: an actor, three cells wide, centred on its own column.

    A column outside the field is skipped rather than allowed to raise.
    MAZE-3's solid border means an actor can never stand on column 0 or 18, so
    this cannot happen in a real game — but half an actor drawn at the edge of
    a hand-built test maze is a clearer failure than an ``IndexError`` from
    two layers down.
    """
    centre = _screen_column(position.x)
    for offset, glyph in zip((-1, 0, 1), glyphs):
        column = centre + offset
        if 0 <= column < COLUMNS:
            field[column, position.y] = Cell(glyph, colour)


def compose_maze_rows(
    maze: "Maze",
    dots: Iterable["Position"],
    player: "Position",
    ghost: "Position",
) -> "Field":
    """The maze, the dots and the two actors, drawn into rows 0 to 28.

    :param maze: which squares are wall and which are corridor.
    :param dots: the corridor squares that still hold a dot.  Read, never
        changed — SCORE-4 says an actor standing on a dot *hides* it.
    :param player: the player's square.
    :param ghost: the ghost's square.
    :returns: a :class:`Field`.  It is 40 x 30 because a field always is;
        **row 29 is left blank** for :func:`compose_frame` or for WI-12.

    The order is ground, walls, dots, player, **ghost last** (END-4).
    """
    field = Field()
    _draw_walls(field, maze)
    _draw_dots(field, frozenset(dots))
    _draw_actor(field, player, PLAYER_GLYPHS, palette.PLAYER)
    _draw_actor(field, ghost, GHOST_GLYPHS, palette.GHOST)
    return field


def compose_frame(
    maze: "Maze",
    dots: Iterable["Position"],
    player: "Position",
    ghost: "Position",
    status_row: Sequence["Cell"],
) -> "Field":
    """The whole 40 x 30 field: the maze rows, and row 29 placed beneath them.

    :param status_row: exactly 40 cells, whatever WI-12 says they are.  This
        function does not read them and owns nothing of their content — it
        checks the width, because a short row would leave the tail of row 29
        showing whatever was under it, and copies them in.
    :returns: a :class:`Field` ready for ``surface.present``.
    """
    if len(status_row) != COLUMNS:
        raise ValueError(
            "the status row is {} cells wide (WIN-2); got {}".format(
                COLUMNS, len(status_row)
            )
        )
    field = compose_maze_rows(maze, dots, player, ghost)
    for column, cell in enumerate(status_row):
        field[column, STATUS_ROW] = cell
    return field
