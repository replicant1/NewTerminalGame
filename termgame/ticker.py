"""The deadline decision — a pure function of (now, the next deadline).

PURE. It imports no clock: **the time arrives as a parameter**, exactly as a
``random.Random`` does in the rest of the core (architecture C7). That is what
makes GHOST-1's timing testable without waiting for it.

The game has **one** deadline and one thread (architecture C4). The ghost is
due about seven times a second whether or not the player is moving (GHOST-1),
and the loop realises that by waiting for a key for only as long as there is
until the next tick.

The one thing that matters here is **how the deadline advances**::

    next_deadline = advanced(next_deadline)       # additive — no drift
    next_deadline = now + GHOST_TICK_SECONDS      # WRONG — drift accumulates

Every reading of a clock is a little late: the loop notices the deadline has
passed some milliseconds after it did. Adding a tick to the *deadline* throws
that lateness away; adding a tick to *now* keeps it, and keeps the next one,
and the next. The architect measured 70 ticks in 10.005 s — 6.997 ticks/s,
mean drift 4.15 ms, max 5.08 ms — with the additive form.
"""

#: About seven times a second (GHOST-1).
GHOST_TICKS_PER_SECOND = 7.0

#: One tick, in seconds. 1/7 s = 142.857 ms.
GHOST_TICK_SECONDS = 1.0 / GHOST_TICKS_PER_SECOND


def first_deadline(now: float, tick: float = GHOST_TICK_SECONDS) -> float:
    """When the ghost is first due, given the clock reads ``now``.

    One whole tick after the first picture is painted, so the player sees the
    starting position before anything moves (START-5).
    """
    return now + tick


def wait_milliseconds(now: float, deadline: float) -> int:
    """How long to wait for a key: all the time there is until ``deadline``.

    Never negative — a negative timeout makes ncurses block forever, which
    would stop the ghost the moment the loop ran a hair late. A deadline that
    has already passed means *do not wait at all*.

    Truncated rather than rounded up, which is what the architect measured:
    waking a fraction of a millisecond early costs one extra turn of the loop
    and never overshoots the tick.
    """
    remaining = deadline - now
    if remaining <= 0.0:
        return 0
    return int(remaining * 1000.0)


def is_due(now: float, deadline: float) -> bool:
    """Whether the tick at ``deadline`` has come due by ``now``.

    At the deadline exactly, it is due.
    """
    return now >= deadline


def advanced(deadline: float, tick: float = GHOST_TICK_SECONDS) -> float:
    """The deadline after this one.

    **Additive.** It takes no ``now`` because it must not have one: adding a
    tick to the clock instead of to the deadline is how a game accumulates
    drift, and there is no way to write that mistake through this function.
    """
    return deadline + tick
