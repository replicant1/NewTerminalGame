# -*- coding: utf-8 -*-
"""Recording doubles that stand in for the windowing toolkit.

**No automated test in this project constructs a toolkit window.**  These are
what make that possible: a canvas that records what was drawn on it, and a
font probe that answers metric questions from a table.

The canvas is a *recording* double, not a strict one.  It records every
drawing call, including the ones the surface must never make, so a test can
assert that the kinds of thing drawn were exactly ``{"text"}`` rather than
relying on the double to raise.  A double that raised would make the
"characters only" test pass for the wrong reason the day somebody loosened
it; recording it and asserting on the record cannot.

Deliberately not named ``test_*``: this is test apparatus, not a test case.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from terminal_game.presentation.frame import (
    FRAME_COLUMNS,
    FRAME_ROWS,
    BLANK,
    Cell,
    Colour,
    Frame,
    FrameBuilder,
)


class CanvasItem:
    """One thing that was drawn, and what it currently looks like."""

    def __init__(self, item_id: int, kind: str, coordinates, options) -> None:
        self.id = item_id
        self.kind = kind
        self.coordinates = tuple(coordinates)
        self.options = dict(options)
        self.deleted = False

    def __repr__(self) -> str:
        return "CanvasItem(#{0} {1} at {2} {3})".format(
            self.id, self.kind, self.coordinates, self.options
        )


class RecordingCanvas:
    """A canvas that draws nothing and remembers everything.

    It models the little of a toolkit canvas the surface actually uses:
    ``configure``, the ``create_*`` family, ``itemconfigure`` and ``delete``.
    The caret-related calls (``focus``, ``icursor``, ``insert``) are here so
    that a test can assert they never happen — SCRN-7.
    """

    #: Everything a canvas can be asked to create.  Only "text" is allowed on
    #: this surface; the rest exist so that breaking the rule is *recorded*
    #: rather than impossible, and can therefore be asserted against.
    CREATABLE = (
        "text",
        "image",
        "bitmap",
        "rectangle",
        "line",
        "oval",
        "polygon",
        "arc",
        "window",
    )

    def __init__(self) -> None:
        self.configuration: Dict[str, object] = {}
        self.calls: List[Tuple[str, tuple, dict]] = []
        self.items: Dict[int, CanvasItem] = {}
        self.caret_calls: List[Tuple[str, tuple]] = []
        self._next_id = 1

    # -- the bits of a canvas the surface uses ---------------------------

    def configure(self, **options):
        self.calls.append(("configure", (), dict(options)))
        self.configuration.update(options)

    config = configure

    def cget(self, key):
        return self.configuration[key]

    def _create(self, kind: str, coordinates, options) -> int:
        item_id = self._next_id
        self._next_id += 1
        self.items[item_id] = CanvasItem(item_id, kind, coordinates, options)
        self.calls.append((
            "create_" + kind, tuple(coordinates), dict(options)
        ))
        return item_id

    def create_text(self, x, y, **options):
        return self._create("text", (x, y), options)

    def create_image(self, x, y, **options):
        return self._create("image", (x, y), options)

    def create_bitmap(self, x, y, **options):
        return self._create("bitmap", (x, y), options)

    def create_window(self, x, y, **options):
        return self._create("window", (x, y), options)

    def create_rectangle(self, *coordinates, **options):
        return self._create("rectangle", coordinates, options)

    def create_line(self, *coordinates, **options):
        return self._create("line", coordinates, options)

    def create_oval(self, *coordinates, **options):
        return self._create("oval", coordinates, options)

    def create_polygon(self, *coordinates, **options):
        return self._create("polygon", coordinates, options)

    def create_arc(self, *coordinates, **options):
        return self._create("arc", coordinates, options)

    def itemconfigure(self, item, **options):
        self.calls.append(("itemconfigure", (item,), dict(options)))
        self.items[item].options.update(options)

    itemconfig = itemconfigure

    def itemcget(self, item, key):
        return self.items[item].options[key]

    def delete(self, *items):
        for item in items:
            self.calls.append(("delete", (item,), {}))
            self.items[item].deleted = True

    # -- the caret, which must never appear (SCRN-7) ---------------------

    def focus(self, *args):
        self.caret_calls.append(("focus", args))

    def icursor(self, *args):
        self.caret_calls.append(("icursor", args))

    def insert(self, *args):
        self.caret_calls.append(("insert", args))

    # -- views a test reads ----------------------------------------------

    def live_items(self) -> Sequence[CanvasItem]:
        """Everything currently on the canvas, in the order it was created."""
        return [item for item in self.items.values() if not item.deleted]

    def kinds_drawn(self):
        """The kinds of thing ever created, deleted ones included."""
        return {item.kind for item in self.items.values()}

    def drawing_calls(self):
        """Just the calls that change the picture, in order."""
        return [
            call
            for call in self.calls
            if call[0].startswith("create_")
            or call[0] in ("itemconfigure", "delete")
        ]


def reconstruct_frame(canvas: RecordingCanvas, geometry, palette) -> Frame:
    """Read the picture back off a recording canvas, as a frame.

    Every live text item is mapped from its pixel position back to a cell,
    and its fill back to a named colour.  Anything that does not map — a
    position that is not a cell origin, a colour that is not in the palette,
    two items in the same cell — raises, because each of those is a defect
    the test exists to catch rather than something to paper over.
    """
    by_colour = {}
    for colour, value in palette.items():
        if value in by_colour:
            raise AssertionError(
                "the palette gives {0} the same colour as {1}; the two could "
                "not be told apart on screen".format(
                    colour.name, by_colour[value].name
                )
            )
        by_colour[value] = colour

    builder = FrameBuilder()
    seen = {}
    for item in canvas.live_items():
        if item.kind != "text":
            raise AssertionError(
                "this surface may only draw characters, but it drew a "
                "{0}: {1!r}".format(item.kind, item)
            )
        x, y = item.coordinates
        row, column = geometry.cell_at_pixel(x, y)
        if (row, column) in seen:
            raise AssertionError(
                "two items are stacked in cell ({0}, {1}): {2!r} and "
                "{3!r}".format(row, column, seen[(row, column)], item)
            )
        seen[(row, column)] = item
        glyph = item.options["text"]
        fill = item.options["fill"]
        if fill not in by_colour:
            raise AssertionError(
                "{0!r} at ({1}, {2}) is not one of the palette's "
                "colours".format(fill, row, column)
            )
        builder.set_cell(row, column, glyph, by_colour[fill])
    return builder.build()


def assert_surface_shows(case, canvas, surface, expected: Frame) -> None:
    """Assert the surface is showing *expected*, glyph and colour.

    The picture is compared as **text** first, so a failure reads as two
    pictures side by side rather than as a mismatched object; the colours of
    every non-blank cell are then compared separately.  A blank cell has no
    colour on screen — nothing is drawn there and the ground shows through —
    so its colour is not compared, and cannot be.
    """
    actual = reconstruct_frame(canvas, surface.geometry, {
        colour: surface.colour_of(colour) for colour in Colour
    })
    case.assertEqual(expected.to_text(), actual.to_text())
    for row in range(FRAME_ROWS):
        for column in range(FRAME_COLUMNS):
            cell = expected.cell_at(row, column)
            if cell.glyph == " ":
                continue
            case.assertEqual(
                cell.colour,
                actual.colour_at(row, column),
                "cell ({0}, {1}) showing {2!r}".format(row, column, cell.glyph),
            )


class FakeFontProbe:
    """Answers font questions from a table, with no toolkit anywhere.

    *advances* maps a glyph to its width; a glyph not in it takes
    *default_advance*, which is how a test builds a font that is fixed width
    everywhere except one awkward glyph.
    """

    def __init__(
        self,
        families=("Menlo", "Monaco", "Helvetica"),
        resolves_to=None,
        default_advance=10,
        advances=None,
        linespace=19,
    ) -> None:
        self._families = tuple(families)
        self._resolves_to = dict(resolves_to or {})
        self._default_advance = default_advance
        self._advances = dict(advances or {})
        self._linespace = linespace
        self.questions = []

    def families(self):
        self.questions.append(("families", ()))
        return self._families

    def resolved_family(self, family, point_size):
        self.questions.append(("resolved_family", (family, point_size)))
        return self._resolves_to.get(family, family)

    def advance(self, family, point_size, glyph):
        self.questions.append(("advance", (family, point_size, glyph)))
        return self._advances.get(glyph, self._default_advance)

    def linespace(self, family, point_size):
        self.questions.append(("linespace", (family, point_size)))
        return self._linespace
