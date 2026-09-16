"""WI-1 — the picture as a value.

A :class:`Frame` is what is on screen: 30 rows of 40 cells, each cell one
character in one named colour.  It is immutable, comparable and renders to
plain text, so that every later picture test is a text comparison with no
window and no toolkit anywhere near it.

Geometry, measured from the specimen picture in ``FUNCTIONAL_REQUIREMENTS.md``
(implementation plan, section 5):

* 30 rows — rows 0..28 are the maze, row 29 is the status line (SCRN-1).
* Every maze row is **37** characters wide: 19 squares at two columns each,
  less the final connector column.  Square *c* is drawn at column ``2 * c``;
  the odd columns are connectors.
* That leaves a **3**-column blank margin at the right of a 40-column window.
  (The architecture's MAZE-1 prose says 38 and 2; its own measurement V8 and
  the plan both say 37 and 3.  37 and 3 is what we build — contradiction C-1.)

**Everything on screen is a character in a cell (SCRN-2, caution C5).**  There
is no way to put anything else in a frame: a cell holds exactly one character.
Keep it that way — under the single-process windowed architecture the medium no
longer enforces it for you.

This module imports nothing but the standard library and names no toolkit.
"""

from __future__ import annotations

from enum import Enum
from typing import Iterable, List, NamedTuple, Sequence, Tuple

__all__ = [
    "FRAME_ROWS",
    "FRAME_COLUMNS",
    "MAZE_ROWS",
    "MAZE_COLUMNS",
    "STATUS_ROW",
    "RIGHT_MARGIN_COLUMNS",
    "Colour",
    "Cell",
    "BLANK",
    "Frame",
    "FrameBuilder",
]


#: Rows in a frame: 29 of maze and one status line (SCRN-1, WIN-2).
FRAME_ROWS = 30

#: Cells across a frame (WIN-2).
FRAME_COLUMNS = 40

#: Rows of the frame the maze occupies — 0 .. ``MAZE_ROWS`` - 1.
MAZE_ROWS = 29

#: The row the status line occupies, and nothing else ever (STAT-1).
STATUS_ROW = 29

#: Columns of each maze row that carry maze: 19 squares * 2, less the last
#: connector column.  Measured from the specimen picture, not asserted in prose.
MAZE_COLUMNS = 37

#: The blank margin down the right-hand edge of the window (MAZE-1).
RIGHT_MARGIN_COLUMNS = FRAME_COLUMNS - MAZE_COLUMNS


class Colour(Enum):
    """The closed vocabulary of colours a cell may be drawn in.

    These are *names*, not pixel values: choosing what blue looks like on a
    real surface belongs to the shell (WI-2), not here.  There are six and
    there are deliberately no more — every colour the requirements name, and
    nothing else.
    """

    WALL_BLUE = "wall blue"            # SCRN-3, the walls
    DOT_GOLD = "dim gold"              # SCRN-4, the dots
    PLAYER_YELLOW = "bright yellow"    # SCRN-5, the player
    GHOST_PINK = "pink"                # SCRN-5, the ghost
    STATUS_CYAN = "cyan"               # SCRN-6, the status line
    GROUND_BLACK = "black"             # WIN-2, the ground


class Cell(NamedTuple):
    """One character in one named colour.

    A cell is only well formed when its glyph is exactly one character and its
    colour is a member of :class:`Colour`; :class:`Frame` and
    :class:`FrameBuilder` refuse anything else rather than accepting it
    quietly.
    """

    glyph: str
    colour: Colour


#: The empty cell — a space on the black ground.
BLANK = Cell(" ", Colour.GROUND_BLACK)


def _validated(cell: object, where: str) -> Cell:
    """Return *cell* if it is a well-formed :class:`Cell`, else raise."""
    if not isinstance(cell, Cell):
        raise ValueError(
            "{0} must be a Cell, not {1!r}".format(where, cell)
        )
    if not isinstance(cell.colour, Colour):
        raise ValueError(
            "{0}: {1!r} is not one of the {2} named colours ({3})".format(
                where,
                cell.colour,
                len(Colour),
                ", ".join(member.name for member in Colour),
            )
        )
    if not isinstance(cell.glyph, str) or len(cell.glyph) != 1:
        raise ValueError(
            "{0}: a cell holds exactly one character, not {1!r}".format(
                where, cell.glyph
            )
        )
    return cell


