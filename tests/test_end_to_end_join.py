"""WI-3 — the launcher and the game, joined.

WI-1's tests proved the launcher behaves for *some* command; WI-2's proved the
game behaves in *some* terminal. These are about the join: that the window the
launcher opens is running the real game, that the whole session closes the
window it opened by the identity it captured, and that the launcher does not
take the window away while the game is still being played.

The seam is the subprocess runner, so what these tests read is the AppleScript
that would have reached the desktop, in the order it would have reached it.

The process lists below are the ones measured on the real desktop: a tab whose
login shell is still starting up lists that shell, a tab running the game lists
``login|Python``, and a tab whose command has ended lists nothing at all.
"""

import io
import re
import unittest

from launcher.desktop import Desktop
from launcher.game import GAME_MODULE, game_command, main, play
from launcher.lifecycle import LaunchFailed, WindowLauncher
from launcher.runner import AutomationError
from tests.launcher_fakes import FakeClock, RecordingRunner

WINDOW_ID = 4211

#: What the tab lists while the login shell is still starting up. Non-empty,
#: which is what stops it being mistaken for a window whose game has ended.
STARTING = "login|-zsh|ssh-add"
#: What it lists while the game is running.
PLAYING = "login|Python"
#: What it lists once the game has exited. The launcher execs the command, so
#: there is no shell left underneath it to keep the list populated.
FINISHED = ""


def honours_the_move(call):
    x, y = re.search(r"to \{(-?\d+), (-?\d+)\}", call.source).groups()
    return "%s,%s" % (x, y)


HAPPY_PATH = {
    "reference_window_geometry": "400,300,1000,800",
    "visible_screen_bounds": "0,0,1440,900",
    "open_window_running": str(WINDOW_ID),
    "configure_window": "ok",
    "window_size": "357,558",
    "set_window_position": honours_the_move,
    "close_window": "closed",
    "window_is_visible": "false",
    # The reap that runs *inside* WindowLauncher.open when setup fails is WI-1's
    # and still asks the busy flag. That path is reached only by the failure
    # tests below; the session path uses the process list throughout.
    "window_is_busy": "false",
}

#: Ways of naming a window that are not the captured identity. None of these may
#: appear in anything the launcher sends after the window exists (caution C1).
POSITIONAL_OR_TITLE = (
    "front window",
    "frontmost",
    "window 1",
    "first window",
    "last window",
    "custom title is",
    "whose name",
)


def playing_then_finished():
    """A window running the game, and then not.

    A function rather than a list of answers because the number of times the
    launcher asks is exactly what several of these tests are about, and a list
    would run out and turn a behavioural difference into a fixture error.
    """
    asked = []

    def answer(call):
        asked.append(call)
        return PLAYING if len(asked) == 1 else FINISHED

    return answer


def build(replies=None, **kwargs):
    merged = dict(HAPPY_PATH)
    merged["window_processes"] = playing_then_finished()
    merged.update(replies or {})
    runner = RecordingRunner(merged)
    clock = FakeClock()
    launcher = WindowLauncher(
        Desktop(runner), clock=clock.time, sleeper=clock.sleep, **kwargs
    )
    return launcher, runner


class TheWindowRunsTheRealGame(unittest.TestCase):

    def test_the_window_is_created_running_the_game_process(self):
        launcher, runner = build()
        play(launcher, game_command())
        self.assertIn(GAME_MODULE, runner.source_of("open_window_running"))

    def test_the_game_is_started_with_a_bounded_lifetime(self):
        """Nothing the launcher opens may sit there for ever waiting on a
        person who has walked away — there would be no way to end it."""
        launcher, runner = build()
        play(launcher, game_command(hold_seconds=9))
        self.assertIn("--hold 9", runner.source_of("open_window_running"))

    def test_the_game_is_the_only_command_the_window_is_given(self):
        launcher, runner = build()
        play(launcher, game_command())
        self.assertEqual(1, len(runner.calls_named("open_window_running")))


