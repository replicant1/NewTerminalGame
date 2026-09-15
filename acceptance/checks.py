# -*- coding: utf-8 -*-
"""Everything a person has to look at, and nothing a machine can settle.

WI-14b puts this in front of somebody. It is code rather than a markdown file
for one reason: **a checklist that is code can be held to account.** There are
tests that every requirement needing a person is registered, that each carries
steps somebody could actually follow, and — the one that matters — that
**nothing here is recorded as verified**.

A `HumanCheck` has no "passed" field. Not set to False: absent. An agent cannot
mark one of these done, because there is nowhere to write it.
"""

from __future__ import annotations

import collections

#: A thing only a person can answer.
#:
#: ``codes``      the requirement codes it settles, as the specification writes them
#: ``question``   what the person is being asked, in one sentence
#: ``steps``      exactly what to do, in order
#: ``look_for``   what a correct answer looks like
#: ``why_machine_cannot``  why this is not automated, which is the load-bearing field
HumanCheck = collections.namedtuple(
    "HumanCheck", "name codes question steps look_for why_machine_cannot")


COLOURS = HumanCheck(
    name="the colours",
    codes=("SCRN-3", "SCRN-4", "SCRN-5", "SCRN-6"),
    question="Are the five colours right, and can the player and the ghost be "
             "told apart by colour as well as by shape?",
    steps=(
        "Run `python3 -m acceptance --run` and let the window open.",
        "Look at the picture while the game is running, before it closes.",
    ),
    look_for=(
        "the walls in BLUE double lines (SCRN-3)",
        "the dots a DIM GOLD, not a bright yellow (SCRN-4)",
        "the player a BRIGHT YELLOW block, ▐█▌ (SCRN-5)",
        "the ghost PINK, not purple, and a different shape, ▗█▖ (SCRN-5)",
        "the status line CYAN (SCRN-6)",
        "player and ghost distinguishable by colour ALONE, and by shape alone",
    ),
    why_machine_cannot=
        "`contents of selected tab` returns text and nothing else. There is no "
        "way to read a cell's colour back out of Terminal, so no automated "
        "check anywhere in this project covers SCRN-3 to SCRN-6 at all. Two "
        "of the five are substitutions besides — an eight-colour terminal has "
        "no gold and no pink, so dim yellow and bold magenta stand in, and "
        "whether they READ as gold and pink is a judgement about a person's "
        "eyes.",
)

FONT_AND_SIZE = HumanCheck(
    name="the font and the window size",
    codes=("WIN-2",),
    question="Is the window comfortably legible, and does every character the "
             "game draws come out one column wide?",
    steps=(
        "With the window open, look at the whole picture.",
        "Look down a long vertical wall from top to bottom.",
    ),
    look_for=(
        "text large enough to read without leaning in — Menlo 14, measured at "
        "357 x 558 points for 40 x 30",
        "vertical walls that line up perfectly down the whole height",
        "no character noticeably wider or narrower than its neighbours",
    ),
    why_machine_cannot=
        "A substituted glyph at a different advance width shears the picture, "
        "and the shear is visible but not measurable through a text capture — "
        "`contents of selected tab` returns the characters the game wrote, not "
        "the characters the font drew. Legibility is a judgement in any case.",
)

FLICKER_AND_CURSOR = HumanCheck(
    name="flicker and the cursor",
    codes=("SCRN-7",),
    question="Does the picture redraw cleanly, and is the text cursor never "
             "visible?",
    steps=(
        "Watch the window for the whole of a session, without pressing "
        "anything.",
        "Watch it again while pressing arrow keys.",
    ),
    look_for=(
        "each frame appearing in one go, not painted in pieces",
        "no tearing and no flashing as the ghost moves",
        "NO text cursor anywhere, at any moment, including as the game exits",
    ),
    why_machine_cannot=
        "Flicker is a property of what the eye sees between frames. A text "
        "capture shows one settled frame and says nothing about how it got "
        "there.",
)

WINDOW_PLACEMENT = HumanCheck(
    name="where the window lands",
    codes=("WIN-4",),
    question="Does the new window land visibly, a little below and right of "
             "the window you were last looking at?",
    steps=(
        "Click on some other window so it is the one you were last looking at.",
        "Run the pack and watch where the game window appears.",
        "If you have more than one display, repeat with the other window on "
        "each display in turn.",
        "Then do it once more with that window dragged hard into the "
        "BOTTOM-RIGHT corner of a display, which is the case the two placement "
        "rules disagree about.",
    ),
    look_for=(
        "the game window fully on screen, never half off an edge",
        "its corner down and right of the window you were looking at — EXCEPT "
        "from the bottom-right corner, where it is expected to be pulled back "
        "left and up instead, and that is not a defect (see below)",
        "on the SAME display as the window you were looking at",
    ),
    why_machine_cannot=
        "The launcher reads the position back rather than trusting the move, "
        "so the number is checked — but `set position` is a request macOS may "
        "constrain, measured twice on this project (asked for y = -1352, "
        "landed at y = 30). Whether the result is somewhere a person can "
        "actually see is not a number.\n\n"
        "     **Two rules, and which one wins is a ruling rather than a "
        "measurement.** `target_position` puts the window below and right of "
        "the reference window, then pulls it back onto the screen — and where "
        "those conflict, the pull back onto the screen wins. So from a "
        "reference window in the bottom-right corner the game window appears "
        "up and to the LEFT of it: on a 1440x900 screen, 217 points left. The "
        "screen it is pulled onto is the UNION of every display, much of which "
        "may be over no display at all, so on a multi-display desktop this is "
        "the one placement a machine cannot vouch for. Looking at it is the "
        "only way to know whether the ruling was right.",
)

