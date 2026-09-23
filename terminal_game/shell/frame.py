"""The shape of a frame the shell paints, and the check that a frame has it. Pure.

A frame is 30 rows of 40 cells. Each cell is a pair ``(character, role)``:
``character`` is a one-character string and ``role`` is one of the six role
names in :mod:`terminal_game.shell.palette` (a ``str`` subclass such as a
``StrEnum`` member works too). Row 0 is the top of the window, cell 0 the
left edge.
"""

from collections.abc import Sequence

from terminal_game.shell.palette import COLOURS, ROLES

COLUMNS = 40
ROWS = 30

Cell = tuple[str, str]
Frame = Sequence[Sequence[Cell]]


def check_frame(frame: Frame) -> list[list[Cell]]:
    """Return ``frame`` as a list of lists, or raise ``ValueError`` saying what is wrong.

    The whole frame is checked before anything is returned, so a caller that
    paints only what this returns can never paint part of a bad frame.
    """
    try:
        rows = list(frame)
    except TypeError:
        raise ValueError(f"a frame is a sequence of {ROWS} rows, not {type(frame).__name__}") from None
    if len(rows) != ROWS:
        raise ValueError(f"a frame has {ROWS} rows, this one has {len(rows)}")
    checked: list[list[Cell]] = []
    for r, row in enumerate(rows):
        try:
            cells = list(row)
        except TypeError:
            raise ValueError(f"row {r} is {type(row).__name__}, not a sequence of {COLUMNS} cells") from None
        if len(cells) != COLUMNS:
            raise ValueError(f"row {r} has {len(cells)} cells, a row has {COLUMNS}")
        out: list[Cell] = []
        for c, cell in enumerate(cells):
            try:
                character, role = cell
            except (TypeError, ValueError):
                raise ValueError(f"cell ({c}, {r}) is {cell!r}, not a (character, role) pair") from None
            if not isinstance(character, str) or len(character) != 1:
                raise ValueError(f"cell ({c}, {r}) holds {character!r}, not exactly one character")
            if not isinstance(role, str) or role not in COLOURS:
                raise ValueError(f"cell ({c}, {r}) has unknown role {role!r}; expected one of {ROLES}")
            out.append((character, role))
        checked.append(out)
    return checked


def blank_frame() -> list[list[Cell]]:
    """A frame with nothing painted: every cell a blank on the background."""
    return [[(" ", "background")] * COLUMNS for _ in range(ROWS)]
