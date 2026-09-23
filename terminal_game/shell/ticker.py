"""When the next tick is due. Pure arithmetic; the caller supplies the clock.

A timer re-armed with a fixed delay after each tick runs slow by however long
each tick's work took, and slower still while keys are being handled. So
ticks are scheduled against deadlines instead: tick *n* is due at
``start + n * period``, and each delay is whatever remains until the next
deadline. The average rate is then exactly ``hz`` however long the handlers
take, as long as they take less than a period (GHOST-1, WI-3/C11).
"""

#: The ghost's cadence: "about seven times a second" (GHOST-1).
TICK_HZ = 7


class TickSchedule:
    """Deadlines for a repeating tick, ``hz`` times a second, from ``start``."""

    def __init__(self, start: float, hz: float = TICK_HZ) -> None:
        if hz <= 0:
            raise ValueError(f"tick rate must be positive, got {hz!r}")
        self.period = 1.0 / hz
        self._next = start + self.period

    def delay_ms(self, now: float) -> int:
        """Milliseconds from ``now`` until the next deadline, never negative."""
        return max(0, round((self._next - now) * 1000))

    def advance(self, now: float) -> None:
        """Record that the tick due at the current deadline has been delivered.

        If the caller has fallen more than a whole period behind (the process
        was stopped, say), the schedule restarts from ``now`` rather than
        firing a burst of ticks to catch up.
        """
        self._next += self.period
        if self._next < now:
            self._next = now + self.period
