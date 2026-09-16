# -*- coding: utf-8 -*-
"""WI-21 — the five questions only a person can answer.

    /usr/bin/python3 tools/the_questions.py --checklist
    /usr/bin/python3 tools/the_questions.py
    /usr/bin/python3 tools/the_questions.py --sizes 14,16,18,20 --seconds 15
    /usr/bin/python3 tools/the_questions.py --seconds 30 --json

**This item answers nothing.**  Five questions have been open for a whole
run, and five developers in a row have declined to close any of them from a
measurement.  They were right every time, and this tool exists to make the
questions **cheap and unambiguous to answer**, not to answer them.  Every
entry in :data:`QUESTIONS` carries ``answer=None`` and there is no code path
that sets it.

What it shows you, and what it is not
-------------------------------------
``--checklist`` prints everything and **opens nothing**, so you can read the
questions and the warning before anything appears on your screen.

With no ``--checklist`` it opens **one window per font size**, each holding
the **real assembled game** — the same :func:`~terminal_game.shell.game.build_game`
the shipped command assembles, at the same anchor, painted by the same
surface.  The ghost moves, the arrows move the player, ``q`` ends it early.

**It is not the shipped exit path, and must not be presented as one.**  The
game is ``/usr/bin/python3 -m terminal_game``, it is unbounded by design
because ``q`` is the only way out of a finished game (CTRL-4, END-6), and
section 4 rule 5 of the plan forbids an agent from starting it: launched by
an agent, nobody is there to press ``q``.  **It is yours to run.**  So the
split this tool keeps, and which the findings repeat question by question:

* the **harness** creates the window identically, so it answers the
  titlebar, the placement and the type size faithfully;
* the **real game** is the only thing that answers a whole game played to an
  ending, a real ``q`` out of a finished game, and the process exiting.

Window hygiene — section 4 of the plan, in full
------------------------------------------------
* The deadline is scheduled on the toolkit's own scheduler **before** the
  event loop is entered, so nothing here waits on a person.
* **A run with no deadline cannot be asked for.**  ``--seconds`` must be
  positive and no more than :data:`MAXIMUM_SECONDS`, and the whole run — every
  window added up — no more than :data:`MAXIMUM_RUN_SECONDS`.  Both are
  refused at parse time, before a window exists.
* The reap is in a ``finally``, so a failure anywhere still takes the window
  away, and the next window does not open until the last is confirmed gone.
* Only ever the handle captured at the moment of creation.  Never "the front
  window", never by title.

**It is not part of the suite**: its name does not match ``test_*``, so
``unittest discover`` never collects it.  What the suite imports is the half
above the toolkit line — the questions, the rulings, the option parsing and
:func:`a_sitting` driven by a recording double.
"""

from __future__ import annotations

import json
import os
import random
import sys
import time
from typing import Any, Callable, NamedTuple, Optional, Tuple

if __name__ == "__main__" and __package__ is None:  # pragma: no cover
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from terminal_game.domain.game_state import Outcome
from terminal_game.shell.anchor import FALLBACK_POSITION
from terminal_game.shell.game import build_game
from terminal_game.shell.grid_surface import FONT_POINT_SIZE
from terminal_game.shell.window_owner import WINDOW_TITLE

from tools.window_manners import window_still_there

__all__ = [
    "DEFAULT_SECONDS",
    "MAXIMUM_SECONDS",
    "MAXIMUM_RUN_SECONDS",
    "SIZE_LADDER",
    "SITTING_SEED",
    "THE_REAL_GAME",
    "THE_HARNESS",
    "THE_JOINERY_VIEW",
    "Question",
    "Ruling",
    "QUESTIONS",
    "RULINGS",
    "Options",
    "Sitting",
    "Stage",
    "parse_options",
    "the_warning",
    "checklist_lines",
    "a_sitting",
    "main",
]


# ---------------------------------------------------------------------------
# How long anything is allowed to be on somebody's screen
# ---------------------------------------------------------------------------

#: One window's default life.  Long enough to read a titlebar, notice where
#: the window landed and watch the ghost move; short enough that a forgotten
#: run goes away by itself.
DEFAULT_SECONDS = 20