def _check_position(row: object, column: object) -> Tuple[int, int]:
    """Refuse any position that is not inside the frame.

    Negatives are refused rather than wrapping round, which is how an
    off-by-one in a caller would otherwise draw silently in the wrong place.
    """
    if isinstance(row, bool) or not isinstance(row, int):
        raise TypeError("row must be an int, not {0!r}".format(row))
    if isinstance(column, bool) or not isinstance(column, int):
        raise TypeError("column must be an int, not {0!r}".format(column))
    if not 0 <= row < FRAME_ROWS:
        raise IndexError(
            "row {0} is outside the frame (0..{1})".format(row, FRAME_ROWS - 1)
        )
    if not 0 <= column < FRAME_COLUMNS:
        raise IndexError(
            "column {0} is outside the frame (0..{1})".format(
                column, FRAME_COLUMNS - 1
            )
        )
    return row, column


class Frame:
    """An immutable 30 x 40 picture.

    Two frames built the same way are equal; two that differ in a single
    glyph, or in a single colour, are not.  A frame renders to text with
    :meth:`to_text`, which keeps every column — including the blank right-hand
    margin — so a picture can be asserted character for character.
    """

    __slots__ = ("_rows",)

    def __init__(self, rows: Iterable[Iterable[Cell]]) -> None:
        materialised = [tuple(row) for row in rows]
        if len(materialised) != FRAME_ROWS:
            raise ValueError(
                "a frame is {0} rows, not {1}".format(
                    FRAME_ROWS, len(materialised)
                )
            )
        built: List[Tuple[Cell, ...]] = []
        for index, row in enumerate(materialised):
            if len(row) != FRAME_COLUMNS:
                raise ValueError(
                    "row {0} is {1} cells, not {2}".format(
                        index, len(row), FRAME_COLUMNS
                    )
                )
            built.append(
                tuple(
                    _validated(cell, "row {0} column {1}".format(index, column))
                    for column, cell in enumerate(row)
                )
            )
        self._rows = tuple(built)

    # -- reading ---------------------------------------------------------

    @classmethod
    def blank(cls) -> "Frame":
        """A frame of nothing but black ground."""
        return cls([[BLANK] * FRAME_COLUMNS for _ in range(FRAME_ROWS)])

    @classmethod
    def from_text(
        cls, text: str, colour: Colour = Colour.GROUND_BLACK
    ) -> "Frame":
        """Build a frame from 30 lines of text, all in one colour.

        Short lines are padded out to 40 columns with blank ground, so that a
        test can write an expected picture without counting trailing spaces.
        A line longer than 40 characters, or a count other than 30 lines, is
        refused.  Colours are not expressible this way; this is a convenience
        for picture comparisons, not a substitute for :class:`FrameBuilder`.
        """
        if not isinstance(colour, Colour):
            raise ValueError(
                "{0!r} is not one of the named colours".format(colour)
            )
        lines = text.split("\n")
        if len(lines) != FRAME_ROWS:
            raise ValueError(
                "a frame is {0} lines, not {1}".format(FRAME_ROWS, len(lines))
            )
        rows: List[List[Cell]] = []
        for index, line in enumerate(lines):
            if len(line) > FRAME_COLUMNS:
                raise ValueError(
                    "line {0} is {1} characters, more than the {2} "
                    "columns of a frame".format(index, len(line), FRAME_COLUMNS)
                )
            row = [Cell(character, colour) for character in line]
            row.extend([BLANK] * (FRAME_COLUMNS - len(line)))
            rows.append(row)
        return cls(rows)

    @property
    def rows(self) -> Tuple[Tuple[Cell, ...], ...]:
        """Every cell, as a tuple of 30 tuples of 40 cells."""
        return self._rows

    def cell_at(self, row: int, column: int) -> Cell:
        """The cell at *row*, *column*; a position outside the frame raises."""
        _check_position(row, column)
        return self._rows[row][column]

    def row_text(self, row: int) -> str:
        """Row *row* as 40 characters, trailing blanks and all."""
        if isinstance(row, bool) or not isinstance(row, int):
            raise TypeError("row must be an int, not {0!r}".format(row))
        if not 0 <= row < FRAME_ROWS:
            raise IndexError(
                "row {0} is outside the frame (0..{1})".format(
                    row, FRAME_ROWS - 1
                )
            )
        return "".join(cell.glyph for cell in self._rows[row])

    def to_text(self) -> str:
        """The whole picture as 30 lines of exactly 40 characters.

        Nothing is stripped: the blank right-hand margin is three real spaces
        on every maze row, because that is what is on screen.
        """
        return "\n".join(
            "".join(cell.glyph for cell in row) for row in self._rows
        )

    def colour_at(self, row: int, column: int) -> Colour:
        """The colour of the cell at *row*, *column*."""
        return self.cell_at(row, column).colour

    # -- value semantics -------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Frame):
            return NotImplemented
        return self._rows == other._rows

    def __ne__(self, other: object) -> bool:
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __hash__(self) -> int:
        return hash(self._rows)

    def __repr__(self) -> str:
        return "Frame({0} x {1})".format(FRAME_ROWS, FRAME_COLUMNS)


