"""WI-14 — where the game's window goes (WIN-4, assumption A2).

**No window, no toolkit and no permission prompt anywhere in this file.**
The query is a collaborator and every test supplies one, which is what lets
the whole of the policy be asserted without anything appearing on anybody's
screen.  The real query lives in ``terminal_game/shell/tk_anchor.py`` and is
exercised once, deliberately, by ``tools/probe_anchor_query.py``; what it
returned on this machine is in ``docs/findings/WI-14-anchor-query.md``.

That split is the point of A2.  A stub cannot prove the absence of a
permission dialog, so the tests do not pretend to — they own the arithmetic
and the policy, and the findings document owns the one thing only a real run
can say.
"""

from __future__ import annotations

import unittest

from terminal_game.shell.anchor import (
    ANCHOR_OFFSET,
    FALLBACK_POSITION,
    Anchor,
    ScreenBounds,
    WindowAnchor,
    brought_onto_screen,
    no_anchor,
)
from terminal_game.shell.toolkit import PixelSize, ScreenPosition
from terminal_game.shell.window_owner import DEFAULT_WINDOW_POSITION

#: A window the size WI-2 measured for Menlo 16pt: 40 x 30 cells.
GAME_WINDOW = PixelSize(width=400, height=570)

#: A roomy screen, so a placement that lands off it did so on purpose.
BIG_SCREEN = ScreenBounds(width=2560, height=1440)


class CountingQuery:
    """A query that records how often it was asked.

    The thing being counted is the point: a privileged query is a chance of
    a dialog, and WIN-4 needs it once at start-up and never again.
    """

    def __init__(self, answer=None, raises=None):
        self.answer = answer
        self.raises = raises
        self.calls = 0

    def __call__(self):
        self.calls += 1
        if self.raises is not None:
            raise self.raises
        return self.answer


def anchored_at(x, y, screen=BIG_SCREEN):
    return Anchor(position=ScreenPosition(x=x, y=y), screen=screen)


class GivenAnAnchorTheWindowGoesBelowAndToTheRight(unittest.TestCase):
    """WIN-4's first half: the placement is the anchor plus the offset."""

    def test_the_placement_is_the_anchor_plus_the_offset(self):
        anchor = WindowAnchor(CountingQuery(anchored_at(100, 200)))

        self.assertEqual(
            ScreenPosition(100 + ANCHOR_OFFSET.x, 200 + ANCHOR_OFFSET.y),
            anchor.position_for(GAME_WINDOW),
        )

    def test_the_offset_is_below_and_to_the_right_of_the_anchor(self):
        """Not beside it, not above it — the requirement says which way."""
        placed = WindowAnchor(
            CountingQuery(anchored_at(100, 200))
        ).position_for(GAME_WINDOW)

        self.assertGreater(placed.x, 100)
        self.assertGreater(placed.y, 200)

    def test_a_different_offset_is_honoured(self):
        anchor = WindowAnchor(
            CountingQuery(anchored_at(100, 200)),
            offset=ScreenPosition(7, 11),
        )

        self.assertEqual(
            ScreenPosition(107, 211), anchor.position_for(GAME_WINDOW)
        )


