"""The curses adapter, against a terminal that lives in memory.

The obligations under test are WI-2's, from the implementation plan:

* a frame is presented in a single pass rather than cell by cell;
* the terminal is restored after a normal exit, after an exception, and
  after a signal;
* a key read returns promptly when a key is waiting and returns nothing when
  the timeout expires;
* echo is off;
* a terminal smaller than 40 x 30 fails loudly rather than drawing a
  truncated picture.
"""

from __future__ import annotations

import unittest

from terminalgame.screen.curses_adapter import (
    CursesScreen,
    FATAL_SIGNALS,
    TerminalSession,
    _timeout_in_milliseconds,
)
from terminalgame.screen.port import Colour, Frame, Key, ScreenTooSmall

from tests.fake_terminal import (
    CursesError,
    FakeCurses,
    FakeLocale,
    FakeSignals,
)


def open_session(**overrides):
    """A session over a fake terminal, with everything a test may want."""
    curses_module = overrides.pop("curses_module", None) or FakeCurses()
    signals = overrides.pop("signal_module", None) or FakeSignals()
    session = TerminalSession(curses_module=curses_module,
                              signal_module=signals,
                              locale_module=FakeLocale(),
                              on_fatal_signal=overrides.pop(
                                  "on_fatal_signal", lambda number: None),
                              **overrides)
    return session, curses_module, signals


def picture(width=40, height=30):
    """A frame with something recognisable in it, in several colours."""
    frame = Frame(width, height)
    frame.put_text(0, 0, "╔" + "═" * (width - 2) + "╗", Colour.WALL)
    for row in range(1, height - 2):
        frame.put(0, row, "║", Colour.WALL)
        frame.put(width - 1, row, "║", Colour.WALL)
        frame.put(2, row, "▪", Colour.DOT)
    frame.put(4, 3, "█", Colour.PLAYER)
    frame.put(6, 3, "▓", Colour.GHOST)
    frame.put_text(0, height - 2, "╚" + "═" * (width - 2) + "╝", Colour.WALL)
    frame.put_text(0, height - 1, " score 0    arrows, q quits".ljust(width),
                   Colour.STATUS)
    return frame


class PresentTest(unittest.TestCase):
    """SCRN-7 and caution C9: the whole frame, in one visible update."""

    def setUp(self):
        self.session, self.curses, self.signals = open_session()
        self.screen = self.session.open()
        self.addCleanup(self.session.close)
        self.window = self.curses.window

    def test_the_whole_frame_reaches_the_glass(self):
        frame = picture()
        self.screen.present(frame)
        self.assertEqual(frame.text_rows(), self.window.text_rows())

    def test_the_player_sees_one_complete_update_not_a_frame_being_painted(self):
        frame = picture()
        self.screen.present(frame)

        # One refresh, carrying the finished picture. Had the adapter
        # presented cell by cell there would be 1 200 partial pictures here,
        # and the player would watch the frame being painted (SCRN-7).
        self.assertEqual(1, len(self.window.presented))
        self.assertEqual(frame.text_rows(), self.window.presented[0])

    def test_each_present_is_exactly_one_update(self):
        frame = picture()
        for _ in range(5):
            self.screen.present(frame)
        self.assertEqual(5, len(self.window.presented))

    def test_a_second_present_rewrites_every_cell_and_wipes_out_debris(self):
        """Caution C9, stated as its consequence.

        An actor glyph is three columns wide and overwrites a column of the
        square next door. Debris on the glass is exactly what that leaves.
        A pass that wrote only the cells that had changed since last time
        would leave it there; a pass that writes the whole frame cannot.
        """
        frame = picture()
        self.screen.present(frame)

        self.window.scribble(3, 5, "XX")
        self.window.scribble(12, 0, "!!!!")
        self.assertNotEqual(frame.text_rows(), self.window.text_rows())

        self.screen.present(frame)   # the identical frame, nothing changed
        self.assertEqual(frame.text_rows(), self.window.text_rows())
        self.assertEqual(frame.text_rows(), self.window.presented[-1])

    def test_the_bottom_right_cell_is_drawn_and_not_lost_to_the_corner(self):
        frame = Frame(40, 30)
        frame.put_text(0, 29, "." * 40, Colour.STATUS)
        self.screen.present(frame)
        self.assertEqual("." * 40, self.window.text_rows()[29])
        self.assertEqual(".", self.window.text_rows()[29][39])

    def test_colours_reach_the_glass_and_differ_between_the_actors(self):
        frame = picture()
        self.screen.present(frame)
        player = self.window.attribute_at(4, 3)
        ghost = self.window.attribute_at(6, 3)
        wall = self.window.attribute_at(0, 1)
        dot = self.window.attribute_at(2, 1)
        status = self.window.attribute_at(1, 29)
        self.assertEqual(5, len({player, ghost, wall, dot, status}),
                         "the five named colours must reach the terminal as "
                         "five different attributes")

    def test_a_frame_of_the_wrong_size_is_refused_rather_than_half_drawn(self):
        with self.assertRaises(ValueError):
            self.screen.present(Frame(20, 10))
        self.assertEqual([], self.window.presented)


