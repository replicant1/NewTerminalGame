"""WI-8 — every way the launcher can fail, and the rule that matters most.

WI-2 proved the happy path. The happy path is not what loses somebody's work,
so this module walks the supervisor down **every** other path with Terminal
replaced by a fake, and asserts two things of each:

1. the path ends with the game window closed by the id that was captured when
   it was created -- or, when the tab is still busy, deliberately **not**
   closed, with the id reported so a person can deal with it;
2. **no command issued on any path names Terminal's front window, addresses a
   window by title, or addresses a window by index.**

The second is the regression test for the rule of implementation plan §2.6
that matters most, and it is enforced here as an *allowlist* rather than a
list of banned words: every occurrence of the word ``window`` in every script
the supervisor issued, on every path, must be part of one of exactly three
phrases (see ``ADDRESSING_ALLOWLIST``). A denylist would let the next new
phrasing through; this will not.

It matters because it has already gone wrong. In an earlier run an agent's
hide-then-reveal resolved to the *user's own* window and hid it: their shell
vanished, with nothing to click, no dialog and no warning.

Nothing here opens a window. ``tests/test_launch_smoke.py`` does that, against
the real Terminal, and only when a person is sitting in front of it.
"""

import os
import re
import signal
import unittest

from termgame import window

#: The id the fake Terminal hands back for the window the supervisor creates.
NEW_WINDOW_ID = 4242

#: Ids of windows that are emphatically **not** ours: the user's shell, their
#: editor, the agent session. If any of these ever appears in a command, the
#: supervisor has started addressing windows it did not open.
SOMEBODY_ELSES_WINDOW_IDS = (367, 2420, 2440, 2486)

#: A tab running the game, as measured: not busy, two processes (``login`` and
#: ``Python``). See ``window.script_tab_state``.
PLAYING = "false 2"
#: The same tab once the child has exited.
ENDED = "false 0"
#: The tab of a window that no longer exists, because the player closed it.
GONE = "gone"

#: The verbatim text ``osascript`` produced for a window id that is not there.
#: Recorded in docs/findings/WI-2-terminal-window-id.md §7.
INVALID_INDEX_ERROR = (
    "osascript failed (1): 36:40: execution error: Terminal got an error: "
    "Can’t get window 1 whose id = 999999. Invalid index. (-1719)"
)


# --------------------------------------------------------------------------
# The rule that matters most, as an allowlist.
# --------------------------------------------------------------------------

#: The only three ways this project is allowed to mention a window.
#:
#: * ``first window whose id is N`` -- the addressing idiom. The window was
#:   watched into existence and this is its id.
#: * ``first window whose tabs contains newTab`` -- the *creation* idiom, and
#:   the only one that does not use an id, because at that instant the window
#:   has not been resolved to an id yet. It is resolved from the tab
#:   ``do script`` just returned, not from anything on the screen.
#: * ``repeat with w in windows`` -- enumerating, in a read, in order to
#:   *count* or to find a reference position. Nothing is ever acted on as a
#:   result.
#: The fourth entry is not a window reference at all: ``title displays window
#: size`` is the name of one of the tab's title components, and turning it off
#: is part of the WIN-3 recipe. It is listed here so that the check below can
#: stay a strict allowlist over the word ``window`` rather than being weakened
#: into a denylist.
ADDRESSING_ALLOWLIST = (
    re.compile(r"first window whose id is \d+"),
    re.compile(r"first window whose tabs contains newTab"),
    re.compile(r"repeat with w in windows"),
    re.compile(r"title displays window size"),
)

#: Denylist too, stated in the words the plan uses, so a failure names the
#: rule that was broken rather than leaving the reader to work it out.
FORBIDDEN = (
    ("Terminal's front window", re.compile(r"front\s+window", re.I)),
    ("a window by index", re.compile(r"\bwindows?\s+-?\d", re.I)),
    ("a window by title", re.compile(r"\bwindow\s+(?:named\s+)?[\"']", re.I)),
    ("a window by name", re.compile(r"\bwindow\s+whose\s+name", re.I)),
    ("a window by list position", re.compile(r"item\s+-?\d+\s+of\s+windows", re.I)),
)

WORD_WINDOW = re.compile(r"\bwindows?\b", re.I)


