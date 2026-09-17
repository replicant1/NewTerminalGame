"""Key presses in, intents out — CTRL-1, CTRL-4, CTRL-5.

The whole of this module is one lookup, and that is the point.  Deciding what
a key *means* is a rule; delivering the key press is the toolkit's job and
acting on the meaning is the session's.  Keeping the rule on its own makes it
testable without a window, without a clock and without a game.

**What arrives here is a keysym** — the name Tk puts in ``event.keysym``:
``"Up"``, ``"q"``, ``"F1"``, ``"Shift_L"``.  Not a binding name, not a
character, not a key code.

**And it is read strictly.**  ``"<Key-Up>"`` is a binding name rather than a
keysym and means nothing here; neither does ``"up"``.  Being lenient about
either would turn a wiring mistake into a silent one, and the wiring mistake
worth worrying about is precisely the one where the arrows quietly stop
working.

**The intended wiring is one binding.**  A shell that binds ``<Key>`` once and
calls :func:`intent_for` with ``event.keysym`` needs no list of keys from here
and cannot fall out of step with this module when the list changes::

    root.bind("<Key>", lambda event: handle(intent_for(event.keysym)))

**Nothing here names the toolkit**, which the Presentation layer's rule
requires in any case: only the painting surface may do that.  So this module
knows Tk's vocabulary without depending on Tk, and ``tests/test_keys.py``
checks that vocabulary against a real Tk rather than trusting it.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, Optional, Tuple

from terminal_game.application.turn import Intent

#: CTRL-1: *"the four arrow keys move the player one square up, down, left or
#: right."*  Up is north, and north is towards row zero — the maze's ``y``
#: increases down the screen, so the screen's "up" and the grid's "north" are
#: the same direction under two names.
ARROW_INTENTS = {
    "Up": Intent.MOVE_NORTH,
    "Down": Intent.MOVE_SOUTH,
    "Left": Intent.MOVE_WEST,
    "Right": Intent.MOVE_EAST,
}  # type: Dict[str, Intent]

#: CTRL-4: *"pressing ``q`` (upper or lower case) quits at once."*  Two
#: separate keysyms rather than one case-folded comparison, because Tk reports
#: the shifted and unshifted keys under different names and folding would also
#: swallow anything else that happened to fold onto them.
QUIT_KEYSYMS = frozenset({"q", "Q"})  # type: FrozenSet[str]

_INTENTS = dict(ARROW_INTENTS)
_INTENTS.update({keysym: Intent.QUIT for keysym in QUIT_KEYSYMS})

#: Every keysym that means anything.  Six: four arrows and two cases of ``q``.
#: Exported so that a test can check them against the toolkit's own vocabulary
#: and so nobody has to re-derive the list; the wiring does not need it.
TRANSLATED_KEYSYMS = tuple(sorted(_INTENTS))  # type: Tuple[str, ...]


def intent_for(keysym: str) -> Optional[Intent]:
    """What a key press means, or ``None`` if it means nothing.

    :param keysym: the ``event.keysym`` of a Tk key event.
    :returns: the :class:`~terminal_game.application.turn.Intent` the key
        stands for, or ``None``.

    **CTRL-5 is the ``None``**: *"no other key does anything, and nothing
    typed is echoed into the maze."*  A key with no meaning is discarded here
    and silently — this function has no side effect of any kind, writes
    nothing anywhere, and keeps no record of what it was asked about.  There
    is nowhere for a stray keystroke to end up.

    Returning ``None`` rather than an ``Intent.IGNORE`` is deliberate: an
    intent for doing nothing is a thing a caller can forget to check, whereas
    ``None`` is the one value every caller already has to handle.
    """
    return _INTENTS.get(keysym)