#: The most one window may be asked for.  A person answering these questions
#: needs seconds, not minutes, and a cap is what makes "bounded" a property
#: of the tool rather than a habit of whoever types the command.
MAXIMUM_SECONDS = 60

#: The most a whole run may be asked for, every window added up.  Capping one
#: window is not enough on its own: four windows at the per-window maximum is
#: four minutes of somebody's screen.
MAXIMUM_RUN_SECONDS = 180

#: The four sizes WI-16 measured, for A4.  14 -> 320x480, 16 -> 400x570,
#: 18 -> 440x630, 20 -> 480x720, all in ``docs/findings/WI-16-the-look.md``.
SIZE_LADDER = (14, 16, 18, 20)

#: Fixed, so that two people looking at "the game" look at the same maze.
SITTING_SEED = 20260916


# ---------------------------------------------------------------------------
# The three instruments, and which questions each may be asked with
# ---------------------------------------------------------------------------

#: The game.  **An agent must never run this.**  It is unbounded by design.
THE_REAL_GAME = "/usr/bin/python3 -m terminal_game"

#: This tool.  A bounded harness over the same window code, and not the
#: shipped exit path.
THE_HARNESS = "/usr/bin/python3 tools/the_questions.py"

#: WI-16's joinery view — the only thing on this project that has ever put a
#: crossing glyph on a screen.  Section 13 names it for A10 by name, and the
#: reason is in :data:`QUESTIONS`.
THE_JOINERY_VIEW = "/usr/bin/python3 tools/the_look.py --view joinery --seconds 20"

FROM_THE_HARNESS = "the bounded harness, which is not the shipped exit path"
FROM_THE_JOINERY_VIEW = "WI-16's joinery view"
FROM_THE_REAL_GAME = "the real game, which is yours to start and nobody else's"
NOT_SEEN_BUT_DECIDED = "decided, not seen: no instrument can settle it"


class Question(NamedTuple):
    """One thing a person has to look at, with the exact way to look at it.

    ``answer`` is :data:`None` on every one of these and nothing in this
    module ever sets it.  That is the whole discipline of this work item:
    five developers declined to convert a measurement into an answer, and a
    field that could be quietly filled in would undo all five.
    """

    code: str
    asks: str
    instrument: str
    asked_of: str
    look_for: str
    if_the_answer_is_no: str
    answer: Optional[str] = None


class Ruling(NamedTuple):
    """One thing a person has to decide, with what a reversal costs.

    A ruling has no instrument.  What it has instead is a blast radius —
    ``lands_in`` is the one place the code changes if the answer comes back
    the other way, which is what makes each of these cheap to reverse.
    """

    code: str
    asks: str
    as_built: str
    lands_in: str
    cost_of_reversing_it: str


