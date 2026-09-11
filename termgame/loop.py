"""The game loop, and the one deadline the game has.

IMPURE — it reads a clock — but only just. Every *decision* it makes has been
pulled out into a pure module: what a key means is
:func:`termgame.controls.command_for_key`, when the ghost is due is
:mod:`termgame.ticker`, and what the picture looks like is the renderer's.
What is left is the shape of the loop itself, and that shape is the whole of
five requirements, so :func:`run_loop` takes its screen, its clock and its
transitions **as parameters** and is driven in the tests by a fake screen and
a fake clock. (Implementation plan §10.1.)

The shape::

    paint(render(state))                       # before the first read: START-5
    loop:
        key = screen.read_key(time until the deadline)
        quit  -> return                        # CTRL-4, END-6
        arrow -> one player transition         # CTRL-1, CTRL-2
        anything else -> nothing               # CTRL-5
        deadline passed -> one ghost transition, deadline += one tick  # GHOST-1
        paint(render(state))                   # SCRN-7

Four properties fall out of that and are worth naming, because each of them is
a requirement that would otherwise need machinery:

* **CTRL-2** — one square per key press, no drift. The loop holds no
  "currently heading" field for a key to set, so there is nothing to repeat.
  One key event, one transition.
* **GHOST-1** — the ghost moves whether or not the player is moving.
  ``getch`` with a timeout returns *as soon as* a key arrives, so a key is
  answered at keypress latency, and the deadline it did not reach is still
  the same deadline on the next turn.
* **No second clock** (architecture C4). One thread, one deadline, no
  ``threading``, no ``asyncio``, no signal handler.
* **END-5** — after the game ends, nothing changes. The loop does **not**
  test the outcome; it calls the transitions as usual and they decline. That
  is what keeps game logic out of the shell, and it is a requirement on
  whatever WI-6 and WI-7 land: *a transition applied to a finished game
  returns the same state.*

The loop still paints on every turn even when nothing changed, which is what
the architecture's §6.2 sketch does. It costs 0.25 ms of a 143 ms tick, and
it is what makes END-5's "the last picture stays on screen" true by doing
rather than by not doing.
"""

import importlib
import os
import random
import sys
import time
from typing import Callable, Optional

from termgame import controls, screen as screen_module, standins, ticker
from termgame.model import Frame, GameState

#: The clock. Monotonic, because the game must not care what the wall clock
#: does while it is running.
MONOTONIC = time.monotonic


def run_loop(
    screen,
    state: GameState,
    render: Callable[[GameState], Frame],
    move_player: Callable[[GameState, object], GameState],
    move_ghost: Callable[[GameState, random.Random], GameState],
    rng: random.Random,
    clock: Callable[[], float] = MONOTONIC,
    tick: float = ticker.GHOST_TICK_SECONDS,
) -> GameState:
    """Play until the player quits, and return the state it ended on.

    ``screen`` needs only two methods — ``paint(frame)`` and
    ``read_key(timeout_ms)`` — so a fake screen is four lines. ``clock`` is a
    callable returning seconds; a fake clock is three.

    Returns **only** when a quit key is pressed (CTRL-4, END-6). A game that
    has been won or lost does not return: the last picture stays on the screen
    and `q` is the only way out of it (END-5).
    """
    deadline = ticker.first_deadline(clock(), tick)
    screen.paint(render(state))  # START-5: painted before the first key read
    while True:
        key = screen.read_key(ticker.wait_milliseconds(clock(), deadline))
        command = controls.command_for_key(key)
        if controls.is_quit(command):
            return state
        direction = controls.as_direction(command)
        if direction is not None:
            state = move_player(state, direction)
        if ticker.is_due(clock(), deadline):
            state = move_ghost(state, rng)
            deadline = ticker.advanced(deadline, tick)
        screen.paint(render(state))


def resolve_render(
    module_lookup: Optional[Callable[[str], object]] = None
) -> Callable[[GameState], Frame]:
    """The renderer to draw with: WI-3's if it has landed, else the stand-in.

    WI-3 and WI-4 were built in parallel against a picture type that was
    already merged, so this module cannot import the real renderer at the
    moment it is written. Looking it up at run time rather than importing it
    means the real picture appears the moment WI-3 is merged, with no change
    here — and WI-9 replaces the whole of this with a plain import.
    """
    lookup = importlib.import_module if module_lookup is None else module_lookup
    try:
        view = lookup("termgame.view")
    except ImportError:
        return standins.render
    render = getattr(view, "render", None)
    return render if callable(render) else standins.render


# --------------------------------------------------------------------------
# The entry point the `Terminal Game` executable calls
# --------------------------------------------------------------------------


def run_game() -> int:
    """Play one game. Returns the process exit code.

    The starting state and the two transitions are stand-ins from
    :mod:`termgame.standins`; **WI-9 deletes them** and puts the real ones
    here. Nothing about the loop changes when it does, which is the point.

    With no controlling terminal there is no key to press, so rather than
    block forever in a window nobody could then close (plan §2.6, rule 4) the
    game paints one frame as plain text and returns. That path is also how an
    agent — which has no tty at all — can see the picture the game would draw.
    """
    rng = random.Random()
    state = standins.new_game(rng)
    render = resolve_render()
    if not _has_a_terminal():
        _write_plainly(render(state))
        return 0
    with screen_module.session() as scr:
        run_loop(
            scr,
            state,
            render,
            standins.move_player,
            standins.move_ghost,
            rng,
        )
    return 0


def _has_a_terminal(stream=None) -> bool:
    stream = sys.stdin if stream is None else stream
    try:
        return os.isatty(stream.fileno())
    except (AttributeError, ValueError, OSError):
        return False


def _write_plainly(frame: Frame, stream=None) -> None:
    """Write a picture as plain text — no curses, no cursor addressing.

    Used only when there is no terminal. Every row is written whole and the
    rows are newline-separated, so nothing is ever written to the last cell of
    the last row of a real screen (architecture C1).
    """
    stream = sys.stdout if stream is None else stream
    stream.write("\n".join(frame.rows()))
    stream.write("\n")
    stream.flush()
