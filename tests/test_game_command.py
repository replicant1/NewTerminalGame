"""The command the launcher runs in the window it owns, as text.

WI-3's risky facts are all facts about this one string: which module it starts,
whether it is bounded, whether ``exec`` survives every hop, and whether the size
it waits for is the size the launcher actually sets. Plan §11.6 made the case
for asserting on generated script text rather than on Python calls, and it
applies here for the same reason — a test that watched a well-behaved builder
being called would not notice the string naming the wrong module, swapping rows
for columns, or dropping the ``exec``.
"""

import contextlib
import io
import os
import unittest

from launcher import script
from launcher.game import (
    DEFAULT_HOLD_SECONDS,
    GAME_MODULE,
    GATE_ATTEMPTS,
    REPOSITORY_ROOT,
    game_command,
    main,
    size_gate,
)


def imports_anything_from(source, package):
    """Does this source import that package? Import lines only, so the name
    appearing in a docstring — which in this module it very deliberately does —
    does not count."""
    for line in source.splitlines():
        stripped = line.strip()
        if not (stripped.startswith("import ") or stripped.startswith("from ")):
            continue
        for word in stripped.replace(",", " ").split():
            if word in ("from", "import"):
                continue
            if word.split(".")[0] == package:
                return True
    return False


class WhatItStarts(unittest.TestCase):

    def test_it_starts_the_real_game_module(self):
        self.assertIn("-m terminalgame.game_main", game_command())

    def test_the_game_is_named_as_text_and_never_imported(self):
        """Plan §3 — the launcher process shares no code with the game.

        Narrow on purpose: this is about the module WI-3 adds. Walking the whole
        of ``launcher/`` for layer violations is WI-12's, and is not done here.
        """
        with open(os.path.join(REPOSITORY_ROOT, "launcher", "game.py"),
                  "r", encoding="utf-8") as handle:
            source = handle.read()
        self.assertFalse(imports_anything_from(source, "terminalgame"))
        self.assertIsInstance(GAME_MODULE, str)

    def test_it_runs_from_the_repository_root_so_the_game_can_be_found(self):
        # The window runs a fresh login shell in the player's home directory,
        # where `python3 -m terminalgame.game_main` finds nothing.
        self.assertIn("cd ", game_command(repository_root="/some/root"))
        self.assertIn("/some/root", game_command(repository_root="/some/root"))

    def test_the_root_it_defaults_to_really_holds_both_halves(self):
        # If this ever stops being true the game would not start, and the only
        # place it would show is a window on someone's desktop.
        self.assertTrue(os.path.isdir(os.path.join(REPOSITORY_ROOT, "launcher")))
        self.assertTrue(os.path.isdir(os.path.join(REPOSITORY_ROOT, "terminalgame")))

    def test_a_root_that_cannot_be_entered_stops_rather_than_running_elsewhere(self):
        # `cd ... || exit 1` — otherwise the game would start in whatever
        # directory the shell happened to be in and fail obscurely.
        self.assertIn("|| exit 1", game_command())

    def test_the_shell_is_replaced_by_the_game_rather_than_waiting_on_it(self):
        """``exec`` is what makes the tab go idle when the game exits.

        Caution C2 turns on the tab's busy flag, and a login shell or an
        intermediate ``sh`` left alive underneath the game would keep that flag
        raised for ever — so the launcher could never close the window.
        """
        command = game_command()
        game_part = command[command.index("cd "):]
        self.assertIn("; exec ", game_part)
        self.assertLess(game_part.index("; exec "), game_part.index("-m "))


class HowLongTheWindowLives(unittest.TestCase):

    def test_the_hold_is_always_passed_explicitly(self):
        # Never inherited from the game's own default: how long a window sits on
        # the player's desktop is this join's decision to make out loud.
        self.assertIn("--hold", game_command())

    def test_the_hold_that_was_asked_for_is_the_hold_that_is_passed(self):
        self.assertIn("--hold 12", game_command(hold_seconds=12))
        self.assertIn("--hold 0.5", game_command(hold_seconds=0.5))

    def test_the_default_hold_is_finite(self):
        self.assertGreater(DEFAULT_HOLD_SECONDS, 0)
        self.assertLess(DEFAULT_HOLD_SECONDS, 60)

    def test_a_negative_hold_is_refused_rather_than_launched(self):
        # UnusableLauncher fails the test if anything reaches the desktop, so
        # this establishes that no window is opened, not merely that argparse
        # complained.
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                main(["--hold", "-1"], launcher=UnusableLauncher())


class TheSizeGate(unittest.TestCase):
    """The window is not yet 40 x 30 when the game starts looking at it."""

    def test_it_waits_for_the_rows_and_columns_the_launcher_actually_sets(self):
        gate = size_gate()
        self.assertIn("-ge %d" % (script.ROWS,), gate)
        self.assertIn("-ge %d" % (script.COLUMNS,), gate)

    def test_rows_are_compared_against_rows_and_columns_against_columns(self):
        """``stty size`` reports rows first, which is the easy thing to get
        backwards — and getting it backwards would wait for a 40-row, 30-column
        window that the launcher never asks for, so the gate would always time
        out and the race would be back."""
        gate = size_gate(columns=50, rows=20)
        self.assertIn("${1:-0} -ge 20", gate)
        self.assertIn("${2:-0} -ge 50", gate)

    def test_it_is_bounded_and_cannot_wait_for_ever(self):
        gate = size_gate(attempts=7)
        self.assertIn("-lt 7", gate)
        self.assertGreater(GATE_ATTEMPTS, 0)

    def test_it_falls_through_rather_than_aborting_when_it_gives_up(self):
        """A screen that really is too small must still reach the game, which
        reports it loudly (SCRN). The gate removes a race; it must never
        suppress the failure."""
        command = game_command()
        self.assertLess(command.index("done"), command.index("-m "))
        self.assertNotIn("exit 2", command)


class SafeToPutInAScript(unittest.TestCase):

    def test_it_is_one_line_because_a_newline_would_be_a_second_command(self):
        command = game_command()
        self.assertEqual(1, len(command.splitlines()))

    def test_applescript_will_accept_it(self):
        # applescript_string refuses control characters outright, so a command
        # carrying one could never be launched at all.
        quoted = script.applescript_string("exec " + game_command())
        self.assertIn(GAME_MODULE, quoted)

    def test_a_root_with_a_space_in_it_stays_one_argument(self):
        command = game_command(repository_root="/Users/someone/Terminal Game")
        self.assertIn("'/Users/someone/Terminal Game'", command)

    def test_a_root_with_a_quote_in_it_is_still_quoted_safely(self):
        command = game_command(repository_root="/tmp/o'brien")
        quoted = script.applescript_string("exec " + command)
        self.assertIn(GAME_MODULE, quoted)

    def test_the_interpreter_is_quoted_too(self):
        command = game_command(python_executable="/opt/py 3/bin/python3")
        self.assertIn("'/opt/py 3/bin/python3'", command)


class UnusableLauncher(object):
    """Standing in where the test asserts the launcher is never reached."""

    def run(self, command):
        raise AssertionError("nothing should have been launched: %r" % (command,))


if __name__ == "__main__":
    unittest.main()
