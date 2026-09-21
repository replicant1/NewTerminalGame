"""Does anything this program draws actually arrive on the screen?

**Two tests, and which of them fails tells you where the fault is.**

``test_a_plain_canvas_reaches_the_screen`` is the control. It is twenty lines
of Tk owing nothing to this project: a canvas, block glyphs drawn with
``create_text``, one capture. If it fails, the toolkit cannot draw and no
application code is implicated.

**Glyphs rather than a rectangle, deliberately.** The game's ink arrives only
ever through ``create_text``; a control that filled a rectangle would pass on a
build that can fill and cannot draw a glyph, and the pair would then blame the
application for a toolkit that had failed at the very primitive the check
depends on.

``test_the_game_reaches_the_screen`` is the check. If the control passes and
this fails, the fault is ours.

Section 7 of the plan asks for exactly this pairing — *"a guard needs a
control"*, because a guard that catches something invisible passes when it
finds nothing. A capture test without a control is the purest form of that:
photograph the wrong rectangle, or photograph nothing at all, and it reports
success forever.

Both are ``needs_window``: they put a real window on the screen, so ground
rule 1.6 keeps them out of the default suite. Run them deliberately:

    .venv/bin/python -m pytest -m needs_window -q

**Two numbers decide both verdicts, and only one of the questions about them
is open.** :func:`pixels.blank`'s threshold and :func:`pixels.near`'s tolerance
are pure functions of a colour count — ``tests/test_pixels.py`` exercises both
directions of each in the default suite, with no screen involved, and that is
where to look for what a tolerance of 24 actually admits.

What **cannot** be settled until something on this machine paints is whether
those numbers are the right ones *for a real maze capture*: whether thin
antialiased box-drawing strokes on black clear 2 % non-dominant colour, and how
much of the wall blue survives the Retina colour profile. **Re-check both the
first time either test goes green**, because a threshold tuned only against
failure is a threshold tuned against one example.
"""

from __future__ import annotations

import sys
import tkinter

import pytest

from terminal_game.presentation import palette
from terminal_game.shell.game import build_game
from tests import pixels

pytestmark = pytest.mark.needs_window

#: The blue a wall is drawn in, taken from the palette rather than repeated
#: here: that module exists so a colour lives in exactly one place, and a
#: duplicate would make a palette edit fail this test with "the maze did not
#: arrive on the screen".
#:
#: Asserting on the game's own ink, rather than on "not white", means the test
#: cannot be satisfied by a window manager's chrome, a wallpaper, or a
#: neighbouring window.
WALL_BLUE = tuple(int(palette.WALL[i:i + 2], 16) for i in (1, 3, 5))


def _drive(root, schedule, cancel, close, results, widget, path,
           settle_ms=900, watchdog_ms=9000):
    """Let the loop run, photograph from inside it, then take the window down.

    ``settle_ms`` is not superstition: a window that has just been mapped has
    not necessarily been composited, and a capture taken in the same turn of
    the loop photographs the desktop behind it.

    The watchdog is plan section 1.5 — a test that maps a window must have an
    exit that does not depend on the thing it is testing working.

    **Whichever path runs cancels the other.** These are scheduled on the
    session's shared interpreter, and a pending ``after`` outlives the widget
    that scheduled it — the same fact ``_on_window_closed`` in the game exists
    to deal with. Left booked, this watchdog fires in the middle of the *next*
    ``needs_window`` test and quits that test's event loop for it.
    """
    booked = {}  # type: dict

    def once():
        try:
            results["why"] = pixels.capture(widget, path)
        finally:
            close()

    booked["shot"] = schedule(settle_ms, once)
    booked["watchdog"] = schedule(watchdog_ms, close)
    try:
        root.mainloop()
    finally:
        # **After the loop, never inside it.** Cancelling the watchdog at the
        # top of the shot callback would leave the capture and the close --
        # the only two steps that can fail -- with no independent exit at all.
        # A close() that raises is swallowed by Tk's callback reporter, the
        # loop keeps turning, and in the game's case the 143 ms beat keeps
        # rebooking itself: the run hangs with a window on somebody's desk.
        for handle in booked.values():
            try:
                cancel(handle)
            except Exception:       # already fired, or the widget is gone
                pass


@pytest.fixture(autouse=True)
def _needs_a_screen():
    if sys.platform != "darwin":
        pytest.skip("screencapture is macOS; this asserts pixels, not behaviour")