class AWholeCleanSession(unittest.TestCase):

    def test_it_asks_creates_configures_places_waits_and_closes_in_that_order(self):
        launcher, runner = build()
        play(launcher, game_command())
        self.assertEqual(
            [
                "reference_window_geometry",
                "visible_screen_bounds",
                "open_window_running",
                "configure_window",
                "window_size",
                "set_window_position",
                "window_processes",   # still playing
                "window_processes",   # finished
                "close_window",
                "window_is_visible",
            ],
            runner.names,
        )

    def test_nothing_is_left_on_the_desktop(self):
        launcher, runner = build()
        result = play(launcher, game_command())
        self.assertTrue(result.closed)
        self.assertEqual(WINDOW_ID, result.window_id)

    def test_the_player_is_measured_before_the_game_window_exists(self):
        # Once the game's own window is open it is the frontmost one, and the
        # launcher would be placing the window relative to itself.
        launcher, runner = build()
        play(launcher, game_command())
        self.assertLess(
            runner.names.index("reference_window_geometry"),
            runner.names.index("open_window_running"),
        )
        self.assertNotIn(
            "reference_window_geometry",
            runner.names[runner.names.index("open_window_running") + 1:],
        )

    def test_every_call_after_creation_names_the_captured_identity(self):
        launcher, runner = build()
        play(launcher, game_command())
        for source in runner.sources_after("open_window_running"):
            self.assertIn("window id %d" % (WINDOW_ID,), source)

    def test_no_call_after_creation_names_a_window_by_position_or_title(self):
        launcher, runner = build()
        play(launcher, game_command())
        for source in runner.sources_after("open_window_running"):
            for phrase in POSITIONAL_OR_TITLE:
                self.assertNotIn(phrase, source)

    def test_the_close_is_confirmed_with_visible_rather_than_exists(self):
        # Terminal keeps a window object addressable after a close, so `exists`
        # would answer true for a window that has gone.
        launcher, runner = build()
        play(launcher, game_command())
        self.assertIn(
            "visible of window id %d" % (WINDOW_ID,),
            runner.source_of("window_is_visible"),
        )

    def test_every_call_is_bounded(self):
        launcher, runner = build()
        play(launcher, game_command())
        for call in runner.calls:
            self.assertGreater(call.timeout, 0)
            self.assertIn("with timeout of", call.source)


class TheGameIsNotInterruptedWhileItIsBeingPlayed(unittest.TestCase):
    """The defect this join was written to find.

    Terminal's ``busy`` flag stops tracking the process running in a tab once
    that tab has been given a fixed number of rows and columns — and WIN-2
    requires exactly that, so it is true of every window this launcher creates.
    Measured: the game alive from +0.9 s to +8.4 s with ``busy`` false from
    +0.9 s onwards. A launcher that believes ``busy`` closes the window on the
    player mid-game.

    The process list keeps telling the truth, so that is what the join asks.
    """

    def test_a_window_still_running_the_game_is_not_closed(self):
        launcher, runner = build(
            {"window_processes": [PLAYING, PLAYING, FINISHED]},
            session_timeout=60.0,
        )
        result = play(launcher, game_command())
        self.assertTrue(result.closed)
        self.assertEqual(3, len(runner.calls_named("window_processes")))

    def test_the_close_comes_after_the_last_sign_of_life_and_not_before(self):
        launcher, runner = build(
            {"window_processes": [PLAYING, PLAYING, FINISHED]},
            session_timeout=60.0,
        )
        play(launcher, game_command())
        last_answer = (
            len(runner.names) - 1 - runner.names[::-1].index("window_processes")
        )
        self.assertLess(last_answer, runner.names.index("close_window"))

    def test_a_window_that_has_not_started_yet_is_not_taken_for_a_finished_one(self):
        """A window exists before its command does.

        The terminal creates the window, a login shell starts up inside it, and
        only then does the game begin. A launcher that reads "nothing running"
        during that gap closes the window before the game ever draws anything.
        """
        launcher, runner = build(
            {"window_processes": [STARTING, STARTING, PLAYING, FINISHED]},
            session_timeout=60.0,
        )
        result = play(launcher, game_command())
        self.assertTrue(result.closed)
        # All four answers were needed: neither start-up reading was taken for
        # the game having ended.
        self.assertEqual(4, len(runner.calls_named("window_processes")))
        self.assertEqual(
            runner.names.index("close_window"),
            runner.names.index("window_processes") + 4,
        )

    def test_an_empty_process_list_is_what_means_it_is_over(self):
        launcher, runner = build({"window_processes": FINISHED})
        result = play(launcher, game_command())
        self.assertTrue(result.closed)
        self.assertEqual(1, len(runner.calls_named("window_processes")))


