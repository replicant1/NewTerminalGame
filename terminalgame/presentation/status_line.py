"""The bottom row of the window: the score, and the keys that can be used.

STAT-1, STAT-2, STAT-3 and SCRN-6. Pure presentation — it reads a game state
and returns text and a colour name. It draws nothing, knows no terminal, and
does not know which row of the frame it will end up on; WI-5b places it.

## One rule, and it reproduces all three lines the specification quotes

The specification gives three examples and never states a rule:

    during play    ' score 0    arrows, q quits'
    on a loss      'CAUGHT  score 37   q quits'
    on a win       'CLEARED  score 274  q quits'

They are all the same shape. **The score is written as `score <n>`
left-justified in nine columns, with two spaces between it and whatever
follows.** Nine because `score ` is six characters and the score itself gets
three, which is enough for every score this game can reach: a 19 x 29 maze
holds fewer than three hundred dots, so the widest real score is three digits.
During play the line is indented by one space; on an ending, the ending's name
takes the front instead.

That single rule produces all three quoted lines character for character, which
is the reason to believe it is the rule the examples were written from.

## Two questions the specification leaves open

**The leading space.** The picture shows the play line as 27 characters
beginning with a space; STAT-2 quotes the same line inline, in backticks,
without one. **This keeps the space**, for three reasons: the picture is a
verbatim code block, which preserves whitespace exactly, where an inline quote
is prose in which a leading space is invisible and easily lost in
transcription; the maze's left wall stands at column 0, so the indent lifts the
status line off it; and the M0 skeleton already in the tree writes it with the
space, so keeping it agrees with what is there rather than contradicting it.
**This is an assumption, not a ruling** — the user has not been asked. It is one
constant to change: :data:`PLAY_INDENT`.

**The two ending lines do not align with each other.** `q quits` begins at
column 19 on a loss and column 20 on a win. That is **incidental**, and the
reason is not that the arithmetic works out — it is that **a game ends one way,
so no player ever sees both lines.** Alignment between them is unobservable.
The difference falls out of `CAUGHT` being six letters and `CLEARED` seven;
forcing them to agree would mean departing from a quoted line to fix something
nobody can see.
"""

from __future__ import annotations

from terminalgame.domain.game_state import Outcome
from terminalgame.screen.port import REQUIRED_WIDTH, Colour

#: SCRN-6 — the status line is written in cyan. The name is the port's; only
#: the terminal adapter knows that this one means cyan.
STATUS_COLOUR = Colour.STATUS

#: `score ` plus three columns for the number. See the module docstring.
SCORE_FIELD_WIDTH = 9

#: Two spaces between the fields, in every one of the quoted lines.
GAP = "  "

#: The one space the picture shows in front of the play line, and the whole of
#: the leading-space question. Set it to "" to drop the indent.
PLAY_INDENT = " "

#: What can be pressed, which is not the same during a game and after one.
PLAYING_KEYS = "arrows, q quits"
ENDED_KEYS = "q quits"

#: What the line calls each ending. Upper case, as STAT-3 quotes them.
ENDING_NAMES = {
    Outcome.CAUGHT: "CAUGHT",
    Outcome.CLEARED: "CLEARED",
}


class StatusLineWillNotFit(ValueError):
    """The row is too narrow to say what STAT-1 requires it to say.

    Plan §11.8 — refuse rather than degrade. Truncating would drop the end of
    the line, and the end of the line is the part that says which keys work; a
    status row that has quietly lost `q quits` is worse than a loud failure,
    because END-6 makes that the only way out of a finished game.
    """


def score_field(score):
    """`score 37  ` — the score, padded to a fixed width.

    Padded rather than the number being right-justified, because that is what
    reproduces the quoted lines: `score 37` is followed by three spaces before
    `q quits` and `score 274` by two, which is one field of nine columns in
    both cases rather than two different gaps.
    """
    return "score {0}".format(score).ljust(SCORE_FIELD_WIDTH)


def status_text(state):
    """The status line for this state, unpadded.

    During play it is the score and the keys (STAT-2); after an ending it names
    which ending happened and the final score (STAT-3). The score shown is
    always the state's own, so "kept up to date" needs nothing doing to it.
    """
    field = score_field(state.score)
    ending = ENDING_NAMES.get(state.outcome)
    if ending is None:
        return PLAY_INDENT + field + GAP + PLAYING_KEYS
    return ending + GAP + field + GAP + ENDED_KEYS


def status_row(state, width=REQUIRED_WIDTH):
    """The whole bottom row: the status line, and blanks to the end of it.

    STAT-1 — "the score and the keys that can be used, and nothing else". The
    row is exactly `width` characters so that whatever it replaces is covered;
    a shorter string would leave the tail of the previous frame's line on the
    screen.
    """
    text = status_text(state)
    if len(text) > width:
        raise StatusLineWillNotFit(
            "the status line needs %d columns and the row is %d: %r (STAT-1)"
            % (len(text), width, text))
    return text.ljust(width)
