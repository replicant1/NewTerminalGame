# -*- coding: utf-8 -*-
"""The smoke test — the real launcher, the real game, a real window.

These run it against the same subprocess seam the launcher's own tests use:
what they see is the AppleScript that would have reached the desktop, in the
order it would have reached it. Nothing here opens a window.

Two things here are worth more than the rest.

**That it arranges its own way out.** M0's ``--hold`` was scaffolding and the
real game exits on ``q`` and never on a timer, so anything that starts a game
with nobody at the keyboard has to end it. There are tests that ``q`` is sent,
that it goes into the captured tab rather than into whatever has focus, and
that no hold is reached for.

**That the window is reaped whatever happens**, including on the way in: a
failure between creating the window and handing back the context manager never
reaches ``__exit__``, so ``__enter__`` reaps for itself.

The register that used to share this file is now `manual_smoketest`, and its
tests are in ``tests/test_manual_smoketest.py``.
"""

from __future__ import annotations

import contextlib
import inspect
import io
import sys
import unittest

from launcher.geometry import Size
from launcher.runner import AutomationError
from manual_smoketest import checks
from auto_smoketest import pack
from auto_smoketest.__main__ import main as smoketest_main
from auto_smoketest.pack import (
    Observation,
    WindowUnderTest,
    census,
    exercise_a_whole_session,
    exercise_the_picture,
    exercise_the_window,
    tab_contents,
    type_into_tab,
    visible_window_count,
    window_title,
)
from tests.launcher_fakes import FailingQueryRunner, FakeClock, RecordingRunner

WINDOW_ID = 7653
COMMAND = "/bin/sh -c 'exec the game'"

#: What the tab's process list looks like while the game is in it, and after.
PLAYING = "login|Python"
FINISHED = ""

#: A pack run where the game starts, is captured, is quit, and goes.
HAPPY_PATH = {
    "open_window_running": str(WINDOW_ID),
    "configure_window": "ok",
    "window_processes": [PLAYING, PLAYING, FINISHED, FINISHED],
    "tab_contents": "wall\nwall\n score 0",
    "window_title": "rodneybailey — Terminal Game — /bin/sh",
    "window_size": "357,558",
    "type_into_tab": "sent",
    "close_window": "closed",
    "window_is_visible": "false",
    "visible_window_count": "1",
}


def happy_path(**overrides):
    """A fresh copy of `HAPPY_PATH`, list replies and all.

    `RecordingRunner` shallow-copies its replies dict and then *consumes* any
    list in it, so a runner built straight from the module-level `HAPPY_PATH`
    drains it: the first test that used one would pass and every later test
    would see an empty queue. Found the hard way. Any test building its own
    runner goes through here.
    """
    fresh = {name: list(reply) if isinstance(reply, list) else reply
             for name, reply in HAPPY_PATH.items()}
    for name, reply in overrides.items():
        fresh[name] = list(reply) if isinstance(reply, list) else reply
    return fresh


def build(replies=None, runner=None):
    """A recording runner and a clock that only moves when the code sleeps."""
    if runner is None:
        runner = RecordingRunner(happy_path(**(replies or {})))
    clock = FakeClock()
    return runner, clock


