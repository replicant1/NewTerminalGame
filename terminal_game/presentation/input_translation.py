"""From the shell's key names to the game's intents.  (CTRL-1, CTRL-4, CTRL-5)

The shell hands over Tk's name for each key pressed (its *keysym*): ``"Up"``,
``"Down"``, ``"Left"``, ``"Right"``, ``"q"``, ``"Q"``, and any other key by its
own name (``"a"``, ``"space"``, ``"Return"``, ``"F1"``, ``"Shift_L"`` ...).
Four arrows become moves, ``q`` and ``Q`` become quit, and every other key
becomes nothing.  ``Q`` covers ``q`` typed with Caps Lock on or with Shift.

The intents are plain strings, so the application layer, which may not import
from presentation, can compare against them without importing anything.

Pure.
"""

from __future__ import annotations

from typing import Optional

MOVE_UP = "up"
MOVE_DOWN = "down"
MOVE_LEFT = "left"
MOVE_RIGHT = "right"
QUIT = "quit"
#: What every other key translates to.
NOTHING = None  # type: Optional[str]

INTENTS = (MOVE_UP, MOVE_DOWN, MOVE_LEFT, MOVE_RIGHT, QUIT)

_KEYS = {
    "Up": MOVE_UP,
    "Down": MOVE_DOWN,
    "Left": MOVE_LEFT,
    "Right": MOVE_RIGHT,
    "q": QUIT,
    "Q": QUIT,
}


def translate(key_name: str) -> Optional[str]:
    """The intent for a key name: a move, quit, or :data:`NOTHING`."""
    if not isinstance(key_name, str):
        return NOTHING
    return _KEYS.get(key_name, NOTHING)
