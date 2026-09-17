"""WI-16b — does the assembled game *place* its window, or merely know how?

WI-14 landed complete, tested and green with the placement never wired: a
finished ``placement.py``, a working ``GameWindow.move_to``, tests for both —
and **no call site**. The game opened at Tk's default corner. WI-14b added the
call. This file is the guard that would have caught it, and that will catch it
if it is ever lost again.

**No test can catch an absent call site by testing the things on either side
of it.** ``test_placement.py`` tests the arithmetic alone;
``test_window_placement.py`` tests the join through a window the test built.
Both pass, and neither can know whether the assembled game ever asks.

Where the call actually sits, measured on WI-14b
------------------------------------------------

``Game.place()`` is called from **``run_game`` and nowhere else**, between
``start()`` and ``show()``. Measured::

    build_game(...) + start()   ->  window at (5, 38)   — Tk's default, unplaced
    an explicit place()         ->  window at (556, 206) — what placement_for says

So a headless journey through ``build_game`` and ``start()`` **cannot** see
whether anybody calls ``place``: the only caller is the one function that puts
a real window on the screen. **The instance is fixed and the class is not** —
so this file guards it three ways, and only one of them is the end-to-end run:

1. **Behaviour, in the default suite** — ``place()`` really moves the window to
   the coordinates ``placement_for`` computes.
2. **The call site, in the default suite** — ``run_game`` really calls it,
   checked by reading the source with ``ast``, the same technique
   ``tools/layer_rule.py`` uses and for the same reason: *a sentence remembers
   what was true once and nothing re-runs it.* **This is the one that catches
   an absent call site**, and it runs by default.
3. **The whole chain, behind ``needs_window``** — ``run_game`` on a real
   window, which is the only way to exercise the real call site for real.

The trap, which is why none of this asserts "it has a position"
---------------------------------------------------------------

**A fresh Tk toplevel already has a position.** The first one here is at
``(5, 38)``; a second on the same root cascades elsewhere. So a test asserting
that the window has a position, or that its geometry parses, or that it is not
at the origin, passes with no placement code having run at all — and a test
pinning the default would depend on how many windows the suite built first.

Every assertion below therefore does one of two things: compares against the
coordinates ``placement_for`` computes, or watches the position **change**.
*A getter answering is not evidence a setter ran.*

**This does not make WIN-4 met**, and nothing here should be read as saying so.
The reader is ``NoAnchor``, which follows nothing, so the window is centred on
the main display rather than appearing beside whatever the player was last
looking at. The route is still an open question with the user (S-2, human item
4). What is under test is that the game *asks and uses the answer*.
"""

from __future__ import annotations

import ast
import inspect
import textwrap

import pytest

from terminal_game.shell import game as game_module
from terminal_game.shell import placement
from terminal_game.shell.game import build_game

#: What the *first* fresh Tk toplevel reports before anybody places it,
#: measured on this machine. **Not used as an expected value anywhere**, and
#: deliberately not asserted against: a second toplevel on the same root
#: cascades to (150, ...), so a test pinning this number would depend on how
#: many windows the suite happened to build first. It is here as the
#: documented reason the guards below watch the position *change* rather than
#: compare it to a constant.
TK_FIRST_TOPLEVEL_CORNER = placement.Point(5, 38)


def window_position(game):
    """Where the window has actually asked to be, read from its own geometry."""
    return placement.position_in_geometry(game.window._root.wm_geometry())


def expected_point(game):
    """What ``placement_for`` says for this game's display and window size."""
    widget = game.window.surface.widget
    display = placement.Rect(
        0, 0, widget.winfo_screenwidth(), widget.winfo_screenheight()
    )
    return placement.placement_for(
        placement.no_anchor(), display, game.window.pixel_size
    )