class WithNothingToAnchorToItUsesTheFixedOffset(unittest.TestCase):
    """A2's fallback, and the three ways the query can give us nothing."""

    def test_a_query_that_sees_nothing_falls_back(self):
        anchor = WindowAnchor(CountingQuery(None))

        self.assertEqual(FALLBACK_POSITION, anchor.position_for(GAME_WINDOW))

    def test_a_query_that_raises_falls_back_rather_than_raising(self):
        """A game that will not start because it could not place its window
        is a worse outcome than a game in an unremarkable place.
        """
        anchor = WindowAnchor(CountingQuery(raises=OSError("no display")))

        self.assertEqual(FALLBACK_POSITION, anchor.position_for(GAME_WINDOW))

    def test_what_the_query_raised_is_kept_rather_than_swallowed(self):
        failure = OSError("no display")
        anchor = WindowAnchor(CountingQuery(raises=failure))

        anchor.position_for(GAME_WINDOW)

        self.assertIs(failure, anchor.failure)

    def test_a_query_that_answers_with_nonsense_falls_back(self):
        """Anything that is not an :class:`Anchor` is nothing seen."""
        anchor = WindowAnchor(CountingQuery("somewhere over there"))

        self.assertEqual(FALLBACK_POSITION, anchor.position_for(GAME_WINDOW))

    def test_the_default_query_sees_nothing_deliberately(self):
        """``no_anchor`` is the honest answer for another application's
        window on a machine where that needs a permission nobody granted.
        """
        self.assertIsNone(no_anchor())
        self.assertEqual(
            FALLBACK_POSITION, WindowAnchor().position_for(GAME_WINDOW)
        )

    def test_the_fallback_is_wi_3_s_own_default_and_not_a_second_spelling(self):
        """Two positions meaning "somewhere safe" is the shape of mistake
        the first-lander rule exists for.  There is one, and WI-3 owns it.
        """
        self.assertIs(DEFAULT_WINDOW_POSITION, FALLBACK_POSITION)

    def test_a_custom_fallback_is_honoured(self):
        anchor = WindowAnchor(no_anchor, fallback=ScreenPosition(5, 6))

        self.assertEqual(
            ScreenPosition(5, 6), anchor.position_for(GAME_WINDOW)
        )


class TheQueryIsAttemptedOnceAndNeverAgain(unittest.TestCase):
    """A repeated privileged query is a repeated chance of a dialog."""

    def test_asking_where_the_window_goes_twice_queries_once(self):
        query = CountingQuery(anchored_at(100, 200))
        anchor = WindowAnchor(query)

        anchor.position_for(GAME_WINDOW)
        anchor.position_for(GAME_WINDOW)
        anchor.position_for(PixelSize(10, 10))

        self.assertEqual(1, query.calls)

    def test_the_answer_is_the_same_every_time(self):
        anchor = WindowAnchor(CountingQuery(anchored_at(100, 200)))

        first = anchor.position_for(GAME_WINDOW)

        self.assertEqual(first, anchor.position_for(GAME_WINDOW))

    def test_a_query_that_failed_is_not_retried(self):
        query = CountingQuery(raises=OSError("no display"))
        anchor = WindowAnchor(query)

        anchor.position_for(GAME_WINDOW)
        anchor.position_for(GAME_WINDOW)

        self.assertEqual(1, query.calls)

    def test_nothing_is_asked_until_somebody_asks_where_the_window_goes(self):
        query = CountingQuery(anchored_at(100, 200))
        anchor = WindowAnchor(query)

        self.assertFalse(anchor.asked)
        self.assertEqual(0, query.calls)

        anchor.position_for(GAME_WINDOW)

        self.assertTrue(anchor.asked)


