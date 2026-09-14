"""The game loop: one thread, no locks, and a clock that does not drift.

GHOST-1, CTRL-1, CTRL-2, CTRL-4, CTRL-5, START-5, END-5, END-6 and SCRN-7.

## The one thing that is easy to get wrong

The ghost moves about seven times a second **whether or not the player does**
(GHOST-1). The loop has a single thread, so the only place it can wait is the
key read — which means the key read's timeout *is* the ghost's schedule.

**So the timeout is recomputed every pass, from the clock, as the time
remaining until the next tick.** Not a fixed timeout, and not a sleep:

* with a fixed timeout, every key press would restart the wait and postpone the
  ghost, so a player holding down an arrow could freeze it — GHOST-1 broken,
  silently, in a way that no test using keys that arrive on schedule would
  catch;
* with a sleep, a key arriving early would not be handled until the sleep
  ended, so the game would feel laggy in exactly the moments it should not.

The schedule is kept as an absolute deadline that advances by whole ticks
(`next_tick += TICK_SECONDS`), never as "now plus a tick". Anchoring it to the
clock rather than to when the last pass happened is what stops the ghost
drifting slower and slower as the loop's own work is added on each time round.
This is architecture caution C7.

If the loop ever falls far behind — a machine that stalled — the deadline is
caught up to the present **without** firing the missed ticks. A burst of ghost
moves to "catch up" would teleport it across the maze, which is worse than
having missed them.

## What this loop does not do

**It does not enforce END-5.** Once the outcome is decided, the Domain refuses
to move the player or the ghost — `move_player`, `advance_player` and
`advance_ghost` all return the state they were given. That guard has the
Domain's whole test suite behind it, and a second copy here would be the one
that rots. So there is no `if the game is over` around the player's move in
this file, and deliberately so.

What *is* here is the optimisation the plan asks for: once the game is over the
loop stops consulting the ghost's policy, because doing so would draw on the
random source to compute a move that is then thrown away. **Delete that check
and the loop is still correct**, which is the test of whether it is an
optimisation or a rule.

The redraw needs no check at all. The loop redraws when the state has *changed*,
and a change is detected by identity — the Domain returns the same object when
nothing happened, a convention WI-8 set for CTRL-3 and WI-10 kept. Once the game
is over nothing changes, so nothing is redrawn, and END-5's "the picture stands"
falls out of the Domain's guarantee rather than being asserted again here.
"""

from __future__ import annotations

import time

from terminalgame.domain.ghost_policy import ghost_move
from terminalgame.domain.maze import EAST, NORTH, SOUTH, WEST
from terminalgame.domain.rules import advance_ghost, advance_player
from terminalgame.screen.port import Key

#: GHOST-1 — "about seven times a second".
TICKS_PER_SECOND = 7.0
TICK_SECONDS = 1.0 / TICKS_PER_SECOND

#: CTRL-1 — the four arrow keys, and nothing else, move the player. `Key.UP` is
#: north, and north is `y - 1`: the rows count down from the top of the screen.
DIRECTION_OF_KEY = {
    Key.UP: NORTH,
    Key.DOWN: SOUTH,
    Key.LEFT: WEST,
    Key.RIGHT: EAST,
}

#: CTRL-4 — upper or lower case, at any point in the game.
QUIT_CHARACTERS = ("q", "Q")


def quits(key):
    """Is this the key that leaves the game? CTRL-4, and END-6 after an ending."""
    return (key is not None
            and key.is_printable
            and key.character in QUIT_CHARACTERS)


def direction_of(key):
    """The way that key moves the player, or `None` if it moves nobody.

    CTRL-5 — "no other key does anything". Anything that is not one of the four
    arrows answers `None` here and is then discarded by the caller, which is
    the whole of what "discarded" means: the loop does not look at it again.
    """
    if key is None:
        return None
    return DIRECTION_OF_KEY.get(key)


def next_deadline(deadline, now, tick_seconds=TICK_SECONDS):
    """The next tick's deadline, anchored to the schedule rather than to `now`.

    Advances by whole ticks so the ghost does not drift, and catches up past
    any ticks that were missed rather than firing them all at once.
    """
    deadline += tick_seconds
    if deadline <= now:
        # The loop fell behind. Skip what was missed instead of bursting.
        missed = int((now - deadline) // tick_seconds) + 1
        deadline += missed * tick_seconds
    return deadline


def play(screen, state, random_source, compose,
         clock=time.monotonic, tick_seconds=TICK_SECONDS,
         ghost_move=ghost_move):
    """Play until the player quits, and return the state they left.

    `compose(state)` builds the frame — injected rather than imported, because
    how a state becomes a picture is Presentation's business and the loop has
    no opinion about it.

    `ghost_move(maze, square, heading, random_source)` is the ghost's policy. It
    is passed the maze, the square and the heading and **not the player**, which
    is GHOST-4 enforced by the call rather than by good behaviour.

    Returns the final :class:`~terminalgame.domain.game_state.GameState`. If its
    outcome is still *playing*, the player quit part-way through.
    """
    # START-5 — the game is under way the moment the window opens: the picture
    # is up before anything is pressed, and the clock is already running.
    screen.present(compose(state))
    shown = state
    deadline = clock() + tick_seconds

    while True:
        # Caution C7. Every pass, from the clock, and never a fixed number.
        key = screen.read_key(max(0.0, deadline - clock()))

        if quits(key):
            return state

        direction = direction_of(key)
        if direction is not None:
            # No guard here on purpose: the Domain refuses this once the game
            # is over, and one enforcement is better than two.
            state = advance_player(state, direction)

        now = clock()
        if now >= deadline:
            if not state.is_over:
                # An optimisation, not a rule — see the module docstring.
                square, heading = ghost_move(
                    state.maze, state.ghost, state.ghost_heading, random_source)
                state = advance_ghost(state, square, heading)
            deadline = next_deadline(deadline, now, tick_seconds)

        if state is not shown:
            # SCRN-7 — the whole frame, in one pass, only when something moved.
            screen.present(compose(state))
            shown = state
