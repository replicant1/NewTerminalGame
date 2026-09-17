"""Shared test scaffolding.

Three unrelated sets of fixtures live here — from WI-1, WI-4 and WI-5 —
because pytest gives a directory exactly one ``conftest.py``.  They do not
interact; the headings below say which is which.

Mazes, from WI-1
----------------

Every structural property of a maze is a property of a *shape*, so a test
about one is only as good as a reader's ability to see the shape it is talking
about.  The :func:`draw` fixture lets a test write the shape out:

    maze = draw('''
        .....
        .###.
        .....
    ''', at=(4, 4))

A maze is always 19 x 29 (MAZE-1) and no other shape is representable, so a
picture is placed *into* an all-wall maze of the proper size rather than
becoming one.  That is convenient rather than a compromise: the surrounding
wall is MAZE-3's solid border, so a test gets a legal border for free and
breaches it only when that is the point.

Placed as a fixture in ``conftest.py`` rather than a module the tests import,
so that nothing has to be added to ``sys.path`` and ``tests/`` stays a plain
directory of test files.

The specimen picture, from WI-4
-------------------------------

The middle of this file is the **specimen picture** of
``docs/FUNCTIONAL_REQUIREMENTS.md``, taken apart into the maze, the dot field
and the two actor positions that compose it.  Assumption P5 makes that picture
normative, and it is the only fixture in the project that can catch a picture
composed correctly but *differently* from what the specification shows.

A toolkit with no window, from WI-5
-----------------------------------

**Nothing here puts a window on the user's screen**, which is plan section
1.6's bar for the default suite and one of the things WI-5 must establish.
The technique is S-1's, measured in ``docs/findings/S-1-tk-headless.md``: call
``withdraw()`` on the root *before the first turn of the event loop*.  Tk
defers mapping a toplevel to idle time, so a root withdrawn before any
``update_idletasks()`` never maps at all — it is not shown and then hidden, it
is never shown.

``tests/test_surface.py`` asserts that this actually held, rather than taking
it on trust.

One root serves the whole session.  Repeatedly creating and destroying Tk
roots in one process is a well-known source of flakiness, and there is nothing
for a second root to do.  The toolkit is imported inside the fixture rather
than at module scope, so a run that touches none of the Presentation tests
never loads it.
"""

from __future__ import annotations

import os
import re
import textwrap
from typing import (
    Callable,
    FrozenSet,
    List,
    NamedTuple,
    Optional,
    Set,
    Tuple,
)

import pytest

from terminal_game.domain.maze import (
    CORRIDOR_CHAR,
    HEIGHT,
    WALL_CHAR,
    WIDTH,
    Maze,
    Position,
)

# --------------------------------------------------------------------------
# Mazes, from WI-1
# --------------------------------------------------------------------------


def _rows_of(picture: str) -> List[str]:
    """The picture's lines, dedented, with blank leading and trailing ones gone."""
    lines = textwrap.dedent(picture).split("\n")
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def draw_at(picture: str, at: Tuple[int, int] = (0, 0)) -> Maze:
    """An all-wall maze with ``picture`` drawn into it at ``at``.

    ``.`` carves a corridor, ``#`` leaves wall, and a space leaves the square
    alone — which is what lets a picture be a shape rather than a rectangle.
    Anything else is a mistake in the test and says so.
    """
    left, top = at
    corridors = []  # type: List[Position]
    for row_index, line in enumerate(_rows_of(picture)):
        for column_index, character in enumerate(line):
            if character == CORRIDOR_CHAR:
                corridors.append(Position(left + column_index, top + row_index))
            elif character not in (WALL_CHAR, " "):
                raise ValueError(
                    "a test picture uses {!r} for corridor, {!r} for wall and "
                    "' ' for leave-alone; row {} column {} is {!r}".format(
                        CORRIDOR_CHAR, WALL_CHAR, row_index, column_index, character
                    )
                )
    return Maze.all_walls().with_corridors_at(corridors)


@pytest.fixture
def draw() -> Callable[..., Maze]:
    """Build a maze from a picture placed inside the 19 x 29 frame."""
    return draw_at


#: A corridor loop with no dead ends, well clear of the border.  Every square
#: on it has exactly two ways on and all of them are mutually reachable, so it
#: is sound by all three questions — the baseline a test breaks one thing in.
SOUND_RING = """
    .....
    .###.
    .###.
    .###.
    .....
"""


@pytest.fixture
def sound_maze(draw: Callable[..., Maze]) -> Maze:
    """A maze that passes all three of the checker's questions."""
    return draw(SOUND_RING, at=(4, 4))


