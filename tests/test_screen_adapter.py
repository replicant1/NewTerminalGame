"""The curses adapter, against a stand-in window.

``curses`` imports perfectly well without a terminal; what needs one is
``initscr``. So everything here that is not about entering and leaving curses
is exercised against a stand-in window object that records what it was asked
to draw. ``tests/test_curses_pty.py`` does the other half against real
ncurses in a real pseudo-terminal.

What is worth asserting here is what a stand-in can actually prove: that the
bottom-right cell is *inserted* and every other cell *written* (C1), that the
characters and attributes arriving at ncurses are the ones the picture held,
that a key code comes back unchanged and a timeout comes back as nothing, and
that no negative timeout ever reaches ncurses.
"""

import unittest

from termgame import controls, screen as screen_module, standins
from termgame.model import STYLE_DEFAULT, Cell, Frame, frame_from_rows


class FakeWindow(object):
    """A curses window that writes nothing anywhere and remembers everything."""

    def __init__(self, height=30, width=40):
        self.height = height
        self.width = width
        self.added = []      # (row, col, char, attribute) from addstr
        self.inserted = []   # ... from insstr
        self.refreshes = 0
        self.timeouts = []
        self.keys = []
        self.keypads = []

    def getmaxyx(self):
        return (self.height, self.width)

    def addstr(self, row, col, text, attribute=0):
        if row == self.height - 1 and col == self.width - 1:
            # What real ncurses does here. See C1.
            raise _CursesError("addwstr() returned ERR")
        self.added.append((row, col, text, attribute))

    def insstr(self, row, col, text, attribute=0):
        self.inserted.append((row, col, text, attribute))

    def refresh(self):
        self.refreshes += 1

    def timeout(self, milliseconds):
        self.timeouts.append(milliseconds)

    def getch(self):
        return self.keys.pop(0) if self.keys else controls.NO_KEY

    def keypad(self, on):
        self.keypads.append(on)


class _CursesError(Exception):
    pass


def a_picture(rows, style=STYLE_DEFAULT):
    return frame_from_rows(rows, style=style)


class PaintTest(unittest.TestCase):
    def setUp(self):
        self.window = FakeWindow(height=3, width=4)
        self.screen = screen_module.Screen(self.window, {STYLE_DEFAULT: 7})

    def test_every_character_of_the_picture_reaches_the_window(self):
        self.screen.paint(a_picture(["abcd", "efgh", "ijkl"]))
        written = dict(
            ((row, col), char)
            for row, col, char, _ in self.window.added + self.window.inserted
        )
        self.assertEqual(12, len(written))
        self.assertEqual("a", written[(0, 0)])
        self.assertEqual("l", written[(2, 3)])

    def test_the_bottom_right_cell_is_inserted_and_never_written(self):
        # C1: addstr at (LINES-1, COLS-1) raises addwstr() returned ERR.
        # FakeWindow raises there too, so a regression here is a test error,
        # not a silently wrong picture.
        self.screen.paint(a_picture(["abcd", "efgh", "ijkl"]))
        self.assertEqual([(2, 3, "l", 7)], self.window.inserted)
        for row, col, _, _ in self.window.added:
            self.assertNotEqual((2, 3), (row, col))

    def test_a_full_forty_by_thirty_picture_paints_without_raising(self):
        window = FakeWindow(30, 40)
        screen = screen_module.Screen(window, {STYLE_DEFAULT: 0})
        screen.paint(a_picture(["x" * 40] * 30))
        self.assertEqual(1199, len(window.added))
        self.assertEqual(1, len(window.inserted))

    def test_the_picture_is_shown_once_when_it_is_complete(self):
        self.screen.paint(a_picture(["abcd", "efgh", "ijkl"]))
        self.assertEqual(1, self.window.refreshes)

    def test_each_cell_carries_the_attribute_its_style_asks_for(self):
        screen = screen_module.Screen(
            self.window, {STYLE_DEFAULT: 7, "wall": 1024, "dot": 2048}
        )
        picture = Frame(
            tuple(
                tuple(Cell(ch, st) for ch, st in row)
                for row in [
                    [("#", "wall"), (".", "dot"), (" ", STYLE_DEFAULT), ("#", "wall")],
                    [(" ", STYLE_DEFAULT)] * 4,
                    [(" ", STYLE_DEFAULT)] * 4,
                ]
            )
        )
        screen.paint(picture)
        by_cell = dict(((r, c), a) for r, c, _, a in self.window.added)
        self.assertEqual(1024, by_cell[(0, 0)])
        self.assertEqual(2048, by_cell[(0, 1)])
        self.assertEqual(7, by_cell[(0, 2)])

    def test_a_style_the_palette_has_never_heard_of_falls_back_to_the_default(self):
        # WI-3 owns the identifier vocabulary. A disagreement between the two
        # halves must cost colour and never the picture.
        screen = screen_module.Screen(self.window, {STYLE_DEFAULT: 7})
        screen.paint(a_picture(["abcd", "efgh", "ijkl"], style="invented"))
        for _, _, _, attribute in self.window.added:
            self.assertEqual(7, attribute)

    def test_a_picture_larger_than_the_window_is_clipped_not_fatal(self):
        window = FakeWindow(height=2, width=2)
        screen = screen_module.Screen(window, {STYLE_DEFAULT: 0})
        screen.paint(a_picture(["abcd", "efgh", "ijkl"]))
        self.assertEqual(3, len(window.added))
        self.assertEqual([(1, 1, "f", 0)], window.inserted)

    def test_a_window_larger_than_the_picture_is_filled_as_far_as_it_goes(self):
        window = FakeWindow(height=5, width=8)
        screen = screen_module.Screen(window, {STYLE_DEFAULT: 0})
        screen.paint(a_picture(["ab", "cd"]))
        self.assertEqual(4, len(window.added))
        self.assertEqual([], window.inserted)


