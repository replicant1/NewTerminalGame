"""WIN-2 as arithmetic — how a grid of character cells becomes a pixel rectangle.

    *"The window is exactly 40 characters wide and 30 rows deep, in a
    fixed-width typeface large enough to read comfortably, on a black
    background."*

Under candidate 2 that size is **derived, not native**.  There is no terminal
to be told "40 columns"; there is a pixel rectangle computed from the font's
cell metrics, and a font substitution silently changes it.  The plan says so in
section 2 and calls the calculation load-bearing.  This module is that
calculation, and it is deliberately the part with no toolkit in it: the
arithmetic can be checked exhaustively in a suite that never opens a window,
and only the two numbers it starts from have to come from a real font.

Those two numbers are **advance** (how far the pen moves after one character)
and **linespace** (how far it moves after one line).  S-1 measured them for the
font this project uses, and AMEND-6 re-measured them on the Tk the project now
runs on:

    Menlo 12 -> advance 10, linespace 19 -> 40 x 30 cells is 400 x 570 pixels

**The nominal size changed and the cell did not.**  S-1 measured Menlo 16 on
Tk 8.5.9, which took a point as a pixel; Tk 9.0.4 applies the 96/72 scaling a
point is owed, so the same cell is asked for as 12.  The pixels are identical
— cell 10 x 19, window 400 x 570, the glyph bboxes unchanged — which is why
human item 3's verdict on the type size survives the move.  ``FONT_SIZE`` is a
number in the toolkit's units, not a size on the glass, and only the second of
those is what WIN-2 and a human care about.

AMEND-6 also re-measured the thing that makes 12 the ceiling: at 12 and below,
a 40-character row drawn as one string lands on the same pixels as 40
characters placed one cell at a time, and above 12 it does not.
``EXACT_GRID_CEILING`` records that, because it is the reason the size is not
simply "whatever looks big enough".

Nothing here knows what a canvas is.  :class:`CellMetrics` is handed its two
numbers by whoever measured them, which in production is
``terminal_game.presentation.surface`` and in a test is the test.
"""

from __future__ import annotations

from typing import Tuple

# --------------------------------------------------------------------------
# The grid, which is fixed by WIN-2 and is not a parameter
# --------------------------------------------------------------------------

#: WIN-2's width, in character cells.
COLUMNS = 40

#: WIN-2's depth, in character cells.  SCRN-1 splits these into rows 0-28 for
#: the maze and row 29 for the status line, but that is a matter for WI-4 and
#: WI-12; here it is simply how many rows there are.
ROWS = 30

# --------------------------------------------------------------------------
# The font, which is fixed by measurement rather than by taste
# --------------------------------------------------------------------------

#: The only family on this machine that owns every glyph the game draws with no
#: substitution anywhere.  Measured by S-1 across 180 families:
#: ``docs/findings/S-1-tk-headless.md`` section 2.
FONT_FAMILY = "Menlo"

#: Chosen because it is the largest Menlo size whose cell grid is exact — see
#: :data:`EXACT_GRID_CEILING`.  It is also assumption P4, "large enough to read
#: comfortably", which no test can settle; a human looks at it in WI-17 and
#: WI-19 changes this one constant if the answer is no.
#:
#: **12 here is the 16 S-1 recommended.**  It is stated in the toolkit's units,
#: which changed under it — see the module docstring.  The cell it produces is
#: unchanged, so **human item 3 is neither answered nor invalidated by the
#: move: it is still owed.**  An earlier draft of this comment said the cell
#: was one a human had already looked at, which is not what the record says —
#: the only time a person has looked at this window it was blank, which is the
#: defect AMEND-6 fixes.  WI-19 reads this constant, so it must not be told
#: the question was settled.
FONT_SIZE = 12

#: Above this size a 40-character row drawn as one string no longer lands on
#: the same pixels as 40 characters placed one at a time — AMEND-6 measured
#: drifts of 4 to 38 px over 40 cells at every size from 13 to 36.  Below and
#: at it, a painter may place per cell, per row, or per changed cell and get
#: the same picture.  If :data:`FONT_SIZE` is ever raised past this, the
#: painter loses that freedom and must place every cell individually.
EXACT_GRID_CEILING = 12


