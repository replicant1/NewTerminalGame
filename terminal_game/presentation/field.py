"""The 40 x 30 field of glyph-and-colour — everything the player sees, as data.

This is the seam between the part of Presentation that decides *what* the
picture is and the part that turns it into pixels.  WI-4 composes rows 0-28 and
WI-12 supplies row 29; both produce one of these, and
``terminal_game.presentation.surface`` is the only thing that paints it.

**SCRN-2 is enforced here, not merely observed.**

    *"Everything is drawn from characters — there are no images."*

A :class:`Cell` is one character and two colours.  There is no other shape a
cell can take, so there is nothing for an image, a line, an arc or a polygon to
travel in.  The plan makes this a ground rule in section 1.4 because under
candidate 2 the medium no longer enforces it; making the *data* incapable of
carrying anything else is how a rule becomes a fact again.  A cell's glyph must
be exactly one character: not two, because two characters in one cell would
overflow into the next; and not zero, because a cell with nothing in it is a
space, which is a character, and saying so keeps every cell the same kind of
thing.

**The field is 40 x 30 and no other shape is representable.**  There is no
width or height parameter.  WIN-2 fixes the grid, and a field of some other
size could only arrive here by mistake.
"""

from __future__ import annotations

from typing import Iterator, List, Sequence, Tuple

from terminal_game.presentation import palette
from terminal_game.presentation.metrics import COLUMNS, ROWS, CellMetrics

#: The character a cell holds when there is nothing to show in it.
BLANK = " "


class Cell(object):
    """One character cell: a single glyph, its colour, and the colour behind it.

    Cells compare by value, so a painter can ask "did this cell change?" and
    get an answer about the picture rather than about object identity.
    """

    __slots__ = ("glyph", "colour", "background")

    def __init__(
        self,
        glyph: str = BLANK,
        colour: str = palette.GROUND,
        background: str = palette.GROUND,
    ) -> None:
        if not isinstance(glyph, str):
            raise TypeError(
                "a cell's glyph must be a string of one character, not {!r}; "
                "SCRN-2 says everything is drawn from characters".format(glyph)
            )
        if len(glyph) != 1:
            raise ValueError(
                "a cell holds exactly one character, not {!r} ({} characters); "
                "two would overflow into the next cell and none is a space, "
                "which is itself a character".format(glyph, len(glyph))
            )
        if not palette.is_colour(colour):
            raise ValueError(
                "a cell's colour must be an #rrggbb triple, not {!r}; see "
                "terminal_game.presentation.palette".format(colour)
            )
        if not palette.is_colour(background):
            raise ValueError(
                "a cell's background must be an #rrggbb triple, not {!r}; see "
                "terminal_game.presentation.palette".format(background)
            )
        self.glyph = glyph
        self.colour = colour
        self.background = background

    def is_blank(self) -> bool:
        """Whether this cell shows nothing: a space on the ground colour."""
        return (
            self.glyph == BLANK
            and self.background == palette.GROUND
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Cell):
            return NotImplemented
        return (self.glyph, self.colour, self.background) == (
            other.glyph,
            other.colour,
            other.background,
        )

    def __ne__(self, other: object) -> bool:
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __hash__(self) -> int:
        return hash((self.glyph, self.colour, self.background))

    def __repr__(self) -> str:
        return "Cell({!r}, colour={!r}, background={!r})".format(
            self.glyph, self.colour, self.background
        )


#: The cell every field starts out full of: a space on the black ground.
EMPTY_CELL = Cell()


class Field(object):
    """A 40 x 30 grid of :class:`Cell`, and nothing else.

    Built empty and filled in; there is no constructor taking a size, because
    WIN-2 fixes the size.  Indexing is ``field[column, row]`` throughout the
    project — column first, the way a screen coordinate reads — and an
    off-grid index raises rather than wrapping.
    """

    __slots__ = ("_cells",)

    def __init__(self) -> None:
        # One flat list, row-major.  A list of lists would let a caller take a
        # row and mutate it behind the field's back; this cannot be reached
        # except through the checked accessors below.
        self._cells = [EMPTY_CELL] * (COLUMNS * ROWS)  # type: List[Cell]

    # -- reading and writing one cell --------------------------------------

    def __getitem__(self, where: Tuple[int, int]) -> Cell:
        column, row = where
        CellMetrics.check_in_grid(column, row)
        return self._cells[row * COLUMNS + column]

    def __setitem__(self, where: Tuple[int, int], cell: Cell) -> None:
        column, row = where
        CellMetrics.check_in_grid(column, row)
        if not isinstance(cell, Cell):
            raise TypeError(
                "a field holds Cell objects, not {!r}; everything the player "
                "sees is a character (SCRN-2)".format(cell)
            )
        self._cells[row * COLUMNS + column] = cell

    # -- reading and writing a run -----------------------------------------

    def write(
        self,
        column: int,
        row: int,
        text: str,
        colour: str,
        background: str = palette.GROUND,
    ) -> None:
        """Put ``text`` into consecutive cells, one character to a cell.

        The convenience WI-12 wants for the status line and WI-4 wants for a
        run of wall glyphs.  It is not a new way to draw: it makes one
        :class:`Cell` per character and goes through :meth:`__setitem__`, so a
        run that would fall off the end of the row raises exactly as a single
        off-grid write would.
        """
        for offset, character in enumerate(text):
            self[column + offset, row] = Cell(character, colour, background)

    def row_text(self, row: int) -> str:
        """The glyphs of one row as a string — what that row reads as.

        This is how a test asks "what does the status line say?" without
        knowing anything about cells, and how WI-4's and WI-12's tests can
        assert an exact string.
        """
        CellMetrics.check_in_grid(0, row)
        start = row * COLUMNS
        return "".join(cell.glyph for cell in self._cells[start : start + COLUMNS])

    def rows(self) -> Iterator[str]:
        """Every row's text, top to bottom."""
        for row in range(ROWS):
            yield self.row_text(row)

    # -- reading the whole thing -------------------------------------------

    def cells(self) -> Iterator[Tuple[int, int, Cell]]:
        """Every cell as ``(column, row, cell)``, row-major from the top-left."""
        for row in range(ROWS):
            for column in range(COLUMNS):
                yield column, row, self._cells[row * COLUMNS + column]

    def snapshot(self) -> Sequence[Cell]:
        """A frozen copy of every cell, row-major.

        The painter keeps one of these to work out what changed between one
        frame and the next.  It is a tuple, so holding it cannot be a way of
        reaching back into the field it came from.
        """
        return tuple(self._cells)

    def differences(self, other: "Field") -> Iterator[Tuple[int, int, Cell]]:
        """Every cell of this field that differs from ``other``'s.

        Yields ``(column, row, cell)`` with this field's cell — the new one.
        """
        for row in range(ROWS):
            base = row * COLUMNS
            for column in range(COLUMNS):
                mine = self._cells[base + column]
                if mine != other._cells[base + column]:
                    yield column, row, mine

    # -- housekeeping ------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Field):
            return NotImplemented
        return self._cells == other._cells

    def __ne__(self, other: object) -> bool:
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __repr__(self) -> str:
        return "Field({} x {})".format(COLUMNS, ROWS)
