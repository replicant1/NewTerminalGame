"""``python3 -m launcher <command>`` — the launcher process end to end."""

import io
import unittest

from launcher.__main__ import main
from launcher.lifecycle import LaunchFailed, ReapResult


class RecordingLauncher(object):
    def __init__(self, result=None, raises=None):
        self.commands = []
        self.result = result or ReapResult(True, "window 7653 closed", 7653)
        self.raises = raises

    def run(self, command):
        self.commands.append(command)
        if self.raises is not None:
            raise self.raises
        return self.result


class TheCommandLine(unittest.TestCase):
    def test_no_command_is_a_usage_error_and_nothing_is_launched(self):
        launcher = RecordingLauncher()
        err = io.StringIO()
        self.assertEqual(2, main([], launcher=launcher, err=err))
        self.assertEqual([], launcher.commands)
        self.assertIn("usage:", err.getvalue())

    def test_the_arguments_are_joined_into_one_shell_command(self):
        launcher = RecordingLauncher()
        main(["/repo/Terminal Game", "--seed", "4"], launcher=launcher, out=io.StringIO())
        self.assertEqual(["/repo/Terminal Game --seed 4"], launcher.commands)


class WhatItReports(unittest.TestCase):
    def test_a_window_that_was_closed_is_a_success(self):
        out = io.StringIO()
        status = main(["/bin/echo", "hi"], launcher=RecordingLauncher(), out=out)
        self.assertEqual(0, status)
        self.assertIn("window 7653 closed", out.getvalue())

    def test_a_window_left_open_is_a_failure_and_says_so(self):
        launcher = RecordingLauncher(
            ReapResult(False, "window 7653 is still busy", 7653)
        )
        out = io.StringIO()
        self.assertEqual(1, main(["/bin/echo", "hi"], launcher=launcher, out=out))
        self.assertIn("still busy", out.getvalue())

    def test_a_failed_launch_names_the_window_it_could_not_take_back(self):
        failure = LaunchFailed(
            RuntimeError("the desktop said no"),
            7653,
            ReapResult(False, "window 7653 is still busy", 7653),
        )
        err = io.StringIO()
        launcher = RecordingLauncher(raises=failure)
        self.assertEqual(1, main(["/bin/echo", "hi"], launcher=launcher, err=err))
        self.assertIn("7653", err.getvalue())
        self.assertIn("the desktop said no", err.getvalue())


if __name__ == "__main__":
    unittest.main()
