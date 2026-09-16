# -*- coding: utf-8 -*-
"""WI-13 — row 29, and nothing else on that row ever.

The bottom row of the window shows the score and the keys that can be used
(STAT-1), in cyan (SCRN-6), and it says which of the two endings happened
once one has (STAT-3).  This module produces that row **as a value**: the
frame composer (WI-12) places what it is handed here and writes nothing on
row 29 itself.

**This module is the only place in the project where a status-line literal
lives.**  The implementation plan confines assumption A7 to this work item,
with an explicit prohibition on any other work item — and any other
developer's tests — containing one.  If the user rules differently on either
contradiction below, the change is the three templates here and the tests in
``tests/test_status_line.py``.  One place, not a hunt across three lanes.

Two contradictions in the specification land here, and both are resolved
under **assumption A7**, which is an assumption and not a ruling:

* **C-3 — STAT-2's literal disagrees with the specimen picture by one
  leading space.**  STAT-2 gives ``score 0    arrows, q quits``, 26
  characters with no leading space; row 29 of the specimen picture is
  ``' score 0    arrows, q quits'``, 27 characters with one.  A7 takes the
  **STAT-2 literal** as normative and the picture's leading space as
  illustrative, so the text starts at column 0.

* **C-4 — STAT-3's two examples cannot come from one alignment rule.**
  ``CAUGHT  score 37   q quits`` puts ``q quits`` at column 19;
  ``CLEARED  score 274  q quits`` puts it at column 20.  No single padding
  rule produces both.  A7 takes them as **two per-ending templates**, each
  reproducing its own example exactly with the score substituted — so the
  line grows and shrinks with the number of digits in the score rather than
  holding a column.

One measurement worth knowing while reading STAT-3's second example: a whole
game is worth **259 to 271 points** (``docs/findings/WI-6-start-squares.md``,
measured over 200 mazes).  **A score of 274 is therefore illustrative and not
reachable in play.**  It is still reproduced character for character here,
because the specification's literal is what A7 makes normative; it is simply
not a number a player will ever see.

This module **selects by** the outcome vocabulary and does not define it:
:class:`~terminal_game.domain.game_state.Outcome` is the Domain's, landed in
WI-6.  There are three members and so there are three templates; a fourth
ending would fail here loudly rather than quietly reading as "playing".

It imports nothing but the standard library and names no toolkit.
"""

from __future__ import annotations

from typing import Tuple

from ..domain.game_state import Outcome
from .frame import FRAME_COLUMNS, STATUS_ROW, Cell, Colour

__all__ = [
    "STATUS_ROW",
    "STATUS_COLOUR",
    "PLAYING_TEMPLATE",
    "CAUGHT_TEMPLATE",
    "CLEARED_TEMPLATE",
    "status_text",
    "status_row",
]


#: SCRN-6 — the status line is written in cyan, and so is the rest of its row.
#:
#: The cells past the text hold a space, and the surface never paints a
#: space, so no pixel differs between a cyan blank and a black one.  Making
#: the whole row one colour is what lets STAT-1 — *"the bottom row shows the
#: score and the keys, and nothing else"* — be asserted as a single property
#: of the row rather than of a prefix of it.
STATUS_COLOUR = Colour.STATUS_CYAN


#: STAT-2, verbatim, with the score substituted.  With ``score=0`` this is
#: the specification's literal character for character.
PLAYING_TEMPLATE = "score {score}    arrows, q quits"

#: STAT-3's loss example, verbatim.  With ``score=37``: the literal exactly.
CAUGHT_TEMPLATE = "CAUGHT  score {score}   q quits"

#: STAT-3's win example, verbatim.  With ``score=274``: the literal exactly.
#: Note the spacing differs from :data:`CAUGHT_TEMPLATE` — that is C-4, and
#: it is deliberate rather than a typo.
CLEARED_TEMPLATE = "CLEARED  score {score}  q quits"


#: Which template each ending uses.  Every member of :class:`Outcome` appears
#: exactly once: there is no third ending and no default branch, so an
#: outcome this module has not been taught about raises instead of silently
#: being drawn as one that it has.
_TEMPLATES = {
    Outcome.UNDECIDED: PLAYING_TEMPLATE,
    Outcome.CAUGHT: CAUGHT_TEMPLATE,
    Outcome.CLEARED: CLEARED_TEMPLATE,
}


def status_text(score: int, outcome: Outcome) -> str:
    """The status line for *score* and *outcome*, as plain text.

    The string is the template for that outcome with the score substituted,
    and nothing else: no padding, no leading space, no truncation.  It is
    always short enough to fit a 40-column row for any score a game can
    reach — the longest template is 24 characters plus the digits.

    A score that is not a whole number, or is negative, is refused: the score
    reaching a status line wrong is the sort of defect that shows up as a
    picture that is nearly right.
    """
    if isinstance(score, bool) or not isinstance(score, int):
        raise TypeError(
            "the score on a status line is a whole number, not {0!r}".format(
                score
            )
        )
    if score < 0:
        raise ValueError(
            "a score can never be negative, got {0:d}".format(score)
        )
    if not isinstance(outcome, Outcome):
        raise ValueError(
            "{0!r} is not one of the {1} outcomes ({2})".format(
                outcome,
                len(Outcome),
                ", ".join(member.name for member in Outcome),
            )
        )
    return _TEMPLATES[outcome].format(score=score)


def status_row(score: int, outcome: Outcome) -> Tuple[Cell, ...]:
    """Row 29 as 40 cells, ready for ``FrameBuilder.place_row``.

    The text sits at column 0 (C-3, assumption A7) and the rest of the row is
    blank.  Every cell is cyan, including the blank ones: row 29 carries the
    status line and nothing else, in one colour (STAT-1, SCRN-6).

    A line too long for the row raises rather than being cut short — a
    truncated status line would still look plausible on screen, which is
    exactly what makes silently trimming it the wrong thing to do.
    """
    text = status_text(score, outcome)
    if len(text) > FRAME_COLUMNS:
        raise ValueError(
            "the status line {0!r} is {1} characters, more than the {2} "
            "columns of a row".format(text, len(text), FRAME_COLUMNS)
        )
    padded = text.ljust(FRAME_COLUMNS)
    return tuple(Cell(character, STATUS_COLOUR) for character in padded)
