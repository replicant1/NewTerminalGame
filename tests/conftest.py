"""Shared test scaffolding.

Two unrelated sets of fixtures live here, one from WI-1 and one from WI-5,
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

import textwrap
from typing import Callable, List, Tuple

import pytest

from terminal_game.domain.maze import CORRIDOR_CHAR, WALL_CHAR, Maze, Position

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
