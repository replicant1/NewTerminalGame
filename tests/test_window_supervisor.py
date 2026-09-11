"""The supervisor sequence -- WIN-1..5 in order, with Terminal replaced.

No window is opened here. ``run_osascript`` is swapped for a fake that records
the scripts it was handed and answers them, so the test can assert the thing
that actually matters: *which window was closed, when, and whether the failure
path closed it too*.
"""

import unittest

from termgame import window

NEW_WINDOW_ID = 4242
OTHER_WINDOW_ID = 99


#: A tab running the game, as measured: not busy, two processes
#: (``login`` and ``Python``). See ``window.script_tab_state``.
PLAYING = "false 2"
#: The same tab once the child has exited.
ENDED = "false 0"


class FakeTerminal(object):
    """Answers the scripts the supervisor sends, and remembers them.

    ``states`` is consumed one poll at a time; the last value repeats.
    """

    def __init__(self, tty_position="none", front_position="10 20", states=None):
        self.scripts = []
        self.tty_position = tty_position
        self.front_position = front_position
        self.states = list(states or [PLAYING, ENDED])
        self.closed = []
        self.raise_on = None

    def __call__(self, script, timeout=20.0):
        self.scripts.append(script)
        if self.raise_on and self.raise_on in script:
            raise window.WindowError("deliberate failure: " + self.raise_on)
        if "tty of tab 1" in script:
            return self.tty_position
        if "set p to position of w" in script:
            return self.front_position
        if "return id of newWindow" in script:
            return str(NEW_WINDOW_ID)
        if "count of processes" in script and "close gameWindow" not in script:
            return self._next_state()
        if "close gameWindow" in script:
            if self._next_state() != ENDED:
                return "busy"
            self.closed.append(script)
            return "closed"
        return ""

    def _next_state(self):
        if len(self.states) > 1:
            return self.states.pop(0)
        return self.states[0]

    def kinds(self):
        """The sequence of what was asked, as short labels."""
        labels = []
        for script in self.scripts:
            if "tty of tab 1" in script:
                labels.append("reference-tty")
            elif "set p to position of w" in script:
                labels.append("reference-front")
            elif "do script" in script:
                labels.append("open")
            elif "number of columns" in script:
                labels.append("configure")
            elif "set position of" in script:
                labels.append("move")
            elif "close gameWindow" in script:
                labels.append("close")
            elif "count of processes" in script:
                labels.append("poll")
            else:
                labels.append("other")
        return labels


