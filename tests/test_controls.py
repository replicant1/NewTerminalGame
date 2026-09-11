"""What a key means — CTRL-1, CTRL-4, CTRL-5.

The architecture calls this layer untestable; the implementation plan's §10.1
rules that the *decision* is not, and this is where those three requirements
are actually checked. **No terminal is attached to any of it.**

The table is asserted exhaustively rather than by sample, because CTRL-5's
"no other key does anything" is a claim about every key there is, and the only
honest way to check a claim like that is to sweep.
"""

import string
import unittest

from termgame import controls
from termgame.model import DOWN, LEFT, RIGHT, UP


class ArrowKeysTest(unittest.TestCase):
    """CTRL-1 — the four arrow keys move one square up, down, left or right."""

    def test_each_arrow_code_maps_to_its_own_direction(self):
        self.assertIs(UP, controls.command_for_key(controls.KEY_UP))
        self.assertIs(DOWN, controls.command_for_key(controls.KEY_DOWN))
        self.assertIs(LEFT, controls.command_for_key(controls.KEY_LEFT))
        self.assertIs(RIGHT, controls.command_for_key(controls.KEY_RIGHT))

    def test_the_four_arrows_map_to_four_different_directions(self):
        # A table that mapped all four to UP would satisfy the test above if
        # it were written carelessly; this one would catch it.
        mapped = [
            controls.command_for_key(code)
            for code in (
                controls.KEY_UP,
                controls.KEY_DOWN,
                controls.KEY_LEFT,
                controls.KEY_RIGHT,
            )
        ]
        self.assertEqual(4, len(set(id(d) for d in mapped)))

    def test_the_key_codes_are_the_ones_ncurses_actually_reports(self):
        # controls.py deliberately does not import curses, so these four
        # integers are copied. If ncurses ever disagreed, the arrows would
        # silently stop working and nothing else in the suite would notice.
        import curses

        self.assertEqual(curses.KEY_UP, controls.KEY_UP)
        self.assertEqual(curses.KEY_DOWN, controls.KEY_DOWN)
        self.assertEqual(curses.KEY_LEFT, controls.KEY_LEFT)
        self.assertEqual(curses.KEY_RIGHT, controls.KEY_RIGHT)
        self.assertEqual(curses.KEY_RESIZE, controls.KEY_RESIZE)
        self.assertEqual(curses.ERR, controls.NO_KEY)

    def test_an_arrow_is_reported_as_a_direction_and_not_as_a_quit(self):
        for code in controls.ARROW_KEYS:
            self.assertFalse(controls.is_quit(controls.command_for_key(code)))
            self.assertIsNotNone(
                controls.as_direction(controls.command_for_key(code))
            )


class QuitKeyTest(unittest.TestCase):
    """CTRL-4 — `q`, upper or lower case, quits at once."""

    def test_lower_case_q_quits(self):
        self.assertIs(controls.QUIT, controls.command_for_key(ord("q")))

    def test_upper_case_q_quits(self):
        self.assertIs(controls.QUIT, controls.command_for_key(ord("Q")))

    def test_quit_is_recognised_as_quit_and_carries_no_direction(self):
        command = controls.command_for_key(ord("q"))
        self.assertTrue(controls.is_quit(command))
        self.assertIsNone(controls.as_direction(command))


class EveryOtherKeyTest(unittest.TestCase):
    """CTRL-5 — no other key does anything."""

    def significant(self, code):
        return controls.command_for_key(code)

    def test_no_other_letter_does_anything(self):
        for letter in string.ascii_letters:
            if letter in "qQ":
                continue
            self.assertIsNone(
                self.significant(ord(letter)), "%r did something" % letter
            )

    def test_no_digit_does_anything(self):
        for digit in string.digits:
            self.assertIsNone(self.significant(ord(digit)), digit)

    def test_no_punctuation_does_anything(self):
        for mark in string.punctuation:
            self.assertIsNone(self.significant(ord(mark)), mark)

    def test_space_enter_tab_escape_and_backspace_do_nothing(self):
        for code in (ord(" "), 10, 13, 9, 27, 127, 8):
            self.assertIsNone(self.significant(code), code)

    def test_no_function_key_does_anything(self):
        # curses.KEY_F0 is 264; F1..F12 follow it.
        for offset in range(0, 13):
            self.assertIsNone(self.significant(264 + offset), 264 + offset)

    def test_a_resize_event_does_nothing(self):
        # The window is a fixed 40 x 30 (WIN-2); a resize is not a move and
        # is certainly not a quit.
        self.assertIsNone(self.significant(controls.KEY_RESIZE))

    def test_the_whole_of_the_key_space_holds_no_surprises(self):
        # A sweep, not a sample: exactly six codes in the entire range that
        # ncurses can report mean anything at all.
        meaningful = [
            code
            for code in range(-1, 1024)
            if controls.command_for_key(code) is not None
        ]
        self.assertEqual(
            sorted(
                [
                    controls.KEY_UP,
                    controls.KEY_DOWN,
                    controls.KEY_LEFT,
                    controls.KEY_RIGHT,
                    ord("q"),
                    ord("Q"),
                ]
            ),
            sorted(meaningful),
        )


class NoKeyTest(unittest.TestCase):
    """A timeout with nothing to report is not a key press."""

    def test_none_means_nothing(self):
        self.assertIsNone(controls.command_for_key(None))

    def test_the_no_key_sentinel_means_nothing(self):
        self.assertIsNone(controls.command_for_key(controls.NO_KEY))

    def test_a_string_from_getkey_is_not_a_key_code(self):
        # `window.getkey()` returns a string; only `getch()`'s integers are
        # key codes here, and a string must not be mistaken for one.
        self.assertIsNone(controls.command_for_key("q"))
        self.assertIsNone(controls.command_for_key("KEY_UP"))

    def test_a_bool_is_not_a_key_code(self):
        # `True == 1` in Python, so a bool that slipped through would be read
        # as the key code 1.
        self.assertIsNone(controls.command_for_key(True))
        self.assertIsNone(controls.command_for_key(False))

    def test_the_decision_is_total_and_never_raises(self):
        for code in range(-64, 2048):
            controls.command_for_key(code)


class HelperTest(unittest.TestCase):
    """The two helpers exist so the loop needs no `isinstance` of its own."""

    def test_nothing_is_neither_a_quit_nor_a_direction(self):
        self.assertFalse(controls.is_quit(None))
        self.assertIsNone(controls.as_direction(None))


if __name__ == "__main__":
    unittest.main()
