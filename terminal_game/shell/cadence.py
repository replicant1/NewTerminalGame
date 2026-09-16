"""The ghost's cadence (GHOST-1).

GHOST-1: the ghost moves "one square at a time about seven times a second,
whether or not the player is moving".  That is the only clock in the game, and
it is expressed here once so that nothing else has to guess at it.
"""

from __future__ import annotations

#: GHOST-1, as written: about seven ghost moves a second.
GHOST_TICKS_PER_SECOND = 7

#: The same cadence as a whole number of milliseconds, which is the unit the
#: windowing toolkit's scheduler takes.  1000 / 7 is 142.857..., so 143 ms is
#: the nearest millisecond: 6.993 ticks a second.
TICK_INTERVAL_MS = 143