class CellMetrics(object):
    """The pixel size of one character cell, and everything that follows from it.

    ``advance`` is the horizontal pen movement for one character and
    ``linespace`` the vertical movement for one line, both in whole pixels, as
    a font reports them.  Both must be positive: a zero or negative cell would
    make every cell in a row share one origin, and the picture would be a
    single column of overprinted characters rather than a grid.
    """

    __slots__ = ("advance", "linespace")

    def __init__(self, advance: int, linespace: int) -> None:
        if advance <= 0:
            raise ValueError(
                "advance must be a positive number of pixels, not {!r}; a cell "
                "with no width gives every column the same origin".format(advance)
            )
        if linespace <= 0:
            raise ValueError(
                "linespace must be a positive number of pixels, not {!r}; a cell "
                "with no height gives every row the same origin".format(linespace)
            )
        self.advance = int(advance)
        self.linespace = int(linespace)

    # -- the size of things ------------------------------------------------

    def pixel_size(self, columns: int = COLUMNS, rows: int = ROWS) -> Tuple[int, int]:
        """The pixel rectangle that holds ``columns`` x ``rows`` cells.

        This is WIN-2's window size.  With the defaults it is the only answer
        this project cares about, and :func:`window_pixel_size` is the name for
        that case; the parameters exist so the arithmetic can be checked at
        sizes other than the one the game happens to use.
        """
        if columns < 0 or rows < 0:
            raise ValueError(
                "a grid cannot have {!r} columns and {!r} rows".format(columns, rows)
            )
        return (columns * self.advance, rows * self.linespace)

    def window_pixel_size(self) -> Tuple[int, int]:
        """WIN-2's 40 x 30 grid as a pixel rectangle.  Menlo 12 gives 400 x 570."""
        return self.pixel_size(COLUMNS, ROWS)

    # -- where things go ---------------------------------------------------

    def cell_origin(self, column: int, row: int) -> Tuple[int, int]:
        """The top-left pixel of one cell, for a painter anchoring north-west.

        Cells abut exactly: the cell at column ``c`` starts where the cell at
        ``c - 1`` ends, with no gap and no overlap.  S-1 confirmed that on a
        real canvas at Menlo 16 — a glyph at x = 0 has bbox ``[-1, 0, 11, 19]``
        and the same glyph at x = 10 has ``[9, 0, 21, 19]``.  AMEND-6 re-read
        both bboxes at Menlo 12 on Tk 9.0.4 and got the same two rectangles.
        """
        self.check_in_grid(column, row)
        return (column * self.advance, row * self.linespace)

    def cell_bounds(self, column: int, row: int) -> Tuple[int, int, int, int]:
        """One cell as ``(left, top, right, bottom)``, right and bottom exclusive."""
        left, top = self.cell_origin(column, row)
        return (left, top, left + self.advance, top + self.linespace)

    # -- what counts as inside ---------------------------------------------

    @staticmethod
    def in_grid(column: int, row: int) -> bool:
        """Whether ``(column, row)`` names a cell of the 40 x 30 grid."""
        return 0 <= column < COLUMNS and 0 <= row < ROWS

    @staticmethod
    def check_in_grid(column: int, row: int) -> None:
        """Raise :class:`IndexError` unless ``(column, row)`` is a cell of the grid.

        The grid is 40 x 30 and nothing else, so an off-grid coordinate is a
        mistake to be reported rather than a request to grow.  Negative indices
        are off-grid too: Python's "counts from the end" is a convenience that
        would quietly paint a cell at the wrong end of the row.
        """
        if not CellMetrics.in_grid(column, row):
            raise IndexError(
                "(column {}, row {}) is outside the {} x {} grid; columns run "
                "0 to {} and rows 0 to {}, and negative indices do not wrap".format(
                    column, row, COLUMNS, ROWS, COLUMNS - 1, ROWS - 1
                )
            )

    # -- housekeeping ------------------------------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CellMetrics):
            return NotImplemented
        return (self.advance, self.linespace) == (other.advance, other.linespace)

    def __ne__(self, other: object) -> bool:  # Python 3.9 still wants this pair
        result = self.__eq__(other)
        if result is NotImplemented:
            return result
        return not result

    def __hash__(self) -> int:
        return hash((self.advance, self.linespace))

    def __repr__(self) -> str:
        return "CellMetrics(advance={}, linespace={})".format(
            self.advance, self.linespace
        )


#: The metrics measured for :data:`FONT_FAMILY` at :data:`FONT_SIZE` — by S-1
#: as Menlo 16 on Tk 8.5.9, and by AMEND-6 as Menlo 12 on Tk 9.0.4, which are
#: the same cell asked for in the two toolkits' different units.
#:
#: This is a **record of a measurement, not a substitute for one.**  The
#: surface measures the real font at start-up and uses what it finds, so that a
#: font substitution changes the window rather than being papered over.  This
#: constant is here so that the pure tests, WI-6's size test and anyone reading
#: the plan have the expected answer to compare against — and so that a
#: substitution shows up as a disagreement instead of going unnoticed.
MEASURED_MENLO_12 = CellMetrics(advance=10, linespace=19)
