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


class ACallbackThatFellOverTest(unittest.TestCase):
    """Measured on this machine: Tk catches, prints and carries on.

    ``docs/findings/WI-3-tk-window-probe.md`` records the measurement. Left
    alone it would mean a session that fell over looked exactly like a session
    that ended, which is the opposite of what the Shell's seam promises. These
    pin the bookkeeping that puts it right; the half that needs a real window
    is measured by ``tools/probe_tk_window.py --fail``.
    """

    def setUp(self):
        self.toolkit = TkToolkit()

    def test_nothing_is_pending_to_begin_with(self):
        self.assertIsNone(self.toolkit.pending_callback_exception)

    def test_a_failed_callback_is_remembered(self):
        failure = ValueError("the collaborator fell over")

        self.toolkit.note_callback_exception(ValueError, failure, None)

        self.assertIs(failure, self.toolkit.pending_callback_exception)

    def test_the_first_failure_is_the_one_kept(self):
        # Reaping the window may provoke more noise; the failure that started
        # it is the one worth reporting.
        first = ValueError("the collaborator fell over")
        second = OSError("and then the window went")

        self.toolkit.note_callback_exception(ValueError, first, None)
        self.toolkit.note_callback_exception(OSError, second, None)

        self.assertIs(first, self.toolkit.pending_callback_exception)

    def test_noting_a_failure_without_a_window_does_not_itself_raise(self):
        self.toolkit.note_callback_exception(ValueError, ValueError("x"), None)

        self.assertIsNotNone(self.toolkit.pending_callback_exception)


if __name__ == "__main__":
    unittest.main()