#: The five rulings inside question 5.  Each is a decision this project took
#: for a stated reason and recorded rather than hid; none is a coin flip.
RULINGS = (
    Ruling(
        code="A3 / C-2 — WIN-5 against END-5 and END-6",
        asks=(
            "Does the window close the instant the outcome is decided, or "
            "when the player presses q after seeing the final picture?"
        ),
        as_built=(
            "the second: the outcome is decided, the final picture stands, "
            "the player presses q, and the window closes itself"
        ),
        lands_in="terminal_game/application/session.py — WI-15, and nowhere else",
        cost_of_reversing_it=(
            "one work item's worth of change; the WIN-5, END-5 and END-6 "
            "sweep rows follow it"
        ),
    ),
    Ruling(
        code="A8 / C-5 — the dot on the losing turn",
        asks=(
            "When the ghost catches the player on a square that still has a "
            "dot, is the dot still eaten and still scored?"
        ),
        as_built=(
            "yes — the player is caught and the dot counts, so the last "
            "number the player ever sees is one higher"
        ),
        lands_in="terminal_game/domain/turn_resolver.py — WI-11, already landed",
        cost_of_reversing_it=(
            "a follow-up branch on WI-11, never a session change: scattering "
            "the step order is exactly what caution C6 exists to prevent"
        ),
    ),
    Ruling(
        code="A9 / C-6 — a winning score the game cannot reach",
        asks=(
            "STAT-3's winning example scores 274. A full game is worth 259 "
            "to 271 points, mean 264.5, so that score cannot occur. Do you "
            "want the example changed?"
        ),
        as_built=(
            "kept as an exemplar of the format, which is all it was ever "
            "needed for; no test and no sweep row asserts 274 as an "
            "achieved score"
        ),
        lands_in=(
            "terminal_game/presentation/status_line.py's formatting tests "
            "and the sweep rows — WI-13 and WI-20"
        ),
        cost_of_reversing_it=(
            "nothing waits on it; you may simply want to know your example "
            "is impossible"
        ),
    ),
    Ruling(
        code="A7 / C-3 and C-4 — the status line's exact wording",
        asks=(
            "The status line literals in the requirements disagree with the "
            "specimen picture by one leading space, and the two ending "
            "examples cannot both come from any single padding rule. Are "
            "the literals what you want?"
        ),
        as_built=(
            "the literals are normative and are reproduced exactly, as one "
            "template per ending; the specimen picture's leading space is "
            "treated as illustrative"
        ),
        lands_in="terminal_game/presentation/status_line.py — WI-13, and nowhere else",
        cost_of_reversing_it=(
            "three template constants in one module; every other item "
            "obtains row 29 from that module rather than typing it"
        ),
    ),
    Ruling(
        code="The ghost's start-corner tie-break — WI-6",
        asks=(
            "START-2 names the furthest corridor square from the player, "
            "singular, but on a real maze four corners tie. Should the tie "
            "be drawn at random instead of broken the same way every time?"
        ),
        as_built=(
            "broken deterministically, so the ghost always starts in the "
            "left-hand column — (1, 1) in 115 of 200 mazes and (1, 27) in "
            "the other 85, never on the right. A player would notice over a "
            "few games. It was not randomised because WI-6 was handed no "
            "random source and inventing one would be inventing a "
            "requirement"
        ),
        lands_in=(
            "ghost_start_square in terminal_game/domain/opening_position.py "
            "— one extra parameter and one draw over the tied squares"
        ),
        cost_of_reversing_it=(
            "two hand-built tests change; the 200-seed property tests "
            "assert that no corridor square is further and pass either way"
        ),
    ),
)