class StubAnchor(object):
    """An anchor reader answering with a rectangle the test chose.

    Deliberately not the real one. WIN-4's general case is an open question
    with the user and the shipped reader follows nothing, so what is under
    test here is whether the game **asks** and whether it **uses the answer**
    — not whether the desktop can be read. It also counts, so "asked" and
    "used" can be told apart.
    """

    def __init__(self, rect):
        self.rect = rect
        self.asked = 0

    def read(self):
        # `read`, not `anchor`. `anchor_from` swallows every exception
        # broadly and deliberately, so a reader with the wrong shape is
        # indistinguishable from one that found nothing — it silently
        # centres. I wrote `anchor` first and got five green-looking
        # fallbacks instead of five errors.
        self.asked += 1
        return self.rect


@pytest.fixture
def game(tk_root, draw):
    """A built, started game on a two-square board. Never shown."""
    made = build_game(master=tk_root, seed=0, maze=draw("..", at=(9, 14)))
    made.start()
    try:
        yield made
    finally:
        made.stop()
        made.window.close()


@pytest.fixture
def anchored(tk_root, draw):
    """A game whose anchor the test supplies, via WI-14c's seam."""
    built = {}

    def build(rect=placement.Rect(300, 400, 900, 700)):
        reader = StubAnchor(rect)
        made = build_game(
            master=tk_root,
            seed=0,
            maze=draw("..", at=(9, 14)),
            anchor_reader=reader,
        )
        made.start()
        built["game"] = made
        return made, reader

    yield build
    made = built.get("game")
    if made is not None:
        made.stop()
        made.window.close()


class TestTheGameAsksAndUsesTheAnswer:
    """What WI-14c's seam makes testable: the anchor is read and obeyed.

    Without an injectable reader none of this could live in the default
    suite, because plan 1.6 forbids the default suite from querying the
    desktop — and a guard that does not run by default is how the placement
    defect survived in the first place.
    """

    def test_the_game_asks_for_an_anchor(self, anchored):
        game, reader = anchored()
        game.place()
        assert reader.asked >= 1, (
            "the assembled game never asked for an anchor: placement.py can "
            "be complete and tested and still never be called"
        )

    def test_the_window_goes_beside_the_anchor_it_was_given(self, anchored):
        rect = placement.Rect(300, 400, 900, 700)
        game, _ = anchored(rect)
        game.place()
        assert window_position(game) == placement.below_and_right_of(rect)

    def test_a_different_anchor_puts_it_somewhere_different(self, anchored):
        # Catches asking and then ignoring the reply, which would pass the
        # "did it ask?" test on its own.
        rect = placement.Rect(1000, 900, 400, 300)
        game, _ = anchored(rect)
        game.place()
        assert window_position(game) == placement.below_and_right_of(rect)

    def test_it_really_is_below_and_to_the_right(self, anchored):
        # WIN-4 in the requirement's own words.
        rect = placement.Rect(300, 400, 900, 700)
        game, _ = anchored(rect)
        game.place()
        where = window_position(game)
        assert where.x > rect.x
        assert where.y > rect.y

    def test_two_different_anchors_do_not_give_the_same_answer(self, anchored):
        # The guard: if placement ignored the anchor entirely and always
        # centred, every test above that supplies one would still pass.
        first, _ = anchored(placement.Rect(300, 400, 900, 700))
        first.place()
        one = window_position(first)
        first.stop()
        first.window.close()
        second, _ = anchored(placement.Rect(1000, 900, 400, 300))
        second.place()
        assert window_position(second) != one


