"""``./check-window-placement`` — the one step of human check H1.

H1 is the check no agent in this project can ever run: with no controlling
terminal there is no "window the player was last looking at" for the game to be
offset from, and nothing here can see a screen. What *can* be tested is
everything around the looking — that the launcher's own report is read
correctly, that the arithmetic is right, that the known intermittent
display-layout fault is called out when it happens, and that the script refuses
to run itself when there is nobody at the screen.

**Nothing in this file runs ``./play``.** Every test that would reach it passes
a stand-in runner, and the one test about the no-terminal guard replaces
``sys.stdin`` rather than relying on how the suite happens to have been
started. A test that launched ``./play`` would open a window on somebody's
screen and then wait for a keypress that never came.
"""

import importlib.machinery
import importlib.util
import io
import os
import stat
import sys
import unittest

from termgame import window

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHECK_PATH = os.path.join(REPO_ROOT, "check-window-placement")


def load_check():
    loader = importlib.machinery.SourceFileLoader("check_window_placement", CHECK_PATH)
    spec = importlib.util.spec_from_loader("check_window_placement", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


check = load_check()

#: The launcher's report, verbatim, as WI-2 recorded it from a live run
#: (docs/findings/WI-2-terminal-window-id.md §9). Reference (-898, 76), game
#: window (-868, 106): thirty across, thirty down.
A_GOOD_RUN = (
    "play: game window 3984 at (-868, 106) (reference (-898, 76) from front)\n"
)

#: The same launch on the run where ``displays()`` silently fell back to a
#: single 1440 x 900 screen, as WI-8 recorded it
#: (docs/findings/WI-8-title-settling-race.md §2). Same reference, and the
#: game landed on the main screen instead.
A_RUN_WITH_NO_LAYOUT = (
    "play: could not read the screen layout (CGGetActiveDisplayList failed "
    "(1)); assuming one 1440 x 900 display. The game window may land on the "
    "wrong screen.\n"
    "play: game window 4102 at (0, 106) (reference (-898, 76) from front)\n"
)


class TheCheckIsAnExecutableLikeTheOthers(unittest.TestCase):
    def test_it_is_executable_and_names_the_pinned_interpreter(self):
        mode = os.stat(CHECK_PATH).st_mode
        self.assertTrue(mode & stat.S_IXUSR, "check-window-placement is not executable")
        with io.open(CHECK_PATH, encoding="utf-8") as handle:
            self.assertEqual("#!/usr/bin/python3", handle.readline().strip())

    def test_the_only_program_it_runs_is_play(self):
        # It must not open a window of its own. ./play opens exactly one and
        # closes that same one by the id it captured.
        with io.open(CHECK_PATH, encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn('os.path.join(root, "play")', source)
        for forbidden in ("osascript", "do script", "open_game_window"):
            self.assertNotIn(forbidden, source, forbidden)


class ReadingTheLaunchersOwnReport(unittest.TestCase):
    def test_it_reads_the_line_the_launcher_really_prints(self):
        report = check.parse(A_GOOD_RUN)
        self.assertEqual(3984, report["id"])
        self.assertEqual((-868, 106), (report["x"], report["y"]))
        self.assertEqual((-898, 76), (report["rx"], report["ry"]))
        self.assertEqual("front", report["source"])

    def test_it_reads_the_line_even_when_other_lines_came_first(self):
        report = check.parse(A_RUN_WITH_NO_LAYOUT)
        self.assertEqual(4102, report["id"])
        self.assertEqual((0, 106), (report["x"], report["y"]))

    def test_output_without_the_line_parses_to_nothing(self):
        self.assertIsNone(check.parse("play: something else entirely\n"))

    def test_the_layout_warning_is_noticed(self):
        self.assertTrue(check.mentions_layout_trouble(A_RUN_WITH_NO_LAYOUT))
        self.assertFalse(check.mentions_layout_trouble(A_GOOD_RUN))


class TheVerdict(unittest.TestCase):
    def verdict_for(self, text, status=0):
        return check.verdict(
            check.parse(text), check.mentions_layout_trouble(text), status
        )

    def test_the_measured_good_run_reads_as_having_landed_where_it_should(self):
        headline, lines = self.verdict_for(A_GOOD_RUN)
        self.assertEqual("LANDED_RIGHT", headline)
        text = "\n".join(lines)
        self.assertIn("30 across and 30 down", text)

    def test_even_a_perfect_offset_leaves_the_judgement_to_the_person(self):
        # The offset being right does not mean the window was on the right
        # screen or entirely on it, and nothing here can see that.
        _headline, lines = self.verdict_for(A_GOOD_RUN)
        text = "\n".join(lines)
        self.assertIn("same screen", text)
        self.assertIn("Only you can see that", text)

    def test_the_measured_layout_failure_says_which_line_is_the_evidence(self):
        headline, lines = self.verdict_for(A_RUN_WITH_NO_LAYOUT)
        self.assertEqual("LAYOUT_UNREADABLE", headline)
        text = "\n".join(lines)
        self.assertIn("could not read your display layout", text)
        self.assertIn("MAIN screen", text)
        self.assertIn("worth reporting", text)

    def test_the_layout_failure_still_reports_the_two_positions(self):
        _headline, lines = self.verdict_for(A_RUN_WITH_NO_LAYOUT)
        text = "\n".join(lines)
        self.assertIn("(-898, 76)", text)
        self.assertIn("(0, 106)", text)

    def test_a_clamped_offset_is_reported_as_something_to_look_at(self):
        # Launching from near a corner legitimately moves the window back on
        # screen, so a different offset is not automatically a failure.
        headline, lines = self.verdict_for(
            "play: game window 9 at (1400, 830) (reference (1390, 820) from front)\n"
        )
        self.assertEqual("LANDED_SHIFTED", headline)
        text = "\n".join(lines)
        self.assertIn("10 across and 10 down", text)
        self.assertIn("not automatically wrong", text)
        self.assertIn("half off the edge", text)

    def test_no_report_at_all_is_itself_worth_reporting(self):
        headline, lines = self.verdict_for("play: something went wrong\n", status=1)
        self.assertEqual("NO_REPORT", headline)
        text = "\n".join(lines)
        self.assertIn("never said where it put its window", text)
        self.assertIn("status 1", text)

    def test_the_offset_it_checks_against_is_the_launchers_own_constant(self):
        # Not a copy of (30, 30) in this script. If WI-2's constant ever
        # changes, this check changes with it rather than disagreeing with it.
        self.assertEqual((30, 30), tuple(window.OFFSET))
        headline, _lines = check.verdict(
            {"x": 5, "y": 7, "rx": 0, "ry": 0, "source": "front", "id": 1},
            False,
            0,
            offset=(5, 7),
        )
        self.assertEqual("LANDED_RIGHT", headline)


class FakeStdin(object):
    def __init__(self, is_a_tty):
        self.is_a_tty = is_a_tty

    def isatty(self):
        return self.is_a_tty


class ItRefusesToRunWithNobodyAtTheScreen(unittest.TestCase):
    """The guard that keeps an agent from leaving a window open for ever.

    ``./play`` waits for somebody to press ``q`` in the window it opened. Run
    with nobody there, it opens a window that nothing will ever close.
    """

    def setUp(self):
        self.saved_stdin = sys.stdin
        self.ran = []

    def tearDown(self):
        sys.stdin = self.saved_stdin

    def runner(self, root):
        self.ran.append(root)
        return 0, A_GOOD_RUN

    def test_without_a_terminal_it_says_why_and_runs_nothing(self):
        sys.stdin = FakeStdin(False)
        complaint = io.StringIO()
        saved = sys.stderr
        sys.stderr = complaint
        try:
            status = main_with(self.runner, argv=[])
        finally:
            sys.stderr = saved
        self.assertEqual(2, status)
        self.assertEqual([], self.ran, "./play was run with nobody at the screen")
        text = complaint.getvalue()
        self.assertIn("this is not a terminal", text)
        self.assertIn("./check-window-placement", text)

    def test_with_a_terminal_it_goes_ahead(self):
        sys.stdin = FakeStdin(True)
        out = io.StringIO()
        status = main_with(self.runner, argv=[], out=out)
        self.assertEqual(0, status)
        self.assertEqual([REPO_ROOT], self.ran)

    def test_anyway_overrides_the_guard_for_somebody_who_means_it(self):
        sys.stdin = FakeStdin(False)
        out = io.StringIO()
        status = main_with(self.runner, argv=["--anyway"], out=out)
        self.assertEqual(0, status)
        self.assertEqual([REPO_ROOT], self.ran)


def main_with(runner, argv, out=None):
    return check.main(argv=argv, out=out or io.StringIO(), runner=runner)


class WhatThePersonIsToldBeforeTheyStart(unittest.TestCase):
    def test_it_says_where_to_put_the_window_before_running_anything(self):
        text = check.PREAMBLE
        self.assertIn("bottom-right", text)
        self.assertIn("NOT your main one", text)
        self.assertIn("press q", text)

    def test_it_lists_the_three_things_to_look_at(self):
        text = check.PREAMBLE
        self.assertIn("below and to the right", text)
        self.assertIn("SAME screen", text)
        self.assertIn("all four of its edges", text)

    def test_the_whole_run_ends_by_asking_for_words_rather_than_a_verdict(self):
        out = io.StringIO()
        check.main(
            argv=["--anyway"],
            out=out,
            runner=lambda root: (0, A_GOOD_RUN),
        )
        self.assertIn("wants", out.getvalue())
        self.assertIn("your words, not a pass or a fail", out.getvalue())

    def test_the_headline_and_the_numbers_both_reach_the_person(self):
        out = io.StringIO()
        check.main(
            argv=["--anyway"],
            out=out,
            runner=lambda root: (0, A_RUN_WITH_NO_LAYOUT),
        )
        text = out.getvalue()
        self.assertIn("LAYOUT_UNREADABLE", text)
        self.assertIn("(0, 106)", text)


if __name__ == "__main__":
    unittest.main()
