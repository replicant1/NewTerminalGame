"""WI-13 — the launcher hardened, and the defect that made it necessary.

Plan §11.2 re-scoped WI-13 from first implementation to hardening and
verification, because DEV-A built the A2 fallbacks into WI-1 — the clamp cannot
function without a screen rectangle, so the fallback was not separable from
WI-1's own outcome. The fallbacks and their failure injection are therefore
already covered in ``tests/test_launcher_lifecycle.py``
(``WhenTheDesktopWillNotSayWhereThePlayerWasLooking`` and
``WhenSetupFailsAfterTheWindowExists``) and are not duplicated here.

What is here is what WI-13 actually adds:

* **the regression** — ``WindowLauncher.run`` used to close the window while
  the game was still in it and report success, because it asked the tab
  whether it was ``busy``;
* **the one-answer property** — there is now exactly one way in this package
  to ask whether something is still running, so the two sides of that seam
  cannot disagree;
* **C2 over C3, revisited** — a window that will not go idle is left open and
  named, because closing it raises the modal sheet that blocks every later
  automation call *including the cleanup itself*.

The real-desktop measurements behind all of this are in
``docs/findings/WI-13-what-actually-breaks-busy.md``.
"""

import inspect
import unittest

import launcher.desktop
import launcher.game
import launcher.lifecycle
import launcher.script
from launcher.desktop import Desktop
from launcher.lifecycle import WindowLauncher
from tests.launcher_fakes import FailingQueryRunner, RecordingRunner
from tests.test_launcher_lifecycle import COMMAND, HAPPY_PATH, WINDOW_ID, build

#: What the tab's process list looks like while the game is in it, as measured
#: against the real command: the login process, and Python under it.
PLAYING = "login|Python"
#: And once it has gone. The launcher ``exec``s, so the login shell is replaced
#: rather than left underneath, and the list empties rather than falling back
#: to a shell.
FINISHED = ""

LAUNCHER_MODULES = (launcher.script, launcher.desktop, launcher.lifecycle,
                    launcher.game)


class TheDefectThatMadeThisItemNecessary(unittest.TestCase):
    """``run`` closed the window with the game still in it, and said "closed".

    Measured on the real desktop, twice: ``busy`` went false at +0.75 s while
    ``login|Python`` ran on to +4.2 s. Nine lying samples per run. A session
    then took the same time whether the game was asked to run for 5 seconds or
    for 12, because in both cases it was killed.
    """

    def test_a_whole_session_does_not_close_a_window_the_game_is_still_in(self):
        # The regression, stated at the level the defect was at: `run`, not
        # `reap`. This is the call that was wrong.
        launcher, runner, _ = build({"window_processes": PLAYING},
                                    session_timeout=2.0, poll_interval=0.5)
        result = launcher.run(COMMAND)
        self.assertFalse(result.closed)
        self.assertNotIn("close_window", runner.names)

    def test_and_does_not_report_success_when_it_has_not_closed_it(self):
        launcher, _, _ = build({"window_processes": PLAYING},
                               session_timeout=2.0, poll_interval=0.5)
        result = launcher.run(COMMAND)
        self.assertFalse(result.closed)
        self.assertIn("still running", result.reason)
        self.assertEqual(WINDOW_ID, result.window_id)

    def test_a_session_that_finishes_normally_still_closes_the_window(self):
        # The pair. Without it, a launcher that never closed anything would
        # satisfy both tests above.
        launcher, runner, _ = build({"window_processes": FINISHED})
        result = launcher.run(COMMAND)
        self.assertTrue(result.closed)
        self.assertIn("close_window", runner.names)

    def test_a_session_waits_for_the_game_and_then_closes(self):
        # And the middle case, which is the one that actually happens: the
        # game runs for a while, then ends, then the window goes.
        launcher, runner, clock = build(
            {"window_processes": [PLAYING, PLAYING, PLAYING, FINISHED]},
            poll_interval=0.25)
        result = launcher.run(COMMAND)
        self.assertTrue(result.closed)
        self.assertEqual(4, len(runner.calls_named("window_processes")))
        self.assertEqual([0.25, 0.25, 0.25], clock.slept)
        self.assertLess(runner.names.index("window_processes"),
                        runner.names.index("close_window"))

    def test_the_session_asks_the_process_list_and_never_the_busy_flag(self):
        launcher, runner, _ = build()
        launcher.run(COMMAND)
        self.assertIn("window_processes", runner.names)
        self.assertNotIn("window_is_busy", runner.names)
        for call in runner.calls:
            self.assertNotIn("busy of selected tab", call.source)


