# -*- coding: utf-8 -*-
"""WI-9 — the input translator: raw key events become intents.

Four arrow keys become Move in a direction; ``q`` and ``Q`` become Quit;
**every other key is discarded** (CTRL-1, CTRL-4, CTRL-5).

**The intent vocabulary lives here** — :class:`Intent`, :class:`IntentKind`,
:data:`QUIT` and :func:`move`.  WI-15's session controller consumes it; it
should not define a second one.

**The direction vocabulary does not live here.**  It is
:class:`terminal_game.domain.maze.Direction`, which landed with WI-5 on day
one; WI-7's ghost policy conforms to it and so does this module.  Anything
that needs a direction uses that one.  ``NORTH`` decreases the row, so it is
up the screen, which is what the up arrow means.

Layer
-----
Presentation.  It may name Application and Domain, and it **may not name the
Shell**.  So it does not import the Shell's ``KeyPress``: :func:`translate`
takes the two plain strings that value carries, and the Shell's key handler —
which is the caller — unpacks it:

    intent = translate(key.keysym, key.char)

Nothing is echoed anywhere
--------------------------
CTRL-5 is half "no other key does anything" and half "nothing typed is echoed
into the maze".  This module satisfies the second half by having no way to
emit anything at all: it prints nothing, logs nothing, writes to no stream and
touches no frame.  A key it does not recognise produces ``None`` and no other
effect whatsoever.  **Do not add logging here**, however tempting a debug line
looks — the whole of this module's contribution to CTRL-5 is that it is
incapable of output.

What it can and cannot see
--------------------------
A key reaches this module as a *keysym* (the toolkit's name for the key) and
the *character* it typed, and nothing else — there is no modifier state on the
value that crosses the seam.  So:

* A modified **letter** is correctly rejected.  Plain ``q`` arrives as
  ``("q", "q")``; control-Q arrives with a control character rather than
  ``"q"``, so it does not quit.  That is why :func:`translate` insists on the
  character as well as the keysym for the quit keys.
* A modified **arrow** cannot be told from a plain one, because an arrow types
  no character either way.  Control-Up is therefore treated as Up.  Making
  that distinction would need the modifier state added to the Shell's key
  value, which is WI-3's to decide; see this item's PR.
"""

from __future__ import annotations

import enum
from typing import Dict, FrozenSet, NamedTuple, Optional

from terminal_game.domain.maze import Direction

__all__ = [
    "IntentKind",
    "Intent",
    "QUIT",
    "move",
    "translate",
    "ARROW_KEYS",
    "QUIT_KEYS",
]


class IntentKind(enum.Enum):
    """What the player asked for.  There are two, and GAME-3 says no more.

    No pause, no restart, no level select: the specification rules all of
    them out in as many words, so there is nowhere for one to be added by
    accident.
    """

    MOVE = "move"
    QUIT = "quit"


class Intent(NamedTuple):
    """One thing the player asked for.

    A value, so a test asserts what was asked for by comparing rather than by
    inspecting.  ``direction`` is set for a Move and ``None`` for a Quit.
    """

    kind: IntentKind
    direction: Optional[Direction] = None


#: CTRL-4.  There is one Quit and it is the same object every time.
QUIT = Intent(IntentKind.QUIT, None)


def move(direction: Direction) -> Intent:
    """A Move intent in *direction* (CTRL-1)."""
    if not isinstance(direction, Direction):
        raise ValueError(
            "{0!r} is not one of the four directions".format(direction)
        )
    return Intent(IntentKind.MOVE, direction)


#: CTRL-1.  The toolkit's names for the four arrow keys, and what each means.
#: ``NORTH`` decreases the row, so the up arrow is ``NORTH``.
ARROW_KEYS: Dict[str, Direction] = {
    "Up": Direction.NORTH,
    "Down": Direction.SOUTH,
    "Left": Direction.WEST,
    "Right": Direction.EAST,
}

#: CTRL-4.  Upper or lower case, and nothing else.
QUIT_KEYS: FrozenSet[str] = frozenset({"q", "Q"})


def translate(keysym: str, char: str) -> Optional[Intent]:
    """Turn one key press into an intent, or into nothing at all.

    *keysym* is the toolkit's name for the key — ``"Up"``, ``"q"``,
    ``"Escape"`` — and *char* is the character it typed, empty for keys that
    type none.  Both are required: defaulting *char* would quietly turn a
    caller that forgot it into one whose quit key had stopped working.

    Returns an :class:`Intent`, or ``None`` for every key that is not one of
    the six the game responds to (CTRL-5).  It raises nothing, prints nothing
    and changes nothing.
    """
    if not isinstance(keysym, str) or not isinstance(char, str):
        return None

    direction = ARROW_KEYS.get(keysym)
    if direction is not None:
        return Intent(IntentKind.MOVE, direction)

    # The character has to agree, so that control-Q and friends — which keep
    # the keysym but type a control character — are discarded like any other
    # unmapped key.
    if keysym in QUIT_KEYS and char in QUIT_KEYS:
        return QUIT

    return None
