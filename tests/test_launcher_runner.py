"""The one place a subprocess is started, exercised against a real subprocess.

No mocking here and no desktop either. ``OsascriptRunner`` invokes
``<executable> -`` and feeds the script in on standard input, and ``/bin/sh -``
does exactly that too — so the runner can be driven end to end, bound and all,
with a shell standing in for ``osascript``. What these tests assert is what
happened: the value that came back, and the exception that was raised.
"""

import os
import tempfile
import time
import unittest

from launcher.runner import AutomationError, AutomationTimeout, OsascriptRunner
from launcher.script import ScriptCall


def shell_runner(grace=0.2):
    return OsascriptRunner(executable="/bin/sh", grace=grace)


class WhatComesBack(unittest.TestCase):
    def test_the_scripts_output_is_returned_stripped(self):
        result = shell_runner().run(ScriptCall("echo", "echo '  7653  '", 5.0))
        self.assertEqual("7653", result)

    def test_the_script_reaches_the_process_on_standard_input(self):
        # Nothing of the script appears in the argument list, so a long or
        # quote-heavy script needs no shell quoting anywhere.
        result = shell_runner().run(
            ScriptCall("quotes", """printf '%s' 'a "b" c'""", 5.0)
        )
        self.assertEqual('a "b" c', result)


class WhenItFails(unittest.TestCase):
    def test_a_non_zero_exit_raises_an_automation_error(self):
        call = ScriptCall("refused", "echo 'not authorised' >&2; exit 1", 5.0)
        try:
            shell_runner().run(call)
        except AutomationError as error:
            self.assertIn("refused", str(error))
            self.assertIn("not authorised", error.stderr)
            self.assertIs(call, error.call)
        else:
            self.fail("a failing script should raise AutomationError")

    def test_the_error_is_not_a_timeout(self):
        try:
            shell_runner().run(ScriptCall("refused", "exit 1", 5.0))
        except AutomationTimeout:
            self.fail("a plain failure was reported as a timeout")
        except AutomationError:
            pass


class WhenItDoesNotComeBack(unittest.TestCase):
    """Caution C4: nothing the launcher runs is unbounded."""

    def test_a_script_that_hangs_is_killed_and_raises(self):
        call = ScriptCall("hangs", "sleep 30", 0.1)
        started = time.monotonic()
        self.assertRaises(AutomationTimeout, shell_runner(grace=0.2).run, call)
        self.assertLess(time.monotonic() - started, 5.0)

    def test_the_wait_is_the_scripts_timeout_plus_the_runners_grace(self):
        runner = OsascriptRunner(executable="/bin/sh", grace=0.3)
        started = time.monotonic()
        self.assertRaises(
            AutomationTimeout, runner.run, ScriptCall("hangs", "sleep 30", 0.4)
        )
        waited = time.monotonic() - started
        self.assertGreaterEqual(waited, 0.7)
        self.assertLess(waited, 3.0)

    def test_a_timeout_is_also_an_automation_error(self):
        # So a caller that only wants to know "the desktop did not answer" can
        # catch the one type.
        self.assertTrue(issubclass(AutomationTimeout, AutomationError))

    def test_the_killed_process_really_stops_running(self):
        # A bound that returns while the process carries on would be no bound at
        # all. The script keeps appending to a file until it is killed, so the
        # file stops growing exactly when the process stops.
        handle, marker = tempfile.mkstemp(prefix="launcher-runner-")
        os.close(handle)
        self.addCleanup(os.unlink, marker)
        script = (
            "exec /bin/sh -c 'while : ; do echo tick >> %s; sleep 0.02; done'"
            % (marker,)
        )
        self.assertRaises(
            AutomationTimeout,
            shell_runner(grace=0.2).run,
            ScriptCall("hangs", script, 0.2),
        )
        at_the_kill = os.path.getsize(marker)
        self.assertGreater(at_the_kill, 0, "the script never got going")
        time.sleep(0.4)
        self.assertEqual(at_the_kill, os.path.getsize(marker))


if __name__ == "__main__":
    unittest.main()
