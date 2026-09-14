"""The game process: draw one frame, wait a moment, give the terminal back.

Run it with::

    python3 -m terminalgame.game_main

This is the M0 walking skeleton, not the game. Its whole job is to exercise
the screen port end to end in a real terminal — raw mode on, one whole frame
presented in one pass, a key read with a timeout, and the terminal handed
back however the process ends. WI-11 replaces the loop below with the real
one and WI-5b replaces the frame with the real picture; until then this is
what the launcher (WI-1, WI-3) has to open a window on.

It cannot block for ever. With no key at all it draws its frame, waits out
`--hold` seconds and exits by itself, so a window running it is never left
with a live process in it that nothing can end.
"""

from __future__ import annotations

import argparse
import sys
import time

from .screen.curses_adapter import TerminalSession
from .screen.port import Colour, Frame, ScreenTooSmall

#: How long the skeleton holds its frame on screen before exiting on its own.
DEFAULT_HOLD_SECONDS = 3.0

#: How long a single key read waits. The real loop (WI-11) recomputes this
#: every pass from the clock; the skeleton only needs it to be short enough
#: that `q` feels immediate and bounded enough that it always comes back.
KEY_POLL_SECONDS = 0.1

TITLE = "Terminal Game"
SKELETON_MESSAGE = "the screen port is alive"
STATUS_LINE = " score 0    arrows, q quits"

EXIT_OK = 0
EXIT_SCREEN_TOO_SMALL = 2


def build_skeleton_frame(width, height):
    """A placeholder picture that puts every named colour on the screen.

    Deliberately not the game's picture: WI-5b composes that from a game
    state, and nothing here should be mistaken for it. What this frame is
    for is showing a human, at a glance, that walls, dots, the player, the
    ghost and the status line all reach the glass in their own colours.
    """
    frame = Frame(width, height)
    maze_rows = height - 1
    right = width - 1

    frame.put_text(0, 0, "╔" + "═" * (right - 1) + "╗", Colour.WALL)
    for row in range(1, maze_rows - 1):
        frame.put(0, row, "║", Colour.WALL)
        frame.put(right, row, "║", Colour.WALL)
    frame.put_text(0, maze_rows - 1, "╚" + "═" * (right - 1) + "╝", Colour.WALL)

    _centre(frame, 2, TITLE, Colour.WALL)
    _centre(frame, 4, SKELETON_MESSAGE, Colour.DOT)

    dots_row = maze_rows // 2
    for column in range(4, right - 3, 2):
        frame.put(column, dots_row, "▪", Colour.DOT)

    _centre(frame, dots_row + 3, "▐█▌", Colour.PLAYER)
    _centre(frame, dots_row + 5, "▐▓▌", Colour.GHOST)
    _centre(frame, maze_rows - 3, "press q to quit", Colour.STATUS)

    frame.put_text(0, height - 1, STATUS_LINE[:width].ljust(width),
                   Colour.STATUS)
    return frame


def _centre(frame, row, text, colour):
    text = text[:frame.width]
    frame.put_text((frame.width - len(text)) // 2, row, text, colour)


def run(screen, hold_seconds=DEFAULT_HOLD_SECONDS, clock=time.monotonic):
    """Present one frame, then wait for `q` or for the hold to run out.

    Returns the key that ended it, or None if the hold expired.
    """
    width, height = screen.size()
    screen.present(build_skeleton_frame(width, height))

    deadline = clock() + hold_seconds
    while True:
        remaining = deadline - clock()
        if remaining <= 0:
            return None
        key = screen.read_key(min(remaining, KEY_POLL_SECONDS))
        if key is not None and key.is_printable and key.character in ("q", "Q"):
            return key


def main(argv=None, session_factory=TerminalSession, stderr=None):
    arguments = _parse_arguments(argv)
    stderr = stderr if stderr is not None else sys.stderr
    try:
        with session_factory() as screen:
            run(screen, hold_seconds=arguments.hold)
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
        description="Draw one frame through the screen port and quit.")
    parser.add_argument(
        "--hold", type=float, default=DEFAULT_HOLD_SECONDS,
        help="seconds to hold the frame before exiting on its own "
             "(default: %(default)s). Never unbounded.")
    arguments = parser.parse_args(argv)
    if arguments.hold < 0:
        parser.error("--hold cannot be negative")
    return arguments


if __name__ == "__main__":
    sys.exit(main())