class TheWayOutIsArrangedRatherThanHopedFor(unittest.TestCase):
    """The obligation `--hold`'s retirement created.

    "Anything that starts a game with nobody at the keyboard must arrange its
    own way out." The game exits on `q` and on nothing else, so the pack has
    to send one.
    """

    def test_the_pack_sends_q_to_end_the_game(self):
        runner, clock = build()
        exercise_a_whole_session(runner, COMMAND, clock=clock.time,
                                 sleeper=clock.sleep)
        self.assertIn("type_into_tab", runner.names)
        self.assertIn('do script "q"', runner.source_of("type_into_tab"))

    def test_it_sends_it_to_the_captured_tab_and_not_to_whatever_has_focus(self):
        # `System Events` keystroke injection would type into the window the
        # person at the machine is looking at. This names the id, like every
        # other call this project makes.
        source = type_into_tab(WINDOW_ID, "q").source
        self.assertIn("in selected tab of window id %d" % WINDOW_ID, source)
        self.assertNotIn("System Events", source)
        self.assertNotIn("keystroke", source)
        for positional in ("front window", "window 1", "first window",
                           "frontmost", "every window"):
            self.assertNotIn(positional, source)

    def test_the_game_ends_because_the_pack_ended_it_not_because_it_waited(self):
        # The real form of "never uses a hold". A pack that waited for the
        # game to stop by itself would look identical on a happy path where
        # it stops anyway -- so the check is the ORDER: `q` must be sent
        # before the process list is ever seen empty.
        runner, clock = build({"window_processes": [PLAYING, PLAYING, PLAYING,
                                                    FINISHED, FINISHED]})
        exercise_a_whole_session(runner, COMMAND, clock=clock.time,
                                 sleeper=clock.sleep)
        names = runner.names
        self.assertIn("type_into_tab", names)
        quit_at = names.index("type_into_tab")
        # Every process-list call before the `q` must have found it running.
        polls_before = names[:quit_at].count("window_processes")
        self.assertGreater(polls_before, 0)
        self.assertLess(quit_at, len(names) - 1)

    def test_it_does_not_sit_and_wait_for_a_game_that_will_not_stop(self):
        # The other half: if the game ignores `q`, the pack gives up rather
        # than waiting for a timer that is not coming, and leaves the window
        # rather than closing it over a live process.
        runner, clock = build({"window_processes": PLAYING})
        observations, _, _, window = exercise_a_whole_session(
            runner, COMMAND, clock=clock.time, sleeper=clock.sleep)
        self.assertIn("type_into_tab", runner.names)
        self.assertEqual(WINDOW_ID, window.abandoned)
        self.assertLess(clock.now, 120.0)

    def test_it_waits_for_the_game_to_appear_before_believing_it_ended(self):
        # An empty process list means "nothing is running", and that is also
        # what a command which failed instantly looks like. Measured the hard
        # way in WI-13: a game started in the wrong directory dies at once and
        # the honest empty list reads exactly like a finished game.
        runner, clock = build({"window_processes": FINISHED})
        observations, _, _, _ = exercise_a_whole_session(
            runner, COMMAND, clock=clock.time, sleeper=clock.sleep)
        started = [o for o in observations if o.codes == ("GAME-1", "WIN-1")]
        self.assertEqual(1, len(started))
        self.assertFalse(started[0].ok)
        self.assertIn("nothing ever ran", started[0].detail)

    def test_waiting_for_the_game_is_bounded(self):
        runner, clock = build({"window_processes": FINISHED})
        window = WindowUnderTest(runner, COMMAND, clock=clock.time,
                                 sleeper=clock.sleep)
        with window:
            self.assertFalse(window.wait_for_the_game(timeout=2.0))
        self.assertLessEqual(clock.now, 30.0)

    def test_waiting_for_it_to_go_is_bounded_too(self):
        runner, clock = build({"window_processes": PLAYING})
        window = WindowUnderTest(runner, COMMAND, clock=clock.time,
                                 sleeper=clock.sleep)
        window.__enter__()
        self.assertFalse(window.wait_until_gone(timeout=2.0))
        window.reap()


