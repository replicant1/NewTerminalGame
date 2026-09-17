"""Row 29 — STAT-1, STAT-2, STAT-3 and SCRN-6.

    *"The bottom row of the window shows the score and the keys that can be
    used, and nothing else."* (STAT-1)

    *"During play it reads ``score 0    arrows, q quits``, with the score kept
    up to date."* (STAT-2)

    *"On a loss it reads ``CAUGHT  score 37   q quits``; on a win,
    ``CLEARED  score 274  q quits``."* (STAT-3)

    *"The status line is written in cyan."* (SCRN-6)

**The content of row 29 is decided here and nowhere else.**  This module
produces the whole row as a string; the frame composer writes it with
:meth:`~terminal_game.presentation.field.Field.write` and decides nothing
about it.  That split is deliberate: a status line composed partly here and
partly in the composer is a status line nobody owns.

The leading space
-----------------

Ruling **C-4** takes the specimen picture as normative, and the specimen's
bottom row carries a leading space that STAT-2's prose does not.  Measured
from ``docs/FUNCTIONAL_REQUIREMENTS.md`` rather than taken on trust: the row
is ``' score 0    arrows, q quits'`` — 27 characters, one leading space, and
exactly ``" " + <the STAT-2 literal>``.

The spacing, which turns out to have a rule after all
-----------------------------------------------------

C-4 says the three literals "pad differently from one another … so there is no
column discipline to infer".  **There is one, and the specification's own three
examples determine it uniquely: the score sits left-aligned in a field of
:data:`SCORE_FIELD_WIDTH` characters.**

=========================  ===============================  ==============
Form                       Built as                         Printed as
=========================  ===============================  ==============
playing, score 0           ``score `` + ``0    ``           ``score 0    arrows, q quits``
caught, score 37           ``CAUGHT  score `` + ``37   ``   ``CAUGHT  score 37   q quits``
cleared, score 274         ``CLEARED  score `` + ``274  ``  ``CLEARED  score 274  q quits``
=========================  ===============================  ==============

Width 5 reproduces all three verbatim.  **Width 4 and width 6 reproduce
none.**  The apparently inconsistent gap — ``q quits`` starting at column 19
in the caught form and column 20 in the cleared form — comes entirely from
``CAUGHT`` being one character shorter than ``CLEARED``, not from the padding.

The alternative reading, fixed separators copied out of each example, also
reproduces all three, because they differ only at score widths the
specification does not print.  The field was chosen because **STAT-2 says the
score is kept up to date**: with a fixed separator, ``arrows, q quits`` slides
right every time the score crosses a power of ten, and the player watches it
happen.  With the field it stays at column 12 for every score from 0 to the
551 corridor squares a 19 x 29 grid can hold.  If the literal reading is
preferred, it is this one constant and the tests that quote it.
"""

from __future__ import annotations

from typing import Tuple

from terminal_game.application.turn import outcome_of
from terminal_game.domain.state import GameState, Outcome
from terminal_game.presentation import palette
from terminal_game.presentation.field import BLANK, Cell
from terminal_game.presentation.metrics import COLUMNS, ROWS

#: SCRN-1's bottom row: the status line's row, derived rather than typed.
STATUS_ROW = ROWS - 1

#: SCRN-6.  Named here as well as in the palette so that a caller writing the
#: row asks this module for everything about the row, colour included.
STATUS_COLOUR = palette.STATUS

#: C-4: the specimen's bottom row begins with a space and STAT-2's prose does
#: not.  The specimen is normative.
LEADING_SPACE = " "

#: How wide the score's field is, left-aligned.  Uniquely determined by the
#: three examples the specification prints — see the module docstring.
SCORE_FIELD_WIDTH = 5

#: What comes before the score in each form, and what comes after it.  Copied
#: character for character out of STAT-2 and STAT-3; the only thing that
#: varies is the number dropped between them.
_FORMS = {
    Outcome.UNDECIDED: ("score ", "arrows, q quits"),
    Outcome.CAUGHT: ("CAUGHT  score ", "q quits"),
    Outcome.CLEARED: ("CLEARED  score ", "q quits"),
}