class ReadKeyTest(unittest.TestCase):
    def setUp(self):
        self.window = FakeWindow()
        self.screen = screen_module.Screen(self.window, {})

    def test_a_key_code_comes_back_exactly_as_ncurses_reported_it(self):
        self.window.keys = [controls.KEY_LEFT]
        self.assertEqual(controls.KEY_LEFT, self.screen.read_key(100))

    def test_nothing_to_report_comes_back_as_nothing(self):
        self.window.keys = []
        self.assertIsNone(self.screen.read_key(100))

    def test_the_timeout_is_passed_through_to_ncurses(self):
        self.screen.read_key(143)
        self.assertEqual([143], self.window.timeouts)

    def test_a_negative_timeout_never_reaches_ncurses(self):
        # A negative timeout means "block for ever", which would stop the
        # ghost the moment the loop ran a hair late.
        self.screen.read_key(-1)
        self.screen.read_key(-10000)
        self.assertEqual([0, 0], self.window.timeouts)

    def test_a_fractional_timeout_is_whole_milliseconds(self):
        self.screen.read_key(12.7)
        self.assertEqual([12], self.window.timeouts)

    def test_the_adapter_makes_no_decision_about_what_the_key_means(self):
        # q comes back as the code for q. What it *means* is controls.py's,
        # and that is the whole reason CTRL-4 has a test.
        self.window.keys = [ord("q")]
        self.assertEqual(ord("q"), self.screen.read_key(0))


class PaletteTest(unittest.TestCase):
    """Where the colours come from."""

    def test_without_wi_3_the_adapter_falls_back_to_its_own_table(self):
        def missing(name):
            raise ImportError(name)

        palette = screen_module.resolve_palette(missing)
        self.assertEqual(screen_module.FALLBACK_PALETTE, palette)

    def test_with_wi_3_present_the_colours_come_from_the_pure_theme(self):
        # H6 is a human perceptual check and the colours may well change
        # after it. When they do, the change must land in the pure module and
        # not here.
        class Style(object):
            def __init__(self, colour, attributes=()):
                self.colour = colour
                self.attributes = attributes

        class Theme(object):
            STYLES = {
                "default": Style(7),
                "wall": Style(21),
                "dot": Style(94, ("dim",)),
                "player": Style(11, ("bold",)),
            }

        palette = screen_module.resolve_palette(lambda name: Theme)
        self.assertEqual(21, palette["wall"].colour)
        self.assertTrue(palette["dot"].dim)
        self.assertFalse(palette["dot"].bold)
        self.assertTrue(palette["player"].bold)
        self.assertFalse(palette["wall"].dim)

    def test_a_theme_with_no_style_table_falls_back_rather_than_crashing(self):
        class Empty(object):
            pass

        self.assertEqual(
            screen_module.FALLBACK_PALETTE, screen_module.resolve_palette(lambda n: Empty)
        )

    def test_the_default_style_is_always_present_however_odd_the_theme(self):
        class Style(object):
            colour = 4
            attributes = ()

        class Theme(object):
            STYLES = {"wall": Style()}

        palette = screen_module.resolve_palette(lambda name: Theme)
        self.assertIn("default", palette)

    def test_the_fallback_knows_every_identifier_the_stand_in_emits(self):
        for style in standins.STYLE_IDS:
            self.assertIn(
                style,
                screen_module.FALLBACK_PALETTE,
                "the adapter would paint %r in the default colour" % style,
            )

    def test_only_bold_and_dim_are_ever_asked_for(self):
        # WI-3 states the attribute list is closed at these two. If a third
        # ever appears, this adapter drops it silently, so say so loudly here.
        self.assertEqual(("bold", "dim"), screen_module.ATTRIBUTE_NAMES)


class TheRealRendererTest(unittest.TestCase):
    """Self-arming: this turns on by itself the moment WI-3 is merged.

    The palette falls back to the default attribute for an identifier it does
    not know, which is the right behaviour and is also exactly how a colour
    bug hides. This test converts that into a loud failure at the moment the
    two halves meet.
    """

    def setUp(self):
        try:
            from termgame import view  # noqa: F401
        except ImportError:
            self.skipTest("WI-3's renderer has not landed on this branch yet")

    def test_every_style_the_real_renderer_emits_is_in_the_palette(self):
        import random

        from termgame import view

        palette = screen_module.resolve_palette()
        state = standins.new_game(random.Random(7))
        frame = view.render(state)
        emitted = set()
        for row in frame.styles():
            emitted.update(row)
        unknown = sorted(emitted - set(palette))
        self.assertEqual(
            [],
            unknown,
            "the renderer emits %s, which the adapter would paint in the "
            "default colour" % unknown,
        )


class CursesConstantsTest(unittest.TestCase):
    """The adapter may import curses; this checks what it relies on exists."""

    def test_the_escape_delay_setter_is_present_on_the_pinned_interpreter(self):
        import curses

        self.assertTrue(hasattr(curses, "set_escdelay"))

    def test_the_escape_delay_is_short_enough_not_to_look_like_a_freeze(self):
        # C10: ncurses otherwise waits up to a second after a bare ESC.
        self.assertLessEqual(screen_module.ESCAPE_DELAY_MS, 50)
        self.assertGreater(screen_module.ESCAPE_DELAY_MS, 0)

    def test_bold_and_dim_exist_to_map_the_two_attribute_names_onto(self):
        import curses

        self.assertNotEqual(0, curses.A_BOLD)
        self.assertNotEqual(0, curses.A_DIM)


if __name__ == "__main__":
    unittest.main()
