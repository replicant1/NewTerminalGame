"""The character grid surface — the one place that turns cells into pixels.

**This is the only module in the Presentation layer allowed to name the
windowing toolkit.**  ``tools.layer_rule.PAINTING_MODULE`` names it, and
``tests/test_layer_rule.py`` pins that the exception stays exactly one module,
so the toolkit cannot spread through the layer quietly.  Everything else this
layer produces is data: a :class:`~terminal_game.presentation.field.Field` of
glyph-and-colour, which this module paints and nothing else touches.

What it owns
------------

* **Cell metrics.**  It measures the real font at start-up and derives WIN-2's
  pixel size from what it finds, rather than trusting a constant.  A font
  substitution therefore changes the window instead of being papered over, and
  :meth:`GridSurface.metrics_match_measurement` is how a caller finds out.
* **A repaint with no flicker** (SCRN-7) — see below.
* **No caret** (SCRN-7) — see below.
* **Nothing but glyphs and flat colour** (SCRN-2) — see below.

SCRN-7, the flicker half
------------------------

    *"The picture is redrawn as things move, without flicker."*

Flicker is what you get when a surface is cleared and then redrawn: for one
frame the player sees the clearing.  This surface never clears.  At
construction it creates one background rectangle and one text item per cell —
2400 items for the 40 x 30 grid — and thereafter a repaint only *reconfigures*
them.  The item identifiers never change for the life of the surface, so there
is no moment at which the picture is incomplete.

:meth:`GridSurface.present` then does the whole frame's worth of
reconfiguration before asking the toolkit to draw anything, and asks exactly
once.  That is "composed off-screen and presented once": the toolkit coalesces
the changes and repaints the affected area a single time.

Only the cells that differ from the last frame are touched.  Measured on this
machine at Menlo 16: reconfiguring all 1200 cells costs 7.3 ms, and the twelve
or so cells an actor move really touches cost 0.092 ms, against a tick budget
of 143 ms.  So the diffing is not there for speed; it is there because it
keeps the item set fixed, and because caution C-5 warns against dirty-*region*
rendering — which this is not.  Every item permanently owns exactly one cell
and is always set to that cell's current content, so there is no region that
can be missed.

SCRN-7, the caret half
----------------------

    *"...and the text cursor is never visible."*

A canvas has no insertion caret unless a text item on it is given the keyboard
focus.  This surface never gives one focus, creates no entry or text widget
anywhere, and sets ``takefocus=0`` so the canvas is skipped by tab traversal
altogether.  Key events belong to the window (WI-6) and the translation of
them to WI-13; the drawing surface has no business with them.

SCRN-2
------

    *"Everything is drawn from characters — there are no images."*

There is no method here that draws anything.  The only way to change the
picture is :meth:`GridSurface.present`, which takes a
:class:`~terminal_game.presentation.field.Field`, and a field can only hold
:class:`~terminal_game.presentation.field.Cell` objects, each of which is
exactly one character and two colours.  The canvas therefore only ever
contains items of type ``text`` and ``rectangle`` — never ``image``,
``bitmap``, ``line``, ``arc``, ``oval``, ``polygon`` or ``window``.
:meth:`GridSurface.item_types` reports what is actually on it, so the claim is
checked rather than asserted.

Not calling ``update()``
------------------------

``root.update()`` **blocks forever** on Tcl/Tk 8.5 under macOS 26 once the
window is mapped.  Measured under S-2 and bisected with ``faulthandler``:
``Tk()``, ``withdraw()``, ``geometry()``, ``deiconify()`` and
``update_idletasks()`` all return; ``update()`` never does, pinned at
``tkinter/__init__.py`` line 1314.  ``docs/findings/S-2-anchor-window.md``
section 7 has it.

This surface therefore calls :meth:`~tkinter.Misc.update_idletasks` and never
:meth:`~tkinter.Misc.update`.  That is the right call regardless: it flushes
the pending redraw without reprocessing the event queue, so a repaint cannot
re-enter the game through a key event that arrives mid-frame.
"""

from __future__ import annotations

import tkinter
import tkinter.font
from typing import FrozenSet, List, Sequence, Tuple

from terminal_game.presentation import palette
from terminal_game.presentation.field import Cell, Field
from terminal_game.presentation.metrics import (
    COLUMNS,
    EXACT_GRID_CEILING,
    FONT_FAMILY,
    FONT_SIZE,
    MEASURED_MENLO_16,
    ROWS,
    CellMetrics,
)

#: The only canvas item types this surface ever creates.  SCRN-2 in one line.
PERMITTED_ITEM_TYPES = frozenset({"text", "rectangle"})  # type: FrozenSet[str]

#: Where a glyph sits in its cell.  North-west, so a cell's origin is the
#: glyph's origin and the arithmetic in ``metrics`` is the whole story.
_ANCHOR = "nw"