class TheWindowIsReapedByConstruction(unittest.TestCase):
    """A failure anywhere inside must not leave one on the desktop."""

    def test_an_ordinary_run_closes_the_window_it_opened(self):
        runner, clock = build()
        exercise_a_whole_session(runner, COMMAND, clock=clock.time,
                                 sleeper=clock.sleep)
        self.assertIn("close_window", runner.names)
        self.assertIn("window id %d" % WINDOW_ID,
                      runner.source_of("close_window"))

    def test_an_exception_inside_still_closes_it(self):
        runner, clock = build()
        window = WindowUnderTest(runner, COMMAND, clock=clock.time,
                                 sleeper=clock.sleep)
        with self.assertRaises(ValueError):
            with window:
                raise ValueError("something went wrong mid-exercise")
        self.assertIn("close_window", runner.names)

    def test_and_does_not_swallow_the_failure_it_was_cleaning_up_after(self):
        runner, clock = build()
        window = WindowUnderTest(runner, COMMAND, clock=clock.time,
                                 sleeper=clock.sleep)
        try:
            with window:
                raise ValueError("the real problem")
        except ValueError as error:
            self.assertEqual("the real problem", str(error))
        else:
            self.fail("the exception was swallowed")

    def test_a_window_with_a_game_still_in_it_is_left_open_and_named(self):
        # Caution C2 beats C3. Closing it raises the modal sheet that blocks
        # every later automation call including the cleanup itself, so
        # "reap anyway" does not even achieve reaping.
        runner, clock = build({"window_processes": PLAYING})
        window = WindowUnderTest(runner, COMMAND, clock=clock.time,
                                 sleeper=clock.sleep)
        with window:
            pass
        self.assertEqual(WINDOW_ID, window.abandoned)
        self.assertNotIn("close_window", runner.names)

    def test_and_says_why_so_a_person_knows_it_was_deliberate(self):
        runner, clock = build({"window_processes": PLAYING})
        window = WindowUnderTest(runner, COMMAND, clock=clock.time,
                                 sleeper=clock.sleep)
        with window:
            pass
        said = " ".join(what for _, what in window.events)
        self.assertIn("LEFT OPEN", said)
        self.assertIn("modal sheet", said)

    def test_it_tries_q_before_giving_up_on_a_window(self):
        runner, clock = build({"window_processes": PLAYING})
        window = WindowUnderTest(runner, COMMAND, clock=clock.time,
                                 sleeper=clock.sleep)
        with window:
            pass
        self.assertIn("type_into_tab", runner.names)

    def test_a_failure_while_configuring_still_closes_the_window(self):
        # The gap `__exit__` cannot cover. Python calls `__exit__` only for an
        # `__enter__` that RETURNED, so a failure between creating the window
        # and handing back `self` leaves one on the desktop for good unless
        # `__enter__` reaps for itself. `WindowLauncher.open` has always done
        # this; the pack did not.
        runner = FailingQueryRunner(
            ["configure_window"], happy_path(window_processes=FINISHED))
        clock = FakeClock()
        window = WindowUnderTest(runner, COMMAND, clock=clock.time,
                                 sleeper=clock.sleep)
        with self.assertRaises(AutomationError):
            with window:
                self.fail("the body must not run when __enter__ failed")
        self.assertIn("close_window", runner.names)
        self.assertIn("window id %d" % WINDOW_ID,
                      runner.source_of("close_window"))

    def test_and_the_configure_failure_is_the_one_that_comes_out(self):
        # The reap runs on the failure path, so it must not bury the failure
        # it was called to clean up after -- and not only when the reap fails
        # in the way it expects to. `AutomationError` is the documented way a
        # desktop call goes wrong; anything else escaping the reap would
        # replace the real diagnosis with a worse one.
        class CloseBreaksOddly(FailingQueryRunner):
            def run(self, call):
                if call.name == "close_window":
                    raise RuntimeError("the runner itself fell over")
                return FailingQueryRunner.run(self, call)

        runner = CloseBreaksOddly(
            ["configure_window"], happy_path(window_processes=FINISHED))
        clock = FakeClock()
        window = WindowUnderTest(runner, COMMAND, clock=clock.time,
                                 sleeper=clock.sleep)
        try:
            with window:
                pass
        except AutomationError as error:
            self.assertIn("configure_window", str(error))
        else:
            self.fail("the configure failure was lost behind the reap")
        # And the reap that went wrong is recorded rather than silently
        # forgotten: the window is still out there.
        self.assertEqual(WINDOW_ID, window.abandoned)

    def test_a_configure_failure_over_a_live_game_names_the_window_it_left(self):
        # Caution C2 still beats C3 on this path: a window with something
        # running in it is left open, and named, rather than closed.
        runner = FailingQueryRunner(
            ["configure_window"], happy_path(window_processes=PLAYING))
        clock = FakeClock()
        window = WindowUnderTest(runner, COMMAND, clock=clock.time,
                                 sleeper=clock.sleep)
        with self.assertRaises(AutomationError):
            with window:
                pass
        self.assertEqual(WINDOW_ID, window.abandoned)
        self.assertNotIn("close_window", runner.names)

    def test_a_reap_that_cannot_ask_leaves_the_window_rather_than_guessing(self):
        runner = FailingQueryRunner(["window_processes"], HAPPY_PATH)
        clock = FakeClock()
        window = WindowUnderTest(runner, COMMAND, clock=clock.time,
                                 sleeper=clock.sleep)
        with window:
            pass
        self.assertEqual(WINDOW_ID, window.abandoned)
        self.assertNotIn("close_window", runner.names)

    def test_the_close_is_confirmed_with_visible_and_not_with_exists(self):
        runner, clock = build()
        exercise_a_whole_session(runner, COMMAND, clock=clock.time,
                                 sleeper=clock.sleep)
        source = runner.source_of("window_is_visible")
        self.assertIn("visible", source)
        self.assertNotIn("exists", source)

    def test_it_reaps_only_once_however_often_it_is_asked(self):
        runner, clock = build()
        window = WindowUnderTest(runner, COMMAND, clock=clock.time,
                                 sleeper=clock.sleep)
        with window:
            pass
        window.reap()
        window.reap()
        self.assertEqual(1, runner.names.count("close_window"))


