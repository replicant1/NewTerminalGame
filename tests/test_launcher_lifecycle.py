"""The order things happen in, and what happens when they go wrong.

These are the tests the implementation plan asks WI-1 for. They run the whole
launcher with the subprocess seam stood in for, so what they see is the
AppleScript that would have reached the desktop, in the order it would have
reached it — which is the thing the cautions are actually about.
"""

import re
import unittest

from launcher.desktop import Desktop
from launcher.geometry import DEFAULT_POSITION, DEFAULT_SCREEN, Offset, Point, Rect, Size
from launcher.lifecycle import LaunchFailed, WindowLauncher
from launcher.runner import AutomationError, AutomationTimeout
from tests.launcher_fakes import FailingQueryRunner, FakeClock, RecordingRunner

WINDOW_ID = 7653
COMMAND = "/repo/Terminal Game"


def honours_the_move(call):
    """A desktop that puts the window exactly where it was asked to.

    The real one does not always — see
    ``test_where_the_window_went_is_read_back_rather_than_assumed`` — so the
    answer is read out of the script rather than assumed by the fake.
    """
    x, y = re.search(r"to \{(-?\d+), (-?\d+)\}", call.source).groups()
    return "%s,%s" % (x, y)

# A reference window at (400, 300), 600 by 500, on a 1440 by 900 screen, and a
# game window 357 by 558 — the real size measured for 40x30 at Menlo 14.
HAPPY_PATH = {
    "reference_window_geometry": "400,300,1000,800",
    "visible_screen_bounds": "0,0,1440,900",
    "open_window_running": str(WINDOW_ID),
    "configure_window": "ok",
    "window_size": "357,558",
    "set_window_position": honours_the_move,
    "window_is_busy": "false",
    "close_window": "closed",
    "window_is_visible": "false",
}

POSITIONAL_OR_TITLE = (
    "front window",
    "frontmost",
    "window 1",
    "first window",
    "last window",
    "custom title is",
    "whose name",
)


def build(replies=None, runner=None, **kwargs):
    """A launcher wired to a recording runner and a clock that never waits."""
    if runner is None:
        merged = dict(HAPPY_PATH)
        merged.update(replies or {})
        runner = RecordingRunner(merged)
    clock = FakeClock()
    launcher = WindowLauncher(
        Desktop(runner),
        clock=clock.time,
        sleeper=clock.sleep,
        **kwargs
    )
    return launcher, runner, clock


class AskBeforeYouCreate(unittest.TestCase):
    """Otherwise the launcher measures the window it just made."""

    def test_the_frontmost_query_comes_before_the_creation_call(self):
        launcher, runner, _ = build()
        launcher.open(COMMAND)
        self.assertLess(
            runner.names.index("reference_window_geometry"),
            runner.names.index("open_window_running"),
        )

    def test_the_frontmost_query_is_never_issued_again_afterwards(self):
        launcher, runner, _ = build()
        launcher.run(COMMAND)
        after = runner.names[runner.names.index("open_window_running") + 1:]
        self.assertNotIn("reference_window_geometry", after)

    def test_it_is_asked_exactly_once_in_a_whole_session(self):
        launcher, runner, _ = build()
        launcher.run(COMMAND)
        self.assertEqual(1, runner.names.count("reference_window_geometry"))

    def test_the_screen_is_also_measured_before_anything_exists(self):
        launcher, runner, _ = build()
        launcher.open(COMMAND)
        self.assertLess(
            runner.names.index("visible_screen_bounds"),
            runner.names.index("open_window_running"),
        )

    def test_nothing_at_all_is_sent_to_the_terminal_before_the_creation_call(self):
        launcher, runner, _ = build()
        launcher.open(COMMAND)
        creation = runner.names.index("open_window_running")
        for call in runner.calls[:creation]:
            self.assertNotIn('"Terminal"', call.source, call.name)