def addressing_faults(script, window_id):
    """Every way *script* breaks §2.6 rule 1. Empty means it is clean."""
    faults = []
    for description, pattern in FORBIDDEN:
        if pattern.search(script):
            faults.append("names %s" % description)

    residue = script
    for allowed in ADDRESSING_ALLOWLIST:
        residue = allowed.sub(" ", residue)
    for stray in WORD_WINDOW.findall(residue):
        faults.append("mentions %r outside the three allowed phrases" % stray)

    for found in re.findall(r"first window whose id is (\d+)", script):
        if int(found) != window_id:
            faults.append(
                "addresses window id %s, which is not the one we created (%d)"
                % (found, window_id)
            )
    return faults


def assert_addresses_only_our_window(test, scripts, window_id):
    """The whole of §2.6 rule 1, over a recorded run."""
    test.assertTrue(scripts, "no commands were recorded, so nothing was checked")
    for script in scripts:
        faults = addressing_faults(script, window_id)
        test.assertEqual(
            [],
            faults,
            "a command breaks the never-touch-a-window-you-did-not-open rule "
            "(%s):\n%s" % ("; ".join(faults), script),
        )


class FakeClock(object):
    """A clock that only moves when something sleeps.

    Ten seconds of the failure-path grace must be *observed*, not asserted
    about a constant, and observing it must not cost the suite ten seconds.
    """

    def __init__(self, start=1000.0):
        self.now = float(start)
        self.start = float(start)
        self.slept = []

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds

    def monotonic(self):
        return self.now

    @property
    def elapsed(self):
        return self.now - self.start


# --------------------------------------------------------------------------
# The fake Terminal.
# --------------------------------------------------------------------------


class RecordingTerminal(object):
    """Stands in for ``window.run_osascript``, and remembers everything.

    It answers the scripts the supervisor actually sends, so the tests below
    assert consequences -- which window was closed, when, what the player was
    told -- rather than that some function was called.
    """

    def __init__(
        self,
        tty_position="none",
        front_position="10 20",
        states=None,
        visible_after_close=None,
        window_name="Terminal Game",
        geometry="40 30 Menlo-Regular 18",
        new_window_id=NEW_WINDOW_ID,
        census=None,
    ):
        self.scripts = []
        self.tty_position = tty_position
        self.front_position = front_position
        self.states = list(states or [PLAYING, ENDED])
        self.current = self.states[0]
        self.visible_after_close = visible_after_close
        self.window_name = window_name
        self.geometry = geometry
        self.new_window_id = new_window_id
        self.census = list(census if census is not None else SOMEBODY_ELSES_WINDOW_IDS)
        self.closed = []
        #: substring -> WindowError text, for "osascript failed here".
        self.failures = {}
        #: substring -> [remaining firings, exception], for anything else.
        self.raises = {}

    # -- injection ---------------------------------------------------------

    def fail_on(self, marker, message="deliberate osascript failure"):
        self.failures[marker] = message
        return self

    def raise_on(self, marker, error, times=1):
        """Raise *error* the next *times* a script mentioning *marker* is run.

        Once by default, because that is what an interrupt is: a signal
        arrives once. A fake that raised for ever would be modelling a person
        holding ^C down, and would hide whether the clean-up runs.
        """
        self.raises[marker] = [times, error]
        return self

    # -- answering ---------------------------------------------------------

    def __call__(self, script, timeout=20.0):
        self.scripts.append(script)
        for marker, remaining in self.raises.items():
            if marker in script and remaining[0] > 0:
                remaining[0] -= 1
                raise remaining[1]
        for marker, message in self.failures.items():
            if marker in script:
                raise window.WindowError(message)
        return self._answer(script)

    def _answer(self, script):
        kind = classify(script)
        if kind == "reference-tty":
            return self.tty_position
        if kind == "reference-front":
            return self.front_position
        if kind == "open":
            # The new window joins the user's, exactly as it does on a real
            # screen: the census below is then a real before/after check.
            if self.new_window_id not in self.census:
                self.census.append(self.new_window_id)
            return str(self.new_window_id)
        if kind == "poll":
            return self._next_state()
        if kind == "close":
            return self._close()
        if kind == "visible":
            # Derived from the census unless a test pins it, so that "is the
            # window still there?" and "what does the screen hold?" cannot
            # disagree inside the fake. A fake that let them disagree hid a
            # real defect once already: the smoke's clean-up believed the
            # window had gone while the census still listed it.
            if self.visible_after_close is not None:
                return self.visible_after_close
            return "true" if self.new_window_id in self.census else "false"
        if kind == "name":
            return self.window_name
        if kind == "geometry":
            return self.geometry
        if kind == "census":
            return "\n".join(str(each) for each in self.census)
        return ""

    def _next_state(self):
        if len(self.states) > 1:
            self.current = self.states.pop(0)
        else:
            self.current = self.states[0]
        return self.current

    def _close(self):
        # Terminal's own behaviour, as measured: a window that is gone answers
        # gone, a busy tab is refused, anything else closes.
        if self.current == GONE:
            return "gone"
        busy, processes = window.parse_tab_state(self.current)
        if busy or processes > 0:
            return "busy"
        self.closed.append(self.scripts[-1])
        self.census = [
            each for each in self.census if each != self.new_window_id
        ]
        return "closed"

    # -- reading back ------------------------------------------------------

    def kinds(self):
        return [classify(script) for script in self.scripts]


