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

from termgame import controls, screen as screen_module
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

    def test_the_fallback_covers_every_style_a_real_picture_emits(self):
        # WI-9 note: this used to be asserted against the stand-in renderer's
        # published vocabulary, which is gone with the stand-ins. The
        # stronger claim is against what the real renderer actually puts on
        # the screen for a real game: if theme.py cannot be read at all, the
        # fallback must still paint the whole picture rather than half of it.
        import random

        from termgame import rules, view

        frame = view.render(rules.new_game(random.Random(11)))
        emitted = set()
        for row in frame.styles():
            emitted.update(row)
        unknown = sorted(emitted - set(screen_module.FALLBACK_PALETTE))
        self.assertEqual(
            [],
            unknown,
            "the fallback would paint %s in the default colour" % unknown,
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

        from termgame import rules, view

        palette = screen_module.resolve_palette()
        state = rules.new_game(random.Random(7))
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


class TheRealThemeTest(unittest.TestCase):
    """The adapter and WI-3's theme, now that both are here.

    Self-arming in the same way as the test above: these skip on a branch
    where WI-3 has not landed and turn themselves on when it has.
    """

    def setUp(self):
        try:
            from termgame import theme  # noqa: F401
        except ImportError:
            self.skipTest("WI-3's theme has not landed on this branch yet")

    def test_the_adapter_paints_with_the_colours_the_pure_theme_names(self):
        # Not the fallback: the numbers come from theme.py, so changing one
        # after human check H6 never touches the adapter.
        from termgame import theme

        palette = screen_module.resolve_palette()
        for name, style in theme.STYLES.items():
            self.assertEqual(
                style.colour,
                palette[name].colour,
                "%s: the adapter is not reading theme.py" % name,
            )
            self.assertEqual("bold" in style.attributes, palette[name].bold, name)
            self.assertEqual("dim" in style.attributes, palette[name].dim, name)

    def test_the_two_halves_agree_on_which_attributes_exist(self):
        from termgame import theme

        self.assertEqual(theme.ATTRIBUTE_NAMES, screen_module.ATTRIBUTE_NAMES)

    def test_the_fallback_still_covers_every_identifier_the_theme_names(self):
        # The fallback is only reached if theme.py cannot be read at all, but
        # a stale one would then paint half the picture in the default
        # colour, silently.
        from termgame import theme

        for name in theme.STYLE_NAMES:
            self.assertIn(name, screen_module.FALLBACK_PALETTE, name)

    def test_a_style_the_theme_does_not_name_still_falls_back(self):
        palette = screen_module.resolve_palette()
        screen = screen_module.Screen(FakeWindow(3, 4), {STYLE_DEFAULT: 7})
        screen.paint(a_picture(["abcd", "efgh", "ijkl"], style="invented"))
        self.assertNotIn("invented", palette)


class _StubCurses(object):
    """Just enough of ``curses`` to watch what ``build_attributes`` asks for.

    ``build_attributes`` is the last place a colour number exists as a
    *number*: after it, every style is an opaque curses attribute and the
    colour cannot be read back out. So this is the only seam at which "the
    status line is painted cyan" can be asserted at all without a terminal,
    and before WI-13 nothing stood here.
    """

    A_BOLD = 1 << 8
    A_DIM = 1 << 9

    class error(Exception):
        pass

    def __init__(self, coloured=True):
        self._coloured = coloured
        self.pairs = []          # (pair number, foreground, background)
        self.started = 0
        self.defaults = 0

    def start_color(self):
        self.started += 1

    def use_default_colors(self):
        self.defaults += 1

    def has_colors(self):
        return self._coloured

    def init_pair(self, number, foreground, background):
        self.pairs.append((number, foreground, background))

    def color_pair(self, number):
        return number << 16

    def colour_asked_for(self, pair_number):
        for number, foreground, _background in self.pairs:
            if number == pair_number:
                return foreground
        raise AssertionError("no colour pair %d was ever allocated" % pair_number)


class BuildAttributesTest(unittest.TestCase):
    """What colour number actually reaches curses — SCRN-3, SCRN-4, SCRN-5, SCRN-6.

    ``TheRealThemeTest`` above asserts that the palette the adapter resolves
    carries the theme's colours. That is half the chain. This is the other
    half: the numbers in that palette are the numbers handed to
    ``curses.init_pair``, so a translation step that dropped or transposed a
    colour would be caught here rather than by a person looking at a screen.
    """

    def setUp(self):
        self.real_curses = screen_module.curses
        self.stub = _StubCurses()
        screen_module.curses = self.stub

    def tearDown(self):
        screen_module.curses = self.real_curses

    def _colours_by_style(self, palette):
        """``{style: the colour number curses was asked for}``.

        Recovered through the attribute each style ended up with, so it maps
        the style the *caller* named to the colour *curses* received, and a
        transposition between two styles would show up as swapped values.
        """
        attributes = screen_module.build_attributes(palette)
        colours = {}
        for style, attribute in attributes.items():
            pair_number = attribute >> 16
            if pair_number:
                colours[style] = self.stub.colour_asked_for(pair_number)
        return colours

    def test_the_theme_s_own_colours_are_the_ones_handed_to_curses(self):
        from termgame import theme

        colours = self._colours_by_style(screen_module.resolve_palette())
        for name, style in theme.STYLES.items():
            self.assertEqual(
                style.colour,
                colours.get(name),
                "the %s style reaches curses as %r, not as the theme's %r"
                % (name, colours.get(name), style.colour),
            )

    def test_the_status_line_reaches_curses_as_cyan(self):
        """SCRN-6, end to end as far as a test without a terminal can go."""
        from termgame import theme

        colours = self._colours_by_style(screen_module.resolve_palette())
        self.assertEqual(51, colours[theme.STYLE_STATUS])
        self.assertEqual(
            (0, 5, 5),
            _rgb_levels(colours[theme.STYLE_STATUS]),
            "the colour curses is asked for on the status line is not cyan",
        )

    def test_each_colour_gets_its_own_pair_against_the_default_background(self):
        # -1 is "whatever the terminal's own background is", which is what
        # use_default_colors buys and is why the game does not paint a
        # rectangle of black over the user's window.
        self._colours_by_style(screen_module.resolve_palette())
        self.assertEqual(1, self.stub.started)
        self.assertEqual(1, self.stub.defaults)
        numbers = [number for number, _fg, _bg in self.stub.pairs]
        self.assertEqual(sorted(numbers), sorted(set(numbers)))
        for _number, _fg, background in self.stub.pairs:
            self.assertEqual(-1, background)

    def test_bold_and_dim_survive_the_translation_alongside_the_colour(self):
        # SCRN-4's "dim" and SCRN-5's "bright" are carried in the same int as
        # the colour pair, so a translation that lost one would be invisible.
        palette = {
            "plain": screen_module.StyleSpec(colour=33),
            "loud": screen_module.StyleSpec(colour=178, bold=True),
            "quiet": screen_module.StyleSpec(colour=51, dim=True),
        }
        attributes = screen_module.build_attributes(palette)
        self.assertFalse(attributes["plain"] & self.stub.A_BOLD)
        self.assertFalse(attributes["plain"] & self.stub.A_DIM)
        self.assertTrue(attributes["loud"] & self.stub.A_BOLD)
        self.assertFalse(attributes["loud"] & self.stub.A_DIM)
        self.assertTrue(attributes["quiet"] & self.stub.A_DIM)
        self.assertFalse(attributes["quiet"] & self.stub.A_BOLD)

    def test_a_terminal_with_no_colour_still_gets_a_playable_picture(self):
        # The one way this can fail, and it must cost colour and not the game.
        screen_module.curses = self.stub = _StubCurses(coloured=False)
        attributes = screen_module.build_attributes(screen_module.resolve_palette())
        self.assertEqual([], self.stub.pairs)
        self.assertTrue(attributes)


def _rgb_levels(index):
    """``index`` as ``(red, green, blue)`` on 0..5 in the xterm colour cube."""
    if not 16 <= index <= 231:
        raise ValueError("%r is not in the 6x6x6 colour cube" % (index,))
    offset = index - 16
    return (offset // 36, (offset // 6) % 6, offset % 6)


class TheFallbackPaletteTest(unittest.TestCase):
    """The fallback is a copy of the theme, and copies go stale.

    It is only reached when ``theme.py`` cannot be imported at all, which is
    to say almost never — which is exactly why a colour changed in one place
    and not the other would sit there unnoticed until the day it mattered.
    """

    def test_the_fallback_asks_for_the_same_colour_as_the_theme_for_every_style(self):
        from termgame import theme

        for name in theme.STYLE_NAMES:
            if name == STYLE_DEFAULT:
                # Deliberately different: the theme names the terminal's own
                # foreground by number, the fallback says "leave it alone".
                self.assertIsNone(screen_module.FALLBACK_PALETTE[name].colour)
                continue
            self.assertEqual(
                theme.STYLES[name].colour,
                screen_module.FALLBACK_PALETTE[name].colour,
                "the fallback's %s has drifted from theme.py" % name,
            )

    def test_the_fallback_carries_the_same_bold_and_dim_as_the_theme(self):
        from termgame import theme

        for name in theme.STYLE_NAMES:
            spec = screen_module.FALLBACK_PALETTE[name]
            attributes = theme.STYLES[name].attributes
            self.assertEqual("bold" in attributes, spec.bold, name)
            self.assertEqual("dim" in attributes, spec.dim, name)


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
