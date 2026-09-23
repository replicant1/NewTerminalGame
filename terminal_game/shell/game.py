"""The game, assembled: the one entry point that runs a whole session in the real window.

``python -m terminal_game`` calls :func:`main`, which

1. finds the anchor (the window that was frontmost at start-up) and the
   displays' visible areas, *before* the game's own window exists (WI-9);
2. makes a fresh random source and a new session from it: a fresh maze, the
   player, the ghost and the dots (WI-2, WI-7, WI-12); the same source then
   drives the ghost;
3. builds the window (WI-3), places it beside the anchor (WI-9) and paints the
   first picture;
4. runs: each key press is translated (WI-6) and handed to the session, each
   tick moves the ghost, and after every event the state is composed (WI-10)
   and painted, until the session has ended, when the window closes itself
   and the process exits 0.

The shell asks the session for its state after each event and composes it;
the application never calls upward (IMPLEMENTATION_PLAN.md §1.4, X2).

:func:`play` is the same loop for a session and window someone else made. The
desktop tests use it to play a fixed-seed game to a win and to a loss.
"""

import random
import sys
from collections.abc import Sequence

from terminal_game.application.session import Session
from terminal_game.presentation.frame_composer import compose
from terminal_game.presentation.input_translation import translate
from terminal_game.shell.anchor import find_anchor, visible_displays
from terminal_game.shell.placement import Rect, place
from terminal_game.shell.window import GameWindow

#: The title bar macOS 26 puts on the window, in points (measured for WI-3):
#: placement works on the window's outer size.
TITLE_BAR_POINTS = 32


def play(session: Session, window: GameWindow, anchor: Rect | None = None,
         displays: Sequence[Rect] = ()) -> int:
    """Place ``window``, paint ``session``'s first picture, and run the session to its end.

    Returns the window's exit status (0 when the session ends on quit or the
    window is closed; 1 when a handler failed).
    """
    if displays:
        width, height = window.size
        window.place(*place(anchor, (width, height + TITLE_BAR_POINTS), displays))

    def after_event() -> None:
        if session.ended:
            window.close()
        else:
            window.paint(compose(session.state))

    def on_key(name: str) -> None:
        session.handle(translate(name))
        after_event()

    def on_tick() -> None:
        session.tick()
        after_event()

    window.paint(compose(session.state))
    return window.run(on_key, on_tick)


def main() -> int:
    """Start a fresh game beside the window that was in front, and play it until ``q``."""
    anchor = find_anchor()
    displays = visible_displays()
    session = Session.new(random.Random())   # seeded from the operating system: a fresh maze each run
    return play(session, GameWindow(), anchor, displays)


if __name__ == "__main__":
    sys.exit(main())