class EverythingAfterwardsNamesTheCapturedIdentity(unittest.TestCase):
    """Caution C1, checked on the text that would have reached the desktop."""

    def test_every_script_after_creation_names_the_captured_window_id(self):
        launcher, runner, _ = build()
        launcher.run(COMMAND)
        sources = runner.sources_after("open_window_running")
        self.assertTrue(sources, "nothing happened after the window was created")
        for source in sources:
            self.assertIn("window id %d" % WINDOW_ID, source)

    def test_no_script_after_creation_reaches_for_a_window_any_other_way(self):
        launcher, runner, _ = build()
        launcher.run(COMMAND)
        for source in runner.sources_after("open_window_running"):
            lowered = source.lower()
            for phrase in POSITIONAL_OR_TITLE:
                self.assertNotIn(phrase, lowered, phrase)

    def test_a_different_captured_id_moves_every_later_script_with_it(self):
        replies = dict(HAPPY_PATH)
        replies["open_window_running"] = "424242"
        launcher, runner, _ = build(replies)
        launcher.run(COMMAND)
        for source in runner.sources_after("open_window_running"):
            self.assertIn("window id 424242", source)
            self.assertNotIn("window id %d" % WINDOW_ID, source)


class EveryCallIsBounded(unittest.TestCase):
    def test_no_script_is_sent_without_a_timeout(self):
        launcher, runner, _ = build()
        launcher.run(COMMAND)
        self.assertTrue(runner.calls)
        for call in runner.calls:
            self.assertGreater(call.timeout, 0.0, call.name)
            self.assertIn("with timeout of", call.source, call.name)


class WhereTheWindowLands(unittest.TestCase):
    """WIN-4, on the remembered geometry rather than on anything current."""

    def test_the_window_is_moved_to_the_remembered_geometry_plus_the_offset(self):
        launcher, runner, _ = build()
        window = launcher.open(COMMAND)
        self.assertEqual(Point(432, 332), window.asked_for)
        self.assertIn("to {432, 332}", runner.source_of("set_window_position"))

    def test_where_the_window_went_is_read_back_rather_than_assumed(self):
        # Measured on the real desktop: a window asked for y = -1353, on a
        # display above the main one, landed at y = 30, because macOS
        # constrains a window to the screen it is on. A launcher that recorded
        # its own arithmetic would believe something untrue about the desktop.
        launcher, _, _ = build({"set_window_position": "-876,30"})
        window = launcher.open(COMMAND)
        self.assertEqual(Point(432, 332), window.asked_for)
        self.assertEqual(Point(-876, 30), window.position)

    def test_the_offset_is_applied_to_the_reference_and_not_to_the_new_window(self):
        # The new window was created wherever the terminal felt like putting it.
        # If the launcher offset from *that*, the answer would move with it.
        replies = dict(HAPPY_PATH, reference_window_geometry="100,50,700,550")
        launcher, runner, _ = build(replies)
        window = launcher.open(COMMAND)
        self.assertEqual(Point(132, 82), window.position)

    def test_the_offset_can_be_changed(self):
        launcher, _, _ = build(offset=Offset(10, 20))
        self.assertEqual(Point(410, 320), launcher.open(COMMAND).position)

    def test_the_measured_size_of_the_real_window_is_what_gets_clamped(self):
        # Reference window hard against the bottom right of the screen.
        replies = dict(HAPPY_PATH, reference_window_geometry="1300,800,1440,900")
        launcher, _, _ = build(replies)
        window = launcher.open(COMMAND)
        self.assertEqual(Size(357, 558), window.size)
        self.assertEqual(Point(1440 - 357, 900 - 558), window.position)

    def test_the_window_is_measured_after_it_is_configured_not_before(self):
        # 40x30 of Menlo changes the window's pixel size, so measuring first
        # would clamp against the wrong rectangle.
        launcher, runner, _ = build()
        launcher.open(COMMAND)
        self.assertLess(
            runner.names.index("configure_window"), runner.names.index("window_size")
        )
        self.assertLess(
            runner.names.index("window_size"),
            runner.names.index("set_window_position"),
        )