#: The five questions, exactly as section 13 of the plan leaves them: all
#: five open, after a whole run of deliberately refusing to answer them.
QUESTIONS = (
    Question(
        code="A1 — the titlebar",
        asks="Does the titlebar read exactly {0!r}?".format(WINDOW_TITLE),
        instrument=THE_HARNESS,
        asked_of=FROM_THE_HARNESS,
        look_for=(
            "the strip along the top of the window, and nothing else on the "
            "screen. Exactly {0!r}, with nothing before it and nothing "
            "after it — no file name, no 'python3', no trailing marker. The "
            "toolkit has read that string back to us on every window this "
            "project has ever opened, and five developers have each refused "
            "to call that an answer, because reading a string back from the "
            "toolkit that set it is not a person seeing a titlebar."
            .format(WINDOW_TITLE)
        ),
        if_the_answer_is_no=(
            "WINDOW_TITLE in terminal_game/shell/window_owner.py is the one "
            "constant, and nothing composes anything around it"
        ),
    ),
    Question(
        code="A10 / SCRN-3 — do the strokes meet?",
        asks=(
            "Do the blue double lines join up into clean corners, tees and "
            "crossings, with no hairline gap where two strokes meet?"
        ),
        instrument=THE_JOINERY_VIEW,
        asked_of=FROM_THE_JOINERY_VIEW,
        look_for=(
            "a lattice filling the whole window. Look where two cells meet: "
            "a hairline of black between one stroke and the next, or a "
            "stroke that steps sideways instead of running straight. If it "
            "reads as solid continuous rules, the answer is yes. Ask it "
            "HERE and not on a game screen: the specimen picture in the "
            "requirements contains no crossing glyph at all, and a real "
            "maze renders one in only 55 of 200 seeds — so a game may never "
            "show you the junction most likely to be wrong. The advance "
            "widths are measured uniform, with a control proving that is "
            "the font's own coverage rather than a fallback artefact; that "
            "settles the SPACING and says nothing whatever about whether "
            "the strokes touch."
        ),
        if_the_answer_is_no=(
            "the glyph table in terminal_game/presentation/wall_glyphs.py, "
            "or the font; FONT_FAMILY in "
            "terminal_game/shell/grid_surface.py is the other constant"
        ),
    ),
    Question(
        code="A4 — is the type comfortable?",
        asks=(
            "Is Menlo at {0}pt, in a window of about 400 x 570 pixels, "
            "large enough to read comfortably?".format(FONT_POINT_SIZE)
        ),
        instrument="{0} --sizes {1}".format(
            THE_HARNESS, ",".join(str(size) for size in SIZE_LADDER)
        ),
        asked_of=FROM_THE_HARNESS,
        look_for=(
            "four windows in turn, the same game at four sizes, so the "
            "answer is a comparison rather than a guess. Can you read the "
            "bottom row without leaning in, and tell the player's shape "
            "from the ghost's at a glance?"
        ),
        if_the_answer_is_no=(
            "FONT_POINT_SIZE in terminal_game/shell/grid_surface.py is one "
            "constant either way, and the window size follows from it: "
            "14 -> 320x480, 16 -> 400x570, 18 -> 440x630, 20 -> 480x720"
        ),
    ),
    Question(
        code="A2 revised / WIN-4 — where the window landed",
        asks="Did the window land somewhere you could see it?",
        instrument=THE_HARNESS,
        asked_of=FROM_THE_HARNESS,
        look_for=(
            "where the window appeared, and nothing more ambitious than "
            "that. READ THE WARNING ABOVE FIRST: it will open at ({0}, {1}) "
            "on your primary display and NOT near your pointer, and that is "
            "expected rather than broken.".format(
                FALLBACK_POSITION.x, FALLBACK_POSITION.y
            )
        ),
        if_the_answer_is_no=(
            "a better fallback position — FALLBACK_POSITION in "
            "terminal_game/shell/anchor.py — and NOT a permission. Granting "
            "Accessibility would change nothing; see the warning."
        ),
    ),
    Question(
        code="A3, A8, A9, A7 and the ghost's start corner — five rulings",
        asks=(
            "Five things the specification does not settle, each decided "
            "here for a stated reason. Do you agree with each?"
        ),
        instrument="{0} --checklist".format(THE_HARNESS),
        asked_of=NOT_SEEN_BUT_DECIDED,
        look_for=(
            "the five rulings printed below. Each says what was built, the "
            "one place the code changes if you rule the other way, and what "
            "that costs. None of them is a coin flip and none of them needs "
            "a screen."
        ),
        if_the_answer_is_no=(
            "each ruling names its own one place; see the "
            "'lands in' line against it"
        ),
    ),
)


# ---------------------------------------------------------------------------
# What only the real game can answer, and the command for it
# ---------------------------------------------------------------------------

#: Things the harness genuinely cannot show you, so that nobody is tempted
#: to read a harness run as covering them.
ONLY_THE_REAL_GAME = (
    "A whole game played to an ending. No run on this project has ever "
    "reached one on a screen: every on-screen run so far ended UNDECIDED "
    "with two dots eaten out of 259 to 271. A game to either ending exists "
    "only headless, in the suite.",
    "A real q ending a FINISHED game. The harness lets you press q, but its "
    "backstop would have closed the window anyway; only the unbounded game "
    "proves q is what got you out.",
    "The close button, pressed by a hand. The exercises evaluate the same "
    "message a window manager sends, which is the real path, but nobody has "
    "clicked it.",
    "The process exiting, and the terminal you started it from coming back "
    "with nothing printed to it.",
)


