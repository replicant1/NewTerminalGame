"""Frames the shell's desktop tests and the WI-3 test card paint. Test support only; pure.

The specimen picture comes straight from ``docs/FUNCTIONAL_REQUIREMENTS.md``
§3, so the test card is the specification's own picture, not a copy of it.
Roles are assigned the way the specimen's prose describes them (SCRN-3..6):
box-drawing and ``■`` walls, ``▪`` dots, ``▐█▌`` the player, ``▗█▖`` the
ghost, the bottom row the status line.
"""

from pathlib import Path

from terminal_game.shell.frame import COLUMNS, ROWS
from terminal_game.shell.palette import BACKGROUND, DOT, GHOST, PLAYER, ROLES, STATUS, WALL

REPO = Path(__file__).resolve().parent.parent
SPEC = REPO / "docs" / "FUNCTIONAL_REQUIREMENTS.md"

VISIBLE_ROLES = tuple(r for r in ROLES if r != BACKGROUND)

#: Every character the game draws: walls, the lone block, dots, player and ghost.
GAME_GLYPHS = "═║╔╗╚╝╠╣╦╩╬■▪▐█▌▗▖"

#: Printable ASCII, the box-drawing and block-element ranges, and the game's own glyphs.
ALPHABET = (
    "".join(chr(c) for c in range(0x21, 0x7F))
    + "".join(chr(c) for c in range(0x2500, 0x25A0))
    + "■▪"
)


def specimen_lines() -> list[str]:
    """The 30 lines of the specimen picture, annotations removed, padded to 40."""
    text = SPEC.read_text(encoding="utf-8")
    block = text.split("A game in progress looks like this:", 1)[1].split("```", 2)[1]
    lines = [ln for ln in block.split("\n") if ln.strip()]
    lines = [ln.split("   ←")[0].rstrip() for ln in lines]
    if len(lines) != ROWS:
        raise ValueError(f"specimen has {len(lines)} lines, expected {ROWS}")
    return [ln.ljust(COLUMNS) for ln in lines]


def specimen_frame():
    """The specimen as a frame, each character in the role its prose gives it."""
    lines = specimen_lines()
    frame = []
    for r, line in enumerate(lines):
        row = []
        for c, ch in enumerate(line):
            if r == ROWS - 1:
                role = STATUS if ch != " " else BACKGROUND
            elif ch == " ":
                role = BACKGROUND
            elif ch == "▪":
                role = DOT
            elif ch in "▐▌" or (ch == "█" and line[c - 1] == "▐"):
                role = PLAYER
            elif ch in "▗▖" or (ch == "█" and line[c - 1] == "▗"):
                role = GHOST
            else:
                role = WALL
            row.append((ch, role))
        frame.append(row)
    return frame


def blank():
    return [[(" ", BACKGROUND)] * COLUMNS for _ in range(ROWS)]


def role_blocks(k: int):
    """A full block in every cell, cell (c, r) in role ``ROLES[(c + r + k) % 6]``.

    Over k = 0..5 every cell shows every role once.
    """
    return [[("█", ROLES[(c + r + k) % len(ROLES)]) for c in range(COLUMNS)] for r in range(ROWS)]


def alphabet(k: int):
    """:data:`ALPHABET` laid out cell by cell, repeating; cell i in visible role (i + k) % 5.

    Neighbouring cells always differ in role, so a glyph straying into its
    neighbour shows up as the wrong colour there.
    """
    frame = []
    for r in range(ROWS):
        row = []
        for c in range(COLUMNS):
            i = r * COLUMNS + c
            row.append((ALPHABET[i % len(ALPHABET)], VISIBLE_ROLES[(i + k + r) % len(VISIBLE_ROLES)]))
        frame.append(row)
    return frame


def border(role: str = STATUS):
    """A full block in every cell of the outer ring, nothing inside it."""
    return [
        [("█", role) if r in (0, ROWS - 1) or c in (0, COLUMNS - 1) else (" ", BACKGROUND) for c in range(COLUMNS)]
        for r in range(ROWS)
    ]


def shifted_specimen():
    """A second picture unlike the specimen in most cells: shifted one row and one cell, roles rotated."""
    base = specimen_frame()
    rotate = {WALL: GHOST, DOT: STATUS, PLAYER: WALL, GHOST: DOT, STATUS: PLAYER, BACKGROUND: BACKGROUND}
    frame = []
    for r in range(ROWS):
        row = []
        for c in range(COLUMNS):
            ch, role = base[(r + 1) % ROWS][(c + 1) % COLUMNS]
            if ch == " ":
                ch, role = "▪", DOT
            else:
                role = rotate[role]
            row.append((ch, role))
        frame.append(row)
    return frame