class TestPlacingActuallyMovesTheWindow:
    """The mechanism: ``place()`` carries `placement_for`'s answer to the window."""

    def test_the_window_ends_up_where_placement_said(self, game):
        wanted = expected_point(game)
        game.place()
        assert window_position(game) == wanted

    def test_place_returns_the_point_it_used(self, game):
        assert game.place() == expected_point(game)

    def test_placing_actually_moves_it(self, game):
        # The guard that makes every assertion here mean something: *a getter
        # answering is not evidence a setter ran.* A window has a position
        # before anybody places it, so the test has to watch the position
        # change, not merely find one.
        before = window_position(game)
        game.place()
        assert window_position(game) != before

    def test_an_unplaced_game_is_not_where_placement_says(self, game):
        # The defect WI-14 shipped, stated without depending on what Tk's
        # default happens to be: `start()` does not place, so a started game
        # is somewhere other than where `placement_for` puts it.
        #
        # Deliberately not asserted as "== (5, 38)". That is the *first*
        # toplevel's default; a second one on the same root cascades to
        # (150, ...), so pinning the number would make this test depend on
        # how many windows the suite happened to build first.
        assert window_position(game) != expected_point(game)

    def test_placing_does_not_disturb_the_size(self, game):
        # A geometry string carrying WxH would silently overrule WIN-2.
        game.place()
        assert game.window.requested_size == (400, 570)

    def test_placing_leaves_the_window_off_the_screen(self, game):
        game.place()
        assert not game.window.is_on_screen()

    def test_placing_twice_is_harmless(self, game):
        game.place()
        once = window_position(game)
        game.place()
        assert window_position(game) == once


def _calls_within(function) -> "set":
    """Every ``x.name()`` attribute call made in a function's own body."""
    source = textwrap.dedent(inspect.getsource(function))
    found = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            found.add(node.func.attr)
    return found


class TestTheCallSiteExists:
    """The guard that catches an absent call site, in the default suite.

    Read out of the source rather than exercised, because the only caller is
    ``run_game`` and ``run_game`` shows a real window. The layer rule is
    checked the same way and for the same stated reason.
    """

    def test_run_game_calls_place(self):
        assert "place" in _calls_within(game_module.run_game), (
            "run_game does not call place(): placement.py can be complete, "
            "tested and entirely dead, which is exactly what WI-14 shipped"
        )

    def test_run_game_places_before_it_shows(self):
        # WI-6's show() says placement happens immediately before it. A
        # window placed after being shown is a window the player sees jump.
        source = inspect.getsource(game_module.run_game)
        assert source.index(".place()") < source.index(".show()")

    def test_the_detector_would_notice_if_the_call_were_missing(self):
        # A control, so the two tests above cannot pass vacuously: a function
        # that genuinely does not call place must come back without it.
        # `build_game` is such a function — measured: start() leaves the
        # window at Tk's default.
        assert "place" not in _calls_within(game_module.build_game)

    def test_the_detector_finds_the_calls_that_are_there(self):
        # And the other direction: it really is reading run_game's body.
        assert {"start", "show", "run"} <= _calls_within(game_module.run_game)


@pytest.mark.needs_window
class TestTheWholeChainOnARealWindow:
    """``run_game`` for real — the only way to exercise the real call site.

    Excluded from the default suite. Section 1.5 in full: ``run_game``'s own
    ``watchdog_ms`` closes the window unconditionally, so the loop has an exit
    scheduled before it is entered and cannot leave a window on the desk.
    """

    def test_the_real_entry_point_runs_and_reaps_itself(self, tk_root):
        # What this can honestly observe, and no more: `run_game` maps a
        # window, returns rather than hanging, and leaves nothing open. The
        # window's position cannot be read afterwards because the window is
        # gone by then — **the call site itself is covered by the static
        # guard above**, which is why that guard is in the default suite and
        # this is not pretending to duplicate it.
        from terminal_game.shell.game import run_game

        played = run_game(master=tk_root, seed=0, watchdog_ms=400)
        assert not played.window.is_open
        assert not played.timer_is_running

    def test_the_window_is_placed_while_it_is_up(self, tk_root, draw):
        # The one thing the static guard cannot show: that the call, on a
        # real mapped window, actually lands the window where placement said.
        # Driven by hand rather than through run_game so the position can be
        # read while the window still exists.
        made = build_game(master=tk_root, seed=0, maze=draw("..", at=(9, 14)))
        try:
            made.start()
            unplaced = window_position(made)
            wanted = expected_point(made)
            made.place()
            made.window.show()
            seen = window_position(made)
            assert seen == wanted
            assert seen != unplaced
            assert made.window.is_on_screen()
        finally:
            made.stop()
            made.window.close()