class ReadKeyTest(unittest.TestCase):

    def setUp(self):
        self.session, self.curses, self.signals = open_session()
        self.screen = self.session.open()
        self.addCleanup(self.session.close)
        self.window = self.curses.window

    def test_a_waiting_key_comes_back_at_once_without_using_up_the_timeout(self):
        self.window.press(self.curses.KEY_UP)
        started = self.curses.now

        key = self.screen.read_key(5.0)

        self.assertEqual(Key.UP, key)
        self.assertEqual(started, self.curses.now,
                         "a key that was already waiting must not cost the "
                         "caller any of its timeout")

    def test_an_empty_keyboard_costs_exactly_the_timeout_and_returns_nothing(self):
        started = self.curses.now

        self.assertIsNone(self.screen.read_key(0.14))

        self.assertAlmostEqual(started + 0.14, self.curses.now, places=6)

    def test_a_key_due_part_way_through_comes_back_when_it_is_due(self):
        self.window.press(self.curses.KEY_LEFT, at=self.curses.now + 0.05)

        key = self.screen.read_key(0.14)

        self.assertEqual(Key.LEFT, key)
        self.assertAlmostEqual(0.05, self.curses.now, places=6)

    def test_a_key_due_after_the_timeout_does_not_come_back_early(self):
        self.window.press(self.curses.KEY_RIGHT, at=self.curses.now + 1.0)

        self.assertIsNone(self.screen.read_key(0.14))
        self.assertAlmostEqual(0.14, self.curses.now, places=6)

        # ... and is still there to be read on a later pass.
        self.assertEqual(Key.RIGHT, self.screen.read_key(2.0))

    def test_each_arrow_arrives_as_its_own_named_key(self):
        expected = [(self.curses.KEY_UP, Key.UP),
                    (self.curses.KEY_DOWN, Key.DOWN),
                    (self.curses.KEY_LEFT, Key.LEFT),
                    (self.curses.KEY_RIGHT, Key.RIGHT)]
        for code, key in expected:
            self.window.press(code)
            self.assertEqual(key, self.screen.read_key(1.0))

    def test_q_and_shift_q_arrive_as_printable_keys_carrying_their_character(self):
        self.window.press(ord("q"))
        self.assertEqual(Key.printable("q"), self.screen.read_key(1.0))
        self.window.press(ord("Q"))
        self.assertEqual(Key.printable("Q"), self.screen.read_key(1.0))

    def test_a_function_key_arrives_as_something_the_loop_can_discard(self):
        self.window.press(self.curses.KEY_F1)
        key = self.screen.read_key(1.0)
        self.assertFalse(key.is_arrow)
        self.assertFalse(key.is_printable)

    def test_a_timeout_of_zero_polls_and_returns_immediately(self):
        started = self.curses.now
        self.assertIsNone(self.screen.read_key(0.0))
        self.assertEqual(started, self.curses.now)

    def test_an_overdue_tick_polls_rather_than_waiting_for_ever(self):
        """A negative timeout means the tick is already late.

        curses reads a negative timeout as "block until a key arrives", which
        would hand the whole game over to the keyboard. The fake terminal
        refuses a negative timeout outright, so this test would fail loudly
        if the adapter ever passed one down.
        """
        started = self.curses.now
        self.assertIsNone(self.screen.read_key(-0.02))
        self.assertEqual(started, self.curses.now)

    def test_the_timeout_is_carried_through_in_milliseconds(self):
        self.assertEqual(140, _timeout_in_milliseconds(0.14))
        self.assertEqual(0, _timeout_in_milliseconds(0.0))
        self.assertEqual(0, _timeout_in_milliseconds(-3.0))
        self.assertEqual(1, _timeout_in_milliseconds(0.0006))
        with self.assertRaises(TypeError):
            _timeout_in_milliseconds(None)

    def test_a_fresh_timeout_is_honoured_on_every_read(self):
        # WI-11 recomputes the timeout each pass; the adapter must not cache
        # the first one it was given.
        self.assertIsNone(self.screen.read_key(0.10))
        self.assertAlmostEqual(0.10, self.curses.now, places=6)
        self.assertIsNone(self.screen.read_key(0.03))
        self.assertAlmostEqual(0.13, self.curses.now, places=6)