class EveryCallNamesTheCapturedIdentity(unittest.TestCase):
    """Caution C1, for the scripts this pack adds."""

    BUILDERS = (
        ("type_into_tab", lambda: type_into_tab(WINDOW_ID, "q")),
        ("tab_contents", lambda: tab_contents(WINDOW_ID)),
        ("window_title", lambda: window_title(WINDOW_ID)),
    )

    def test_each_one_addresses_the_window_by_its_id(self):
        for name, builder in self.BUILDERS:
            self.assertIn("window id %d" % WINDOW_ID, builder().source, name)

    def test_none_of_them_names_a_window_by_position_or_by_title(self):
        for name, builder in self.BUILDERS:
            source = builder().source
            for positional in ("front window", "frontmost", "window 1",
                               "first window", "last window", "whose name",
                               "custom title is"):
                self.assertNotIn(positional, source, (name, positional))

    def test_a_different_id_produces_a_different_script(self):
        for name, builder in self.BUILDERS:
            self.assertNotEqual(builder().source,
                                type_into_tab(WINDOW_ID + 1, "q").source, name)

    def test_every_call_is_bounded(self):
        for name, builder in self.BUILDERS:
            call = builder()
            self.assertGreater(call.timeout, 0, name)
            self.assertIn("with timeout of", call.source, name)

    def test_the_census_counts_visible_windows_and_not_existing_ones(self):
        source = visible_window_count().source
        self.assertIn("visible is true", source)
        self.assertNotIn("exists", source)

    def test_nothing_here_ever_quits_terminal_or_closes_more_than_one(self):
        for name, builder in self.BUILDERS:
            source = builder().source
            self.assertNotIn("quit", source, name)
            self.assertNotIn("close every", source, name)