class TheGameThatWillNotStop(unittest.TestCase):
    """Caution C2 beats caution C3 — plan §11.3."""

    def test_a_window_still_running_something_is_left_alone(self):
        launcher, runner = build(
            {"window_processes": PLAYING}, session_timeout=1.0
        )
        result = play(launcher, game_command())
        self.assertFalse(result.closed)
        self.assertEqual([], runner.calls_named("close_window"))

    def test_the_window_it_could_not_take_back_is_named_so_a_human_can(self):
        launcher, runner = build(
            {"window_processes": PLAYING}, session_timeout=1.0
        )
        result = play(launcher, game_command())
        self.assertEqual(WINDOW_ID, result.window_id)
        self.assertIn(str(WINDOW_ID), result.reason)

    def test_giving_up_is_bounded_by_the_timeout_it_was_given(self):
        """One ask every 0.25s for 1.0s: at 0, 0.25, 0.5, 0.75 and 1.0.

        Pinned to the exact budget rather than "more than one", so a change that
        made the launcher poll for ever fails here rather than passing. A
        quarter of a second because it is exact in binary — with 0.1 the fake
        clock accumulates to 0.9999999999999999 and buys itself a twelfth poll,
        putting floating-point drift into the expected number.
        """
        launcher, runner = build(
            {"window_processes": PLAYING},
            session_timeout=1.0,
            poll_interval=0.25,
        )
        play(launcher, game_command())
        self.assertEqual(5, len(runner.calls_named("window_processes")))


class WhenSetupFailsWithTheGameAlreadyStarted(unittest.TestCase):

    def test_the_captured_window_is_still_reaped_by_its_own_identity(self):
        launcher, runner = build(
            {"configure_window": AutomationError("the desktop said no")}
        )
        with self.assertRaises(LaunchFailed) as caught:
            play(launcher, game_command())
        self.assertEqual(WINDOW_ID, caught.exception.window_id)
        self.assertIn(
            "window id %d" % (WINDOW_ID,), runner.source_of("close_window")
        )

    def test_a_failure_while_the_game_is_running_leaves_the_window_open(self):
        launcher, runner = build(
            {
                "configure_window": AutomationError("the desktop said no"),
                "window_is_busy": "true",
            },
            failure_timeout=0.5,
        )
        with self.assertRaises(LaunchFailed) as caught:
            play(launcher, game_command())
        self.assertFalse(caught.exception.reap.closed)
        self.assertEqual([], runner.calls_named("close_window"))
        self.assertIn(str(WINDOW_ID), str(caught.exception))


class TheJoinReportsWhatItDid(unittest.TestCase):
    """``python3 -m launcher.game`` end to end, seam and all."""

    def test_a_clean_session_succeeds_and_says_the_window_closed(self):
        launcher, runner = build()
        out = io.StringIO()
        status = main([], launcher=launcher, out=out)
        self.assertEqual(0, status)
        self.assertIn(str(WINDOW_ID), out.getvalue())
        self.assertIn(GAME_MODULE, runner.source_of("open_window_running"))

    def test_the_hold_on_the_command_line_reaches_the_window(self):
        launcher, runner = build()
        main(["--hold", "2"], launcher=launcher, out=io.StringIO())
        self.assertIn("--hold 2", runner.source_of("open_window_running"))

    def test_a_window_left_open_is_reported_as_a_failure(self):
        launcher, _ = build(
            {"window_processes": PLAYING}, session_timeout=1.0
        )
        out = io.StringIO()
        self.assertEqual(1, main([], launcher=launcher, out=out))
        self.assertIn(str(WINDOW_ID), out.getvalue())

    def test_a_failed_launch_names_the_window_on_the_error_stream(self):
        launcher, _ = build(
            {"configure_window": AutomationError("the desktop said no")}
        )
        err = io.StringIO()
        self.assertEqual(1, main([], launcher=launcher, err=err))
        self.assertIn(str(WINDOW_ID), err.getvalue())


class AskingWhatIsRunningInTheWindow(unittest.TestCase):
    """The signal itself: the script it sends and the answers it understands."""

    def test_it_asks_the_captured_window_and_no_other(self):
        launcher, runner = build()
        play(launcher, game_command())
        source = runner.calls_named("window_processes")[0].source
        self.assertIn(
            "processes of selected tab of window id %d" % (WINDOW_ID,), source
        )

    def test_an_empty_answer_means_nothing_is_running(self):
        _, runner = build({"window_processes": ""})
        self.assertEqual([], Desktop(runner).processes(WINDOW_ID))

    def test_the_names_come_back_separated(self):
        _, runner = build({"window_processes": "login|Python"})
        self.assertEqual(["login", "Python"], Desktop(runner).processes(WINDOW_ID))

    def test_a_window_that_has_gone_away_is_running_nothing(self):
        # The script answers with an empty list rather than failing, because
        # nothing is running in a window that no longer exists.
        launcher, runner = build({"window_processes": ""})
        self.assertFalse(launcher.has_live_processes(WINDOW_ID))

    def test_a_window_running_the_game_is_running_something(self):
        launcher, runner = build({"window_processes": PLAYING})
        self.assertTrue(launcher.has_live_processes(WINDOW_ID))


if __name__ == "__main__":
    unittest.main()