def classify(script):
    """A short label for one of the scripts ``window.py`` composes."""
    if "tty of tab 1" in script:
        return "reference-tty"
    if "if visible of w then" in script and "set out to" in script:
        return "census"
    if "set p to position of w" in script:
        return "reference-front"
    if "do script" in script:
        return "open"
    if "set number of columns" in script:
        return "configure"
    if "set position of" in script:
        return "move"
    if "close gameWindow" in script:
        return "close"
    if "count of processes" in script:
        return "poll"
    if "font name of gameTab" in script:
        return "geometry"
    if "return name of" in script:
        return "name"
    if "visible of (first window" in script:
        return "visible"
    return "other"


# --------------------------------------------------------------------------
# The scenarios. Every one of them is walked by the regression test at the
# bottom of this file as well as by its own test.
# --------------------------------------------------------------------------


class SupervisorPathTestCase(unittest.TestCase):
    """Machinery shared by every failure-path test. Opens no window."""

    def setUp(self):
        self.real_run = window.run_osascript
        self.real_displays = window.displays
        self.real_tty = window.controlling_tty
        self.real_sleep = window._sleep
        self.real_now = window._now
        self.real_startup = window.STARTUP_GRACE_SECONDS
        self.real_grace = window.CLOSE_GRACE_SECONDS
        window._sleep = lambda seconds: None
        # The grace is a wall-clock wait and its value is pinned by its own
        # test; shortening it here keeps the suite quick without changing what
        # ./play does.
        window.STARTUP_GRACE_SECONDS = 0.0
        window.displays = lambda report=None: [(0, 0, 1512, 982)]
        window.controlling_tty = lambda: "/dev/ttys009"
        self.reports = []

    def tearDown(self):
        window.run_osascript = self.real_run
        window.displays = self.real_displays
        window.controlling_tty = self.real_tty
        window._sleep = self.real_sleep
        window._now = self.real_now
        window.STARTUP_GRACE_SECONDS = self.real_startup
        window.CLOSE_GRACE_SECONDS = self.real_grace

    def supervise(self, terminal, root="/tmp/repo", close_grace=0.0, **kwargs):
        window.run_osascript = terminal
        return window.supervise(
            root, report=self.reports.append, close_grace=close_grace, **kwargs
        )

    def said(self, needle):
        return [message for message in self.reports if needle in str(message)]

    def assert_closed_our_window(self, terminal):
        self.assertEqual(
            1,
            len(terminal.closed),
            "the window was not closed exactly once: %r" % (terminal.kinds(),),
        )
        self.assertIn(
            "first window whose id is %d" % NEW_WINDOW_ID, terminal.closed[0]
        )

    def assert_reported_the_id(self, window_id=NEW_WINDOW_ID):
        self.assertTrue(
            self.said(str(window_id)),
            "the window id was never reported, so nobody knows which window "
            "to deal with: %r" % self.reports,
        )


class TheChildCrashesOnStartup(SupervisorPathTestCase):
    """The tab is process-free from the very first poll."""

    def test_the_window_is_still_closed_by_id(self):
        terminal = RecordingTerminal(states=[ENDED])
        self.assertEqual(0, self.supervise(terminal))
        self.assert_closed_our_window(terminal)

    def test_the_close_is_confirmed_with_visible_and_never_with_exists(self):
        terminal = RecordingTerminal(states=[ENDED])
        self.supervise(terminal)
        self.assertIn("visible", terminal.kinds())
        for script in terminal.scripts:
            self.assertNotIn("exists", script)

    def test_a_window_that_lingers_after_the_close_is_reported(self):
        terminal = RecordingTerminal(states=[ENDED], visible_after_close="true")
        self.supervise(terminal)
        self.assertTrue(self.said("still reports itself visible"))
        self.assert_reported_the_id()


