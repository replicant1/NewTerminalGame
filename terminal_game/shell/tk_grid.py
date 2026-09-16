# -*- coding: utf-8 -*-
"""WI-2 — the Tk binding for the character grid surface.

This module is deliberately tiny and deliberately the only place in the
project that imports the windowing toolkit for the surface.  Everything with
a decision in it lives in :mod:`terminal_game.shell.grid_surface`, which names
no toolkit and is unit-tested with a recording double.

**Nothing here may be called from an automated test.**  Constructing a font
probe or a canvas needs a live toolkit interpreter, and the suite never
creates one.  What is here is exercised by the walking skeleton (WI-4) and
looked at by a person (WI-16).

The interpreter is ``/usr/bin/python3`` — 3.9.6 with Tk 8.5.9.  The other
interpreter on this machine has no ``_tkinter`` at all and this import fails
outright on it, which is the loud failure we want rather than a mystery.
"""

from __future__ import annotations

import tkinter
import tkinter.font

from terminal_game.shell.grid_surface import (
    FONT_FAMILY,
    FONT_POINT_SIZE,
    GROUND,
    CellMetrics,
    CharacterGridSurface,
    font_specification,
    measure_cell_metrics,
    pixel_size_for,
)
from terminal_game.shell.toolkit import PixelSize

__all__ = [
    "TkFontProbe",
    "measure_metrics",
    "grid_pixel_size",
    "surface_on",
    "create_surface",
]


class TkFontProbe:
    """Answers the four questions :func:`measure_cell_metrics` asks of a font.

    It needs a toolkit interpreter — a ``Tk`` root, or any widget — but it
    does **not** need a mapped window: a root that has been withdrawn before
    the event loop is entered measures perfectly well and never appears on
    anybody's screen.
    """

    __slots__ = ("_master", "_cache")

    def __init__(self, master) -> None:
        self._master = master
        self._cache = {}

    def _font(self, family: str, point_size: int):
        key = (family, point_size)
        if key not in self._cache:
            self._cache[key] = tkinter.font.Font(
                root=self._master, family=family, size=point_size
            )
        return self._cache[key]

    def families(self):
        return tkinter.font.families(self._master)

    def resolved_family(self, family: str, point_size: int) -> str:
        return self._font(family, point_size).actual("family")

    def advance(self, family: str, point_size: int, glyph: str) -> int:
        return self._font(family, point_size).measure(glyph)

    def linespace(self, family: str, point_size: int) -> int:
        return self._font(family, point_size).metrics("linespace")


def measure_metrics(
    master=None,
    family: str = FONT_FAMILY,
    point_size: int = FONT_POINT_SIZE,
) -> CellMetrics:
    """Measure one character cell, before there is a window to put it in.

    The window owner (WI-3) is *told* its pixel size when it is built, and it
    is the thing that creates the window — so the measurement has to happen
    first, with no window anywhere.  Given no *master*, this makes a Tk
    interpreter of its own, **withdraws it before the event loop can be
    entered so it is never mapped**, measures, and destroys it again.  Nothing
    reaches the screen and there is nothing to reap.

    Raises a :class:`~terminal_game.shell.grid_surface.SurfaceFontError` if
    the pinned font is missing, substituted, or not fixed width — see
    :mod:`terminal_game.shell.grid_surface` for why a quiet substitution is
    the worst outcome available.
    """
    if master is not None:
        return measure_cell_metrics(TkFontProbe(master), family, point_size)

    scratch = tkinter.Tk()
    scratch.withdraw()
    try:
        return measure_cell_metrics(
            TkFontProbe(scratch), family, point_size
        )
    finally:
        scratch.destroy()


def grid_pixel_size(
    family: str = FONT_FAMILY, point_size: int = FONT_POINT_SIZE
) -> PixelSize:
    """The pixels a 40 x 30 grid needs in this font — what WI-3 is told."""
    return pixel_size_for(measure_metrics(None, family, point_size))


def surface_on(
    target,
    metrics: CellMetrics,
    family: str = FONT_FAMILY,
    point_size: int = FONT_POINT_SIZE,
) -> CharacterGridSurface:
    """Paint into a drawing target somebody else made.

    *target* is what :meth:`WindowOwner.open` hands back — the canvas inside
    the game's window.  This is the join between WI-3 and WI-2, and it is the
    only thing that crosses between them.
    """
    return CharacterGridSurface(
        target, metrics, font=font_specification(family, point_size)
    )


def create_surface(
    master,
    family: str = FONT_FAMILY,
    point_size: int = FONT_POINT_SIZE,
) -> CharacterGridSurface:
    """Measure the font and build a surface on a new canvas inside *master*.

    A convenience for the case where the canvas has not already been made —
    the walking skeleton, and looking at the thing by hand.  When the window
    owner has already created a drawing target, use :func:`measure_metrics`
    and :func:`surface_on` instead, so there is one canvas and not two.

    The canvas is created but not placed: where it sits in the window is the
    window owner's business (WI-3), not the surface's.
    """
    metrics = measure_metrics(master, family, point_size)
    canvas = tkinter.Canvas(master, background=GROUND, highlightthickness=0)
    return surface_on(canvas, metrics, family, point_size)
