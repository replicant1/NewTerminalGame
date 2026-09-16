"""The game process: a whole game, in the window the launcher opened.

Run it with::

    python3 -m terminalgame.game_main

This is the assembly point and almost nothing else. Every part it puts together
was built and tested somewhere else, and this module's whole job is to hand each
one to the next:

* the **Domain** makes a maze and opens a game on it (WI-4, WI-7);
* **Presentation** turns a state into a frame (WI-5a, WI-5b) and writes the
  status row (WI-6);
* the **screen port** puts that frame on the glass and reads keys (WI-2);
* the **loop** decides when each of those happens (WI-11).

It was the M0 skeleton until now — one frame, a `--hold` timer, and no game
underneath it. Both are gone. The real game runs until the player presses `q`,
which is END-6, and the window closing afterwards is the launcher's doing.

## One seed names one whole game

A single `random.Random` is built from `--seed` and handed **both** to
`new_game_with`, which uses it for the maze and for the opening positions, and
to the loop, which uses it for the ghost. That matters more than it looks: with
two sources a seed would reproduce the maze but not the game played on it, and
reproducing a whole game is precisely what the smoke test needs.

With no seed the game is different every time, which is MAZE-4.

## The status row is passed explicitly, and that is not a formality

`compose(state, status_line=None)` leaves row 29 blank, and a frame with a blank
row 29 is a perfectly well-formed frame — it composes without complaint and
satisfies every test the frame builder has. So forgetting to pass the status row
here would not break anything loudly; it would produce a game that quietly fails
STAT-1 while looking entirely correct to every automated check above it. That is
why :func:`build_frame` exists as a named function with a test of its own,
rather than as an argument written inline at the call site.
"""

from __future__ import annotations

import argparse
import random
import sys

from .application.loop import play
from .domain.game_state import new_game_with
from .presentation.frame_builder import compose
from .presentation.status_line import status_row
from .screen.curses_adapter import TerminalSession
from .screen.port import ScreenTooSmall

EXIT_OK = 0
EXIT_SCREEN_TOO_SMALL = 2


def build_frame(state):
    """The real picture: the composed maze with the real status row on it.

    The one line that joins WI-5b to WI-6. See the module docstring for why it
    is a function with a name rather than an argument at the call site.
    """
    return compose(state, status_line=status_row(state))


def play_a_game(screen, seed=None):
    """Open a game and play it until the player quits. Returns the last state.

    Separated from :func:`main` so that a test can play a whole game against a
    stood-in screen without going near a terminal, an argument parser or an
    exit code.
    """
    random_source = random.Random(seed)
    state = new_game_with(random_source)
    return play(screen, state, random_source, build_frame)


def main(argv=None, session_factory=TerminalSession, stderr=None):
    arguments = _parse_arguments(argv)
    stderr = stderr if stderr is not None else sys.stderr
    try:
        with session_factory() as screen:
            play_a_game(screen, seed=arguments.seed)
    except ScreenTooSmall as too_small:
        # Loud, and after the terminal has been given back, so the message is
        # readable rather than scrawled across a curses screen.
        stderr.write(str(too_small) + "\n")
        stderr.flush()
        return EXIT_SCREEN_TOO_SMALL
    return EXIT_OK


def _parse_arguments(argv):
    parser = argparse.ArgumentParser(
        prog="terminalgame.game_main",
        description="Play a game of Terminal Game in this window.")
    parser.add_argument(
        "--seed", type=int, default=None,
        help="play a reproducible game: the same seed gives the same maze, "
             "the same opening position and the same ghost. Omit it for a "
             "fresh game every time.")
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