class FrameBuilder:
    """Fills in a picture cell by cell and hands over a :class:`Frame`.

    The builder is the mutable half of the seam; the frame it builds is not.
    A frame already built never changes, whatever the builder does next.
    """

    __slots__ = ("_rows",)

    def __init__(self, ground: Cell = BLANK) -> None:
        _validated(ground, "the ground cell")
        self._rows: List[List[Cell]] = [
            [ground] * FRAME_COLUMNS for _ in range(FRAME_ROWS)
        ]

    def cell_at(self, row: int, column: int) -> Cell:
        """Read back what has been placed so far."""
        _check_position(row, column)
        return self._rows[row][column]

    def set_cell(self, row: int, column: int, glyph: str, colour: Colour) -> None:
        """Place one character in one colour.  A bad position or colour raises."""
        _check_position(row, column)
        cell = _validated(
            Cell(glyph, colour), "row {0} column {1}".format(row, column)
        )
        self._rows[row][column] = cell

    def write(self, row: int, column: int, text: str, colour: Colour) -> None:
        """Place *text* one character to a cell, starting at *column*.

        Nothing is written at all if the text would run past the right-hand
        edge — a partial write is the sort of thing that shows up three work
        items later as a picture that is nearly right.
        """
        if not isinstance(text, str):
            raise ValueError("text must be a str, not {0!r}".format(text))
        _check_position(row, column)
        if not isinstance(colour, Colour):
            raise ValueError(
                "{0!r} is not one of the named colours".format(colour)
            )
        end = column + len(text)
        if end > FRAME_COLUMNS:
            raise IndexError(
                "writing {0} characters at column {1} would run to column "
                "{2}, past the {3} columns of a frame".format(
                    len(text), column, end - 1, FRAME_COLUMNS
                )
            )
        for offset, character in enumerate(text):
            self._rows[row][column + offset] = Cell(character, colour)

    def place_row(self, row: int, cells: Sequence[Cell]) -> None:
        """Put a whole row in place, as a value handed over by someone else.

        This is how row 29 arrives: the status line owns that row and produces
        it; whoever is composing rows 0..28 places it and writes nothing there
        itself (STAT-1).
        """
        if isinstance(row, bool) or not isinstance(row, int):
            raise TypeError("row must be an int, not {0!r}".format(row))
        if not 0 <= row < FRAME_ROWS:
            raise IndexError(
                "row {0} is outside the frame (0..{1})".format(
                    row, FRAME_ROWS - 1
                )
            )
        placed = list(cells)
        if len(placed) != FRAME_COLUMNS:
            raise ValueError(
                "a row is {0} cells, not {1}".format(FRAME_COLUMNS, len(placed))
            )
        self._rows[row] = [
            _validated(cell, "row {0} column {1}".format(row, column))
            for column, cell in enumerate(placed)
        ]

    def build(self) -> Frame:
        """The finished picture, as an immutable value."""
        return Frame(self._rows)