class RawModeTest(unittest.TestCase):
    """CTRL-5 and SCRN-7: nothing echoes, and the cursor never shows."""

    def test_the_session_turns_echo_off_and_hides_the_cursor(self):
        session, curses_module, _ = open_session()
        self.assertTrue(curses_module.echo_on)
        self.assertTrue(curses_module.cursor_visible)

        session.open()
        try:
            self.assertFalse(curses_module.echo_on,
                             "typing must not reach the maze (CTRL-5)")
            self.assertFalse(curses_module.line_buffered,
                             "keys must arrive one at a time, unbuffered")
            self.assertFalse(curses_module.cursor_visible,
                             "the text cursor is never visible (SCRN-7)")
            self.assertTrue(curses_module.window.keypad_on,
                            "arrow keys must arrive decoded")
        finally:
            session.close()

    def test_a_terminal_that_cannot_hide_its_cursor_still_plays(self):
        curses_module = FakeCurses(cursor_settable=False)
        session, _, _ = open_session(curses_module=curses_module)
        screen = session.open()
        try:
            self.assertIsInstance(screen, CursesScreen)
            self.assertFalse(curses_module.echo_on)
        finally:
            session.close()

    def test_a_terminal_with_no_colours_still_plays_in_plain_text(self):
        curses_module = FakeCurses(colours=False)
        session, _, _ = open_session(curses_module=curses_module)
        screen = session.open()
        try:
            frame = picture()
            screen.present(frame)
            self.assertEqual(frame.text_rows(), curses_module.window.text_rows())
        finally:
            session.close()


class RestoreTheTerminalTest(unittest.TestCase):
    """Caution C10 — the terminal comes back on every exit path."""

    def test_after_a_normal_exit(self):
        session, curses_module, _ = open_session()
        with session:
            self.assertTrue(curses_module.in_curses_mode)
        self.assertTrue(curses_module.is_restored, curses_module.describe())

    def test_after_an_unhandled_exception(self):
        session, curses_module, _ = open_session()
        with self.assertRaises(ZeroDivisionError):
            with session:
                raise ZeroDivisionError("something in the game went wrong")
        self.assertTrue(curses_module.is_restored, curses_module.describe())

    def test_after_a_keyboard_interrupt(self):
        session, curses_module, _ = open_session()
        with self.assertRaises(KeyboardInterrupt):
            with session:
                raise KeyboardInterrupt()
        self.assertTrue(curses_module.is_restored, curses_module.describe())

    def test_after_a_terminating_signal(self):
        died_of = []
        session, curses_module, signals = open_session(
            on_fatal_signal=died_of.append)
        with session:
            self.assertFalse(curses_module.is_restored)
            signals.deliver(signals.SIGTERM)
            self.assertTrue(curses_module.is_restored, curses_module.describe())
        self.assertEqual([signals.SIGTERM], died_of)
        self.assertTrue(curses_module.is_restored, curses_module.describe())

    def test_after_a_hangup(self):
        session, curses_module, signals = open_session()
        session.open()
        try:
            signals.deliver(signals.SIGHUP)
        finally:
            session.close()
        self.assertTrue(curses_module.is_restored, curses_module.describe())

    def test_the_signals_that_would_otherwise_skip_every_finally_are_handled(self):
        session, _, signals = open_session()
        with session:
            installed = set(signals.handlers)
        self.assertEqual({getattr(signals, name) for name in FATAL_SIGNALS},
                         installed)

    def test_the_player_s_own_signal_handlers_are_put_back(self):
        signals = FakeSignals()

        def the_player_s_handler(number, frame):
            pass

        signals.signal(signals.SIGTERM, the_player_s_handler)
        session, _, _ = open_session(signal_module=signals)
        with session:
            self.assertIsNot(the_player_s_handler,
                             signals.handlers[signals.SIGTERM])
        self.assertIs(the_player_s_handler, signals.handlers[signals.SIGTERM])

    def test_a_session_that_cannot_install_signal_handlers_still_runs(self):
        # `signal.signal` raises off the main thread. That is not a reason to
        # refuse to play, and the terminal still comes back by the finally.
        signals = FakeSignals(refuse=(FakeSignals.SIGTERM, FakeSignals.SIGHUP))
        session, curses_module, _ = open_session(signal_module=signals)
        with session:
            pass
        self.assertTrue(curses_module.is_restored, curses_module.describe())

    def test_closing_twice_is_harmless(self):
        session, curses_module, _ = open_session()
        session.open()
        session.close()
        session.close()
        self.assertTrue(curses_module.is_restored, curses_module.describe())
        self.assertFalse(session.is_active)

    def test_the_terminal_is_only_taken_over_once_per_session(self):
        session, curses_module, _ = open_session()
        with session:
            pass
        self.assertEqual(1, curses_module.initscr_calls)