# --------------------------------------------------------------------------
# The specimen picture
# --------------------------------------------------------------------------
#
# Assumption P5 makes the picture in ``docs/FUNCTIONAL_REQUIREMENTS.md``
# normative for the grid-to-screen mapping, the three-cell actor glyphs and
# the status-line literals.  It is a real 19 x 29 maze with real dots and two
# real actors on it, which makes it the best fixture in the project — and it
# is the only one that can catch a picture composed correctly but *differently*
# from what the specification shows.
#
# Added by WI-4, which needs the maze, the dots and the actors rather than
# just the rows.  WI-3's tests read the same picture, and WI-12 and WI-16 will
# want the status row, so the parse lives here rather than in any one of them.


def _specimen_screen_rows() -> List[str]:
    """Every line of the specimen picture, annotations stripped.

    Raises rather than returning something short: a fixture that silently
    finds nothing turns every test built on it green for the wrong reason.
    """
    path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs",
        "FUNCTIONAL_REQUIREMENTS.md",
    )
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    marker = "A game in progress looks like this:"
    if marker not in text:
        raise AssertionError(
            "{} no longer contains {!r}, so the specimen picture cannot be "
            "found. Assumption P5 makes that picture normative; fix the "
            "locator rather than deleting what depends on it.".format(path, marker)
        )
    fenced = text.split(marker, 1)[1].split("```")[1]
    rows = [
        re.split(r"\s{3,}←", line)[0]
        for line in fenced.split("\n")
        if line.strip()
    ]
    if len(rows) < HEIGHT + 1:
        raise AssertionError(
            "the specimen picture parsed to {} rows; MAZE-1 and SCRN-1 want "
            "{} maze rows and a status row".format(len(rows), HEIGHT)
        )
    return rows


#: What a *corridor* square is drawn as at the square's own column: blank (a
#: dot already eaten), the dot, or the solid centre cell of an actor.  Defined
#: without reference to any wall glyph, so that classifying the picture does
#: not assume the very table WI-3's tests are checking.
SPECIMEN_CORRIDOR_GLYPHS = frozenset({" ", "▪", "█"})

#: The left-hand cell of each actor, which is how the two solid blocks in the
#: picture are told apart.  ▐ is the player's, ▗ is the ghost's.
_PLAYER_LEFT = "▐"
_GHOST_LEFT = "▗"


class Specimen(NamedTuple):
    """The specimen picture, taken apart into what composes it."""

    screen_rows: Tuple[str, ...]  # all 30, exactly as printed
    maze_rows: Tuple[str, ...]  # the 29 maze rows
    status_row: str  # row 29, the status line
    maze: Maze
    dots: FrozenSet[Position]
    player: Position
    ghost: Position


def read_specimen() -> Specimen:
    """Take the specimen picture apart into a maze, a dot field and two actors."""
    rows = _specimen_screen_rows()
    maze_rows = rows[:HEIGHT]
    wall_rows = []  # type: List[str]
    dots = set()  # type: Set[Position]
    player = None  # type: Optional[Position]
    ghost = None  # type: Optional[Position]
    for y in range(HEIGHT):
        line = ""
        for x in range(WIDTH):
            glyph = maze_rows[y][2 * x]
            if glyph not in SPECIMEN_CORRIDOR_GLYPHS:
                line += WALL_CHAR
                continue
            line += CORRIDOR_CHAR
            if glyph == "▪":
                dots.add(Position(x, y))
            elif glyph == "█":
                flank = maze_rows[y][2 * x - 1] if 2 * x - 1 >= 0 else ""
                if flank == _PLAYER_LEFT:
                    player = Position(x, y)
                elif flank == _GHOST_LEFT:
                    ghost = Position(x, y)
                else:
                    raise AssertionError(
                        "a solid block at {} is flanked by {!r}, which is "
                        "neither the player's nor the ghost's".format(
                            Position(x, y), flank
                        )
                    )
        wall_rows.append(line)
    if player is None or ghost is None:
        raise AssertionError(
            "the specimen picture must contain both actors; found "
            "player={} ghost={}".format(player, ghost)
        )
    return Specimen(
        screen_rows=tuple(rows),
        maze_rows=tuple(maze_rows),
        status_row=rows[HEIGHT],
        maze=Maze.from_rows(wall_rows),
        dots=frozenset(dots),
        player=player,
        ghost=ghost,
    )


@pytest.fixture
def specimen() -> Specimen:
    """The specimen picture of ``docs/FUNCTIONAL_REQUIREMENTS.md``, parsed."""
    return read_specimen()

# --------------------------------------------------------------------------
# A toolkit with no window, from WI-5
# --------------------------------------------------------------------------


@pytest.fixture(scope="session")
def tk_root():
    """A Tk root that never reaches the screen, for the whole test session."""
    import tkinter

    root = tkinter.Tk()
    root.withdraw()          # must be the very next statement — see above
    try:
        yield root
    finally:
        root.destroy()


@pytest.fixture
def surface(tk_root):
    """A fresh :class:`GridSurface` on the withdrawn root, reaped afterwards."""
    from terminal_game.presentation.surface import GridSurface

    made = GridSurface(tk_root)
    try:
        yield made
    finally:
        made.widget.destroy()