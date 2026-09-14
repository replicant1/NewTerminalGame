"""The seam: the one place in the system where a subprocess is started.

Everything above this module deals in :class:`~launcher.script.ScriptCall`
values, which are text. Everything below it is ``osascript``. Standing a
different runner in this one place is what lets the launcher's ordering,
placement and failure handling be tested with no desktop anywhere near them.

Caution C4 lives here: no call is unbounded. The script carries its own
AppleScript ``with timeout``, and this module puts a wall-clock bound around the
process on top of it, because an Apple Event that never returns would otherwise
hang the launcher with a window already open on the player's desktop.
"""

import subprocess


class AutomationError(Exception):
    """The desktop refused, failed, or answered something unusable."""

    def __init__(self, message, call=None, stderr=""):
        Exception.__init__(self, message)
        self.call = call
        self.stderr = stderr


class AutomationTimeout(AutomationError):
    """The call did not come back inside its bound, and was killed."""


class OsascriptRunner(object):
    """Runs a :class:`~launcher.script.ScriptCall` through ``osascript``.

    The script arrives on standard input rather than as an argument, so no
    quoting of the script itself is needed and no script text is exposed in the
    process table.
    """

    #: Seconds added to the script's own timeout before the process is killed.
    #: The AppleScript ``with timeout`` should fire first and give a usable
    #: error; this is the backstop for when it does not.
    GRACE = 3.0

    def __init__(self, executable="/usr/bin/osascript", grace=GRACE):
        self.executable = executable
        self.grace = grace

    def run(self, call):
        """Run ``call`` and return its result as stripped text.

        Raises :class:`AutomationTimeout` if the process had to be killed, and
        :class:`AutomationError` if it failed.
        """
        deadline = call.timeout + self.grace
        try:
            completed = subprocess.run(
                [self.executable, "-"],
                input=call.source,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=deadline,
            )
        except subprocess.TimeoutExpired:
            raise AutomationTimeout(
                "%s did not answer within %.1fs and was killed"
                % (call.name, deadline),
                call=call,
            )
        if completed.returncode != 0:
            raise AutomationError(
                "%s failed with status %d: %s"
                % (call.name, completed.returncode, completed.stderr.strip()),
                call=call,
                stderr=completed.stderr,
            )
        return completed.stdout.strip()