def the_warning() -> str:
    """The one thing to say before a person looks, or C-7 reads as a bug.

    Measured in ``docs/findings/WI-14-anchor-query.md`` and confirmed on
    four real windows in ``docs/findings/WI-18-the-game-on-screen.md``.  The
    numbers are quoted with their source because a measurement carries the
    moment it was taken.
    """
    return "\n".join(
        (
            "  READ THIS BEFORE YOU LOOK - otherwise it will read as a bug",
            "",
            "  The window will open at the fixed fallback position ({0}, {1})".format(
                FALLBACK_POSITION.x, FALLBACK_POSITION.y
            ),
            "  on your PRIMARY display. It will NOT appear near your pointer.",
            "",
            "  That is correct, and the reason is geometry rather than",
            "  permission. Measured on this machine (WI-14, confirmed in",
            "  WI-18): the toolkit reports the pointer in whole-desktop",
            "  coordinates - it read (-175, -448), a second display up and to",
            "  the left - while it describes only the primary display, at",
            "  1512 x 982. It knows the desktop is 5120 x 2422 but gives no",
            "  origin, so there is NO RECTANGLE to bound the pointer into, and",
            "  an anchor that cannot be bounded is treated as nothing seen.",
            "",
            "  GRANTING ACCESSIBILITY WOULD NOT CHANGE THIS. If you dislike",
            "  where the window lands, the fix is a better fallback position,",
            "  not a permission. Please do not grant one for this.",
        )
    )


# ---------------------------------------------------------------------------
# What a run was asked to do
# ---------------------------------------------------------------------------


class Sitting(NamedTuple):
    """One window: the game at one size, for one bounded stretch."""

    point_size: int
    seconds: int


class Options:
    """What a run was asked to do.  A value, so it can be asserted."""

    def __init__(self, sizes, seconds, quiet, checklist_only):
        self.sizes = tuple(sizes)
        self.seconds = seconds
        self.quiet = quiet
        self.checklist_only = checklist_only

    def __eq__(self, other):
        if not isinstance(other, Options):
            return NotImplemented
        return (
            self.sizes == other.sizes
            and self.seconds == other.seconds
            and self.quiet == other.quiet
            and self.checklist_only == other.checklist_only
        )

    def __repr__(self):
        return (
            "Options(sizes={0}, seconds={1}, quiet={2}, "
            "checklist_only={3})".format(
                self.sizes, self.seconds, self.quiet, self.checklist_only
            )
        )

    @property
    def sittings(self) -> Tuple[Sitting, ...]:
        """Every window this run will open, in order."""
        if self.checklist_only:
            return ()
        return tuple(Sitting(size, self.seconds) for size in self.sizes)

    @property
    def windows(self) -> int:
        return len(self.sittings)

    @property
    def worst_case_seconds(self) -> int:
        """The longest this run can possibly last, if nobody presses a key."""
        return sum(sitting.seconds for sitting in self.sittings)


def parse_options(argv) -> Options:
    """Read the command line, refusing anything unbounded.

    A run with no deadline is the one thing this tool must never do, so both
    caps are applied here — before a window exists — rather than discovered
    when one will not go away.
    """
    argv = list(argv)
    sizes = [FONT_POINT_SIZE]
    seconds = DEFAULT_SECONDS
    quiet = "--json" in argv
    checklist_only = "--checklist" in argv

    if "--sizes" in argv:
        sizes = [int(s) for s in argv[argv.index("--sizes") + 1].split(",") if s]
        if not sizes:
            raise ValueError("--sizes needs at least one point size")
        if any(size <= 0 for size in sizes):
            raise ValueError("a font size must be positive")
    if "--seconds" in argv:
        seconds = int(argv[argv.index("--seconds") + 1])
    if seconds <= 0:
        raise ValueError(
            "--seconds must be positive: this tool never opens a window "
            "without a deadline"
        )
    if seconds > MAXIMUM_SECONDS:
        raise ValueError(
            "--seconds must be at most {0}: a window held longer than that "
            "is somebody's screen, not a measurement".format(MAXIMUM_SECONDS)
        )

    options = Options(sizes, seconds, quiet, checklist_only)
    if options.worst_case_seconds > MAXIMUM_RUN_SECONDS:
        raise ValueError(
            "{0} window(s) at {1}s each is {2}s, and a whole run may be at "
            "most {3}s: ask for fewer sizes or a shorter deadline".format(
                options.windows,
                seconds,
                options.worst_case_seconds,
                MAXIMUM_RUN_SECONDS,
            )
        )
    return options