class WhenTheDesktopWillNotSayWhereThePlayerWasLooking(unittest.TestCase):
    """Architecture assumption A2: a refusal degrades, it does not abort."""

    def test_the_window_is_still_created_and_still_placed(self):
        runner = FailingQueryRunner(["reference_window_geometry"], HAPPY_PATH)
        launcher, runner, _ = build(runner=runner)
        window = launcher.open(COMMAND)
        self.assertEqual(WINDOW_ID, window.window_id)
        self.assertEqual(DEFAULT_POSITION, window.position)
        self.assertIn(
            "to {%d, %d}" % DEFAULT_POSITION, runner.source_of("set_window_position")
        )

    def test_the_launcher_records_that_it_had_no_reference(self):
        runner = FailingQueryRunner(["reference_window_geometry"], HAPPY_PATH)
        launcher, _, _ = build(runner=runner)
        self.assertIsNone(launcher.open(COMMAND).reference)

    def test_a_refused_screen_query_falls_back_to_the_documented_screen(self):
        # The documented default is deliberately smaller than most real
        # screens, so being wrong about it can only pull the window further
        # inside one: here the offset survives in x and the clamp bites in y,
        # putting the window at the bottom of a 1024 by 768 screen rather than
        # somewhere it might not be visible at all.
        runner = FailingQueryRunner(["visible_screen_bounds"], HAPPY_PATH)
        launcher, _, _ = build(runner=runner)
        window = launcher.open(COMMAND)
        self.assertEqual(DEFAULT_SCREEN, window.screen)
        self.assertEqual(
            Point(432, DEFAULT_SCREEN.bottom - 558), window.position
        )
        self.assertTrue(DEFAULT_SCREEN.contains_point(window.position))

    def test_both_queries_refused_still_produces_a_running_window(self):
        runner = FailingQueryRunner(
            ["reference_window_geometry", "visible_screen_bounds"], HAPPY_PATH
        )
        launcher, runner, _ = build(runner=runner)
        window = launcher.open(COMMAND)
        self.assertEqual(WINDOW_ID, window.window_id)
        self.assertEqual(DEFAULT_POSITION, window.position)
        self.assertIn("open_window_running", runner.names)


class WhenSetupFailsAfterTheWindowExists(unittest.TestCase):
    """Caution C3: deal with the window before dealing with the error."""

    def _failing_at(self, stage):
        replies = dict(HAPPY_PATH)
        replies[stage] = AutomationError("the desktop said no")
        return build(replies)

    def test_a_failure_while_configuring_closes_the_captured_window(self):
        launcher, runner, _ = self._failing_at("configure_window")
        self.assertRaises(LaunchFailed, launcher.open, COMMAND)
        self.assertIn("close_window", runner.names)
        self.assertIn("close window id %d" % WINDOW_ID, runner.source_of("close_window"))

    def test_a_failure_while_measuring_closes_the_captured_window(self):
        launcher, runner, _ = self._failing_at("window_size")
        self.assertRaises(LaunchFailed, launcher.open, COMMAND)
        self.assertIn("close window id %d" % WINDOW_ID, runner.source_of("close_window"))

    def test_a_failure_while_moving_closes_the_captured_window(self):
        launcher, runner, _ = self._failing_at("set_window_position")
        self.assertRaises(LaunchFailed, launcher.open, COMMAND)
        self.assertIn("close window id %d" % WINDOW_ID, runner.source_of("close_window"))

    def test_a_timed_out_call_is_treated_the_same_as_a_refusal(self):
        replies = dict(HAPPY_PATH)
        replies["configure_window"] = AutomationTimeout("no answer")
        launcher, runner, _ = build(replies)
        self.assertRaises(LaunchFailed, launcher.open, COMMAND)
        self.assertIn("close_window", runner.names)

    def test_the_failure_says_which_window_and_that_it_went(self):
        launcher, _, _ = self._failing_at("configure_window")
        try:
            launcher.open(COMMAND)
        except LaunchFailed as failure:
            self.assertEqual(WINDOW_ID, failure.window_id)
            self.assertTrue(failure.reap.closed)
            self.assertIsInstance(failure.cause, AutomationError)
        else:
            self.fail("open should have raised")

    def test_an_interruption_also_reaps_before_it_propagates(self):
        replies = dict(HAPPY_PATH)
        replies["window_size"] = KeyboardInterrupt()
        launcher, runner, _ = build(replies)
        self.assertRaises(LaunchFailed, launcher.open, COMMAND)
        self.assertIn("close window id %d" % WINDOW_ID, runner.source_of("close_window"))

    def test_nothing_is_closed_when_setup_succeeds(self):
        launcher, runner, _ = build()
        launcher.open(COMMAND)
        self.assertNotIn("close_window", runner.names)