class GridSurface(object):
    """A 40 x 30 grid of character cells, painted onto a canvas.

    ``master`` is the widget to build the canvas inside — in production the
    window WI-6 owns, in a test a withdrawn root.  The surface does not create
    a toplevel and does not show one: putting the canvas on the screen belongs
    to WI-6, and placing that window belongs to WI-15.
    """

    def __init__(
        self,
        master: "tkinter.Misc",
        family: str = FONT_FAMILY,
        size: int = FONT_SIZE,
        ground: str = palette.GROUND,
    ) -> None:
        if not palette.is_colour(ground):
            raise ValueError(
                "the ground must be an #rrggbb triple, not {!r}".format(ground)
            )

        self._ground = ground
        self._font = tkinter.font.Font(root=master, family=family, size=size)

        # WIN-2 is derived from what the font actually reports, not from a
        # constant.  If the family is missing the toolkit substitutes another
        # and these two numbers change with it — which is the point.
        self._metrics = CellMetrics(
            advance=self._font.measure("M"),
            linespace=self._font.metrics("linespace"),
        )
        width, height = self._metrics.window_pixel_size()

        self._canvas = tkinter.Canvas(
            master,
            width=width,
            height=height,
            background=ground,
            highlightthickness=0,   # no focus ring eating two pixels of grid
            borderwidth=0,
            takefocus=0,            # SCRN-7: never take the keyboard focus
            insertwidth=0,          # and no insertion caret if it somehow did
        )

        # One rectangle and one text item per cell, created once and never
        # destroyed.  The order matters: rectangles first, so every glyph is
        # drawn over its own background rather than under it.
        self._backgrounds = []  # type: List[int]
        self._glyphs = []  # type: List[int]
        self._build_items()

        # What is currently on the canvas, so a repaint can touch only what
        # changed.  Starts as the blank field the items were created to show.
        self._painted = Field().snapshot()  # type: Sequence[Cell]

    # -- construction ------------------------------------------------------

    def _build_items(self) -> None:
        advance = self._metrics.advance
        linespace = self._metrics.linespace
        for row in range(ROWS):
            for column in range(COLUMNS):
                left, top = column * advance, row * linespace
                self._backgrounds.append(
                    self._canvas.create_rectangle(
                        left,
                        top,
                        left + advance,
                        top + linespace,
                        fill=self._ground,
                        width=0,        # a flat colour, with no outline drawn
                    )
                )
                self._glyphs.append(
                    self._canvas.create_text(
                        left,
                        top,
                        text=" ",
                        fill=self._ground,
                        font=self._font,
                        anchor=_ANCHOR,
                    )
                )

    # -- what the window owner needs --------------------------------------

    @property
    def widget(self) -> "tkinter.Canvas":
        """The canvas, for WI-6 to place in its window.

        Handed over for *placement*, not for drawing.  Nothing outside this
        module draws on it, and :meth:`item_types` is how a test confirms that
        nothing has.
        """
        return self._canvas

    @property
    def metrics(self) -> CellMetrics:
        """The cell metrics measured from the real font at construction."""
        return self._metrics

    @property
    def pixel_size(self) -> Tuple[int, int]:
        """WIN-2's window size in pixels, as derived from the measured font."""
        return self._metrics.window_pixel_size()

    @property
    def ground(self) -> str:
        """The background colour of the whole surface.  WIN-2's black."""
        return self._ground

    @property
    def font_description(self) -> Tuple[str, int]:
        """The family the toolkit actually resolved, and the size asked for.

        The family can differ from the one requested: if it is missing, the
        toolkit substitutes.  A caller that cares — WI-6, WI-17 — asks here
        rather than assuming it got what it asked for.
        """
        return (self._font.actual("family"), int(self._font.actual("size")))

    def metrics_match_measurement(self) -> bool:
        """Whether this font gives the cell size S-1 measured for Menlo 16.

        False means the font was substituted, or the size changed, and WIN-2's
        pixel rectangle is not the 400 x 570 the plan records.  That is not an
        error here — the window simply becomes whatever the font says — but it
        is something a caller should be able to notice.
        """
        return self._metrics == MEASURED_MENLO_16

    def exact_cell_grid(self) -> bool:
        """Whether a row drawn as one string lands where per-cell placement does.

        True at :data:`~terminal_game.presentation.metrics.EXACT_GRID_CEILING`
        and below.  This surface places every cell individually, so it is
        correct either way; the answer matters to anyone considering a faster
        per-row painter, and to WI-19 if a human asks for larger type.
        """
        return self.font_description[1] <= EXACT_GRID_CEILING

    # -- painting ----------------------------------------------------------

    def present(self, field: Field) -> None:
        """Show ``field``: compose the whole frame, then present it once.

        Every cell that differs from what is currently shown is reconfigured,
        nothing is destroyed or created, and the toolkit is asked to draw
        exactly once, at the end.  A cell that has not changed is not touched.
        """
        if not isinstance(field, Field):
            raise TypeError(
                "a surface presents a Field of glyph-and-colour, not {!r}; "
                "everything the player sees is a character (SCRN-2)".format(field)
            )

        wanted = field.snapshot()
        painted = self._painted
        canvas = self._canvas

        for index in range(COLUMNS * ROWS):
            cell = wanted[index]
            if cell == painted[index]:
                continue
            canvas.itemconfigure(
                self._glyphs[index], text=cell.glyph, fill=cell.colour
            )
            canvas.itemconfigure(
                self._backgrounds[index], fill=cell.background
            )

        self._painted = wanted

        # One flush for the whole frame.  update_idletasks, never update —
        # see the module docstring.
        canvas.update_idletasks()

    def repaint(self) -> None:
        """Write every cell to the canvas again, whether or not it changed.

        :meth:`present` already keeps the canvas equal to the last field it
        was given, so nothing in the ordinary run of the game needs this.  It
        is for the case where the canvas has been disturbed from outside — a
        display change, or a caller that wants the picture restored without
        having kept a copy of the field that produced it.

        It deliberately does **not** go through :meth:`present`'s diff.  A
        cell that is blank in the painter's record but wrong on the canvas is
        exactly the case this method exists for, and a diff would skip it.
        """
        canvas = self._canvas
        for index in range(COLUMNS * ROWS):
            cell = self._painted[index]
            canvas.itemconfigure(
                self._glyphs[index], text=cell.glyph, fill=cell.colour
            )
            canvas.itemconfigure(
                self._backgrounds[index], fill=cell.background
            )
        canvas.update_idletasks()

    # -- what is actually on the canvas ------------------------------------

    def item_count(self) -> int:
        """How many canvas items exist.  Two per cell, fixed for the surface's life."""
        return len(self._canvas.find_all())

    def item_types(self) -> FrozenSet[str]:
        """Every kind of thing on the canvas — SCRN-2, checked rather than claimed.

        Should never be anything but ``{"text", "rectangle"}``.  Anything else
        means something drew on this canvas that is not a glyph on a flat
        colour.
        """
        return frozenset(
            self._canvas.type(item) for item in self._canvas.find_all()
        )

    def item_ids(self) -> Tuple[int, ...]:
        """The canvas item identifiers, in creation order.

        Stable for the life of the surface.  A test that compares this across
        repaints is asking the question that matters for flicker: *was the
        picture ever torn down and rebuilt?*
        """
        return tuple(self._backgrounds) + tuple(self._glyphs)

    def shown_cell(self, column: int, row: int) -> Cell:
        """What the canvas is actually showing at ``(column, row)``.

        Read back from the canvas items themselves, not from the surface's
        record of what it painted — so a test using this is asking the canvas
        what it holds rather than asking the painter what it believes.
        """
        CellMetrics.check_in_grid(column, row)
        index = row * COLUMNS + column
        return Cell(
            glyph=self._canvas.itemcget(self._glyphs[index], "text"),
            colour=self._canvas.itemcget(self._glyphs[index], "fill"),
            background=self._canvas.itemcget(self._backgrounds[index], "fill"),
        )

    def shown_row(self, row: int) -> str:
        """What the canvas is showing on one row, as a string."""
        return "".join(self.shown_cell(column, row).glyph for column in range(COLUMNS))

    # -- SCRN-7's caret half, as a question -------------------------------

    def caret_is_impossible(self) -> bool:
        """Whether a text caret could appear on this surface.

        Three things have to be true, and all three are set at construction:
        the canvas refuses the keyboard focus, no canvas item holds focus, and
        the insertion caret has no width even if one somehow did.
        """
        return (
            str(self._canvas.cget("takefocus")) in ("0", "")
            and not self._canvas.focus()
            and int(self._canvas.cget("insertwidth")) == 0
        )

    def descendant_widget_classes(self) -> FrozenSet[str]:
        """The Tk class of every widget this surface created, canvas included.

        A caret needs a widget that edits text.  This surface creates exactly
        one widget and it is a ``Canvas``; if an ``Entry``, ``Text``,
        ``TEntry`` or ``Spinbox`` ever appears here, SCRN-7 is at risk.
        """
        classes = {self._canvas.winfo_class()}
        for child in self._canvas.winfo_children():
            classes.add(child.winfo_class())
        return frozenset(classes)

    def __repr__(self) -> str:
        width, height = self.pixel_size
        family, size = self.font_description
        return "GridSurface({} x {} cells, {} x {} px, {} {})".format(
            COLUMNS, ROWS, width, height, family, size
        )