class SupervisorTest(unittest.TestCase):
    def setUp(self):
        self.real_run = window.run_osascript
        self.real_displays = window.displays
        self.real_tty = window.controlling_tty
        self.reports = []
        self.real_sleep = window.time.sleep
        window.time.sleep = lambda seconds: None
        window.displays = lambda: [(0, 0, 1512, 982)]
        window.controlling_tty = lambda: "/dev/ttys009"

    def tearDown(self):
        window.run_osascript = self.real_run
        window.displays = self.real_displays
        window.controlling_tty = self.real_tty
        window.time.sleep = self.real_sleep

    def supervise(self, terminal, root="/tmp/repo", close_grace=0):
        window.run_osascript = terminal
        return window.supervise(
            root, report=self.reports.append, close_grace=close_grace
        )

    def test_the_window_is_opened_configured_placed_waited_on_then_closed(self):
        terminal = FakeTerminal()
        self.assertEqual(0, self.supervise(terminal))
        kinds = terminal.kinds()
        self.assertEqual("open", kinds[kinds.index("open")])
        self.assertLess(kinds.index("open"), kinds.index("configure"))
        self.assertLess(kinds.index("configure"), kinds.index("move"))
        self.assertLess(kinds.index("move"), kinds.index("poll"))
        self.assertLess(kinds.index("poll"), kinds.index("close"))

    def test_the_window_that_is_closed_is_the_one_that_was_created(self):
        terminal = FakeTerminal()
        self.supervise(terminal)
        self.assertEqual(1, len(terminal.closed))
        self.assertIn(
            "first window whose id is %d" % NEW_WINDOW_ID, terminal.closed[0]
        )
        self.assertNotIn(
            "first window whose id is %d" % OTHER_WINDOW_ID, terminal.closed[0]
        )

    def test_nothing_after_the_open_addresses_anything_but_the_new_window(self):
        terminal = FakeTerminal()
        self.supervise(terminal)
        after_open = terminal.scripts[terminal.kinds().index("open") + 1 :]
        self.assertTrue(after_open)
        for script in after_open:
            self.assertIn("first window whose id is %d" % NEW_WINDOW_ID, script)
            self.assertNotIn("front window", script)

    def test_the_window_is_placed_below_and_right_of_the_reference(self):
        terminal = FakeTerminal(tty_position="200 100")
        self.supervise(terminal)
        move = [s for s in terminal.scripts if "set position of" in s][0]
        self.assertIn("to {230, 130}", move)

    def test_the_front_window_is_used_when_no_tab_has_our_tty(self):
        terminal = FakeTerminal(tty_position="none", front_position="400 200")
        self.supervise(terminal)
        move = [s for s in terminal.scripts if "set position of" in s][0]
        self.assertIn("to {430, 230}", move)

    def test_the_child_is_launched_by_name_with_no_arguments(self):
        terminal = FakeTerminal()
        self.supervise(terminal, root="/Users/somebody/NewTerminalGame")
        opened = [s for s in terminal.scripts if "do script" in s][0]
        self.assertIn(
            "do script \"exec '/Users/somebody/NewTerminalGame/Terminal Game'\"",
            opened,
        )

    def test_an_empty_window_is_closed_when_configuring_it_fails(self):
        # Rule 5: the failure path runs the same wait-then-close-by-id.
        terminal = FakeTerminal(states=[ENDED])
        terminal.raise_on = "number of columns"
        with self.assertRaises(window.WindowError):
            self.supervise(terminal)
        self.assertEqual(1, len(terminal.closed))
        self.assertIn(
            "first window whose id is %d" % NEW_WINDOW_ID, terminal.closed[0]
        )

    def test_a_window_still_running_the_game_is_left_open_not_forced(self):
        # Rule 3: a busy tab is never closed -- that raises a modal sheet.
        terminal = FakeTerminal(states=[PLAYING])
        terminal.raise_on = "number of columns"
        with self.assertRaises(window.WindowError):
            self.supervise(terminal)
        self.assertEqual([], terminal.closed)
        self.assertTrue(
            any(str(NEW_WINDOW_ID) in message for message in self.reports),
            "the id of the window left open was not reported: %r" % self.reports,
        )

    def test_the_supervisor_waits_for_the_game_to_end_before_closing(self):
        # WIN-5 on the architect's reading of A1: the last picture stays, the
        # player presses q, the process exits, the window closes then.
        terminal = FakeTerminal(states=[PLAYING, PLAYING, ENDED])
        self.supervise(terminal)
        self.assertEqual(1, len(terminal.closed))
        self.assertGreaterEqual(terminal.kinds().count("poll"), 3)


class WaitAndCloseTest(unittest.TestCase):
    """``wait_until_idle`` and ``close_when_idle`` on their own."""

    def setUp(self):
        self.real_run = window.run_osascript
        self.slept = []

    def tearDown(self):
        window.run_osascript = self.real_run

    def answer(self, states):
        remaining = list(states)

        def fake(script, timeout=20.0):
            self.sent.append(script)
            return remaining.pop(0) if len(remaining) > 1 else remaining[0]

        self.sent = []
        window.run_osascript = fake

    def test_waiting_returns_true_once_the_game_has_ended(self):
        self.answer([PLAYING, PLAYING, ENDED])
        self.assertTrue(
            window.wait_until_idle(7, timeout=5, sleep=self.slept.append)
        )
        self.assertEqual([0.2, 0.2], self.slept)

    def test_a_tab_that_is_busy_counts_as_running_even_with_no_processes(self):
        # Measured: busy is briefly true while the shell is being replaced.
        self.answer(["true 0", "true 0", ENDED])
        self.assertTrue(
            window.wait_until_idle(7, timeout=5, sleep=self.slept.append)
        )
        self.assertEqual([0.2, 0.2], self.slept)

    def test_waiting_gives_up_rather_than_hanging_for_ever(self):
        self.answer([PLAYING])
        self.assertFalse(
            window.wait_until_idle(7, timeout=0, sleep=self.slept.append)
        )

    def test_an_empty_tab_is_not_read_as_ended_during_the_startup_grace(self):
        # The window must not be closed on a game that has not painted yet.
        self.answer([ENDED])
        self.assertFalse(
            window.wait_until_idle(
                7, timeout=0, startup=5.0, sleep=self.slept.append
            )
        )

    def test_close_when_idle_does_not_close_a_tab_still_running_the_game(self):
        self.answer([PLAYING])
        self.assertFalse(
            window.close_when_idle(7, timeout=0, sleep=self.slept.append)
        )
        self.assertFalse([s for s in self.sent if "close gameWindow" in s])

    def test_close_when_idle_closes_a_tab_whose_game_has_ended(self):
        self.answer([ENDED, "closed"])
        self.assertTrue(
            window.close_when_idle(7, timeout=1, sleep=self.slept.append)
        )
        self.assertTrue([s for s in self.sent if "close gameWindow" in s])


if __name__ == "__main__":
    unittest.main()