class TheChildHangs(SupervisorPathTestCase):
    """Something went wrong *and* the game is still running in the window."""

    def failing_run(self):
        terminal = RecordingTerminal(states=[PLAYING])
        terminal.fail_on("set number of columns", "osascript failed (1): nope")
        with self.assertRaises(window.WindowError):
            self.supervise(terminal, close_grace=0.0)
        return terminal

    def test_the_close_is_not_even_attempted_on_a_busy_tab(self):
        # §2.6 rule 3. Forcing it raises a modal sheet that only a human can
        # dismiss, and that sheet blocks every later AppleScript call.
        terminal = self.failing_run()
        self.assertEqual([], terminal.closed)

    def test_the_window_id_is_reported_and_the_window_left_open(self):
        self.failing_run()
        self.assertTrue(self.said("still running"))
        self.assertTrue(self.said("left open"))
        self.assert_reported_the_id()

    def test_the_grace_is_ten_seconds_of_real_waiting(self):
        # Not a number in a comment: the failure path really does poll for
        # ten seconds before it gives up and leaves the window alone.
        self.assertEqual(10.0, window.CLOSE_GRACE_SECONDS)
        clock = FakeClock()
        terminal = RecordingTerminal(states=[PLAYING])
        window.run_osascript = terminal
        self.assertFalse(
            window.close_when_idle(
                NEW_WINDOW_ID, sleep=clock.sleep, clock=clock.monotonic
            )
        )
        self.assertAlmostEqual(
            window.CLOSE_GRACE_SECONDS, clock.elapsed, delta=window.POLL_SECONDS
        )
        self.assertEqual([], terminal.closed)

    def test_play_waits_the_grace_and_no_longer_before_giving_up(self):
        # ./play's own call: close_grace is not passed at all.
        window.CLOSE_GRACE_SECONDS = 0.8
        clock = FakeClock()
        window._sleep = clock.sleep
        window._now = clock.monotonic
        terminal = RecordingTerminal(states=[PLAYING])
        terminal.fail_on("set number of columns", "osascript failed (1): x")
        window.run_osascript = terminal
        with self.assertRaises(window.WindowError):
            window.supervise("/tmp/repo", report=self.reports.append)
        self.assertAlmostEqual(0.8, clock.elapsed, delta=window.POLL_SECONDS)
        self.assertEqual([], terminal.closed)
        self.assert_reported_the_id()


class TheSupervisorIsInterrupted(SupervisorPathTestCase):
    """^C, a kill, or the launching terminal closing under us."""

    def test_a_signal_during_the_game_still_closes_the_window(self):
        terminal = RecordingTerminal(states=[ENDED])
        terminal.raise_on(
            "count of processes", window.SupervisorInterrupted("signal 15")
        )
        status = self.supervise(terminal)
        self.assertEqual(window.INTERRUPTED_EXIT_STATUS, status)
        self.assert_closed_our_window(terminal)
        self.assertTrue(self.said("interrupted"))

    def test_a_child_that_exits_during_the_grace_is_still_reaped(self):
        terminal = RecordingTerminal(states=[PLAYING, PLAYING, ENDED])
        terminal.raise_on(
            "count of processes", window.SupervisorInterrupted("signal 1")
        )
        self.assertEqual(
            window.INTERRUPTED_EXIT_STATUS,
            self.supervise(terminal, close_grace=5.0),
        )
        self.assert_closed_our_window(terminal)

    def test_an_interrupt_while_the_game_is_still_running_leaves_it_open(self):
        terminal = RecordingTerminal(states=[PLAYING])
        terminal.raise_on(
            "count of processes", window.SupervisorInterrupted("signal 2")
        )
        self.assertEqual(
            window.INTERRUPTED_EXIT_STATUS, self.supervise(terminal)
        )
        self.assertEqual([], terminal.closed)
        self.assert_reported_the_id()

    def test_a_keyboard_interrupt_closes_the_window_and_is_not_swallowed(self):
        terminal = RecordingTerminal(states=[ENDED])
        terminal.raise_on("count of processes", KeyboardInterrupt())
        with self.assertRaises(KeyboardInterrupt):
            self.supervise(terminal)
        self.assert_closed_our_window(terminal)