class TooSmallTest(unittest.TestCase):
    """The window is not big enough: say so, do not draw half a maze."""

    def test_a_short_terminal_is_refused(self):
        curses_module = FakeCurses(width=40, height=24)
        session, _, _ = open_session(curses_module=curses_module)
        with self.assertRaises(ScreenTooSmall) as caught:
            session.open()
        self.assertEqual((40, 24), (caught.exception.actual_width,
                                    caught.exception.actual_height))

    def test_a_narrow_terminal_is_refused(self):
        curses_module = FakeCurses(width=39, height=30)
        session, _, _ = open_session(curses_module=curses_module)
        with self.assertRaises(ScreenTooSmall):
            session.open()

    def test_exactly_forty_by_thirty_is_enough(self):
        curses_module = FakeCurses(width=40, height=30)
        session, _, _ = open_session(curses_module=curses_module)
        with session as screen:
            self.assertEqual((40, 30), screen.size())

    def test_a_bigger_terminal_is_fine(self):
        curses_module = FakeCurses(width=120, height=40)
        session, _, _ = open_session(curses_module=curses_module)
        with session as screen:
            self.assertEqual((120, 40), screen.size())

    def test_refusing_gives_the_terminal_back_before_it_raises(self):
        curses_module = FakeCurses(width=20, height=10)
        session, _, _ = open_session(curses_module=curses_module)
        with self.assertRaises(ScreenTooSmall):
            session.open()
        self.assertTrue(curses_module.is_restored, curses_module.describe())
        self.assertFalse(session.is_active)


class FailureDuringSetUpTest(unittest.TestCase):

    def test_a_failure_after_initscr_still_gives_the_terminal_back(self):
        curses_module = FakeCurses()

        def explode():
            raise CursesError("this terminal will not stop echoing")

        curses_module.noecho = explode
        session, _, _ = open_session(curses_module=curses_module)
        with self.assertRaises(CursesError):
            session.open()
        self.assertFalse(curses_module.in_curses_mode,
                         "curses must have been shut down again")
        self.assertFalse(session.is_active)


class FrameSizedToTheScreenTest(unittest.TestCase):

    def test_new_frame_matches_the_screen_and_presents_without_complaint(self):
        curses_module = FakeCurses(width=48, height=32)
        session, _, _ = open_session(curses_module=curses_module)
        with session as screen:
            frame = screen.new_frame()
            self.assertEqual((48, 32), (frame.width, frame.height))
            frame.put_text(0, 0, "hello", Colour.STATUS)
            screen.present(frame)
            self.assertEqual("hello" + " " * 43,
                             curses_module.window.text_rows()[0])


if __name__ == "__main__":
    unittest.main()