class OneQuestionOneAnswer(unittest.TestCase):
    """Two sides of one seam must not be able to disagree.

    ``busy`` and the process list answered the same question — *is the
    command still running* — and answered it differently. While both existed
    the wrong one was the default, which is how the defect above survived
    being documented. WI-13 removed the wrong one rather than deprecating it.
    """

    def test_nothing_in_the_launcher_reads_the_busy_flag(self):
        for module in LAUNCHER_MODULES:
            for number, line in enumerate(inspect.getsource(module).splitlines(), 1):
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue          # the tombstone comments explain the absence
                self.assertNotIn("busy of selected tab", stripped,
                                 "%s line %d" % (module.__name__, number))

    def test_there_is_no_script_builder_for_it_and_no_desktop_method(self):
        self.assertFalse(hasattr(launcher.script, "window_is_busy"))
        self.assertFalse(hasattr(Desktop, "is_busy"))

    def test_the_one_answer_that_remains_is_the_process_list(self):
        self.assertTrue(hasattr(launcher.script, "window_processes"))
        self.assertTrue(hasattr(Desktop, "processes"))
        self.assertTrue(hasattr(WindowLauncher, "has_live_processes"))

    def test_waiting_defaults_to_it_rather_than_offering_a_choice(self):
        # The parameter stays so a test can inject one; what it must not be is
        # a decision a caller can get wrong, which is what it was.
        launcher, runner, _ = build({"window_processes": FINISHED})
        launcher.wait_until_idle(WINDOW_ID, timeout=1.0)
        self.assertEqual(["window_processes"], runner.names)

    def test_the_default_is_reached_through_the_launcher_not_the_desktop(self):
        # `has_live_processes` is where the reasoning lives, so that is what
        # should be called; going straight to `desktop.processes` would work
        # and would put the "empty means idle" decision in two places.
        source = inspect.getsource(WindowLauncher.wait_until_idle)
        self.assertIn("self.has_live_processes", source)

    def test_an_empty_process_list_is_what_idle_means(self):
        launcher, _, _ = build({"window_processes": FINISHED})
        self.assertFalse(launcher.has_live_processes(WINDOW_ID))

    def test_and_any_process_at_all_means_it_is_not_idle(self):
        for answer in (PLAYING, "Python", "login", "login|Python|tail"):
            launcher, _, _ = build({"window_processes": answer})
            self.assertTrue(launcher.has_live_processes(WINDOW_ID), answer)


class TheWarningIsGoneBecauseTheDefectIs(unittest.TestCase):
    """A warning that outlives its defect teaches readers not to believe them."""

    def test_run_no_longer_warns_that_it_can_kill_the_game(self):
        source = inspect.getdoc(WindowLauncher.run) or ""
        self.assertNotIn("Do not build anything new on it", source)
        self.assertNotIn("WI-13 deletes this warning", source)

    def test_run_still_says_what_it_waits_on_and_why(self):
        # Deleting the warning must not delete the knowledge. Somebody will
        # one day wonder why this does not use `busy`, and the answer should
        # be here rather than only in a finding.
        source = inspect.getdoc(WindowLauncher.run) or ""
        self.assertIn("has_live_processes", source)
        self.assertIn("busy", source)