class WhatTheExercisesReport(unittest.TestCase):

    def test_a_clean_run_reports_the_game_started_quit_and_left_nothing(self):
        runner, clock = build()
        observations, shown, seen, window = exercise_a_whole_session(
            runner, COMMAND, clock=clock.time, sleeper=clock.sleep)
        self.assertTrue(all(o.ok for o in observations),
                        [str(o) for o in observations])
        self.assertIsNone(window.abandoned)
        self.assertEqual("wall\nwall\n score 0", shown)

    def test_a_run_that_leaves_a_window_says_so_in_the_observation(self):
        runner, clock = build({"window_processes": PLAYING})
        observations, _, _, window = exercise_a_whole_session(
            runner, COMMAND, clock=clock.time, sleeper=clock.sleep)
        left = [o for o in observations if o.codes == ("WIN-5",)]
        self.assertEqual(1, len(left))
        self.assertIn("LEFT OPEN", left[0].detail)

    #: Thirty rows of at most forty columns: SCRN-1's own shape, and what a
    #: real capture looks like. Deliberately not a fixed picture — on `main`
    #: the game process is still M0's skeleton and the real one arrives with
    #: WI-12, so a pinned frame would pass now and fail when the thing it is
    #: meant to check turns up.
    A_FRAME = "\n".join(["x" * 40] * 30)

    def test_a_frame_shaped_capture_is_judged_on_its_shape(self):
        observations = exercise_the_picture(self.A_FRAME)
        fits = [o for o in observations if "fits" in o.name]
        self.assertEqual(1, len(fits))
        self.assertTrue(fits[0].ok)

    def test_a_capture_that_is_not_a_frame_is_reported_rather_than_judged(self):
        # The defect the pack found in itself on its first real run: the
        # process list goes non-empty while the tab is still a shell, and a
        # capture taken then is the shell's echo of a 389-column command line.
        # Judging that as "SCRN-1 fails" would be wrong and alarming.
        observations = exercise_the_picture("$ some enormous command line" * 20)
        self.assertFalse(observations[0].ok)
        self.assertIn("not a frame", observations[0].detail)
        self.assertEqual(1, len(observations))    # nothing else is judged

    def test_a_frame_with_a_row_too_wide_is_reported_as_a_failure(self):
        rows = ["x" * 40] * 29 + ["y" * 41]
        observations = exercise_the_picture("\n".join(rows))
        fits = [o for o in observations if "fits" in o.name]
        self.assertFalse(fits[0].ok)
        self.assertIn("41", fits[0].detail)

    def test_an_empty_capture_is_reported_rather_than_passed_over(self):
        observations = exercise_the_picture("")
        self.assertFalse(observations[0].ok)

    def test_a_shell_is_not_mistaken_for_a_frame_and_a_frame_is(self):
        # The predicate on its own, both ways round.
        self.assertTrue(pack.looks_like_a_frame(self.A_FRAME))
        self.assertFalse(pack.looks_like_a_frame(""))
        self.assertFalse(pack.looks_like_a_frame("\n".join(["x" * 40] * 29)))
        # The shell state it is actually distinguishing from, as captured on
        # the real desktop: a login line and the echo of the command.
        self.assertFalse(pack.looks_like_a_frame(
            "Last login: Mon Sep 14\nexec /bin/sh -c '...'\n% exec ..."))
        # And a frame one column too wide is STILL a frame, so that the width
        # check can report it rather than swallow it.
        self.assertTrue(pack.looks_like_a_frame(
            "\n".join(["x" * 40] * 29 + ["y" * 41])))

    def test_the_window_size_is_reported_as_a_number_for_a_person(self):
        observations = exercise_the_window({"size": Size(357, 558),
                                            "title": "Terminal Game"})
        size = [o for o in observations if o.codes == ("WIN-2",)][0]
        self.assertIsNone(size.ok)          # observed, not judged
        self.assertIn("357 x 558", size.detail)

    def test_the_title_is_reported_and_explicitly_not_verified(self):
        observations = exercise_the_window(
            {"size": Size(357, 558),
             "title": "rodneybailey — Terminal Game — /bin/sh"})
        title = [o for o in observations if o.codes == ("WIN-3",)][0]
        self.assertIsNone(title.ok)
        self.assertIn("NOT VERIFIED", title.detail)

    def test_a_reading_that_failed_is_reported_as_a_failure_not_as_a_number(self):
        observations = exercise_the_window(
            {"size": AutomationError("refused"), "title": AutomationError("refused")})
        for observation in observations:
            self.assertFalse(observation.ok)
            self.assertIn("not read", observation.detail)

    def test_an_observation_renders_its_three_states_distinctly(self):
        self.assertIn("ok", str(Observation("a", ("X-1",), True, "d")))
        self.assertIn("FAIL", str(Observation("a", ("X-1",), False, "d")))
        self.assertIn("note", str(Observation("a", ("X-1",), None, "d")))


