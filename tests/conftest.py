"""Fixtures shared by the tests that need a real toolkit but no window.

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
for a second root to do.
"""

from __future__ import annotations

import tkinter

import pytest


@pytest.fixture(scope="session")
def tk_root():
    """A Tk root that never reaches the screen, for the whole test session."""
    root = tkinter.Tk()
    root.withdraw()          # must be the very next statement — see above
    try:
        yield root
    finally:
        root.destroy()


@pytest.fixture
def surface(tk_root):
    """A fresh :class:`GridSurface` on the withdrawn root, reaped afterwards.

    Imported inside the fixture rather than at module scope so that collecting
    this file does not import the toolkit for tests that do not want it.
    """
    from terminal_game.presentation.surface import GridSurface

    made = GridSurface(tk_root)
    try:
        yield made
    finally:
        made.widget.destroy()