class TheSignalHandlerItself(unittest.TestCase):
    """``_InterruptsRaise`` against a real signal, in the real process.

    Safe by construction: the kill only happens once the handler has been
    observed to be installed, so a failure to install fails the assertion
    rather than killing the test run.
    """

    def test_a_real_sigterm_becomes_an_exception_and_the_handler_is_restored(self):
        before = signal.getsignal(signal.SIGTERM)
        guard = window._InterruptsRaise()
        with self.assertRaises(window.SupervisorInterrupted):
            with guard:
                self.assertIsNot(
                    signal.getsignal(signal.SIGTERM),
                    before,
                    "the handler was not installed; not sending a signal",
                )
                os.kill(os.getpid(), signal.SIGTERM)
        self.assertIs(before, signal.getsignal(signal.SIGTERM))

    def test_it_covers_the_three_signals_that_can_reach_the_supervisor(self):
        self.assertEqual(("SIGINT", "SIGTERM", "SIGHUP"), window.INTERRUPT_SIGNALS)

    def test_off_the_main_thread_it_does_nothing_rather_than_failing(self):
        # The launch smoke runs the supervisor on a worker thread. A worker
        # has no business rewiring the process's signal handling, and its
        # window is closed by the same finally regardless.
        import threading

        outcome = []

        def body():
            try:
                with window._InterruptsRaise():
                    outcome.append("entered")
            except Exception as error:  # pragma: no cover - the bug we forbid
                outcome.append(error)

        thread = threading.Thread(target=body)
        thread.start()
        thread.join(5)
        self.assertEqual(["entered"], outcome)


class TheReferenceQueryFails(SupervisorPathTestCase):
    """Terminal is not running, or the game was launched from something else."""

    def test_the_front_window_is_used_when_the_tty_query_fails(self):
        terminal = RecordingTerminal(front_position="400 200", states=[ENDED])
        terminal.fail_on("tty of tab 1", "osascript failed (1): no Terminal")
        self.supervise(terminal)
        move = [s for s in terminal.scripts if classify(s) == "move"][0]
        self.assertIn("to {430, 230}", move)

    def test_the_fixed_fallback_is_used_when_both_queries_fail(self):
        terminal = RecordingTerminal(states=[ENDED])
        terminal.fail_on("tty of tab 1", "osascript failed (1): no Terminal")
        terminal.fail_on("set p to position of w", "osascript failed (1): none")
        self.supervise(terminal)
        move = [s for s in terminal.scripts if classify(s) == "move"][0]
        expected = window.offset_position(
            window.FALLBACK_POSITION, (0, 0, 1512, 982)
        )
        self.assertIn("to {%d, %d}" % expected, move)

    def test_the_game_still_runs_and_the_window_is_still_closed(self):
        terminal = RecordingTerminal(states=[ENDED])
        terminal.fail_on("tty of tab 1", "osascript failed (1): no Terminal")
        terminal.fail_on("set p to position of w", "osascript failed (1): none")
        self.assertEqual(0, self.supervise(terminal))
        self.assertIn("open", terminal.kinds())
        self.assert_closed_our_window(terminal)

    def test_the_osascript_text_is_surfaced_not_swallowed(self):
        terminal = RecordingTerminal(states=[ENDED])
        terminal.fail_on("tty of tab 1", "osascript failed (1): -1743 not allowed")
        self.supervise(terminal)
        self.assertTrue(
            self.said("-1743 not allowed"),
            "the osascript error text was swallowed: %r" % self.reports,
        )


class AnOsascriptErrorAtEveryStep(SupervisorPathTestCase):
    """WI-8: an error at any step is surfaced with its text."""

    def test_a_failure_to_open_carries_its_text_and_closes_nothing(self):
        terminal = RecordingTerminal(states=[ENDED])
        terminal.fail_on("do script", INVALID_INDEX_ERROR)
        with self.assertRaises(window.WindowError) as caught:
            self.supervise(terminal)
        self.assertIn("Invalid index. (-1719)", str(caught.exception))
        self.assertEqual([], terminal.closed)
        self.assertNotIn("close", terminal.kinds())

    def test_a_failure_to_configure_carries_its_text_and_still_closes(self):
        terminal = RecordingTerminal(states=[ENDED])
        terminal.fail_on("set number of columns", "osascript failed (1): bad font")
        with self.assertRaises(window.WindowError) as caught:
            self.supervise(terminal)
        self.assertIn("bad font", str(caught.exception))
        self.assert_closed_our_window(terminal)

    def test_a_failure_to_move_carries_its_text_and_still_closes(self):
        terminal = RecordingTerminal(states=[ENDED])
        terminal.fail_on("set position of", "osascript failed (1): off screen")
        with self.assertRaises(window.WindowError) as caught:
            self.supervise(terminal)
        self.assertIn("off screen", str(caught.exception))
        self.assert_closed_our_window(terminal)

    def test_a_failure_to_close_does_not_mask_what_actually_went_wrong(self):
        # The clean-up runs in a finally. An exception escaping it would
        # replace the real error and the player would never learn the cause.
        terminal = RecordingTerminal(states=[ENDED])
        terminal.fail_on("set number of columns", "osascript failed (1): bad font")
        terminal.fail_on("close gameWindow", "osascript failed (1): no such window")
        with self.assertRaises(window.WindowError) as caught:
            self.supervise(terminal)
        self.assertIn("bad font", str(caught.exception))
        self.assertNotIn("no such window", str(caught.exception))
        self.assertTrue(self.said("could not close"))
        self.assertTrue(self.said("no such window"))
        self.assert_reported_the_id()