class TheCommandLineItself(unittest.TestCase):
    """`python3 -m auto_smoketest`, which nothing reached until now.

    Every line of `__main__.main` was unexecuted by the suite: the entry
    point called `pack.run(game_command())` with no seam, so the only way to
    reach it was a real desktop. That is the same shape as the bug found in
    the register's entry point an hour earlier — a function whose tests all
    called it directly while the command itself was never exercised.
    """

    #: A capture the size SCRN-1 asks for. `HAPPY_PATH`'s is three rows,
    #: which is right for the exercises that never look at it and wrong here:
    #: the whole run reports a failure if no picture was drawn.
    A_REAL_FRAME = "\n".join(["#" * 37 + "   "] * 29
                             + [" score 0    arrows, q quits".ljust(40)])

    def _main(self, argv=None, replies=None):
        merged = {"tab_contents": self.A_REAL_FRAME}
        merged.update(replies or {})
        runner, clock = build(merged)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = smoketest_main(argv or [], runner=runner,
                                  clock=clock.time, sleeper=clock.sleep)
        return code, out.getvalue(), runner

    def test_a_clean_run_reports_and_exits_zero(self):
        code, said, runner = self._main()
        self.assertEqual(0, code)
        self.assertIn("THE EXERCISES", said)
        self.assertIn("the game starts in its window", said)
        self.assertIn("close_window", runner.names)

    def test_it_runs_the_real_game_command_and_only_one_window(self):
        _, _, runner = self._main()
        self.assertIn("terminalgame.game_main",
                      runner.source_of("open_window_running"))
        self.assertEqual(1, len(runner.calls_named("open_window_running")))

    def test_a_failing_exercise_exits_one(self):
        # Nothing ever ran in the tab: the game did not start.
        code, said, _ = self._main(replies={"window_processes": FINISHED})
        self.assertEqual(1, code)
        self.assertIn("FAIL", said)

    def test_a_window_left_open_exits_two_and_names_it(self):
        code, said, runner = self._main(replies={"window_processes": PLAYING})
        self.assertEqual(2, code)
        self.assertIn("WINDOW %d WAS LEFT OPEN" % WINDOW_ID, said)
        self.assertIn("modal sheet", said)
        self.assertNotIn("close_window", runner.names)

    def test_show_picture_prints_the_capture_and_is_off_by_default(self):
        _, without, _ = self._main()
        _, with_it, _ = self._main(["--show-picture"])
        self.assertNotIn("what the tab was showing", without)
        self.assertIn("what the tab was showing", with_it)
        self.assertIn("| score 0", with_it)

    def test_it_sends_the_reader_to_the_other_half(self):
        _, said, _ = self._main()
        self.assertIn("python3 -m manual_smoketest", said)
        self.assertIn(str(len(checks.CODES_NEEDING_A_PERSON)), said)

    def test_the_real_command_line_reaches_it(self):
        # The bug class this class exists for: a `main` whose arguments are
        # only ever supplied by a test passes while the command ignores them.
        runner, clock = build()
        saved = sys.argv
        sys.argv = ["python3 -m auto_smoketest", "--show-picture"]
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                smoketest_main(runner=runner, clock=clock.time,
                               sleeper=clock.sleep)
        finally:
            sys.argv = saved
        self.assertIn("what the tab was showing", out.getvalue())


class TheStaleExecutablesAreNotResurrected(unittest.TestCase):
    """The five at the repository root are off limits, and this is the item
    somebody would be most tempted to raid them for."""

    STALE = ("verify", "launch-smoke", "check-window-placement", "play",
             "Terminal Game")

    def test_the_pack_starts_nothing_but_the_command_it_was_given(self):
        # The property that matters is what it RUNS, not what its prose
        # mentions -- the module docstring names the five precisely in order
        # to say they are not used, and a scan for the names would fail on
        # that sentence. This looks at the only call that starts anything.
        runner, clock = build()
        exercise_a_whole_session(runner, COMMAND, clock=clock.time,
                                 sleeper=clock.sleep)
        starts = runner.calls_named("open_window_running")
        self.assertEqual(1, len(starts))
        self.assertIn(COMMAND, starts[0].source)
        for stale in self.STALE:
            self.assertNotIn(stale, starts[0].source, stale)

    def test_and_starts_it_through_the_desktop_rather_than_a_shell(self):
        # No subprocess, no os.system: everything this pack does to the
        # machine goes through the launcher's one audited seam.
        source = inspect.getsource(pack)
        self.assertNotIn("subprocess", source)
        self.assertNotIn("os.system", source)
        self.assertNotIn("popen", source.lower())

    def test_the_only_thing_it_types_into_a_tab_is_q(self):
        runner, clock = build()
        exercise_a_whole_session(runner, COMMAND, clock=clock.time,
                                 sleeper=clock.sleep)
        for call in runner.calls_named("type_into_tab"):
            self.assertIn('do script "q"', call.source)


if __name__ == "__main__":
    unittest.main()