# ---------------------------------------------------------------------------
# The checklist, printed and written down from one place so the two agree
# ---------------------------------------------------------------------------


def _wrapped(text: str, indent: str = "     ", width: int = 72, hang: str = ""):
    """Break *text* into indented lines.  No dependency, no surprises.

    *hang* is added to the indent of every line after the first, so a
    bulleted item's continuation lines sit under its text rather than under
    its bullet.
    """
    words = text.split()
    lines, current = [], indent
    continuation = indent + hang
    for word in words:
        candidate = word if current.strip() == "" else current + " " + word
        if len(candidate) > width and current.strip():
            lines.append(current)
            current = continuation + word
        else:
            current = candidate if current.strip() else indent + word
    if current.strip():
        lines.append(current)
    return lines


def checklist_lines(options: Optional[Options] = None):
    """The whole checklist, as lines.  The product of this work item.

    The findings document quotes this rather than restating it, so there is
    one wording and it cannot drift.
    """
    lines = ["WI-21 - the five questions only a person can answer", ""]
    lines.append(the_warning())
    lines.append("")
    lines.append("THE FIVE QUESTIONS")
    for number, question in enumerate(QUESTIONS, start=1):
        lines.append("")
        lines.append("  {0}. {1}".format(number, question.code))
        lines.extend(_wrapped(question.asks))
        lines.append("     run:  {0}".format(question.instrument))
        lines.append("     from: {0}".format(question.asked_of))
        lines.extend(_wrapped("look for: " + question.look_for))
        lines.extend(_wrapped("if no: " + question.if_the_answer_is_no))

    lines.append("")
    lines.append("  THE FIVE RULINGS INSIDE QUESTION 5")
    for ruling in RULINGS:
        lines.append("")
        lines.append("    {0}".format(ruling.code))
        lines.extend(_wrapped(ruling.asks, indent="       "))
        lines.extend(_wrapped("as built: " + ruling.as_built, indent="       "))
        lines.extend(_wrapped("lands in: " + ruling.lands_in, indent="       "))
        lines.extend(
            _wrapped(
                "reversing it costs: " + ruling.cost_of_reversing_it,
                indent="       ",
            )
        )

    lines.append("")
    lines.append("THE GAME ITSELF - yours to run, and only yours")
    lines.append("")
    lines.append("    {0}".format(THE_REAL_GAME))
    lines.append("")
    lines.extend(
        _wrapped(
            "No agent on this project may start that command. It is "
            "unbounded by design - q is the only way out of a finished game "
            "(CTRL-4, END-6) - so launched by an agent, nobody is there to "
            "press q. Everything above this line was shown to you through a "
            "bounded harness over the same window code; it creates the "
            "window identically, but it is NOT the shipped exit path.",
            indent="    ",
        )
    )
    lines.append("")
    lines.append("    What only the real game can answer:")
    for item in ONLY_THE_REAL_GAME:
        lines.append("")
        lines.extend(_wrapped("- " + item, indent="      ", hang="  "))
    lines.append("")
    lines.extend(
        _wrapped(
            "Add --seed N to replay one particular maze. The two endings are "
            "{0} and {1}; a cleared game is worth 259 to 271 points, so "
            "expect to be caught long before you clear one.".format(
                Outcome.CAUGHT.name, Outcome.CLEARED.name
            ),
            indent="    ",
        )
    )

    if options is not None and options.windows:
        lines.append("")
        lines.append(
            "THIS RUN: {0} window(s), {1}s each, {2}s at the very most, and "
            "each closes itself.".format(
                options.windows, options.seconds, options.worst_case_seconds
            )
        )
        lines.append("Press q in a window to move on sooner.")
    return lines


# ---------------------------------------------------------------------------
# One sitting: one window, held for a person, and reaped
# ---------------------------------------------------------------------------