class NothingSurvivesAFailure(unittest.TestCase):
    """Caution C3, over every stage that can fail after the window exists."""

    STAGES = ("configure_window", "window_size", "set_window_position")

    def test_a_failure_at_any_stage_closes_the_captured_window(self):
        for stage in self.STAGES:
            runner = FailingQueryRunner([stage], HAPPY_PATH)
            launcher, runner, _ = build(runner=runner)
            with self.assertRaises(Exception):
                launcher.open(COMMAND)
            self.assertIn("close_window", runner.names, stage)
            self.assertIn("window id %d" % WINDOW_ID,
                          runner.source_of("close_window"), stage)

    def test_it_closes_the_captured_identity_and_never_a_positional_one(self):
        for stage in self.STAGES:
            runner = FailingQueryRunner([stage], HAPPY_PATH)
            launcher, runner, _ = build(runner=runner)
            try:
                launcher.open(COMMAND)
            except Exception:
                pass
            source = runner.source_of("close_window")
            for phrase in ("front window", "window 1", "first window",
                           "last window", "every window", "frontmost"):
                self.assertNotIn(phrase, source, (stage, phrase))

    def test_a_failure_before_the_window_exists_closes_nothing(self):
        # The converse. A launcher that closed something on every failure
        # would pass the tests above and be dangerous, because before the
        # creation call there is no window of ours to close.
        runner = FailingQueryRunner(["open_window_running"], HAPPY_PATH)
        launcher, runner, _ = build(runner=runner)
        with self.assertRaises(Exception):
            launcher.open(COMMAND)
        self.assertNotIn("close_window", runner.names)


class C2BeatsC3WhenTheyDisagree(unittest.TestCase):
    """Plan §11.3 — and the reason is that "reap anyway" does not even reap.

    These two cautions give opposite instructions when setup fails while the
    game is still running. Closing a busy window raises a modal sheet only a
    person can dismiss, and while it is up every automation call hangs behind
    it — including the cleanup. So the window is left, and its id is named.
    """

    def test_a_window_that_will_not_go_idle_is_left_open(self):
        launcher, runner, _ = build({"window_processes": PLAYING},
                                    poll_interval=0.5)
        result = launcher.reap(WINDOW_ID, timeout=2.0)
        self.assertFalse(result.closed)
        self.assertNotIn("close_window", runner.names)

    def test_and_its_identity_is_named_so_a_person_can_deal_with_it(self):
        launcher, _, _ = build({"window_processes": PLAYING}, poll_interval=0.5)
        result = launcher.reap(WINDOW_ID, timeout=2.0)
        self.assertEqual(WINDOW_ID, result.window_id)
        self.assertIn(str(WINDOW_ID), result.reason)

    def test_and_the_reason_says_why_rather_than_only_what(self):
        launcher, _, _ = build({"window_processes": PLAYING}, poll_interval=0.5)
        result = launcher.reap(WINDOW_ID, timeout=2.0)
        self.assertIn("modal sheet", result.reason)
        self.assertIn("hang", result.reason)

    def test_the_wait_is_bounded_and_gives_up(self):
        launcher, runner, clock = build({"window_processes": PLAYING},
                                        poll_interval=0.5)
        launcher.reap(WINDOW_ID, timeout=2.0)
        self.assertLessEqual(clock.now, 2.5)
        self.assertLess(len(runner.calls_named("window_processes")), 10)

    def test_a_window_it_cannot_even_ask_about_is_not_closed(self):
        # A refused query is not an idle window. Guessing here is how a live
        # game gets killed by a launcher that could not see it.
        runner = FailingQueryRunner(["window_processes"], HAPPY_PATH)
        launcher, runner, _ = build(runner=runner)
        result = launcher.reap(WINDOW_ID, timeout=1.0)
        self.assertFalse(result.closed)
        self.assertNotIn("close_window", runner.names)

    def test_reaping_never_raises_whatever_the_desktop_does(self):
        # It runs on the failure path, where an exception of its own would
        # bury the failure it was called to clean up after.
        for stage in ("window_processes", "close_window", "window_is_visible"):
            runner = FailingQueryRunner([stage], HAPPY_PATH)
            launcher, _, _ = build(runner=runner)
            result = launcher.reap(WINDOW_ID, timeout=1.0)
            self.assertTrue(result.reason, stage)
            self.assertEqual(WINDOW_ID, result.window_id, stage)

    def test_a_refusal_before_the_close_means_the_window_is_still_there(self):
        for stage in ("window_processes", "close_window"):
            runner = FailingQueryRunner([stage], HAPPY_PATH)
            launcher, _, _ = build(runner=runner)
            self.assertFalse(launcher.reap(WINDOW_ID, timeout=1.0).closed, stage)

    def test_a_refusal_of_only_the_confirmation_still_counts_as_closed(self):
        # The distinction is worth keeping rather than flattening. The close
        # itself succeeded; what failed was reading back whether the window
        # went. Reporting "not closed" would send a person looking for a
        # window that is almost certainly gone, so it reports closed and says
        # in the reason that it could not check.
        runner = FailingQueryRunner(["window_is_visible"], HAPPY_PATH)
        launcher, runner, _ = build(runner=runner)
        result = launcher.reap(WINDOW_ID, timeout=1.0)
        self.assertTrue(result.closed)
        self.assertIn("could not be checked", result.reason)
        self.assertIn("close_window", runner.names)


