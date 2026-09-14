"""Stand-ins for the desktop, used by the launcher's tests.

The seam these plug into is :class:`launcher.runner.OsascriptRunner`, which is
the single place a subprocess is started. Standing in for it means the tests see
the *AppleScript text* the launcher would have sent to the desktop, which is the
thing worth asserting on: whether a script names the captured window id is a
fact about the script, not about which Python method happened to be called.
"""

from launcher.runner import AutomationError


class RecordingRunner(object):
    """A runner that records every script and answers from a script of replies.

    ``replies`` maps a call name to either a string (the answer), an exception
    instance (raised instead), a callable taking the call and returning the
    answer, or a list of those consumed in turn.
    """

    def __init__(self, replies=None):
        self.calls = []
        self.replies = dict(replies or {})

    # -- the seam -------------------------------------------------------

    def run(self, call):
        self.calls.append(call)
        reply = self.replies.get(call.name)
        if isinstance(reply, list):
            if not reply:
                raise AssertionError("no reply left for %s" % (call.name,))
            reply = reply.pop(0)
        if isinstance(reply, BaseException):
            raise reply
        if callable(reply):
            reply = reply(call)
        if reply is None:
            raise AssertionError(
                "the test did not say what %s should answer" % (call.name,)
            )
        return reply

    # -- what a test wants to know afterwards ---------------------------

    @property
    def names(self):
        return [call.name for call in self.calls]

    def sources_after(self, name):
        """Every script sent after the call named ``name``, excluding it."""
        index = self.names.index(name)
        return [call.source for call in self.calls[index + 1:]]

    def calls_named(self, name):
        return [call for call in self.calls if call.name == name]

    def source_of(self, name):
        matching = self.calls_named(name)
        if len(matching) != 1:
            raise AssertionError(
                "expected exactly one %s call, got %d" % (name, len(matching))
            )
        return matching[0].source


class FailingQueryRunner(RecordingRunner):
    """A recording runner whose named calls refuse, as a permission would."""

    def __init__(self, refuse, replies=None):
        RecordingRunner.__init__(self, replies)
        self.refuse = set(refuse)

    def run(self, call):
        if call.name in self.refuse:
            self.calls.append(call)
            raise AutomationError(
                "%s: Not authorised to send Apple events" % (call.name,), call=call
            )
        return RecordingRunner.run(self, call)


class FakeClock(object):
    """A clock and a sleep that move only when the code under test sleeps."""

    def __init__(self, start=0.0):
        self.now = start
        self.slept = []

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds
