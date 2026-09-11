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
  returns the same state.* Both of them honour it, so the loop never grew
  the ``if`` it was written not to need.

The loop still paints on every turn even when nothing changed, which is what
the architecture's §6.2 sketch does. It costs 0.25 ms of a 143 ms tick, and
it is what makes END-5's "the last picture stays on screen" true by doing
rather than by not doing.

**WI-9 wired the real game in here.** WI-4 shipped this loop against
stand-ins, because the rules and the renderer had not landed yet, and it
looked the renderer up at run time rather than importing it. Both of those
are gone: :func:`run_game` now builds a real starting state with
:func:`termgame.rules.new_game` and drives the loop with
:func:`termgame.view.render`, :func:`termgame.rules.move_player` and
:func:`termgame.rules.move_ghost`. Nothing about :func:`run_loop` changed
when it did, which was the point of taking them as parameters — and the
``Terminal Game`` executable did not change either.
"""

import os
import random
import sys
import time
from typing import Callable

from termgame import controls, rules, screen as screen_module, ticker, view
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


# --------------------------------------------------------------------------
# The entry point the `Terminal Game` executable calls
# --------------------------------------------------------------------------


def run_game(open_screen=None, out=None) -> int:
    """Play one game, from a maze nobody has seen before. Returns the exit code.

    This is the whole of the wiring, and it is four names long: a fresh game
    from :func:`termgame.rules.new_game`, the picture from
    :func:`termgame.view.render`, and the two transitions from
    :mod:`termgame.rules`. There is no argument by which a different game
    could be asked for and no title screen to get past — the game is under
    way the moment the state exists (START-5).

    The random source is a bare ``random.Random()``, seeded by the operating
    system, so no two games are the same (MAZE-4). It is the *same* source
    the maze and the ghost both draw from, which is why a seeded
    :func:`termgame.rules.new_game` reproduces a whole game and an unseeded
    one never repeats.

    ``open_screen`` is the context manager that hands the loop a screen, and
    defaults to the curses adapter's :func:`termgame.screen.session`. A
    caller that supplies one has thereby said it has a screen. With neither a
    screen nor a controlling terminal there is no key to press, so rather
    than block forever in a window nobody could then close (plan §2.6, rule
    4) the game paints one frame as plain text on ``out`` and returns. That
    path is also how an agent — which has no tty at all — can see the picture
    the game would have drawn.

    It returns **only** after :func:`run_loop` returns, and :func:`run_loop`
    returns only on ``q`` (CTRL-4, END-6). Winning or losing does not end the
    process: the last picture stays on the screen until the player leaves
    (END-5), and the process exiting is what lets the supervisor close the
    window (WIN-5).
    """
    rng = random.Random()
    state = rules.new_game(rng)
    if open_screen is None and not _has_a_terminal():
        _write_plainly(view.render(state), stream=out)
        return 0
    opener = screen_module.session if open_screen is None else open_screen
    with opener() as scr:
        run_loop(
            scr,
            state,
            view.render,
            rules.move_player,
            rules.move_ghost,
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
