"""WI-12 — the assembly point: the real game in the real window.

Until WI-12 this module tested the M0 skeleton — one frame, a `--hold` timer,
and no game underneath. Both are gone, so these are new tests rather than
adjusted ones.

**The failure this file exists to catch.** `compose(state, status_line=None)`
leaves row 29 blank, and a frame with a blank row 29 is a perfectly well-formed
frame: it composes without complaint and satisfies every test the frame builder
has. So forgetting to pass the status row would not break anything loudly — it
would produce a game that quietly fails STAT-1 while looking entirely correct to
every automated check above it. `TheStatusRowReachesTheFrame` is the guard, and
it asserts the row is **not blank** and carries the real score, because
"a status row exists" is exactly what a blank row also satisfies.
"""

from __future__ import annotations

import io
import random
import unittest

from terminalgame.domain.game_state import Outcome, new_game_with
from terminalgame.game_main import (
    EXIT_OK,
    EXIT_SCREEN_TOO_SMALL,
    build_frame,
    main,
    play_a_game,
)
from terminalgame.presentation.frame_builder import HEIGHT, STATUS_ROW, WIDTH
from terminalgame.presentation.status_line import status_text
from terminalgame.screen.curses_adapter import TerminalSession
from terminalgame.screen.port import Colour, Key
from tests.fake_terminal import FakeCurses, FakeLocale, FakeSignals


def session_over(curses_module):
    """A real `TerminalSession` driven by a fake curses — WI-2's arrangement."""
    def factory():
        return TerminalSession(curses_module=curses_module,
                               signal_module=FakeSignals(),
                               locale_module=FakeLocale(),
                               on_fatal_signal=lambda number: None)
    return factory


def quitting_curses(width=WIDTH, height=HEIGHT):
    """A fake terminal with `q` already pressed, so a game ends at once."""
    curses_module = FakeCurses(width=width, height=height)
    curses_module.window.press(ord("q"), at=0.0)
    return curses_module


class QuietScreen(object):
    """A screen that quits at once. Enough to assemble a game on."""

    def __init__(self, keys=None, width=WIDTH, height=HEIGHT):
        self.keys = list(keys or [Key.printable("q")])
        self.presented = []
        self._size = (width, height)

    def size(self):
        return self._size

    def new_frame(self):
        return None

    def present(self, frame):
        self.presented.append(frame)

    def read_key(self, timeout_seconds):
        return self.keys.pop(0) if self.keys else Key.printable("q")


def row_text(frame, row):
    return "".join(frame.cell(column, row).character
                   for column in range(frame.width))


class TheStatusRowReachesTheFrame(unittest.TestCase):
    """STAT-1, and the silent way it could have been lost."""

    def setUp(self):
        self.state = new_game_with(random.Random(3))

    def test_the_bottom_row_is_not_blank(self):
        frame = build_frame(self.state)
        self.assertNotEqual("", row_text(frame, STATUS_ROW).strip(),
                            "row 29 is blank: the status line was never "
                            "passed to compose (STAT-1)")

    def test_it_carries_the_real_score_and_not_a_placeholder(self):
        scored = self.state.with_changes(score=41)
        self.assertIn("score 41", row_text(build_frame(scored), STATUS_ROW))

    def test_it_is_exactly_what_the_status_module_says_it_should_be(self):
        row = row_text(build_frame(self.state), STATUS_ROW)
        self.assertEqual(status_text(self.state), row.rstrip())

    def test_it_changes_when_the_game_ends(self):
        caught = self.state.with_changes(outcome=Outcome.CAUGHT, score=9)
        row = row_text(build_frame(caught), STATUS_ROW)
        self.assertIn("CAUGHT", row)
        self.assertIn("score 9", row)

    def test_it_is_cyan(self):
        frame = build_frame(self.state)
        for column in range(WIDTH):
            self.assertEqual(Colour.STATUS,
                             frame.cell(column, STATUS_ROW).colour)

    def test_the_rows_above_it_are_not_the_status_line(self):
        frame = build_frame(self.state)
        for row in range(STATUS_ROW):
            self.assertNotIn("arrows, q quits", row_text(frame, row))


