"""The window lifecycle policy — the order things must happen in.

The dangerous parts of WIN-1 to WIN-5 are not any single automation call, they
are the *sequence*:

* ask the desktop where the player was looking **before** creating anything,
  because the moment the game's window exists it is the frontmost one and the
  launcher would otherwise measure itself;
* capture the new window's identity in the same breath as creating it, and name
  that identity in every call afterwards (caution C1);
* never close a window with something still running in it (caution C2);
* and if anything fails after the window exists, deal with the window before
  dealing with the error (caution C3).

None of that needs a desktop to be checked, because every desktop operation goes
through the adapter passed in, and the clock and the sleep do too.
"""

import time

from launcher.geometry import (
    DEFAULT_OFFSET,
    DEFAULT_POSITION,
    DEFAULT_SCREEN,
    target_position,
)
from launcher.runner import AutomationError

#: Seconds to wait for the window to fall idle after a *successful* session.
#: A game lasts as long as the player wants it to, so this is not a deadline
#: anybody should ever reach — but caution C4 says nothing waits forever, so it
#: is finite and it has a way out.
SESSION_TIMEOUT = 4 * 60 * 60.0

#: Seconds to wait for the window to fall idle when setup has already failed.
#: Short on purpose: the failure happened milliseconds after the window was
#: created, so either the shell has not got going yet and will be idle almost at
#: once, or the game is running and waiting for a player — in which case waiting
#: longer changes nothing and only delays the report.
FAILURE_TIMEOUT = 2.0

POLL_INTERVAL = 0.1


class GameWindow(object):
    """A window this launcher created, and what it knows about it."""

    def __init__(self, window_id, position=None, size=None, reference=None, screen=None):
        self.window_id = window_id
        self.position = position
        self.size = size
        #: The frame of the window the player was last looking at, or ``None``
        #: if the desktop would not say and a default position was used.
        self.reference = reference
        self.screen = screen

    def __repr__(self):
        return "GameWindow(window_id=%r, position=%r, size=%r)" % (
            self.window_id,
            self.position,
            self.size,
        )


class ReapResult(object):
    """What happened when the launcher tried to get rid of its own window."""

    def __init__(self, closed, reason, window_id=None):
        self.closed = closed
        self.reason = reason
        self.window_id = window_id

    def __repr__(self):
        return "ReapResult(closed=%r, reason=%r, window_id=%r)" % (
            self.closed,
            self.reason,
            self.window_id,
        )


class LaunchFailed(Exception):
    """Setup failed after the window already existed.

    ``reap`` says what became of that window. If ``reap.closed`` is false there
    is a window on the player's desktop that the launcher could not take back,
    and ``window_id`` names it so a human can.
    """

    def __init__(self, cause, window_id, reap):
        Exception.__init__(
            self,
            "launching the game window failed after it was created (window id %r): "
            "%s — %s" % (window_id, cause, reap.reason),
        )
        self.cause = cause
        self.window_id = window_id
        self.reap = reap


class WindowLauncher(object):
    """Creates, owns and destroys exactly one terminal window."""

    def __init__(
        self,
        desktop,
        offset=DEFAULT_OFFSET,
        default_screen=DEFAULT_SCREEN,
        default_position=DEFAULT_POSITION,
        session_timeout=SESSION_TIMEOUT,
        failure_timeout=FAILURE_TIMEOUT,
        poll_interval=POLL_INTERVAL,
        clock=time.monotonic,
        sleeper=time.sleep,
    ):
        self.desktop = desktop
        self.offset = offset
        self.default_screen = default_screen
        self.default_position = default_position
        self.session_timeout = session_timeout
        self.failure_timeout = failure_timeout
        self.poll_interval = poll_interval
        self.clock = clock
        self.sleeper = sleeper

    # -- the whole life of a window -------------------------------------

    def run(self, command):
        """Open a window running ``command``, wait for it to finish, close it.

        Returns the :class:`ReapResult`. The window is the launcher's throughout
        and belongs to nobody else.
        """
        window = self.open(command)
        return self.reap(window.window_id, self.session_timeout)

    def open(self, command):
        """Create the game's window and put it where WIN-4 asks for it."""
        reference = self._ask(self.desktop.reference_window)
        screen = self._ask(self.desktop.visible_screen)
        if screen is None:
            screen = self.default_screen

        # Everything above this line happened before a window existed. Nothing
        # below it may ask the desktop what is frontmost.
        window_id = self.desktop.open_window_running(command)

        try:
            self.desktop.configure(window_id)
            size = self.desktop.window_size(window_id)
            if reference is None:
                position = self.default_position
            else:
                position = target_position(reference, size, screen, self.offset)
            self.desktop.move(window_id, position)
        except BaseException as cause:
            raise LaunchFailed(
                cause, window_id, self.reap(window_id, self.failure_timeout)
            ) from cause

        return GameWindow(window_id, position, size, reference, screen)

    # -- getting rid of it again ----------------------------------------

    def wait_until_idle(self, window_id, timeout):
        """Is nothing running in that window? Polls, bounded, and gives up."""
        deadline = self.clock() + timeout
        while True:
            try:
                if not self.desktop.is_busy(window_id):
                    return True
            except AutomationError:
                # A window we cannot even ask about is not one we should close.
                return False
            if self.clock() >= deadline:
                return False
            self.sleeper(self.poll_interval)

    def reap(self, window_id, timeout):
        """Close the captured window once it is idle, and check that it went.

        Never raises: this is what runs on the failure path, where an exception
        of its own would bury the failure it was called to clean up after.
        """
        try:
            return self._reap(window_id, timeout)
        except BaseException as error:  # pragma: no cover - belt and braces
            return ReapResult(False, "reaping failed: %s" % (error,), window_id)

    def _reap(self, window_id, timeout):
        if not self.wait_until_idle(window_id, timeout):
            return ReapResult(
                False,
                "window %r is still busy after %.1fs and was left open on "
                "purpose: closing a window with a live process in it raises a "
                "modal sheet that only a person at the screen can dismiss, and "
                "every automation call after that would hang behind it"
                % (window_id, timeout),
                window_id,
            )
        try:
            self.desktop.close(window_id)
        except AutomationError as error:
            return ReapResult(False, "closing window %r failed: %s" % (window_id, error), window_id)
        try:
            still_visible = self.desktop.is_visible(window_id)
        except AutomationError as error:
            return ReapResult(
                True,
                "window %r was closed; whether it went could not be checked: %s"
                % (window_id, error),
                window_id,
            )
        if still_visible:
            return ReapResult(
                False, "window %r is still visible after being closed" % (window_id,), window_id
            )
        return ReapResult(True, "window %r closed" % (window_id,), window_id)

    # -- helpers ---------------------------------------------------------

    @staticmethod
    def _ask(query):
        """Run a pre-creation query, or return ``None`` if the desktop will not.

        Architecture assumption A2: a refused Accessibility permission must
        degrade to a documented default, not abort the game.
        """
        try:
            return query()
        except AutomationError:
            return None