TITLE_BAR = HumanCheck(
    name="the title bar",
    codes=("WIN-3",),
    question="What does the title bar actually say?",
    steps=(
        "With the window open, read the title bar.",
    ),
    look_for=(
        "it should contain 'Terminal Game'",
        "it will probably ALSO contain the user name and the running command, "
        "e.g. 'rodneybailey — Terminal Game — /bin/sh'",
    ),
    why_machine_cannot=
        "WIN-3 asks for the title to read 'Terminal Game' and nothing else. "
        "Two of the components in that bar — the active process name and the "
        "working directory the login shell publishes — are absent from "
        "Terminal's scripting dictionary and are governed by the player's "
        "saved profile, which assumption A3 forbids changing. **WIN-3 is "
        "therefore NOT MET and is not to be recorded as verified.** This check "
        "exists to record what it does say, so the user can decide whether to "
        "relax A3 or accept it.",
)

GHOST_CONFINEMENT = HumanCheck(
    name="the ghost that cannot get out",
    codes=("GHOST-1",),
    question="In about one game in sixty the ghost circles a small loop for "
             "the whole game. Is that acceptable?",
    steps=(
        "Run `python3 -m acceptance --run --seed 21`, and again with 26.",
        "Watch whether the ghost ever leaves its circuit.",
    ),
    look_for=(
        "whether it reads as 'the ghost is stuck' or just as an easy game",
    ),
    why_machine_cannot=
        "**The mechanism is verified and GHOST-2, GHOST-3 and GHOST-4 are "
        "met** — there is a test that a confined ghost still goes straight "
        "where it can, never reverses and never leaves the corridors. What "
        "cannot be settled is GHOST-1's purpose clause, 'one ghost roams the "
        "maze': measured over 500 games, 8 of them (1.6%) confine the ghost "
        "to a loop reaching 4.5% to 37.2% of the maze, and no random source "
        "can change it. Whether that matters is a judgement about how the "
        "game should feel.",
)

THE_FEEL_OF_IT = HumanCheck(
    name="whether it plays well",
    codes=("GHOST-1", "MAZE-4", "CTRL-1"),
    question="Does it feel right to play?",
    steps=(
        "Play several games through to a win and to a loss.",
        "Press the arrow keys and watch the player move.",
    ),
    look_for=(
        "the ghost at about seven moves a second — fast enough to be a threat, "
        "slow enough to escape",
        "the mazes interesting rather than merely legal: 47-49% corridor, no "
        "dead ends, plenty of loops",
        "arrow keys that respond at once, with no lag and no dropped presses",
    ),
    why_machine_cannot=
        "Every specified property of the maze is a floor — no dead end, no "
        "isolated pocket, corridors one square wide — and nothing in MAZE-1 to "
        "MAZE-6 asks whether a layout is INTERESTING. The tick rate is "
        "verified against a clock; whether it feels right is not a number.",
)

A_REAL_KEYBOARD = HumanCheck(
    name="a real keyboard",
    codes=("CTRL-1", "CTRL-4", "END-6", "WIN-5"),
    question="Do the arrow keys and `q` work when a person presses them?",
    steps=(
        "With the game running, press each arrow key and watch the player.",
        "Press some other keys — letters, function keys — and watch nothing "
        "happen.",
        "Press `q`. Then run it again and press `Q`.",
    ),
    look_for=(
        "the player moving one square per press, and not moving into walls",
        "unmapped keys doing NOTHING — no movement, no score change",
        "`q` and `Q` both ending the game at once",
        "the window closing itself afterwards, leaving nothing behind",
    ),
    why_machine_cannot=
        "**Nobody has pressed an arrow key in a real window on this project.** "
        "The pack drives `q` as terminal input, which proves the game's "
        "read-key path and quit condition — but not that a key from a real "
        "keyboard reaches the same code. Arrow keys arrive as escape "
        "sequences and have never been exercised that way at all.",
)

