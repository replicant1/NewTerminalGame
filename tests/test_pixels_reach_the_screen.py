"""Does anything this program draws actually arrive on the screen?

**Two tests, and which of them fails tells you where the fault is.**

``test_a_plain_canvas_reaches_the_screen`` is the control. It is twenty lines
of Tk owing nothing to this project: a canvas, one filled rectangle, one
capture. If it fails, the toolkit cannot draw and no application code is
implicated.

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
"""

from __future__ import annotations

import sys
import tkinter

import pytest

from terminal_game.presentation import palette
from terminal_game.shell.game import build_game
from tests import pixels

pytestmark = pytest.mark.needs_window

#: The blue a wall is drawn in. Asserting on this rather than on "not white"
#: means the test is satisfied by *the game's own ink* and not by a window
#: manager's chrome, a wallpaper, or a neighbouring window.
WALL_BLUE = (0x21, 0x21, 0xDE)


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

    def drop(which):
        handle = booked.pop(which, None)
        if handle is not None:
            cancel(handle)

    def once():
        drop("watchdog")
        try:
            results["why"] = pixels.capture(widget, path)
        finally:
            close()

    def expire():
        drop("shot")
        close()

    booked["shot"] = schedule(settle_ms, once)
    booked["watchdog"] = schedule(watchdog_ms, expire)
    root.mainloop()


@pytest.fixture(autouse=True)
def _needs_a_screen():
    if sys.platform != "darwin":
        pytest.skip("screencapture is macOS; this asserts pixels, not behaviour")


class TestTheScreen:
    def test_a_plain_canvas_reaches_the_screen(self, tk_root, tmp_path):
        """The control: Tk alone, no project code, one unmissable rectangle.

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
        canvas.create_rectangle(50, 50, 350, 520,
                                fill="#%02x%02x%02x" % WALL_BLUE, outline="")
        top.deiconify()

        def shut():
            if top.winfo_exists():
                top.destroy()
            tk_root.quit()          # leave the loop; the root is shared

        _drive(tk_root, top.after, top.after_cancel, shut, results, canvas, shot)

        if results.get("why"):
            pytest.skip("could not photograph the window: %s" % results["why"])

        counts = pixels.histogram(shot)
        assert not pixels.blank(counts), (
            "a plain Tk canvas with a solid rectangle on it photographed as "
            "one flat colour: the toolkit is mapping windows without painting "
            "them, and no application code is implicated"
        )
        assert pixels.near(counts, WALL_BLUE) > 0, (
            "the rectangle's own colour is nowhere in the capture"
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

        if results.get("why"):
            pytest.skip("could not photograph the window: %s" % results["why"])

        counts = pixels.histogram(shot)
        assert not pixels.blank(counts), (
            "the game's window photographed as one flat colour — it drew "
            "nothing. Every other test passes on this, because they read what "
            "Tk was told rather than what reached the screen"
        )
        assert pixels.near(counts, WALL_BLUE) > 0, (
            "no wall ink in the capture: the maze did not arrive on the screen"
        )