class AGameNothingBoundsButAPerson(unittest.TestCase):
    """What happens when the command genuinely never ends.

    M0's `--hold` was scaffolding and the technical lead said it was not a
    precedent: the real game exits on `q` and never on a timer. So once the
    hold goes, **the launched command is bounded by nothing the launcher
    controls** — a player at the keyboard is the only thing that ends it.

    That is correct for a game, and it is safe here only because of the
    obligation this item exists for: the launcher waits on the process list
    and never closes a window something is running in. These tests pin what
    happens at the end of that wait, because it is no longer hypothetical.

    **Anything that starts a game with nobody at the keyboard must arrange its
    own way out.** That is WI-14a's to carry.
    """

    def test_a_game_that_never_ends_is_never_closed_out_from_under_it(self):
        launcher, runner, _ = build({"window_processes": PLAYING},
                                    session_timeout=3.0, poll_interval=0.5)
        result = launcher.run(COMMAND)
        self.assertFalse(result.closed)
        self.assertNotIn("close_window", runner.names)

    def test_the_wait_still_ends_rather_than_hanging_for_ever(self):
        # Caution C4. The game may be unbounded; the launcher's patience is
        # not, or `run` would never return and nothing could report anything.
        launcher, _, clock = build({"window_processes": PLAYING},
                                   session_timeout=3.0, poll_interval=0.5)
        launcher.run(COMMAND)
        self.assertLessEqual(clock.now, 3.5)

    def test_and_the_window_it_left_behind_is_named_in_the_result(self):
        # An orphan window is a nuisance a person closes in one gesture. An
        # orphan window nobody can identify is a hunt.
        launcher, _, _ = build({"window_processes": PLAYING},
                               session_timeout=3.0, poll_interval=0.5)
        result = launcher.run(COMMAND)
        self.assertEqual(WINDOW_ID, result.window_id)
        self.assertIn(str(WINDOW_ID), result.reason)

    def test_a_player_pressing_q_gives_the_ordinary_ending(self):
        # The pair: the unbounded game does end, when a person ends it, and
        # then everything above gives way to the normal path. Without this,
        # a launcher that never closed anything would pass all three.
        launcher, runner, _ = build(
            {"window_processes": [PLAYING, PLAYING, FINISHED]},
            session_timeout=30.0, poll_interval=0.25)
        result = launcher.run(COMMAND)
        self.assertTrue(result.closed)
        self.assertIn("close_window", runner.names)