class NeverCloseAWindowSomethingIsRunningIn(unittest.TestCase):
    """Caution C2. The modal sheet it would raise blocks every later call."""

    def test_idleness_is_confirmed_before_the_close(self):
        launcher, runner, _ = build()
        launcher.run(COMMAND)
        self.assertLess(
            runner.names.index("window_is_busy"), runner.names.index("close_window")
        )

    def test_a_window_that_stays_busy_is_left_open_on_purpose(self):
        launcher, runner, _ = build({"window_is_busy": "true"}, poll_interval=0.5)
        result = launcher.reap(WINDOW_ID, timeout=2.0)
        self.assertFalse(result.closed)
        self.assertNotIn("close_window", runner.names)
        self.assertIn("still busy", result.reason)
        self.assertIn("modal sheet", result.reason)

    def test_the_wait_for_idleness_gives_up_rather_than_polling_for_ever(self):
        launcher, runner, clock = build({"window_is_busy": "true"}, poll_interval=0.5)
        launcher.reap(WINDOW_ID, timeout=2.0)
        self.assertLessEqual(clock.now, 2.5)
        self.assertLess(len(runner.calls_named("window_is_busy")), 10)

    def test_it_waits_while_the_window_is_busy_and_closes_once_it_is_not(self):
        launcher, runner, clock = build(
            {"window_is_busy": ["true", "true", "false"]}, poll_interval=0.25
        )
        result = launcher.reap(WINDOW_ID, timeout=10.0)
        self.assertTrue(result.closed)
        self.assertEqual([0.25, 0.25], clock.slept)
        self.assertIn("close_window", runner.names)

    def test_a_window_that_cannot_be_asked_is_not_closed_either(self):
        runner = FailingQueryRunner(["window_is_busy"], HAPPY_PATH)
        launcher, runner, _ = build(runner=runner)
        result = launcher.reap(WINDOW_ID, timeout=1.0)
        self.assertFalse(result.closed)
        self.assertNotIn("close_window", runner.names)


class CheckingThatItWent(unittest.TestCase):
    def test_the_check_is_visible_and_not_exists(self):
        launcher, runner, _ = build()
        launcher.run(COMMAND)
        source = runner.source_of("window_is_visible")
        self.assertIn("visible of window id %d" % WINDOW_ID, source)
        self.assertNotIn("exists", source)

    def test_a_window_still_visible_after_a_close_is_reported_as_not_reaped(self):
        launcher, _, _ = build({"window_is_visible": "true"})
        result = launcher.reap(WINDOW_ID, timeout=1.0)
        self.assertFalse(result.closed)
        self.assertIn("still visible", result.reason)

    def test_a_successful_reap_says_which_window_it_closed(self):
        launcher, _, _ = build()
        result = launcher.reap(WINDOW_ID, timeout=1.0)
        self.assertTrue(result.closed)
        self.assertEqual(WINDOW_ID, result.window_id)
        self.assertIn(str(WINDOW_ID), result.reason)

    def test_a_close_that_fails_is_reported_rather_than_raised(self):
        # reap runs on the failure path, where an exception of its own would
        # bury the failure it was called to clean up after.
        runner = FailingQueryRunner(["close_window"], HAPPY_PATH)
        launcher, _, _ = build(runner=runner)
        result = launcher.reap(WINDOW_ID, timeout=1.0)
        self.assertFalse(result.closed)
        self.assertIn("closing window", result.reason)


class AWholeSession(unittest.TestCase):
    def test_the_calls_happen_in_the_one_safe_order(self):
        launcher, runner, _ = build()
        result = launcher.run(COMMAND)
        self.assertTrue(result.closed)
        self.assertEqual(
            [
                "reference_window_geometry",
                "visible_screen_bounds",
                "open_window_running",
                "configure_window",
                "window_size",
                "set_window_position",
                "window_is_busy",
                "close_window",
                "window_is_visible",
            ],
            runner.names,
        )

    def test_the_command_the_caller_asked_for_is_what_gets_run(self):
        launcher, runner, _ = build()
        launcher.run("/repo/Terminal Game --seed 4")
        self.assertIn(
            'do script "exec /repo/Terminal Game --seed 4"',
            runner.source_of("open_window_running"),
        )

    def test_a_session_leaves_nothing_on_the_desktop(self):
        launcher, runner, _ = build()
        result = launcher.run(COMMAND)
        self.assertTrue(result.closed)
        self.assertEqual(1, runner.names.count("close_window"))
        self.assertEqual(1, runner.names.count("window_is_visible"))


if __name__ == "__main__":
    unittest.main()
