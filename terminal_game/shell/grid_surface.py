# -*- coding: utf-8 -*-
"""WI-2 — the character grid surface.

The one thing that turns a :class:`~terminal_game.presentation.frame.Frame`
into pixels.  It measures the fixed-width font's cell metrics, reports how
many pixels 40 x 30 cells need (which is what makes WIN-2 true), and paints
every cell **at its own computed position** on a black ground in the colour
the cell says.

Three rules this module exists to keep:

**It draws characters and nothing else (SCRN-2, caution C5).**  Under the
single-process windowed architecture the medium no longer stops you drawing a
picture, so the rule lives here instead.  The only drawing call this module
makes is ``create_text``.  Do not add ``create_image``, ``create_bitmap``,
``create_rectangle``, ``create_line``, ``create_oval``, ``create_polygon`` or
``create_arc`` — not for a background, not for a border, not for a "block"
that would be easier than a glyph.  The black ground is the canvas's own
background colour, not a rectangle drawn over it.

**Each cell is drawn at its own computed position**, never as a row of text.
The picture is then correct cell by cell whatever a glyph's natural advance
width happens to be.  This is the mitigation for the glyph-alignment risk that
candidate 2 carries, and it costs nothing.

**The font is pinned by name and a substitution is fatal.**  40 x 30 is
derived from font metrics here, not set as a property, so a silent
substitution silently changes the size of the window.  Measured on this
machine: Tk's own ``TkFixedFont`` alias resolves to ``.AppleSystemUIFont``,
which is *not* fixed width — six different advance widths across the glyphs we
draw.  See ``docs/findings/WI-2-cell-metrics.md``.

This module names no toolkit.  The Tk binding is
:mod:`terminal_game.shell.tk_grid`, which is the only place the toolkit is
imported, and it is deliberately tiny.
"""

from __future__ import annotations

from typing import Dict, Iterable, NamedTuple, Optional, Sequence, Tuple

from terminal_game.presentation.frame import (
    FRAME_COLUMNS,
    FRAME_ROWS,
    Cell,
    Colour,
    Frame,
)

__all__ = [
    "FONT_FAMILY",
    "FONT_POINT_SIZE",
    "REQUIRED_GLYPHS",
    "PALETTE",
    "GROUND",
    "SurfaceFontError",
    "FontNotAvailable",
    "FontSubstituted",
    "FontNotFixedWidth",
    "CellMetrics",
    "PixelSize",
    "GridGeometry",
    "CharacterGridSurface",
    "measure_cell_metrics",
    "font_specification",
]


#: The fixed-width family, pinned by name.  Measured present on this machine
#: with uniform advance across every glyph the picture uses.
FONT_FAMILY = "Menlo"

#: **Assumption A4** — "large enough to read comfortably" is one named
#: constant, settled by eye and by nobody else.  16pt Menlo measures 10 x 19
#: pixels a cell, so the window is 400 x 570.  WI-16 puts it in front of a
#: person; if they want it bigger, this line is the only thing that changes.
FONT_POINT_SIZE = 16


def _required_glyphs() -> str:
    """Every character the picture can contain, as one string.

    The printable ASCII range covers the status line; the rest are the wall,
    dot and actor glyphs measured from the specimen picture.  A font that does
    not give all of these the same advance is not usable here, and
    :func:`measure_cell_metrics` says so rather than letting the grid drift.
    """
    ascii_printable = "".join(chr(code) for code in range(32, 127))
    walls = "═║╔╗╚╝╠╣╦╩╬"
    marks = "▪■"                    # dot, lone wall square
    player = "▐█▌"             # SCRN-5
    ghost = "▗█▖"              # SCRN-5
    return ascii_printable + walls + marks + player + ghost


REQUIRED_GLYPHS = _required_glyphs()


#: What each named colour looks like.  The vocabulary is closed by
#: :class:`~terminal_game.presentation.frame.Colour`; this is the one place
#: that says what the names mean in pixels, and WI-16 settles it by eye.
PALETTE = {
    Colour.WALL_BLUE: "#4060ff",        # SCRN-3, blue double lines
    Colour.DOT_GOLD: "#a07818",         # SCRN-4, a small dim gold square
    Colour.PLAYER_YELLOW: "#ffe838",    # SCRN-5, a bright yellow block
    Colour.GHOST_PINK: "#ff74c8",       # SCRN-5, a pink block
    Colour.STATUS_CYAN: "#28d8d8",      # SCRN-6, cyan
    Colour.GROUND_BLACK: "#000000",     # WIN-2, a black background
}

#: The ground the whole window is painted on (WIN-2).
GROUND = PALETTE[Colour.GROUND_BLACK]

#: A cell with this glyph paints nothing at all; the ground shows through.
_SPACE = " "


class SurfaceFontError(Exception):
    """The pinned font cannot be used, and the grid cannot be trusted."""


class FontNotAvailable(SurfaceFontError):
    """The named family is not installed."""