def status_text(outcome: Outcome, score: int) -> str:
    """The whole of row 29, for this outcome and this score.

    Includes C-4's leading space and excludes any padding to the right: the
    row is as long as it needs to be and the rest of the field stays blank,
    which is what STAT-1's "and nothing else" asks for.
    """
    if not isinstance(outcome, Outcome):
        raise TypeError(
            "the status line is chosen by an Outcome, not {!r}; the vocabulary "
            "is undecided, caught and cleared and there is no fourth".format(outcome)
        )
    if isinstance(score, bool) or not isinstance(score, int):
        # bool is an int in Python, and `score True` would render as "score 1".
        raise TypeError("the score must be a whole number, not {!r}".format(score))
    if score < 0:
        raise ValueError(
            "the score cannot be {}; SCORE-5 says it never goes down and it "
            "starts at zero".format(score)
        )

    before, after = _FORMS[outcome]
    return LEADING_SPACE + before + str(score).ljust(SCORE_FIELD_WIDTH) + after


def status_for(state: "GameState") -> str:
    """Row 29 for a game state — the call every caller should be making.

    **Asks :func:`~terminal_game.application.turn.outcome_of`, and never reads
    ``GameState.outcome``.**  The stored field is a cache the resolver stamps;
    the function is the derived total truth, and on a hand-built board the two
    can disagree.  Lane A found that in WI-11 with a failing test, where
    reading the field would have let a board with both actors on one square
    and an ``UNDECIDED`` stamp stay playable.

    The same crack runs through here.  If the session asks the function and
    the status line reads the field, the second source of truth has simply
    moved into the status line — and it would show as a decided game still
    offering ``arrows, q quits`` while the picture sits frozen behind it.
    **Everything that asks whether the game is over asks the same function**,
    so this function exists to make that the easy thing rather than a rule to
    remember.

    :func:`status_text` still takes an outcome directly, because a test that
    wants to render a particular form should be able to say so without
    building a state that produces it.
    """
    return status_text(outcome_of(state), state.score)


def status_cells(outcome: Outcome, score: int) -> "Tuple[Cell, ...]":
    """Row 29 as exactly :data:`~terminal_game.presentation.metrics.COLUMNS` cells.

    The same row as :func:`status_text`, in the shape
    :func:`~terminal_game.presentation.frame.compose_frame` asks for — the
    status text in :data:`STATUS_COLOUR`, then blanks to the end of the row.

    **The padding lives here on purpose.**  A row that stops short would leave
    the tail of row 29 showing whatever was under it, so something has to
    decide how it ends — and STAT-1's "and nothing else" makes that a
    statement about row 29's content, which is WI-12's and nobody else's.  If
    the composer padded it, part of row 29 would be composed outside this
    module.

    :func:`status_text` remains the primary answer.  This is the adaptor for a
    caller that wants cells, and it exists so that caller does not write the
    padding itself.
    """
    text = status_text(outcome, score)
    blank = Cell(BLANK, STATUS_COLOUR)
    return tuple(
        Cell(character, STATUS_COLOUR) for character in text
    ) + (blank,) * (COLUMNS - len(text))


def cells_for(state: "GameState") -> "Tuple[Cell, ...]":
    """Row 29 as cells, for a game state.  :func:`status_for`'s shape-adaptor.

    Asks :func:`~terminal_game.application.turn.outcome_of` for the same
    reason :func:`status_for` does, and for the same reason it matters.
    """
    return status_cells(outcome_of(state), state.score)


def is_decided(outcome: Outcome) -> bool:
    """Whether the status line is showing an ending rather than a game in play.

    STAT-3 asks that the line "says which of the two endings happened".  This
    is that question asked of the outcome, so a caller does not have to know
    which members of the vocabulary are endings.
    """
    return outcome is not Outcome.UNDECIDED
