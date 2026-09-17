"""The join between the placement arithmetic and the real window.

``tests/test_placement.py`` owns what a position should be and never touches
the toolkit. This owns the one thing that file cannot: that
:meth:`GameWindow.move_to` actually moves the window to the position it was
given, and that a negative coordinate survives the trip through Tk.

**Only the join.** What the arithmetic computes is already pinned next door
and is not re-asserted here through a bigger object.

No window reaches the screen: every window here is built on the session's
withdrawn root, is never shown, and is reaped however the test ends. The
fixture is local rather than in ``conftest.py`` — WI-6's own ``window``
fixture lives in ``tests/test_window.py`` and the conftest is a named
contention point, so this adds nothing to either.
"""

from __future__ import annotations

import pytest

from terminal_game.shell.placement import Point, Rect, centred_on, placement_for
from terminal_game.shell.window import GameWindow

MAIN_DISPLAY = Rect(0, 0, 1512, 982)
UPPER_DISPLAY = Rect(-949, -1440, 2560, 1440)


@pytest.fixture
def unshown_window(tk_root):
    """A window on the session root, never shown, always reaped."""
    made = GameWindow(master=tk_root)
    try:
        yield made
    finally:
        made.close()


def test_a_fresh_window_already_has_a_position_of_tks_choosing(unshown_window) -> None:
    """Measured rather than assumed, and it corrected a claim I had written.

    An unplaced window is not at "no position": Tk gives a fresh toplevel one
    of its own — ``(5, 38)`` on this build. So ``position()`` answering
    something is **not** evidence that anything placed the window, and a test
    that checked placement by asking whether a position existed would pass
    without the placement code being called at all.

    The tests below therefore move to distinctive coordinates and check those.
    """
    where = unshown_window.position()
    assert where is not None
    assert where != Point(340, 240)  # the place the next test moves it to


def test_moving_the_window_puts_it_where_it_was_told(unshown_window) -> None:
    unshown_window.move_to(Point(340, 240))
    assert unshown_window.position() == Point(340, 240)


def test_a_negative_position_survives_the_trip_through_tk(unshown_window) -> None:
    """The measurement this whole item turns on, asserted through the real
    toolkit rather than against a format string.

    A window on the display at ``(-949, -1440)`` has a negative origin, and
    the tidy way of writing that in a geometry string means somewhere else
    entirely.
    """
    unshown_window.move_to(Point(-909, -1400))
    assert unshown_window.position() == Point(-909, -1400)


def test_moving_twice_ends_at_the_second_place(unshown_window) -> None:
    unshown_window.move_to(Point(100, 100))
    unshown_window.move_to(Point(-3469, -1400))
    assert unshown_window.position() == Point(-3469, -1400)


def test_the_placement_decision_reaches_the_window(unshown_window) -> None:
    """The seam end to end: a reader, a decision, a window that moved.

    One test, because the join is one thing. Which position the decision
    produces is `test_placement.py`'s business.
    """

    class Anchor(object):
        def read(self):
            return Rect(-949, -1440, 2560, 1440)

    where = placement_for(Anchor(), MAIN_DISPLAY, unshown_window.pixel_size)
    unshown_window.move_to(where)
    assert unshown_window.position() == where


def test_a_window_with_no_anchor_still_gets_placed(unshown_window) -> None:
    """The degraded path reaches the window too, rather than leaving it
    wherever the toolkit felt like putting it."""
    from terminal_game.shell.placement import no_anchor

    where = placement_for(no_anchor(), MAIN_DISPLAY, unshown_window.pixel_size)
    unshown_window.move_to(where)

    assert unshown_window.position() == where
    assert where == centred_on(MAIN_DISPLAY, unshown_window.pixel_size)


def test_moving_a_closed_window_is_refused(unshown_window) -> None:
    unshown_window.close()
    with pytest.raises(RuntimeError):
        unshown_window.move_to(Point(10, 10))


def test_a_closed_window_has_no_position(unshown_window) -> None:
    unshown_window.move_to(Point(10, 10))
    unshown_window.close()
    assert unshown_window.position() is None


def test_placing_the_window_does_not_show_it(unshown_window) -> None:
    """Section 1.6: the default suite puts no window on the user's screen.

    Moving a withdrawn window must not map it — that would put a window on
    somebody's desk every time this file runs.
    """
    unshown_window.move_to(Point(200, 200))
    assert not unshown_window.is_on_screen()