THE_SHELL_AFTERWARDS = HumanCheck(
    name="the shell afterwards",
    codes=("END-6",),
    question="If the window survives the game, is the terminal usable?",
    steps=(
        "Run the game process directly rather than through the launcher: "
        "`python3 -m terminalgame.game_main` in a terminal of at least 40x30.",
        "Quit it with `q`.",
        "Type something at the prompt.",
    ),
    look_for=(
        "what you type APPEARING — echo back on, cursor visible again",
        "the shell responding normally to a command",
    ),
    why_machine_cannot=
        "Caution C10 is tested against a pseudo-terminal, down to the one "
        "termios bit that does not come back (PENDIN, transient kernel state "
        "rather than a mode the player chose). What a pseudo-terminal cannot "
        "tell you is whether the PERSON's shell is usable afterwards.",
)

PERMISSION = HumanCheck(
    name="the Automation permission",
    codes=("Q2",),
    question="What happens on a machine where Terminal automation has NOT "
             "been granted?",
    steps=(
        "On a machine that has never granted it — or after revoking it in "
        "System Settings > Privacy & Security > Automation — run the pack.",
        "Answer the permission prompt with 'Don't Allow'.",
    ),
    look_for=(
        "the game still opening and still playable, at the documented default "
        "position, rather than the launcher aborting",
        "no window left behind either way",
    ),
    why_machine_cannot=
        "**No agent on this team can grant this permission, revoke it, or "
        "confirm it was granted.** Every measurement on this project was taken "
        "on a machine where it had already been granted. The refusal PATH is "
        "tested by injection; a real refusal is not, and Q2 remains an "
        "assumption rather than a ruling.",
)

SAVED_PREFERENCES = HumanCheck(
    name="the player's own Terminal settings",
    codes=("Q3",),
    question="Were the player's saved Terminal preferences left alone?",
    steps=(
        "After running the pack, open a NEW ordinary Terminal window.",
        "Check its font, size, colours and title.",
    ),
    look_for=(
        "an ordinary window exactly as it was before — the game's 40x30 black "
        "settings applied to its own window only",
    ),
    why_machine_cannot=
        "Assumption A3 forbids changing the player's profile and the launcher "
        "sets everything on one window rather than on the settings. That it "
        "did not leak is a claim about the person's machine, and the person is "
        "the one who knows what it looked like before.",
)

ENDINGS = HumanCheck(
    name="how it ends",
    codes=("END-1", "END-2", "END-4", "END-5", "STAT-3"),
    question="Do the two endings look right, and does the picture freeze?",
    steps=(
        "Play until the ghost catches you.",
        "Play again and eat every dot.",
    ),
    look_for=(
        "on a loss, the GHOST drawn where the two met, not the player",
        "the picture stopping and staying still — nothing moving afterwards",
        "the status line naming which ending happened and the final score",
        "`q` still working afterwards, and nothing else doing anything",
    ),
    why_machine_cannot=
        "The rules and the draw order are tested exhaustively in the domain "
        "and the presentation. What is not tested is that a person watching a "
        "real window sees a picture that has clearly stopped rather than one "
        "that looks stuck.",
)


#: Every check, in the order WI-14b should work through them: the ones that
#: need the window open first, then the ones that need a game played, then the
#: ones that need a different machine or a changed setting.
ALL = (
    COLOURS,
    FONT_AND_SIZE,
    TITLE_BAR,
    WINDOW_PLACEMENT,
    FLICKER_AND_CURSOR,
    A_REAL_KEYBOARD,
    ENDINGS,
    THE_FEEL_OF_IT,
    GHOST_CONFINEMENT,
    THE_SHELL_AFTERWARDS,
    SAVED_PREFERENCES,
    PERMISSION,
)

#: Requirement codes that **cannot** be settled without a person, gathered from
#: the register. A test checks this against what the exercises claim to cover,
#: so neither half can quietly grow to overlap the other.
CODES_NEEDING_A_PERSON = tuple(sorted(
    set(code for check in ALL for code in check.codes)))


def render(checks=ALL):
    """The register as text, for a person to work through."""
    lines = [
        "THE HUMAN CHECKS",
        "=" * 70,
        "",
        "%d checks, covering %d requirement codes." % (
            len(checks), len(set(c for k in checks for c in k.codes))),
        "",
        "None of these is recorded as verified anywhere, and none of them can",
        "be. They are what is left when everything a machine can check has",
        "been checked.",
        "",
    ]
    for number, check in enumerate(checks, 1):
        lines.append("-" * 70)
        lines.append("%d. %s   [%s]" % (number, check.name.upper(),
                                        ", ".join(check.codes)))
        lines.append("")
        lines.append("   %s" % check.question)
        lines.append("")
        lines.append("   Do this:")
        for step in check.steps:
            lines.append("     - %s" % step)
        lines.append("")
        lines.append("   Look for:")
        for item in check.look_for:
            lines.append("     - %s" % item)
        lines.append("")
        lines.append("   Why no machine can answer it:")
        lines.append("     %s" % check.why_machine_cannot)
        lines.append("")
    lines.append("-" * 70)
    return "\n".join(lines)