class Stage:
    """Everything a sitting needs that touches a screen, in one argument.

    Gathered like this for one reason: a test can hand :func:`a_sitting` a
    recording toolkit and a stand-in surface, and assert that the deadline is
    scheduled before the loop is entered and that the window is reaped even
    when the body falls over — **with no window anywhere**.  The real one is
    built by :func:`real_stage`, below the toolkit line.
    """

    __slots__ = (
        "toolkit",
        "pixel_size",
        "make_surface",
        "position",
        "point_size",
        "cell_width_px",
        "cell_height_px",
        "anchor_saw_something",
        "anchor_failure",
        "measure",
    )

    def __init__(
        self,
        toolkit: Any,
        pixel_size: Any,
        make_surface: Callable[[Any], Any],
        position: Any,
        point_size: int = FONT_POINT_SIZE,
        cell_width_px: Optional[int] = None,
        cell_height_px: Optional[int] = None,
        anchor_saw_something: bool = False,
        anchor_failure: Optional[str] = None,
        measure: Optional[Callable[[dict, Any], None]] = None,
    ) -> None:
        self.toolkit = toolkit
        self.pixel_size = pixel_size
        self.make_surface = make_surface
        self.position = position
        self.point_size = point_size
        self.cell_width_px = cell_width_px
        self.cell_height_px = cell_height_px
        self.anchor_saw_something = anchor_saw_something
        self.anchor_failure = anchor_failure
        self.measure = measure


def a_sitting(stage: Stage, seconds: int, seed: int = SITTING_SEED) -> dict:
    """Open one window on the **real assembled game**, hold it, reap it.

    The game is :func:`~terminal_game.shell.game.build_game` with everything
    left at its default, so the picture comes from the production join in
    ``terminal_game/shell/game.py`` and this module composes nothing of its
    own.  The ghost moves, the arrows move the player and ``q`` ends it
    early; the deadline ends it if nobody does anything at all.

    Returns a record of what was asked for and what happened.  It never
    raises: a failure is reported in ``error`` and the window is reaped in
    the ``finally`` either way.
    """
    record = {
        "point_size": stage.point_size,
        "seconds": seconds,
        "seed": seed,
        "asked_for": {
            "title": WINDOW_TITLE,
            "width_px": stage.pixel_size.width,
            "height_px": stage.pixel_size.height,
            "x": stage.position.x,
            "y": stage.position.y,
            "cell_width_px": stage.cell_width_px,
            "cell_height_px": stage.cell_height_px,
            "anchor_saw_something": stage.anchor_saw_something,
            "anchor_failure": stage.anchor_failure,
        },
        "measured": {},
        "error": None,
    }
    game = build_game(
        stage.toolkit,
        stage.pixel_size,
        stage.make_surface,
        position=stage.position,
        random_source=random.Random(seed),
    )
    started = time.monotonic()
    target = None
    try:
        surface = game.start()
        target = getattr(surface, "canvas", None)
        if stage.measure is not None and target is not None:
            stage.toolkit.schedule_once(
                600, lambda: stage.measure(record["measured"], target)
            )
        # The deadline, on the toolkit's own scheduler, BEFORE the event loop
        # is entered. This run cannot outlive it even if nothing else
        # happens at all, and it does not depend on anybody pressing
        # anything.
        stage.toolkit.schedule_once(
            int(seconds * 1000), game.owner.end_session
        )
        game.run()
    except BaseException as exc:  # reported, not swallowed: see the finally
        record["error"] = "{0}: {1}".format(type(exc).__name__, exc)
    finally:
        game.owner.end_session()
        record["measured"]["window_reaped"] = not game.owner.is_open
        record["measured"]["widget_still_there"] = window_still_there(target)
        record["measured"]["held_for_s"] = round(time.monotonic() - started, 3)

    record["measured"].update(
        {
            "exit_code": game.exit_code,
            "session_failure": None
            if game.failure is None
            else "{0}: {1}".format(
                type(game.failure).__name__, game.failure
            ),
            "phase_at_the_end": game.session.phase.value,
            "frames_shown": game.frames_shown,
            "score": game.session.state.score.points,
            "outcome": game.session.state.outcome.name,
            "ended_before_the_deadline": record["measured"]["held_for_s"]
            < seconds,
        }
    )
    return record


