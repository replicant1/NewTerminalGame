"""The Application layer: the loop that drives everything else.

One thread and no locks. It reads a key, moves the player, ticks the ghost,
asks Presentation for a frame and hands it to the screen port — and it is the
only part of the game that knows what a clock is.

**Nothing depends on Application** (implementation plan §3). It depends on
Presentation, on the Domain and on the Screen port, and on nothing above it,
because there is nothing above it.

It holds no rules. Whether a move is legal, whether the game has ended, where
the ghost goes — all of that belongs to the Domain and is asked rather than
decided here. What this layer owns is *when*: when a key is read, when the
ghost moves, and when the picture is redrawn.
"""