class TestTheScreen:
    def test_a_plain_canvas_reaches_the_screen(self, tk_root, tmp_path):
        """The control: Tk alone, no project code, unmissable glyphs.

        If this fails, nothing below it means anything — the toolkit is not
        drawing, and no amount of correct application code would show.
        """
        shot = tmp_path / "control.bmp"
        results = {}  # type: dict
        # A Toplevel on the session's root, never a second Tk(): this build
        # can crash on a second interpreter in one process.
        top = tkinter.Toplevel(tk_root)
        top.title("pixel control")
        canvas = tkinter.Canvas(top, width=400, height=570,
                                background=palette.GROUND,
                                highlightthickness=0, borderwidth=0)
        canvas.pack()
        # **Glyphs, not a rectangle.** The game's wall ink arrives only ever
        # through ``create_text`` — every per-cell rectangle in the surface is
        # filled with the ground. A control that filled a rectangle would pass
        # on a build that can fill and cannot draw glyphs, and then the pair
        # would blame the application for a toolkit that had failed at exactly
        # the primitive the check depends on.
        # **Full blocks, not box-drawing.** ``═`` is two thin bars in an
        # otherwise empty cell: six rows of it put roughly 2 % ink on the
        # canvas, which is the same order as ``blank()``'s own threshold, so
        # the control could fail on a toolkit that was drawing correctly. A
        # false failure of the *control* is the worst verdict this pair can
        # give — it says "Tk cannot draw" about a Tk that can, and makes the
        # check unreadable. U+2588 fills its cell, so the ink is above the
        # threshold by construction rather than by a font metric nobody here
        # can measure.
        for row in range(6):
            canvas.create_text(
                200, 60 + row * 80, text="████████", fill=palette.WALL,
                font=("Menlo", 48), anchor="center",
            )
        top.deiconify()

        def shut():
            # Never destroy the session root: it is shared, and later tests
            # need the interpreter it owns. Leave the loop instead.
            if top.winfo_exists():
                top.destroy()
            tk_root.quit()

        _drive(tk_root, top.after, top.after_cancel, shut, results, canvas, shot)

        why = results.get("why")
        if why is not None and why.environmental:
            pytest.skip("could not photograph the window: %s" % why.why)
        assert why is None, (
            "the window was never photographable: %s. That is not an "
            "environment problem and must not skip — a window that is not on "
            "the screen is the defect this test exists to catch" % why.why
            if why is not None else ""
        )

        counts = pixels.histogram(shot)
        assert not pixels.blank(counts), (
            "a plain Tk canvas with box-drawing glyphs on it photographed as "
            "one flat colour: the toolkit is mapping windows without painting "
            "them, and no application code is implicated"
        )
        assert pixels.near(counts, WALL_BLUE) > 0, (
            "the glyphs' own colour is nowhere in the capture"
        )

    def test_the_game_reaches_the_screen(self, tk_root, tmp_path):
        """The check: the real game, shown the way the entry point shows it.

        A maze fills most of the board and its walls are drawn in
        :data:`WALL_BLUE`, so a frame that arrived has that ink in it. This is
        the assertion no other test in the suite can make, and the one that
        would have caught a blank window.
        """
        shot = tmp_path / "game.bmp"
        results = {}  # type: dict
        game = build_game(master=tk_root, seed=1)
        game.start()
        game.place()
        game.window.show()
        try:
            _drive(tk_root, game.window.after, game.window.cancel,
                   game.window.close, results,
                   game.window.surface.widget, shot)
        finally:
            game.stop()
            tk_root.quit()

        why = results.get("why")
        if why is not None and why.environmental:
            pytest.skip("could not photograph the window: %s" % why.why)
        assert why is None, (
            "the window was never photographable: %s. That is not an "
            "environment problem and must not skip — a window that is not on "
            "the screen is the defect this test exists to catch" % why.why
            if why is not None else ""
        )

        counts = pixels.histogram(shot)
        assert not pixels.blank(counts), (
            "the game's window photographed as one flat colour — it drew "
            "nothing. Every other test passes on this, because they read what "
            "Tk was told rather than what reached the screen"
        )
        assert pixels.near(counts, WALL_BLUE) > 0, (
            "no wall ink in the capture: the maze did not arrive on the screen"
        )