# ---------------------------------------------------------------------------
# Everything below here touches the real toolkit and the real screen.
# ---------------------------------------------------------------------------


def real_stage(point_size: int) -> Stage:  # pragma: no cover - needs a window
    """The real thing: the real font, the real anchor, the real toolkit.

    Assembled exactly as :func:`terminal_game.shell.game.main` assembles it,
    which is what lets the harness answer the titlebar, the placement and
    the type-size questions faithfully.
    """
    from terminal_game.shell import tk_grid
    from terminal_game.shell.anchor import WindowAnchor
    from terminal_game.shell.grid_surface import pixel_size_for
    from terminal_game.shell.tk_anchor import pointer_anchor
    from terminal_game.shell.tk_toolkit import TkToolkit

    metrics = tk_grid.measure_metrics(point_size=point_size)
    pixel_size = pixel_size_for(metrics)
    anchor = WindowAnchor(pointer_anchor)
    position = anchor.position_for(pixel_size)
    return Stage(
        toolkit=TkToolkit(),
        pixel_size=pixel_size,
        make_surface=lambda target: tk_grid.surface_on(
            target, metrics, point_size=point_size
        ),
        position=position,
        point_size=point_size,
        cell_width_px=metrics.width,
        cell_height_px=metrics.height,
        anchor_saw_something=anchor.anchor() is not None,
        anchor_failure=None
        if anchor.failure is None
        else repr(anchor.failure),
        measure=_read_the_window_back,
    )


def _read_the_window_back(measured, canvas):  # pragma: no cover - needs a window
    """Read the window back once, from the handle we were given and no other.

    This is what lets the findings say where the window *actually* landed
    rather than where it was asked to land — and note that reading the title
    back is emphatically **not** an answer to A1.
    """
    root = canvas.winfo_toplevel()
    measured.update(
        {
            "title_read_back_which_is_not_an_answer_to_A1": root.title(),
            "window_width_px": root.winfo_width(),
            "window_height_px": root.winfo_height(),
            "landed_at_x": root.winfo_x(),
            "landed_at_y": root.winfo_y(),
            "canvas_items": len(canvas.find_all()),
            "canvas_item_kinds": sorted(
                {canvas.type(item) for item in canvas.find_all()}
            ),
        }
    )


def main(argv) -> int:  # pragma: no cover - measured by running it
    try:
        options = parse_options(argv)
    except (ValueError, IndexError) as error:
        print("the_questions: {0}".format(error), file=sys.stderr)
        return 2

    if not options.quiet:
        print("\n".join(checklist_lines(options)))
        print()

    findings = {
        "asked_for": {
            "sizes": list(options.sizes),
            "seconds_each": options.seconds,
            "windows": options.windows,
            "worst_case_seconds": options.worst_case_seconds,
            "checklist_only": options.checklist_only,
        },
        "answers": {question.code: question.answer for question in QUESTIONS},
        "sittings": [],
    }

    for sitting in options.sittings:
        if not options.quiet:
            print(
                "  opening the game at {0}pt for up to {1}s...".format(
                    sitting.point_size, sitting.seconds
                )
            )
        record = a_sitting(real_stage(sitting.point_size), sitting.seconds)
        findings["sittings"].append(record)
        if not record["measured"]["window_reaped"]:
            print(
                "the_questions: a window was NOT reaped; stopping rather "
                "than opening another.",
                file=sys.stderr,
            )
            break

    # A run that opened nothing has not reaped everything; it has reaped
    # nothing, and reporting ``true`` over an empty list would be the same
    # vacuous pass WI-10's guards refuse to give.
    findings["windows_opened"] = len(findings["sittings"])
    findings["all_windows_reaped"] = (
        all(
            record["measured"].get("window_reaped")
            for record in findings["sittings"]
        )
        if findings["sittings"]
        else None
    )
    findings["errors"] = [
        record["error"] for record in findings["sittings"] if record["error"]
    ]
    print(json.dumps(findings, indent=2, sort_keys=True))
    if findings["errors"] or findings["all_windows_reaped"] is False:
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main(sys.argv[1:]))