class TheFrameIsTheWholeWindow(unittest.TestCase):

    def test_it_is_exactly_the_window_the_launcher_makes(self):
        frame = build_frame(new_game_with(random.Random(1)))
        self.assertEqual(WIDTH, frame.width)
        self.assertEqual(HEIGHT, frame.height)

    def test_the_maze_and_the_actors_are_on_it(self):
        state = new_game_with(random.Random(1))
        text = "\n".join(row_text(build_frame(state), row)
                         for row in range(STATUS_ROW))
        self.assertIn("║", text, "no wall glyphs (SCRN-3)")
        self.assertIn("▪", text, "no dots (SCRN-4)")


class PlayingAWholeGame(unittest.TestCase):

    def test_a_game_is_opened_and_played_and_handed_back(self):
        screen = QuietScreen()
        final = play_a_game(screen, seed=5)
        self.assertEqual(Outcome.PLAYING, final.outcome)
        self.assertGreaterEqual(len(screen.presented), 1)

    def test_one_seed_gives_one_game(self):
        first = play_a_game(QuietScreen(), seed=5)
        second = play_a_game(QuietScreen(), seed=5)
        self.assertEqual(first, second)

    def test_different_seeds_give_different_games(self):
        self.assertNotEqual(play_a_game(QuietScreen(), seed=5).maze,
                            play_a_game(QuietScreen(), seed=6).maze)

    def test_the_seed_reaches_the_ghost_as_well_as_the_maze(self):
        """One seed names the *whole* game, which is why one source is used.

        Played far enough for the ghost to have moved several times: two runs
        on one seed must agree about where it ended up, not merely about the
        maze.
        """
        keys = [None] * 40 + [Key.printable("q")]
        first = play_a_game(QuietScreen(list(keys)), seed=8)
        second = play_a_game(QuietScreen(list(keys)), seed=8)
        self.assertEqual(first.ghost, second.ghost)
        self.assertEqual(first.ghost_heading, second.ghost_heading)


class TheProcessEntryPoint(unittest.TestCase):

    def test_a_normal_run_ends_well_and_gives_the_terminal_back(self):
        curses_module = quitting_curses()
        status = main([], session_factory=session_over(curses_module))
        self.assertEqual(EXIT_OK, status)
        self.assertTrue(curses_module.is_restored, curses_module.describe())
        self.assertGreaterEqual(len(curses_module.window.presented), 1)

    def test_the_real_picture_reaches_the_glass(self):
        """What a player would actually see, read off the fake terminal.

        The rows are asserted directly rather than through `str()` of whatever
        was recorded: a repr can contain almost anything, and a test that
        matches one is not reading the screen.
        """
        curses_module = quitting_curses()
        main([], session_factory=session_over(curses_module))
        rows = curses_module.window.presented[0]
        self.assertEqual(HEIGHT, len(rows))
        self.assertIn("arrows, q quits", rows[STATUS_ROW],
                      "the status row never reached the terminal (STAT-1)")
        self.assertIn("║", "\n".join(rows[:STATUS_ROW]), "no maze was drawn")

    def test_a_window_too_small_fails_loudly_instead_of_drawing_half_a_maze(self):
        curses_module = quitting_curses(width=80, height=24)
        stderr = io.StringIO()
        status = main([], session_factory=session_over(curses_module),
                      stderr=stderr)
        self.assertEqual(EXIT_SCREEN_TOO_SMALL, status)
        message = stderr.getvalue()
        self.assertIn("40", message)
        self.assertIn("30", message)
        self.assertIn("24", message)
        self.assertEqual([], curses_module.window.presented,
                         "nothing may be drawn into a window that is too small")

    def test_a_terminal_too_small_is_still_handed_back(self):
        curses_module = quitting_curses(width=80, height=24)
        main([], session_factory=session_over(curses_module),
             stderr=io.StringIO())
        self.assertTrue(curses_module.is_restored, curses_module.describe())

    def test_a_terminal_that_fails_mid_frame_still_gives_the_terminal_back(self):
        # Caution C10's hardest case: something goes wrong in the middle of
        # drawing, nothing catches it, and the player is left in the shell.
        curses_module = quitting_curses()
        curses_module.window.fail_writes = True
        with self.assertRaises(Exception):
            main([], session_factory=session_over(curses_module))
        self.assertTrue(curses_module.is_restored, curses_module.describe())

    def test_a_seed_can_be_given_on_the_command_line(self):
        curses_module = quitting_curses()
        self.assertEqual(
            EXIT_OK,
            main(["--seed", "3"], session_factory=session_over(curses_module)))


if __name__ == "__main__":
    unittest.main()