class FontSubstituted(SurfaceFontError):
    """The toolkit quietly gave us a different family than the one asked for."""


class FontNotFixedWidth(SurfaceFontError):
    """The family does not give every glyph we draw the same advance."""


class CellMetrics(NamedTuple):
    """How many pixels one character cell occupies."""

    width: int
    height: int


class PixelSize(NamedTuple):
    """A size in pixels, as the window owner needs it."""

    width: int
    height: int


class GridGeometry:
    """Where each cell of the frame lands, in pixels.

    The origin of cell (*row*, *column*) is its top-left pixel.  Text is
    anchored there — north-west — so a glyph narrower than its cell sits at
    the left of it, as it would in a terminal.
    """

    __slots__ = ("_metrics",)

    def __init__(self, metrics: CellMetrics) -> None:
        if not isinstance(metrics, CellMetrics):
            raise TypeError(
                "metrics must be a CellMetrics, not {0!r}".format(metrics)
            )
        if metrics.width <= 0 or metrics.height <= 0:
            raise ValueError(
                "a cell cannot be {0} x {1} pixels".format(*metrics)
            )
        self._metrics = metrics

    @property
    def metrics(self) -> CellMetrics:
        return self._metrics

    @property
    def pixel_size(self) -> PixelSize:
        """The pixels a whole 40 x 30 grid needs — WIN-2, multiplied out."""
        return PixelSize(
            FRAME_COLUMNS * self._metrics.width,
            FRAME_ROWS * self._metrics.height,
        )

    def cell_origin(self, row: int, column: int) -> Tuple[int, int]:
        """The top-left pixel of cell (*row*, *column*)."""
        if not 0 <= row < FRAME_ROWS:
            raise IndexError(
                "row {0} is outside the grid (0..{1})".format(
                    row, FRAME_ROWS - 1
                )
            )
        if not 0 <= column < FRAME_COLUMNS:
            raise IndexError(
                "column {0} is outside the grid (0..{1})".format(
                    column, FRAME_COLUMNS - 1
                )
            )
        return column * self._metrics.width, row * self._metrics.height

    def cell_at_pixel(self, x: int, y: int) -> Tuple[int, int]:
        """The cell whose origin is exactly (*x*, *y*).

        Deliberately exact rather than a division: a position that is not a
        cell origin is a bug in whoever computed it, and should say so.
        """
        if x % self._metrics.width or y % self._metrics.height:
            raise ValueError(
                "({0}, {1}) is not the origin of any cell at {2} x {3} "
                "pixels".format(x, y, self._metrics.width, self._metrics.height)
            )
        column = x // self._metrics.width
        row = y // self._metrics.height
        if not (0 <= row < FRAME_ROWS and 0 <= column < FRAME_COLUMNS):
            raise ValueError(
                "({0}, {1}) is outside the grid".format(x, y)
            )
        return row, column

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GridGeometry):
            return NotImplemented
        return self._metrics == other._metrics

    def __hash__(self) -> int:
        return hash(self._metrics)

    def __repr__(self) -> str:
        return "GridGeometry({0!r})".format(self._metrics)


def font_specification(
    family: str = FONT_FAMILY, point_size: int = FONT_POINT_SIZE
) -> Tuple[str, int]:
    """The font, in the form the toolkit takes it."""
    return (family, point_size)


def measure_cell_metrics(
    probe,
    family: str = FONT_FAMILY,
    point_size: int = FONT_POINT_SIZE,
    required_glyphs: str = REQUIRED_GLYPHS,
) -> CellMetrics:
    """Measure one character cell, or refuse loudly.

    *probe* is anything answering ``families()``, ``resolved_family(family,
    point_size)``, ``advance(family, point_size, glyph)`` and
    ``linespace(family, point_size)``.  In a real run that is
    :class:`terminal_game.shell.tk_grid.TkFontProbe`; in a test it is a fake,
    and no window is created either way.

    Three ways this refuses, all of them silent failures otherwise:

    * the family is not installed at all;
    * the toolkit substituted a different family for it;
    * the family does not give every glyph we draw the same advance, so
      "40 characters wide" would not be 40 equal characters.
    """
    families = list(probe.families())
    if family not in families:
        raise FontNotAvailable(
            "the font {0!r} is not installed, and the grid's size is derived "
            "from its metrics. {1} families are available.".format(
                family, len(families)
            )
        )

    resolved = probe.resolved_family(family, point_size)
    if resolved != family:
        raise FontSubstituted(
            "asked the toolkit for {0!r} and it resolved to {1!r}; a "
            "substituted font silently changes the size of the "
            "window.".format(family, resolved)
        )

    widths = {}
    for glyph in required_glyphs:
        widths.setdefault(probe.advance(family, point_size, glyph), []).append(
            glyph
        )
    if len(widths) != 1:
        summary = ", ".join(
            "{0}px for {1}".format(width, len(glyphs))
            for width, glyphs in sorted(widths.items())
        )
        raise FontNotFixedWidth(
            "{0!r} at {1}pt is not fixed width across the {2} glyphs this "
            "game draws ({3}); the character grid would not line up.".format(
                family, point_size, len(required_glyphs), summary
            )
        )

    width = next(iter(widths))
    height = probe.linespace(family, point_size)
    if width <= 0 or height <= 0:
        raise FontNotFixedWidth(
            "{0!r} at {1}pt measures {2} x {3} pixels a cell, which cannot "
            "be right.".format(family, point_size, width, height)
        )
    return CellMetrics(width, height)