class ThePlayerClosedTheWindowThemselves(SupervisorPathTestCase):
    """A window id that no longer resolves is not a crash."""

    def test_a_gone_window_ends_the_wait_rather_than_raising(self):
        terminal = RecordingTerminal(states=[PLAYING, GONE])
        self.assertEqual(0, self.supervise(terminal))
        self.assertTrue(self.said("game window"))

    def test_a_gone_window_is_not_reported_as_left_open(self):
        terminal = RecordingTerminal(states=[GONE], visible_after_close="gone")
        self.supervise(terminal)
        self.assertEqual([], self.said("left open"))

    def test_the_scripts_that_can_meet_a_gone_window_all_tolerate_it(self):
        for script in (
            window.script_tab_state(NEW_WINDOW_ID),
            window.script_close_window(NEW_WINDOW_ID),
            window.script_window_visible(NEW_WINDOW_ID),
        ):
            self.assertIn("on error", script)
            self.assertIn('return "gone"', script)

    def test_gone_reads_as_a_tab_that_is_not_running(self):
        self.assertEqual((False, 0), window.parse_tab_state("gone"))
        self.assertFalse(window.parse_tab_state("gone")[0])


class TheScreenLayoutCannotBeRead(SupervisorPathTestCase):
    """``displays()`` falls back -- but it may not do so in silence.

    Measured during WI-8: on one call out of several, on this machine,
    ``displays()`` returned the 1440 x 900 fallback while
    ``CGGetActiveDisplayList`` reported all three real displays correctly a
    few seconds later. The consequence is not cosmetic. The reference window
    sat at (-898, 76); against the fallback rectangle that point is on no
    display at all, so the clamp moved the game window to the main screen and
    it landed at (0, 106) instead of (-868, 106) -- WIN-4 quietly not holding,
    with nothing said.
    """

    def test_a_reference_on_no_display_is_clamped_onto_the_first_one(self):
        # This is the consequence the silent fallback produced.
        fallback = [window.FALLBACK_SCREEN_BOUNDS]
        self.assertEqual(
            window.FALLBACK_SCREEN_BOUNDS,
            window.choose_display((-898, 76), fallback),
        )
        self.assertEqual(
            (0, 106),
            window.offset_position((-898, 76), window.FALLBACK_SCREEN_BOUNDS),
        )

    def test_the_real_layout_puts_the_window_next_to_the_reference(self):
        # The same reference, against what the machine actually has.
        real = window.applescript_display_bounds(
            [(0, 0, 1512, 982), (-3509, -1440, 2560, 1440), (-949, -1440, 2560, 1440)]
        )
        self.assertEqual(
            (-868, 106),
            window.offset_position((-898, 76), window.choose_display((-898, 76), real)),
        )

    def test_an_unreadable_layout_is_reported_with_the_reason(self):
        said = []
        real_ctypes = window.ctypes.cdll.LoadLibrary

        def explode(path):
            raise OSError("image not found")

        window.ctypes.cdll.LoadLibrary = explode
        try:
            # self.real_displays, not window.displays: setUp has stubbed the
            # latter, and it is the real one that has to report.
            self.assertEqual(
                [window.FALLBACK_SCREEN_BOUNDS],
                self.real_displays(report=said.append),
            )
        finally:
            window.ctypes.cdll.LoadLibrary = real_ctypes
        self.assertTrue(said, "the fallback happened in silence")
        self.assertIn("image not found", said[0])
        self.assertIn("wrong screen", said[0])

    def test_the_supervisor_passes_its_own_report_to_the_layout_query(self):
        terminal = RecordingTerminal(states=[ENDED])
        window.displays = lambda report=None: (
            report("could not read the screen layout (test)") or
            [window.FALLBACK_SCREEN_BOUNDS]
        )
        self.supervise(terminal)
        self.assertTrue(
            self.said("could not read the screen layout"),
            "the layout fallback never reached the player: %r" % self.reports,
        )

    def test_the_game_still_starts_when_the_layout_cannot_be_read(self):
        # Reporting it must not become a reason not to play.
        terminal = RecordingTerminal(states=[ENDED])
        window.displays = lambda report=None: [window.FALLBACK_SCREEN_BOUNDS]
        self.assertEqual(0, self.supervise(terminal))
        self.assert_closed_our_window(terminal)


