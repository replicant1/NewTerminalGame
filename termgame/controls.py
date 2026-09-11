"""The key decision — a pure function of a key code.

PURE. This module imports nothing impure and in particular does not import
``curses``: it is the whole reason CTRL-1, CTRL-2, CTRL-4 and CTRL-5 can be
tested with no terminal attached.

The architecture (§8) calls the curses adapter and the loop "not unit-tested",
and then (§10) traces five requirements to them with "unit" as the check. The
implementation plan rules on that contradiction in its §10.1: the two
*decisions* in that layer — which command a key code means, and when the
ghost's tick is due — are pulled out here and in :mod:`termgame.ticker`, so
what is left in the adapter is only the call into ncurses.

The key codes are ncurses' own, recorded here as integers so that nothing in
the core has to import ``curses`` to speak about them. That they really are
ncurses' values is asserted by the adapter's tests, which may import curses.

    >>> command_for_key(259) is UP
    True
    >>> command_for_key(ord("Q")) is QUIT
    True
    >>> command_for_key(ord("x")) is None
    True
"""

import enum
from typing import Dict, FrozenSet, Optional, Union

from termgame.model import DOWN, LEFT, RIGHT, UP, Direction

# --------------------------------------------------------------------------
# The key codes ncurses reports
# --------------------------------------------------------------------------

#: ``curses.KEY_DOWN``.
KEY_DOWN = 258
#: ``curses.KEY_UP``.
KEY_UP = 259
#: ``curses.KEY_LEFT``.
KEY_LEFT = 260
#: ``curses.KEY_RIGHT``.
KEY_RIGHT = 261
#: ``curses.KEY_RESIZE`` — the window changed size. The game does nothing
#: about it: the window is a fixed 40 x 30 (WIN-2).
KEY_RESIZE = 410

#: ``curses.ERR`` — ``getch`` timed out with nothing to report.
NO_KEY = -1


# --------------------------------------------------------------------------
# The commands a key can mean
# --------------------------------------------------------------------------


class Command(enum.Enum):
    """A command that is not a direction. There is exactly one (CTRL-4)."""

    QUIT = "QUIT"


#: Leave the game at once, at any point, finished or not (CTRL-4, END-6).
QUIT = Command.QUIT

#: The arrow keys, and nothing else, are directions (CTRL-1).
ARROW_KEYS: Dict[int, Direction] = {
    KEY_UP: UP,
    KEY_DOWN: DOWN,
    KEY_LEFT: LEFT,
    KEY_RIGHT: RIGHT,
}

#: ``q`` in either case quits (CTRL-4).
QUIT_KEYS: FrozenSet[int] = frozenset({ord("q"), ord("Q")})

#: What a decided key can be: a direction, the quit command, or nothing.
Decision = Optional[Union[Direction, Command]]


def command_for_key(key: Optional[int]) -> Decision:
    """What ``key`` means: a :class:`~termgame.model.Direction`, :data:`QUIT`,
    or ``None``.

    ``None`` covers three cases that the loop treats identically: no key was
    ready before the timeout (:data:`NO_KEY`), the adapter reported nothing at
    all, and **every other key on the keyboard** (CTRL-5). Total: there is no
    key code for which this raises.
    """
    if key is None:
        return None
    if isinstance(key, bool) or not isinstance(key, int):
        # A `bool` is an `int` in Python and `True == 1`; neither a bool nor a
        # string from `getkey()` is a key code, and neither means anything.
        return None
    direction = ARROW_KEYS.get(key)
    if direction is not None:
        return direction
    if key in QUIT_KEYS:
        return QUIT
    return None


def is_quit(command: Decision) -> bool:
    """Whether a decided command is the one that leaves the game."""
    return command is QUIT


def as_direction(command: Decision) -> Optional[Direction]:
    """The direction a decided command carries, or ``None`` if it carries none.

    This exists so the loop needs no ``isinstance`` of its own: nothing about
    what a key means lives outside this module.
    """
    return command if isinstance(command, Direction) else None