class CharacterGridSurface:
    """Paints a frame onto a canvas, one character to a cell.

    The canvas is a collaborator, not something this class creates: in a real
    run it is a toolkit canvas, in a test it is a recording double, and the
    code is the same either way.  Construction configures the canvas — exact
    pixel size, black ground, no border, no caret — because forgetting to do
    that shows up as a grey window with a focus ring round it.

    Repainting is a difference, not a redraw.  The surface remembers the frame
    it last painted and touches only the cells that changed, so the ghost
    moving at seven frames a second costs six cell updates rather than twelve
    hundred.  That is the whole of the no-flicker story (SCRN-7): there is no
    clear-then-redraw for the window server to catch halfway.
    """

    __slots__ = ("_canvas", "_geometry", "_font", "_palette", "_items",
                 "_painted")

    def __init__(
        self,
        canvas,
        metrics: CellMetrics,
        font: Optional[Tuple[str, int]] = None,
        palette: Optional[Dict[Colour, str]] = None,
    ) -> None:
        self._canvas = canvas
        self._geometry = GridGeometry(metrics)
        self._font = font if font is not None else font_specification()
        self._palette = dict(PALETTE if palette is None else palette)
        missing = [
            colour.name for colour in Colour if colour not in self._palette
        ]
        if missing:
            raise ValueError(
                "the palette has no colour for {0}".format(", ".join(missing))
            )
        self._items: Dict[Tuple[int, int], int] = {}
        self._painted: Optional[Frame] = None
        self._prepare()

    # -- what the window owner asks --------------------------------------

    def pixel_size(self) -> PixelSize:
        """How many pixels this surface needs.

        **This is the one call across the WI-2 / WI-3 boundary.**  The window
        owner asks; it tells the surface nothing about the game in return.
        """
        return self._geometry.pixel_size

    @property
    def canvas(self):
        """The thing being drawn on, so the window owner can place it.

        The window owner puts this in its window and otherwise leaves it
        alone; the surface does not know or care where in the window it sits.
        """
        return self._canvas

    @property
    def geometry(self) -> GridGeometry:
        return self._geometry

    @property
    def font(self) -> Tuple[str, int]:
        return self._font

    def colour_of(self, colour: Colour) -> str:
        """What a named colour looks like on this surface."""
        try:
            return self._palette[colour]
        except KeyError:
            raise ValueError(
                "{0!r} is not one of the named colours".format(colour)
            )

    # -- painting --------------------------------------------------------

    def _prepare(self) -> None:
        size = self._geometry.pixel_size
        self._canvas.configure(
            width=size.width,
            height=size.height,
            background=GROUND,
            highlightthickness=0,
            borderwidth=0,
            # SCRN-7: no text caret, ever.  A canvas only shows one when an
            # item has the focus, which this surface never gives away — but a
            # zero-width caret cannot appear even if some later code does.
            insertwidth=0,
        )

    def paint(self, frame: Frame) -> None:
        """Show *frame*, changing only the cells that differ from the last one."""
        if not isinstance(frame, Frame):
            raise TypeError(
                "a surface paints a Frame, not {0!r}".format(frame)
            )
        previous = self._painted
        for row in range(FRAME_ROWS):
            for column in range(FRAME_COLUMNS):
                cell = frame.cell_at(row, column)
                if previous is not None and previous.cell_at(row, column) == cell:
                    continue
                self._show(row, column, cell)
        self._painted = frame

    def clear(self) -> None:
        """Take everything off the surface, leaving the black ground."""
        for item in self._items.values():
            self._canvas.delete(item)
        self._items = {}
        self._painted = None

    @property
    def painted(self) -> Optional[Frame]:
        """The frame currently on the surface, or ``None`` before the first."""
        return self._painted

    def _show(self, row: int, column: int, cell: Cell) -> None:
        position = (row, column)
        item = self._items.get(position)
        if cell.glyph == _SPACE:
            if item is not None:
                self._canvas.delete(item)
                del self._items[position]
            return
        fill = self.colour_of(cell.colour)
        if item is None:
            x, y = self._geometry.cell_origin(row, column)
            self._items[position] = self._canvas.create_text(
                x,
                y,
                text=cell.glyph,
                fill=fill,
                font=self._font,
                anchor="nw",
            )
        else:
            self._canvas.itemconfigure(item, text=cell.glyph, fill=fill)