class TheCapturedIdReachesTheCaller(SupervisorPathTestCase):
    """``on_window_opened`` — how the smoke learns the id without guessing."""

    def test_the_hook_is_handed_the_id_the_supervisor_captured(self):
        terminal = RecordingTerminal(states=[ENDED])
        seen = []
        self.supervise(terminal, on_window_opened=seen.append)
        self.assertEqual([NEW_WINDOW_ID], seen)

    def test_the_hook_runs_before_anything_is_done_to_the_window(self):
        terminal = RecordingTerminal(states=[ENDED])
        at_call = []
        self.supervise(
            terminal,
            on_window_opened=lambda each: at_call.append(list(terminal.kinds())),
        )
        self.assertEqual(["reference-tty", "reference-front", "open"], at_call[0])

    def test_a_hook_that_fails_does_not_leave_the_window_behind(self):
        terminal = RecordingTerminal(states=[ENDED])

        def explode(window_id):
            raise ValueError("the caller's own bug")

        with self.assertRaises(ValueError):
            self.supervise(terminal, on_window_opened=explode)
        self.assert_closed_our_window(terminal)


# --------------------------------------------------------------------------
# The regression test for the rule that matters most.
# --------------------------------------------------------------------------


def every_path():
    """One callable per path the supervisor can take, for the sweep below.

    Adding a path here is how a later work item gets it covered by the
    never-touch-a-window-you-did-not-open assertion for free.
    """

    def plain(terminal):
        return terminal

    def crash_on_startup(terminal):
        terminal.states = [ENDED]
        return terminal

    def configure_fails_tab_ended(terminal):
        terminal.states = [ENDED]
        return terminal.fail_on("set number of columns", "osascript failed (1): x")

    def configure_fails_tab_busy(terminal):
        terminal.states = [PLAYING]
        return terminal.fail_on("set number of columns", "osascript failed (1): x")

    def move_fails(terminal):
        terminal.states = [ENDED]
        return terminal.fail_on("set position of", "osascript failed (1): x")

    def open_fails(terminal):
        return terminal.fail_on("do script", INVALID_INDEX_ERROR)

    def tty_query_fails(terminal):
        terminal.states = [ENDED]
        return terminal.fail_on("tty of tab 1", "osascript failed (1): x")

    def both_queries_fail(terminal):
        terminal.states = [ENDED]
        terminal.fail_on("tty of tab 1", "osascript failed (1): x")
        return terminal.fail_on("set p to position of w", "osascript failed (1): x")

    def close_fails(terminal):
        terminal.states = [ENDED]
        terminal.fail_on("set number of columns", "osascript failed (1): x")
        return terminal.fail_on("close gameWindow", INVALID_INDEX_ERROR)

    def interrupted(terminal):
        terminal.states = [PLAYING, ENDED]
        return terminal.raise_on(
            "count of processes", window.SupervisorInterrupted("signal 15")
        )

    def keyboard_interrupt(terminal):
        terminal.states = [ENDED]
        return terminal.raise_on("count of processes", KeyboardInterrupt())

    def window_gone(terminal):
        terminal.states = [PLAYING, GONE]
        terminal.visible_after_close = "gone"
        return terminal

    def lingers_after_close(terminal):
        terminal.states = [ENDED]
        terminal.visible_after_close = "true"
        return terminal

    def played_for_a_while(terminal):
        terminal.states = [PLAYING, PLAYING, PLAYING, ENDED]
        return terminal

    return [
        ("the game is played and ends", plain),
        ("the child crashes on startup", crash_on_startup),
        ("configuring fails, the tab has ended", configure_fails_tab_ended),
        ("configuring fails, the tab is still busy", configure_fails_tab_busy),
        ("positioning fails", move_fails),
        ("the window cannot be opened at all", open_fails),
        ("the tty reference query fails", tty_query_fails),
        ("both reference queries fail", both_queries_fail),
        ("the close itself fails", close_fails),
        ("a signal interrupts the supervisor", interrupted),
        ("the supervisor is ^C'd", keyboard_interrupt),
        ("the player closed the window themselves", window_gone),
        ("the window lingers after the close", lingers_after_close),
        ("the game is played for a while", played_for_a_while),
    ]


