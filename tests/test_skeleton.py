"""WI-7 — the walking skeleton: the join, and ``q``.

**Almost all of this runs with nothing on the screen.** A ``GameWindow`` is
withdrawn until :meth:`show` is called, so a whole window can be built,
painted and closed without a person seeing anything — which is what lets the
join be asserted in the default suite. Exactly one test here maps a real
window, and it is marked ``needs_window``.

**What this file owns is the join and nothing else.** That the composer draws
the right picture is WI-4b's, and it is pinned against the specimen there.
That a canvas shows what it was given is WI-5's. That Tk delivers a key event
to a binding at all is **WI-6's**, and its own ``needs_window`` test already
proves it — including the trap that ``event_generate`` on a withdrawn
toplevel is accepted and delivers nothing. So this file asserts what is left:
that the field the composer produced is the field that reached the glass,
cell for cell, and that when a ``q`` arrives the window closes.
"""

from __future__ import annotations

from typing import List

import pytest

from terminal_game.presentation import frame as frame_module
from terminal_game.presentation import surface as surface_module
from terminal_game.presentation.field import Field
from terminal_game.presentation.metrics import COLUMNS, ROWS
from terminal_game.shell import skeleton as skeleton_module
from terminal_game.shell.skeleton import (
    FIXTURE_GHOST,
    FIXTURE_PLAYER,
    FIXTURE_STATUS_TEXT,
    build_skeleton,
    fixture_frame,
    fixture_maze,
    fixture_status_row,
    quit_on_key,
    run_skeleton,
)
from terminal_game.domain.structure import check


class FakeKeyEvent(object):
    """What Tk hands a binding, reduced to the one attribute that matters."""

    def __init__(self, keysym: str) -> None:
        self.keysym = keysym


# --------------------------------------------------------------------------
# The fixtures are legal, so nothing below is testing nonsense
# --------------------------------------------------------------------------


def test_the_fixture_maze_is_a_legal_maze() -> None:
    """A guard. A malformed fixture would make every test here meaningless.

    It is the specification's own picture, so it had better satisfy MAZE-3,
    MAZE-5 and MAZE-6 — and WI-1's checker is what says so, rather than my
    reading of it.
    """
    report = check(fixture_maze())
    assert report.is_sound, report.describe()


def test_the_fixture_is_the_picture_the_specification_prints(specimen) -> None:
    """The fixture really is the specimen, not something that resembles it.

    Worth pinning because the value of showing this particular maze is that a
    person can hold the window up against the requirements document. If the
    two drifted apart, the window would still look fine and the comparison
    would quietly stop meaning anything.
    """
    assert fixture_maze() == specimen.maze
    assert FIXTURE_PLAYER == specimen.player
    assert FIXTURE_GHOST == specimen.ghost
    assert FIXTURE_STATUS_TEXT == specimen.status_row


def test_the_fixture_status_row_is_forty_cells_of_cyan() -> None:
    """SCRN-6's colour, on a fixture WI-12 will supersede.

    WI-7 composes none of row 29's *content* — the text is a copied literal —
    but it has to be the right width and the right colour or ``compose_frame``
    would refuse it and the window would be wrong.
    """
    from terminal_game.presentation import palette

    row = fixture_status_row()
    assert len(row) == COLUMNS
    assert {cell.colour for cell in row} == {palette.STATUS}
    assert "".join(cell.glyph for cell in row).rstrip() == FIXTURE_STATUS_TEXT.rstrip()


# --------------------------------------------------------------------------
# The join — the one thing WI-7 owns
# --------------------------------------------------------------------------


def test_the_composed_frame_reaches_the_surface_unaltered(tk_root) -> None:
    """**The item's whole purpose**, and the only place it is asserted.

    Not "the picture looks right" — WI-4b owns that against the specimen — but
    that *this* field, the one the composer produced, is the one on the glass.
    Every cell of all 40 x 30, because a join that dropped one row or shifted
    one column would still produce something plausible.
    """
    window = build_skeleton(master=tk_root)
    try:
        composed = fixture_frame()

        for row in range(ROWS):
            assert window.surface.shown_row(row) == composed.row_text(row), (
                "row {} differs".format(row)
            )
        for column, row, cell in composed.cells():
            assert window.surface.shown_cell(column, row) == cell, (
                "cell ({}, {}) differs".format(column, row)
            )
    finally:
        window.close()


def test_the_join_test_would_notice_a_difference(tk_root) -> None:
    """The control: the comparison above must be capable of disagreeing.

    A ``shown_row`` that returned the field it was handed, or a comparison
    over an empty range, would make the join test pass on anything. Comparing
    the painted window against a *blank* field shows the comparison has teeth
    — without breaking, changing or re-running any production code.
    """
    window = build_skeleton(master=tk_root)
    try:
        blank = Field()
        differing = [
            row
            for row in range(ROWS)
            if window.surface.shown_row(row) != blank.row_text(row)
        ]
        assert len(differing) == 30, (
            "the painted window should differ from a blank field on every row"
        )
    finally:
        window.close()


def test_building_the_skeleton_puts_nothing_on_the_screen(tk_root) -> None:
    """Section 1.6: the default suite must never put a window on the screen.

    ``build_skeleton`` paints the frame but does not show the window, which is
    what lets every test above run where a person would see nothing.
    """
    window = build_skeleton(master=tk_root)
    try:
        assert window.is_open
        assert not window.is_on_screen()
    finally:
        window.close()


