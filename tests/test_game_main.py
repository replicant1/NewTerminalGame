"""The game process that draws one frame and quits, over a fake terminal."""

from __future__ import annotations

import contextlib
import io
import unittest

from terminalgame import game_main
from terminalgame.screen.curses_adapter import TerminalSession
from terminalgame.screen.port import Colour

from tests.fake_terminal import (
    CursesError,
    FakeCurses,
    FakeLocale,
    FakeSignals,
)


def session_over(curses_module):
    def factory():
        return TerminalSession(curses_module=curses_module,
                               signal_module=FakeSignals(),
                               locale_module=FakeLocale(),
                               on_fatal_signal=lambda number: None)
    return factory


class SkeletonFrameTest(unittest.TestCase):

    def setUp(self):
        self.frame = game_main.build_skeleton_frame(40, 30)

    def test_the_frame_is_exactly_the_window_the_launcher_makes(self):
        self.assertEqual((40, 30), (self.frame.width, self.frame.height))
        rows = self.frame.text_rows()
        self.assertEqual(30, len(rows))
        self.assertTrue(all(len(row) == 40 for row in rows))

    def test_the_bottom_row_carries_the_status_line_and_the_rows_above_do_not(self):
        rows = self.frame.text_rows()
        self.assertTrue(rows[29].startswith(game_main.STATUS_LINE))
        for row in rows[:29]:
            self.assertNotIn("arrows, q quits", row)

    def test_every_colour_the_specification_names_reaches_the_frame(self):
        used = {cell.colour for _, _, cell in self.frame.cells()}
        for colour in (Colour.WALL, Colour.DOT, Colour.PLAYER,
                       Colour.GHOST, Colour.STATUS):
            self.assertIn(colour, used)

    def test_the_status_row_is_cyan_all_the_way_across(self):
        for column in range(40):
            self.assertEqual(Colour.STATUS, self.frame.cell(column, 29).colour)

    def test_it_composes_for_a_terminal_larger_than_the_minimum(self):
        frame = game_main.build_skeleton_frame(80, 40)
        self.assertEqual((80, 40), (frame.width, frame.height))
        self.assertEqual(40, len(frame.text_rows()))


class RunTest(unittest.TestCase):

    def setUp(self):
        self.curses = FakeCurses()
        self.session = TerminalSession(curses_module=self.curses,
                                       signal_module=FakeSignals(),
                                       locale_module=FakeLocale(),
                                       on_fatal_signal=lambda number: None)
        self.screen = self.session.open()
        self.addCleanup(self.session.close)
        self.window = self.curses.window
        # The terminal's own virtual clock, so that waiting for a key really
        # does use up the hold.
        self.clock = lambda: self.curses.now

    def test_one_frame_reaches_the_glass_in_one_update(self):
        game_main.run(self.screen, hold_seconds=0.3, clock=self.clock)
        self.assertEqual(1, len(self.window.presented))
        self.assertEqual(game_main.build_skeleton_frame(40, 30).text_rows(),
                         self.window.presented[0])

    def test_it_quits_on_q(self):
        self.window.press(ord("q"), at=0.05)
        ended_with = game_main.run(self.screen, hold_seconds=10.0,
                                   clock=self.clock)
        self.assertEqual("q", ended_with.character)
        self.assertLess(self.curses.now, 1.0,
                        "q must end it at once, not after the hold")

    def test_it_quits_on_shift_q(self):
        self.window.press(ord("Q"), at=0.05)
        ended_with = game_main.run(self.screen, hold_seconds=10.0,
                                   clock=self.clock)
        self.assertEqual("Q", ended_with.character)

    def test_with_nobody_at_the_keyboard_it_ends_itself_when_the_hold_runs_out(self):
        self.assertIsNone(game_main.run(self.screen, hold_seconds=0.35,
                                        clock=self.clock))
        self.assertGreaterEqual(self.curses.now, 0.35)
        self.assertLess(self.curses.now, 0.5,
                        "it must not overrun its hold by much")

    def test_other_keys_do_not_end_it(self):
        for code in (self.curses.KEY_UP, ord("x"), ord(" "),
                     self.curses.KEY_F1):
            self.window.press(code)
        self.assertIsNone(game_main.run(self.screen, hold_seconds=0.35,
                                        clock=self.clock))
        self.assertGreaterEqual(self.curses.now, 0.35)

    def test_a_hold_of_zero_draws_the_frame_and_leaves_at_once(self):
        self.assertIsNone(game_main.run(self.screen, hold_seconds=0.0,
                                        clock=self.clock))
        self.assertEqual(1, len(self.window.presented))
        self.assertEqual(0.0, self.curses.now)


class MainTest(unittest.TestCase):

    def test_a_normal_run_ends_well_and_gives_the_terminal_back(self):
        curses_module = FakeCurses()
        status = game_main.main(["--hold", "0"],
                                session_factory=session_over(curses_module))
        self.assertEqual(game_main.EXIT_OK, status)
        self.assertTrue(curses_module.is_restored, curses_module.describe())
        self.assertEqual(1, len(curses_module.window.presented))

    def test_a_window_too_small_fails_loudly_instead_of_drawing_half_a_maze(self):
        curses_module = FakeCurses(width=80, height=24)
        stderr = io.StringIO()
        status = game_main.main(["--hold", "0"],
                                session_factory=session_over(curses_module),
                                stderr=stderr)
        self.assertEqual(game_main.EXIT_SCREEN_TOO_SMALL, status)
        message = stderr.getvalue()
        self.assertIn("40", message)
        self.assertIn("30", message)
        self.assertIn("24", message)
        self.assertEqual([], curses_module.window.presented,
                         "nothing may be drawn into a window that is too small")
        self.assertTrue(curses_module.is_restored, curses_module.describe())

    def test_a_terminal_that_fails_mid_frame_still_gives_the_terminal_back(self):
        # Caution C10's hardest case: something goes wrong in the middle of
        # drawing, nothing catches it, and the player is left in the shell.
        curses_module = FakeCurses()
        curses_module.window.fail_writes = True

        with self.assertRaises(CursesError):
            game_main.main(["--hold", "0"],
                           session_factory=session_over(curses_module))

        self.assertTrue(curses_module.is_restored, curses_module.describe())

    def test_a_negative_hold_is_refused_rather_than_meaning_for_ever(self):
        with self.assertRaises(SystemExit):
            with contextlib.redirect_stderr(io.StringIO()):
                game_main.main(["--hold", "-1"],
                               session_factory=session_over(FakeCurses()))

    def test_the_default_hold_is_finite(self):
        self.assertGreater(game_main.DEFAULT_HOLD_SECONDS, 0)
        self.assertLess(game_main.DEFAULT_HOLD_SECONDS, 60)


if __name__ == "__main__":
    unittest.main()
