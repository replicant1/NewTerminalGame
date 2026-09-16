"""The Tk adapter, checked without ever creating a window.

Importing Tk is harmless; a window exists only once ``create_window`` has been
called, and nothing in this file calls it.  What can be checked here is that
the adapter answers the whole of the Shell's seam, that its key translation
loses nothing, and that a freshly built adapter genuinely has no window
behind it.
"""

import unittest

from terminal_game.shell.tk_toolkit import TkToolkit, key_press_from_event
from terminal_game.shell.toolkit import KeyPress, Toolkit


class TkKeyEvent:
    """Shaped like the event Tk hands to a ``<Key>`` binding."""

    def __init__(self, keysym, char):
        self.keysym = keysym
        self.char = char


class TheAdapterAnswersTheSeamTest(unittest.TestCase):
    def test_it_implements_every_part_of_the_toolkit_seam(self):
        # If any abstract method were missing, constructing it would raise.
        toolkit = TkToolkit()

        self.assertIsInstance(toolkit, Toolkit)
        self.assertEqual(frozenset(), TkToolkit.__abstractmethods__)


class TheKeyTranslationTest(unittest.TestCase):
    def test_an_arrow_keeps_its_name_and_types_nothing(self):
        self.assertEqual(
            KeyPress(keysym="Up", char=""),
            key_press_from_event(TkKeyEvent("Up", "")),
        )

    def test_a_letter_keeps_both_its_name_and_its_character(self):
        self.assertEqual(
            KeyPress(keysym="q", char="q"),
            key_press_from_event(TkKeyEvent("q", "q")),
        )

    def test_the_shifted_letter_is_distinguishable_from_the_plain_one(self):
        # CTRL-4 asks for q in either case, so the two must not be conflated
        # here; telling them apart, or not, is WI-9's business.
        self.assertEqual(
            KeyPress(keysym="Q", char="Q"),
            key_press_from_event(TkKeyEvent("Q", "Q")),
        )


class AFreshAdapterHasNoWindowTest(unittest.TestCase):
    """Constructing the adapter must not reach the window server."""

    def setUp(self):
        self.toolkit = TkToolkit()

    def test_it_has_nothing_to_run_an_event_loop_for(self):
        with self.assertRaises(RuntimeError):
            self.toolkit.run_event_loop()

    def test_it_has_nothing_to_schedule_against(self):
        with self.assertRaises(RuntimeError):
            self.toolkit.schedule_once(143, lambda: None)

    def test_taking_away_a_window_it_never_made_is_harmless(self):
        self.toolkit.destroy_window()
        self.toolkit.stop_event_loop()
        self.toolkit.cancel_scheduled("no-such-timer")


if __name__ == "__main__":
    unittest.main()