# --------------------------------------------------------------------------
# ``q`` ends it
# --------------------------------------------------------------------------


def test_a_q_closes_the_window(tk_root) -> None:
    """CTRL-4, on the handler rather than through Tk's dispatch.

    That a key event reaches a binding is WI-6's and is pinned by its own
    ``needs_window`` test. What arrives here is what WI-7 decides to do about
    it.
    """
    for keysym in ("q", "Q"):
        window = build_skeleton(master=tk_root)
        try:
            quit_on_key(window)(FakeKeyEvent(keysym))
            assert not window.is_open, "{!r} did not close the window".format(keysym)
        finally:
            window.close()


def test_no_other_key_closes_the_window(tk_root) -> None:
    """CTRL-5, and the control that makes the test above mean something.

    If every key closed the window, ``q`` closing it would prove nothing. The
    arrows are in here deliberately: they translate to real intents, so this
    also shows the skeleton reads a move and drops it rather than failing to
    recognise it.
    """
    window = build_skeleton(master=tk_root)
    try:
        handler = quit_on_key(window)
        for keysym in ("Up", "Down", "Left", "Right", "a", "Z", "Escape",
                       "F1", "space", "Shift_L", "1"):
            handler(FakeKeyEvent(keysym))
            assert window.is_open, "{!r} closed the window".format(keysym)
    finally:
        window.close()


def test_the_window_is_closed_by_the_key_and_not_by_luck(tk_root) -> None:
    """One window, many harmless keys, then a ``q`` — in that order.

    Separating the two tests above leaves open that the window was already
    closing for some other reason. Here the same window survives eleven keys
    and then dies on the twelfth.
    """
    window = build_skeleton(master=tk_root)
    try:
        handler = quit_on_key(window)
        for keysym in ("Up", "Down", "Left", "Right", "a", "Z", "Escape",
                       "F1", "space", "Shift_L", "1"):
            handler(FakeKeyEvent(keysym))
        assert window.is_open

        handler(FakeKeyEvent("q"))
        assert not window.is_open
    finally:
        window.close()


def test_closing_the_window_ends_the_loop_with_nothing_on_the_screen(tk_root) -> None:
    """WIN-5's mechanism, exercised without showing anything.

    ``mainloop`` runs on a withdrawn root, ``after`` fires inside it and
    ``close`` ends it — measured for WI-6, and it is what lets the loop be
    exercised in the default suite at all. A hang here would hang the suite,
    so this is also the cheapest early warning that the exit path still works.
    """
    window = build_skeleton(master=tk_root)
    window.after(10, window.close)
    window.run()

    assert not window.is_open


# --------------------------------------------------------------------------
# One vocabulary, not three
# --------------------------------------------------------------------------


def test_the_entry_point_the_composer_and_the_painter_share_one_field() -> None:
    """An identity guard across all three, after WI-4b.

    The skeleton is the first thing to hold the composer and the painter at
    once, so it is the first place they could be pointed at different types.
    Behaviour tests on each half would pass throughout such a drift; only an
    identity assertion catches it.
    """
    assert skeleton_module.Field is frame_module.Field
    assert skeleton_module.Field is surface_module.Field
    assert isinstance(fixture_frame(), surface_module.Field)


# --------------------------------------------------------------------------
# The one test that puts a real window on a real screen
# --------------------------------------------------------------------------


@pytest.mark.needs_window
class TestOnTheRealScreen:
    """Excluded from the default suite. Section 1.5 applies without exception.

    Run it deliberately, and **under a deadline outside pytest** — a
    pytest-internal timeout does not help when a hang is inside ``mainloop``:

        .venv/bin/python -m pytest -q -m needs_window
    """

    def test_the_skeleton_opens_paints_and_closes_itself(self, tk_root) -> None:
        """The whole slice on a real window, ending by itself.

        The watchdog is the only thing that presses anything, because nobody
        is here to press ``q``. It closes the window unconditionally, so the
        failure mode of every assertion below is a closed window and a red
        test rather than something left on the user's desk.
        """
        window = run_skeleton(master=tk_root, watchdog_ms=700)

        # run() returned, which is the thing that could have hung.
        assert not window.is_open

    def test_what_was_on_the_screen_was_the_composed_frame(self, tk_root) -> None:
        """The join again, but this time on a window that was really mapped.

        Checked *while* it is up, from inside an ``after`` callback, because
        once it closes there is nothing left to ask.
        """
        from terminal_game.shell.skeleton import build_skeleton as build

        window = build(master=tk_root)
        composed = fixture_frame()
        seen = {}  # type: dict

        def look_then_close() -> None:
            seen["on_screen"] = window.is_on_screen()
            seen["rows"] = [window.surface.shown_row(r) for r in range(ROWS)]
            seen["size"] = window.pixel_size
            window.close()

        window.show()
        window.after(400, look_then_close)
        window.after(3000, window.close)  # belt and braces
        window.run()

        assert not window.is_open
        assert seen.get("on_screen") is True, "the window never reached the screen"
        assert seen["rows"] == [composed.row_text(r) for r in range(ROWS)]
        assert seen["size"] == (400, 570)
