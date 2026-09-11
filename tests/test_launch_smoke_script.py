"""``./launch-smoke`` — the one-command smoke, driven without a real window.

The smoke's *own* value is that it opens a real window; that run is a human
check and cannot live in the suite. What *can* live here is everything the
smoke decides: that it learns the window id from the supervisor rather than by
enumerating windows, that it waits for the window to be configured before
reading the title back, that it reaps the window when a check fails, that it
never forces a busy tab, and that every command it causes to be issued obeys
§2.6 rule 1.

So the whole smoke is run here with ``window.run_osascript`` replaced. No
window is opened by this file.

The stand-in child it writes is also checked here, because two properties of
it are load-bearing and neither is obvious: it must be named literally
``Terminal Game`` (Terminal composes the title from the active process name)
and it must **end by itself**. A child that blocks for ever is a window that
cannot be closed without Terminal's modal confirmation sheet, which only a
human can dismiss and which blocks every later AppleScript call in the system.
"""

import importlib.machinery
import importlib.util
import io
import os
import stat
import unittest

from termgame import window

from test_window_failure_paths import (  # the fake Terminal, and §2.6 rule 1
    ENDED,
    NEW_WINDOW_ID,
    PLAYING,
    FakeClock,
    RecordingTerminal,
    SOMEBODY_ELSES_WINDOW_IDS,
    assert_addresses_only_our_window,
    classify,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SMOKE_PATH = os.path.join(REPO_ROOT, "launch-smoke")


def load_smoke():
    """Import ``launch-smoke``, which has no ``.py`` extension by design."""
    loader = importlib.machinery.SourceFileLoader("launch_smoke", SMOKE_PATH)
    spec = importlib.util.spec_from_loader("launch_smoke", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


smoke = load_smoke()


class TheSmokeIsAnExecutableLikeTheOthers(unittest.TestCase):
    def test_it_is_executable_and_names_the_pinned_interpreter(self):
        mode = os.stat(SMOKE_PATH).st_mode
        self.assertTrue(mode & stat.S_IXUSR, "launch-smoke is not executable")
        self.assertTrue(mode & stat.S_IXOTH)
        with open(SMOKE_PATH, "rb") as handle:
            self.assertEqual(b"#!/usr/bin/python3\n", handle.readline())

    def test_it_runs_in_one_command_with_no_arguments(self):
        # "A repeatable launch smoke the conductor and the user can run in one
        # command." Defaults, not a recipe.
        parsed = smoke.main.__doc__  # no required arguments
        self.assertIsNone(parsed)
        self.assertEqual(1, smoke.run_once.__code__.co_argcount - 2)


class TheStandInChild(unittest.TestCase):
    """Why it is a stand-in, and what makes it safe."""

    def test_it_is_named_exactly_terminal_game(self):
        # WIN-3 rests on the file name: Terminal composes the window title
        # from the active process name. A differently-named stand-in would
        # smoke-test a title the real game never shows.
        self.assertEqual("Terminal Game", window.CHILD_NAME)

    def test_its_first_write_clears_the_working_directory_prefix(self):
        source = smoke.child_source(1.0)
        first_write = source.index("sys.stdout.write")
        self.assertIn("\\033]7;\\007", source[first_write : first_write + 60])

    def test_it_ends_by_itself_and_never_blocks_for_ever(self):
        # §2.6 rule 4. If this ever gains an input(), a read, a cat or an
        # unbounded wait, the smoke gains a window it cannot close.
        source = smoke.child_source(1.0)
        for forbidden in ("input(", "sys.stdin", "os.read", "while True"):
            self.assertNotIn(forbidden, source, "the stand-in child can block")
        self.assertIn("time.sleep(1.0)", source)

    def test_the_child_it_writes_really_does_exit(self):
        # Run it. Not in a window -- just as a process, with no tty.
        import subprocess
        import tempfile

        directory = tempfile.mkdtemp(prefix="termgame-smoke-test-")
        path = os.path.join(directory, window.CHILD_NAME)
        try:
            with open(path, "w") as handle:
                handle.write(smoke.child_source(0.1))
            os.chmod(path, 0o755)
            done = subprocess.run(
                [path],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=20,
            )
            self.assertEqual(0, done.returncode, done.stderr)
            self.assertTrue(done.stdout.startswith(b"\x1b]7;\x07"))
        finally:
            if os.path.exists(path):
                os.remove(path)
            os.rmdir(directory)

    def test_the_child_lives_long_enough_for_the_read_backs(self):
        # Two osascript round trips, measured at roughly 0.2s each.
        self.assertGreaterEqual(smoke.CHILD_SECONDS, 1.0)
        self.assertLessEqual(smoke.CHILD_SECONDS, 10.0)


class TheSmokeRun(unittest.TestCase):
    """The whole of ``run_once``, with Terminal replaced. Opens no window."""

    def setUp(self):
        self.real_run = window.run_osascript
        self.real_displays = window.displays
        self.real_tty = window.controlling_tty
        self.real_sleep = window._sleep
        self.real_now = window._now
        self.real_startup = window.STARTUP_GRACE_SECONDS
        # A clock that only moves when something sleeps: the clean-up's ten
        # second grace is then exercised in full, in a few milliseconds.
        self.clock = FakeClock()
        window._sleep = self.clock.sleep
        window._now = self.clock.monotonic
        window.STARTUP_GRACE_SECONDS = 0.0
        window.displays = lambda report=None: [(0, 0, 1512, 982)]
        window.controlling_tty = lambda: "/dev/ttys009"
        self.real_title_seconds = smoke.TITLE_SECONDS
        self.real_title_poll = smoke.TITLE_POLL_SECONDS
        smoke.TITLE_SECONDS = 0.0
        smoke.TITLE_POLL_SECONDS = 0.0
        self.out = io.StringIO()

    def tearDown(self):
        window.run_osascript = self.real_run
        window.displays = self.real_displays
        window.controlling_tty = self.real_tty
        window._sleep = self.real_sleep
        window._now = self.real_now
        window.STARTUP_GRACE_SECONDS = self.real_startup
        smoke.TITLE_SECONDS = self.real_title_seconds
        smoke.TITLE_POLL_SECONDS = self.real_title_poll

    def run_smoke(self, terminal, timeout=20.0):
        window.run_osascript = terminal
        return smoke.run_once(out=self.out, child_seconds=0.0, timeout=timeout)

    def healthy(self, **kwargs):
        return RecordingTerminal(states=[PLAYING, ENDED], **kwargs)

    # -- the happy path ----------------------------------------------------

    def test_a_clean_run_passes_every_check(self):
        result = self.run_smoke(self.healthy())
        self.assertTrue(
            result.passed,
            "\n".join(str(check) for check in result.checks),
        )
        self.assertEqual(NEW_WINDOW_ID, result.window_id)

    def test_it_checks_the_title_the_size_and_the_font(self):
        result = self.run_smoke(self.healthy())
        names = " ".join(check.name for check in result.checks)
        self.assertIn("'Terminal Game'", names)
        self.assertIn("40 x 30 in Menlo-Regular 18", names)

    def test_it_censuses_the_visible_windows_before_and_after(self):
        result = self.run_smoke(self.healthy())
        self.assertEqual(sorted(SOMEBODY_ELSES_WINDOW_IDS), sorted(result.before))
        self.assertEqual(sorted(result.before), sorted(result.after))
        self.assertNotIn(NEW_WINDOW_ID, result.after)

    def test_the_window_id_comes_from_the_supervisor_not_from_a_census(self):
        # The census answers with four of the user's windows and never with
        # ours, so a smoke that guessed "the new one" from the census would
        # find nothing. This passes only because the id arrived through
        # on_window_opened.
        terminal = self.healthy(new_window_id=31337)
        result = self.run_smoke(terminal)
        self.assertEqual(31337, result.window_id)
        self.assertTrue(result.passed)

    # -- the rule that matters most ---------------------------------------

    def test_no_command_the_smoke_issues_touches_anybody_elses_window(self):
        terminal = self.healthy()
        self.run_smoke(terminal)
        assert_addresses_only_our_window(
            self, terminal.scripts, NEW_WINDOW_ID
        )

    def test_it_confirms_the_close_with_visible_and_never_with_exists(self):
        terminal = self.healthy()
        self.run_smoke(terminal)
        for script in terminal.scripts:
            self.assertNotIn("exists", script)
        self.assertTrue(
            [s for s in terminal.scripts if "visible of (first window" in s]
        )

    # -- the failure paths -------------------------------------------------

    def test_a_wrong_title_fails_the_run_and_says_what_it_read(self):
        result = self.run_smoke(self.healthy(window_name="bash — Terminal Game"))
        self.assertFalse(result.passed)
        self.assertTrue(
            [c for c in result.checks if not c.ok and "Terminal Game" in c.detail]
        )

    def test_a_wrong_tab_size_fails_the_run(self):
        result = self.run_smoke(self.healthy(geometry="80 24 Menlo-Regular 18"))
        self.assertFalse(result.passed)
        self.assertTrue([c for c in result.checks if not c.ok and "80" in c.detail])

    def test_a_window_that_stays_visible_fails_the_run(self):
        result = self.run_smoke(self.healthy(visible_after_close="true"))
        self.assertFalse(result.passed)
        self.assertTrue(
            [c for c in result.checks if not c.ok and "still on the screen" in c.detail]
        )

    def test_a_census_that_does_not_reconcile_fails_the_run(self):
        terminal = self.healthy()

        real_answer = terminal._answer

        def answer(script):
            value = real_answer(script)
            if classify(script) == "census" and terminal.closed:
                # One of the user's windows vanished during the run. Whatever
                # caused that, the smoke must not report PASS.
                #
                # Recognised through ``classify`` rather than by a substring of
                # the census script: WI-10a rewrote that script and a literal
                # here silently stopped matching, which turned this test green
                # against a smoke that was no longer being lied to at all.
                return ", ".join(str(each) for each in terminal.census[1:])
            return value

        terminal._answer = answer
        result = self.run_smoke(terminal)
        self.assertFalse(result.passed)
        self.assertTrue(
            [c for c in result.checks if not c.ok and "before" in c.detail]
        )

    def test_a_supervisor_that_raises_is_reported_not_swallowed(self):
        terminal = self.healthy()
        terminal.fail_on("set number of columns", "osascript failed (1): bad font")
        result = self.run_smoke(terminal)
        self.assertFalse(result.passed)
        self.assertTrue(
            [c for c in result.checks if not c.ok and "bad font" in c.detail],
            [str(c) for c in result.checks],
        )

    def test_it_reaps_the_window_when_a_check_fails_partway(self):
        # The supervisor blew up before its own close could run, and the tab
        # has ended, so the smoke's own clean-up must close the window.
        terminal = RecordingTerminal(states=[ENDED])
        terminal.raise_on("set position of", RuntimeError("the sky fell"))
        result = self.run_smoke(terminal)
        self.assertFalse(result.passed)
        self.assertEqual(
            1, len(terminal.closed), "the smoke left a window on the screen"
        )

    def test_it_never_forces_a_busy_tab_and_says_which_window_it_left(self):
        # §2.6 rule 3 and the hang path: report the id, leave the window open.
        terminal = RecordingTerminal(states=[PLAYING])
        terminal.raise_on("set position of", RuntimeError("the sky fell"))
        result = self.run_smoke(terminal)
        self.assertFalse(result.passed)
        self.assertEqual([], terminal.closed)
        self.assertIn("LEFT OPEN", self.out.getvalue())
        self.assertIn(str(NEW_WINDOW_ID), self.out.getvalue())
        # It waited the full grace before giving up, and it never forced it.
        self.assertGreaterEqual(self.clock.elapsed, smoke.CLEANUP_SECONDS)

    def test_the_clean_up_waits_no_longer_than_play_itself_would(self):
        # The smoke should be neither more patient nor more forceful than the
        # launcher it is smoking.
        self.assertEqual(window.CLOSE_GRACE_SECONDS, smoke.CLEANUP_SECONDS)


class TheTitleHasToSettle(unittest.TestCase):
    """Measured on the real machine, and it cost this item a red run.

    ``do script`` opens a window running the user's *login shell*, which
    sources their startup files before our ``exec`` line runs, and Terminal's
    title follows whatever that shell is doing meanwhile. The first read --
    about half a second after the window appeared -- returned

        'rodneybailey — ssh-add --apple-use-keychain ~/.ssh/id_ed25519'

    which is the user's own profile, not a WIN-3 failure. WI-2 never saw it
    because it read the title a full second after creating the window. So the
    title is polled, not sampled once.
    """

    SHELL_TITLE = "rodneybailey — ssh-add --apple-use-keychain ~/.ssh/id_ed25519"

    def setUp(self):
        self.real_run = window.run_osascript
        self.reads = []

    def tearDown(self):
        window.run_osascript = self.real_run

    def answer(self, titles):
        remaining = list(titles)

        def fake(script, timeout=20.0):
            self.reads.append(script)
            return remaining.pop(0) if len(remaining) > 1 else remaining[0]

        window.run_osascript = fake

    def test_a_shell_still_starting_up_is_waited_out_not_failed(self):
        self.answer([self.SHELL_TITLE, self.SHELL_TITLE, "Terminal Game"])
        title, took = smoke.settled_title(NEW_WINDOW_ID, deadline=5.0, poll=0.0)
        self.assertEqual("Terminal Game", title)
        self.assertEqual(3, len(self.reads))
        self.assertLess(took, 5.0)

    def test_a_title_that_never_settles_is_reported_with_what_it_read(self):
        self.answer(["rodneybailey — bash"])
        title, took = smoke.settled_title(NEW_WINDOW_ID, deadline=0.0, poll=0.0)
        self.assertEqual("rodneybailey — bash", title)

    def test_every_read_addresses_the_window_we_opened(self):
        self.answer(["Terminal Game"])
        smoke.settled_title(NEW_WINDOW_ID, deadline=0.0, poll=0.0)
        assert_addresses_only_our_window(self, self.reads, NEW_WINDOW_ID)

    def test_the_child_outlives_the_time_the_title_is_given_to_settle(self):
        # Otherwise the child exits mid-poll and the title reverts to the
        # shell's, and the smoke fails for a reason that is not WIN-3.
        self.assertGreater(smoke.CHILD_SECONDS, smoke.TITLE_SECONDS)


class TheSmokeReport(unittest.TestCase):
    def test_a_failed_check_prints_FAIL_and_a_passed_one_does_not(self):
        self.assertTrue(str(smoke.Check("x", False, "why")).startswith("FAIL"))
        self.assertIn("why", str(smoke.Check("x", False, "why")))
        self.assertTrue(str(smoke.Check("x", True)).startswith("ok"))

    def test_the_detail_is_printed_only_when_the_check_failed(self):
        # A detail beside "ok" reads as a contradiction: the real run printed
        # "ok  the window is no longer visible -- it is still on the screen".
        passed = smoke.Check("the window is no longer visible", True, "still there")
        self.assertNotIn("still there", str(passed))
        self.assertIn(
            "still there",
            str(smoke.Check("the window is no longer visible", False, "still there")),
        )

    def test_a_result_with_no_checks_at_all_is_not_a_pass(self):
        # Otherwise a smoke that died before checking anything reports PASS.
        self.assertFalse(smoke.SmokeResult().passed)

    def test_one_failed_check_fails_the_whole_run(self):
        result = smoke.SmokeResult()
        result.check("a", True)
        result.check("b", False)
        self.assertFalse(result.passed)


if __name__ == "__main__":
    unittest.main()
