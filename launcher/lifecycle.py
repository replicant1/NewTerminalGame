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

#: How often to ask while the answer is still likely to be changing — a window
#: whose login shell has only just started, or whose command has only just
#: failed, settles within a second or two of being created.
POLL_INTERVAL = 0.1

#: How long to keep asking that often before settling down.
SETTLE_AFTER = 2.0

#: And how often to ask after that. Every ask is an ``osascript`` process and
#: an Apple event to Terminal: a trivial round trip was measured at 36 ms on
#: this machine, and the real call is an Apple event on top of that. At a tenth
#: of a second, a ten-minute game spends about 6,000 processes and 215 seconds
#: of subprocess time beside the game it is watching — and a game lasts as long
#: as the player wants it to, so there is no start-up window to bound it.
#:
#: Nothing needs that rate. The question being asked is "has the player quit
#: yet", and nobody notices a window closing a second after they press ``q``.
#: The same ten minutes costs about 620 asks this way.
SETTLED_POLL_INTERVAL = 1.0


class GameWindow(object):
    """A window this launcher created, and what it knows about it."""

    def __init__(
        self,
        window_id,
        position=None,
        size=None,
        reference=None,
        screen=None,
        asked_for=None,
    ):
        self.window_id = window_id
        #: Where the window actually ended up, as the desktop reports it.
        self.position = position
        #: Where the launcher's arithmetic asked for it to go. The two differ
        #: when macOS constrains the window to the screen it is on.
        self.asked_for = asked_for
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
        settle_after=SETTLE_AFTER,
        settled_poll_interval=SETTLED_POLL_INTERVAL,
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
        self.settle_after = settle_after
        self.settled_poll_interval = settled_poll_interval
        self.clock = clock
        self.sleeper = sleeper

    # -- the whole life of a window -------------------------------------

    def run(self, command):
        """Open a window running ``command``, wait for it to finish, close it.

        Returns the :class:`ReapResult`. The window is the launcher's throughout
        and belongs to nobody else.

        It waits by :meth:`has_live_processes` — the tab's process list — which
        is the only thing in this system that answers "is the command still
        running" correctly for a window that has been given a grid. Until WI-13
        this method waited on the tab's ``busy`` flag instead, and so closed the
        window while the game was still in it and reported success.

        An empty process list is an unambiguous "nothing is running in there"
        and needs no matching of names, because :func:`launcher.script.open_window_running`
        ``exec``s the command and leaves no login shell alive underneath it. It
        covers the start-up gap for free as well: a window whose login shell has
        not finished starting lists that shell, so it is never mistaken for a
        window whose game has ended.

        ``launcher.game`` had its own copy of this called ``play``, written when
        ``run`` still consulted ``busy``. WI-13 removed that difference and the
        copy outlived it, warning readers away from this method on grounds that
        no longer existed. There is one route now, and this is it.
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
                asked_for = self.default_position
            else:
                asked_for = target_position(reference, size, screen, self.offset)
            # Where it *went*, not where it was asked to go. macOS constrains a
            # window to the screen it is on, and it was measured doing exactly
            # that on this machine: a window asked for y = -1353, on a display
            # above the main one, landed at y = 30 instead. Recording the
            # arithmetic rather than the outcome would mean the launcher
            # believed something about the player's desktop that is not true.
            position = self.desktop.move(window_id, asked_for)
        except BaseException as cause:
            # `BaseException`, and that is deliberate rather than careless. A
            # window exists by this point, so caution C3 says deal with the
            # window before dealing with the error -- and that is as true of a
            # Ctrl-C as of an `AutomationError`.
            #
            # The cost is that a `KeyboardInterrupt` here comes out as a
            # `LaunchFailed` rather than as itself, so the interrupt does not
            # propagate as an interrupt. That is the better trade: `LaunchFailed`
            # carries the `ReapResult`, which is how anybody learns whether the
            # window was taken back or is still sitting on the desktop, and on a
            # Ctrl-C that is exactly what the person needs to be told. Re-raising
            # the interrupt unchanged would throw that away. The original is
            # kept as `cause` and chained with `from`.
            raise LaunchFailed(
                cause, window_id, self.reap(window_id, self.failure_timeout)
            ) from cause

        return GameWindow(window_id, position, size, reference, screen, asked_for)

    # -- getting rid of it again ----------------------------------------

    def has_live_processes(self, window_id):
        """Is anything running in that window?

        **This is the only answer to that question in the system**, and caution
        C2 turns on it: closing a window with a live process in it raises a
        modal sheet that only a person can dismiss, and every automation call
        after that hangs behind it.

        It reads the tab's process list. The tab's ``busy`` flag used to be a
        second answer and was a wrong one — setting ``number of columns`` and
        ``number of rows``, which WIN-2 requires and :meth:`open` therefore
        does to every window it creates, makes ``busy`` report false for the
        whole life of the process. It was removed in WI-13 rather than left
        available, because one question with two answers is how the launcher
        came to kill the game and report success.

        See :func:`launcher.script.window_processes` and
        ``docs/findings/WI-3-busy-is-false-after-a-grid-resize.md``.
        """
        return bool(self.desktop.processes(window_id))

    def wait_until_idle(self, window_id, timeout, still_running=None):
        """Is nothing running in that window? Polls, bounded, and gives up.

        ``still_running`` is the question asked each time round. It defaults to
        :meth:`has_live_processes`, which is the only thing that answers it
        correctly for a window this launcher created; the parameter stays so a
        test can inject one, not so that callers have a choice to get wrong.

        **The asking slows down.** Each ask costs a subprocess and an Apple
        event, and this loop runs for the whole length of a game — see
        :data:`SETTLED_POLL_INTERVAL`. So it asks quickly while the answer is
        still likely to be changing and then settles, which is
        :meth:`_interval_after`. The bound is unaffected: no sleep ever runs
        past the deadline.
        """
        if still_running is None:
            still_running = self.has_live_processes
        started = self.clock()
        deadline = started + timeout
        while True:
            try:
                if not still_running(window_id):
                    return True
            except AutomationError:
                # A window we cannot even ask about is not one we should close.
                return False
            now = self.clock()
            if now >= deadline:
                return False
            # Never sleep past the deadline: giving up late is still late.
            self.sleeper(min(self._interval_after(now - started), deadline - now))

    def _interval_after(self, elapsed):
        """How long to wait before asking again, ``elapsed`` seconds in.

        Two speeds rather than a ramp, because the thing being waited on has
        two phases and not a continuum: a window is either still settling into
        existence, or it is running a game that will end whenever the player
        decides. Never shorter than ``poll_interval``, so a caller that asks
        for a slow poll is not quietly given a fast one.
        """
        if elapsed < self.settle_after:
            return self.poll_interval
        return max(self.poll_interval, self.settled_poll_interval)

    def reap(self, window_id, timeout, still_running=None):
        """Close the captured window once it is idle, and check that it went.

        Never raises: this is what runs on the failure path, where an exception
        of its own would bury the failure it was called to clean up after.
        """
        try:
            return self._reap(window_id, timeout, still_running)
        except BaseException as error:  # pragma: no cover - belt and braces
            return ReapResult(False, "reaping failed: %s" % (error,), window_id)

    def _reap(self, window_id, timeout, still_running=None):
        if not self.wait_until_idle(window_id, timeout, still_running):
            return ReapResult(
                False,
                "something is still running in window %r after %.1fs and it "
                "was left open on "
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
