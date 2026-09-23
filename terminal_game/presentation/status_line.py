"""The bottom row of the window: the score, the keys, and on an ending which one.

STAT-1 to STAT-3, SCRN-6.  The text follows the specimen exactly, one leading
blank included (IMPLEMENTATION_PLAN.md section 1.8, Q4):

    during play   " score 0    arrows, q quits"
    on a loss     " CAUGHT  score 37   q quits"
    on a win      " CLEARED  score 274  q quits"

The score is left-aligned in a fixed field, so the text after it starts in the
same cell whatever the score: cell 12 during play, 20 on a loss, 21 on a win,
as in those three examples.  The row is padded with blanks to 40 cells and every
cell is in the status colour.

Pure.  The outcome is given as :data:`PLAYING`, :data:`LOST` or :data:`WON`.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from terminal_game.presentation.roles import STATUS

WIDTH = 40

PLAYING = None  # type: Optional[str]
LOST = "lost"
WON = "won"

# outcome -> (text before the score, the cell the text after it starts in, that text)
_FORMS = {
    PLAYING: (" score ", 12, "arrows, q quits"),
    LOST: (" CAUGHT  score ", 20, "q quits"),
    WON: (" CLEARED  score ", 21, "q quits"),
}


def status_text(score: int, outcome: Optional[str] = PLAYING) -> str:
    """The 40 characters of the status row."""
    try:
        before, tail_cell, tail = _FORMS[outcome]
    except KeyError:
        raise ValueError("unknown outcome %r; expected PLAYING (None), %r or %r"
                         % (outcome, LOST, WON)) from None
    if isinstance(score, bool) or not isinstance(score, int) or score < 0:
        raise ValueError("the score is a whole number, 0 or more, not %r" % (score,))
    digits = str(score)
    field = tail_cell - len(before)
    if len(digits) >= field:
        raise ValueError("a score of %d does not fit before cell %d" % (score, tail_cell))
    return (before + digits.ljust(field) + tail).ljust(WIDTH)


def status_row(score: int, outcome: Optional[str] = PLAYING) -> List[Tuple[str, str]]:
    """The status row as 40 ``(character, role)`` cells, all in the status colour."""
    return [(character, STATUS) for character in status_text(score, outcome)]