class NoPathEverTouchesAWindowWeDidNotOpen(SupervisorPathTestCase):
    """THE regression test. Read the module docstring before changing it."""

    def walk(self, arrange):
        terminal = arrange(RecordingTerminal())
        window.run_osascript = terminal
        try:
            window.supervise(
                "/tmp/repo", report=self.reports.append, close_grace=0.0
            )
        except (window.WindowError, KeyboardInterrupt, ValueError):
            pass
        return terminal

    def test_no_command_on_any_path_names_a_front_window_title_or_index(self):
        checked = 0
        for description, arrange in every_path():
            terminal = self.walk(arrange)
            self.assertTrue(
                terminal.scripts, "%s issued no commands at all" % description
            )
            for script in terminal.scripts:
                faults = addressing_faults(script, NEW_WINDOW_ID)
                self.assertEqual(
                    [],
                    faults,
                    "on the path where %s, a command breaks §2.6 rule 1 "
                    "(%s):\n%s" % (description, "; ".join(faults), script),
                )
                checked += 1
        self.assertGreater(checked, 40, "far too few commands were inspected")

    def test_no_command_on_any_path_mentions_another_window_s_id(self):
        for description, arrange in every_path():
            terminal = self.walk(arrange)
            for script in terminal.scripts:
                for other in SOMEBODY_ELSES_WINDOW_IDS:
                    self.assertNotIn(
                        "id is %d" % other,
                        script,
                        "on the path where %s, a command addressed window %d, "
                        "which belongs to the user:\n%s"
                        % (description, other, script),
                    )

    def test_every_write_after_the_open_addresses_the_captured_id(self):
        writes = ("configure", "move", "close")
        for description, arrange in every_path():
            terminal = self.walk(arrange)
            for script in terminal.scripts:
                if classify(script) in writes:
                    self.assertIn(
                        "first window whose id is %d" % NEW_WINDOW_ID,
                        script,
                        "on the path where %s, a write did not address the "
                        "captured id:\n%s" % (description, script),
                    )

    def test_the_users_other_windows_are_all_still_there_afterwards(self):
        # The fake's census starts as the user's shell, editor and agent
        # session -- WI-2 measured exactly these four -- and gains the game
        # window when it is created. Nothing may ever remove one of the first
        # four, on any path.
        for description, arrange in every_path():
            terminal = self.walk(arrange)
            missing = set(SOMEBODY_ELSES_WINDOW_IDS) - set(terminal.census)
            self.assertEqual(
                set(),
                missing,
                "on the path where %s, the user's window(s) %s went away"
                % (description, sorted(missing)),
            )

    def test_the_game_window_itself_is_gone_once_the_game_has_ended(self):
        # The other half of the census: it is not enough to leave the user's
        # windows alone, ours has to actually go.
        terminal = self.walk(lambda each: each)
        self.assertNotIn(
            NEW_WINDOW_ID,
            terminal.census,
            "the game window is still on the screen after a normal game",
        )

    def test_the_checker_itself_can_fail(self):
        # A regression test that cannot fail is worse than no test, and this
        # one is the most valuable in the item. These are the four phrasings
        # that have actually destroyed somebody's work or would have.
        for bad in (
            'tell application "Terminal" to close front window',
            'tell application "Terminal" to close window 1',
            'tell application "Terminal" to close window "Terminal Game"',
            "tell application \"Terminal\" to close (first window whose name "
            'is "Terminal Game")',
        ):
            self.assertNotEqual(
                [],
                addressing_faults(bad, NEW_WINDOW_ID),
                "the checker passed a command that must never be issued: %s" % bad,
            )

    def test_the_checker_passes_the_three_phrasings_that_are_allowed(self):
        for good in (
            window.script_close_window(NEW_WINDOW_ID),
            window.script_open_window("exec '/tmp/repo/Terminal Game'"),
            window.script_visible_window_ids(),
            window.script_front_position(),
        ):
            self.assertEqual([], addressing_faults(good, NEW_WINDOW_ID), good)


if __name__ == "__main__":
    unittest.main()