class AWindowPastTheEdgeIsBroughtBack(unittest.TestCase):
    """WIN-4's purpose: *so it always lands somewhere visible*.

    An anchor near the bottom-right corner plus an offset is exactly how a
    window ends up half off the screen, and it is the common case rather
    than a strange one — people work in the corner.
    """

    def test_a_placement_past_the_right_edge_comes_back(self):
        screen = ScreenBounds(width=1000, height=1000)
        anchor = WindowAnchor(CountingQuery(anchored_at(980, 10, screen)))

        placed = anchor.position_for(PixelSize(400, 200))

        self.assertEqual(1000 - 400, placed.x)

    def test_a_placement_past_the_bottom_edge_comes_back(self):
        screen = ScreenBounds(width=1000, height=1000)
        anchor = WindowAnchor(CountingQuery(anchored_at(10, 980, screen)))

        placed = anchor.position_for(PixelSize(400, 200))

        self.assertEqual(1000 - 200, placed.y)

    def test_the_whole_window_fits_on_the_screen_afterwards(self):
        screen = ScreenBounds(width=1000, height=1000)
        anchor = WindowAnchor(CountingQuery(anchored_at(999, 999, screen)))
        size = PixelSize(400, 200)

        placed = anchor.position_for(size)

        self.assertGreaterEqual(placed.x, 0)
        self.assertGreaterEqual(placed.y, 0)
        self.assertLessEqual(placed.x + size.width, screen.width)
        self.assertLessEqual(placed.y + size.height, screen.height)

    def test_a_window_that_fits_is_not_moved(self):
        screen = ScreenBounds(width=1000, height=1000)
        anchor = WindowAnchor(CountingQuery(anchored_at(100, 100, screen)))

        self.assertEqual(
            ScreenPosition(100 + ANCHOR_OFFSET.x, 100 + ANCHOR_OFFSET.y),
            anchor.position_for(PixelSize(400, 200)),
        )

    def test_a_window_bigger_than_the_screen_goes_to_the_corner(self):
        """No good answer exists; the top-left at least shows the title and
        the first rows rather than the middle of the picture.
        """
        placed = brought_onto_screen(
            ScreenPosition(300, 300),
            PixelSize(4000, 3000),
            ScreenBounds(width=1000, height=1000),
        )

        self.assertEqual(ScreenPosition(0, 0), placed)

    def test_a_negative_placement_comes_back_to_the_corner(self):
        placed = brought_onto_screen(
            ScreenPosition(-50, -70),
            PixelSize(400, 200),
            ScreenBounds(width=1000, height=1000),
        )

        self.assertEqual(ScreenPosition(0, 0), placed)


class TheFallbackIsNotClamped(unittest.TestCase):
    """Because a query that saw nothing told us nothing about the screen.

    Clamping the fallback would need a screen size we do not have, and
    inventing one is worse than using a fixed position chosen to be safe.
    """

    def test_the_fallback_comes_back_exactly_as_it_was_given(self):
        anchor = WindowAnchor(no_anchor, fallback=ScreenPosition(9000, 9000))

        self.assertEqual(
            ScreenPosition(9000, 9000), anchor.position_for(GAME_WINDOW)
        )

    def test_the_real_fallback_is_comfortably_on_any_ordinary_screen(self):
        """120, 120 with a 400 x 570 window needs 520 x 690, which is less
        than any display this game could be run on.
        """
        self.assertLess(
            FALLBACK_POSITION.x + GAME_WINDOW.width, 1024
        )
        self.assertLess(
            FALLBACK_POSITION.y + GAME_WINDOW.height, 768
        )


class TheValuesAreWhatTheyClaimToBe(unittest.TestCase):
    def test_the_offset_is_a_little_below_and_to_the_right(self):
        self.assertGreater(ANCHOR_OFFSET.x, 0)
        self.assertGreater(ANCHOR_OFFSET.y, 0)
        self.assertLess(ANCHOR_OFFSET.x, 100)
        self.assertLess(ANCHOR_OFFSET.y, 100)

    def test_an_anchor_carries_the_screen_it_was_found_on(self):
        """Without it there is nothing to bring a window back onto."""
        anchor = anchored_at(1, 2, ScreenBounds(3, 4))

        self.assertEqual(ScreenPosition(1, 2), anchor.position)
        self.assertEqual(ScreenBounds(3, 4), anchor.screen)


class NothingHereTouchesTheToolkit(unittest.TestCase):
    """The rule that keeps a permission dialog out of the suite.

    WI-10's rule 5 guards that no Tk interpreter is ever constructed by the
    suite, over the whole tree.  This is the narrower statement for this
    item: the module holding the policy does not name the toolkit at all, so
    there is no path from a test to the screen even by accident.
    """

    def test_the_policy_module_does_not_import_the_toolkit(self):
        import ast
        import os

        import terminal_game.shell.anchor as module

        with open(module.__file__, "r", encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), filename=os.path.basename(module.__file__))

        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])

        self.assertNotIn("tkinter", imported)


if __name__ == "__main__":
    unittest.main()
