"""The repeating tick at the ghost's cadence (GHOST-1).

The windowing toolkit offers a one-shot "call me back in N milliseconds".  A
repeating tick is therefore something the Shell builds: deliver the tick, then
arm the next one.  That re-arming is the whole of this class.
"""

from __future__ import annotations

from typing import Callable, Optional

from .toolkit import TimerHandle, Toolkit


class TickTimer:
    """Delivers a tick every *interval_ms* until it is stopped.

    The order inside :meth:`_expire` is deliberate: the tick is delivered
    first, and the next one is armed only if the timer is still running
    afterwards.  Two things follow, both of which matter.

    * If the tick's recipient raises, nothing is left scheduled.  The window
      owner is about to reap the window, and a callback pointing at a
      half-dead session would fire in the middle of that.
    * If the tick's recipient ends the session — which it may, a tick is how
      the ghost catches the player — the timer notices it has been stopped and
      does not arm another.
    """

    def __init__(
        self,
        toolkit: Toolkit,
        interval_ms: int,
        on_tick: Callable[[], None],
    ) -> None:
        self._toolkit = toolkit
        self._interval_ms = interval_ms
        self._on_tick = on_tick
        self._handle: Optional[TimerHandle] = None
        self._running = False

    @property
    def interval_ms(self) -> int:
        return self._interval_ms

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Begin ticking.  Starting an already-running timer does nothing."""
        if self._running:
            return
        self._running = True
        self._arm()

    def stop(self) -> None:
        """Stop ticking, cancelling any tick already scheduled.

        Safe to call on a timer that was never started, and safe to call
        twice: the session's shutdown path does exactly that.
        """
        self._running = False
        if self._handle is not None:
            handle, self._handle = self._handle, None
            self._toolkit.cancel_scheduled(handle)

    def _arm(self) -> None:
        self._handle = self._toolkit.schedule_once(self._interval_ms, self._expire)

    def _expire(self) -> None:
        self._handle = None
        if not self._running:
            return
        self._on_tick()
        if self._running:
            self._arm()