class TheAskingSlowsDown(unittest.TestCase):
    """The launcher watches a game for as long as a person plays it.

    Every ask is an `osascript` process and an Apple event to Terminal, and
    `wait_until_idle` runs from the moment the window opens until the player
    presses `q`. At a tenth of a second that is thousands of processes beside
    the game, for the whole of it. So the loop asks quickly while the answer
    is still likely to be changing, and then settles.
    """

    def test_it_asks_quickly_while_the_window_is_still_settling(self):
        # The fast phase is the one that matters for correctness: a command
        # that fails at once, or a login shell that has not started yet,
        # resolves within a second or two of the window being created.
        launcher, _, clock = build({"window_processes": [PLAYING] * 5 + [FINISHED]},
                                   poll_interval=0.1, settle_after=2.0,
                                   settled_poll_interval=1.0)
        self.assertTrue(launcher.wait_until_idle(WINDOW_ID, timeout=60.0))
        self.assertEqual([0.1, 0.1, 0.1, 0.1, 0.1], clock.slept)

    def test_and_settles_once_the_window_is_plainly_just_running_a_game(self):
        launcher, _, clock = build({"window_processes": PLAYING},
                                   poll_interval=0.1, settle_after=2.0,
                                   settled_poll_interval=1.0)
        launcher.wait_until_idle(WINDOW_ID, timeout=10.0)
        fast = [nap for nap in clock.slept if nap == 0.1]
        settled = [nap for nap in clock.slept if nap == 1.0]
        # Twenty at a tenth of a second covers the first two seconds, then it
        # settles: eight more covers the remaining eight.
        self.assertEqual(20, len(fast))
        self.assertEqual(8, len(settled))
        self.assertEqual(clock.slept, fast + settled,
                         "the fast asks all come first")

    def test_a_long_game_costs_far_fewer_asks_than_a_flat_poll_would(self):
        # The point of the whole thing, stated as the number it saves. Ten
        # minutes at a flat tenth of a second is 6,000 asks.
        launcher, _, clock = build({"window_processes": PLAYING},
                                   poll_interval=0.1, settle_after=2.0,
                                   settled_poll_interval=1.0)
        launcher.wait_until_idle(WINDOW_ID, timeout=600.0)
        self.assertLess(len(clock.slept), 700)
        self.assertGreater(6000 / float(len(clock.slept)), 8.0,
                           "should be most of an order of magnitude cheaper")

    def test_settling_does_not_loosen_the_bound_it_was_given(self):
        # Caution C4. A slower poll must not mean overshooting the deadline by
        # most of an interval -- the last sleep is cut to what is left.
        launcher, _, clock = build({"window_processes": PLAYING},
                                   poll_interval=0.1, settle_after=2.0,
                                   settled_poll_interval=1.0)
        self.assertFalse(launcher.wait_until_idle(WINDOW_ID, timeout=2.5))
        self.assertEqual(2.5, clock.now)

    def test_a_caller_that_asks_for_a_slow_poll_is_not_given_a_fast_one(self):
        # `poll_interval` is a floor as well as the opening speed, so settling
        # can only ever slow the loop down. Here the settled interval is the
        # SHORTER of the two and is correctly ignored: every ask stays 2.0s
        # apart. The trailing 1.0 is not the settled interval reasserting
        # itself, it is the last sleep being cut to the 1.0s left before the
        # deadline.
        launcher, _, clock = build({"window_processes": PLAYING},
                                   poll_interval=2.0, settle_after=2.0,
                                   settled_poll_interval=1.0)
        launcher.wait_until_idle(WINDOW_ID, timeout=9.0)
        self.assertEqual([2.0, 2.0, 2.0, 2.0, 1.0], clock.slept)
        self.assertEqual(9.0, clock.now)


class GoingIsCheckedWithVisible(unittest.TestCase):
    """Measured in WI-3: Terminal keeps a window addressable after a close."""

    def test_the_check_after_a_close_reads_visible(self):
        launcher, runner, _ = build()
        launcher.run(COMMAND)
        self.assertIn("visible", runner.source_of("window_is_visible"))

    def test_it_does_not_read_exists(self):
        launcher, runner, _ = build()
        launcher.run(COMMAND)
        self.assertNotIn("exists", runner.source_of("window_is_visible"))

    def test_a_window_still_visible_after_the_close_is_not_reported_reaped(self):
        launcher, _, _ = build({"window_is_visible": "true"})
        result = launcher.run(COMMAND)
        self.assertFalse(result.closed)

    def test_a_window_that_went_is_reported_reaped(self):
        launcher, _, _ = build({"window_is_visible": "false"})
        self.assertTrue(launcher.run(COMMAND).closed)


class EveryCallIsStillBounded(unittest.TestCase):
    """Caution C4 — nothing the launcher issues can wait for ever."""

    def test_every_script_this_item_touched_carries_a_timeout(self):
        for builder, arguments in (
                (launcher.script.window_processes, (WINDOW_ID,)),
                (launcher.script.close_window, (WINDOW_ID,)),
                (launcher.script.window_is_visible, (WINDOW_ID,))):
            call = builder(*arguments)
            self.assertGreater(call.timeout, 0, builder.__name__)
            self.assertIn("with timeout of", call.source, builder.__name__)

    def test_the_poll_loop_cannot_run_for_ever_even_if_nothing_changes(self):
        launcher, runner, clock = build({"window_processes": PLAYING},
                                        poll_interval=0.1)
        launcher.wait_until_idle(WINDOW_ID, timeout=1.0)
        self.assertLessEqual(clock.now, 1.2)


if __name__ == "__main__":
    unittest.main()
